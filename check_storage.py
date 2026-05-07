import requests
import os
from dotenv import load_dotenv
load_dotenv()

url = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
key = os.getenv('SUPABASE_SERVICE_KEY')
headers = {'apikey': key}

r = requests.get(f'{url}/storage/v1/object/list/volantini', headers=headers)
if r.status_code == 200:
    files = r.json()
    print(f'Images in storage: {len(files)}')
    for f in files[:5]:
        print(f"  {f['name']}")
else:
    print(f'Error: {r.status_code} - {r.text}')