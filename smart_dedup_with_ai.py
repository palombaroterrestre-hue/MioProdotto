"""
smart_dedup_with_ai.py
====================
- Logica similarity da smart_dedup_final.py
- Feedback learning (calibra soglie)
- AI confirmation (Ollama per gruppi dubbiosi)
- Feedback always in the loop
"""

import os
import requests
import unicodedata
import re
import json
import ollama
import math
from collections import Counter
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']  # FIX 1: service key per scritture
GEMMA_KEY = os.environ['GEMMA_API_KEY']

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

ai_client = ollama.Client(
    host='https://api.ollama.com',
    headers={'Authorization': f'Bearer {GEMMA_KEY}'}
)
MODEL = 'gemma4:31b-cloud'

# ============================================================
# CONFIG
# ============================================================
AI_LIMIT = 500
MAX_RETRIES = 3
BACKUP_FILE = 'ai_dedup_results.json'

# ============================================================
# CONSTANTS
# ============================================================
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

DEFAULT_THRESHOLDS = {
    'LATTICINI': 0.76,
    'CARNI': 0.80,
    'SALUMI': 0.84,
    'BEVANDE': 0.68,
    'DOLCI': 0.80,
    'CONDIMENTI': 0.76,
    'NON_FOOD': 0.92,
    'GENERIC': 0.80,
}

AI_SIMILARITY_RANGE = (0.70, 0.85)

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ''
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r"['\u2018\u2019\u0060\u00b4\u02bc]", '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.upper().strip()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def get_category(name: str) -> str:
    n = normalize(name)
    if any(k in n for k in NON_FOOD_KEYWORDS):
        return 'NON_FOOD'
    for cat, keywords in CATEGORY_MAP.items():
        if any(k in n for k in keywords):
            return cat
    return 'GENERIC'

def same_category(name1: str, name2: str) -> bool:
    c1, c2 = get_category(name1), get_category(name2)
    if (c1 == 'NON_FOOD') != (c2 == 'NON_FOOD'):
        return False
    if c1 == 'GENERIC' or c2 == 'GENERIC':
        return True
    return c1 == c2

def canonical_score(name: str, name_counts: Counter) -> float:
    """Score per scegliere canonical più informativo."""
    words = normalize(name).split()
    specific = len(words)
    freq = math.sqrt(name_counts.get(name, 0) + 1)
    has_qty = 1.1 if re.search(r'\d+\s*(ml|gr|kg|g|l\b|pz|cl)', name, re.I) else 1.0
    return specific * freq * has_qty

# ============================================================
# STEP 1: CALIBRATE THRESHOLDS FROM FEEDBACK
# ============================================================
def calibrate_thresholds():
    """Calibra soglie usando feedback esistente (media semplice)."""
    print("\n[1] Loading feedback...")
    
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/dedup_feedback?select=*",
        headers=headers
    )
    feedback = resp.json() if resp.status_code == 200 else []
    print(f"  Feedback loaded: {len(feedback)}")
    
    # Raggruppa per categoria
    category_correts = Counter()  # category -> count CORRECT
    category_wrongs = Counter()   # category -> count WRONG
    
    for f in feedback:
        cat = f.get('category') or get_category(f.get('alias_name', ''))
        label = f.get('label', '')
        if label == 'CORRECT' or label == 'AI_CORRECT':
            category_correts[cat] += 1
        elif label == 'WRONG' or label == 'AI_WRONG':
            category_wrongs[cat] += 1
    
    # Calcola soglie calibrate
    calibrated = DEFAULT_THRESHOLDS.copy()
    
    for cat in category_correts | category_wrongs:
        correct = category_correts.get(cat, 0)
        wrong = category_wrongs.get(cat, 0)
        total = correct + wrong
        
        if total > 0:
            # Media semplice: WRONG abbassa, CORRECT alza
            # WRONG ha peso maggiore per essere conservative
            adjustment = (correct - wrong) / (total * 10)
            calibrated[cat] = max(0.5, min(0.95, DEFAULT_THRESHOLDS.get(cat, 0.80) + adjustment))
            print(f"  {cat}: {DEFAULT_THRESHOLDS.get(cat, 0.80):.2f} -> {calibrated[cat]:.2f} (CORRECT: {correct}, WRONG: {wrong})")
    
    return calibrated, feedback

# ============================================================
# STEP 2-3: FIND DUPLICATES + AI CONFIRM
# ============================================================
def find_duplicates(names: list, thresholds: dict) -> dict:
    """Trova gruppi duplicati usando soglie calibrate."""
    sim_edges = {}
    total_pairs = len(names) * (len(names) - 1) // 2
    processed = 0

    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            processed += 1
            if processed % 50000 == 0:
                print(f"    Comparing: {processed}/{total_pairs}")

            if not same_category(name1, name2):
                continue

            n1, n2 = normalize(name1), normalize(name2)
            if abs(len(n1) - len(n2)) / max(len(n1), len(n2), 1) > 0.5:
                continue

            sim = similarity(name1, name2)
            cat = get_category(name1)
            threshold = thresholds.get(cat, 0.80)

            if sim >= threshold:
                sim_edges.setdefault(name1, []).append(name2)
                sim_edges.setdefault(name2, []).append(name1)

    # Connected components
    visited = set()
    groups = {}

    for name in names:
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
            groups[list(group)[0]] = list(group)[1:]

    return groups

