import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Try with accent
r = requests.get(f"{url}/rest/v1/product?nome=ilike.%caff%C3%A8%&limit=10", headers=headers)
prods = r.json()
with open('caff_accents.json', 'w', encoding='utf-8') as f:
    json.dump(prods, f, indent=2, ensure_ascii=False)
print(f"With accent (caffè): {len(prods)} products")
for p in prods:
    print(f"  - {p['nome']}")