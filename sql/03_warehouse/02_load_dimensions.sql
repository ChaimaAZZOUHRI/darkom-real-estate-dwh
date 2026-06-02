-- ============================================================
-- Load Dimension Tables
-- Project: Darkom Real Estate Data Warehouse
-- Source: clean.darkom_annonces_clean
-- Target: bi_schema dimension tables
-- ============================================================


-- ============================================================
-- Load dim_date
-- ============================================================

INSERT INTO bi_schema.dim_date (
    date_publication,
    annee_publication,
    mois_publication,
    trimestre_publication
)
SELECT DISTINCT
    date_publication,
    annee_publication,
    mois_publication,
    trimestre_publication
FROM clean.darkom_annonces_clean
WHERE date_publication IS NOT NULL
ON CONFLICT (date_publication) DO NOTHING;


-- ============================================================
-- Load dim_location
-- ============================================================

INSERT INTO bi_schema.dim_location (
    ville,
    quartier
)
SELECT DISTINCT
    ville,
    quartier
FROM clean.darkom_annonces_clean
WHERE ville IS NOT NULL
  AND quartier IS NOT NULL
ON CONFLICT (ville, quartier) DO NOTHING;


-- ============================================================
-- Load dim_property
-- ============================================================

INSERT INTO bi_schema.dim_property (
    type_bien,
    categorie_surface,
    surface_bin
)
SELECT DISTINCT
    type_bien,
    categorie_surface,
    surface_bin
FROM clean.darkom_annonces_clean
WHERE type_bien IS NOT NULL
  AND categorie_surface IS NOT NULL
  AND surface_bin IS NOT NULL
ON CONFLICT (type_bien, categorie_surface, surface_bin) DO NOTHING;


-- ============================================================
-- Load dim_transaction
-- ============================================================

INSERT INTO bi_schema.dim_transaction (
    transaction
)
SELECT DISTINCT
    transaction
FROM clean.darkom_annonces_clean
WHERE transaction IS NOT NULL
ON CONFLICT (transaction) DO NOTHING;


-- ============================================================
-- Quick validation
-- ============================================================

SELECT 'dim_date' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_date

UNION ALL

SELECT 'dim_location' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_location

UNION ALL

SELECT 'dim_property' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_property

UNION ALL

SELECT 'dim_transaction' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_transaction;




-- ============================================================
-- Verification
-- ============================================================

-- Count dimension rows
SELECT 'dim_date' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_date

UNION ALL

SELECT 'dim_location' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_location

UNION ALL

SELECT 'dim_property' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_property

UNION ALL

SELECT 'dim_transaction' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.dim_transaction;

-- Preview dimensions
SELECT * FROM bi_schema.dim_date LIMIT 10;
SELECT * FROM bi_schema.dim_location LIMIT 10;
SELECT * FROM bi_schema.dim_property LIMIT 10;
SELECT * FROM bi_schema.dim_transaction LIMIT 10;