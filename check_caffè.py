import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Search for caffè products
r = requests.get(f'{url}/rest/v1/product?nome.ilike.%25CAFF%25&order=fine_validita.desc&limit=30', headers=headers)
prods = r.json()
print(f'Found {len(prods)} products with CAFF')
for p in prods[:20]:
    print(f"  {p['nome']}")

print('\n=== Alias CAFFE ===')
r2 = requests.get(f'{url}/rest/v1/product_aliases?or=(canonical_name.ilike.%25CAFFE%25,alias_name.ilike.%25CAFFE%25)&limit=20', headers=headers)
aliases = r2.json()
print(f'Found {len(aliases)} aliases')
for a in aliases[:15]:
    print(f"  {a['alias_name']} -> {a['canonical_name']}")