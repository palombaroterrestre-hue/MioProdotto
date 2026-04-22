# PROJECT_STATE

Documento di handover rapido per riprendere il progetto anche con un altro modello LLM.

## Product Goal

Costruire una web app che notifichi via email gli utenti quando uno o piu' prodotti della loro watchlist compaiono nei nuovi volantini.

## Current Status

- Scraping storico funzionante su `estrattore_con_quantita.py`
- Migliorie di robustezza introdotte (retry rete, validazione env, controlli difensivi)
- Prompt prodotti aggiornato in versione piu' deterministica
- Git for Windows installato in macchina
- Skills installate correttamente via `npx skills add JuliusBrussee/caveman -a cursor -y`

## Decisions

- Database prodotti: **Supabase**
- GitHub: versionamento codice + documentazione + eventuali export statici
- Strategia update: script incrementale dedicato (`scraper_volantino_latest.py`)

## Next Implementation Priority

1. Creare `scraper_volantino_latest.py`
2. Logica trigger: avvio ricerca da `fine_validita ultimo volantino - 3 giorni`
3. Estrazione solo del nuovo volantino (se URL non presente in DB)
4. Preparare schema watchlist/notifiche email

## Known Constraints

- Il terminale puo' non vedere subito `git` nel PATH: usare nuova sessione se necessario
- Le date in DB sono nel formato `GG/MM/YYYY`, richiedono parsing esplicito
- Evitare reprocessing duplicato: controllo su `fonte_volantino_link`

## Environment Variables

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GEMMA_API_KEY`
- `BASE_PATH`
- `POPPLER_PATH`

## Run Commands

```bash
python estrattore_con_quantita.py
python estrattore_con_quantita_v2.py
```

## Handover Checklist

- Leggere prima `README.md` e questo file
- Verificare `.env`
- Verificare accesso Supabase
- Eseguire script su una finestra temporale ridotta prima del run completo
