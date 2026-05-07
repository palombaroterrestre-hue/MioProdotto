import requests
import os
from dotenv import load_dotenv
load_dotenv()

url = 'https://fsxctxzzifohmbgqwcxk.supabase.co'
key = os.getenv('SUPABASE_SERVICE_KEY')
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

# Create bucket
r = requests.post(f'{url}/storage/v1/bucket', headers=headers, json={'id': 'volantini', 'name': 'volantini', 'public': True})
print(f'Create bucket: {r.status_code}')
if r.status_code in [200, 201]:
    print('Bucket created!')
else:
    print(r.text)