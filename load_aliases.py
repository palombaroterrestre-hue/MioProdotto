import requests
import re
import uuid
from datetime import datetime, timezone

url = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTczNzI1MCwiZXhwIjoyMDkxMzEzMjUwfQ.X7DudvCF90BkSPNny0AblDI_te-vcP3KlVprjIXSBCw'
headers = {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates'}

# Read SQL file and extract INSERT values
with open('intelligent_dedup_brand.sql', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the CREATE TABLE line
lines = content.split('\n')
insert_lines = [l for l in lines if l.startswith('INSERT INTO product_aliases')]

print(f'Found {len(insert_lines)} INSERT statements')

# Parse each INSERT
rows = []
for line in insert_lines:
    # Extract alias_name and canonical_name
    match = re.search(r"VALUES \('([^']+)',\s*'([^']+)',\s*([0-9.]+)\)", line)
    if match:
        alias_name = match.group(1)
        canonical_name = match.group(2)
        similarity_score = float(match.group(3))
        rows.append({
            'id': str(uuid.uuid4()),
            'alias_name': alias_name,
            'canonical_name': canonical_name,
            'similarity_score': similarity_score,
            'created_at': datetime.now(timezone.utc).isoformat()
        })

print(f'Parsed {len(rows)} rows')

# Insert in batches
batch_size = 50
inserted = 0
for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    r = requests.post(url + '/rest/v1/product_aliases', headers=headers, json=batch)
    if r.status_code in (200, 201):
        inserted += len(batch)
        print(f'Inserted {inserted}/{len(rows)}')
    else:
        print(f'Error at {i}: {r.status_code} {r.text[:200]}')

print(f'Done! Inserted {inserted} aliases')