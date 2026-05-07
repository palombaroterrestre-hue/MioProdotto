import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BASE_PATH = r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto"

def upload_images():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    image_dir = os.path.join(BASE_PATH, "temp_pagine")
    images = list(Path(image_dir).glob("*.jpg"))
    
    print(f"Immagini: {len(images)}")
    
    success = 0
    for i, img in enumerate(images):
        print(f"[{i+1}/{len(images)}] {img.name}...", end=" ")
        
        url = f"{SUPABASE_URL}/storage/v1/object/volantini/{img.name}"
        data = img.read_bytes()
        
        # Try different upload method
        r = requests.post(
            url,
            headers={**headers, "Content-Type": "image/jpeg"},
            data=data
        )
        
        if r.status_code in [200, 201]:
            print("OK")
            success += 1
        else:
            print(f"ERR: {r.status_code} - {r.text[:100] if r.text else ''}")
    
    print(f"\nFatto: {success}/{len(images)}")

if __name__ == "__main__":
    upload_images()