import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get all distinct product names that contain 'espresso' directly from DB
r = requests.get(f'{url}/rest/v1/rilevazioni_v2?select=nome&nome=ilike.*espresso.*&limit=50', headers=headers)
prods = r.json()
print(f'ESPRESSO in rilevazioni_v2: {len(prods)} products')
for p in prods[:20]:
    print(f"  - {p.get('nome')}")

print('\n--- Compare with product table ---')
r2 = requests.get(f'{url}/rest/v1/product?select=nome&nome=ilike.*espresso.*&limit=50', headers=headers)
prods2 = r2.json()
print(f'ESPRESSO in product: {len(prods2)} products')
for p in prods2[:20]:
    print(f"  - {p.get("nome")}")