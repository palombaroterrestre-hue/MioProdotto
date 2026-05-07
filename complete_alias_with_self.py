"""
complete_alias_with_self.py
=====================
Popola la colonna alias per TUTTI i prodotti:
- Se è in un gruppo dedup → alias = canonical
- Se è unico → alias = nome originale (se stesso)
- Identifica casi dubbi per Gemma (similarity 0.70-0.85)
"""

import requests
import os
import json
import unicodedata
import re
from collections import Counter
from difflib import SequenceMatcher
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

print("=" * 50)
print("COMPLETE ALIAS WITH SELF UPDATE")
print("=" * 50 + "\n")

# ============================================================
# STEP 1: Carica TUTTI i prodotti
# ============================================================
print("STEP 1: Loading all products...")
all_names = []
product_id_map = {}  # nome -> id
product_data = {}   # nome -> {id, nome}

offset = 0
while True:
    url = f"{SUPABASE_URL}/rest/v1/product?select=id,nome&order=id&limit=1000&offset={offset}"
    resp = requests.get(url, headers=headers)
    batch = resp.json()
    if not batch:
        break
    for p in batch:
        nome = p.get('nome', '')
        if nome:
            all_names.append(nome)
            product_id_map[nome] = p['id']
            product_data[nome] = p
    offset += 1000
    print(f"  Loaded {len(all_names)}...")

print(f"Total: {len(all_names)} products\n")

# ============================================================
# STEP 2: Similarity e gruppi
# ============================================================
print("STEP 2: Computing similarity groups...")

name_counts = Counter(all_names)
unique_names = sorted(set(all_names), key=lambda x: -name_counts[x])
print(f"Unique names: {len(unique_names)}")

def normalize(name):
    if not isinstance(name, str):
        return ''
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r"['\u2018\u2019\u0060\u00b4\u02bc]", '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.upper().strip()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# Soglie per category
CATEGORY_THRESHOLDS = {
    'LATTICINI': 0.76,
    'CARNI': 0.80,
    'SALUMI': 0.84,
    'BEVANDE': 0.68,
    'DOLCI': 0.80,
    'CONDIMENTI': 0.76,
    'NON_FOOD': 0.92,
    'GENERIC': 0.80,
}

NON_FOOD_KEYWORDS = [
    'GIOCATTOLI', 'CHICCO', 'PANNOLINI', 'SALVIETTE', 'DETERSIVO',
    'AMMORBIDENTE', 'CANDEGGINA', 'SGRASSATORE', 'TOVAGLIA',
    'SCOPA', 'MOP', 'SPAZZOLA', 'PIATTI CARTA', 'BICCHIERI CARTA'
]

CATEGORY_MAP = {
    'LATTICINI': ['YOGURT', 'KEFIR', 'BURRO', 'PANNA', 'MOZZARELLA', 'RICOTTA', 'MASCARPONE', 'GORGONZOLA', 'BRIE', 'PARMIGIANO', 'FORMAGGINI', 'BEL PAESE'],
    'CARNI': ['HAMBURGER', 'BISTECCHE', 'TRIPPA', 'SPEZZATINO', 'POLPETTE', 'MACINATA', 'BRASATO', 'SCALOPPINE', 'BOVINO', 'SUINO', 'POLLO', 'TACCHINO'],
    'SALUMI': ['PROSCIUTTO', 'MORTADELLA', 'SPECK', 'PANCETTA', 'SALAME', 'SALSICCIA', 'WURSTEL', 'BRESAOLA'],
    'BEVANDE': ['ACQUA', 'COCA COLA', 'SPRITE', 'FANTA', 'BIRRA', 'VINO', 'PROSECCO', 'SUCCO DI', 'BIBITA'],
    'DOLCI': ['BISCOTTI', 'CIOCCOLATO', 'TORTA', 'GELATO', 'WAFER', 'MERENDINE', 'MARMELLATA', 'MAXIBON', 'KINDER', 'NUTELLA'],
    'CONDIMENTI': ['MAIONESE', 'KETCHUP', 'SENAPE', 'OLIO', 'ACETO', 'SUGO', 'PESTO', 'DADO', 'BRODO'],
}

def get_category(name):
    n = normalize(name)
    if any(k in n for k in NON_FOOD_KEYWORDS):
        return 'NON_FOOD'
    for cat, keywords in CATEGORY_MAP.items():
        if any(k in n for k in keywords):
            return cat
    return 'GENERIC'

