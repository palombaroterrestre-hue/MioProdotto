import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Delete product_aliases table
r = requests.delete(f'{url}/rest/v1/product_aliases', headers=headers)
print(f"Delete product_aliases: {r.status_code}")

# Add alias column to product table
r2 = requests.post(f'{url}/rest/v1/rpc/exec_sql', json={'query': 'ALTER TABLE product ADD COLUMN alias TEXT'}, headers=headers)
print(f"Add alias column: {r2.status_code} - {r2.text[:200]}")