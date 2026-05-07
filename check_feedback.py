import os, requests, json
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# Get table structure and sample data
r = requests.get(f'{url}/rest/v1/dedup_feedback?limit=3', headers=headers)
prods = r.json()
print(f"Status: {r.status_code}")
print(f"Columns: {list(prods[0].keys()) if prods else 'empty table'}")

if prods:
    with open('feedback_schema.json', 'w', encoding='utf-8') as f:
        json.dump(prods, f, indent=2, ensure_ascii=False)
    print("Sample data saved to feedback_schema.json")