"""
smart_dedup_final.py — VERSIONE CORRETTA
========================================
Differenze rispetto alla versione precedente: vedi commenti FIX 1-9
"""

import os
import requests
import unicodedata
import re  # FIX 3 — aggiunto per strip apostrofi
from difflib import SequenceMatcher
from collections import Counter
from dotenv import load_dotenv  # FIX 1 — credenziali da .env

# ── FIX 1: credenziali da variabile d'ambiente, non hardcoded ─────────────────
# PRIMA: SUPABASE_URL e SUPABASE_KEY scritti in chiaro nel codice
# DOPO:  letti da .env — il file .env non viene mai committato su GitHub
load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
# ─────────────────────────────────────────────────────────────────────────────

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# ── FIX 2: legge da 'product' invece di 'rilevazioni_v2' ─────────────────────
# PRIMA: /rest/v1/rilevazioni_v2 — tabella vecchia, ora è solo backup
# DOPO:  /rest/v1/product — tabella attiva usata dal frontend
# Legge a blocchi da 1000 per superare il limite REST di Supabase
print('Loading products from Supabase...')
all_names = []
offset = 0
while True:
    url = (
        f"{SUPABASE_URL}/rest/v1/product"
        f"?select=nome&order=id&limit=1000&offset={offset}"
    )
    resp = requests.get(url, headers=headers)
    batch = [p['nome'] for p in resp.json() if p.get('nome')]
    if not batch:
        break
    all_names.extend(batch)
    offset += 1000
    print(f'  Loaded {len(all_names)} products...')

print(f'Total: {len(all_names)} product names')

# ── NUOVO: Leggi feedback utente da dedup_feedback ────────────────────────────
print('Loading feedback from dedup_feedback...')
feedback_resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/dedup_feedback?select=alias_name,canonical_name,label",
    headers=headers
)
feedback_data = feedback_resp.json() if feedback_resp.status_code == 200 else []

# Process feedback: correct_aliases = {alias: canonical}, wrong_aliases = {alias: canonical}
correct_aliases = {}  # alias_name -> canonical_name (CORRECT)
wrong_aliases = set()  # set of (alias_name, canonical_name) pairs (WRONG)
for f in feedback_data:
    alias = f.get('alias_name', '')
    canonical = f.get('canonical_name', '')
    label = f.get('label', '')
    if label == 'CORRECT' and alias and canonical:
        correct_aliases[alias] = canonical
    elif label == 'WRONG' and alias and canonical:
        wrong_aliases.add((alias, canonical))

print(f'  CORRECT feedbacks: {len(correct_aliases)}')
print(f'  WRONG feedbacks: {len(wrong_aliases)}')
# ─────────────────────────────────────────────────────────────────────────────

name_counts = Counter(all_names)
unique_names = sorted(set(all_names), key=lambda x: -name_counts[x])

# ── FIX 3: normalizzazione completa con apostrofi e spazi ────────────────────
# PRIMA: solo NFD + strip diacritici
#        non gestiva: L'ORIGINALE → LORIGINALE
#        non gestiva: PANNA  FRESCA → PANNA FRESCA (doppio spazio)
#        non gestiva: CAFFÈ → CAFFE (solo se accentato con combining char)
# DOPO:  gestisce tutti i casi italiani comuni
def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ''
    # Decomposizione NFD: à → a + combining accent
    name = unicodedata.normalize('NFD', name)
    # Rimuovi diacritici (categoria Unicode Mn = combining marks)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    # Rimuovi apostrofi in tutte le varianti tipografiche italiane
    name = re.sub(r"['\u2018\u2019\u0060\u00b4\u02bc]", '', name)
    # Collassa spazi multipli e tab
    name = re.sub(r'\s+', ' ', name)
    return name.upper().strip()
# ─────────────────────────────────────────────────────────────────────────────

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# ── FIX 4: rimosso find_brand_groups() — era definito ma mai usato ────────────
# PRIMA: funzione di 20 righe che non veniva chiamata da nessuna parte (dead code)
# DOPO:  eliminata per chiarezza
# ─────────────────────────────────────────────────────────────────────────────

# ── FIX 5: category guard — blocca prodotti di categorie diverse ──────────────
# PRIMA: nessun controllo categoriale
#        risultato: "KEFIR ASSORTITI" e "GIOCATTOLI ASSORTITI" venivano raggruppati
# DOPO:  se un prodotto è non-alimentare, non può mai matchare con un alimentare
NON_FOOD_KEYWORDS = [
    'GIOCATTOLI', 'CHICCO', 'PANNOLINI', 'SALVIETTE', 'DETERSIVO',
    'AMMORBIDENTE', 'CANDEGGINA', 'SGRASSATORE', 'TOVAGLIA',
    'SCOPA', 'MOP', 'SPAZZOLA', 'PIATTI CARTA', 'BICCHIERI CARTA'
]

