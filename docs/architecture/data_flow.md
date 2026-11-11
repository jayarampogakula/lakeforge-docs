# 🌊 LakeForge Data Flow Architecture

This document describes the operational data lifecycle in LakeForge across all Medallion tiers: from source ingestion to Unity Catalog consumption.

---

## 🧭 End-to-End Pipeline Execution Flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           STAGE 0: ENVIRONMENT PROVISIONING                            │
│  - Pipeline: SETUP_Environment_Provisioning.ipynb                                       │
│  - Creates environment catalogs: <env>_bronze, <env>_silver, <env>_gold, <env>_quarantine│
│  - Creates tenant catalogs: <env>_<client_id> (e.g. dev_client_alpha)                   │
│  - Provisions Unity Catalog volumes: /Volumes/<env>_<client>/raw_files/landing/         │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              STAGE 1: BRONZE INGESTION                                  │
│  - Pipeline: Bronze_Generic_Pipeline.ipynb                                              │
│  - Engine: lakeforge.bronze.BronzeWriter                                                │
│  - Connectors: lakeforge.ingestion.* (Auto Loader, JDBC, Kafka, Cloud Storage)         │
│  - Ingests raw data with schema detection & drift handling                              │
│  - Appends system audit metadata: _ingestion_timestamp, _source_system, _record_hash    │
│  - Writes to target: <env>_bronze.<schema>.<table_name>                                 │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 2: DATA QUALITY & QUARANTINE GATE                         │
│  - Engine: lakeforge.dq.DQEngine                                                        │
│  - Validates rules from configs/dq/[<client_id>/]<dataset>.json                         │
│  - Rules: null_check, duplicate_check, regex_check, range_check, allowed_values         │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
      [Failed Rows]  │                                               │ [Passed Rows]
                     ▼                                               ▼
┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────┐
│          BRONZE QUARANTINE STORAGE           │  │       STAGE 3: SILVER TRANSFORMATION │
│ - Target: <env>_quarantine.<table_name>_bad  │  │ - Pipeline: SILVER_Transformation.ipynb
│ - Stores: raw payload, failed rules, reasons │  │ - Engine: lakeforge.silver.transformer
│ - Triage audit and remediation               │  │ - Applies deduplication, type casts, │
└──────────────────────────────────────────────┘  │   standardization, and derived logic │
                                                  │ - Merges via SCD-1 or SCD-2 Engine   │
                                                  │ - Target: <env>_silver.<schema>.<table>
                                                  └──────────────────┬───────────────────┘
                                                                     │
                                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                STAGE 4: GOLD AGGREGATION                                │
│  - Pipeline: GOLD_Aggregation_Pipeline.ipynb                                            │
│  - Engine: lakeforge.gold.aggregations                                                  │
│  - Configs: configs/aggregations/<dataset>.json                                         │
│  - Generates star & snowflake business marts with groupBy keys and aggregate metrics    │
│  - Runs table optimization (OPTIMIZE + Z-ORDER / CLUSTER BY)                            │
│  - Target: <env>_gold.<schema>.<mart_table>                                             │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                STAGE 5: SEMANTIC VIEWS LAYER                            │
│  - Pipeline: VIEWS_Creation_Pipeline.ipynb                                              │
│  - Categorized configurations:                                                          │
│    * configs/views/bronze/  ➔ Diagnostic & landing views                                │
│    * configs/views/silver/  ➔ Cleaned operational views                                 │
│    * configs/views/gold/    ➔ Executive & client reporting views                        │
│  - Tenant-specific views under configs/views/<layer>/<client_id>/                        │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 6: CENTRALIZED GOVERNANCE & DATA PROTECTION                  │
│  - Pipeline: GOVERNANCE_Security_Pipeline.ipynb                                         │
│  - Engine: lakeforge.governance.governance_engine                                       │
│  - Configurations:                                                                      │
│    * configs/governance/access_control.json (Global RBAC grants)                        │
│    * configs/governance/<client_id>/access_control.json (Tenant RBAC overrides)         │
│    * configs/governance/data_protection.json (PII masking rules & row-level filters)    │
│  - Enforces Unity Catalog Grants, tag-based column masking, and row-level predicates    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏢 Multi-Tenant Data Separation Model

In LakeForge, data isolation between clients is guaranteed at both storage and catalog tiers:

1. **Dedicated Client Catalogs**: Each client gets its own dedicated Unity Catalog (`<env>_<client_id>`, e.g. `dev_client_alpha`).
2. **Dedicated Landing Volumes**: Raw files land directly in secure volumes:
   ```text
   /Volumes/<env>_<client_id>/raw_files/landing/
   ```
3. **Decoupled View Layers**: Clients access data exclusively through restricted views governed by Unity Catalog access policies, preventing cross-tenant visibility.
