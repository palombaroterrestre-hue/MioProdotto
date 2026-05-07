import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Hardcoded for dry-run - same values as .env.local
SUPABASE_URL = "https://fsxctxzzifohmbgqwcxk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZzeGN0eHp6aWZvaG1iZ3F3Y3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzcyNTAsImV4cCI6MjA5MTMxMzI1MH0.eO-27fG5G4x5RC1dWkDTKmFcp8my3o1Hp4gZTJAxVpc"
BASE_URL = "https://www.ekomdiscount.it/wp-content/uploads"
MAX_PROMO_PER_MONTH = 40
TRIGGER_DAYS_BEFORE_END = 5

headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

def parse_italian_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None

def get_last_flyer_info():
    url = f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=fine_validita,fonte_volantino_link&limit=5000"
    r = requests.get(url, headers=headers)
    rows = r.json()
    best_date = None
    best_url = None
    for row in rows:
        d = parse_italian_date(str(row.get("fine_validita", "")).strip())
        if not d:
            continue
        if best_date is None or d > best_date:
            best_date = d
            best_url = str(row.get("fonte_volantino_link", "")).strip()
    return best_date, (best_url or "N/D")

def get_month_candidates(today):
    current = (today.year, f"{today.month:02d}")
    first_day_of_month = today.replace(day=1)
    prev_month_day = first_day_of_month - timedelta(days=1)
    previous = (prev_month_day.year, f"{prev_month_day.month:02d}")
    if current == previous:
        return [current]
    return [current, previous]

def pdf_exists(url):
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

def find_latest_pdf_url(today):
    for year, month in get_month_candidates(today):
        for promo_num in range(MAX_PROMO_PER_MONTH, 0, -1):
            url = f"{BASE_URL}/{year}/{month}/EKOMPromo{promo_num:02d}-LGPM.pdf"
            if pdf_exists(url):
                return url, str(year), month
    return None

def already_processed(url):
    check_url = f"{SUPABASE_URL}/rest/v1/rilevazioni_v2?select=id&fonte_volantino_link=eq.{url}&limit=1"
    r = requests.get(check_url, headers=headers)
    return len(r.json()) > 0

# Run dry-run
now = datetime.now()
today = now.date()

print("=== DRY RUN ===")
print(f"Today: {today}")
print()

last_info = get_last_flyer_info()
if last_info:
    last_end_date, last_url = last_info
    trigger_date = last_end_date - timedelta(days=TRIGGER_DAYS_BEFORE_END)
    
    print(f"[DB] Last fine_validita: {last_end_date}")
    print(f"[DB] Last flyer URL: {last_url}")
    print(f"[CALC] Trigger date (last_date - {TRIGGER_DAYS_BEFORE_END} days): {trigger_date}")
    print(f"[CHECK] Today > trigger: {today > trigger_date}")
    print()
    
    found = find_latest_pdf_url(now)
    if found:
        candidate_url, anno, mese = found
        print(f"[FIND] Latest PDF: {candidate_url}")
        print(f"[FIND] Already in DB: {already_processed(candidate_url)}")
    else:
        print("[FIND] No PDF found")
else:
    print("[ERROR] No flyers in DB")