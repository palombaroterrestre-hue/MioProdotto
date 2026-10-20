"""Scraper volantini Ekom per GitHub Actions (nessun PC).

Fonte: elenco pubblico del sito Ekom (nessun login):
  https://www.ekomdiscount.it/ebsn/api/leaflet/search?parent_leaflet_type_id=1
Regione letta per ora: solo Liguria e Piemonte (PDF che finisce in "-LGPM.pdf").

Modi:
  python script/scraper_ekom_cloud.py --dry-run
      Scarica il PDF, crea le immagini con nome unico in ./out_pagine.
      NON scrive su Supabase, NON chiama l'AI.
  python script/scraper_ekom_cloud.py --scrivi
      Come sopra, poi carica le immagini su Storage, legge le pagine con
      l'AI e scrive nelle tabelle v6_volantini, v6_pagine, v6_offerte.
Nessuna chiave nel codice: SUPABASE_URL, SUPABASE_SECRET_KEY, OLLAMA_API_KEY
arrivano dai GitHub Secrets.
"""
import argparse
import io
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from pdf2image import convert_from_bytes

LISTA_URL = "https://www.ekomdiscount.it/ebsn/api/leaflet/search?parent_leaflet_type_id=1"
SUFFISSO_REGIONE = "-LGPM.pdf"
USER_AGENT = "MioProdotto-scraper/1.0 (uso personale, 1 richiesta a settimana)"
OUT_DIR = "out_pagine"
BUCKET = "volantini"
MODELLO = "gemma4:31b-cloud"

http = requests.Session()
http.headers["User-Agent"] = USER_AGENT


def get_con_retry(url, tentativi=3, timeout=60):
    for i in range(1, tentativi + 1):
        try:
            r = http.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"[!] GET fallita ({i}/{tentativi}) {url}: {e}")
            if i == tentativi:
                raise
            time.sleep(3 * i)


def leggi_elenco():
    r = get_con_retry(LISTA_URL)
    dati = json.loads(r.text, strict=False)
    volantini = dati["data"]["leaflets"]
    risultato = []
    for v in volantini:
        loc = v.get("location", "")
        if not loc.endswith(SUFFISSO_REGIONE):
            continue
        m = re.match(r"EKOMPromo(\d+)-", loc)
        if not m:
            print(f"[!] Nome PDF inatteso: {loc}")
            continue
        risultato.append({
            "leaflet_id": v["leafletId"],
            "numero_promo": int(m.group(1)),
            "pdf": loc,
            "pdf_url": v["baseLocation"].rstrip("/") + "/" + loc,
            "dal": v["validateDateFrom"][:10],
            "al": v["validateDateTo"][:10],
            "titolo": v.get("title", ""),
        })
    return risultato


def nome_pagina(v, n):
    # Nome unico: promo + data inizio + numero pagina. Non si sovrascrive piu'.
    base = v["pdf"].replace(".pdf", "")
    return f"{base}_{v['dal']}_p{n:02d}.jpg"


def scarica_e_crea_pagine(v):
    r = get_con_retry(v["pdf_url"], timeout=120)
    if not r.content.startswith(b"%PDF"):
        raise RuntimeError("Il file scaricato non e' un PDF")
    pagine = convert_from_bytes(r.content, dpi=200)
    os.makedirs(OUT_DIR, exist_ok=True)
    file = []
    for i, img in enumerate(pagine, start=1):
        path = os.path.join(OUT_DIR, nome_pagina(v, i))
        img.convert("RGB").save(path, "JPEG", quality=85)
        file.append((i, path, img))
    return len(r.content), file


# ---------- parte che scrive (solo con --scrivi) ----------

PROMPT = """Sei un estrattore OCR per volantini promozionali.
Restituisci SOLO un JSON array valido, un oggetto per prodotto realmente visibile:
[{"marca":"STRINGA o null","nome":"STRINGA MAIUSCOLO","quantita_valore":0,"quantita_unita":"G|KG|ML|LT|PZ|null","prezzo":0.00,"promo":"STRINGA o null"}]
Regole: nome senza claim (NOVITA', SUPER PREZZO). prezzo = prezzo finale con punto decimale.
promo = es. "-20%", "3x2", "2x1", "A PARTIRE DA" oppure null. Quantita non leggibile: null.
Non inventare prodotti. Se non ce ne sono: []."""


def estrai_json(testo):
    if not testo:
        return None
    for a, b in (("[", "]"), ("{", "}")):
        i, j = testo.find(a), testo.rfind(b)
        if i != -1 and j > i:
            try:
                return json.loads(testo[i:j + 1])
            except Exception:
                pass
    return None


def chiedi_ai(client, img_bytes):
    for i in range(5):
        try:
            res = client.chat(model=MODELLO, format="json", messages=[
                {"role": "user", "content": PROMPT, "images": [img_bytes]}])
            testo = res.get("message", {}).get("content", "")
            prodotti = estrai_json(testo)
            if prodotti is None:
                raise ValueError("Risposta AI non JSON: " + testo[:300])
            if isinstance(prodotti, dict):
                prodotti = [prodotti]
            if not isinstance(prodotti, list):
                raise ValueError("Risposta AI non valida: " + testo[:300])
            return prodotti
        except Exception as e:
            print(f"      [!] AI errore ({i + 1}/5): {e}")
            time.sleep(10)
    raise RuntimeError("Lettura AI fallita dopo 5 tentativi")


