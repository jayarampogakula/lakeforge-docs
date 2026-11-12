# ❓ Frequently Asked Questions (FAQ)

Got questions about LakeForge? Here are answers to the most common architectural and operational questions.

---

### Q1: How does LakeForge differ from native Databricks Delta Live Tables (DLT)?

**Answer:**
Delta Live Tables (DLT) is Databricks' proprietary orchestration and table declaration framework. While powerful, DLT has specific constraints:
- **Portability**: DLT pipelines cannot run on standard vanilla Apache Spark, local Docker containers, or outside Databricks.
- **Cost**: DLT clusters carry a premium DBU pricing tier compared to standard Databricks compute.
- **Black-box execution**: Customizing low-level quarantine logic, multi-tenant config fallback, or proprietary SCD Type 2 mechanics can be restrictive in DLT.

**LakeForge** operates on standard PySpark and Delta Lake, using standard Databricks jobs or standard clusters without the DLT cost surcharge. It can also run locally, in Docker, or on standard Spark clusters while providing enterprise features like Trust Engine scoring, multi-tenant scoping, and unified CLI deployments.

---

### Q2: Can LakeForge run outside Databricks (e.g. AWS EMR, GCP Dataproc, or local PySpark)?

**Answer:**
**Yes!** The core components of LakeForge (`lakeforge.ingestion`, `lakeforge.bronze`, `lakeforge.dq`, `lakeforge.silver`, `lakeforge.gold`, `lakeforge.trust_engine`, and CLI) are built on open-source **PySpark** and **Delta Lake**.

You can run LakeForge in:
- Local Python virtual environments with `pyspark` and `delta-spark`.
- Docker containers (see `deployment/docker/Dockerfile`).
- AWS EMR clusters with Delta Lake enabled.
- Google Cloud Dataproc clusters.

*Note: Features specific to Databricks Unity Catalog (such as UC column masks, row filters, and DButils secrets) gracefully fall back to environment variables or open-source equivalents when running outside Databricks.*

---

### Q3: What happens when an incoming batch has schema drift (e.g., new columns added)?

**Answer:**
LakeForge provides three configurable drift policies under `schema_drift.policy`:
1. `add_new_columns` (Default): Automatically appends the new columns to the target Delta table using Delta's schema evolution (`mergeSchema = true`) and logs the new columns to the metadata drift log.
2. `ignore`: Discards the new columns and only writes existing recognized columns.
3. `fail`: Rejects the batch, stops the pipeline immediately, and fires an alert.

---

### Q4: Does a failing Data Quality check crash the pipeline?

**Answer:**
**No, by default.** LakeForge uses the **Quarantine Pattern**. Records that fail quality rules (e.g., negative amounts, malformed emails) are split into a separate quarantine table (`bronze.quarantine.<table_name>_quarantine`) with audit reasons. Valid records proceed to the Silver and Gold layers without interruption.

However, if you set critical rules with `action: "abort"`, or if the overall batch failure rate exceeds an allowed threshold (e.g., max 10% failures), LakeForge will fail the job to prevent bad data from reaching production.

---

### Q5: How do client-specific overrides work in multi-tenant environments?

**Answer:**
When you pass `--client <client_name>` (e.g., `--client client_alpha`), the LakeForge config resolver checks the category-first directory:
1. `configs/<category>/<client_name>/<file>.json` (e.g., `configs/ingestion/client_alpha/sales.json`)
2. If the file exists, its properties take precedence.
3. If not found, it seamlessly falls back to the default `configs/<category>/<file>.json`.

This allows you to maintain one central configuration base while customizing specific schemas, delimiters, or DQ thresholds for specific clients.

---

### Q6: How does the Trust Engine calculate the Trust Score?

**Answer:**
The Trust Score is a normalized value between `0%` and `100%` computed using weighted penalties:
- **Data Quality Rule Pass Rate** (default weight: 40%)
- **Schema Drift Stability** (default weight: 20%)
- **Row Count Drift / Volume Anomalies** (default weight: 20%)
- **Key Uniqueness & Duplication Rates** (default weight: 20%)

A score $\ge 95\%$ is considered **EXCELLENT**, while a score $< 70\%$ flags the dataset as **CRITICAL**.

---

### Q7: How are Delta tables kept clean and performant over time?

**Answer:**
LakeForge includes an automated **Table Maintenance Engine** (`lakeforge.maintenance.table_maintenance` and `pipelines/MAINTENANCE_Table_Optimization.ipynb`) that runs:
- `OPTIMIZE ... ZORDER BY` on high-cardinality query keys.
- `VACUUM` with configurable retention hours (default: 168 hours / 7 days).
- `ANALYZE TABLE COMPUTE STATISTICS` to maintain Spark Cost-Based Optimizer (CBO) query performance.

---

### Q8: How do I upgrade LakeForge to a new version?

**Answer:**
To upgrade in your environment:
```bash
pip install --upgrade git+https://github.com/jayarampogakula/Lakeforge.git
```
In Databricks notebooks:
```python
%pip install --upgrade git+https://github.com/jayarampogakula/Lakeforge.git
dbutils.library.restartPython()
```
All LakeForge 1.x releases maintain backwards compatibility according to Semantic Versioning.


---

### Q9: How do I add, rename, or remove an environment stage?

**Answer:**
All stages are defined in one single file: **`configs/environments/env_settings.json`**.
1. Edit `configs/environments/env_settings.json` to add, rename, or remove stage keys (e.g., adding `"qa"` or `"uat"`).
2. Run `lakeforge sync-stages` from the CLI. This automatically regenerates the `targets:` block in root `databricks.yml`, `deployments/_template/databricks.yml`, and all client bundles.
3. Commit the changes. The CLI (`lakeforge deploy`), CI/CD workflows, and notebook widgets will pick up the new stages automatically.

---

### Q10: How do I deploy a stage to a separate Databricks account or workspace?

**Answer:**
Add the `workspace_host` property to the target stage in `configs/environments/env_settings.json`:
```json
"prod": {
  "workspace_host": "https://dbc-enterprise-prod.cloud.databricks.com",
  "catalogs": { ... }
}
```
Then run `lakeforge sync-stages`. In your CI/CD pipeline or runner, configure `DATABRICKS_PROD_CLIENT_ID` and `DATABRICKS_PROD_CLIENT_SECRET` (or `DATABRICKS_PROD_TOKEN`). LakeForge will direct the deployment to that target workspace automatically.

---

### Q11: How does Service Principal M2M OAuth authentication work in CI/CD?

**Answer:**
In your GitHub Actions secrets or Azure DevOps variable groups, provide:
- `DATABRICKS_<STAGE>_CLIENT_ID` (the Service Principal UUID / Application ID)
- `DATABRICKS_<STAGE>_CLIENT_SECRET` (the generated OAuth secret)

When running `databricks bundle deploy`, the Databricks CLI natively exchanges these credentials for short-lived machine-to-machine tokens. This removes the risk of hardcoded bearer tokens expiring after 90 days.

---

### Q12: How do I use custom Python functions or external SQL in my pipelines?

**Answer:**
- **For Python**: Define your function in a Python module (e.g. `lakeforge/transformations/custom.py`) with signature `def my_func(df: DataFrame, **params) -> DataFrame:`. In your JSON config, specify `"custom_module": "lakeforge.transformations.custom"` and `"custom_function": "my_func"`.
- **For External SQL**: Create a `.sql` file in your repository (e.g. `configs/queries/my_query.sql`) and reference `"query_file": "configs/queries/my_query.sql"` in your transformation or aggregation JSON configuration.
