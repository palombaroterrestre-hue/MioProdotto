-- Crea tabella volantino_pagine per marcare le pagine dei volantini
-- Esegui questo codice in https://supabase.com/dashboard/project/fsxctxzzifohmbgqwcxk/sql/new

CREATE TABLE volantino_pagine (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    nome_file TEXT UNIQUE NOT NULL,
    pagina_num INTEGER NOT NULL,
    volantino_url TEXT NOT NULL,
    image_url TEXT,
    mark_data JSONB DEFAULT '{}'::jsonb,
    checked BOOLEAN DEFAULT FALSE
);

-- Abilita Row Level Security
ALTER TABLE volantino_pagine ENABLE ROW LEVEL SECURITY;

-- Policy per lettura pubblica
CREATE POLICY "Anyone can read volantino_pagine" ON volantino_pagine 
    FOR SELECT USING (true);

-- Policy per scrittura solo servizio
CREATE POLICY "Service can all volantino_pagine" ON volantino_pagine 
    FOR ALL USING (true) WITH CHECK (true);

-- Verifica
SELECT COUNT(*) as righe FROM volantino_pagine;