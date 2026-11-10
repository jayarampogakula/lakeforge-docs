# 🏗️ Architecture Guide

LakeForge is built on the **Medallion Architecture** pattern, providing an enterprise foundation for transforming raw, multi-source data into governed, curated, business-ready data marts on the Databricks Lakehouse platform.

---

## 🏛️ High-Level System Architecture

```text
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
│  - File tracking log                    - Quarantine staging                           │
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
│  - Decoupled SQL Views                  - Unity Catalog RBAC & Column Masking          │
│  - Row-Level Access Policies            - Direct BI, Lakeview & AI / ML consumption     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧱 The Medallion Data Layers

### 1. Ingestion Engine (`lakeforge.ingestion`)
The ingestion engine abstracts source-specific connection logic. It supports:
- **Relational Databases**: Oracle, PostgreSQL, MySQL, Azure SQL Server via JDBC with parallel partition reading and pushdown predicates.
- **Enterprise Warehouses**: Snowflake, Google BigQuery, AWS Redshift with staged unloads and query pushdown.
- **Cloud Storage**: AWS S3, Azure Data Lake Gen2 (ADLS), Google Cloud Storage (GCS) using Databricks Auto Loader (`cloudFiles`).
- **File Loaders**: CSV (with encoding detection via `chardet`), Excel (multi-sheet support), JSON (nested and multiline), Parquet, and XML.
- **Streaming Platforms**: Apache Kafka and Azure Event Hubs with checkpoint recovery and watermark control.
- **APIs & SaaS**: Generic paginated REST API loader with rate-limiting, Jira, SharePoint, and Google Sheets.

### 2. Bronze Layer: Raw Zone (`lakeforge.bronze`)
The Bronze layer retains raw records in their original format to ensure complete traceability.
Every record written through `BronzeWriter` is enriched with standard audit metadata:

| Audit Column | Data Type | Description |
|---|---|---|
| `_ingestion_timestamp` | `TIMESTAMP` | Precise UTC timestamp of batch or streaming ingestion |
| `_ingestion_date` | `DATE` | UTC date partition key for optimized pruning |
| `_source_system` | `STRING` | Identifier of origin system (e.g. `oracle_crm`, `pos_ny`) |
| `_record_hash` | `STRING` | MD5 hash of all input values for duplicate detection |
| `_file_path` | `STRING` | Source storage URI or volume file path (when applicable) |

### 3. Silver Layer: Cleansed Zone (`lakeforge.silver`)
The Silver layer cleanses, enriches, and structures data into reliable operational datasets:
- **DQ Engine Gate**: Runs automated data quality rules before committing to Silver. Failed records are routed to `bronze.quarantine.<table_name>_quarantine`.
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
The Gold layer provides aggregated metrics optimized for reporting and analytics:
- **Declarative Aggregations**: Generates SQL aggregation queries automatically from JSON specifications (`groupBy` keys, join predicates, metric expressions like `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`).
- **Liquid Clustering / Z-Ordering**: Automatic partition optimization for rapid query response times.

### 5. Views Layer (`lakeforge.views`)
A decoupled semantic layer that builds logical SQL views over Gold and Silver Delta tables without replicating storage. Supports client-specific reporting lenses and row-filtered multi-tenant views.

---

## 🛡️ Cross-Cutting Framework Pillars

### 1. Data Quality Engine (`lakeforge.dq`)
The DQ Engine provides configurable rule-based validations:
- `null_check`: Threshold-enforced null checks.
- `duplicate_check`: Uniqueness constraint validation across composite keys.
- `regex_check`: Pattern matching (emails, phone numbers, postal codes, SSNs).
- `range_check`: Numeric boundaries (`min_value`, `max_value`).
- `datatype_check`: Schema type enforcement.
- `allowed_values`: Enumerated set verification.
- `referential_integrity`: Left anti-joins against parent dimensions.
- `custom_sql`: Arbitrary Spark SQL expressions.

### 2. Trust Engine (`lakeforge.trust_engine`)
The Trust Engine computes a composite **Data Trust Score (0 - 100%)** per pipeline execution:
- Factors: Data quality pass rate, schema drift status, row count drift anomalies, and duplicate explosion rates.
- Results are logged into Delta table `monitoring.logs.trust_validation_log` and can trigger email/Slack webhooks.

### 3. Governance & Security (`lakeforge.governance`)
Centralized management of Unity Catalog security:
- **RBAC**: Programmatic `GRANT SELECT`, `USAGE`, and `MODIFY` on catalogs, schemas, tables, and views to specified Microsoft Entra / Okta user groups.
- **Column-Level PII Masking**: Tag-based column masking (e.g. SHA-256 hashing or redaction for credit cards, emails, SSNs).
- **Row-Level Filtering**: User-context predicates (e.g., `WHERE region = current_user_region()`).

### 4. Table Maintenance Suite (`lakeforge.maintenance`)
Automated Delta Lake health tasks:
- `OPTIMIZE` with `Z-ORDER BY` clustering on high-cardinality join/filter columns.
- `VACUUM` with configurable retention hours (`retention_hours=168` for 7 days) to reclaim dead storage.
- `ANALYZE TABLE COMPUTE STATISTICS` to keep Spark cost-based optimizer (CBO) statistics fresh.

### 5. Observability & Operations (`lakeforge.observability`)
- Structured JSON logging.
- Pipeline execution metrics: duration, bytes read, rows written, memory usage.
- Webhook alerts for Slack, Teams, and PagerDuty on pipeline failure or low Trust Score.
