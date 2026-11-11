# 🏗️ Architecture Guide

LakeForge is built on the **Medallion Architecture** pattern, providing an enterprise foundation for transforming raw, multi-source data into governed, curated, business-ready data marts on the Databricks Lakehouse platform.

---

## 🏛️ High-Level System Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           STAGE 0: ENVIRONMENT PROVISIONING                            │
│   Creates environment catalogs, tenant catalogs, and landing volumes:                  │
│   <env>_bronze, <env>_silver, <env>_gold, <env>_quarantine, <env>_<client_id>          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EXTERNAL DATA SOURCES                                │
│   Databases (Oracle, PG, MySQL, MSSQL) • Cloud Storage (S3, ADLS, GCS) • APIs • Kafka  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             LAKEFORGE INGESTION ENGINE                                 │
│  - 16+ Specialized Connectors           - Auto Loader Integration                      │
│  - Dynamic Schema Detector              - Batch & Structured Streaming                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              BRONZE LAYER (Raw Zone)                                   │
│  - Exact raw data representation        - System Audit Metadata Columns                │
│  - Zero data loss retention             - Append & Overwrite partitions                │
│  - File tracking log                    - Landing volumes: /Volumes/<catalog>/landing/ │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼ [Data Quality Gate: DQEngine]
                                    ┌───────┴───────┐
                     [Valid Records]│               │[Failed Records]
                                    ▼               ▼
┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────┐
│          SILVER LAYER (Cleansed Zone)        │  │       BRONZE QUARANTINE TABLE        │
│  - Type Casting & Standardization            │  │  - Isolated bad records              │
│  - Deduplication & Window Ranking            │  │  - Failure reason payload            │
│  - Slowly Changing Dimensions (SCD 1 & 2)    │  │  - Actionable triage audit           │
│  - Dynamic Transformation Chains             │  └──────────────────────────────────────┘
└──────────────────────┬───────────────────────┘
                       │
                       ▼ [Trust Gate: TrustEngine]
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           GOLD LAYER (Business Marts)                                  │
│  - Declarative Star & Snowflake Schemas - Optimized Z-Ordering / Liquid Clustering     │
│  - Dimensional Aggregations             - Multi-Tenant Isolated Datamarts              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         VIEWS & CONSUMPTION LAYER                                      │
│  - Decoupled SQL Views (Bronze / Silver / Gold tiers)                                  │
│  - Centralized Unity Catalog RBAC       - Tag-based column masking (data_protection)   │
│  - Row-Level Access Policies            - Direct BI, Lakeview & AI / ML consumption     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧱 The Medallion Pipeline Stages

### 0. Environment Provisioning (`pipelines/SETUP_Environment_Provisioning.ipynb`)
Before processing begins, automated provisioning ensures all Unity Catalog objects exist:
- **Catalogs**: `<env>_bronze`, `<env>_silver`, `<env>_gold`, `<env>_monitoring`, `<env>_quarantine`.
- **Tenant Catalogs**: `<env>_<client_id>` (e.g. `dev_client_alpha`).
- **Landing Volumes**: Creates `/Volumes/<catalog>/raw_files/landing/` for staging ingestion files.

### 1. Ingestion Engine (`lakeforge.ingestion`)
Abstracts connection logic for batch and streaming sources:
- **Relational Databases**: Oracle, PostgreSQL, MySQL, Azure SQL Server via JDBC with parallel partition extraction.
- **Enterprise Warehouses**: Snowflake, Google BigQuery, AWS Redshift with query pushdown.
- **Cloud Storage**: AWS S3, Azure Data Lake Gen2 (ADLS), Google Cloud Storage (GCS) using Databricks Auto Loader (`cloudFiles`).
- **File Loaders**: CSV (automatic `chardet` encoding detection), Excel (multi-sheet support), JSON, Parquet, and XML.
- **Streaming Platforms**: Apache Kafka and Azure Event Hubs with checkpoints.
- **APIs & SaaS**: Paginated REST API loader with rate-limiting, Jira, SharePoint, and Google Sheets.

### 2. Bronze Layer: Raw Zone (`lakeforge.bronze`)
Preserves incoming records in raw Delta format with standard audit columns:

