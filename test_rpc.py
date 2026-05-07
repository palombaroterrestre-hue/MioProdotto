import requests
import os

url = "https://fsxctxzzifohmbgqwcxk.supabase.co/rest/v1/rpc/exec_sql"
key = os.getenv("SUPABASE_SERVICE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

payload = {"query": "SELECT 1 as test"}

try:
    r = requests.post(url, headers=headers, json=payload)
    print(f"Risposta: {r.status_code}")
    print(r.text)
except Exception as e:
    print(f"Errore: {e}")