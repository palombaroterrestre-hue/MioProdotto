import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Check if alias column exists
r = requests.get(f'{url}/rest/v1/product?select=nome,alias&limit=3', headers=headers)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")