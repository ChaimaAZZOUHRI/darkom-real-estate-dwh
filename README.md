# Darkom Real Estate Data Warehouse

Projet de **Business Intelligence** de bout en bout pour l’analyse du marché immobilier marocain à partir des annonces de **Darkom.ma**.

L’objectif de ce projet est de construire un pipeline complet permettant de transformer des données brutes issues d’un fichier CSV en un **Data Warehouse structuré**, puis en **tableaux de bord Power BI interactifs** pour l’analyse décisionnelle.

---

## Objectif du projet

Ce projet vise à :

- charger des annonces immobilières brutes dans PostgreSQL
- nettoyer et transformer les données
- concevoir un schéma BI dimensionnel
- créer des indicateurs métiers pertinents
- construire des dashboards Power BI interactifs
- produire des insights pour l’aide à la décision

---

## Architecture du projet

Le projet suit le pipeline suivant :

**CSV → Staging → Clean → Data Warehouse → Power BI**

### Étapes principales
1. **Source**
   - fichier `darkom_annonces.csv`

2. **Staging**
   - chargement brut des données dans PostgreSQL
   - vérification de l’intégrité du chargement
   - logs de suivi

3. **Clean**
   - suppression des doublons
   - gestion des valeurs manquantes
   - traitement des valeurs aberrantes
   - standardisation des villes, types de biens et transactions
   - correction des types de données

4. **Feature engineering**
   - prix par m²
   - âge estimé du bien
   - catégories de prix
   - catégories de surface
   - dimensions temporelles

5. **Data Warehouse**
   - schéma BI dimensionnel optimisé pour l’analyse
   - table de faits + tables de dimensions

6. **Power BI**
   - tableaux de bord interactifs
   - KPIs dynamiques
   - filtres analytiques

---

## Structure du projet

```text
darkom-real-estate-dwh/
├── .venv/
├── data/
├── docs/
├── logs/
├── powerbi/
├── scripts/
├── sql/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
