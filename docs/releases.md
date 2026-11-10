# 🏷️ Release Notes & Changelog

All notable changes to LakeForge are documented here. LakeForge strictly adheres to [Semantic Versioning 2.0.0](https://semver.org/).

---

## [v1.0.0] - 2026-11-01 (Official Initial Release)

We are thrilled to announce the official release of **LakeForge 1.0.0** — an enterprise-grade, metadata-driven Medallion Lakehouse framework on Databricks!

### ✨ Highlights

#### 1. Ingestion Layer
- Added 16 pre-built connectors across file systems (CSV, Excel, JSON, Parquet, XML), relational databases (Oracle, PostgreSQL, MySQL, Azure SQL), cloud data warehouses (Snowflake, BigQuery, Redshift), streaming (Kafka), and SaaS APIs (Generic REST, Jira, SharePoint, Google Sheets).
- Built-in automatic file encoding detection (`chardet`) and Spark schema detection.
- Native Databricks Auto Loader (`cloudFiles`) integration for streaming cloud ingestion.

#### 2. Bronze Layer & Quarantine
- Automated audit columns: `_ingestion_timestamp`, `_ingestion_date`, `_source_system`, `_record_hash`.
- Schema drift policies: `add_new_columns`, `ignore`, and `fail`.
- File ingestion tracker to ensure idempotent ingestion runs.

#### 3. Data Quality Engine
- Introduced `DQEngine` supporting 10+ core validation rules:
  - Null checks with configurable thresholds.
  - Primary/composite key uniqueness checks.
  - Regex pattern matching for email, phone, and custom formats.
  - Value range boundaries and allowable enumerated lists.
  - Referential integrity validation via left anti-joins.
  - Arbitrary Spark SQL custom expressions.
- Automated routing of defective records to isolated quarantine Delta tables (`bronze.quarantine.<table_name>_quarantine`).

#### 4. Silver Layer & History Management
- Declarative transformation engine supporting `cast`, `standardize`, `filter`, `derived_column`, `deduplicate`, `drop`, `rename`, and `join`.
- Production-grade Slowly Changing Dimension (SCD Type 1 and Type 2) Delta merge engine.

#### 5. Gold Layer & Views
- Declarative dimensional aggregation engine generating SQL queries from JSON specifications.
- Automated creation and replacement of decoupled semantic SQL views.

#### 6. Trust Engine & Observability
- 0 to 100% composite Data Trust Score calculation based on quality pass rate, schema drift, volume stability, and key uniqueness.
- Automated generation of HTML execution reports and Delta logging.
- Structured JSON logging and metric collection.

#### 7. LakeForge CLI
- Unified `lakeforge` command-line executable:
  - `lakeforge init`: Scaffold starter projects.
  - `lakeforge validate`: Verify JSON config schemas and references.
  - `lakeforge run`: Run pipelines across Bronze, Silver, Gold, Views, and Governance stages.
  - `lakeforge deploy`: Automated stage deployment across Dev, Test, Staging, and Prod.

#### 8. Enterprise Governance & Maintenance
- Unity Catalog RBAC management for catalogs, schemas, tables, and views.
- Tag-based column PII masking (SHA-256 hashing and redaction) and row-level access control.
- Automated Delta table maintenance (`OPTIMIZE`, `Z-ORDER BY`, `VACUUM`, `ANALYZE TABLE`).

---

## [v0.9.0-beta] - 2026-10-15

### Added
- Core PySpark ingestion loaders for CSV and Oracle JDBC.
- Basic bronze table writer with audit timestamps.
- Initial implementation of the DQ validation framework.
- Unit testing harness with Pytest.

---

## 📌 Versioning Policy

LakeForge follows `MAJOR.MINOR.PATCH` versioning:
- **MAJOR**: Incompatible API or breaking configuration schema changes.
- **MINOR**: New connectors, validators, CLI subcommands, or backwards-compatible functionality.
- **PATCH**: Backwards-compatible bug fixes, performance improvements, and documentation updates.

### Support Matrix

| LakeForge Version | Python Support | Databricks Runtime | Status |
|---|---|---|---|
| **1.0.x** | 3.9, 3.10, 3.11 | DBR 13.3 LTS, 14.3 LTS, 15.4 LTS | **Active / Current** |
| **0.9.x** | 3.9, 3.10 | DBR 13.3 LTS | EOL (Upgrade to 1.0.0) |
