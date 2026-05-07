"""
simple_set_alias_self.py
====================
Per ogni prodotto SENZA alias, imposta alias = nome stesso
"""

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

print("=== SET ALIAS = NOME FOR ALL PRODUCTS ===\n")

# Get all products WITHOUT alias
print("Loading products without alias...")
all_products = []
offset = 0
while True:
    # Get products where alias is null OR alias = nome (not set)
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/product?select=id,nome,alias&limit=1000&offset={offset}",
        headers=headers
    )
    batch = resp.json()
    if not batch:
        break
    for p in batch:
        all_products.append(p)
    offset += 1000
    print(f"  Loaded {len(all_products)}...")

print(f"Total: {len(all_products)} products\n")

# Set alias = nome for products without alias
print("Setting alias = nome for all products...")
updates_needed = []
for p in all_products:
    nome = p.get('nome', '')
    current_alias = p.get('alias')
    
    # If no alias OR alias is different from nome, set alias = nome
    if not current_alias or current_alias != nome:
        updates_needed.append({
            'id': p['id'],
            'alias': nome
        })

print(f"Products to update: {len(updates_needed)}\n")

# Apply updates
print("Updating...")
BATCH = 50
updated = 0
for i in range(0, len(updates_needed), BATCH):
    batch = updates_needed[i:i+BATCH]
    for rec in batch:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/product?id=eq.{rec['id']}",
            json={'alias': rec['alias']},
            headers=headers
        )
        if r.status_code in (200, 204):
            updated += 1
    print(f"  Updated {min(i+BATCH, len(updates_needed))}/{len(updates_needed)}")

print(f"\nDone! Updated: {updated}")

# Verify
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
resp2 = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?alias=not.is.null&select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
total = resp.json()
with_alias = resp2.json()
print(f"\nTotal products: {total[0]['count'] if total else '?'}")
print(f"With alias: {with_alias[0]['count'] if with_alias else '?'}")