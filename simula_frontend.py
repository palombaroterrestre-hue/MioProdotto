import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Simula la query esatta del frontend per "CAFFE"
upperQuery = "CAFFE"

# Step 1: cerca alias
r = requests.get(f"{url}/rest/v1/product_aliases?or=(alias_name.ilike.%{upperQuery}%,canonical_name.ilike.%{upperQuery}%)&limit=20", headers=headers)
aliasData = r.json()
canonicalNames = {upperQuery}
if aliasData:
    for a in aliasData:
        canonicalNames.add(a['canonical_name'].upper())
        canonicalNames.add(a['alias_name'].upper())

print(f"canonicalNames: {canonicalNames}")

# Step 2: cerca products - ESATTAMENTE come fa il frontend
orConditions = ','.join([f"nome.ilike.%{n}%" for n in canonicalNames])
fullQuery = f"or={orConditions}"
print(f"Full query: {fullQuery}")

r2 = requests.get(f"{url}/rest/v1/product?{fullQuery}&limit=50", headers=headers)
prods = r2.json()

with open('frontend_sim.json', 'w', encoding='utf-8') as f:
    json.dump(prods, f, indent=2, ensure_ascii=False)
print(f"Products found: {len(prods)}")
for p in prods[:10]:
    print(f"  - {p['nome']}")