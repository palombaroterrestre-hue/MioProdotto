import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Try using supabase client to execute SQL
try:
    from supabase import create_client, Client
    supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    # Try to execute SQL via rpc if available
    # First check if there's a function we can use
    result = supabase.rpc('pg_catalog.alter_table', {
        'arg': {}
    }).execute()
    print(f"RPC result: {result}")
except Exception as e:
    print(f"Error: {e}")
    print("\nCannot add column via API - requires Supabase SQL Editor or admin access.")
    print("\nPlease run in Supabase SQL Editor:")
    print("ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT;")