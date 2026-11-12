# 🗺️ Product Roadmap

This roadmap highlights completed milestones, current engineering priorities, and future architectural initiatives for LakeForge.

---

## 🧭 Milestone Summary

```text
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│        PHASE 1        │ ➔  │        PHASE 2        │ ➔  │        PHASE 3        │ ➔  │        PHASE 4        │
│   Core Architecture   │    │  Enterprise & Bundles │    │   AI & Interoperability│   │  Federated Mesh Plane │
│       [COMPLETED]     │    │       [CURRENT]       │    │       [PLANNED]       │    │       [FUTURE]        │
└───────────────────────┘    └───────────────────────┘    └───────────────────────┘    └───────────────────────┘
```

---

## ✅ Phase 1: Core Medallion Architecture (Completed - v1.0.0)

- [x] **Multi-Source Ingestion Engine**:
  - File loaders: CSV, Excel (multi-sheet), JSON, Parquet, XML.
  - Relational database connectors: Oracle, PostgreSQL, MySQL, Azure SQL.
  - Cloud warehouse pushdowns: Snowflake, Google BigQuery, AWS Redshift.
  - Streaming: Apache Kafka, Structured Streaming.
  - SaaS & APIs: Generic REST API loader, Jira, SharePoint, Google Sheets.
- [x] **Bronze Layer**:
  - Raw audit metadata enrichment (`_ingestion_timestamp`, `_source_system`, `_record_hash`, `_ingestion_date`).
  - Schema inference and schema drift detection.
- [x] **Data Quality Engine**:
  - 10+ core validation checks (`null_check`, `duplicate_check`, `regex_check`, `range_check`, `referential_integrity`, etc.).
  - Automated quarantine table routing.
- [x] **Silver Layer**:
  - Declarative transformation pipeline (`cast`, `standardize`, `derived_column`, `deduplicate`, `join`).
  - Slowly Changing Dimension (SCD Type 1 and Type 2) Delta merge engine.
- [x] **Gold Layer & Views**:
  - Declarative dimensional aggregation engine.
  - Decoupled semantic SQL view manager.
- [x] **Trust Engine & Reporting**:
  - Weighted composite quality scoring (0 - 100%).
  - Automated HTML pipeline execution reports and Delta logging.
- [x] **LakeForge CLI**:
  - Subcommands: `init`, `validate`, `run`, `deploy`.

---

## 🚀 Phase 2: Enterprise Scaling, Multi-Bundle & Governance (v1.1.0 - v1.2.0)

- [x] **Multi-Bundle Architecture (DABs)**:
  - Independent client bundles under `deployments/<client_id>/databricks.yml` and shared root `databricks.yml`.
  - Client onboarding blueprint template in `deployments/_template/`.
- [x] **Central Stage Registry & Multi-Account Architecture**:
  - `configs/environments/env_settings.json` drives bundles, CLI, notebooks, and CI/CD.
  - `lakeforge sync-stages` CLI command for bundle targets synchronization.
  - Multi-account / multi-workspace routing via `workspace_host` and Service Principal M2M OAuth.
- [x] **Modular Python Libraries & External SQL**:
  - Modular PySpark functions in `lakeforge.transformations.*` and `lakeforge.aggregations.*`.
  - External `.sql` file integration (`query_file`).
- [x] **Automated PR Reviewer & Duplicate Detector**:
  - `lakeforge pr-review` CLI tool with AST duplicate function detection.
- [x] **Automated Environment & Volume Provisioning**:
  - `SETUP_Environment_Provisioning.ipynb` dynamically builds `<env>_bronze`, `<env>_silver`, `<env>_gold`, `<env>_quarantine`, `<env>_<client>`, and landing volumes.
- [x] **Category-First Multi-Tenant Scoping**:
  - Clean config hierarchy (`configs/<type>/<client_id>/<file>.json`) with automatic fallback to global defaults.
- [x] **Comprehensive Configuration Templates**:
  - `template_all_options.json` and documentation guide across all configuration directories.
- [x] **Centralized Governance & Data Protection**:
  - Automated Unity Catalog RBAC grants and `data_protection.json` tag-based PII masking policies (SHA-256, redaction).
- [x] **CI/CD Branch Policy Guardrails & Mirrored Workflows**:
  - 4 mirrored workflows (`ci_cd`, `pr_review`, `dab_deploy`, `dab_export`) across GitHub Actions and Azure DevOps.
- [ ] **Enhanced Streaming Connectors**:
  - Native Azure Event Hubs and Google Cloud Pub/Sub connectors.
  - Micro-batch trigger tuning and backpressure telemetry.
- [ ] **Delta Lake 3.x Features**:
  - Support for Delta Liquid Clustering (`CLUSTER BY`) in all automated table maintenance routines.

---

## 🔮 Phase 3: AI-Assisted Engineering & Interoperability (Planned - v1.2.0)

- [ ] **GenAI Pipeline Configuration Assistant**:
  - Natural-language to JSON configuration generator powered by LLMs.
  - Automatic prompt-to-DQ rule generator based on sample dataset profiling.
- [ ] **Multi-Table Format Interoperability**:
  - UniForm support: Query LakeForge Delta tables natively as Apache Iceberg and Apache Hudi without duplicating data.
- [ ] **MLflow Integration**:
  - Direct feature store integration with Databricks Feature Store.
  - Automated ML model training triggers upon Gold mart refreshes.
- [ ] **Real-Time Anomaly Detection**:
  - Machine learning-powered volume and drift anomaly detection in the Trust Engine.

---

## 🌐 Phase 4: Decentralized Data Mesh Plane (Future)

- [ ] **Web-Based Management Portal**:
  - Browser-based visual UI for pipeline authoring, config validation, and quarantine triage.
- [ ] **Federated Data Product Registry**:
  - Self-service data product contract definition and cross-domain data sharing.
- [ ] **Cross-Catalog Data Mesh Governance**:
  - Global federated catalog access synchronization across multiple cloud regions and enterprise subsidiaries.

---

## 💬 Community & Feedback

Have a feature request or architectural suggestion?
- Submit an issue on the [LakeForge GitHub Repository](https://github.com/jayarampogakula/Lakeforge/issues).
- Discuss proposed RFCs in the Discussions tab.
