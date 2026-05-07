import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BASE_PATH = r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto"

def upload_all_images():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    image_dir = os.path.join(BASE_PATH, "temp_pagine")
    images = list(Path(image_dir).glob("*.jpg"))
    
    print(f"Immagini da caricare: {len(images)}")
    
    success = 0
    for i, img in enumerate(images):
        print(f"[{i+1}/{len(images)}] {img.name}...")
        
        with open(img, "rb") as f:
            data = f.read()
        
        r = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/volantini/{img.name}",
            headers=headers,
            files={"file": (img.name, data, "image/jpeg")}
        )
        
        if r.status_code in [200, 201]:
            success += 1
            print(f"  OK")
        else:
            print(f"  ERRORE: {r.status_code}")
    
    print(f"\nFatte! {success}/{len(images)} immagini caricate")

if __name__ == "__main__":
    upload_all_images()