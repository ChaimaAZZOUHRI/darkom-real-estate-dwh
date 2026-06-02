-- ============================================================
-- Verification
-- ============================================================

-- Count loaded rows
SELECT COUNT(*) AS total_rows_staging
FROM staging.darkom_annonces_raw;

-- Preview raw data
SELECT *
FROM staging.darkom_annonces_raw
LIMIT 10;

-- Check duplicated annonce_id before cleaning
SELECT
    annonce_id,
    COUNT(*) AS duplicate_count
FROM staging.darkom_annonces_raw
GROUP BY annonce_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Check missing values before cleaning
SELECT
    COUNT(*) FILTER (WHERE annonce_id IS NULL OR annonce_id = '') AS missing_annonce_id,
    COUNT(*) FILTER (WHERE date_publication IS NULL OR date_publication = '') AS missing_date_publication,
    COUNT(*) FILTER (WHERE titre IS NULL OR titre = '') AS missing_titre,
    COUNT(*) FILTER (WHERE ville IS NULL OR ville = '') AS missing_ville,
    COUNT(*) FILTER (WHERE quartier IS NULL OR quartier = '') AS missing_quartier,
    COUNT(*) FILTER (WHERE type_bien IS NULL OR type_bien = '') AS missing_type_bien,
    COUNT(*) FILTER (WHERE transaction IS NULL OR transaction = '') AS missing_transaction,
    COUNT(*) FILTER (WHERE prix IS NULL OR prix = '') AS missing_prix,
    COUNT(*) FILTER (WHERE surface IS NULL OR surface = '') AS missing_surface,
    COUNT(*) FILTER (WHERE nb_chambres IS NULL OR nb_chambres = '') AS missing_nb_chambres,
    COUNT(*) FILTER (WHERE nb_salles_bain IS NULL OR nb_salles_bain = '') AS missing_nb_salles_bain,
    COUNT(*) FILTER (WHERE etage IS NULL OR etage = '') AS missing_etage,
    COUNT(*) FILTER (WHERE annee_construction IS NULL OR annee_construction = '') AS missing_annee_construction
FROM staging.darkom_annonces_raw;