import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Simula la query del frontend per "caffè"
upperQuery = "CAFFÈ"

# Step 1: cerca alias
r = requests.get(f"{url}/rest/v1/product_aliases?or=(alias_name.ilike.%{upperQuery}%,canonical_name.ilike.%{upperQuery}%)&limit=20", headers=headers)
aliasData = r.json()
print(f"Aliases found: {len(aliasData)}")
canonicalNames = {upperQuery}
if aliasData:
    for a in aliasData:
        canonicalNames.add(a['canonical_name'])
        canonicalNames.add(a['alias_name'])
print(f"Search names: {canonicalNames}")

# Step 2: cerca products
orConditions = ','.join([f"nome.ilike.%{n}%" for n in canonicalNames])
print(f"Query: or({orConditions})")

r2 = requests.get(f"{url}/rest/v1/product?or={orConditions}&limit=10", headers=headers)
prods = r2.json()
print(f"Products found: {len(prods)}")
for p in prods[:5]:
    print(f"  - {p['nome']}")