def riduci(img, max_w=1400):
    if img.width > max_w:
        img = img.resize((max_w, int(img.height * max_w / img.width)))
    return img.convert("RGB")


def scrivi_v6(v, file_pagine):
    import ollama
    from supabase import create_client

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    ai = ollama.Client(host="https://api.ollama.com",
                       headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"})

    anno, mese = int(v["dal"][:4]), int(v["dal"][5:7])
    ex = (sb.table("v6_volantini").select("id,pagine").eq("anno", anno)
          .eq("numero_promo", v["numero_promo"]).execute().data)
    prefix = v["pdf"].replace(".pdf", "") + "_" + v["dal"]
    if ex:
        vol = ex[0]
        print(f"[ripresa] Promo {v['numero_promo']}/{anno} (id {vol['id']}).")
        sb.table("v6_volantini").update({"pagine": 0}).eq("id", vol["id"]).execute()
    else:
        # pagine=0 indica un volantino incompleto, anche se il processo si interrompe.
        vol = sb.table("v6_volantini").insert({
            "numero_promo": v["numero_promo"], "anno": anno, "mese": mese,
            "valido_dal": v["dal"], "valido_al": v["al"], "pagine": 0,
            "sorgente": "ebsn api leaflet/search", "immagine_prefix": prefix,
            "anno_metodo": "date dall'elenco Ekom (campo validateDate)",
        }).execute().data[0]

    esistenti = (sb.table("v6_pagine").select("id,pagina_num")
                 .eq("volantino_id", vol["id"]).execute().data)
    per_numero = {p["pagina_num"]: p for p in esistenti}
    for n, path, img in file_pagine:
        pag = per_numero.get(n)
        if pag:
            offerte = (sb.table("v6_offerte").select("id")
                       .eq("pagina_id", pag["id"]).limit(1).execute().data)
            if offerte:
                print(f"  pagina {n}: gia' completata, salto")
                continue
        nome = os.path.basename(path)
        # Un tentativo precedente puo' aver caricato l'immagine prima di fermarsi.
        with open(path, "rb") as f:
            sb.storage.from_(BUCKET).upload(nome, f, {"content-type": "image/jpeg", "upsert": "true"})
        if not pag:
            pag = sb.table("v6_pagine").insert(
                {"volantino_id": vol["id"], "pagina_num": n, "immagine_path": nome}).execute().data[0]
        buf = io.BytesIO()
        riduci(img).save(buf, format="JPEG", quality=80)
        prodotti = chiedi_ai(ai, buf.getvalue())
        righe = []
        for p in prodotti:
            if not isinstance(p, dict) or not p.get("nome"):
                continue
            righe.append({
                "pagina_id": pag["id"], "marca": p.get("marca"),
                "nome_letto": str(p["nome"]).upper(),
                "quantita_valore": p.get("quantita_valore"),
                "quantita_unita": p.get("quantita_unita"),
                "prezzo": p.get("prezzo"), "promo": p.get("promo"),
                "confidenza": None, "verificato_ocr": False, "prodotto_id": None,
            })
        if not righe:
            print(f"  pagina {n}: 0 offerte (AI non ha letto prodotti, vado avanti)")
            continue
        inserite = sb.table("v6_offerte").insert(righe).execute().data
        if not inserite:
            raise RuntimeError(f"Pagina {n}: nessuna offerta salvata")
        print(f"  pagina {n}: {len(righe)} offerte")
    # Solo tutte le pagine con offerte salvate rendono completo il volantino.
    sb.table("v6_volantini").update({"pagine": len(file_pagine)}).eq("id", vol["id"]).execute()
    print(f"[completo] Promo {v['numero_promo']}/{anno}: {len(file_pagine)} pagine")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--scrivi", action="store_true")
    ap.add_argument("--promo", type=int, help="solo questo numero promo")
    args = ap.parse_args()

    elenco = leggi_elenco()
    if not elenco:
        print("ERRORE: nessun volantino Liguria/Piemonte nell'elenco (formato cambiato?)")
        sys.exit(2)
    for v in elenco:
        if args.promo and v["numero_promo"] != args.promo:
            continue
        print(f"Volantino promo {v['numero_promo']} id {v['leaflet_id']}: {v['dal']} -> {v['al']}")
        print(f"  PDF: {v['pdf_url']}")
        try:
            peso, pagine = scarica_e_crea_pagine(v)
        except Exception as e:
            print(f"ERRORE download/immagini: {e}")
            sys.exit(3)
        print(f"  scaricato {peso / 1e6:.1f} MB, {len(pagine)} pagine, es. {os.path.basename(pagine[0][1])}")
        if args.scrivi:
            scrivi_v6(v, pagine)
        else:
            print("  DRY RUN: nessuna scrittura su Supabase, nessuna chiamata AI.")


if __name__ == "__main__":
    main()

