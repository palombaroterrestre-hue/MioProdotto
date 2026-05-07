"""
bulk_set_alias.py
================
Bulk update alias = nome using concurrent requests
"""

import requests
import os
import concurrent.futures
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

def update_record(rec):
    """Update single record"""
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/product?id=eq.{rec['id']}",
        json={'alias': rec['alias']},
        headers=headers
    )
    return r.status_code in (200, 204)

print("=== BULK SET ALIAS = NOME ===\n")

# Get all products
print("Loading products...")
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
    print(f"  {len(all_products)}...")

print(f"Total: {len(all_products)}\n")

# Build update list
updates = []
for p in all_products:
    nome = p.get('nome', '')
    current = p.get('alias')
    if not current or current != nome:
        updates.append({'id': p['id'], 'alias': nome})

print(f"Need to update: {len(updates)}\n")

# Process in parallel
print("Updating (parallel)...")
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(update_record, updates))

print(f"\nUpdated: {sum(results)}/{len(updates)}")

# Verify
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?alias=not.is.null&select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
if resp.json():
    print(f"With alias: {resp.json()[0]['count']}")