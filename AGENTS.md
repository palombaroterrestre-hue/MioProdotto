# MioProdotto

Promo flyer scraping system for Ekom. Scrapes PDFs, extracts product data via Ollama AI, saves to Supabase.

## Run Commands

```bash
python script/estrattore_con_quantita_v4.py            # extract products from PDFs → rilevazioni_v4
python script/genera_alias.py                          # generate/update alias column (run after extraction)
python script/genera_alias.py --force                  # regenerate all aliases from scratch
python script/scraper_volantino_latest.py              # incremental updates only
python test_2024.py                                    # verify PDF URLs still exist
```

## Environment Variables

Required in `.env` (never commit this file):
- `SUPABASE_URL`, `SUPABASE_KEY` - Supabase service_role key for DB writes
- `GEMMA_API_KEY` - Ollama API key for AI extraction
- `BASE_PATH` - local project root
- `POPPLER_PATH` - poppler bin path for `pdf2image`

## Key Constraints

- **Unica tabella**: `rilevazioni_v4` — contiene tutti i prodotti + colonna `alias`
- **Alias**: colonna TEXT su `rilevazioni_v4`, popolata da `genera_alias.py`
- **Duplicati volantini**: check su `link_volantino + pagina_num` prima di estrarre
- **Date**: formato ISO `YYYY-MM-DD` in DB
- **Webapp**: query su `nome_prodotto ILIKE` + `alias ILIKE`, dedup via alias
- **Emoji**: mappata da `categoria` a runtime in `lib/supabase.ts`
- Scripts usano `sys.platform == "win32"` per UTF-8 su Windows

## Architecture

- `script/` - active development directory
- `script/genera_alias.py` — alias generation via token overlap + inverted index
- `lib/supabase.ts` — unico client Supabase, punta a `rilevazioni_v4`
- `webapp_static/pagine_volantini/` — cached PDF pages (gitignored)
- URL pubblico: https://mio-prodotto.vercel.app

## Alias Algorithm

1. Fetch prodotti da `rilevazioni_v4` (con paginazione 1000)
2. Raggruppa per `categoria` (confronti solo intra-categoria)
3. Inverted index: solo coppie che condividono ≥1 token non comune
4. Similarità Jaccard su token: ≥0.80 → unione; ≥0.60 + stesso brand/tipo → unione
5. Union-Find per componenti connesse
6. Canonical: nome più corto con brand nel gruppo
7. Batch update (50 per volta) su Supabase

## References

- Full project state: `PROJECT_STATE.md`