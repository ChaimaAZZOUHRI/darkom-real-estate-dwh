-- ============================================================
-- Create BI Schema / Gold Layer
-- Project: Darkom Real Estate Data Warehouse
-- Layer: Warehouse / BI Schema
-- Purpose: Prepare dimensional tables for Power BI
-- ============================================================


-- Create BI schema if it does not exist
CREATE SCHEMA IF NOT EXISTS bi_schema;


-- Drop fact table first because it depends on dimensions
DROP TABLE IF EXISTS bi_schema.fact_annonces;

-- Drop dimension tables
DROP TABLE IF EXISTS bi_schema.dim_date;
DROP TABLE IF EXISTS bi_schema.dim_location;
DROP TABLE IF EXISTS bi_schema.dim_property;
DROP TABLE IF EXISTS bi_schema.dim_transaction;


-- ============================================================
-- Dimension: Date
-- ============================================================

CREATE TABLE bi_schema.dim_date (
    date_id SERIAL PRIMARY KEY,
    date_publication DATE UNIQUE,
    annee_publication INTEGER,
    mois_publication INTEGER,
    trimestre_publication INTEGER
);


-- ============================================================
-- Dimension: Location
-- ============================================================

CREATE TABLE bi_schema.dim_location (
    location_id SERIAL PRIMARY KEY,
    ville TEXT,
    quartier TEXT,
    UNIQUE (ville, quartier)
);


-- ============================================================
-- Dimension: Property
-- ============================================================

CREATE TABLE bi_schema.dim_property (
    property_id SERIAL PRIMARY KEY,
    type_bien TEXT,
    categorie_surface TEXT,
    surface_bin TEXT,
    UNIQUE (type_bien, categorie_surface, surface_bin)
);


-- ============================================================
-- Dimension: Transaction
-- ============================================================

CREATE TABLE bi_schema.dim_transaction (
    transaction_id SERIAL PRIMARY KEY,
    transaction TEXT UNIQUE
);


-- ============================================================
-- Fact table: Annonces
-- ============================================================

CREATE TABLE bi_schema.fact_annonces (
    fact_id SERIAL PRIMARY KEY,
    annonce_id TEXT UNIQUE,

    date_id INTEGER REFERENCES bi_schema.dim_date(date_id),
    location_id INTEGER REFERENCES bi_schema.dim_location(location_id),
    property_id INTEGER REFERENCES bi_schema.dim_property(property_id),
    transaction_id INTEGER REFERENCES bi_schema.dim_transaction(transaction_id),

    prix NUMERIC,
    prix_capped NUMERIC,

    surface NUMERIC,
    surface_capped NUMERIC,

    prix_m2 NUMERIC,
    prix_m2_capped NUMERIC,

    nb_chambres INTEGER,
    nb_salles_bain INTEGER,
    etage INTEGER,
    annee_construction INTEGER,
    age_bien INTEGER,

    categorie_prix TEXT,

    is_outlier BOOLEAN,
    prix_is_outlier BOOLEAN,
    surface_is_outlier BOOLEAN,
    prix_m2_is_outlier BOOLEAN,

    date_publication_imputed BOOLEAN,
    quartier_imputed BOOLEAN,
    type_bien_imputed BOOLEAN,
    transaction_imputed BOOLEAN,
    nb_chambres_imputed BOOLEAN,
    nb_salles_bain_imputed BOOLEAN,
    etage_imputed BOOLEAN,
    annee_construction_imputed BOOLEAN
);


-- ============================================================
-- Indexes for better performance in Power BI
-- ============================================================

CREATE INDEX idx_fact_annonces_date_id
ON bi_schema.fact_annonces(date_id);

CREATE INDEX idx_fact_annonces_location_id
ON bi_schema.fact_annonces(location_id);

CREATE INDEX idx_fact_annonces_property_id
ON bi_schema.fact_annonces(property_id);

CREATE INDEX idx_fact_annonces_transaction_id
ON bi_schema.fact_annonces(transaction_id);

CREATE INDEX idx_fact_annonces_prix
ON bi_schema.fact_annonces(prix);

CREATE INDEX idx_fact_annonces_surface
ON bi_schema.fact_annonces(surface);

CREATE INDEX idx_fact_annonces_prix_m2
ON bi_schema.fact_annonces(prix_m2);




-- ============================================================
-- Verification
-- ============================================================

-- Check if BI schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'bi_schema';

-- Check created warehouse tables
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'bi_schema'
ORDER BY table_name;

-- Check fact table columns
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'bi_schema'
  AND table_name = 'fact_annonces'
ORDER BY ordinal_position;