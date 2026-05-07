import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test table creation via SQL
# Note: Supabase Python client doesn't support DDL directly
# We use the postgres function to execute raw SQL if available

# Check if we can create via rpc
try:
    result = supabase.rpc('exec_sql', {'query': 'SELECT 1'}).execute()
    print("RPC available - can execute SQL")
except Exception as e:
    print(f"RPC not available: {e}")

print("\nTo create a new table, you have these options:")
print("1. Go to https://supabase.com/dashboard/project/fsxctxzzifohmbgqwcxk/editor")
print("2. Use Supabase SQL Editor with your credentials")
print("\nOr I can create a script that inserts a test record into an existing table")