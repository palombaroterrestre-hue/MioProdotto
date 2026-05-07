import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Search with proper case-insensitive
r = requests.get(f'{url}/rest/v1/product?select=nome&or=(nome.eq.LAVAZZA,nome.eq.lavazza,nome.ilike.%LAVAZZA%)&limit=20', headers=headers)
prods = r.json()
print(f'LAVAZZA exact/case-insensitive: {len(prods)}')
for p in prods:
    print(f"  - {p.get('nome')}")

# Try with different patterns  
print('\nTry *LAVAZZA*:')
r2 = requests.get(f'{url}/rest/v1/product?nome=ilike.*lavazza.*', headers=headers)
prods2 = r2.json()
print(f'Found: {len(prods2)}')
for p in prods2[:10]:
    print(f"  - {p.get('nome')}")