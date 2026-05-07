import os, requests
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Use encoded search
search_term = quote('caffè')
r = requests.get(f'{url}/rest/v1/product?nome.ilike.%25{search_term}%25&limit=20', headers=headers)
prods = r.json()
print(f'Search for "caffè": {len(prods)} results')
for p in prods[:15]:
    print(f"  - {p.get('nome')}")

print('\n=== Search with accent removed ===')
search_term2 = quote('caffe')  # no accent
r2 = requests.get(f'{url}/rest/v1/product?nome.ilike.%25{search_term2}%25&limit=20', headers=headers)
prods2 = r2.json()
print(f'Search for "caffe": {len(prods2)} results')
for p in prods2[:15]:
    print(f"  - {p.get('nome')}")