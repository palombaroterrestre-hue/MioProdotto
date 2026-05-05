-- Aggiungi colonne mancanti a dedup_feedback per smart_dedup_with_ai.py

ALTER TABLE dedup_feedback 
ADD COLUMN IF NOT EXISTS similarity NUMERIC,
ADD COLUMN IF NOT EXISTS category TEXT,
ADD COLUMN IF NOT EXISTS gemma_answer TEXT;

-- Verifica colonne
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'dedup_feedback';