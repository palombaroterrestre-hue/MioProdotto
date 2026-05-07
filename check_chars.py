import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Check exact characters in CAFFE DEK
r = requests.get(f"{url}/rest/v1/product?nome=ilike.%DEK%", headers=headers)
prods = r.json()
print(f"DEK products: {len(prods)}")
for p in prods:
    nome = p['nome']
    print(f"  nome: {repr(nome)}")
    print(f"  contains 'CAFFE': {'CAFFE' in nome}")
    print(f"  bytes: {[hex(ord(c)) for c in nome[:10]]}")
    print()