# MioProdotto

Promo flyer scraping system for Ekom. Scrapes PDFs, extracts product data via Ollama AI, saves to Supabase.

## Run Commands

```bash
python estrattore_con_quantita.py                    # root version
python script/estrattore_con_quantita.py              # latest version (has retry logic, UTF-8 fix)
python script/scraper_volantino_latest.py            # incremental updates only
python test_2024.py                                   # verify PDF URLs still exist
```

## Environment Variables

Required in `.env` (never commit this file):
- `SUPABASE_URL`, `SUPABASE_KEY` - Supabase database
- `GEMMA_API_KEY` - Ollama API key for AI extraction
- `BASE_PATH` - local project root (e.g. `C:\Users\Bruss\OneDrive\Documents\MioProdotto`)
- `POPPLER_PATH` - poppler bin path for `pdf2image` (e.g. `C:\poppler\Library\bin`)
- `ALERT_SMTP_*` - email notification settings

## Key Constraints

- Dates in DB are `GG/MM/YYYY` format - requires explicit parsing
- Duplicate prevention: check `fonte_volantino_link` before reprocessing
- Scripts use `sys.platform == "win32"` to force UTF-8 encoding on Windows stdout
- Skills installed via `npx skills add` - config in `skills-lock.json`

## Architecture

- `script/` - active development directory with latest scripts
- `root` - original scripts, may be stale
- `webapp_static/pagine_volantini/` - cached PDF pages (gitignored)
- `skills/` - agent skills from GitHub (anthropics/skills, JuliusBrussee/caveman)

## References

- Full project state and handover info: `PROJECT_STATE.md`
- Original README at root with setup instructions