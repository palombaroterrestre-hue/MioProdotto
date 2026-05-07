import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

# Try to delete table via REST API (might not work, needs SQL)
# First check if table exists
r = requests.get(f'{url}/rest/v1/product_aliases?limit=1', headers=headers)
print(f"Table exists: {r.status_code == 200}")

# Try alternate method - using postgrest to drop
# This typically requires a function or direct SQL access

# Try SQL execution via different endpoint
r2 = requests.post(
    f'{url}/rest/v1/rpc/exec_sql',
    json={'query': 'DROP TABLE IF EXISTS product_aliases CASCADE;'},
    headers=headers
)
print(f"SQL via rpc: {r2.status_code} - {r2.text[:200] if r2.text else 'empty'}")

# Alternative: try direct table delete via storage or other method
print("\nNote: Table deletion requires Supabase SQL Editor or admin access.")
print("Run this SQL in Supabase SQL Editor:")
print("DROP TABLE IF EXISTS product_aliases CASCADE;")
print("ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT;")