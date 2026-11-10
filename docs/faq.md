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
When you pass `--client <client_name>` (e.g., `--client client_alpha`), the LakeForge config resolver checks:
1. `configs/clients/<client_name>/<layer>/<file>.json`
2. If the file exists, its properties take precedence.
3. If not found, it seamlessly falls back to the default `configs/<layer>/<file>.json`.

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
