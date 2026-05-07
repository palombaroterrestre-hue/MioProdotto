import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path
from pdf2image import convert_from_bytes
from PIL import Image

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BASE_PATH = os.getenv("BASE_PATH", r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto")
POPPLER_PATH = os.getenv("POPPLER_PATH", r"C:\poppler\Library\bin")

os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")

def scarica_pdf(url, headers, cache):
    if url in cache:
        return cache[url]
    try:
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code == 200:
            cache[url] = r.content
            return r.content
    except Exception as e:
        print(f"Errore: {e}")
    return None

def genera_immagini_mancanti():
    headers = {"apikey": SUPABASE_KEY}
    
    # Get all unique (url, page, filename) from rilevazioni_v2
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=file_pagina_intera,pagina_num,fonte_volantino_link&limit=10000",
        headers=headers
    )
    data = r.json()
    
    # Unique pages needed
    unique = {}
    for item in data:
        key = item["file_pagina_intera"]
        unique[key] = {
            "volantino_url": item["fonte_volantino_link"],
            "pagina_num": item["pagina_num"]
        }
    
    print(f"Totale pagine uniche richieste: {len(unique)}")
    
    # Check which files we already have locally
    output_dir = os.path.join(BASE_PATH, "temp_pagine")
    os.makedirs(output_dir, exist_ok=True)
    
    local_files = set(f.name for f in Path(output_dir).glob("*.jpg"))
    print(f"Immagini locali: {len(local_files)}")
    
    # Find missing
    missing = {k: v for k, v in unique.items() if k not in local_files}
    print(f"Immagini mancanti: {len(missing)}")
    
    if not missing:
        print("Tutte le immagini sono gia presenti!")
        return
    
    # Download PDFs and generate images
    pdf_cache = {}
    
    for i, (nome_file, info) in enumerate(missing.items()):
        volantino_url = info["volantino_url"]
        pagina_num = info["pagina_num"]
        
        print(f"[{i+1}/{len(missing)}] {nome_file}...")
        
        pdf_bytes = scarica_pdf(volantino_url, headers, pdf_cache)
        if not pdf_bytes:
            continue
            
        try:
            images = convert_from_bytes(
                pdf_bytes,
                first_page=pagina_num,
                last_page=pagina_num,
                dpi=150
            )
            
            if images:
                img_path = os.path.join(output_dir, nome_file)
                images[0].save(img_path, "JPEG", quality=85)
                print(f"  Salvato: {img_path}")
        except Exception as e:
            print(f"  Errore: {e}")
            continue
    
    print(f"\nFatto! Immagini in: {output_dir}")

if __name__ == "__main__":
    genera_immagini_mancanti()