import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Search for DEK LAVAZZA
r = requests.get(f"{url}/rest/v1/product?nome=ilike.%DEK%LAVAZZA%&limit=20", headers=headers)
prods = r.json()
with open('dek_lavazza.json', 'w', encoding='utf-8') as f:
    json.dump(prods, f, indent=2, ensure_ascii=False)
print(f"DEK LAVAZZA: {len(prods)} products")
for p in prods:
    print(f"  - {p['nome']}")