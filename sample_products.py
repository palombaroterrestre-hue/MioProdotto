import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get count and sample of products with alphabetical names
r = requests.get(f'{url}/rest/v1/product?select=nome&order=nome&limit=30&offset=100', headers=headers)
prods = r.json()
print(f'Products (sample from offset 100):')
for p in prods:
    print(f"  {p.get('nome')}")