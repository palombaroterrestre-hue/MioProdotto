import requests
import time
from datetime import datetime

def scout_ekom_links():
    """
    Scansiona il server Ekom alla ricerca di PDF validi 
    generando i link basati sui pattern individuati.
    """
    BASE_URL = "https://www.ekomdiscount.it/wp-content/uploads"
    # Pattern costante individuato dai tuoi link
    SUFFIX = "-LGPM.pdf"
    
    # Definiamo l'arco temporale (dal 2025 ad oggi)
    anni = [2025, 2026]
    mesi = [f"{m:02d}" for m in range(1, 13)]
    
    # Range di numeri promo da testare per ogni mese
    range_promo = range(1, 35) 

    found_links = []
    
    print(f"{'STATO':<10} | {'PERCORSO':<15} | {'PROMO':<8} | {'URL'}")
    print("-" * 100)

    for anno in anni:
        for mese in mesi:
            # Evitiamo di cercare nel futuro (oltre Aprile 2026)
            if anno == 2026 and int(mese) > 4:
                continue
                
            for p in range_promo:
                promo_str = f"{p:02d}"
                # Costruzione URL: /ANNO/MESE/EKOMPromoXX-LGPM.pdf
                target_url = f"{BASE_URL}/{anno}/{mese}/EKOMPromo{promo_str}{SUFFIX}"
                
                try:
                    # Usiamo HEAD invece di GET: interroga il server senza scaricare il file (molto più veloce)
                    response = requests.head(target_url, timeout=5, allow_redirects=True)
                    
                    if response.status_code == 200:
                        print(f"✅ TROVATO  | {anno}/{mese:<10} | #{promo_str:<6} | {target_url}")
                        found_links.append({
                            "url": target_url,
                            "anno": anno,
                            "mese": mese,
                            "promo": promo_str
                        })
                    # I 404 vengono ignorati per pulizia del terminale
                    
                except requests.RequestException as e:
                    print(f"❌ ERRORE   | Connessione fallita per Promo {promo_str}: {e}")
                
                # Un piccolo delay per non sovraccaricare il server (evita il ban IP)
                time.sleep(0.02)

    return found_links

if __name__ == "__main__":
    print(f"Avvio scouting dei link Ekom... (Data attuale: {datetime.now().strftime('%d/%m/%Y')})\n")
    valid_links = scout_ekom_links()
    
    print("\n" + "="*50)
    print(f"REPORT FINALE: Trovati {len(valid_links)} volantini validi.")
    print("="*50)
    # Nello script, cerca questa parte:
risultati = analizza_prodotti(buf.getvalue())
print("    [DEBUG] Risposta ricevuta dall'AI!") # <--- Aggiungi questo