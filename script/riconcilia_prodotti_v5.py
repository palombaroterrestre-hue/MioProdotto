"""
Riconciliazione prodotti v5: filtro quantita' + embeddings locali + giudice LLM.

Sostituisce la logica di genera_alias.py (Jaccard su token) per TROVARE i duplicati.
ATTENZIONE: questo script e' in SOLA LETTURA sul database. Produce due CSV:
  - proposte_unioni_v5.csv   -> gruppi di prodotti da unire (da rivedere)
  - coda_revisione_v5.csv    -> coppie dubbie da far decidere a una persona
L'applicazione delle unioni al DB/sito e' un passo separato, da fare solo dopo
la revisione umana (vedi issue #3). Il giudice viene chiamato in parallelo
(8 richieste alla volta, parametro WORKERS_GIUDICE).

Come funziona (issue #1, #3, #4):
  1. Ogni prodotto viene normalizzato: nome pulito + quantita' in forma canonica
     (es. "1,5L" e "1500ML" diventano entrambi "1500ML").
  2. FILTRO QUANTITA' OBBLIGATORIO: due prodotti con quantita' lette e diverse
     non vengono MAI uniti (niente merge tra taglie).
  3. Embeddings locali (sentence-transformers, modello multilingua MiniLM,
     nessuna API a pagamento, nessun tetto giornaliero) trovano le coppie
     candidate per similarita' semantica dentro la stessa categoria.
  4. Unione automatica solo sopra soglia alta (0.99) E stessa quantita'.
  5. Zona grigia (0.85-0.99): decide il "giudice" gemma4:31b-cloud su Ollama
     cloud con prompt few-shot. Puo' rispondere UGUALI, DIVERSI o NON-SICURO.
  6. NON-SICURO, e ogni coppia con quantita' mancante su entrambi i lati,
     finisce nella coda di revisione umana.

Misurato sul dataset di test (798 coppie da correzioni umane, 19/10/2026):
  precisione ~55-60%, recall ~84% (sistema attuale: recall ~1%, 1383 falsi merge
  tra taglie diverse). I dubbi vanno in coda invece di diventare errori.

Setup (una tantum):
  pip install sentence-transformers supabase python-dotenv requests
Nel .env servono: SUPABASE_URL, SUPABASE_KEY, GEMMA_API_KEY (chiave Ollama cloud).
Uso: python script/riconcilia_prodotti_v5.py
"""

import os
import sys
import csv
import re
import json
import time
import unicodedata
from collections import defaultdict

