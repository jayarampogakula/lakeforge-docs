# 🚀 Getting Started with LakeForge

Welcome to LakeForge, the enterprise metadata-driven Data Lakehouse framework designed for **Databricks**, **Delta Lake**, and **Apache Spark**.

LakeForge simplifies and standardizes building production data pipelines following the **Medallion Architecture** (Bronze ➔ Silver ➔ Gold ➔ Views) with automated data quality gates, slowly changing dimensions (SCD), multi-tenant scoping, centralized Unity Catalog governance, automated Delta maintenance, and an intuitive CLI.

---

## ⚡ 5-Minute Quickstart

Follow this step-by-step guide to get your first LakeForge pipeline running on Databricks or local Spark.

### Step 1: Provision Environment & Volumes

LakeForge provides an automated provisioning pipeline (`pipelines/SETUP_Environment_Provisioning.ipynb`) that creates the target Unity Catalog structure and landing volumes based on your active environment and client scope:

```sql
-- Environment catalogs for Medallion architecture
CREATE CATALOG IF NOT EXISTS dev_bronze;
CREATE CATALOG IF NOT EXISTS dev_silver;
CREATE CATALOG IF NOT EXISTS dev_gold;
CREATE CATALOG IF NOT EXISTS dev_quarantine;
CREATE CATALOG IF NOT EXISTS dev_monitoring;

-- Tenant-specific catalog and raw files landing volume
CREATE CATALOG IF NOT EXISTS dev_client_alpha;
CREATE SCHEMA IF NOT EXISTS dev_client_alpha.raw_files;
CREATE VOLUME IF NOT EXISTS dev_client_alpha.raw_files.landing;
```

> 💡 **Tip:** Running `SETUP_Environment_Provisioning.ipynb` dynamically checks your environment configuration and provisions these objects automatically.

---

### Step 2: Install LakeForge

In your Databricks cluster or notebook environment:

```python
# Install directly from the LakeForge GitHub repository
%pip install git+https://github.com/jayarampogakula/Lakeforge.git

# Restart Python kernel to pick up the installed package
dbutils.library.restartPython()
```

Or install locally using `pip`:

```bash
pip install lakeforge
```

---

### Step 3: Initialize a LakeForge Project

Using the LakeForge CLI, scaffold a new project directory structure with starter configurations:

```bash
lakeforge init my_lakehouse
cd my_lakehouse
```

This creates the standard LakeForge directory structure:

```text
my_lakehouse/
├── configs/
│   ├── environments/
│   │   └── env_settings.json
│   ├── ingestion/
│   │   └── sample_sales.json
│   ├── dq/
│   │   └── sample_sales.json
│   ├── transformations/
│   │   └── sales_clean.json
│   ├── aggregations/
│   │   └── sales_summary.json
│   └── views/
│       └── reporting_views.json
└── README.md
```

---

### Step 4: Validate Your Configuration Files

Before running pipelines, use the built-in validator to verify JSON schema integrity and ensure target paths and rules are syntactically sound:

```bash
lakeforge validate configs --env dev
```

Output:
```text
============================================================
LakeForge Config Validator (env=dev)
============================================================
[VALID] configs/environments/env_settings.json
[VALID] configs/ingestion/sample_sales.json
[VALID] configs/dq/sample_sales.json
[VALID] configs/transformations/sales_clean.json
[VALID] configs/aggregations/sales_summary.json
[VALID] configs/views/reporting_views.json
------------------------------------------------------------
Summary: 6 checked, 6 valid, 0 errors.
Configs are production ready!
============================================================
```

---

### Step 5: Run Your First Pipeline

You can run pipelines using either the **LakeForge CLI** or python code:

#### Option A: Using the LakeForge CLI

```bash
# Ingest into Bronze
lakeforge run --layer bronze --name sample_sales --env dev

# Clean and transform into Silver
lakeforge run --layer silver --name sales_clean --source bronze.raw.sample_sales --env dev

# Aggregate into Gold
lakeforge run --layer gold --name sales_summary --env dev

# Deploy Reporting Views
lakeforge run --layer views --env dev
```

#### Option B: Using Python in a Databricks Notebook

```python
from pyspark.sql import SparkSession
from lakeforge.ingestion import create_csv_loader
from lakeforge.bronze import create_bronze_writer
from lakeforge.dq.dq_engine import DQEngine
from lakeforge.silver.transformer import SilverTransformer

spark = SparkSession.builder.appName("LakeForge-Quickstart").getOrCreate()

# 1. Ingest Raw CSV data
loader = create_csv_loader(spark)
df_raw = loader.load_csv(
    file_path="/Volumes/bronze/raw/landing/sales_2026.csv",
    header=True,
    delimiter=","
)

# 2. Append Audit Columns and write to Bronze Delta Table
writer = create_bronze_writer(spark)
df_bronze = writer.add_audit_columns(df_raw, source_system="pos_terminal_01")
writer.write_to_bronze(
    df=df_bronze,
    target_table="bronze.raw.sales",
    mode="append",
    partition_cols=["_ingestion_date"]
)

# 3. Validate Data Quality with DQ Engine
dq_rules = [
    {"rule_name": "order_id_not_null", "rule_type": "null_check", "column": "order_id", "threshold": 0.0},
    {"rule_name": "order_id_unique", "rule_type": "duplicate_check", "columns": ["order_id"]},
    {"rule_name": "positive_amount", "rule_type": "range_check", "column": "amount", "min_value": 0.01}
]
dq_engine = DQEngine(spark=spark, rules=dq_rules)
valid_df, quarantine_df = dq_engine.validate(df_bronze)

# Route bad rows to quarantine table
if quarantine_df.count() > 0:
    quarantine_df.write.format("delta").mode("append").saveAsTable("bronze.quarantine.sales_bad_records")

# 4. Transform & Standardize to Silver
transformer = SilverTransformer(spark=spark)
silver_df = transformer.apply_transformations(
    df=valid_df,
    transformations=[
        {"type": "cast", "columns": {"amount": "double", "order_date": "date"}},
        {"type": "standardize", "column": "customer_email", "operation": "lowercase"}
    ]
)
silver_df.write.format("delta").mode("append").saveAsTable("silver.cleaned.sales")

print("Pipeline completed successfully!")
```

---

## 📈 Verifying Results

After execution, query your Delta tables to inspect data and audit fields:

```sql
-- Verify bronze data and system audit tracking columns
SELECT 
    order_id, 
    customer_email, 
    amount, 
    _source_system, 
    _ingestion_timestamp, 
    _record_hash 
FROM bronze.raw.sales 
LIMIT 5;

-- Check quarantine table for rejected rows
SELECT * FROM bronze.quarantine.sales_bad_records;

-- Query transformed silver data
SELECT * FROM silver.cleaned.sales;
```

---

## 🧭 Next Steps

- Explore the [Installation Guide](installation.md) for custom Docker containers, Azure DevOps, and Databricks Asset Bundles.
- Read [Architecture](architecture.md) to understand the inner workings of Bronze, Silver, Gold, and Trust Engine.
- Explore [CLI Documentation](cli.md) for automated stage deployments across Dev, Test, Staging, and Prod.
