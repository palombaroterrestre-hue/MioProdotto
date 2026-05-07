import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

r = requests.get(f'{url}/rest/v1/product?nome.ilike.*dek*', headers=headers)
prods = r.json()
with open('dek_products.json', 'w', encoding='utf-8') as f:
    json.dump(prods[:3], f, indent=2, ensure_ascii=False)
print(f"Saved {len(prods[:3])} products to dek_products.json")