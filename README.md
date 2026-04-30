# MioProdotto - Volantini Watchlist

Sistema di scraping volantini Ekom con estrazione prodotti via AI,
salvataggio su Supabase e notifiche email per utenti con watchlist.

## Stack
- Scraping: Python + pdf2image + gemma4:31b-cloud
- Database: Supabase (rilevazioni_v2, product_aliases, watchlist)
- Frontend: Next.js su Vercel - https://mio-prodotto.vercel.app

## Stato attuale
- 1000 prodotti in rilevazioni_v2
- 458 alias in product_aliases
- Ricerca con deduplicazione live
- Watchlist table pronta

## Run
python estrattore_con_quantita.py
python script/scraper_volantino_latest.py

## Setup
Crea .env con: SUPABASE_URL, SUPABASE_KEY, GEMMA_API_KEY

## Note
- Non committare .env o .env.local
- Date in DB formato GG/MM/YYYY