import requests
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Get products that have alias set (current state)
print("Getting current alias state...")
all_products = []
offset = 0
while True:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/product?select=id,nome,alias&limit=1000&offset={offset}",
        headers=headers
    )
    batch = resp.json()
    if not batch:
        break
    all_products.extend(batch)
    offset += 1000
    print(f"  Loaded {len(all_products)}...")
products = all_products
print(f"Total products: {len(products)}")

# Get unique canonical names from alias field
canonical_names = set()
for p in products:
    if p.get('alias'):
        canonical_names.add(p['alias'])

print(f"Unique canonical names: {len(canonical_names)}")

# Build map: nome -> canonical alias
alias_map = {}
for p in products:
    nome = p.get('nome', '')
    alias = p.get('alias')
    if alias:
        alias_map[nome] = alias

# Find products without alias but their nome matches a canonical
updates_needed = []
for p in products:
    nome = p.get('nome', '')
    if nome in canonical_names and not p.get('alias'):
        updates_needed.append({
            'id': p['id'],
            'alias': nome
        })

print(f"Products needing update: {len(updates_needed)}")

# Apply updates
print("Updating...")
for i, rec in enumerate(updates_needed):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/product?id=eq.{rec['id']}",
        json={'alias': rec['alias']},
        headers=headers
    )
    if (i + 1) % 100 == 0:
        print(f"  Updated {i+1}/{len(updates_needed)}")

print(f"Done! Updated {len(updates_needed)} products")