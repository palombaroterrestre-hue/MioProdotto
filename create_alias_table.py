import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("ERRORE: Manca SUPABASE_KEY nel file .env")
    exit(1)

# Extract project ref from URL
project_ref = SUPABASE_URL.replace("https://", "").split(".")[0]
print(f"Project: {project_ref}")

# Connect to Supabase
conn_str = f"postgresql://postgres:{SUPABASE_KEY}@db.{project_ref}.supabase.co:5432/postgres"
print(f"[1] Connessione a Supabase...")

try:
    conn = psycopg2.connect(conn_str)
    print("   Connesso!")
    
    cur = conn.cursor()
    
    # Create table
    print("[2] Creo tabella alias_product...")
    cur.execute("""
        CREATE TABLE alias_product (
          id SERIAL PRIMARY KEY,
          nome TEXT,
          prezzo NUMERIC,
          quantita_singola TEXT,
          percentuale_sconto NUMERIC,
          emoji TEXT,
          tipo_meccanica TEXT,
          inizio_validita TEXT,
          fine_validita TEXT,
          fonte_volantino_link TEXT,
          pagina_num INTEGER,
          file_pagina_intera TEXT,
          alias_name TEXT
        );
    """)
    print("   Tabella creata!")
    
    # Copy data
    print("[3] Copio dati da rilevazioni_v2...")
    cur.execute("""
        INSERT INTO alias_product (
          nome, prezzo, quantita_singola, percentuale_sconto, emoji, tipo_meccanica,
          inizio_validita, fine_validita, fonte_volantino_link, pagina_num, file_pagina_intera
        )
        SELECT 
          nome, prezzo, quantita_singola, percentuale_sconto, emoji, tipo_meccanica,
          inizio_validita, fine_validita, fonte_volantino_link, pagina_num, file_pagina_intera
        FROM rilevazioni_v2;
    """)
    print("   Dati copiati!")
    
    # Update sequence
    print("[4] Aggiorno sequenza ID...")
    cur.execute("SELECT setval('alias_product_id_seq', (SELECT MAX(id) FROM alias_product));")
    print("   Sequenza aggiornata!")
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM alias_product;")
    count = cur.fetchone()[0]
    print(f"\n[OK] Fatto! {count} record in alias_product")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERRORE: {e}")
    exit(1)