import os
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

import estrattore_con_quantita as extractor


BASE_URL = "https://www.ekomdiscount.it/wp-content/uploads"
MAX_PROMO_PER_MONTH = 40
TRIGGER_DAYS_BEFORE_END = 5
DEFAULT_TO_EMAIL = "bruneri.matteo@gmail.com"


def parse_italian_date(value: str) -> Optional[datetime.date]:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def get_last_flyer_info() -> Optional[Tuple[datetime.date, str]]:
    # Si leggono piu' righe e si sceglie in Python la data massima per evitare ordinamenti errati su stringa.
    res = (
        extractor.supabase.table("rilevazioni_v2")
        .select("fine_validita,fonte_volantino_link")
        .limit(5000)
        .execute()
    )
    rows: List[Dict[str, Any]] = res.data or []
    best_date = None
    best_url = None

    for row in rows:
        d = parse_italian_date(str(row.get("fine_validita", "")).strip())
        if not d:
            continue
        if best_date is None or d > best_date:
            best_date = d
            best_url = str(row.get("fonte_volantino_link", "")).strip()

    if best_date is None:
        return None
    return best_date, (best_url or "N/D")


def get_month_candidates(today: datetime) -> List[Tuple[int, str]]:
    current = (today.year, f"{today.month:02d}")
    first_day_of_month = today.replace(day=1)
    prev_month_day = first_day_of_month - timedelta(days=1)
    previous = (prev_month_day.year, f"{prev_month_day.month:02d}")
    if current == previous:
        return [current]
    return [current, previous]


