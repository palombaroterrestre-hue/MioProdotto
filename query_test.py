import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Prefer': 'return=representation'}

# Try different query syntax
tests = [
    ('eq', 'MISTO PER SOFFRITTO'),
    ('ilike', 'MISTO%'),
    ('like', '%MISTO%'),
    ('ilike', '%caff%'),
]

for op, val in tests:
    r = requests.get(f'{url}/rest/v1/product?nome={op}.{val}&limit=3', headers=headers)
    prods = r.json()
    print(f"nome={op}.{val}: {len(prods)} results")
    if prods:
        print(f"  -> {prods[0].get('nome')}")