CATEGORY_MAP = {
    'LATTICINI':  ['YOGURT', 'KEFIR', 'BURRO', 'PANNA', 'MOZZARELLA',
                   'RICOTTA', 'MASCARPONE', 'GORGONZOLA', 'BRIE',
                   'PARMIGIANO', 'FORMAGGINI', 'BEL PAESE'],
    'CARNI':      ['HAMBURGER', 'BISTECCHE', 'TRIPPA', 'SPEZZATINO',
                   'POLPETTE', 'MACINATA', 'BRASATO', 'SCALOPPINE',
                   'BOVINO', 'SUINO', 'POLLO', 'TACCHINO'],
    'SALUMI':     ['PROSCIUTTO', 'MORTADELLA', 'SPECK', 'PANCETTA',
                   'SALAME', 'SALSICCIA', 'WURSTEL', 'BRESAOLA'],
    'BEVANDE':    ['ACQUA NATURALE', 'ACQUA FRIZZANTE', 'COCA COLA',
                   'SPRITE', 'FANTA', 'BIRRA', 'VINO', 'PROSECCO',
                   'SUCCO DI', 'BIBITA'],
'DOLCI':      ['BISCOTTI', 'CIOCCOLATO', 'CIOCCOLATINI', 'TORTA',
                    'GELATO', 'WAFER', 'MERENDINE', 'MARMELLATA', 'MAXIBON',
                    'KINDER', 'NUTELLA', 'FIGURA', 'MERCO', 'SNICKERS', 'MARS'],
    'CONDIMENTI': ['MAIONESE', 'KETCHUP', 'SENAPE', 'OLIO', 'ACETO',
                   'SUGO', 'PESTO', 'DADO', 'BRODO'],
}

def get_category(name: str) -> str:
    n = normalize(name)
    if any(k in n for k in NON_FOOD_KEYWORDS):
        return 'NON_FOOD'
    for cat, keywords in CATEGORY_MAP.items():
        if any(k in n for k in keywords):
            return cat
    return 'GENERIC'

def same_category(name1: str, name2: str) -> bool:
    c1 = get_category(name1)
    c2 = get_category(name2)
    # Non-food non può mai matchare con food
    if (c1 == 'NON_FOOD') != (c2 == 'NON_FOOD'):
        return False
    # GENERIC è compatibile con tutto
    if c1 == 'GENERIC' or c2 == 'GENERIC':
        return True
    return c1 == c2
# ─────────────────────────────────────────────────────────────────────────────

# ── FIX 6: soglie dinamiche per categoria ─────────────────────────────────────
# PRIMA: base_threshold=0.80, brand_threshold=0.70 — fissi per tutto
#        BEVANDE con 0.80: "COCA COLA 33CL" e "COCA COLA 1L" non matchavano
#        SALUMI con 0.70: "PROSCIUTTO COTTO" e "PROSCIUTTO CRUDO" matchavano
# DOPO:  ogni categoria ha la sua soglia calibrata
CATEGORY_THRESHOLDS = {
    'LATTICINI':  0.76,
    'CARNI':      0.80,
    'SALUMI':     0.84,
    'BEVANDE':    0.68,
    'DOLCI':      0.80,
    'CONDIMENTI': 0.76,
    'NON_FOOD':   0.92,
    'GENERIC':    0.80,
}

def get_threshold(name1: str, name2: str) -> float:
    c1 = get_category(name1)
    c2 = get_category(name2)
    cat = c1 if c1 != 'GENERIC' else c2
    return CATEGORY_THRESHOLDS.get(cat, 0.80)
# ─────────────────────────────────────────────────────────────────────────────

def find_duplicates(names: list) -> dict:

    # ── FIX 7: logica threshold corretta ──────────────────────────────────────
    # PRIMA: bug di precedenza operatori:
    #        shared_significant = words1 & words2 - stopwords
    #        Python interpreta come: words1 & (words2 - stopwords) — SBAGLIATO
    #        Inoltre: la variabile 'threshold' veniva settata ma mai usata
    #        per filtrare — gli archi venivano aggiunti comunque
    # DOPO:  logica chiara e corretta:
    #        1. check categoriale (FIX 5)
    #        2. calcola similarity
    #        3. ottieni threshold dinamico (FIX 6)
    #        4. se sim >= threshold → aggiungi arco
    # ─────────────────────────────────────────────────────────────────────────
    sim_edges = {}

    total_pairs = len(names) * (len(names) - 1) // 2
    processed = 0

    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            processed += 1
            if processed % 5000 == 0:
                pct = processed / total_pairs * 100
                print(f'  Comparing pairs: {processed}/{total_pairs} ({pct:.1f}%)')

            # FIX 5 applicato: skip se categorie incompatibili
            if not same_category(name1, name2):
                continue

            # Pre-filter veloce: se similarity < 0.50 salta senza chiamare
            # SequenceMatcher completo (ottimizzazione performance)
            n1 = normalize(name1)
            n2 = normalize(name2)
            if abs(len(n1) - len(n2)) / max(len(n1), len(n2), 1) > 0.5:
                continue

            sim = similarity(name1, name2)

            # FIX 6 applicato: threshold dinamico per categoria
            threshold = get_threshold(name1, name2)

            if sim < threshold:
                continue

            sim_edges.setdefault(name1, []).append(name2)
            sim_edges.setdefault(name2, []).append(name1)

    # Connected components (algoritmo invariato — funzionava correttamente)
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
            group_list = list(group)

            # ── FIX 8: canonical selection — preferisce nomi più informativi ──
            # PRIMA: max con -len(words) → preferiva il nome PIÙ CORTO
            #        "HAMBURGER" veniva scelto su "HAMBURGER DI BOVINO ADULTO"
            #        perdendo informazione utile per l'utente
            # DOPO:  score bilancia specificità + frequenza + presenza quantità
            import math as _math
            def canonical_score(n):
                words = normalize(n).split()
                specificity = len(words)                           # più parole = più specifico
                frequency   = _math.sqrt(name_counts.get(n, 0) + 1)  # frequenza (sublineare)
                has_qty     = 1.1 if re.search(                    # bonus se ha quantità
                    r'\d+\s*(ml|gr|kg|g|l\b|pz|cl)', n, re.I) else 1.0
                return specificity * frequency * has_qty

            canonical = max(group_list, key=canonical_score)
            # ─────────────────────────────────────────────────────────────────

            aliases = [n for n in group_list if n != canonical]
            groups[canonical] = sorted(aliases, key=lambda n: -similarity(canonical, n))

    return groups


