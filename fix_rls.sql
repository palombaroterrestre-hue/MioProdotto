-- Enable RLS
ALTER TABLE volantino_pagine ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Anyone can read volantino_pagine" ON volantino_pagine;

-- Create readable policy for all
CREATE POLICY "Public read volantino_pagine" ON volantino_pagine
    FOR SELECT USING (true);
