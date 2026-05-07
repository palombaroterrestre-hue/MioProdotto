"""
complete_alias_update.py
=======================
Script ottimizzato per completare la colonna alias.
Usa batch update per essere più veloce.
"""

import requests
import os
import json
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

print("=== COMPLETE ALIAS UPDATE ===\n")

# Step 1: Get all products
print("Loading all products...")
all_products = []
offset = 0
while True:
    url = f"{SUPABASE_URL}/rest/v1/product?select=id,nome,alias&limit=1000&offset={offset}"
    resp = requests.get(url, headers=headers)
    batch = resp.json()
    if not batch:
        break
    all_products.extend(batch)
    offset += 1000
    print(f"  Loaded {len(all_products)}...")

print(f"Total products: {len(all_products)}\n")

# Step 2: Find unique canonical names (alias values that are themselves canonicals)
canonical_names = set()
for p in all_products:
    alias = p.get('alias', '')
    if alias:
        canonical_names.add(alias)

print(f"Unique canonical names: {len(canonical_names)}")

# Step 3: Find products WITHOUT alias whose nome matches a canonical
# These need alias = their canonical
updates_needed = []
for p in all_products:
    nome = p.get('nome', '')
    current_alias = p.get('alias')
    
    # If nome is itself a canonical, set alias to itself
    if nome in canonical_names and not current_alias:
        updates_needed.append({
            'id': p['id'],
            'alias': nome
        })

# Also: find products that ARE aliases of something, but haven't been updated yet
# They need alias = their canonical (looked up from other products)
# Build lookup: product_nome -> its_canonical_for_alias
nome_to_canonical = {}
for p in all_products:
    alias = p.get('alias')
    if alias:
        nome_to_canonical[p['nome']] = alias

# Find products that should get alias based on being in a group
for p in all_products:
    nome = p.get('nome', '')
    if not p.get('alias') and nome in nome_to_canonical:
        updates_needed.append({
            'id': p['id'],
            'alias': nome_to_canonical[nome]
        })

print(f"Products needing update: {len(updates_needed)}\n")

# Step 4: Apply batch updates (10 records per PATCH)
print("Updating in batches of 10...")
BATCH_SIZE = 10
for i in range(0, len(updates_needed), BATCH_SIZE):
    batch = updates_needed[i:i+BATCH_SIZE]
    
    # For each record, make individual request with id filter
    for rec in batch:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/product?id=eq.{rec['id']}",
            json={'alias': rec['alias']},
            headers=headers
        )
        if r.status_code not in (200, 204):
            print(f"  ERROR {rec['id']}: {r.status_code}")
    
    print(f"  Updated {min(i+BATCH_SIZE, len(updates_needed))}/{len(updates_needed)}")

print(f"\nDone! Updated {len(updates_needed)} products")

# Step 5: Verify
print("\nVerifying...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?alias=not.is.null&select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
count_data = resp.json()
if count_data:
    print(f"Products with alias: {count_data[0]['count']}")
else:
    print("Products with alias: (count query failed)")
    
print("\n=== COMPLETE ===")