print('Finding duplicate groups...')
groups = find_duplicates(unique_names)
print(f'Found {len(groups)} groups with duplicates')

# Debug MAIONESE
print('\n=== MAIONESE GROUP ===')
for canonical, aliases in groups.items():
    if 'MAIONESE' in normalize(canonical):
        print(f'  Canonical: {canonical}')
        for alias in aliases:
            print(f'    -> {alias}  (sim: {similarity(canonical, alias):.2f})')

# ── NUOVO: Applica feedback e aggiorna colonna alias in product ───────────────
# 1. Applica CORRECT: forza il canonical scelto dall'utente
# 2. Rimuovi WRONG: escludi le coppie sbagliate
# 3. Aggiorna colonna 'alias' nella tabella product

print('\nApplying feedback to groups...')

# Add CORRECT feedbacks as forced aliases
for alias, canonical in correct_aliases.items():
    if alias in unique_names and canonical in unique_names:
        # Add alias to the canonical's group
        if canonical not in groups:
            groups[canonical] = []
        if alias not in groups[canonical]:
            groups[canonical].append(alias)
        print(f'  FORCED: {alias} -> {canonical}')

# Remove WRONG feedbacks
removed_count = 0
for canonical, aliases in list(groups.items()):
    filtered_aliases = []
    for alias in aliases:
        if (alias, canonical) not in wrong_aliases:
            filtered_aliases.append(alias)
        else:
            removed_count += 1
            print(f'  REMOVED WRONG: {alias} -> {canonical}')
    groups[canonical] = filtered_aliases

print(f'  Total removed (WRONG): {removed_count}')

# Build alias updates for product table: nome -> alias (canonical)
print('\nBuilding alias updates for product table...')
alias_updates = {}  # nome -> canonical
for canonical, aliases in groups.items():
    # The canonical itself maps to itself
    alias_updates[canonical] = canonical
    # Each alias maps to the canonical
    for alias in aliases:
        alias_updates[alias] = canonical

print(f'  Total products with alias: {len(alias_updates)}')

# ── NUOVO: Aggiorna colonna alias nella tabella product ────────────────────────
print('\nUpdating product table with alias column...')

# First get all product IDs and names
print('  Fetching product IDs...')
product_map = {}  # nome -> id
offset = 0
while True:
    url = f"{SUPABASE_URL}/rest/v1/product?select=id,nome&order=id&limit=1000&offset={offset}"
    resp = requests.get(url, headers=headers)
    batch = resp.json()
    if not batch:
        break
    for p in batch:
        product_map[p['nome']] = p['id']
    offset += 1000
    print(f'    Loaded {len(product_map)} products...')

# Prepare updates
print('  Preparing updates...')
updates = []
for nome, alias_canonical in alias_updates.items():
    if nome in product_map:
        updates.append({
            'id': product_map[nome],
            'alias': alias_canonical
        })

print(f'  Total updates: {len(updates)}')

# Bulk update product table
print('  Updating product table...')
BATCH = 50
for i in range(0, len(updates), BATCH):
    batch = updates[i:i+BATCH]
    # Use upsert with id
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/product",
        json=batch,
        headers={**headers, 'Prefer': 'return=minimal'}
    )
    if r.status_code not in (200, 204):
        print(f'  ERROR batch {i}: {r.status_code} {r.text[:200]}')
    else:
        print(f'  Updated {min(i+BATCH, len(updates))}/{len(updates)}')

print('\nAlias column updated in product table!')

# Verifica finale: conta prodotti con alias
verify = requests.get(
    f"{SUPABASE_URL}/rest/v1/product?alias=not.is.null&select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
print(f'\nProducts with alias: {verify.headers.get("content-range", "?")}')
print('\nDone.')