def pdf_exists(url: str) -> bool:
    try:
        r = extractor.http.head(url, timeout=3, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def find_latest_pdf_url(today: datetime) -> Optional[Tuple[str, str, str]]:
    for year, month in get_month_candidates(today):
        # Si scansiona al contrario per trovare piu' rapidamente l'ultimo promo disponibile.
        for promo_num in range(MAX_PROMO_PER_MONTH, 0, -1):
            url = f"{BASE_URL}/{year}/{month}/EKOMPromo{promo_num:02d}-LGPM.pdf"
            if pdf_exists(url):
                return url, str(year), month
    return None


def already_processed(url: str) -> bool:
    check = (
        extractor.supabase.table("rilevazioni_v2")
        .select("id", count="exact")
        .eq("fonte_volantino_link", url)
        .limit(1)
        .execute()
    )
    return bool(check.count and check.count > 0)


def reload_aliases() -> bool:
    """Run smart_dedup_final.py to regenerate aliases and reload to Supabase."""
    import subprocess
    import sys
    
    try:
        # Run the dedup script
        result = subprocess.run(
            [sys.executable, "smart_dedup_final.py"],
            cwd=extractor.BASE_PATH,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"[ALIAS] Errore dedup: {result.stderr}")
            return False
        
        print(f"[ALIAS] Dedup completato: {result.stdout}")
        
        # Run the loader
        result2 = subprocess.run(
            [sys.executable, "load_aliases.py"],
            cwd=extractor.BASE_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result2.returncode != 0:
            print(f"[ALIAS] Errore loader: {result2.stderr}")
            return False
        
        print(f"[ALIAS] Alias ricaricati: {result2.stdout}")
        return True
        
    except Exception as e:
        print(f"[ALIAS] Exception: {e}")
        return False


def send_email(status: str, subject: str, details: Dict[str, str]) -> None:
    load_dotenv()
    smtp_host = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("ALERT_SMTP_PORT", "465"))
    smtp_user = os.getenv("ALERT_SMTP_USER")
    smtp_pass = os.getenv("ALERT_SMTP_PASS")
    from_email = os.getenv("ALERT_FROM_EMAIL", smtp_user or "")
    to_email = os.getenv("ALERT_TO_EMAIL", DEFAULT_TO_EMAIL)

    if not smtp_user or not smtp_pass or not from_email or not to_email:
        print("[MAIL] Config SMTP incompleta. Salto invio email.")
        return

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    lines = [
        f"Timestamp run: {datetime.now().isoformat(timespec='seconds')}",
        f"Esito: {status}",
        f"Dettagli: {details.get('reason', 'N/D')}",
    ]
    if details.get("url"):
        lines.append(f"URL volantino: {details['url']}")
    if details.get("last_end_date"):
        lines.append(f"Fine validita ultimo volantino DB: {details['last_end_date']}")
    if details.get("trigger_date"):
        lines.append(f"Data trigger (-5 giorni): {details['trigger_date']}")

    msg.set_content("\n".join(lines))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print(f"[MAIL] Inviata notifica {status} a {to_email}")


def main() -> None:
    now = datetime.now()
    today = now.date()

    last_info = get_last_flyer_info()
    if not last_info:
        reason = "Nessun volantino presente in DB: impossibile calcolare trigger."
        print(f"[SKIP] {reason}")
        send_email(
            "NOT_FOUND",
            "[MioProdotto][Beta] Nessun nuovo volantino",
            {"reason": reason},
        )
        return

    last_end_date, last_url = last_info
    trigger_date = last_end_date - timedelta(days=TRIGGER_DAYS_BEFORE_END)

    if today < trigger_date:
        reason = (
            "Finestra non ancora aperta. "
            f"Oggi={today.isoformat()} < Trigger={trigger_date.isoformat()}"
        )
        print(f"[SKIP] {reason}")
        send_email(
            "NOT_FOUND",
            "[MioProdotto][Beta] Nessun nuovo volantino",
            {
                "reason": reason,
                "last_end_date": last_end_date.isoformat(),
                "trigger_date": trigger_date.isoformat(),
                "url": last_url,
            },
        )
        return

    found = find_latest_pdf_url(now)
    if not found:
        reason = "Nessun PDF disponibile nel mese corrente e precedente."
        print(f"[SKIP] {reason}")
        send_email(
            "NOT_FOUND",
            "[MioProdotto][Beta] Nessun nuovo volantino",
            {
                "reason": reason,
                "last_end_date": last_end_date.isoformat(),
                "trigger_date": trigger_date.isoformat(),
            },
        )
        return

    candidate_url, anno, mese = found
    if already_processed(candidate_url):
        reason = "Ultimo PDF trovato ma gia presente in DB."
        print(f"[SKIP] {reason} URL={candidate_url}")
        send_email(
            "NOT_FOUND",
            "[MioProdotto][Beta] Nessun nuovo volantino",
            {
                "reason": reason,
                "url": candidate_url,
                "last_end_date": last_end_date.isoformat(),
                "trigger_date": trigger_date.isoformat(),
            },
        )
        return

    print(f"[FOUND] Nuovo volantino: {candidate_url}")
    
    # Scrape the new flyer
    scrape_success = False
    try:
        scrape_success = extractor.elabora_volantino(candidate_url, anno, mese)
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")
    
    if not scrape_success:
        reason = f"Estrazione fallita per {candidate_url}"
        print(f"[FAIL] {reason}")
        send_email(
            "ERROR",
            "[MioProdotto][Beta] Errore estrazione",
            {"reason": reason, "url": candidate_url},
        )
        return
    
    # Reload aliases after new products are scraped
    print("[ALIAS] Ricaricando alias table...")
    alias_success = reload_aliases()
    
    if not alias_success:
        # Non blocchiamo se gli alias falliscono, i prodotti sono gia in DB
        print("[WARN] Alias reload failed, but products are saved")
    
    send_email(
        "FOUND",
        "[MioProdotto][Beta] Volantino trovato",
        {
            "reason": "Nuovo volantino estratto e alias ricaricati.",
            "url": candidate_url,
            "last_end_date": last_end_date.isoformat(),
            "trigger_date": trigger_date.isoformat(),
        },
    )


if __name__ == "__main__":
    main()
