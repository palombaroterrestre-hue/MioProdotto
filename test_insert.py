import requests
headers = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTczNzI1MCwiZXhwIjoyMDkxMzEzMjUwfQ.X7DudvCF90BkSPNny0AblDI_te-vcP3KlVprjIXSBCw',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTczNzI1MCwiZXhwIjoyMDkxMzEzMjUwfQ.X7DudvCF90BkSPNny0AblDI_te-vcP3KlVprjIXSBCw'
}
# Test insert
data = {
    'alias_name': 'TEST',
    'canonical_name': 'TEST',
    'label': 'AI_CORRECT',
    'similarity': 0.85,
    'category': 'DOLCI',
    'gemma_answer': 'SI'
}
r = requests.post('https://fsxctxzzifohmbgqwcxk.supabase.co/rest/v1/dedup_feedback', json=data, headers=headers)
print('Status:', r.status_code)
print('Response:', r.text[:500])