import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get table schema
r = requests.get(f'{url}/rest/v1/product?select=*&limit=1', headers=headers)
prods = r.json()
if prods:
    with open('schema_check.json', 'w', encoding='utf-8') as f:
        json.dump(prods[0], f, indent=2, ensure_ascii=False)
    print("Schema saved")

# Also check if there's an issue with column 'nome' - check directly with exact match
r2 = requests.get(f'{url}/rest/v1/product?nome=eq.MISTO PER SOFFRITTO', headers=headers)
prods2 = r2.json()
print(f"Exact match 'MISTO PER SOFFRITTO': {len(prods2)}")