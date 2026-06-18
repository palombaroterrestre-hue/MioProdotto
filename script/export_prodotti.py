import os, sys, csv, re, time, unicodedata
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

def strip_accents(s: str) -> str:
    return re.sub(r'[\u0300-\u036f]', '', unicodedata.normalize('NFD', s)).upper().strip()

def fetch_all():
    all_data = []
    start = 0
    limit = 1000
    while True:
        resp = supabase.table('rilevazioni_v4').select('*')\
            .order('fine_promozione', desc=True).range(start, start + limit - 1).execute()
        if not resp.data:
            break
        all_data.extend(resp.data)
        print(f"  fetched {len(resp.data)} records (total: {len(all_data)})", file=sys.stderr)
        if len(resp.data) < limit:
            break
        start += limit
        time.sleep(0.1)
    return all_data

print("Fetching products from rilevazioni_v4...", file=sys.stderr)
data = fetch_all()
print(f"Total raw records: {len(data)}", file=sys.stderr)

alias_map = {}
for r in data:
    group_key = strip_accents(r.get('alias') or '').strip() or strip_accents(r.get('nome_prodotto') or '')
    existing = alias_map.get(group_key)
    if not existing or (r.get('fine_promozione') or '') > (existing.get('fine_promozione') or ''):
        alias_map[group_key] = r

products = list(alias_map.values())
products.sort(key=lambda p: (p.get('categoria') or '', p.get('nome_prodotto') or ''))

out_path = os.path.join(os.path.dirname(__file__), '..', 'export_prodotti.csv')
with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['nome_prodotto', 'quantita', 'categoria', 'inizio_promozione', 'fine_promozione'])
    for p in products:
        w.writerow([
            p.get('nome_prodotto', ''),
            p.get('quantita', ''),
            p.get('categoria', ''),
            p.get('inizio_promozione', ''),
            p.get('fine_promozione', ''),
        ])

print(f"\nExport completato: {len(products)} prodotti unici -> {out_path}", file=sys.stderr)