import requests
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMMA_API_KEY = os.getenv("GEMMA_API_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_KEY richiesti in .env")
if not GEMMA_API_KEY:
    raise RuntimeError("GEMMA_API_KEY richiesto in .env (chiave Ollama cloud)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- parametri misurati sul dataset di test (vedi issue #4) ---
MODELLO_EMB = "paraphrase-multilingual-MiniLM-L12-v2"  # locale, gratuito
T_LOW = 0.85    # sotto: coppie scartate senza giudice
T_HIGH = 0.99   # sopra + stessa quantita' -> unione automatica
GIUDICE_MODEL = "gemma4:31b-cloud"
WORKERS_GIUDICE = 8  # richieste parallele al giudice (aumentabile se non si supera il rate limit)
EMB_CACHE = "emb_cache_minilm.npz"  # cache su disco: i rilanci non ricalcolano

# api.ollama.com (Cloudflare) rifiuta client senza User-Agent da browser: errore 403 codice 1010
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"})


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = re.sub(r"[̀-ͯ]", "", s).upper().strip()
    return re.sub(r"\s+", " ", s)


def parse_qta(q: str) -> str:
    """Quantita' in forma canonica: '1,5L'->'1500ML', '1KG'->'1000G', '4 ROTOLI'->'4PZ'. 'N/D' o non letta -> 'ND'."""
    q = (q or "").strip().upper().replace(",", ".").replace(" ", "")
    if not q or q == "N/D":
        return "ND"

    def base(v, u):
        v = float(v)
        if u == "KG":
            v *= 1000
            u = "G"
        if u == "GR":
            u = "G"
        if u in ("LT", "L"):
            v *= 1000
            u = "ML"
        if u == "CL":
            v *= 10
            u = "ML"
        return v, u

    m = re.fullmatch(r"(\d+(?:\.\d+)?)(KG|G|GR|L|LT|ML|CL)X(\d+)", q)  # 100GX3
    if m:
        v, u = base(m.group(1), m.group(2))
        return f"{v * int(m.group(3)):g}{u}"
    m = re.fullmatch(r"(\d+)X(\d+(?:\.\d+)?)(KG|G|GR|L|LT|ML|CL)", q)  # 20X4G
    if m:
        v, u = base(m.group(2), m.group(3))
        return f"{v * int(m.group(1)):g}{u}"
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(KG|G|GR|L|LT|ML|CL)", q)  # 225G, 1,5L
    if m:
        v, u = base(m.group(1), m.group(2))
        return f"{v:g}{u}"
    m = re.fullmatch(r"(\d+)(PZ|PEZZI|ROTOLI|CAPS|CAPSULE|LAVAGGI|PZ\.|X)", q)
    if m:
        return f"{m.group(1)}PZ"
    return "ND"


PROMPT_GIUDICE = '''Due nomi di prodotto da un volantino supermercato (estratti automaticamente, possono contenere errori OCR). Decidi se sono lo stesso prodotto nella stessa confezione.

Regole:
- Refusi ed errori OCR, ANCHE nella marca (es. FINDOS per FINDUS), spazi o lettere scambiate = stesso prodotto.
- Ordine delle parole diverso = stesso prodotto.
- Marca diversa, tipo/variante/gusto/ingrediente diverso, o quantita' diversa = DIVERSI.
- Se manca l'informazione per decidere (es. marca presente solo su un lato) o sei in dubbio = NON-SICURO.

Esempi:
A: "CUCCIOLONE CLASSICO ALGIDA" (480G) | B: "CUCCIOLONE ALGIDA CLASSICO" (480G) -> UGUALI
A: "SAPONE CREMA DI SCHIAMPAGNA MARSOGLIA" (400G) | B: "SAPONE CREMA SPUMA DI SCIAMPAGNA MARSIGLIA" (ND) -> UGUALI
A: "TOVAGLIOLI MONOVOLO SCOTTEX" (ND) | B: "T OVAGLIOLI MONOVELO SCOTTEX" (ND) -> UGUALI
A: "MOZZARELLA SANTA LUCIA GALBANI" (100G) | B: "MOZZARELLA TRIS SANTA LUCIA GALBANI" (100G) -> DIVERSI
A: "CAFFE QUALITA ORO LAVAZZA" (250G) | B: "CAFFE DEK LAVAZZA" (250G) -> DIVERSI
A: "IMPANATE DI SUINO" (1000G) | B: "IMPANATE DI POLLO" (1000G) -> DIVERSI
A: "MISTO PER RISOTTO E SPAGHETTI APPETTAIS" (300G) | B: "MISTO PER RISOTTO E SPAGHETTI APPEITAIS" (300G) -> NON-SICURO

Rispondi SOLO con UGUALI, DIVERSI o NON-SICURO.
A: "{a}" (quantita: {qa})
B: "{b}" (quantita: {qb})'''


def giudice(a: str, qa: str, b: str, qb: str) -> str:
    """UGUALI / DIVERSI / NONSICURO dal giudice LLM su Ollama cloud."""
    for tentativo in range(3):
        try:
            r = HTTP.post(
                "https://api.ollama.com/api/chat",
                json={"model": GIUDICE_MODEL, "stream": False,
                      "messages": [{"role": "user", "content": PROMPT_GIUDICE.format(a=a, qa=qa, b=b, qb=qb)}]},
                headers={"Authorization": f"Bearer {GEMMA_API_KEY}"},
                timeout=60,
            )
            if r.status_code == 429 and tentativo < 2:
                time.sleep(15 * (tentativo + 1))
                continue
            r.raise_for_status()
            ans = r.json()["message"]["content"].upper()
            if "NON" in ans and "SICURO" in ans:
                return "NONSICURO"
            if "UGUALI" in ans and "DIVERSI" not in ans:
                return "UGUALI"
            if "DIVERSI" in ans:
                return "DIVERSI"
            return "NONSICURO"  # risposta non chiara: meglio la coda umana che un errore
        except requests.RequestException:
            if tentativo < 2:
                time.sleep(5)
                continue
            return "NONSICURO"  # giudice irraggiungibile: coda umana, non errore automatico


def fetch_righe() -> list[dict]:
    """Sola lettura: tutte le righe di rilevazioni_v4, paginate da 1000."""
    righe = []
    start = 0
    while True:
        resp = (supabase.table("rilevazioni_v4")
                .select("id,nome_prodotto,quantita,categoria")
                .order("id")
                .range(start, start + 999)
                .execute())
        righe.extend(resp.data)
        if len(resp.data) < 1000:
            break
        start += 1000
    return righe


def embeddings_nomi(nomi: list[str]) -> dict[str, np.ndarray]:
    """Embeddings MiniLM con cache su disco: rilanciare lo script non ricalcola tutto."""
    from sentence_transformers import SentenceTransformer
    cache: dict[str, np.ndarray] = {}
    if os.path.exists(EMB_CACHE):
        d = np.load(EMB_CACHE)
        cache = {n: v for n, v in zip(d["names"], d["V"])}
    da_fare = [n for n in nomi if n not in cache]
    print(f"embeddings: {len(cache)} in cache, {len(da_fare)} da calcolare")
    if da_fare:
        modello = SentenceTransformer(MODELLO_EMB)
        for i in range(0, len(da_fare), 256):
            blocco = da_fare[i:i + 256]
            V = modello.encode(blocco, batch_size=128, normalize_embeddings=True, convert_to_numpy=True)
            for n, v in zip(blocco, V):
                cache[n] = v
            print(f"  {min(i + 256, len(da_fare))}/{len(da_fare)}")
        nomi_tutti = sorted(cache)
        np.savez_compressed(EMB_CACHE, names=np.array(nomi_tutti),
                            V=np.stack([cache[n] for n in nomi_tutti]).astype(np.float32))
    return cache


def main():
    print("Scarico rilevazioni_v4 (sola lettura)...")
    righe = fetch_righe()
    print(f"righe: {len(righe)}")

    # nodi unici (nome normalizzato, quantita' canonica, categoria)
    nodi, visti = [], set()
    for r in righe:
        n = norm(r["nome_prodotto"])
        if not n:
            continue
        key = (n, parse_qta(r["quantita"]), r["categoria"] or "GENERICO")
        if key not in visti:
            visti.add(key)
            nodi.append(key)
    print(f"prodotti unici (nome, quantita', categoria): {len(nodi)}")

    emb = embeddings_nomi(sorted({n for n, q, c in nodi}))

    # candidati: stessa categoria, similarita' >= T_LOW
    per_cat = defaultdict(list)
    for i, (n, q, c) in enumerate(nodi):
        per_cat[c].append(i)
    auto, coda = [], []
    genitore = {}

    def find(x):
        genitore.setdefault(x, x)
        while genitore[x] != x:
            genitore[x] = genitore[genitore[x]]
            x = genitore[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            genitore[ra] = rb

    # fase 1: candidati da embeddings + filtro quantita' (nessuna chiamata al giudice)
    da_giudicare = []
    for c, idxs in per_cat.items():
        V = np.stack([emb[nodi[i][0]] for i in idxs])
        S = V @ V.T
        for x in range(len(idxs)):
            for y in np.where(S[x] >= T_LOW)[0]:
                if y <= x:
                    continue
                i, j = idxs[x], idxs[y]
                ni, qi, _ = nodi[i]
                nj, qj, _ = nodi[j]
                sim = float(S[x, y])
                # filtro quantita' obbligatorio: taglie lette e diverse -> mai unire
                if qi != "ND" and qj != "ND" and qi != qj:
                    continue
                if sim >= T_HIGH and qi == qj and qi != "ND":
                    union(i, j)
                    auto.append((ni, qi, nj, qj, c, sim))
                elif qi == "ND" and qj == "ND":
                    # quantita' ignota da entrambi i lati: niente decisioni automatiche
                    coda.append((ni, qi, nj, qj, c, sim, "quantita' mancante"))
                else:
                    da_giudicare.append((i, j, ni, qi, nj, qj, c, sim))
    print(f"unioni automatiche: {len(auto)}, coppie da giudicare: {len(da_giudicare)}")

    # fase 2: giudice in parallelo (le chiamate sono di rete, la CPU resta libera)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKERS_GIUDICE) as pool:
        verdetti = list(pool.map(lambda t: giudice(t[2], t[3], t[4], t[5]), da_giudicare))
    for (i, j, ni, qi, nj, qj, c, sim), verdetto in zip(da_giudicare, verdetti):
        if verdetto == "UGUALI":
            union(i, j)
        elif verdetto == "NONSICURO":
            coda.append((ni, qi, nj, qj, c, sim, "giudice in dubbio"))
    print(f"coppie finite in coda di revisione: {len(coda)}")

    # gruppi finali con piu' di un membro
    gruppi = defaultdict(list)
    for i, (n, q, c) in enumerate(nodi):
        gruppi[find(i)].append((n, q, c))
    gruppi_multi = [g for g in gruppi.values() if len(g) > 1]
    print(f"gruppi proposti con almeno 2 nomi: {len(gruppi_multi)}")

    with open("proposte_unioni_v5.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["gruppo", "nome_canonico", "membri", "categoria", "quantita"])
        for k, g in enumerate(sorted(gruppi_multi, key=len, reverse=True), 1):
            canonico = min(g, key=lambda t: len(t[0]))
            w.writerow([k, canonico[0], " | ".join(n for n, q, c in g), canonico[2],
                        " | ".join(sorted({q for n, q, c in g}))])
    with open("coda_revisione_v5.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["prodotto_a", "quantita_a", "prodotto_b", "quantita_b", "categoria", "similarita", "motivo"])
        for a, qa, b, qb, c, sim, motivo in sorted(coda, key=lambda t: -t[5]):
            w.writerow([a, qa, b, qb, c, f"{sim:.3f}", motivo])
    print("Scritti proposte_unioni_v5.csv e coda_revisione_v5.csv")
    print("NESSUNA scrittura sul database: rivedi i CSV prima di applicare le unioni.")


if __name__ == "__main__":
    main()
