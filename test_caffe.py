import requests
url = 'https://fsxctxzzifohmbgqwcxk.supabase.co/rest/v1/product'
headers = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTczNzI1MCwiZXhwIjoyMDkxMzEzMjUwfQ.X7DudvCF90BkSPNny0AblDI_te-vcP3KlVprjIXSBCw',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTczNzI1MCwiZXhwIjoyMDkxMzEzMjUwfQ.X7DudvCF90BkSPNny0AblDI_te-vcP3KlVprjIXSBCw'
}
# Search CAFFE in nome OR alias
params = {'or': '(nome.ilike.*CAFFE*,alias.ilike.*CAFFE*)', 'select': 'nome,alias', 'limit': 50}
r = requests.get(url, headers=headers, params=params)
data = r.json()
print(f'Total products with CAFFE: {len(data)}')
print()
for p in data[:20]:
    print(f"  {p['nome']} -> alias: {p['alias']}")
if len(data) > 20:
    print(f'  ... and {len(data)-20} more')