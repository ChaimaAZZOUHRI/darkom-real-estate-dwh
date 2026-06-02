-- ============================================================
-- Relationship Checks
-- Project: Darkom Real Estate Data Warehouse
-- Purpose: Validate Data Warehouse relationships and foreign keys
-- ============================================================


-- ============================================================
-- 1. Check row count consistency between clean layer and fact table
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM clean.darkom_annonces_clean) AS clean_rows,
    (SELECT COUNT(*) FROM bi_schema.fact_annonces) AS fact_rows;


-- ============================================================
-- 2. Check missing foreign keys in fact table
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
    COUNT(*) FILTER (WHERE location_id IS NULL) AS missing_location_id,
    COUNT(*) FILTER (WHERE property_id IS NULL) AS missing_property_id,
    COUNT(*) FILTER (WHERE transaction_id IS NULL) AS missing_transaction_id
FROM bi_schema.fact_annonces;


-- ============================================================
-- 3. Check orphan date_id
-- ============================================================

SELECT COUNT(*) AS orphan_date_id
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_date d
    ON f.date_id = d.date_id
WHERE d.date_id IS NULL;


-- ============================================================
-- 4. Check orphan location_id
-- ============================================================

SELECT COUNT(*) AS orphan_location_id
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_location l
    ON f.location_id = l.location_id
WHERE l.location_id IS NULL;


-- ============================================================
-- 5. Check orphan property_id
-- ============================================================

SELECT COUNT(*) AS orphan_property_id
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_property p
    ON f.property_id = p.property_id
WHERE p.property_id IS NULL;


-- ============================================================
-- 6. Check orphan transaction_id
-- ============================================================

SELECT COUNT(*) AS orphan_transaction_id
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_transaction t
    ON f.transaction_id = t.transaction_id
WHERE t.transaction_id IS NULL;


-- ============================================================
-- 7. Check duplicate annonce_id in fact table
-- ============================================================

SELECT
    annonce_id,
    COUNT(*) AS duplicate_count
FROM bi_schema.fact_annonces
GROUP BY annonce_id
HAVING COUNT(*) > 1;


-- ============================================================
-- 8. Check dimension table counts
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
FROM bi_schema.dim_transaction

UNION ALL

SELECT 'fact_annonces' AS table_name, COUNT(*) AS total_rows
FROM bi_schema.fact_annonces;


-- ============================================================
-- 9. Preview final BI model
-- ============================================================

SELECT
    f.annonce_id,
    d.date_publication,
    d.annee_publication,
    d.mois_publication,
    l.ville,
    l.quartier,
    p.type_bien,
    p.categorie_surface,
    t.transaction,
    f.prix,
    f.surface,
    f.prix_m2,
    f.categorie_prix,
    f.is_outlier
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_date d
    ON f.date_id = d.date_id
LEFT JOIN bi_schema.dim_location l
    ON f.location_id = l.location_id
LEFT JOIN bi_schema.dim_property p
    ON f.property_id = p.property_id
LEFT JOIN bi_schema.dim_transaction t
    ON f.transaction_id = t.transaction_id
LIMIT 20;




-- ============================================================
-- Final Relationship Status
-- ============================================================

SELECT
    CASE
        WHEN
            COUNT(*) FILTER (WHERE date_id IS NULL) = 0
            AND COUNT(*) FILTER (WHERE location_id IS NULL) = 0
            AND COUNT(*) FILTER (WHERE property_id IS NULL) = 0
            AND COUNT(*) FILTER (WHERE transaction_id IS NULL) = 0
        THEN 'SUCCESS: All foreign keys are valid'
        ELSE 'WARNING: Some foreign keys are missing'
    END AS relationship_status
FROM bi_schema.fact_annonces;