import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Check rilevazioni_v2
r = requests.get(f'{url}/rest/v1/rilevazioni_v2?nome.ilike.%25CAFF%25&limit=10', headers=headers)
prods = r.json()
print(f'rilevazioni_v2 - CAFF: {len(prods)} products')
for p in prods[:10]:
    print(f"  - {p.get('nome')}")

# Check product table
print('\nproduct table - CAFF:')
r2 = requests.get(f'{url}/rest/v1/product?nome.ilike.%25CAFF%25&limit=10', headers=headers)
prods2 = r2.json()
print(f'Found: {len(prods2)}')
for p in prods2[:10]:
    print(f"  - {p.get("nome")}")