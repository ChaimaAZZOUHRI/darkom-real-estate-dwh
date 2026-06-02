-- ============================================================
-- Load Fact Table
-- Project: Darkom Real Estate Data Warehouse
-- Source: clean.darkom_annonces_clean
-- Target: bi_schema.fact_annonces
-- ============================================================


INSERT INTO bi_schema.fact_annonces (
    annonce_id,

    date_id,
    location_id,
    property_id,
    transaction_id,

    prix,
    prix_capped,

    surface,
    surface_capped,

    prix_m2,
    prix_m2_capped,

    nb_chambres,
    nb_salles_bain,
    etage,
    annee_construction,
    age_bien,

    categorie_prix,

    is_outlier,
    prix_is_outlier,
    surface_is_outlier,
    prix_m2_is_outlier,

    date_publication_imputed,
    quartier_imputed,
    type_bien_imputed,
    transaction_imputed,
    nb_chambres_imputed,
    nb_salles_bain_imputed,
    etage_imputed,
    annee_construction_imputed
)
SELECT
    c.annonce_id,

    d.date_id,
    l.location_id,
    p.property_id,
    t.transaction_id,

    c.prix,
    c.prix_capped,

    c.surface,
    c.surface_capped,

    c.prix_m2,
    c.prix_m2_capped,

    c.nb_chambres,
    c.nb_salles_bain,
    c.etage,
    c.annee_construction,
    c.age_bien,

    c.categorie_prix,

    c.is_outlier,
    c.prix_is_outlier,
    c.surface_is_outlier,
    c.prix_m2_is_outlier,

    c.date_publication_imputed,
    c.quartier_imputed,
    c.type_bien_imputed,
    c.transaction_imputed,
    c.nb_chambres_imputed,
    c.nb_salles_bain_imputed,
    c.etage_imputed,
    c.annee_construction_imputed

FROM clean.darkom_annonces_clean c

LEFT JOIN bi_schema.dim_date d
    ON c.date_publication = d.date_publication

LEFT JOIN bi_schema.dim_location l
    ON c.ville = l.ville
   AND c.quartier = l.quartier

LEFT JOIN bi_schema.dim_property p
    ON c.type_bien = p.type_bien
   AND c.categorie_surface = p.categorie_surface
   AND c.surface_bin = p.surface_bin

LEFT JOIN bi_schema.dim_transaction t
    ON c.transaction = t.transaction

ON CONFLICT (annonce_id) DO NOTHING;


-- ============================================================
-- Quick validation
-- ============================================================

SELECT COUNT(*) AS total_fact_rows
FROM bi_schema.fact_annonces;


-- Check missing foreign keys
SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
    COUNT(*) FILTER (WHERE location_id IS NULL) AS missing_location_id,
    COUNT(*) FILTER (WHERE property_id IS NULL) AS missing_property_id,
    COUNT(*) FILTER (WHERE transaction_id IS NULL) AS missing_transaction_id
FROM bi_schema.fact_annonces;


-- Compare clean layer and fact table row counts
SELECT
    (SELECT COUNT(*) FROM clean.darkom_annonces_clean) AS clean_rows,
    (SELECT COUNT(*) FROM bi_schema.fact_annonces) AS fact_rows;





-- ============================================================
-- Verification
-- ============================================================

-- Count fact rows
SELECT COUNT(*) AS total_fact_rows
FROM bi_schema.fact_annonces;

-- Compare clean and fact rows
SELECT
    (SELECT COUNT(*) FROM clean.darkom_annonces_clean) AS clean_rows,
    (SELECT COUNT(*) FROM bi_schema.fact_annonces) AS fact_rows;

-- Check missing foreign keys
SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
    COUNT(*) FILTER (WHERE location_id IS NULL) AS missing_location_id,
    COUNT(*) FILTER (WHERE property_id IS NULL) AS missing_property_id,
    COUNT(*) FILTER (WHERE transaction_id IS NULL) AS missing_transaction_id
FROM bi_schema.fact_annonces;

-- Preview final fact table
SELECT *
FROM bi_schema.fact_annonces
LIMIT 10;