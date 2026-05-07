"""
gemma_dedup_confirm.py
====================
Identifica casi dubbi e chiede conferma a Gemma.
Similarity tra 0.70-0.85 = dubbio.
"""

import requests
import os
import json
import unicodedata
import re
from collections import Counter
from difflib import SequenceMatcher
from dotenv import load_dotenv
import ollama

load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
GEMMA_KEY = os.environ['GEMMA_API_KEY']

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Setup Ollama client
ai_client = ollama.Client(
    host='https://api.ollama.com',
    headers={'Authorization': f'Bearer {GEMMA_KEY}'}
)
MODEL = 'gemma4:31b-cloud'

print("=" * 50)
print("GEMMA DEDUP CONFIRM")
print("=" * 50 + "\n")

# ============================================================
# STEP 1: Load products
# ============================================================
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

# ============================================================
# STEP 2: Get unique names
# ============================================================
all_names = [p['nome'] for p in all_products if p.get('nome')]
unique_names = sorted(set(all_names), key=lambda x: -Counter(all_names)[x])
print(f"Unique names: {len(unique_names)}\n")

# ============================================================
# STEP 3: Similarity functions
# ============================================================
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

# ============================================================
# STEP 4: Find dubbi cases (similarity 0.70-0.85)
# ============================================================
print("Finding dubbi cases (similarity 0.70-0.85)...")

dubbi_pairs = []

# Get unique alias values (canonical names)
alias_values = set()
for p in all_products:
    if p.get('alias'):
        alias_values.add(p['alias'])

# For each product with alias different from nome, check similarity
for p in all_products:
    nome = p.get('nome', '')
    alias = p.get('alias', '')
    
    if alias and alias != nome:
        sim = similarity(nome, alias)
        if 0.70 <= sim < 0.85:
            dubbi_pairs.append({
                'nome': nome,
                'alias': alias,
                'similarity': round(sim, 2)
            })

# Remove duplicates
seen = set()
unique_dubbi = []
for d in dubbi_pairs:
    key = (d['nome'], d['alias'])
    if key not in seen:
        seen.add(key)
        unique_dubbi.append(d)

print(f"Dubbi cases found: {len(unique_dubbi)}\n")

# Show first 10
print("First 10 dubbi cases:")
for d in unique_dubbi[:10]:
    print(f"  {d['nome']} <-> {d['alias']} (sim: {d['similarity']})")

# Save to file for reference
with open('dubbi_cases.json', 'w', encoding='utf-8') as f:
    json.dump(unique_dubbi, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(unique_dubbi)} dubbi cases to dubbi_cases.json")

# ============================================================
# STEP 5: Ask Gemma for confirmation (limit to 10 for test)
# ============================================================
if not unique_dubbi:
    print("\nNo dubbi cases found!")
    exit(0)

TEST_LIMIT = 10
print(f"\nAsking Gemma to confirm first {TEST_LIMIT} cases...")

gemma_results = []

for i, case in enumerate(unique_dubbi[:TEST_LIMIT]):
    nome = case['nome']
    alias = case['alias']
    
    prompt = f"""Sono due prodotti alimentari:

A: {nome}
B: {alias}

Sono la STESSA cosa (stesso tipo, stesso formato)?
Rispondi SOLO con: SI o NO"""

    print(f"\n[{i+1}/{TEST_LIMIT}] Checking: {nome} <-> {alias}")
    
    try:
        res = ai_client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        answer = res.get('message', {}).get('content', '').strip().upper()
        
        # Check if SI or NO in response
        is_same = 'SI' in answer or 'SÌ' in answer.upper()
        
        print(f"  Gemma: {answer[:50]}")
        
        gemma_results.append({
            'nome': nome,
            'alias': alias,
            'similarity': case['similarity'],
            'gemma_answer': answer,
            'confirm': is_same
        })
        
    except Exception as e:
        print(f"  Error: {e}")
        gemma_results.append({
            'nome': nome,
            'alias': alias,
            'similarity': case['similarity'],
            'error': str(e)
        })

# Save results
with open('gemma_results.json', 'w', encoding='utf-8') as f:
    json.dump(gemma_results, f, ensure_ascii=False, indent=2)

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 50)
print("GEMMA RESULTS")
print("=" * 50)

confirmed = sum(1 for r in gemma_results if r.get('confirm'))
rejected = sum(1 for r in gemma_results if not r.get('confirm') and 'confirm' in r)
errors = sum(1 for r in gemma_results if 'error' in r)

print(f"Confirmed (SI): {confirmed}")
print(f"Rejected (NO): {rejected}")
print(f"Errors: {errors}")

print("\nResults saved to: gemma_results.json")