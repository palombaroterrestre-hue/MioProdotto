import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Try different connection string formats
project_ref = SUPABASE_URL.replace("https://", "").split(".")[0]

# Format 1: Standard
conn_str_1 = f"postgresql://postgres:{SUPABASE_KEY}@db.{project_ref}.supabase.co:5432/postgres"

# Format 2: With sslmode
conn_str_2 = f"postgresql://postgres:{SUPABASE_KEY}@db.{project_ref}.supabase.co:5432/postgres?sslmode=require"

# Try direct connection to Supabase through the API
# Or try via the transitory host

hosts_to_try = [
    f"db.{project_ref}.supabase.co",
    f"postgres.{project_ref}.supabase.co",
    "localhost",
]

for host in hosts_to_try:
    try:
        conn_str = f"postgresql://postgres:{SUPABASE_KEY}@{host}:5432/postgres?sslmode=require"
        print(f"Trying: {host}...")
        conn = psycopg2.connect(conn_str, connect_timeout=5)
        print(f"Connected to {host}!")
        
        cur = conn.cursor()
        
        # Check if column exists first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'product' AND column_name = 'alias';")
        result = cur.fetchone()
        
        if result:
            print(f"Column 'alias' already exists!")
        else:
            print("Adding alias column...")
            cur.execute("ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT;")
            conn.commit()
            print("Column added!")
        
        conn.close()
        break
        
    except Exception as e:
        print(f"  Failed: {e}")
        continue
else:
    print("Could not connect to any host")