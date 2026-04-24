import os
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

# --- 1. CARICAMENTO CONFIGURAZIONI ---
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

# Inizializzazione Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = ollama.Client(host='https://api.ollama.com', headers={'Authorization': f'Bearer {API_KEY}'})

# Sessione HTTP con retry per maggiore affidabilità rete
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

# Percorso salvataggio immagini per la WebApp
PAGINE_OUTPUT = os.path.join(BASE_PATH, 'webapp_static', 'pagine_volantini')
if not os.path.exists(PAGINE_OUTPUT):
    os.makedirs(PAGINE_OUTPUT, exist_ok=True)

# --- 2. LOGICA DI COERENZA DATA (SINCRONIZZAZIONE ANNO) ---
def calcola_anno_corretto(gg_mm_str, anno_link, mese_link):
    """
    Sincronizza l'anno del link con il contenuto del PDF.
    Esempio: Link 2024/12 + PDF 02/01 => Anno 2025.
    """
    try:
        giorno, mese = gg_mm_str.split('/')
        mese_pdf = int(mese)
        mese_l = int(mese_link)
        anno_l = int(anno_link)

        # Se il volantino è caricato a Dicembre ma la validità è Gennaio, è l'anno successivo
        if mese_l == 12 and mese_pdf == 1:
            return f"{giorno}/{mese}/{anno_l + 1}"
        
        # Altrimenti usiamo l'anno della cartella di upload
        return f"{giorno}/{mese}/{anno_l}"
    except (ValueError, TypeError, AttributeError):
        return f"{gg_mm_str}/{datetime.now().year}"

# --- 3. FUNZIONE AI CON RETRY ---
def chiedi_a_gemma(prompt, image_bytes):
    max_tentativi = 3
    for i in range(max_tentativi):
        try:
            res = ai_client.chat(
                model='gemma4:31b-cloud',
                messages=[{'role': 'user', 'content': prompt, 'images': [image_bytes]}]
            )
            content = res.get('message', {}).get('content', '')
            # Estrazione JSON pulita tramite Regex
            match = re.search(r'\[\s*{.*}\s*\]|{\s*".*"\s*:\s*".*"\s*}', content, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except Exception as e:
            print(f"      [!] Errore AI (tentativo {i+1}): {e}")
            time.sleep(5)
    return None

# --- 4. ELABORAZIONE VOLANTINO ---
def elabora_volantino(url_volantino, anno_link, mese_link):
    nome_base = url_volantino.split('/')[-1].replace('.pdf', '')
    print(f"\n🚀 ANALISI: {nome_base}")
    
    try:
        response = http.get(url_volantino, timeout=30)
        response.raise_for_status()
        pagine_pdf = convert_from_bytes(response.content, dpi=300, poppler_path=POPPLER_PATH)
    except requests.RequestException as e:
        print(f"❌ Errore download {url_volantino}: {e}")
        return
    except Exception as e:
        print(f"❌ Errore download/conversione {url_volantino}: {e}")
        return
    
    if not pagine_pdf:
        print("⚠️ PDF senza pagine. Salto volantino.")
        return

    # 4.1 Estrazione Date dalla prima pagina
    buf_p1 = io.BytesIO()
    pagine_pdf[0].save(buf_p1, format='JPEG')
    prompt_date = "Estrai inizio e fine validità in JSON: {'inizio': 'GG/MM', 'fine': 'GG/MM'}. Solo numeri e slash."
    res_date = chiedi_a_gemma(prompt_date, buf_p1.getvalue())
    
    if not res_date:
        print("⚠️ Impossibile leggere date. Salto volantino.")
        return
    if not isinstance(res_date, dict) or not res_date.get('inizio') or not res_date.get('fine'):
        print("⚠️ Date incomplete/non valide. Salto volantino.")
        return

    data_inizio = calcola_anno_corretto(res_date['inizio'], anno_link, mese_link)
    data_fine = calcola_anno_corretto(res_date['fine'], anno_link, mese_link)
    print(f"📅 Validità Calcolata: {data_inizio} - {data_fine}")

    # 4.2 Processo Pagine
    for i, pagina in enumerate(pagine_pdf):
        num_pag = i + 1
        
        # Checkpoint Supabase: Evitiamo duplicati
        check = supabase.table("rilevazioni_v2").select("id", count="exact")\
            .eq("fonte_volantino_link", url_volantino).eq("pagina_num", num_pag).execute()
        
        if check.count and check.count > 0:
            print(f"  [skip] Pagina {num_pag} già presente.")
            continue

        print(f"  [work] Pagina {num_pag}...")
        nome_img = f"{nome_base}_p{num_pag}.jpg"
        pagina.save(os.path.join(PAGINE_OUTPUT, nome_img), 'JPEG')
        
        buf = io.BytesIO()
        pagina.save(buf, format='JPEG')
        
         # --- PROMPT CON LOGICA COMMERCIALE COMPLETA ---
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
        - rimuovi claim non di nome prodotto (es: "NOVITA", "SUPER PREZZO", "SOLO DA NOI").

        2) quantita_singola:
        - formato compatto senza spazi: "300G", "1KG", "1LT", "500ML", "6PZ".
        - se non leggibile: "N/D".

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
        
        if prodotti:
            batch = []
            for p in prodotti:
                # Forza il nome in MAIUSCOLO per uniformità database
                nome_prodotto = str(p.get('nome', 'N/D')).upper()
                
                batch.append({
                    "nome": nome_prodotto,
                    "prezzo": p.get('prezzo', 0),
                    "quantita_singola": p.get('quantita_singola', 'N/D'),
                    "percentuale_sconto": p.get('sconto_perc', 0),
                    "emoji": p.get('emoji', '🛒'),
                    "tipo_meccanica": p.get('tipo_meccanica', 'OFFERTA SEMPLICE'),
                    "inizio_validita": data_inizio,
                    "fine_validita": data_fine,
                    "fonte_volantino_link": url_volantino,
                    "pagina_num": num_pag,
                    "file_pagina_intera": nome_img
                })
            
            try:
                supabase.table("rilevazioni_v2").insert(batch).execute()
                print(f"    [OK] Pagina {num_pag}: {len(prodotti)} prodotti salvati.")
            except Exception as e:
                print(f"    [!] Errore Supabase: {e}")

# --- 5. ESECUZIONE DINAMICA (START DIC 2024 -> OGGI) ---
if __name__ == "__main__":
    BASE_URL = "https://www.ekomdiscount.it/wp-content/uploads"
    volantini_elaborati = 0
    anno_attuale = datetime.now().year
    
    # Iniziamo da Dicembre 2024 (per il primo volantino 2025) e proseguiamo
    config_scansione = [
        {"anno": "2024", "mesi": ["12"]},
        {"anno": "2025", "mesi": [f"{m:02d}" for m in range(1, 13)]}
    ]
    
    # Aggiungiamo anni successivi se presenti (es. 2026)
    if anno_attuale > 2025:
        for a in range(2026, anno_attuale + 1):
            config_scansione.append({"anno": str(a), "mesi": [f"{m:02d}" for m in range(1, 13)]})

    print(f"🔍 Avvio recupero storico totale (Target: Dic 2024 -> {anno_attuale})")

    for blocco in config_scansione:
        for mese in blocco["mesi"]:
            # Scouting dei PDF (Pattern EKOMPromo01...40)
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