import os, requests
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')  # This is service role key

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Try using the pg_catalog to add column - need to use proper SQL execution
# Supabase doesn't expose direct SQL via REST for security, but let's try the storage or different endpoint

# Alternative: Check if we can use the "sql" endpoint
r = requests.post(
    f'{url}/rest/v1/rpc/sql',
    json={'query': 'ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT'},
    headers=headers
)
print(f"Method 1 (rpc/sql): {r.status_code} - {r.text[:200] if r.text else 'empty'}")

# Try with postgREST custom headers
r2 = requests.post(
    f'{url}/rest/v1/rpc/exec',
    json={'sql': 'ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT'},
    headers=headers
)
print(f"Method 2 (rpc/exec): {r2.status_code} - {r2.text[:200] if r2.text else 'empty'}")

# Try with direct auth as service role - try alternative endpoint
r3 = requests.post(
    f'{url}/database/v1/statements',
    json={'query': 'ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT'},
    headers=headers
)
print(f"Method 3 (database/v1): {r3.status_code} - {r3.text[:200] if r3.text else 'empty'}")