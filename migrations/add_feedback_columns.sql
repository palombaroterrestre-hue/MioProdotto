-- Esegui questo SQL dalla Supabase Dashboard SQL Editor
-- per aggiungere colonne mancanti a dedup_feedback

ALTER TABLE dedup_feedback ADD COLUMN similarity NUMERIC;
ALTER TABLE dedup_feedback ADD COLUMN category TEXT;
ALTER TABLE dedup_feedback ADD COLUMN gemma_answer TEXT;

-- Verifica
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'dedup_feedback'
ORDER BY ordinal_position;