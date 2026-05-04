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

# ── FIX 9: scrittura diretta su Supabase + path relativo per SQL ──────────────
# PRIMA 1: path hardcoded assoluto Windows "C:/Users/Bruss/OneDrive/..."
#           il file non funzionava su qualsiasi altra macchina
# PRIMA 2: il SQL generava CREATE TABLE + policy — ora la tabella esiste già
#           e rieseguire causava errori "relation already exists"
# PRIMA 3: aliases[:5] — limite arbitrario di 5 alias per canonical
#           perdeva alias validi oltre il quinto
# PRIMA 4: nessun campo source/confidence — non sapevi come erano stati generati
# DOPO:    scrive direttamente su Supabase via API + salva SQL come backup
#          in path relativo (funziona su qualsiasi macchina)
# ─────────────────────────────────────────────────────────────────────────────

# Prepara i record
rows = []
for canonical, aliases in groups.items():
    for alias in aliases:  # FIX 9c: nessun limite [:5]
        sim = similarity(canonical, alias)
        rows.append({
            'alias_name':       alias,
            'canonical_name':   canonical,
            'similarity_score': round(sim, 4),
            'source':           'string_match',  # FIX 9d: traccia il metodo
            'confidence':       round(sim, 4)
        })

print(f'\nTotal alias pairs to save: {len(rows)}')

# Svuota gli alias string_match esistenti prima di ricaricare
print('Clearing existing string_match aliases...')
del_resp = requests.delete(
    f"{SUPABASE_URL}/rest/v1/product_aliases?source=eq.string_match",
    headers=headers
)
print(f'  Cleared: {del_resp.status_code}')

# Carica a batch su Supabase
print('Uploading to Supabase...')
BATCH = 100
for i in range(0, len(rows), BATCH):
    batch = rows[i:i+BATCH]
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/product_aliases",
        json=batch,
        headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
    )
    if r.status_code not in (200, 201):
        print(f'  ERROR batch {i}: {r.status_code} {r.text[:200]}')
    else:
        print(f'  Saved {min(i+BATCH, len(rows))}/{len(rows)}')

# Salva anche SQL locale come backup (path relativo) — FIX 9a/9b
sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'intelligent_dedup_brand.sql')
print(f'\nSaving SQL backup to: {sql_path}')
with open(sql_path, 'w', encoding='utf-8') as f:
    f.write('-- Alias backup generato da smart_dedup_final.py\n')
    f.write('-- Caricamento diretto su Supabase già avvenuto\n\n')
    for row in rows:
        esc_alias  = row['alias_name'].replace("'", "''")
        esc_canon  = row['canonical_name'].replace("'", "''")
        f.write(
            f"INSERT INTO product_aliases "
            f"(alias_name, canonical_name, similarity_score, source, confidence) "
            f"VALUES ('{esc_alias}', '{esc_canon}', "
            f"{row['similarity_score']}, 'string_match', {row['confidence']}) "
            f"ON CONFLICT (alias_name, canonical_name) DO NOTHING;\n"
        )

print(f'SQL backup saved: {len(rows)} rows')

# Verifica finale
verify = requests.get(
    f"{SUPABASE_URL}/rest/v1/product_aliases?select=count",
    headers={**headers, 'Prefer': 'count=exact'}
)
print(f'\nFinal count in product_aliases: {verify.headers.get("content-range", "?")}')
print('\nDone.')
