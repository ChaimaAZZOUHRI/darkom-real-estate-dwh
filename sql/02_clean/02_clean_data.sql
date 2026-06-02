-- ============================================================
-- Verification
-- ============================================================

-- Count clean rows
SELECT COUNT(*) AS total_rows_clean
FROM clean.darkom_annonces_clean;

-- Preview clean data
SELECT *
FROM clean.darkom_annonces_clean
LIMIT 10;

-- Check missing values after cleaning
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

-- Check imputation flags
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

-- Check outliers
SELECT
    SUM(prix_is_outlier::int) AS prix_outliers,
    SUM(surface_is_outlier::int) AS surface_outliers,
    SUM(prix_m2_is_outlier::int) AS prix_m2_outliers,
    SUM(is_outlier::int) AS total_outlier_rows
FROM clean.darkom_annonces_clean;

-- Check engineered variables
SELECT
    annonce_id,
    prix,
    surface,
    prix_m2,
    age_bien,
    categorie_prix,
    categorie_surface,
    is_outlier
FROM clean.darkom_annonces_clean
LIMIT 20;