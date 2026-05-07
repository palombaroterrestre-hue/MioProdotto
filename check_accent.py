import requests
h = {'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzcyNTAsImV4cCI6MjA5MTMxMzI1MH0.eO-27fG5G4x5RC1dWkDTKmFcp8my3o1Hp4gZTJAxVpc'}
r = requests.get('https://fsxctxzzifohmbgqwcxk.supabase.co/rest/v1/product', headers=h, params={'select': 'nome', 'limit': 200})
data = r.json()
import unicodedata
for p in data[:20]:
    n = p['nome']
    # Check accent
    nfd = unicodedata.normalize('NFD', n)
    ascii_name = nfd.encode('ascii', 'ignore').decode('ascii')
    if 'CAFF' in ascii_name.upper():
        print(f'Original: {repr(n)} -> ASCII: {repr(ascii_name)}')