import socket
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Risolvi IP per db.fsxctxzzifohmbgqwcxk.supabase.co
print("[1] Risolvo IP...")
try:
    ip = socket.gethostbyname("db.fsxctxzzifohmbgqwcxk.supabase.co")
    print(f"   IP: {ip}")
except Exception as e:
    print(f"   Errore: {e}")
    # Prova IP noto Supabase
    ip = "54.75.53.21"
    print(f"   Uso IP noto: {ip}")

# Prova connessione diretta
print("[2] Provo connessione...")
try:
    dsn = f"host={ip} port=5432 dbname=postgres user=postgres password={SUPABASE_KEY} sslmode=require connect_timeout=10"
    conn = psycopg2.connect(dsn)
    print("   Connesso!")
    
    cur = conn.cursor()
    
    # Crea tabella
    print("[3] Creo volantino_pagine...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS volantino_pagine (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            nome_file TEXT UNIQUE NOT NULL,
            pagina_num INTEGER NOT NULL,
            volantino_url TEXT NOT NULL,
            image_url TEXT,
            mark_data JSONB DEFAULT '{}'::jsonb,
            checked BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM volantino_pagine")
    count = cur.fetchone()[0]
    print(f"   Tabella ready! Righe: {count}")
    
    cur.close()
    conn.close()
    print("\n✅ Fatto!")
    
except Exception as e:
    print(f"   Errore: {e}")