def ask_gemma(nome: str, alias: str, feedback_context: list) -> tuple:
    """Chiede a Gemma con feedback context e retry."""
    
    # Costruisci context da feedback (ultimi 20)
    feedback_str = ""
    for f in feedback_context[:20]:
        feedback_str += f"- {f.get('label', '?')}: {f.get('alias_name', '')} → {f.get('canonical_name', '')}\n"
    
    prompt = f"""Sei un esperto di prodotti alimentari italiani.

FEEDBACK PRECEDENTE:
{feedback_str or 'Nessun feedback disponibile.'}

PRODOTTI DA VALUTARE:
A: {nome}
B: {alias}

Sono la STESSA cosa (stesso tipo, formato, brand)?
Rispondi SOLO con: SI o NO"""

    # Retry logic
    for attempt in range(MAX_RETRIES):
        try:
            res = ai_client.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': prompt}]
            )
            answer = res.get('message', {}).get('content', '').strip().upper()
            confirm = 'SI' in answer or 'SÌ' in answer
            return confirm, answer
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Retry {attempt+1}/{MAX_RETRIES}: {e}")
                continue
            return None, str(e)

# ============================================================
# STEP 4: SAVE TO FEEDBACK
# ============================================================
def save_to_feedback(nome: str, alias: str, sim: float, confirm: bool, answer: str):
    """Salva risposta in dedup_feedback."""
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/dedup_feedback",
            json={
                'alias_name': nome,
                'canonical_name': alias,
                'similarity': sim,
                'category': get_category(nome),
                'label': 'CORRECT' if confirm else 'WRONG',
                'gemma_answer': answer
            },
            headers=headers
        )
        if r.status_code not in (200, 201):
            print(f"  Warning: Could not save feedback ({r.status_code})")
    except Exception as e:
        print(f"  Warning: {e}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("SMART DEDUP WITH AI + FEEDBACK LEARNING")
    print("=" * 60)

    # Step 1: Calibra soglie da feedback
    thresholds, feedback_data = calibrate_thresholds()

    # Step 2: Carica prodotti
    print("\n[2] Loading products...")
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
    print(f"  Total: {len(all_products)}")

    # Step 3: Trova gruppi duplicati
    print("\n[3] Finding duplicate groups...")
    all_names = [p['nome'] for p in all_products if p.get('nome')]
    unique_names = sorted(set(all_names), key=lambda x: -Counter(all_names)[x])
    print(f"  Unique: {len(unique_names)}")

    groups = find_duplicates(unique_names, thresholds)
    print(f"  Groups: {len(groups)}")

    # Step 4: Filtra dubbi + AI confirm
    print(f"\n[4] AI confirmation ({AI_LIMIT} groups)...")
    
    # Prepara lista dubbi
    dubbi = []
    for canonical, aliases in groups.items():
        for alias in aliases:
            sim = similarity(canonical, alias)
            if AI_SIMILARITY_RANGE[0] <= sim < AI_SIMILARITY_RANGE[1]:
                dubbi.append((canonical, alias, sim))

    # Limita e processa
    dubbi = dubbi[:AI_LIMIT]
    print(f"  Dubbi groups: {len(dubbi)}")
    
    confirmed = []
    rejected = []
    errors = []
    
    # Backup setup
    all_results = []

    for i, (nome, alias, sim) in enumerate(dubbi):
        print(f"\n  [{i+1}/{len(dubbi)}] {nome} <-> {alias} (sim: {sim:.2f})")
        
        confirm, answer = ask_gemma(nome, alias, feedback_data)
        
        result = {'nome': nome, 'alias': alias, 'similarity': sim, 'answer': answer, 'confirm': confirm}
        all_results.append(result)
        
        if confirm is None:
            errors.append((nome, alias, sim))
            print(f"    ERROR: {answer}")
        else:
            print(f"    Gemma: {answer[:50]}")
            
            # Salva in feedback
            save_to_feedback(nome, alias, sim, confirm, answer)
            
            if confirm:
                confirmed.append((nome, alias, sim))
            else:
                rejected.append((nome, alias, sim))
        
        # Backup every 10
        if (i + 1) % 10 == 0:
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"  [Backup saved: {i+1}]")

    # Final backup
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Step 5: Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Confirmed (SI): {len(confirmed)}")
    print(f"Rejected (NO): {len(rejected)}")
    print(f"Errors: {len(errors)}")

    # Step 6: Apply aliases (solo confirmed)
    print("\n[5] Applying aliases to product table...")
    
    # Prepara map
    alias_updates = {}
    for nome, alias, sim in confirmed:
        alias_updates[nome] = alias
    
    # Trova IDs e aggiorna
    product_map = {p['nome']: p['id'] for p in all_products}
    updated = 0
    
    for nome, alias_canonical in alias_updates.items():
        if nome in product_map:
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/product?id=eq.{product_map[nome]}",
                json={'alias': alias_canonical},
                headers=headers
            )
            updated += 1
    
    print(f"  Updated: {updated}/{len(alias_updates)}")
    print("\nDone!")

if __name__ == '__main__':
    main()