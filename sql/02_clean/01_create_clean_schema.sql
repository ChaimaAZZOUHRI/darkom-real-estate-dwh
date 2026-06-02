-- The automated Python script transform_clean_data.py also creates this table before loading clean data.


-- ============================================================
-- Create Clean Schema / Silver Layer
-- Purpose: Store cleaned, standardized, and enriched data
-- ============================================================


-- Create clean schema
CREATE SCHEMA IF NOT EXISTS clean;


-- Drop existing clean table if it already exists
DROP TABLE IF EXISTS clean.darkom_annonces_clean;


-- Create clean table
CREATE TABLE clean.darkom_annonces_clean (
    annonce_id TEXT PRIMARY KEY,

    date_publication DATE,
    titre TEXT,
    ville TEXT,
    quartier TEXT,
    type_bien TEXT,
    transaction TEXT,

    prix NUMERIC,
    surface NUMERIC,
    nb_chambres INTEGER,
    nb_salles_bain INTEGER,
    etage INTEGER,
    annee_construction INTEGER,

    prix_m2 NUMERIC,
    age_bien INTEGER,
    surface_bin TEXT,
    categorie_prix TEXT,
    categorie_surface TEXT,

    annee_publication INTEGER,
    mois_publication INTEGER,
    trimestre_publication INTEGER,

    date_publication_imputed BOOLEAN,
    quartier_imputed BOOLEAN,
    type_bien_imputed BOOLEAN,
    transaction_imputed BOOLEAN,
    nb_chambres_imputed BOOLEAN,
    nb_salles_bain_imputed BOOLEAN,
    etage_imputed BOOLEAN,
    annee_construction_imputed BOOLEAN,

    prix_is_outlier BOOLEAN,
    surface_is_outlier BOOLEAN,
    prix_m2_is_outlier BOOLEAN,
    is_outlier BOOLEAN,

    prix_capped NUMERIC,
    surface_capped NUMERIC,
    prix_m2_capped NUMERIC
);


-- ============================================================
-- Indexes for clean layer
-- ============================================================

CREATE INDEX idx_clean_annonce_id
ON clean.darkom_annonces_clean(annonce_id);

CREATE INDEX idx_clean_ville
ON clean.darkom_annonces_clean(ville);

CREATE INDEX idx_clean_type_bien
ON clean.darkom_annonces_clean(type_bien);

CREATE INDEX idx_clean_transaction
ON clean.darkom_annonces_clean(transaction);

CREATE INDEX idx_clean_date_publication
ON clean.darkom_annonces_clean(date_publication);

CREATE INDEX idx_clean_prix
ON clean.darkom_annonces_clean(prix);

CREATE INDEX idx_clean_surface
ON clean.darkom_annonces_clean(surface);

CREATE INDEX idx_clean_prix_m2
ON clean.darkom_annonces_clean(prix_m2);


-- ============================================================
-- Verification
-- ============================================================

-- Check if clean schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'clean';


-- Check if clean table exists
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'clean'
  AND table_name = 'darkom_annonces_clean';


-- Check clean table columns
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'clean'
  AND table_name = 'darkom_annonces_clean'
ORDER BY ordinal_position;


-- Check created indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'clean'
  AND tablename = 'darkom_annonces_clean'
ORDER BY indexname;



-- ============================================================
-- Verification
-- ============================================================

-- Check if clean schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'clean';

-- Check if clean table exists
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'clean'
  AND table_name = 'darkom_annonces_clean';

-- Check clean table columns
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'clean'
  AND table_name = 'darkom_annonces_clean'
ORDER BY ordinal_position;