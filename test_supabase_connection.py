import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}...")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing connection...")
result = supabase.table("rilevazioni_v2").select("*").limit(1).execute()

if result.data is not None:
    print(f"Connected! Query returned {len(result.data)} record(s)")
else:
    print("Connection successful but no data returned")