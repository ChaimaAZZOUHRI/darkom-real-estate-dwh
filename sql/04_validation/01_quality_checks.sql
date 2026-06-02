-- ============================================================
-- Quality Checks
-- Project: Darkom Real Estate Data Warehouse
-- Purpose: Validate staging, clean, and warehouse data quality
-- ============================================================


-- ============================================================
-- 1. Row counts by layer
-- ============================================================

SELECT 'staging.darkom_annonces_raw' AS table_name, COUNT(*) AS total_rows
FROM staging.darkom_annonces_raw

UNION ALL

SELECT 'clean.darkom_annonces_clean' AS table_name, COUNT(*) AS total_rows
FROM clean.darkom_annonces_clean

UNION ALL

SELECT 'bi_schema.fact_annonces' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.fact_annonces;


-- ============================================================
-- 2. Missing values after cleaning
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE date_publication IS NULL) AS missing_date_publication,
    COUNT(*) FILTER (WHERE ville IS NULL) AS missing_ville,
    COUNT(*) FILTER (WHERE quartier IS NULL) AS missing_quartier,
    COUNT(*) FILTER (WHERE type_bien IS NULL) AS missing_type_bien,
    COUNT(*) FILTER (WHERE transaction IS NULL) AS missing_transaction,
    COUNT(*) FILTER (WHERE prix IS NULL) AS missing_prix,
    COUNT(*) FILTER (WHERE surface IS NULL) AS missing_surface,
    COUNT(*) FILTER (WHERE nb_chambres IS NULL) AS missing_nb_chambres,
    COUNT(*) FILTER (WHERE nb_salles_bain IS NULL) AS missing_nb_salles_bain,
    COUNT(*) FILTER (WHERE etage IS NULL) AS missing_etage,
    COUNT(*) FILTER (WHERE annee_construction IS NULL) AS missing_annee_construction
FROM clean.darkom_annonces_clean;


-- ============================================================
-- 3. Imputation summary
-- ============================================================

SELECT
    SUM(date_publication_imputed::int) AS date_publication_imputed,
    SUM(quartier_imputed::int) AS quartier_imputed,
    SUM(type_bien_imputed::int) AS type_bien_imputed,
    SUM(transaction_imputed::int) AS transaction_imputed,
    SUM(nb_chambres_imputed::int) AS nb_chambres_imputed,
    SUM(nb_salles_bain_imputed::int) AS nb_salles_bain_imputed,
    SUM(etage_imputed::int) AS etage_imputed,
    SUM(annee_construction_imputed::int) AS annee_construction_imputed
FROM clean.darkom_annonces_clean;


-- ============================================================
-- 4. Outlier summary
-- ============================================================

SELECT
    SUM(prix_is_outlier::int) AS prix_outliers,
    SUM(surface_is_outlier::int) AS surface_outliers,
    SUM(prix_m2_is_outlier::int) AS prix_m2_outliers,
    SUM(is_outlier::int) AS total_outlier_rows
FROM clean.darkom_annonces_clean;


-- ============================================================
-- 5. Numeric sanity checks
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE prix <= 0) AS invalid_prix,
    COUNT(*) FILTER (WHERE surface <= 0) AS invalid_surface,
    COUNT(*) FILTER (WHERE prix_m2 <= 0) AS invalid_prix_m2,
    COUNT(*) FILTER (WHERE nb_chambres < 0) AS invalid_nb_chambres,
    COUNT(*) FILTER (WHERE nb_salles_bain < 0) AS invalid_nb_salles_bain,
    COUNT(*) FILTER (WHERE etage < 0) AS invalid_etage,
    COUNT(*) FILTER (WHERE age_bien < 0) AS invalid_age_bien
FROM clean.darkom_annonces_clean;


-- ============================================================
-- 6. Distribution by transaction
-- ============================================================

SELECT
    transaction,
    COUNT(*) AS total_annonces,
    ROUND(AVG(prix), 2) AS avg_prix,
    ROUND(AVG(surface), 2) AS avg_surface,
    ROUND(AVG(prix_m2), 2) AS avg_prix_m2
FROM clean.darkom_annonces_clean
GROUP BY transaction
ORDER BY total_annonces DESC;


-- ============================================================
-- 7. Distribution by type_bien
-- ============================================================

SELECT
    type_bien,
    COUNT(*) AS total_annonces,
    ROUND(AVG(prix), 2) AS avg_prix,
    ROUND(AVG(surface), 2) AS avg_surface,
    ROUND(AVG(prix_m2), 2) AS avg_prix_m2
FROM clean.darkom_annonces_clean
GROUP BY type_bien
ORDER BY total_annonces DESC;


-- ============================================================
-- 8. Distribution by city
-- ============================================================

SELECT
    ville,
    COUNT(*) AS total_annonces,
    ROUND(AVG(prix), 2) AS avg_prix,
    ROUND(AVG(surface), 2) AS avg_surface,
    ROUND(AVG(prix_m2), 2) AS avg_prix_m2
FROM clean.darkom_annonces_clean
GROUP BY ville
ORDER BY total_annonces DESC;




-- ============================================================
-- Final Quality Status
-- ============================================================

SELECT
    CASE
        WHEN COUNT(*) = 0 THEN 'SUCCESS: No invalid numeric values detected'
        ELSE 'WARNING: Invalid numeric values detected'
    END AS quality_status
FROM clean.darkom_annonces_clean
WHERE prix <= 0
   OR surface <= 0
   OR prix_m2 <= 0
   OR nb_chambres < 0
   OR nb_salles_bain < 0
   OR etage < 0
   OR age_bien < 0;