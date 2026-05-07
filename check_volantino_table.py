import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Crea tabella via REST - in Supabase bisogna usare SQL Editor
# Proviamo prima a vedere se possiamo usare la tabella esistente
print("[1] Test connessione a Supabase...")
r = requests.get(
    f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=nome&limit=1",
    headers={"apikey": SUPABASE_KEY}
)
print(f"   Status: {r.status_code}")
if r.status_code != 200:
    print(f"   Errore: {r.text}")
    exit(1)

# Prova a leggere volantino_pagine (se esiste)
print("[2] Controllo se volantino_pagine esiste...")
r = requests.get(
    f"{SUPABASE_URL}/rest/v1/volantino_pagine?select=*&limit=1",
    headers={"apikey": SUPABASE_KEY}
)
print(f"   Status: {r.status_code}")
print(f"   Risposta: {r.text[:200]}")

if r.status_code == 200:
    print("\n✅ Tabella volantino_pagine esiste già!")
elif r.status_code == 404:
    print("\n❌ Tabella non esiste - crea manualmente da Supabase Dashboard -> SQL Editor:")
    print("""
CREATE TABLE volantino_pagine (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    nome_file TEXT UNIQUE NOT NULL,
    pagina_num INTEGER NOT NULL,
    volantino_url TEXT NOT NULL,
    image_url TEXT,
    mark_data JSONB DEFAULT '{}'::jsonb,
    checked BOOLEAN DEFAULT FALSE
);

ALTER TABLE volantino_pagine ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read" ON volantino_pagine FOR SELECT USING (true);
CREATE POLICY "Service can all" ON volantino_pagine FOR ALL USING (true) USING (true) WITH CHECK (true);
    """)