import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def populate_table():
    # Get unique pages from rilevazioni_v2
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=file_pagina_intera,pagina_num,fonte_volantino_link&limit=5000",
        headers={"apikey": SUPABASE_KEY}
    )
    data = r.json()
    
    # Build unique records
    unique = {}
    for item in data:
        nome_file = item["file_pagina_intera"]
        if nome_file not in unique:
            unique[nome_file] = {
                "nome_file": nome_file,
                "pagina_num": item["pagina_num"],
                "volantino_url": item["fonte_volantino_link"],
                "image_url": f"{SUPABASE_URL}/storage/v1/object/public/volantini/{nome_file}",
                "checked": False
            }
    
    print(f"Inserisco {len(unique)} record...")
    
    # Insert in batches
    records = list(unique.values())
    batch_size = 50
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/volantino_pagine",
            headers=headers,
            json=batch
        )
        print(f"  Batch {i//batch_size + 1}: {r.status_code}")
        if r.status_code not in [200, 201]:
            print(f"    Errore: {r.text[:200]}")
    
    # Verify
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/volantino_pagine?select=id&limit=1",
        headers={"apikey": SUPABASE_KEY}
    )
    print(f"\nVerifica: {r.status_code}")
    
    # Count
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/volantino_pagine?select=nome_file",
        headers={"apikey": SUPABASE_KEY}
    )
    records = r.json()
    print(f"Totale record: {len(records)}")
    
    # Show sample URLs
    print("\nSample URL:")
    if records:
        first = records[0]
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/volantino_pagine?nome_file=eq.{first['nome_file']}&select=image_url",
            headers={"apikey": SUPABASE_KEY}
        )
        print(r.json())

if __name__ == "__main__":
    populate_table()