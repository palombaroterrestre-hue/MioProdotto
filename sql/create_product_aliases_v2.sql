-- Run in Supabase SQL Editor one at a time

-- 1. Create table
CREATE TABLE product_aliases (
    id UUID PRIMARY KEY,
    alias_name TEXT,
    canonical_name TEXT,
    similarity_score DOUBLE PRECISION,
    category TEXT,
    created_at TIMESTAMPTZ
);

ALTER TABLE product_aliases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON product_aliases FOR ALL USING (true) WITH CHECK (true);