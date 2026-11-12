# 🏷️ Release Notes & Changelog

All notable changes to LakeForge are documented here. LakeForge strictly adheres to [Semantic Versioning 2.0.0](https://semver.org/).

---

## [v1.2.0] - 2026-11-12 (Stage Registry, Modular Code & PR Reviewer)

### ✨ Key Features & Improvements

#### 1. Central Stage Registry & Multi-Account Deployments
- **Registry Single Source of Truth**: `configs/environments/env_settings.json` now drives all stages for the CLI, Databricks Asset Bundles, notebook environment widgets, and CI/CD pipelines.
- **`lakeforge sync-stages` CLI**: Synchronizes all bundle targets across root `databricks.yml`, `deployments/_template/`, and all active tenant bundles (`deployments/<client_id>/`).
- **Multi-Account Stages**: Support for `workspace_host` in `env_settings.json` to route stages to independent Databricks accounts.
- **Service Principal M2M OAuth**: Support for `DATABRICKS_<STAGE>_CLIENT_ID` / `_CLIENT_SECRET` credential pairs with precedence over static tokens.

#### 2. Modular Python Functions & External SQL Support
- **Modular Transformations**: Extensible Python transformation libraries (`lakeforge/transformations/generic.py`, `custom.py`, and tenant-specific `client_alpha/custom.py`).
- **Modular Aggregations**: Custom Gold mart aggregation libraries (`lakeforge/aggregations/custom.py` and `client_alpha/custom.py`).
- **External SQL Files**: Replaced messy inline JSON SQL with direct references to `.sql` files (`query_file`).

#### 3. Automated PR Reviewer (`lakeforge pr-review`)
- AST-based duplicate function detector to prevent code duplication.
- Test coverage verification and configuration schema validation.
- Automated posting of review feedback directly to PR threads.

#### 4. Client Blueprint Template & Comprehensive Config Dictionaries
- Standardized onboarding blueprint in `deployments/_template/`.
- Exhaustive `template_all_options.json` files in every config directory (`ingestion`, `dq`, `transformations`, `aggregations`, `views`, `governance`).

#### 5. Mirrored CI/CD Suite (GitHub Actions + Azure DevOps)
- Mirrored workflows: `ci_cd.yml`, `pr_review.yml`, `dab_deploy.yml`, `dab_export.yml` in `.github/workflows/` and `azure-pipelines/workflows/`.

---

## [v1.1.0] - 2026-11-10 (Multi-Bundle & Enterprise Orchestration)

### ✨ Key Features & Improvements

#### 1. Multi-Bundle Architecture (`deployments/<client_id>/`)
- Per-client bundles promoted to top-level `deployments/` (`client_alpha: databricks.yml + resources/`).
- Deploy only selected clients without affecting other tenants or the global bundle.
- Global manifests consolidated under `infrastructure/` (Databricks, Docker, Terraform, Workflows).

#### 2. Environment & Volume Provisioning (`SETUP_Environment_Provisioning.ipynb`)
- Automated creation of environment catalogs (`<env>_bronze`, `<env>_silver`, `<env>_gold`, `<env>_quarantine`, `<env>_monitoring`).
- Dynamic provisioning of tenant catalogs (`<env>_<client_id>`) and raw landing volumes (`/Volumes/<env>_<client>/raw_files/landing/`).

#### 3. Category-First Configuration Hierarchy
- Restructured client overrides to `configs/<category>/<client_id>/<file>.json` for improved discoverability and clean directory co-location.
- Organized views into categorized subfolders: `configs/views/bronze/`, `configs/views/silver/`, `configs/views/gold/`.
- Added `configs/governance/data_protection.json` for centralized column-level PII masking and row filters.

#### 4. Serverless Pipeline Runtime & CI Guardrails
- Automatic `/Workspace` path detection for seamless imports in Databricks Serverless environments.
- Bronze `source_system` parameterization and reconstructed Silver transformation dependencies.
- Strict CI/CD branch policy enforcement: `dev` builds from any branch, while `test`, `staging`, and `prod` enforce `main` branch only.

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
