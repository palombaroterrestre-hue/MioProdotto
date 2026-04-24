# MioProdotto - Volantini Watchlist

Sistema di scraping volantini Ekom con estrazione prodotti via AI, salvataggio su Supabase e notifiche future per utenti con watchlist.

## Obiettivo

Quando un prodotto monitorato da un utente compare in un nuovo volantino, la web app invia una email di avviso.

## Stato Attuale

- Scraping storico disponibile in `estrattore_con_quantita.py`
- Scraping incrementale disponibile in `scraper_volantino_latest.py`
- Estrazione da PDF con `pdf2image` + modello `gemma4:31b-cloud`
- Salvataggio su tabella Supabase `rilevazioni_v2`
- Notifica beta via email su esito `FOUND` / `NOT_FOUND`

## Script Principali

- `estrattore_con_quantita.py`: pipeline principale con prompt commerciale e salvataggio in DB
- `scraper_volantino_latest.py`: cerca il volantino piu' recente e processa solo il nuovo


## Setup Locale

1. Installa dipendenze Python del progetto.
2. Crea `.env` con le variabili richieste:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMMA_API_KEY`
   - `BASE_PATH`
   - `POPPLER_PATH`
   - `ALERT_SMTP_HOST`
   - `ALERT_SMTP_PORT`
   - `ALERT_SMTP_USER`
   - `ALERT_SMTP_PASS`
   - `ALERT_FROM_EMAIL`
   - `ALERT_TO_EMAIL`
3. Esegui lo script:

```bash
python estrattore_con_quantita.py
python scraper_volantino_latest.py
```

## Roadmap Breve

- Trigger di ricerca nuovo volantino da `fine_validita - 5 giorni`
- Pipeline watchlist -> matching prodotti -> invio email
- Scheduler giornaliero

## Note Operative

- Supabase e' il database operativo consigliato.
- GitHub e' usato per versionamento codice/documentazione, non come DB runtime.
- Evitare il commit di `.env` o altri file con credenziali.
