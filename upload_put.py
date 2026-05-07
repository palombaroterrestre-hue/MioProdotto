import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

url = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
key = os.getenv('SUPABASE_SERVICE_KEY')
base = r"C:\Users\Bruss\OneDrive\Images\Nuova cartella\OneDrive\MioProdotto"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}"
}

images = list(Path(base, "temp_pagine").glob("*.jpg"))
print(f"Immagini: {len(images)}")

for i, img in enumerate(images):
    print(f"[{i+1}/{len(images)}] {img.name}...", end=" ")
    
    # Try PUT (upsert)
    r = requests.put(
        f"{url}/storage/v1/object/volantini/{img.name}",
        headers=headers,
        data=img.read_bytes()
    )
    
    if r.status_code in [200, 201]:
        print("OK")
    else:
        print(f"ERR: {r.status_code}")

print("Fatto!")