import requests
from difflib import SequenceMatcher
from collections import Counter

SUPABASE_URL = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzcyNTAsImV4cCI6MjA5MTMxMzI1MH0.eO-27fG5G4x5RC1dWkDTKmFcp8my3o1Hp4gZTJAxVpc'

headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY}
response = requests.get(SUPABASE_URL + '/rest/v1/rilevazioni_v2?select=nome&order=id&limit=10000', headers=headers)
all_names = [p['nome'] for p in response.json()]
name_counts = Counter(all_names)
unique_names = sorted(set(all_names), key=lambda x: -name_counts[x])

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

def similarity(a, b):
    return SequenceMatcher(None, normalize(a).lower(), normalize(b).lower()).ratio()

# BRAND-FIRST approach: Group products that share a brand
def find_brand_groups(names):
    """Group products by brand presence"""
    brand_products = {}
    no_brand = []
    
    for name in names:
        norm = normalize(name).upper()
        # Extract potential brand (first significant word after first 2)
        words = norm.split()
        
        # Find brand word
        brand = None
        for w in words[:3]:  # Brand usually in first 3 words
            if len(w) > 3 and w not in ['DI', 'DA', 'DEL', 'DELLA', 'E', 'IL', 'LA', 'LE', 'LO', 'UN', 'UNA']:
                brand = w
                break
        
        if brand:
            if brand not in brand_products:
                brand_products[brand] = []
            brand_products[brand].append(name)
        else:
            no_brand.append(name)
    
    return brand_products, no_brand

# Similarity-based grouping with lower threshold for brand-matched products
def find_duplicates(names, base_threshold=0.80, brand_threshold=0.70):
    groups = {}
    processed = set()
    
    # Build similarity graph
    sim_edges = {}
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            sim = similarity(name1, name2)
            
            # Use lower threshold if they share a brand
            threshold = brand_threshold  # Start with lower
            norm1 = normalize(name1).upper()
            norm2 = normalize(name2).upper()
            words1 = set(norm1.split()[:5])
            words2 = set(norm2.split()[:5])
            
            # If they share significant words (brands), use lower threshold
            shared_significant = words1 & words2 - {'DI', 'DA', 'DEL', 'E', 'IL', 'LA', 'LE', 'LO', 'UN'}
            if len(shared_significant) > 0 and sim >= brand_threshold:
                threshold = brand_threshold
            elif sim >= base_threshold:
                threshold = base_threshold
            else:
                continue
            
            if name1 not in sim_edges:
                sim_edges[name1] = []
            if name2 not in sim_edges:
                sim_edges[name2] = []
            sim_edges[name1].append(name2)
            sim_edges[name2].append(name1)
    
    # Find connected components
    visited = set()
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
            # Smart canonical: prefer SHORTEST name with brand, then frequency
            canonical = max(group_list, key=lambda x: (
                -len(normalize(x).split()),  # Shorter = better (negative for max)
                name_counts.get(x, 0)  # Frequency
            ))
            aliases = [n for n in group_list if n != canonical]
            groups[canonical] = sorted(aliases, key=lambda n: -similarity(canonical, n))
    
    return groups

print('Finding similar products...')
groups = find_duplicates(unique_names, base_threshold=0.80, brand_threshold=0.70)
print(f'Found {len(groups)} groups with duplicates')

# Show MAIONESE
print('\n=== MAIONESE GROUP ===')
for canonical, aliases in groups.items():
    if 'MAIONESE' in canonical.upper():
        print(f'\n  Canonical: {canonical}')
        for alias in aliases:
            print(f'    -> {alias}')

# Show top 15
print('\n=== TOP 15 DUPLICATE GROUPS ===')
sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))[:15]
for canonical, aliases in sorted_groups:
    print(f'\n  {canonical}')
    for alias in aliases[:3]:
        print(f'    -> {alias}')

# Generate SQL
with open('C:/Users/Bruss/OneDrive/Documents/MioProdotto/intelligent_dedup_brand.sql', 'w', encoding='utf-8') as f:
    f.write('CREATE TABLE IF NOT EXISTS product_aliases (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), alias_name TEXT NOT NULL, canonical_name TEXT NOT NULL, similarity_score NUMERIC, created_at TIMESTAMPTZ DEFAULT NOW()); ALTER TABLE product_aliases ENABLE ROW LEVEL SECURITY; CREATE POLICY "Allow read" ON product_aliases FOR SELECT USING (true); CREATE POLICY "Allow insert" ON product_aliases FOR INSERT WITH CHECK (true);\n\n')
    total = 0
    for canonical, aliases in groups.items():
        for alias in aliases[:5]:
            sim = similarity(canonical, alias)
            esc_alias = alias.replace("'", "''")
            esc_canon = canonical.replace("'", "''")
            f.write(f"INSERT INTO product_aliases (alias_name, canonical_name, similarity_score) VALUES ('{esc_alias}', '{esc_canon}', {sim:.2f});\n")
            total += 1
    print(f'\nSaved {total} alias mappings to intelligent_dedup_brand.sql')