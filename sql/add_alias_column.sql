-- Step 1: Add column (run in Supabase SQL Editor)
ALTER TABLE rilevazioni_v2 ADD COLUMN IF NOT EXISTS alias_name TEXT;

-- Step 2: Populate alias_name from product_aliases
-- This joins rilevazioni_v2 with product_aliases to update alias names
UPDATE rilevazioni_v2 r
SET alias_name = pa.canonical_name
FROM product_aliases pa
WHERE r.nome = pa.alias_name;

-- Step 3: For products without alias, set alias_name = nome (themselves)
UPDATE rilevazioni_v2
SET alias_name = nome
WHERE alias_name IS NULL OR alias_name = '';