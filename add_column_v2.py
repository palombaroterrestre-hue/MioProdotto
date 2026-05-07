import os
import requests
from dotenv import load_dotenv
load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

# Service role key should have full access - try different approach
# Use the "pg" schema directly via a function

# Check what functions exist
r = requests.get(
    f'{url}/rest/v1/rpc/',
    headers={'apikey': key, 'Authorization': f'Bearer {key}'}
)
print(f"Available RPC functions: {r.status_code}")

# Try to use the "pg" extension or execute directly
# Let me try with the correct format for Supabase

# Another approach - create a simple SQL function in the database first, then call it
# For now, let's try using postgREST with the correct parameters

# Most likely, the issue is that we need to use the "anon" key with RLS disabled or 
# we need to enable a specific function

# Let me try one more thing - using the management API
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# Try to create a simple function that adds the column
create_func_sql = """
CREATE OR REPLACE FUNCTION add_column_if_not_exists()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'product' AND column_name = 'alias'
  ) THEN
    ALTER TABLE product ADD COLUMN alias TEXT;
  END IF;
END $$;
"""

# Try executing as a function call
r = requests.post(
    f'{url}/rest/v1/rpc/add_column_if_not_exists',
    json={},
    headers=headers
)
print(f"Execute function: {r.status_code} - {r.text[:300] if r.text else 'empty'}")

# Check if it worked
r2 = requests.get(f'{url}/rest/v1/product?select=nome,alias&limit=1', headers=headers)
print(f"Check column: {r2.status_code} - {r2.text[:200] if r2.text else 'empty'}")