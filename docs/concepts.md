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

### Category-First Configuration Hierarchy

Configurations follow a category-first directory pattern, keeping configs of the same type adjacent while enabling seamless client overrides:

```text
configs/
├── ingestion/
│   ├── sales.json                    <-- Global / Default config
│   └── client_alpha/
│       └── sales.json                <-- Overrides global sales.json for client_alpha
├── dq/
│   ├── sales.json                    <-- Global DQ rules
│   └── client_alpha/
│       └── sales.json                <-- Overrides DQ rules for client_alpha
├── transformations/
│   ├── sales_clean.json              <-- Global Silver transform
│   └── client_alpha/
│       └── sales_clean.json          <-- Overrides transform for client_alpha
├── views/
│   ├── bronze/                       <-- Diagnostic & landing views
│   ├── silver/
│   │   ├── reporting_views.json
│   │   └── client_alpha/
│   │       └── sales_views.json      <-- Client-specific Silver views
│   └── gold/
│       └── client_alpha/
│           └── sales_views.json      <-- Client-specific Gold reporting views
└── governance/
    ├── access_control.json           <-- Global RBAC catalog & schema grants
    ├── client_alpha/
    │   └── access_control.json       <-- Client Alpha RBAC overrides
    └── data_protection.json          <-- Column PII masking & row security
```

### Resolution Rules (`lakeforge.metadata.ConfigParser`):
1. When `--client client_alpha` is specified, LakeForge looks first in `configs/<category>/<client_id>/<file>.json`.
2. If found, it merges or overrides the configuration for that client.
3. If not found, it falls back seamlessly to the global `configs/<category>/<file>.json`.
4. Tables are automatically namespaced (e.g. `<env>_client_alpha.sales` or tagged with client metadata).

---

## 📦 3. Independent Multi-Bundle Deployment Pattern & Blueprint Template

Databricks recommends deploying independent bundles per tenant. LakeForge structures bundles to isolate deployments:

- **Global Main Bundle** (`databricks.yml` at root): Deploys the shared framework and global workflows (`infrastructure/databricks/resources/lakeforge_global_job.yml`).
- **Client Blueprint Template** (`deployments/_template/`): A standardized blueprint ready for instant cloning to onboard new clients. Contains starter `databricks.yml` and `environment_setup.job.yml`.
- **Per-Client Bundles** (`deployments/<client_id>/databricks.yml`): Independent bundles containing client-specific ETL jobs and view refresh triggers.
- **Shared Code Sync**: Client bundles sync the root `pipelines/`, `configs/`, and `lakeforge/` packages without code duplication via `sync.paths: ["../../pipelines", "../../configs", "../../lakeforge"]`.

Deploying or modifying one client never triggers downtime or updates on another tenant!

---

## 🎛️ 4. Central Stage Registry & Multi-Account Architecture

Stage names, target catalogs, and schemas are defined in a single source of truth: **`configs/environments/env_settings.json`**.

### Key Architectural Benefits:
1. **Zero Hardcoded Stages**: The CLI (`lakeforge deploy`), notebook environment widgets, and CI/CD workflows read their available stages dynamically from `env_settings.json`.
2. **Automated Bundle Target Synchronization**: Running `lakeforge sync-stages` automatically regenerates the `targets:` blocks in root `databricks.yml` and all `deployments/*/databricks.yml` files.
3. **Multi-Account & Multi-Workspace Routing**: A stage can be hosted in an entirely different Databricks account/workspace simply by defining `workspace_host` in that stage's JSON configuration:
   ```json
   "prod": {
     "workspace_host": "https://dbc-enterprise-prod.cloud.databricks.com",
     "catalogs": { ... }
   }
   ```
4. **Credential Security**: **Never store secrets in `env_settings.json`** (as it is checked into git and synced to `/Workspace/Shared/...`). Only non-secret settings belong in the file.

---

## 🔑 5. Service Principal OAuth (M2M) vs PAT Authentication

LakeForge supports enterprise machine-to-machine (M2M) OAuth credentials across all CI/CD deployment pipelines:

- **Service Principal OAuth (Recommended)**: Pass client credentials via `DATABRICKS_<STAGE>_CLIENT_ID` and `DATABRICKS_<STAGE>_CLIENT_SECRET`. The Databricks CLI automatically exchanges them for short-lived ephemeral bearer tokens.
- **Personal Access Tokens (PAT)**: Supported via `DATABRICKS_<STAGE>_TOKEN` for backwards compatibility.
- **Precedence**: If both are present, Service Principal OAuth takes precedence over static PATs.

