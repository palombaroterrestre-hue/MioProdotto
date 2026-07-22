import csv, os, sys, time
from dotenv import load_dotenv
from supabase import create_client, Client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_KEY richiesti in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

csv_path = os.path.join(os.path.dirname(__file__), '..', 'DEDUPLICATI_CORRETTI.csv')

rows = []
with open(csv_path, 'r', encoding='latin-1') as f:
    reader = csv.DictReader(f, delimiter=';')
    for r in reader:
        rows.append(r)

to_process = []
for r in rows:
    mantieni = r.get('MANTIENI', '').strip()
    a = r.get('PRODOTTO_A', '').strip()
    b = r.get('PRODOTTO_B', '').strip()
    if not mantieni:
        continue
    if a and a != mantieni:
        to_process.append((mantieni, a))
    if b and b != mantieni:
        to_process.append((mantieni, b))

# Deduplicate
seen = set()
unique_pairs = []
for m, e in to_process:
    key = (m, e)
    if key not in seen:
        seen.add(key)
        unique_pairs.append((m, e))

print(f"Righe CSV: {len(rows)}")
print(f"Coppie da processare: {len(to_process)}")
print(f"Coppie uniche: {len(unique_pairs)}")

updated_total = 0
errors = 0

for idx, (mantieni, elimina) in enumerate(unique_pairs):
    try:
        resp = supabase.table('rilevazioni_v4') \
            .update({'alias': mantieni}) \
            .eq('nome_prodotto', elimina) \
            .neq('alias', mantieni) \
            .execute()

        if resp.data:
            updated_total += len(resp.data)
    except Exception as e:
        errors += 1
        print(f"  -> ERRORE: {e}", file=sys.stderr)

    if idx % 10 == 0 and idx > 0:
        time.sleep(0.3)

    if (idx + 1) % 50 == 0 or idx == len(unique_pairs) - 1:
        print(f"[{idx+1}/{len(unique_pairs)}] Aggiornati finora: {updated_total}", file=sys.stderr)

print(f"\n--- COMPLETATO ---")
print(f"Record aggiornati: {updated_total}")
print(f"Errori: {errors}")
