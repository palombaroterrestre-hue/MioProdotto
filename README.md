# MioProdotto - Volantini Watchlist

Sistema di scraping volantini Ekom con estrazione prodotti via AI, salvataggio su Supabase e notifiche future per utenti con watchlist.

## Obiettivo

Quando un prodotto monitorato da un utente compare in un nuovo volantino, la web app invia una email di avviso.

## Stato Attuale

- Scraping storico disponibile in `estrattore_con_quantita.py`
- Versione refactor disponibile in `estrattore_con_quantita_v2.py`
- Estrazione da PDF con `pdf2image` + modello `gemma4:31b-cloud`
- Salvataggio su tabella Supabase `rilevazioni_v2`

## Script Principali

- `estrattore_con_quantita.py`: pipeline principale con prompt commerciale e salvataggio in DB
- `estrattore_con_quantita_v2.py`: refactor robusto mantenendo la logica business

## Setup Locale

1. Installa dipendenze Python del progetto.
2. Crea `.env` con le variabili richieste:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMMA_API_KEY`
   - `BASE_PATH`
   - `POPPLER_PATH`
3. Esegui lo script:

```bash
python estrattore_con_quantita.py
```

## Roadmap Breve

- Aggiungere `scraper_volantino_latest.py` per aggiornamento incrementale
- Trigger di ricerca nuovo volantino da `fine_validita - 3 giorni`
- Pipeline watchlist -> matching prodotti -> invio email
- Scheduler giornaliero

## Note Operative

- Supabase e' il database operativo consigliato.
- GitHub e' usato per versionamento codice/documentazione, non come DB runtime.
- Evitare il commit di `.env` o altri file con credenziali.