---

## 🐍 6. Extensible Python Function Libraries & External SQL Support

LakeForge avoids inline SQL and config bloat by supporting modular Python libraries and external SQL scripts:

### Modular Python Functions
Define reusable PySpark logic in Python modules (e.g. `lakeforge/transformations/generic.py`, `lakeforge/transformations/custom.py`, or tenant-specific `lakeforge/transformations/<client_id>/custom.py`):
```json
{
  "custom_module": "lakeforge.transformations.client_alpha.custom",
  "custom_function": "clean_client_alpha_sales",
  "params": {"tax_rate": 0.08}
}
```

### External SQL Files
Rather than embedding multi-line SQL queries inside JSON strings, point directly to external `.sql` files:
```json
{
  "query_file": "configs/queries/gold_revenue_summary.sql"
}
```
The LakeForge execution engine resolves the query file relative to the repository root at runtime.

---

## 🔒 7. Data Protection & Centralized PII Masking

Data privacy is governed centrally through `configs/governance/data_protection.json`:
- **Tag-Based Column Masking**: Masks sensitive columns dynamically in Unity Catalog (e.g., credit cards, tax IDs, emails, SSNs) using SHA-256 hashes or redacting masks based on the querying user's group.
- **Row-Level Security (RLS)**: Enforces row filters based on user attributes or client affiliation:
  ```sql
  CREATE OR REPLACE ROW FILTER silver.client_filter ON silver.cleaned.sales
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('admin'), true, client_id = current_user_client());
  ```

---

## 🚦 8. Branching & Deployment Policy Enforcement

To ensure production stability, LakeForge implements strict branch guardrails enforced in CI/CD pipelines (`.github/workflows/ci_cd.yml` and `azure-pipelines/workflows/ci_cd.yml`):

| Target Environment | Permitted Source Branch | Trigger | Bundle Mode |
|---|---|---|---|
| **dev** | ANY branch (`main`, `dev`, `feature/**`, `bugfix/**`) | Push to PR / branch | User-scoped (`~/.lakeforge/...`) |
| **test** | `main` only | Merge to `main` | Production (`mode: production`) |
| **staging** | `main` only | Manual dispatch from `main` | Production (`mode: production`) |
| **prod** | `main` only | Manual dispatch with approval gate | Production (`mode: production`) |

If a developer attempts to deploy to `test`, `staging`, or `prod` from a feature branch, the build immediately aborts with an enforcement error.

---

## 🔄 9. Schema Evolution & Drift Policies

When upstream schemas change unexpectedly, LakeForge protects downstream integrity through configurable **Drift Policies**:

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

## 🛡️ 10. Data Quality Gates & Quarantine Pattern

LakeForge isolates invalid records without crashing batches:

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
3. Failing records are split into a **Quarantine Table** (`<env>_quarantine.<table_name>_bad`).
4. Quarantine records include the original raw payload, the failed rule names, timestamp, and rejection reasons.

---

## ⏳ 11. Slowly Changing Dimensions (SCD Type 1 vs Type 2)

- **SCD Type 1 (In-Place Overwrite)**: Updates existing records in place whenever non-key attributes change.
- **SCD Type 2 (History-Preserving)**: Maintains full historical change tracking using `effective_start_date`, `effective_end_date` (defaulting to `9999-12-31`), and `is_current` boolean flags.

---

## 🎯 12. Trust Score Formulation

The LakeForge **Trust Engine** grades pipeline execution health using a composite score from `0%` to `100%`:

$$\text{Trust Score} = w_{\text{dq}} \cdot S_{\text{dq}} + w_{\text{drift}} \cdot S_{\text{drift}} + w_{\text{volume}} \cdot S_{\text{volume}} + w_{\text{dups}} \cdot S_{\text{dups}}$$

Where:
- $S_{\text{dq}}$: Data Quality pass percentage across all validation rules.
- $S_{\text{drift}}$: Schema consistency score.
- $S_{\text{volume}}$: Row count drift score.
- $S_{\text{dups}}$: Uniqueness score.

### Classification Tiers:
- 🟢 **95% – 100%**: **EXCELLENT** — Production-ready, full confidence.
- 🟡 **85% – 94%**: **GOOD** — Minor non-critical anomalies detected.
- 🟠 **70% – 84%**: **ACCEPTABLE** — Quality alerts triggered, review recommended.
- 🔴 **< 70%**: **CRITICAL** — Data quarantined, downstream publishing paused.