| Audit Column | Data Type | Description |
|---|---|---|
| `_ingestion_timestamp` | `TIMESTAMP` | Precise UTC timestamp of pipeline ingestion run |
| `_ingestion_date` | `DATE` | UTC date partition key for optimized pruning |
| `_source_system` | `STRING` | Configurable source identifier (e.g. `oracle_erp`, `pos_alpha`) |
| `_record_hash` | `STRING` | MD5 hash of all input values for duplicate detection |
| `_file_path` | `STRING` | Source storage URI or volume file path |

### 3. Silver Layer: Cleansed Zone (`lakeforge.silver`)
Cleanses, enriches, and structures data into reliable operational datasets:
- **DQ Engine Gate**: Runs automated data quality rules before committing to Silver. Failed records are routed to `<env>_quarantine.<table_name>_bad`.
- **Transformation Engine**: Executes chained transformation actions declared in JSON configurations:
  - `cast`: Coerces data types with error handling.
  - `standardize`: Uppercase, lowercase, regex stripping, whitespace trimming.
  - `filter`: SQL boolean expression filters.
  - `derived_column`: Dynamic Spark SQL expressions.
  - `deduplicate`: Windowed row ranking based on primary keys and ordering timestamps.
  - `rename` & `drop`: Field mapping and cleanup.
  - `join`: Dynamic catalog joins with foreign dimension tables.
- **Slowly Changing Dimensions (SCD Type 1 & 2)**:
  - `SCD Type 1`: Overwrites existing records on primary key match.
  - `SCD Type 2`: Retains full version history by managing `effective_start_date`, `effective_end_date` (set to `9999-12-31` for active rows), and boolean `is_current` flags.

### 4. Gold Layer: Curated Marts (`lakeforge.gold`)
Aggregates cleansed Silver tables into optimized business marts:
- **Declarative Aggregations**: Generates SQL aggregation queries automatically from JSON specifications (`groupBy` keys, join predicates, metric expressions like `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`).
- **Liquid Clustering / Z-Ordering**: Automatic partition optimization for fast query response.

### 5. Categorized Views Layer (`lakeforge.views`)
A decoupled semantic layer that builds logical SQL views without replicating physical storage. Organized into three distinct tiers:
- `configs/views/bronze/`: Diagnostic and raw landing inspection views.
- `configs/views/silver/`: Cleaned operational views with tenant overrides (`configs/views/silver/<client_id>/`).
- `configs/views/gold/`: Client-facing reporting views (`configs/views/gold/<client_id>/`).

---

## 🏢 Multi-Bundle Deployment Layout

LakeForge follows the Databricks recommended multi-bundle architecture: **one repository, one bundle per deployment unit**:

```text
lakeforge/
├── databricks.yml                              # MAIN bundle (global medallion job)
├── deployments/                                # PER-CLIENT bundles (one independent bundle per client)
│   └── client_alpha/
│       ├── databricks.yml                      # CLIENT bundle (independent)
│       └── resources/
│           ├── client_alpha_etl_job.yml        # Provisioning -> Bronze -> Silver -> Views -> Governance
│           └── client_alpha_views_job.json     # On-demand views refresh
└── infrastructure/
    ├── databricks/resources/
    │   └── lakeforge_global_job.yml            # Global pipeline workflow
    ├── docker/                                 # Isolated container runtimes
    ├── terraform/                              # Terraform Databricks Workspace & Job IaC
    └── workflows/                              # Orchestration guidelines
```

---

## 🛡️ Centralized Governance & Data Protection

Managed via `lakeforge.governance.governance_engine`:
- **Role-Based Access Control (RBAC)**: Programmatic `GRANT SELECT`, `USAGE`, and `MODIFY` configured in:
  - `configs/governance/access_control.json` (Global catalog & schema permissions)
  - `configs/governance/<client_id>/access_control.json` (Tenant-specific access grants)
- **Data Protection & PII Masking (`configs/governance/data_protection.json`)**: Tag-based column masking policies (SHA-256 hashing, full redaction, email masking) and row-level security filters applied at the Unity Catalog layer.
