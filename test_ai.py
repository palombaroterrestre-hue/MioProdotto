import os
import json
import ollama
import re
import unicodedata
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
API_KEY = os.getenv('GEMMA_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = ollama.Client(host='https://api.ollama.com', headers={'Authorization': f'Bearer {API_KEY}'})

response = supabase.table('rilevazioni_v2').select('nome').execute()
all_names = [p['nome'] for p in response.data]
name_counts = Counter(all_names)
unique_names = sorted(set(all_names), key=lambda x: -name_counts[x])

# Try with products with SAME brand AND same category
barilla_pasta = [n for n in unique_names if 'PASTA' in n.upper() and 'BARILLA' in n.upper()]
barilla_unique = sorted(set(barilla_pasta))[:8]

print(f'Trovati {len(barilla_unique)} prodotti BARILLA PASTA')
for p in barilla_unique:
    print(f'  - {p}')

if len(barilla_unique) >= 3:
    target = barilla_unique[0]
    candidates = barilla_unique[1:6]

    prompt = f'''Analizza prodotti alimentari dello stesso brand BARILLA.

PRODOTTO PRINCIPALE: {target}

CANDIDATI:
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(candidates)])}

Per ogni candidato, indica se e la STESSA PASSATA (stesso tipo, stesso formato, stessa quantita).
Rispondi JSON array:
[{{"name": "nome", "is_same": true/false, "reason": "spiegazione"}}]

NON usare markdown. Solo JSON.'''

    print(f'\nTarget: {target}')
    print(f'Call AI...')

    try:
        res = ai_client.chat(
            model='gemma4:31b-cloud',
            messages=[{'role': 'user', 'content': prompt}]
        )

        content = res.get('message', {}).get('content', '')
        print(f'Risposta: {content}')

        match = re.search(r'\[[\s\S]*\]', content)
        if match:
            data = json.loads(match.group(0))
            print(f'Risultati:')
            for item in data:
                print(f"  {item.get('name')}: is_same={item.get('is_same')} - {item.get('reason')}")
    except Exception as e:
        print(f'Errore: {e}')