import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Search for LAVAZZA specifically
r = requests.get(f'{url}/rest/v1/product?nome.ilike.%25LAVAZZA%25&limit=20', headers=headers)
prods = r.json()
print(f'Products with LAVAZZA: {len(prods)}')
for p in prods:
    print(f"  - {p['nome']}")

# Search for ESPRESSO
print('\nProducts with ESPRESSO:')
r2 = requests.get(f'{url}/rest/v1/product?nome.ilike.%25ESPRESSO%25&limit=20', headers=headers)
prods2 = r2.json()
print(f'Found: {len(prods2)}')
for p in prods2[:10]:
    print(f"  - {p['nome']}")