import os
import sys
import json
import ollama
import io
import re
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
from requests.adapters import HTTPAdapter
from supabase import create_client, Client
from urllib3.util.retry import Retry

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("GEMMA_API_KEY")
BASE_PATH = os.getenv("BASE_PATH")
POPPLER_PATH = os.getenv("POPPLER_PATH")

missing_env = [
    key for key, value in {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "GEMMA_API_KEY": API_KEY,
        "BASE_PATH": BASE_PATH,
        "POPPLER_PATH": POPPLER_PATH,
    }.items() if not value
]
if missing_env:
    raise RuntimeError(f"Variabili .env mancanti: {', '.join(missing_env)}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = ollama.Client(host='https://api.ollama.com', headers={'Authorization': f'Bearer {API_KEY}'})


def esegui_supabase_con_retry(callable_query, descrizione="operazione Supabase", tentativi=3, attesa_base=2):
    for tentativo in range(1, tentativi + 1):
        try:
            return callable_query().execute()
        except Exception as e:
            ultimo_tentativo = tentativo == tentativi
            print(f"    [!] {descrizione} fallita (tentativo {tentativo}/{tentativi}): {e}")
            if ultimo_tentativo:
                print(f"    [x] {descrizione} non disponibile. Continuo senza bloccare il processo.")
                return None
            time.sleep(attesa_base * tentativo)


def upload_immagine_storage(filename, image_path, volantino_url, pagina_num):
    try:
        with open(image_path, "rb") as f:
            supabase.storage.from_("volantini").upload(
                filename, f, {"content-type": "image/jpeg", "upsert": "true"}
            )
        image_url = f"{SUPABASE_URL}/storage/v1/object/public/volantini/{filename}"
        supabase.table("volantino_pagine").upsert(
            {"nome_file": filename, "image_url": image_url, "volantino_url": volantino_url, "pagina_num": pagina_num},
            on_conflict="nome_file",
        ).execute()
        return True
    except Exception as e:
        print(f"    [!] Upload immagine fallito: {e}")
        return False


def estrai_json_da_risposta_ai(content):
    if not content:
        return None
    try:
        return json.loads(content)
    except Exception:
        pass
    start_arr = content.find('[')
    end_arr = content.rfind(']')
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidate = content[start_arr:end_arr + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    start_obj = content.find('{')
    end_obj = content.rfind('}')
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidate = content[start_obj:end_obj + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None
    return None


http = requests.Session()
http_retry = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET"],
    raise_on_status=False,
)
http_adapter = HTTPAdapter(max_retries=http_retry)
http.mount("https://", http_adapter)
http.mount("http://", http_adapter)

PAGINE_OUTPUT = os.path.join(BASE_PATH, 'webapp_static', 'pagine_volantini')
if not os.path.exists(PAGINE_OUTPUT):
    os.makedirs(PAGINE_OUTPUT, exist_ok=True)

TABLE = "rilevazioni_v4"


def ggmm_to_iso(gg_mm_str, anno_link, mese_link):
    try:
        giorno, mese = gg_mm_str.split('/')
        mese_pdf = int(mese)
        mese_l = int(mese_link)
        anno_l = int(anno_link)
        if mese_l == 12 and mese_pdf == 1:
            anno = anno_l + 1
        else:
            anno = anno_l
        return f"{anno:04d}-{mese_pdf:02d}-{int(giorno):02d}"
    except (ValueError, TypeError, AttributeError):
        return datetime.now().strftime("%Y-%m-%d")


def chiedi_a_gemma(prompt, image_bytes):
    max_tentativi = 3
    for i in range(max_tentativi):
        try:
            res = ai_client.chat(
                model='gemma4:31b-cloud',
                messages=[{'role': 'user', 'content': prompt, 'images': [image_bytes]}]
            )
            content = res.get('message', {}).get('content', '')
            return estrai_json_da_risposta_ai(content)
        except Exception as e:
            print(f"      [!] Errore AI (tentativo {i+1}): {e}")
            time.sleep(5)
    return None


def riduci_per_ai(img, max_larghezza=1400):
    w, h = img.size
    if w > max_larghezza:
        rapporto = max_larghezza / w
        return img.resize((max_larghezza, int(h * rapporto)), 3)
    return img


def elabora_volantino(url_volantino, anno_link, mese_link):
    nome_base = url_volantino.split('/')[-1].replace('.pdf', '')
    print(f"\n🚀 ANALISI: {nome_base}")

    try:
        response = http.get(url_volantino, timeout=30)
        response.raise_for_status()
        pagine_pdf = convert_from_bytes(response.content, dpi=400, poppler_path=POPPLER_PATH)
    except requests.RequestException as e:
        print(f"❌ Errore download {url_volantino}: {e}")
        return
    except Exception as e:
        print(f"❌ Errore download/conversione {url_volantino}: {e}")
        return

    if not pagine_pdf:
        print("⚠️ PDF senza pagine. Salto volantino.")
        return

    buf_p1 = io.BytesIO()
    riduci_per_ai(pagine_pdf[0]).save(buf_p1, format='JPEG', quality=80)
    prompt_date = "Estrai inizio e fine validità in JSON: {'inizio': 'GG/MM', 'fine': 'GG/MM'}. Solo numeri e slash."
    res_date = chiedi_a_gemma(prompt_date, buf_p1.getvalue())

    if not res_date:
        print("⚠️ Impossibile leggere date. Salto volantino.")
        return
    if not isinstance(res_date, dict) or not res_date.get('inizio') or not res_date.get('fine'):
        print("⚠️ Date incomplete/non valide. Salto volantino.")
        return

    data_inizio = ggmm_to_iso(res_date['inizio'], anno_link, mese_link)
    data_fine = ggmm_to_iso(res_date['fine'], anno_link, mese_link)
    print(f"📅 Validità: {data_inizio} - {data_fine}")

    for i, pagina in enumerate(pagine_pdf):
        num_pag = i + 1

        check = esegui_supabase_con_retry(
            lambda: supabase.table(TABLE)
            .select("id", count="exact")
            .eq("link_volantino", url_volantino)
            .eq("pagina_num", num_pag),
            descrizione=f"controllo duplicati pagina {num_pag}",
        )
        if check is None:
            print(f"  [skip] Pagina {num_pag}: Supabase non raggiungibile, salto in sicurezza.")
            continue

        if check.count and check.count > 0:
            print(f"  [skip] Pagina {num_pag} già presente.")
            continue

        print(f"  [work] Pagina {num_pag}...")
        nome_img = f"{nome_base}_p{num_pag}.jpg"
        local_path = os.path.join(PAGINE_OUTPUT, nome_img)
        pagina.save(local_path, 'JPEG')
        upload_immagine_storage(nome_img, local_path, url_volantino, num_pag)

        buf = io.BytesIO()
        larghezza_ai = int(pagina.width * 0.75) if num_pag == 1 else 1400
        riduci_per_ai(pagina, larghezza_ai).save(buf, format='JPEG', quality=80)

        prompt_prodotti = """
        Sei un estrattore OCR strutturato per volantini promozionali.

        OBIETTIVO
        Estrai SOLO i prodotti realmente presenti nella pagina e restituisci ESCLUSIVAMENTE un JSON array valido.

        FORMATO OUTPUT (OBBLIGATORIO)
        [
          {
            "nome": "STRINGA",
            "quantita_singola": "STRINGA",
            "tipo_meccanica": "A PARTIRE DA|SCONTO PERCENTUALE|3*2|2*1|OFFERTA SEMPLICE",
            "prezzo": 0.00,
            "sconto_perc": 0,
            "emoji": "STRINGA"
          }
        ]

        REGOLE DI ESTRAZIONE
        1) nome:
        - usa solo il nome prodotto principale (tipicamente in grassetto).
        - MAIUSCOLO.
        - rimuovi claim non di nome prodotto (es: "NOVITA'", "SUPER PREZZO", "SOLO DA NOI").

        2) quantita_singola:
        - formato compatto senza spazi: "300G", "1KG", "1LT", "500ML", "6PZ", "80GX2".
        - se non leggibile metti sempre "N/D".
        Se il formato della quantità non rientra in uno standard chiaro (es. #T, #.#T), non inventare. Mantieni lo stesso standard per i record simili, ad esempio "KG 2" e "2 KG" sarà sempre "2KG"
        Se dubbio, usa solo "N/D" senza campi aggiuntivi.

        3) tipo_meccanica (scegli UNA sola voce):
        - "A PARTIRE DA" -> se esplicitamente indicato o prezzi variabili per varianti.
        - "SCONTO PERCENTUALE" -> se compare una % di sconto.
        - "3*2" -> promo 3 al prezzo di 2.
        - "2*1" -> promo 2 al prezzo di 1.
        - altrimenti "OFFERTA SEMPLICE".

        4) prezzo:
        - prezzo finale visibile del prodotto.
        - numero decimale con punto, senza simbolo valuta.
        - esempio: 1.99

        5) sconto_perc:
        - solo numero intero senza simbolo %.
        - se assente: 0.

        6) emoji (scegli la più coerente):
        - 🥛 Latticini/Latte | 🧀 Formaggi | 🍖 Salumi/Carne | 🐟 Pesce
        - 🍎 Ortofrutta | 🍞 Pane/Sostituti | 🍝 Pasta/Riso/Farina
        - ☕ Caffè/Tè | 🍪 Biscotti/Dolci | 🥤 Bevande/Vino/Birra
        - 🧊 Surgelati | 🥫 Conserve/Olio/Sughi
        - 🧻 Igiene casa/Persona | 🐶 Animali
        - 🛒 Generico se dubbio

        REGOLE DI QUALITA
        - Non inventare prodotti non visibili.
        - Non aggiungere campi extra.
        - Non aggiungere testo fuori dal JSON.
        - Se trovi un solo prodotto, restituisci comunque un array con 1 oggetto.
        - Se non trovi prodotti validi, restituisci [].

        Rispondi ORA con solo JSON valido.
        """
        prodotti = chiedi_a_gemma(prompt_prodotti, buf.getvalue())
        if isinstance(prodotti, dict):
            prodotti = [prodotti]

        if not prodotti:
            print(f"    ⚠️ AI non ha restituito prodotti per pagina {num_pag}")
            continue

        batch = []
        for p in prodotti:
            nome_prodotto = str(p.get('nome', 'N/D')).upper()
            emoji = p.get('emoji', '🛒')

            categoria_map = {
                '🥛': 'LATTICINI', '🧀': 'FORMAGGI', '🍖': 'CARNE', '🐟': 'PESCE',
                '🍎': 'ORTOFRUTTA', '🍞': 'PANE', '🍝': 'PASTA',
                '☕': 'CAFFE', '🍪': 'DOLCI', '🥤': 'BEVANDE',
                '🧊': 'SURGELATI', '🥫': 'CONSERVE',
                '🧻': 'IGIENE', '🐶': 'ANIMALI',
            }
            categoria = categoria_map.get(emoji, 'GENERICO')

            batch.append({
                "nome_prodotto": nome_prodotto,
                "prezzo": p.get('prezzo', 0),
                "sconto": p.get('sconto_perc', 0),
                "quantita": p.get('quantita_singola', 'N/D'),
                "tipo_meccanica": p.get('tipo_meccanica', 'OFFERTA SEMPLICE'),
                "inizio_promozione": data_inizio,
                "fine_promozione": data_fine,
                "link_volantino": url_volantino,
                "pagina_num": num_pag,
                "file_pagina_intera": nome_img,
                "categoria": categoria,
            })

        try:
            inserimento = esegui_supabase_con_retry(
                lambda: supabase.table(TABLE).insert(batch),
                descrizione=f"salvataggio pagina {num_pag}",
            )
            if inserimento is not None:
                print(f"    [OK] Pagina {num_pag}: {len(prodotti)} prodotti salvati.")
            else:
                print(f"    [!] Pagina {num_pag} non salvata per indisponibilità Supabase.")
        except Exception as e:
            print(f"    [!] Errore inatteso in fase di salvataggio: {e}")


if __name__ == "__main__":
    BASE_URL = "https://www.ekomdiscount.it/wp-content/uploads"

    if len(sys.argv) > 1:
        url = sys.argv[1]
        m = re.search(r'/(\d{4})/(\d{2})/', url)
        if m:
            elabora_volantino(url, m.group(1), m.group(2))
        else:
            print("URL non valido. Formato atteso: .../YYYY/MM/...")
    else:
        volantini_elaborati = 0
        anno_attuale = datetime.now().year

        config_scansione = [
            {"anno": "2023", "mesi": ["12"]},
            {"anno": "2024", "mesi": [f"{m:02d}" for m in range(1, 13)]},
            {"anno": "2025", "mesi": [f"{m:02d}" for m in range(1, 13)]}
        ]

        if anno_attuale > 2025:
            for a in range(2026, anno_attuale + 1):
                config_scansione.append({"anno": str(a), "mesi": [f"{m:02d}" for m in range(1, 13)]})

        print(f"🔍 Avvio recupero storico totale (Target: Dic 2023 -> {anno_attuale})")

        for blocco in config_scansione:
            for mese in blocco["mesi"]:
                for p in range(1, 41):
                    url = f"{BASE_URL}/{blocco['anno']}/{mese}/EKOMPromo{p:02d}-LGPM.pdf"
                    try:
                        r = http.head(url, timeout=3, allow_redirects=True)
                        if r.status_code == 200:
                            elabora_volantino(url, blocco['anno'], mese)
                            volantini_elaborati += 1
                    except requests.RequestException:
                        continue

        print(f"\n🏁 Processo completato. Totale volantini gestiti: {volantini_elaborati}")
