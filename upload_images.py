import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

BASE_PATH = os.getenv("BASE_PATH", r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto")
IMAGE_DIR = os.path.join(BASE_PATH, "temp_pagine")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def upload_images():
    image_files = list(Path(IMAGE_DIR).glob("*.jpg"))
    print(f"Trovati {len(image_files)} immagini")
    
    success = 0
    errors = 0
    
    for i, img_path in enumerate(image_files):
        print(f"[{i+1}/{len(image_files)} Carico {img_path.name}...")
        
        with open(img_path, "rb") as f:
            file_data = f.read()
        
        r = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/volantini/{img_path.name}",
            headers=headers,
            files={"file": (img_path.name, file_data, "image/jpeg")}
        )
        
        if r.status_code in [200, 201]:
            print(f"   OK: {r.status_code}")
            success += 1
        else:
            print(f"   ERRORE: {r.status_code} - {r.text[:100]}")
            errors += 1
    
    print(f"\nFatto! Successi: {success}, Errori: {errors}")
    
    # Show public URLs
    print("\nURL pubblici:")
    for img_path in image_files[:3]:
        print(f"{SUPABASE_URL}/storage/v1/object/public/volantini/{img_path.name}")

if __name__ == "__main__":
    upload_images()