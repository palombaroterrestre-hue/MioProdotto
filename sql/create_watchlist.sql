-- Tabella "watchlist" usata dal sito (aggiungi/leggi prodotti seguiti).
-- Al momento la tabella NON esiste nel database: con la chiave pubblica
-- Supabase risponde PGRST205 e la funzione watchlist del sito fallisce in silenzio.
-- Da eseguire nell'SQL Editor di Supabase. Il sito vi accede con la chiave
-- pubblica (ruolo anon), quindi servono policy RLS per select/insert.

CREATE TABLE IF NOT EXISTS public.watchlist (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome_prodotto TEXT NOT NULL,
  utente_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY "watchlist anon select" ON public.watchlist
  FOR SELECT TO anon USING (true);

CREATE POLICY "watchlist anon insert" ON public.watchlist
  FOR INSERT TO anon WITH CHECK (true);
