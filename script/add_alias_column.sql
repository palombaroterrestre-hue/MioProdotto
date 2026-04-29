-- Add alias_name column to rilevazioni_v2
ALTER TABLE rilevazioni_v2 ADD COLUMN IF NOT EXISTS alias_name TEXT;

-- This will be populated with the canonical name from product_aliases
-- Run this after syncing with product_aliases table