def get_threshold(name1, name2):
    c1 = get_category(name1)
    c2 = get_category(name2)
    cat = c1 if c1 != 'GENERIC' else c2
    return CATEGORY_THRESHOLDS.get(cat, 0.80)

def same_category(name1, name2):
    c1 = get_category(name1)
    c2 = get_category(name2)
    if (c1 == 'NON_FOOD') != (c2 == 'NON_FOOD'):
        return False
    if c1 == 'GENERIC' or c2 == 'GENERIC':
        return True
    return c1 == c2

# Trova gruppi con similarity > threshold
sim_edges = {}
for i, name1 in enumerate(unique_names):
    for name2 in unique_names[i+1:]:
        if not same_category(name1, name2):
            continue
        n1, n2 = normalize(name1), normalize(name2)
        if abs(len(n1) - len(n2)) / max(len(n1), len(n2), 1) > 0.5:
            continue
        sim = similarity(name1, name2)
        threshold = get_threshold(name1, name2)
        if sim >= threshold:
            sim_edges.setdefault(name1, []).append(name2)
            sim_edges.setdefault(name2, []).append(name1)

# Connected components
visited = set()
groups = {}
for name in unique_names:
    if name in visited:
        continue
    group = set([name])
    queue = [name]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for neighbor in sim_edges.get(current, []):
            if neighbor not in visited:
                group.add(neighbor)
                queue.append(neighbor)
    if len(group) > 1:
        # Canonical selection
        canonical = max(group, key=lambda n: (len(normalize(n).split()), name_counts.get(n, 0)))
        groups[canonical] = {
            'aliases': [n for n in group if n != canonical],
            'all': list(group)
        }

print(f"Found {len(groups)} groups with duplicates\n")

# ============================================================
# STEP 3: Costruisci mapping nome -> alias
# ============================================================
print("STEP 3: Building name -> alias mapping...")

alias_updates = {}  # nome -> alias_value

for canonical, data in groups.items():
    # Canonical maps to itself
    alias_updates[canonical] = canonical
    # Each alias maps to canonical
    for alias_name in data['aliases']:
        alias_updates[alias_name] = canonical

# UNIQUE products (not in any group) -> alias = se stessi
for nome in unique_names:
    if nome not in alias_updates:
        alias_updates[nome] = nome  # himself

print(f"Total mappings: {len(alias_updates)}\n")

# ============================================================
# STEP 4: Identifica casi DUBBI per Gemma
# ============================================================
print("STEP 4: Identifying DUBBI cases (similarity 0.70-0.85)...")

dubbi_cases = []  # Per Gemma review

for canonical, data in groups.items():
    for alias_name in data['aliases']:
        sim = similarity(canonical, alias_name)
        if 0.70 <= sim < get_threshold(canonical, alias_name):
            dubbi_cases.append({
                'canonical': canonical,
                'alias': alias_name,
                'similarity': round(sim, 2)
            })

print(f"Dubbi cases found: {len(dubbi_cases)}\n")

# ============================================================
# STEP 5: Update colonna alias per TUTTI
# ============================================================
print("STEP 5: Updating ALL products with alias column...")

# Prepara update records
update_records = []
for nome in all_names:
    if nome in alias_updates:
        product_id = product_id_map.get(nome)
        if product_id:
            update_records.append({
                'id': product_id,
                'alias': alias_updates[nome]
            })

print(f"Records to update: {len(update_records)}\n")

# Apply updates
print("Applying updates...")
BATCH = 50
updated = 0
errors = 0

for i in range(0, len(update_records), BATCH):
    batch = update_records[i:i+BATCH]
    for rec in batch:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/product?id=eq.{rec['id']}",
            json={'alias': rec['alias']},
            headers=headers
        )
        if r.status_code in (200, 204):
            updated += 1
        else:
            errors += 1
    print(f"  Updated {min(i+BATCH, len(update_records))}/{len(update_records)}")

print(f"\nUpdated: {updated}, Errors: {errors}")

# ============================================================
# STEP 6: Verifica
# ============================================================
print("\nSTEP 6: Verifying...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?alias=not.is.null&select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
count_data = resp.json()
if count_data:
    print(f"Products with alias: {count_data[0]['count']}")

# Save dubbi cases for Gemma
if dubbi_cases:
    with open('dubbi_cases.json', 'w', encoding='utf-8') as f:
        json.dump(dubbi_cases, f, ensure_ascii=False, indent=2)
    print(f"Dubbi cases saved to: dubbi_cases.json")

print("\n" + "=" * 50)
print("COMPLETE!")
print("=" * 50)