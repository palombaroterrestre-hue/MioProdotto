import os
import json
import ollama
import re
import unicodedata
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("GEMMA_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not API_KEY:
    raise RuntimeError("Variabili .env mancanti")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = ollama.Client(host='https://api.ollama.com', headers={'Authorization': f'Bearer {API_KEY}'})

MODEL = 'gemma4:31b-cloud'

def normalize(name):
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.upper().strip()

def get_all_products():
    response = supabase.table('rilevazioni_v2').select('nome').execute()
    products = [p['nome'] for p in response.data]
    name_counts = Counter(products)
    unique_names = sorted(set(products), key=lambda x: -name_counts[x])
    return unique_names, name_counts

def ask_ai_for_similar(target_product, candidate_list, limit=20):
    candidates_text = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(candidate_list[:limit])])
    
    prompt = f"""Analizza prodotti alimentari.

PRODOTTO PRINCIPALE: {target_product}

CANDIDATI:
{candidates_text}

Per ogni candidato, indica se e la STESSA PASSATA (stesso tipo, stesso formato).
Rispondi SOLO con JSON array:
[{{"name": "nome", "is_same": true/false, "reason": "spiegazione"}}]

Includi il prodotto PRINCIPALE stesso nella risposta.
NON usare markdown."""

    try:
        res = ai_client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        content = res.get('message', {}).get('content', '')
        
        match = re.search(r'\[[\s\S]*\]', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"    [!] Errore: {e}")
    
    return None

def run_ai_deduplication():
    print("=== AI DEDUPLICATION con Ollama ===\n")
    
    unique_names, name_counts = get_all_products()
    print(f"Prodotti unici: {len(unique_names)}")
    
    processed = set()
    aliases = []
    
    batch_size = 50
    
    for i, product in enumerate(unique_names[:200]):
        if product in processed:
            continue
        
        print(f"\n[{i+1}/{min(200, len(unique_names))}] Analizzo: {product}")
        
        candidates = [p for p in unique_names if p != product and p not in processed]
        
        result = ask_ai_for_similar(product, candidates)
        
        if result and len(result) > 1:
            print(f"    Trovati {len(result)} prodotti simili")
            
            canonical = product
            for item in result:
                name = item.get('name', '')
                if name and name != canonical:
                    aliases.append({
                        'canonical_name': canonical,
                        'alias_name': name,
                        'source': 'ai_gemma4'
                    })
            
            processed.add(product)
            for item in result:
                if item.get('name'):
                    processed.add(item['name'])
        else:
            print(f"    Nessun duplicato trovato")
        
        if (i + 1) % batch_size == 0:
            print(f"\n--- Inserimento batch {i+1} ---")
            if aliases:
                supabase.table('product_aliases').upsert(aliases, on_conflict='alias_name,canonical_name').execute()
                aliases = []
    
    if aliases:
        supabase.table('product_aliases').upsert(aliases, on_conflict='alias_name,canonical_name').execute()
    
    print(f"\n=== COMPLETATO ===")
    print(f"Alias inseriti: {len(aliases)}")

if __name__ == '__main__':
    run_ai_deduplication()