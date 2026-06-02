import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text


# ============================================================
# Allow Python to import shared utilities from scripts/utils
# ============================================================

SCRIPTS_DIR = Path(__file__).resolve().parents[1]

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))


# ============================================================
# Shared utilities
# ============================================================

from utils.db_connection import get_engine  # noqa: E402
from utils.logging_config import (  # noqa: E402
    get_logger,
    log_step,
    log_missing_values,
)


# ============================================================
# Logger for this script
# ============================================================

logger = get_logger(
    logger_name="transform_clean_data",
    log_filename="transform_clean_data.log",
)


# ============================================================
# Helper functions
# ============================================================

def clean_string(value):
    """
    Clean text values.
    Empty values are converted to None.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "" or value.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None

    return value


def remove_accents(text):
    """
    Remove accents and convert text to lowercase.
    Useful for keyword detection.
    """

    text = clean_string(text)

    if text is None:
        return None

    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))

    return text.lower().strip()


def standardize_text(value, default="Non renseigné"):
    """
    Standardize text values and fill missing values.
    """

    value = clean_string(value)

    if value is None:
        return default

    return value.title()


def standardize_city(city):
    """
    Standardize city names.
    """

    key = remove_accents(city)

    city_mapping = {
        "casa": "Casablanca",
        "casablanca": "Casablanca",
        "rabat": "Rabat",
        "marrakech": "Marrakech",
        "agadir": "Agadir",
        "tanger": "Tanger",
        "kenitra": "Kénitra",
        "fes": "Fès",
        "fez": "Fès",
        "meknes": "Meknès",
        "oujda": "Oujda",
        "tetouan": "Tétouan",
    }

    if key is None:
        return "Non renseigné"

    return city_mapping.get(key, str(city).strip().title())


def normalize_type_bien(value):
    """
    Standardize property type values.
    """

    key = remove_accents(value)

    if key is None:
        return None

    type_mapping = {
        "appartement": "Appartement",
        "appart": "Appartement",
        "villa": "Villa",
        "terrain": "Terrain",
        "bureau": "Bureau",
        "duplex": "Duplex",
    }

    return type_mapping.get(key, str(value).strip().title())


def infer_type_bien(row):
    """
    Infer missing property type from title.
    """

    existing_type = normalize_type_bien(row["type_bien"])

    if existing_type is not None:
        return existing_type

    titre = remove_accents(row["titre"])

    if titre is None:
        return "Non renseigné"

    if "terrain" in titre or "lot" in titre:
        return "Terrain"

    if "appartement" in titre or "appart" in titre:
        return "Appartement"

    if "villa" in titre:
        return "Villa"

    if "bureau" in titre:
        return "Bureau"

    if "duplex" in titre:
        return "Duplex"

    return "Non renseigné"


def normalize_transaction(value):
    """
    Standardize transaction values.
    """

    key = remove_accents(value)

    if key is None:
        return None

    if key in {"vente", "vendre", "a vendre"}:
        return "Vente"

    if key in {"location", "louer", "a louer"}:
        return "Location"

    return str(value).strip().title()


def find_transaction_price_threshold(df):
    """
    Estimate a data-driven price threshold to distinguish Vente and Location.

    Rule tested:
    prix > threshold  -> Vente
    prix <= threshold -> Location
    """

    temp = df.copy()
    temp["transaction_norm"] = temp["transaction"].apply(normalize_transaction)

    labeled_df = temp[
        temp["transaction_norm"].isin(["Vente", "Location"])
        & temp["prix"].notna()
    ].copy()

    if labeled_df.empty or labeled_df["transaction_norm"].nunique() < 2:
        logger.warning(
            "Transaction threshold could not be estimated. "
            "Default threshold used: 100000"
        )
        return 100000

    labeled_df["target"] = labeled_df["transaction_norm"].map(
        {"Location": 0, "Vente": 1}
    )

    prices = sorted(labeled_df["prix"].dropna().unique())

    if len(prices) < 2:
        logger.warning(
            "Not enough price values for threshold estimation. "
            "Default threshold used: 100000"
        )
        return 100000

    candidate_thresholds = [
        (prices[i] + prices[i + 1]) / 2
        for i in range(len(prices) - 1)
    ]

    best_threshold = 100000
    best_score = -1

    for threshold in candidate_thresholds:
        predicted = (labeled_df["prix"] > threshold).astype(int)
        true = labeled_df["target"]

        true_positive = ((predicted == 1) & (true == 1)).sum()
        true_negative = ((predicted == 0) & (true == 0)).sum()
        false_positive = ((predicted == 1) & (true == 0)).sum()
        false_negative = ((predicted == 0) & (true == 1)).sum()

        sensitivity_denominator = true_positive + false_negative
        specificity_denominator = true_negative + false_positive

        if sensitivity_denominator == 0 or specificity_denominator == 0:
            continue

        sensitivity = true_positive / sensitivity_denominator
        specificity = true_negative / specificity_denominator

        balanced_accuracy = (sensitivity + specificity) / 2

        if balanced_accuracy > best_score:
            best_score = balanced_accuracy
            best_threshold = threshold

    logger.info("Estimated transaction threshold: %s MAD", round(best_threshold, 2))
    logger.info("Threshold balanced accuracy: %s", round(best_score, 4))

    return round(best_threshold, 2)


def infer_transaction(row, transaction_price_threshold):
    """
    Infer missing transaction using:
    1. Existing transaction
    2. Keywords in title
    3. Data-driven price threshold
    """

    existing_transaction = normalize_transaction(row["transaction"])

    if existing_transaction is not None:
        return existing_transaction

    titre = remove_accents(row["titre"])

    if titre is not None:
        if "location" in titre or "louer" in titre or "a louer" in titre:
            return "Location"

        if "vente" in titre or "vendre" in titre or "a vendre" in titre:
            return "Vente"

    if pd.notna(row["prix"]):
        if row["prix"] > transaction_price_threshold:
            return "Vente"
        return "Location"

    return "Non renseigné"


def categorize_surface(surface):
    """
    Create surface categories.
    """

    if pd.isna(surface):
        return "Non renseigné"

    if surface < 80:
        return "Petit"

    if surface <= 150:
        return "Moyen"

    return "Grand"


def categorize_price(row):
    """
    Create price categories depending on transaction type.
    """

    price = row["prix"]
    transaction = row["transaction"]

    if pd.isna(price):
        return "Non renseigné"

    if transaction == "Location":
        if price <= 3000:
            return "Économique"
        if price <= 7000:
            return "Moyen"
        if price <= 15000:
            return "Haut standing"
        return "Luxe"

    if transaction == "Vente":
        if price <= 600000:
            return "Économique"
        if price <= 1500000:
            return "Moyen"
        if price <= 3000000:
            return "Haut standing"
        return "Luxe"

    return "Non renseigné"


def fill_by_group_median(df, column, group_columns):
    """
    Fill missing values using median of similar groups.
    """

    before_missing = int(df[column].isna().sum())

    df[column] = df[column].fillna(
        df.groupby(group_columns, observed=False)[column].transform("median")
    )

    after_missing = int(df[column].isna().sum())

    logger.info(
        "Filled %s using group median %s | before: %s | after: %s | filled: %s",
        column,
        group_columns,
        before_missing,
        after_missing,
        before_missing - after_missing,
    )

    return df


def add_outlier_flags_and_capped_values(df, column, group_columns=None):
    """
    Detect outliers using IQR.

    Original values are preserved.
    Capped values are created separately.
    """

    outlier_col = f"{column}_is_outlier"
    capped_col = f"{column}_capped"

    df[outlier_col] = False
    df[capped_col] = df[column]

    if group_columns is None:
        groups = [(None, df.index)]
    else:
        groups = df.groupby(
            group_columns,
            observed=False,
            dropna=False,
        ).groups.items()

    for group_name, group_index in groups:
        values = df.loc[group_index, column].dropna()

        if len(values) < 4:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1

        if pd.isna(iqr) or iqr == 0:
            continue

        lower_bound = max(0, q1 - 1.5 * iqr)
        upper_bound = q3 + 1.5 * iqr

        is_outlier = (
            (df.loc[group_index, column] < lower_bound)
            | (df.loc[group_index, column] > upper_bound)
        )

        df.loc[group_index, outlier_col] = is_outlier.fillna(False)

        df.loc[group_index, capped_col] = df.loc[group_index, column].clip(
            lower=lower_bound,
            upper=upper_bound,
        )

        logger.info(
            "Outlier check | column: %s | group: %s | lower: %s | upper: %s | outliers: %s",
            column,
            group_name,
            round(lower_bound, 2),
            round(upper_bound, 2),
            int(is_outlier.sum()),
        )

    total_outliers = int(df[outlier_col].sum())

    logger.info("Total outliers detected for %s: %s", column, total_outliers)

    return df


# ============================================================
# PostgreSQL table creation
# ============================================================

def create_clean_table():
    """
    Create the clean table in PostgreSQL.
    """

    create_sql = """
    CREATE SCHEMA IF NOT EXISTS clean;

    DROP TABLE IF EXISTS clean.darkom_annonces_clean;

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
    """

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(create_sql))

    logger.info("Clean table created successfully.")


# ============================================================
# Main cleaning pipeline
# ============================================================

def transform_clean_data():
    """
    Cleaning pipeline:
    staging.darkom_annonces_raw -> clean.darkom_annonces_clean
    """

    try:
        logger.info("")
        logger.info("#" * 90)
        logger.info("STARTING CLEAN DATA TRANSFORMATION")
        logger.info("#" * 90)

        engine = get_engine()

        # ------------------------------------------------------------
        # Step 1 - Load raw data from staging
        # ------------------------------------------------------------

        log_step(logger, 1, "LOAD DATA FROM STAGING")

        df = pd.read_sql_query(
            "SELECT * FROM staging.darkom_annonces_raw;",
            engine,
        )

        logger.info("Rows loaded from staging: %s", df.shape[0])
        logger.info("Columns loaded from staging: %s", df.shape[1])
        logger.info("Columns: %s", list(df.columns))

        # ------------------------------------------------------------
        # Step 2 - Initial missing values
        # ------------------------------------------------------------

        log_step(logger, 2, "INITIAL MISSING VALUES BEFORE CLEANING")

        log_missing_values(
            logger,
            df,
            df.columns,
            "raw staging data",
        )

        # ------------------------------------------------------------
        # Step 3 - Remove duplicates
        # ------------------------------------------------------------

        log_step(logger, 3, "REMOVE DUPLICATED ANNONCE_ID")

        initial_rows = len(df)
        duplicated_ids = int(df["annonce_id"].duplicated().sum())

        logger.info("Duplicated annonce_id before cleaning: %s", duplicated_ids)

        df = df.drop_duplicates(subset=["annonce_id"], keep="first").copy()

        logger.info("Rows before duplicate removal: %s", initial_rows)
        logger.info("Rows after duplicate removal: %s", len(df))
        logger.info("Rows removed: %s", initial_rows - len(df))

        # ------------------------------------------------------------
        # Step 4 - Clean text columns
        # ------------------------------------------------------------

        log_step(logger, 4, "CLEAN TEXT COLUMNS")

        text_columns = ["titre", "ville", "quartier", "type_bien", "transaction"]

        for col in text_columns:
            before_missing = int(df[col].isna().sum())
            df[col] = df[col].apply(clean_string)
            after_missing = int(df[col].isna().sum())

            logger.info(
                "Text column cleaned: %s | missing before: %s | missing after: %s",
                col,
                before_missing,
                after_missing,
            )

        df["titre"] = df["titre"].apply(
            lambda x: standardize_text(x, default="Sans titre")
        )

        df["ville"] = df["ville"].apply(standardize_city)

        logger.info("Titles standardized.")
        logger.info("City names standardized.")

        # ------------------------------------------------------------
        # Step 5 - Convert numeric columns
        # ------------------------------------------------------------

        log_step(logger, 5, "CONVERT NUMERIC COLUMNS")

        numeric_columns = [
            "prix",
            "surface",
            "nb_chambres",
            "nb_salles_bain",
            "etage",
            "annee_construction",
        ]

        for col in numeric_columns:
            before_valid = int(df[col].notna().sum())

            df[col] = pd.to_numeric(df[col], errors="coerce")

            after_valid = int(df[col].notna().sum())
            invalid_created = before_valid - after_valid

            logger.info(
                "Numeric conversion: %s | valid before: %s | valid after: %s | invalid created: %s",
                col,
                before_valid,
                after_valid,
                invalid_created,
            )

        # ------------------------------------------------------------
        # Step 6 - Remove impossible numeric values
        # ------------------------------------------------------------

        log_step(logger, 6, "HANDLE IMPOSSIBLE NUMERIC VALUES")

        invalid_price_count = int((df["prix"] <= 0).sum())
        invalid_surface_count = int((df["surface"] <= 0).sum())

        df.loc[df["prix"] <= 0, "prix"] = np.nan
        df.loc[df["surface"] <= 0, "surface"] = np.nan

        logger.info(
            "Invalid price values converted to missing: %s",
            invalid_price_count,
        )
        logger.info(
            "Invalid surface values converted to missing: %s",
            invalid_surface_count,
        )

        # ------------------------------------------------------------
        # Step 7 - Convert and impute date
        # ------------------------------------------------------------

        log_step(logger, 7, "CONVERT AND IMPUTE DATE_PUBLICATION")

        df["date_publication"] = pd.to_datetime(
            df["date_publication"],
            errors="coerce",
        )

        df["date_publication_imputed"] = df["date_publication"].isna()

        missing_dates = int(df["date_publication_imputed"].sum())

        median_date = df["date_publication"].dropna().median()

        if pd.isna(median_date):
            median_date = pd.Timestamp("2026-01-01")

        df["date_publication"] = df["date_publication"].fillna(median_date)

        logger.info("Missing dates before imputation: %s", missing_dates)
        logger.info("Median date used for imputation: %s", median_date)
        logger.info(
            "Missing dates after imputation: %s",
            int(df["date_publication"].isna().sum()),
        )

        # ------------------------------------------------------------
        # Step 8 - Create imputation flags
        # ------------------------------------------------------------

        log_step(logger, 8, "CREATE IMPUTATION FLAGS")

        df["quartier_imputed"] = df["quartier"].isna()
        df["type_bien_imputed"] = df["type_bien"].isna()
        df["transaction_imputed"] = df["transaction"].isna()
        df["nb_chambres_imputed"] = df["nb_chambres"].isna()
        df["nb_salles_bain_imputed"] = df["nb_salles_bain"].isna()
        df["etage_imputed"] = df["etage"].isna()
        df["annee_construction_imputed"] = df["annee_construction"].isna()

        imputation_flags = [
            "date_publication_imputed",
            "quartier_imputed",
            "type_bien_imputed",
            "transaction_imputed",
            "nb_chambres_imputed",
            "nb_salles_bain_imputed",
            "etage_imputed",
            "annee_construction_imputed",
        ]

        for col in imputation_flags:
            logger.info("%s: %s rows", col, int(df[col].sum()))

        # ------------------------------------------------------------
        # Step 9 - Infer type_bien
        # ------------------------------------------------------------

        log_step(logger, 9, "INFER AND STANDARDIZE TYPE_BIEN")

        missing_type_before = int(df["type_bien"].isna().sum())

        df["type_bien"] = df.apply(infer_type_bien, axis=1)

        logger.info("Missing type_bien before inference: %s", missing_type_before)
        logger.info(
            "Missing type_bien after inference: %s",
            int(df["type_bien"].isna().sum()),
        )
        logger.info("Type_bien distribution after inference:")
        logger.info("\n%s", df["type_bien"].value_counts(dropna=False).to_string())

        # ------------------------------------------------------------
        # Step 10 - Infer transaction
        # ------------------------------------------------------------

        log_step(logger, 10, "INFER AND STANDARDIZE TRANSACTION")

        missing_transaction_before = int(df["transaction"].isna().sum())

        transaction_price_threshold = find_transaction_price_threshold(df)

        df["transaction"] = df.apply(
            lambda row: infer_transaction(row, transaction_price_threshold),
            axis=1,
        )

        logger.info(
            "Missing transaction before inference: %s",
            missing_transaction_before,
        )
        logger.info(
            "Missing transaction after inference: %s",
            int(df["transaction"].isna().sum()),
        )
        logger.info("Transaction threshold used: %s MAD", transaction_price_threshold)
        logger.info("Transaction distribution after inference:")
        logger.info("\n%s", df["transaction"].value_counts(dropna=False).to_string())

        # ------------------------------------------------------------
        # Step 11 - Fill quartier
        # ------------------------------------------------------------

        log_step(logger, 11, "FILL QUARTIER")

        missing_quartier_before = int(df["quartier"].isna().sum())

        df["quartier"] = df["quartier"].apply(
            lambda x: standardize_text(x, default="Non renseigné")
        )

        logger.info("Missing quartier before filling: %s", missing_quartier_before)
        logger.info(
            "Missing quartier after filling: %s",
            int(df["quartier"].isna().sum()),
        )

        # ------------------------------------------------------------
        # Step 12 - Create surface bins
        # ------------------------------------------------------------

        log_step(logger, 12, "CREATE SURFACE BINS")

        bins = [0, 50, 100, 200, float("inf")]
        labels = ["<50", "50-100", "100-200", "200+"]

        df["surface_bin"] = pd.cut(
            df["surface"],
            bins=bins,
            labels=labels,
            include_lowest=True,
        )

        logger.info("Surface bins created.")
        logger.info("Surface bin distribution:")
        logger.info("\n%s", df["surface_bin"].value_counts(dropna=False).to_string())

        # ------------------------------------------------------------
        # Step 13 - Apply real-estate business rules
        # ------------------------------------------------------------

        log_step(logger, 13, "APPLY BUSINESS RULES")

        terrain_count = int((df["type_bien"] == "Terrain").sum())
        villa_missing_floor = int(
            ((df["type_bien"] == "Villa") & (df["etage"].isna())).sum()
        )

        df.loc[
            df["type_bien"] == "Terrain",
            ["nb_chambres", "nb_salles_bain", "etage"],
        ] = 0

        df.loc[df["type_bien"] == "Villa", "etage"] = df.loc[
            df["type_bien"] == "Villa",
            "etage",
        ].fillna(0)

        logger.info("Terrain rows set to 0 rooms/bathrooms/floor: %s", terrain_count)
        logger.info("Villa rows with missing floor set to 0: %s", villa_missing_floor)

        # ------------------------------------------------------------
        # Step 14 - Impute numeric missing values
        # ------------------------------------------------------------

        log_step(logger, 14, "IMPUTE NUMERIC MISSING VALUES")

        log_missing_values(
            logger,
            df,
            ["nb_chambres", "nb_salles_bain", "etage", "annee_construction"],
            "before numeric imputation",
        )

        df = fill_by_group_median(df, "nb_chambres", ["type_bien", "surface_bin"])
        df = fill_by_group_median(df, "nb_chambres", ["surface_bin"])

        before_final = int(df["nb_chambres"].isna().sum())
        df["nb_chambres"] = df["nb_chambres"].fillna(df["nb_chambres"].median())

        logger.info(
            "Final fallback for nb_chambres using global median | before: %s | after: %s",
            before_final,
            int(df["nb_chambres"].isna().sum()),
        )

        df = fill_by_group_median(df, "nb_salles_bain", ["type_bien", "surface_bin"])
        df = fill_by_group_median(df, "nb_salles_bain", ["type_bien"])

        before_final = int(df["nb_salles_bain"].isna().sum())
        df["nb_salles_bain"] = df["nb_salles_bain"].fillna(
            df["nb_salles_bain"].median()
        )

        logger.info(
            "Final fallback for nb_salles_bain using global median | before: %s | after: %s",
            before_final,
            int(df["nb_salles_bain"].isna().sum()),
        )

        df = fill_by_group_median(df, "etage", ["type_bien"])

        before_final = int(df["etage"].isna().sum())
        df["etage"] = df["etage"].fillna(df["etage"].median())

        logger.info(
            "Final fallback for etage using global median | before: %s | after: %s",
            before_final,
            int(df["etage"].isna().sum()),
        )

        before_final = int(df["annee_construction"].isna().sum())
        df["annee_construction"] = df["annee_construction"].fillna(
            df["annee_construction"].median()
        )

        logger.info(
            "annee_construction filled using global median | before: %s | after: %s",
            before_final,
            int(df["annee_construction"].isna().sum()),
        )

        log_missing_values(
            logger,
            df,
            ["nb_chambres", "nb_salles_bain", "etage", "annee_construction"],
            "after numeric imputation",
        )

        # ------------------------------------------------------------
        # Step 15 - Convert integer columns
        # ------------------------------------------------------------

        log_step(logger, 15, "CONVERT INTEGER COLUMNS")

        integer_columns = [
            "nb_chambres",
            "nb_salles_bain",
            "etage",
            "annee_construction",
        ]

        for col in integer_columns:
            df[col] = df[col].round().astype("Int64")
            logger.info("Column converted to integer: %s", col)

        # ------------------------------------------------------------
        # Step 16 - Create temporal variables
        # ------------------------------------------------------------

        log_step(logger, 16, "CREATE TEMPORAL VARIABLES")

        df["annee_publication"] = df["date_publication"].dt.year.astype("Int64")
        df["mois_publication"] = df["date_publication"].dt.month.astype("Int64")
        df["trimestre_publication"] = df["date_publication"].dt.quarter.astype(
            "Int64"
        )

        logger.info(
            "annee_publication, mois_publication, trimestre_publication created."
        )
        logger.info("Publication year distribution:")
        logger.info("\n%s", df["annee_publication"].value_counts(dropna=False).to_string())

        # ------------------------------------------------------------
        # Step 17 - Feature engineering
        # ------------------------------------------------------------

        log_step(logger, 17, "FEATURE ENGINEERING")

        df["prix_m2"] = df["prix"] / df["surface"]

        df["age_bien"] = (
            df["annee_publication"] - df["annee_construction"]
        ).clip(lower=0).round().astype("Int64")

        df["categorie_surface"] = df["surface"].apply(categorize_surface)
        df["categorie_prix"] = df.apply(categorize_price, axis=1)

        logger.info("prix_m2 created.")
        logger.info("age_bien created.")
        logger.info("categorie_surface created.")
        logger.info("categorie_prix created.")

        logger.info("categorie_surface distribution:")
        logger.info("\n%s", df["categorie_surface"].value_counts(dropna=False).to_string())

        logger.info("categorie_prix distribution:")
        logger.info("\n%s", df["categorie_prix"].value_counts(dropna=False).to_string())

        # ------------------------------------------------------------
        # Step 18 - Detect outliers and create capped values
        # ------------------------------------------------------------

        log_step(logger, 18, "OUTLIER DETECTION AND CAPPING")

        df = add_outlier_flags_and_capped_values(
            df,
            column="prix",
            group_columns=["transaction"],
        )

        df = add_outlier_flags_and_capped_values(
            df,
            column="surface",
            group_columns=["type_bien"],
        )

        df = add_outlier_flags_and_capped_values(
            df,
            column="prix_m2",
            group_columns=["transaction", "type_bien"],
        )

        df["is_outlier"] = (
            df["prix_is_outlier"]
            | df["surface_is_outlier"]
            | df["prix_m2_is_outlier"]
        )

        logger.info("Global outlier rows: %s", int(df["is_outlier"].sum()))

        # ------------------------------------------------------------
        # Step 19 - Final formatting
        # ------------------------------------------------------------

        log_step(logger, 19, "FINAL FORMATTING BEFORE LOAD")

        df["surface_bin"] = df["surface_bin"].astype(str)
        df["surface_bin"] = df["surface_bin"].replace("nan", "Non renseigné")

        final_columns = [
            "annonce_id",
            "date_publication",
            "titre",
            "ville",
            "quartier",
            "type_bien",
            "transaction",
            "prix",
            "surface",
            "nb_chambres",
            "nb_salles_bain",
            "etage",
            "annee_construction",
            "prix_m2",
            "age_bien",
            "surface_bin",
            "categorie_prix",
            "categorie_surface",
            "annee_publication",
            "mois_publication",
            "trimestre_publication",
            "date_publication_imputed",
            "quartier_imputed",
            "type_bien_imputed",
            "transaction_imputed",
            "nb_chambres_imputed",
            "nb_salles_bain_imputed",
            "etage_imputed",
            "annee_construction_imputed",
            "prix_is_outlier",
            "surface_is_outlier",
            "prix_m2_is_outlier",
            "is_outlier",
            "prix_capped",
            "surface_capped",
            "prix_m2_capped",
        ]

        df = df[final_columns]

        df["date_publication"] = pd.to_datetime(df["date_publication"]).dt.date

        df_to_load = df.astype(object).where(pd.notna(df), None)

        logger.info("Final clean dataframe rows: %s", df_to_load.shape[0])
        logger.info("Final clean dataframe columns: %s", df_to_load.shape[1])
        logger.info("Final columns: %s", list(df_to_load.columns))

        # ------------------------------------------------------------
        # Step 20 - Create clean table and load data
        # ------------------------------------------------------------

        log_step(logger, 20, "CREATE CLEAN TABLE AND LOAD DATA")

        create_clean_table()

        with engine.begin() as conn:
            df_to_load.to_sql(
                name="darkom_annonces_clean",
                con=conn,
                schema="clean",
                if_exists="append",
                index=False,
                method="multi",
            )

            total_rows = conn.execute(
                text("SELECT COUNT(*) FROM clean.darkom_annonces_clean;")
            ).scalar()

        logger.info("Rows inserted into clean.darkom_annonces_clean: %s", total_rows)

        # ------------------------------------------------------------
        # Step 21 - Final validation
        # ------------------------------------------------------------

        log_step(logger, 21, "FINAL VALIDATION")

        logger.info("Expected clean rows: %s", df_to_load.shape[0])
        logger.info("Rows found in PostgreSQL clean table: %s", total_rows)

        if total_rows == df_to_load.shape[0]:
            logger.info("Validation status: SUCCESS. Row counts match.")
        else:
            logger.warning("Validation status: WARNING. Row counts do not match.")

        logger.info("")
        logger.info("#" * 90)
        logger.info("CLEAN DATA TRANSFORMATION FINISHED SUCCESSFULLY")
        logger.info("#" * 90)

    except Exception as error:
        logger.exception("Clean data transformation failed: %s", error)
        raise


if __name__ == "__main__":
    transform_clean_data()