import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Simple query for CAFFE
r = requests.get(f"{url}/rest/v1/product?nome=ilike.%CAFFE%&limit=10", headers=headers)
prods = r.json()

with open('caff_test.json', 'w', encoding='utf-8') as f:
    json.dump(prods, f, indent=2, ensure_ascii=False)
print(f"CAFFE: {len(prods)} products")
for p in prods:
    print(f"  {p['nome']}")