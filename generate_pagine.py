import os
import sys
import requests
import json
from dotenv import load_dotenv

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BASE_PATH = os.getenv("BASE_PATH", r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto")
POPPLER_PATH = os.getenv("POPPLER_PATH", r"C:\poppler\Library\bin")

os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")

from pdf2image import convert_from_bytes
from PIL import Image

def scarica_e_genera_immagini():
    headers = {"apikey": SUPABASE_KEY}
    
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=fonte_volantino_link,pagina_num,file_pagina_intera&limit=5000",
        headers=headers
    )
    data = r.json()
    
    unique = {}
    for item in data:
        key = item["file_pagina_intera"]
        unique[key] = {
            "volantino_url": item["fonte_volantino_link"],
            "pagina_num": item["pagina_num"]
        }
    
    print(f"Trovati {len(unique)} pagine uniche")
    
    output_dir = os.path.join(BASE_PATH, "temp_pagine")
    os.makedirs(output_dir, exist_ok=True)
    
    pdfs_scaricati = {}
    
    for i, (nome_file, info) in enumerate(unique.items()):
        volantino_url = info["volantino_url"]
        pagina_num = info["pagina_num"]
        
        print(f"[{i+1}/{len(unique)}] {nome_file}...")
        
        if volantino_url not in pdfs_scaricati:
            print(f"  Scarico PDF: {volantino_url[:50]}...")
            try:
                r = requests.get(volantino_url, headers=headers, timeout=60)
                if r.status_code != 200:
                    print(f"  Errore download: {r.status_code}")
                    continue
                pdf_bytes = r.content
                pdfs_scaricati[volantino_url] = pdf_bytes
                print(f"  PDF scaricato: {len(pdf_bytes)} bytes")
            except Exception as e:
                print(f"  Errore: {e}")
                continue
        else:
            print(f"  PDF gia scaricato, riutilizzo")
            pdf_bytes = pdfs_scaricati[volantino_url]
        
        print(f"  Estraggo pagina {pagina_num}...")
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
            else:
                print("  Nessuna immagine generata")
                
        except Exception as e:
            print(f"  Errore estrazione: {e}")
            continue
    
    print(f"\nFatto! Immagini in: {output_dir}")
    return output_dir

if __name__ == "__main__":
    scarica_e_genera_immagini()