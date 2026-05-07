import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get first product raw
r = requests.get(f'{url}/rest/v1/product?select=nome&limit=1', headers=headers)
prod = r.json()[0]
nome = prod['nome']
print(f"Raw nome: {repr(nome)}")
print(f"Bytes: {[hex(ord(c)) for c in nome]}")
print(f"Contains 'caff': {'caff' in nome.lower()}")