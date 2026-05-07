import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

project_ref = SUPABASE_URL.replace("https://", "").split(".")[0]
conn_str = f"postgresql://postgres:{SUPABASE_KEY}@db.{project_ref}.supabase.co:5432/postgres"

print(f"Connecting to Supabase...")

try:
    conn = psycopg2.connect(conn_str)
    print("Connected!")
    
    cur = conn.cursor()
    
    # Add alias column
    print("Adding alias column to product table...")
    cur.execute("ALTER TABLE product ADD COLUMN IF NOT EXISTS alias TEXT;")
    print("Column added!")
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'product' AND column_name = 'alias';")
    result = cur.fetchone()
    print(f"Verification: {result}")
    
    cur.close()
    conn.close()
    
    print("\nDone! Column 'alias' added to product table.")
    
except Exception as e:
    print(f"ERROR: {e}")