import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get first 5 products to see what data looks like
r = requests.get(f'{url}/rest/v1/product?select=nome,prezzo&limit=5', headers=headers)
prods = r.json()
print('First 5 products in DB:')
for p in prods:
    print(f"  nome: '{p.get('nome')}', prezzo: {p.get('prezzo')}")

# Count total
r2 = requests.get(f'{url}/rest/v1/product?select=count', headers=headers)
print(f'\nTotal products: {r2.json()}')