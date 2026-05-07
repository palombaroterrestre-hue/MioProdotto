import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}

# Try adding column via pg_catalog
# Try using the alter table via POST to a different endpoint

# Method 1: Try with different approach - check if there's a way to run SQL
# Since direct SQL doesn't work, try checking if there's a migration endpoint

# Alternative: Try table insert with the new column to trigger creation
# This won't work - need SQL

# Let's try the SQL function approach differently
import json

# Try calling a custom function if available
try:
    r = requests.post(
        f"{url}/rest/v1/rpc/alter_table_column",
        json={"table_name": "product", "column_name": "alias", "column_type": "text"},
        headers=headers
    )
    print(f"Method 1: {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"Method 1 error: {e}")

# Check tables info
r2 = requests.get(f'{url}/rest/v1/', headers=headers)
print(f"\nAvailable endpoints (partial): {r2.text[:500]}")