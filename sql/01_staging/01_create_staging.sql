CREATE SCHEMA IF NOT EXISTS staging;

DROP TABLE IF EXISTS staging.darkom_annonces_raw;

CREATE TABLE staging.darkom_annonces_raw (
    annonce_id TEXT,
    date_publication TEXT,
    titre TEXT,
    ville TEXT,
    quartier TEXT,
    type_bien TEXT,
    transaction TEXT,
    prix TEXT,
    surface TEXT,
    nb_chambres TEXT,
    nb_salles_bain TEXT,
    etage TEXT,
    annee_construction TEXT
);


-- ============================================================
-- Verification
-- ============================================================

-- Check if staging schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'staging';

-- Check if raw staging table exists
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'staging'
  AND table_name = 'darkom_annonces_raw';

-- Check table columns
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'staging'
  AND table_name = 'darkom_annonces_raw'
ORDER BY ordinal_position;