# ⭐ Best Practices

Production-tested architectural, operational, and performance guidelines for operating LakeForge at enterprise scale.

---

## ⚡ 1. Delta Lake Storage & Performance Tuning

### File Sizing & Liquid Clustering
- **File Sizing**: Aim for file sizes between **128 MB and 1 GB** on Delta tables. Small files degrade query performance due to metadata overhead.
- **Liquid Clustering (`CLUSTER BY`)**: On Databricks Runtime 13.3 LTS and higher, prefer Liquid Clustering over legacy partitioning and Z-Ordering for large tables with multi-column queries:
  ```sql
  ALTER TABLE silver.cleaned.sales CLUSTER BY (customer_id, order_date);
  ```
- **Z-Ordering**: If using partition-based tables, choose at most 2–4 high-cardinality columns commonly used in `WHERE` and `JOIN` filters for `Z-ORDER BY`:
  ```sql
  OPTIMIZE silver.cleaned.transactions ZORDER BY (transaction_id, customer_id);
  ```

### Compaction & Vacuum Retention
- Schedule table maintenance regularly using `lakeforge.maintenance`:
  - Run `OPTIMIZE` daily during low-traffic windows.
  - Run `VACUUM` with retention of at least **7 days (168 hours)** to protect active concurrent readers and allow time-travel queries:
  ```python
  from lakeforge.maintenance.table_maintenance import TableMaintenanceManager
  
  maintenance = TableMaintenanceManager(spark=spark)
  maintenance.run_maintenance(
      table_name="silver.cleaned.sales",
      optimize=True,
      z_order_columns=["customer_id"],
      vacuum=True,
      retention_hours=168
  )
  ```

---

## 🔐 2. Credential & Secrets Security

- **Never Hardcode Credentials**: Never place database passwords, API tokens, or cloud keys in JSON configuration files or notebook code.
- **Use Databricks Secret Scopes**: Configure references to secret scopes in your JSON files:
  ```json
  {
    "secret_scope": "lakeforge_kv_scope",
    "username_key": "salesforce_client_id",
    "password_key": "salesforce_client_secret"
  }
  ```
- **Managed Identity & IAM Roles**: In Azure and AWS environments, prefer cluster-assigned Azure Managed Identities or AWS IAM Instance Profiles over static service principal tokens.

---

## 🛡️ 3. Data Quality & Quarantine Strategy

- **Keep Quarantine Tables Finite**: Ensure quarantine tables have retention policies. Implement periodic archiving or cleanup so quarantine storage does not grow unbounded.
- **Non-Zero Thresholds for High Volume**: When validating non-essential fields (such as phone numbers or postal codes), use a threshold (e.g. `threshold: 0.95`) rather than `threshold: 1.0` to avoid stopping pipelines over minor data entry anomalies.
- **Always Include Primary Key Null Checks**: Always set `threshold: 0.0` (zero tolerance) for primary keys and foreign keys.

---

## 🌊 4. Streaming vs. Micro-Batch Guidelines

| Requirement | Recommended Approach | LakeForge Loader |
|---|---|---|
| Ingesting cloud files (S3/ADLS/GCS) | **Databricks Auto Loader** (`cloudFiles`) | Auto Loader via `FilesystemLoader` |
| Real-time messaging (Kafka, Event Hubs) | **Structured Streaming** with Trigger Once or AvailableNow | `KafkaLoader.load_stream` |
| Daily ERP database extracts | **Micro-batch parallel partitioned JDBC** | `OracleLoader`, `PostgresLoader` |
| Low-volume SaaS API endpoints | **Scheduled hourly/daily batch** with state checkpoint | `APILoader` |

- **Use `AvailableNow` for Micro-batch Streaming**: When processing streaming feeds on a schedule without keeping clusters running 24/7, use `trigger(availableNow=True)` to process all pending data efficiently at lowest cost.

---

## 🏷️ 5. Multi-Tenant Governance

- **Catalog-Level Isolation**: For strict enterprise data boundaries, assign separate Unity Catalogs to different tenants (`client_a_catalog`, `client_b_catalog`).
- **Use Dynamic Row-Level Filters**: If sharing a multi-tenant Silver table, configure Unity Catalog row filters that read `CURRENT_USER()` or workspace tenant tokens:
  ```sql
  CREATE OR REPLACE ROW FILTER silver.client_filter ON silver.cleaned.sales
  RETURN IF(IS_ACCOUNT_GROUP_MEMBER('admin'), true, client_id = current_tenant_id());
  ```

---

## 🚀 6. CI/CD Pipeline Promotion

1. **Local & Pull Request Verification**: Run `lakeforge validate configs --env dev` and `pytest tests/unit_tests/` in pull request checks.
2. **Staging Dry Run**: Use `lakeforge deploy --stage staging --dry-run` to preview all schema changes, grants, and bundle assets before deploying.
3. **Automated Rollback**: Tag git commits (`v1.0.0`, `v1.0.1`) and maintain versioned Databricks Asset Bundles so you can roll back within seconds if regressions occur.


---

## 🔒 7. Stage Registry & Credential Hardening

- **Never Commit Credentials to `env_settings.json`**: This file is checked into version control and synced to `/Workspace/Shared/...` where it is readable by all workspace users. Keep all passwords, tokens, and OAuth secrets in CI secrets (`DATABRICKS_<STAGE>_CLIENT_ID` / `_CLIENT_SECRET`) or Databricks Secret Scopes.
- **Prefer Service Principal M2M OAuth over PAT**: Service Principal OAuth secret pairs do not expire after 90 days and automatically exchange for short-lived ephemeral bearer tokens at runtime.
- **Always Run `sync-stages --check` in CI**: Ensure no bundle target has drifted from the central stage registry defined in `env_settings.json`.

---

## 🐍 8. Modular Python Code over Inline JSON SQL

- **Avoid Monolithic JSON SQL Strings**: When business logic exceeds 5 lines of SQL, extract it into a dedicated `.sql` file (`"query_file": "..."`) or a Python function (`"custom_module"`, `"custom_function"`).
- **Package Reusable Functions in `lakeforge.transformations.generic`**: Place enterprise-wide cleaning, formatting, and mathematical routines in `generic.py` so multiple pipelines and clients can reuse them without duplication.
- **Use `lakeforge pr-review`**: Run `lakeforge pr-review --fail-on-duplicate` in your pull request checks to prevent duplicate code and ensure test coverage for all new components.
