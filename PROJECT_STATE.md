# PROJECT STATE — MioProdotto
Ultimo aggiornamento: 3 maggio 2026

## Stack
- Scraping: Python + pdf2image + gemma4 su Ollama cloud
- Database: Supabase
- Frontend: Next.js su Vercel
- URL pubblico: https://mio-prodotto.vercel.app

## Tabelle Supabase
- product: tabella ATTIVA (7292 prodotti)
- product_aliases: alias deduplicazione (1655 alias, string_match)
- dedup_feedback: feedback utente per AI learning (vuota)
- staging_products: prodotti in attesa di review (vuota)
- rilevazioni_v2: BACKUP SOLA LETTURA (non modificare mai)
- watchlist: preferenze utenti per notifiche

## File principali
- smart_dedup_final.py: deduplicazione string-based, legge product, scrive product_aliases
- estrattore_con_quantita.py: scraper originale (non più in uso attivo)
- script/scraper_volantino_latest.py: scraper incrementale con retry
- lib/supabase.ts: client frontend, searchProdotti() usa ilike su product
- lib/ai_dedup.py: motore AI (da completare, manca collegamento Ollama)
- lib/feedback_examples.py: carica esempi feedback per prompt Ollama
- apply_ai_dedup.py: rigenera alias con AI su tutto il DB (da completare)

## Stato funzionalità
- Ricerca frontend: FUNZIONANTE con deduplicazione alias
- Scraper incrementale: FUNZIONANTE con dry-run mode
- Alias string_match: 1655 coppie caricate
- AI deduplication: DA COMPLETARE (manca metodo Ollama)
- Dashboard feedback: DA COSTRUIRE (flyer-review page)
- Email notifiche watchlist: DA COSTRUIRE
- GitHub Actions scheduler: DA CONFIGURARE

## Prossimi step in ordine
1. Collegare lib/ai_dedup.py al metodo Ollama corretto
2. Creare dashboard review su app/flyer-review/page.tsx
3. Implementare Supabase Storage per immagini PDF
4. Creare notify_watchlist.py
5. Configurare GitHub Actions cron

## Note critiche
- NON modificare rilevazioni_v2
- NON committare .env o .env.local
- Date in DB formato GG/MM/YYYY
- Non eseguire estrattore_con_quantita.py senza Ollama attivo
- Dopo ogni push verificare con git log --oneline -1