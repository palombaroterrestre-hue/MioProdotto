import requests
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
import numpy as np

SUPABASE_URL = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzcyNTAsImV4cCI6MjA5MTMxMzI1MH0.eO-27fG5G4x5RC1dWkDTKmFcp8my3o1Hp4gZTJAxVpc'

response = requests.get(SUPABASE_URL + '/rest/v1/rilevazioni_v2?select=nome&order=id&limit=10000',
                     headers={'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY})
all_names = [p['nome'] for p in response.json()]
unique_names = sorted(set(all_names))

KNOWN_BRANDS = {
    'CALVE', 'CALVA', 'BARILLA', 'MULINO BIANCO', 'GALBANI', 'BIRAGHI',
    'LAVAZZA', 'DANTE', 'RIGAMONTI', 'STUFFER', 'COLUSSI', 'PERONI',
    'NOVI', 'MAREBLU', 'DELICIUS', 'NANNI', 'INVERNIZZI', 'GRANAROLO',
    'SACLA', 'SACLÀ', 'MUTTI', 'KNORR', 'STAR', 'FINDUS', 'CHANTE CLAIR',
    'CHANTECLAIR', 'DIXAN', 'SCOTTEX', 'VIROSAC', 'FERRERO', 'NUTELLA',
    'CIRIO', 'PARMALAT', 'GIOVANARDI', 'BON', 'MCCAIN', 'APPETAIS'
}

def normalize(name):
    result = []
    for c in name:
        code = ord(c)
        if code in [0xc0, 0xc1, 0xc2, 0xc3]: result.append('A')
        elif code in [0xc8, 0xc9]: result.append('E')
        elif code in [0xe0, 0xe1, 0xe2, 0xe3]: result.append('a')
        elif code in [0xe8, 0xe9]: result.append('e')
        elif code in [0xec, 0xed, 0xee]: result.append('i')
        elif code in [0xf2, 0xf3, 0xf4]: result.append('o')
        elif code in [0xf9, 0xfa, 0xfb]: result.append('u')
        else: result.append(c)
    return ''.join(result)

def extract_brand(name):
    norm = normalize(name).upper()
    for brand in KNOWN_BRANDS:
        if brand.upper() in norm:
            return brand.upper()
    return None

# TF-IDF Clustering
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), lowercase=True)
X = vectorizer.fit_transform(unique_names)
clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=0.7, metric='cosine', linkage='average')
labels = clustering.fit_predict(X.toarray())

clusters = {}
for i, label in enumerate(labels):
    if label not in clusters:
        clusters[label] = []
    clusters[label].append(unique_names[i])

# VALID clusters (same brand)
valid_clusters = []
for label, products in clusters.items():
    if len(products) >= 2:
        brands = [extract_brand(p) for p in products]
        unique_brands = set([b for b in brands if b])
        if len(unique_brands) <= 1:
            valid_clusters.append({
                'brand': list(unique_brands)[0] if unique_brands else 'GENERIC',
                'products': products,
                'canonical': min(products, key=lambda x: len(normalize(x)))
            })

print('=' * 70)
print('  ML CLUSTERING - EXAMPLES OF DEDUPLICATION RESULTS')
print('=' * 70)

# Show 15 best examples (with most products or best brand matches)
best_clusters = sorted(valid_clusters, key=lambda x: (-len(x['products']), x['brand']))[:15]

examples_shown = 0
for c in best_clusters:
    brand = c['brand']
    products = c['products']
    canonical = c['canonical']
    
    if len(products) >= 3:
        examples_shown += 1
        print(f'\n>>> EXAMPLE {examples_shown}: {brand}')
        print(f'   Canonical: {canonical}')
        print(f'   Variants ({len(products)}):')
        for p in products[:8]:
            if p == canonical:
                print(f'   * {p} [canonical]')
            else:
                print(f'   - {p}')

print('\n' + '=' * 70)
print('  MAIONESE PRODUCTS - DETAILED VIEW')
print('=' * 70)

maionesi = [p for p in unique_names if 'MAIONESE' in p.upper()]
for m in maionesi:
    idx = unique_names.index(m)
    cluster_products = clusters[labels[idx]]
    brand = extract_brand(m)
    
    print(f'\n>>> {m}')
    print(f'   Brand detected: {brand}')
    print(f'   In cluster with:')
    
    for p in cluster_products:
        if p != m:
            b = extract_brand(p)
            status = 'OK' if b == brand else '!!'
            print(f'   {status} {p}')

print('\n' + '=' * 70)
print('  PASTA PRODUCTS - SHOWING CORRECT SEPARATION BY BRAND')
print('=' * 70)

paste = [p for p in unique_names if 'PASTA' in p.upper() and 'SEMOLA' in p.upper()]
for p in paste:
    b = extract_brand(p)
    print(f'   {p} -> brand: {b}')

print('\n' + '=' * 70)
print('  GENERATING SQL FILE...')
print('=' * 70)

# Generate SQL
with open('C:/Users/Bruss/OneDrive/Documents/MioProdotto/ml_dedup_final.sql', 'w', encoding='utf-8') as f:
    f.write('-- ML-Generated Product Aliases\n')
    f.write('CREATE TABLE IF NOT EXISTS product_aliases (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), alias_name TEXT NOT NULL, canonical_name TEXT NOT NULL, similarity_score NUMERIC, created_at TIMESTAMPTZ DEFAULT NOW()); ALTER TABLE product_aliases ENABLE ROW LEVEL SECURITY; CREATE POLICY "Allow read" ON product_aliases FOR SELECT USING (true); CREATE POLICY "Allow insert" ON product_aliases FOR INSERT WITH CHECK (true);\n\n')
    
    count = 0
    for c in valid_clusters:
        canonical = c['canonical']
        for alias in c['products']:
            if alias != canonical:
                esc_alias = alias.replace("'", "''")
                esc_canon = canonical.replace("'", "''")
                f.write(f"INSERT INTO product_aliases (alias_name, canonical_name, similarity_score) VALUES ('{esc_alias}', '{esc_canon}', 0.85);\n")
                count += 1
    
    print(f'\nGenerated SQL with {count} alias mappings')
    print(f'Saved to: ml_dedup_final.sql')

print('\n' + '=' * 70)
print('  SUMMARY STATISTICS')
print('=' * 70)

brand_counts = {}
for c in valid_clusters:
    brand = c['brand']
    if brand not in brand_counts:
        brand_counts[brand] = 0
    brand_counts[brand] += len(c['products'])

print(f'\nTotal valid clusters: {len(valid_clusters)}')
print(f'Total alias mappings: {sum(len(c["products"]) for c in valid_clusters)}')
print('\nTop 10 brands by product count:')
for brand, count in sorted(brand_counts.items(), key=lambda x: -x[1])[:10]:
    print(f'  {brand}: {count} products')