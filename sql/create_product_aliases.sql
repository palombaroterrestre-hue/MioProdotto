-- Step 1: Create table
CREATE TABLE product_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alias_name TEXT,
    canonical_name TEXT,
    similarity_score DOUBLE PRECISION,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Enable RLS
ALTER TABLE product_aliases ENABLE ROW LEVEL SECURITY;

-- Step 3: Allow read
CREATE POLICY "Allow read" ON product_aliases FOR SELECT USING (true);

-- Step 4: Allow insert
CREATE POLICY "Allow insert" ON product_aliases FOR INSERT WITH CHECK (true);