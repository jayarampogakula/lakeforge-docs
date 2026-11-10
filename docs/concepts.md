# 💡 Core Concepts

Understanding the core concepts behind LakeForge will help you design maintainable, scalable, and audit-proof data architectures.

---

## 📄 1. Metadata-Driven Declarative Pipelines

LakeForge separates **business rules** from **execution engines**. Instead of writing repetitive Spark Python or SQL code for every pipeline, you declare your source, destination, schema drift policies, data quality rules, and transformations in clean JSON configuration files.

### Why Declarative?
- **Zero Boilerplate**: No need to write repetitive `spark.read`, Delta merge, or quarantine try/catch logic.
- **Portability**: The same configuration executes identically in development notebooks, automated CLI runs, CI/CD runners, and Databricks Asset Bundles.
- **Auditable**: Configurations are version-controlled in Git, enabling clear code review and change histories.

---

## 🏢 2. Multi-Tenancy & Client Scoping

LakeForge supports enterprise multi-tenancy out of the box using the `--client` / `client_id` parameter.

### Configuration Hierarchy & Fallback

```text
configs/
├── ingestion/
│   ├── sales.json                 <-- Global / Default config
│   └── customers.json
├── clients/
│   ├── client_alpha/              <-- Client-specific overrides
│   │   ├── ingestion/
│   │   │   └── sales.json         <-- Overrides global sales.json for client_alpha
│   │   └── dq/
│   │       └── sales.json
│   └── client_beta/
│       └── ingestion/
│           └── sales.json
```

### Resolution Rules:
1. When `--client client_alpha` is specified, LakeForge looks first in `configs/clients/client_alpha/<category>/<file>.json`.
2. If found, it merges or overrides the configuration for that client.
3. If not found, it falls back seamlessly to the global `configs/<category>/<file>.json`.
4. Tables are automatically namespaced (e.g. `silver.client_alpha.sales` or tagged with client metadata).

---

## 🔄 3. Schema Evolution & Drift Policies

When upstream schemas change unexpectedly (e.g., source database adds a new column or drops an old one), LakeForge protects downstream integrity through configurable **Drift Policies**:

| Policy | Behavior | Best Used For |
|---|---|---|
| `fail` | Aborts pipeline execution immediately and alerts engineering if unexpected schema differences are detected. | Strict regulatory datasets where unintended columns cannot be processed. |
| `ignore` | Ignores extraneous incoming columns and processes only known schema columns. | Upstream providers who add debug or internal fields that should be discarded. |
| `add_new_columns` (Default) | Uses Delta Lake schema evolution (`mergeSchema=true`) to append new columns without interrupting the pipeline. | Fast-evolving ingestion feeds from SaaS or NoSQL data sources. |

```json
{
  "source_name": "sales_stream",
  "schema_drift": {
    "policy": "add_new_columns",
    "log_drift_to_catalog": true,
    "notify_on_drift": true
  }
}
```

---

## 🛡️ 4. Data Quality Gates & Quarantine Pattern

Traditional pipelines often crash when a single invalid record enters a batch, halting downstream processing. Alternatively, systems that silently ignore errors corrupt downstream reports.

LakeForge employs the **Quarantine Pattern**:

```text
Incoming Ingested Batch
           │
           ▼
     [ DQEngine ]
     ┌─────┴────────────────┐
     ▼                      ▼
Valid Records         Failed Records
     │                      │
     ▼                      ▼
Silver Delta Table    Quarantine Delta Table
(Clean & Trusted)     (Preserved for Investigation)
```

1. Each record is evaluated against data quality rules.
2. Passing records proceed to the **Silver Layer**.
3. Failing records are split into a **Quarantine Table** (`bronze.quarantine.<table_name>_quarantine`).
4. Quarantine records include the original raw payload, the failed rule names, timestamp, and rejection reasons.
5. The pipeline completes successfully, keeping business marts updated while preserving bad data for triage.

---

## ⏳ 5. Slowly Changing Dimensions (SCD Type 1 vs Type 2)

LakeForge provides native, optimized Delta Lake merge implementations for both SCD patterns:

### SCD Type 1 (In-Place Overwrite)
Updates existing records in place whenever non-key attributes change. No historical record is preserved.
- **Use Case**: Correcting typos, customer phone numbers where history is not required.

### SCD Type 2 (History-Preserving)
Maintains full historical change tracking using date ranges and status flags:
- `effective_start_date`: Timestamp or date when the version became active.
- `effective_end_date`: Timestamp when superseded (active records default to `9999-12-31`).
- `is_current`: Boolean flag (`true` for current active record, `false` for historical).

```text
Customer Record Evolution (SCD Type 2):
+----+----------+-----------+------------+------------+------------+
| ID | Name     | City      | StartDate  | EndDate    | is_current |
+----+----------+-----------+------------+------------+------------+
| 1  | Alice    | New York  | 2025-01-01 | 2026-03-15 | false      |
| 1  | Alice    | Chicago   | 2026-03-15 | 9999-12-31 | true       |
+----+----------+-----------+------------+------------+------------+
```

---

## 🎯 6. Trust Score Formulation

The LakeForge **Trust Engine** grades pipeline execution health using a composite score from `0%` to `100%`:

$$\text{Trust Score} = w_{\text{dq}} \cdot S_{\text{dq}} + w_{\text{drift}} \cdot S_{\text{drift}} + w_{\text{volume}} \cdot S_{\text{volume}} + w_{\text{dups}} \cdot S_{\text{dups}}$$

Where:
- $S_{\text{dq}}$: Data Quality pass percentage across all validation rules.
- $S_{\text{drift}}$: Schema consistency score (100% if no unauthorized schema change; penalty applied on drift).
- $S_{\text{volume}}$: Row count drift score (detects unexpected spikes or drops against historical moving averages).
- $S_{\text{dups}}$: Uniqueness score (evaluates key duplication ratio).

### Classification Tiers:
- 🟢 **95% – 100%**: **EXCELLENT** — Production-ready, full confidence.
- 🟡 **85% – 94%**: **GOOD** — Minor non-critical anomalies detected.
- 🟠 **70% – 84%**: **ACCEPTABLE** — Quality alerts triggered, review recommended.
- 🔴 **< 70%**: **CRITICAL** — Data quarantined, downstream publishing paused.
