# 🎓 Tutorials

Step-by-step practical guides to building end-to-end solutions using LakeForge.

---

## 🏬 Tutorial 1: End-to-End Retail Lakehouse from Scratch

In this tutorial, we will build a complete retail data pipeline from raw transaction data to an executive revenue datamart.

### Prerequisites
- Databricks workspace with Unity Catalog enabled.
- LakeForge installed (`%pip install git+https://github.com/jayarampogakula/Lakeforge.git`).

### Step 1: Initialize Catalogs and Schemas
```sql
CREATE CATALOG IF NOT EXISTS retail_prod;
CREATE SCHEMA IF NOT EXISTS retail_prod.bronze;
CREATE SCHEMA IF NOT EXISTS retail_prod.silver;
CREATE SCHEMA IF NOT EXISTS retail_prod.gold;
CREATE SCHEMA IF NOT EXISTS retail_prod.quarantine;
```

### Step 2: Ingest Raw CSV Orders into Bronze
Create a notebook cell and load orders from cloud storage into Bronze:

```python
from pyspark.sql import SparkSession
from lakeforge.ingestion import create_csv_loader
from lakeforge.bronze import create_bronze_writer

spark = SparkSession.builder.getOrCreate()

# Load raw orders
csv_loader = create_csv_loader(spark)
df_raw = csv_loader.load_csv(
    file_path="/Volumes/retail_prod/bronze/landing/orders_2026.csv",
    header=True
)

# Append audit columns and write to Bronze Delta table
writer = create_bronze_writer(spark)
df_bronze = writer.add_audit_columns(df_raw, source_system="shopify_pos")

writer.write_to_bronze(
    df=df_bronze,
    target_table="retail_prod.bronze.orders",
    mode="append",
    partition_cols=["_ingestion_date"]
)
print("Bronze ingestion complete. Ingested rows:", df_bronze.count())
```

### Step 3: Run Data Quality Checks
Ensure orders contain non-null IDs, positive pricing, and valid dates:

```python
from lakeforge.dq.dq_engine import DQEngine

rules = [
    {"rule_name": "order_id_not_null", "rule_type": "null_check", "column": "order_id", "threshold": 0.0},
    {"rule_name": "order_id_unique", "rule_type": "duplicate_check", "columns": ["order_id"]},
    {"rule_name": "valid_price", "rule_type": "range_check", "column": "price", "min_value": 0.01},
    {"rule_name": "valid_status", "rule_type": "allowed_values", "column": "status", "allowed_values": ["COMPLETED", "SHIPPED", "PENDING", "CANCELLED"]}
]

dq_engine = DQEngine(spark=spark, rules=rules)
valid_df, quarantine_df = dq_engine.validate(spark.table("retail_prod.bronze.orders"))

if quarantine_df.count() > 0:
    quarantine_df.write.format("delta").mode("append").saveAsTable("retail_prod.quarantine.orders_bad")
    print(f"Quarantined {quarantine_df.count()} bad records.")
```

### Step 4: Standardize and Cleanse to Silver
Apply type casts and derived calculations:

```python
from lakeforge.silver.transformer import SilverTransformer

transformer = SilverTransformer(spark=spark)

silver_df = transformer.apply_transformations(
    df=valid_df,
    transformations=[
        {"type": "cast", "columns": {"price": "double", "quantity": "integer", "order_date": "timestamp"}},
        {"type": "derived_column", "column": "net_amount", "expression": "price * quantity"},
        {"type": "standardize", "column": "customer_email", "operation": "lowercase"}
    ]
)

silver_df.write.format("delta").mode("overwrite").saveAsTable("retail_prod.silver.orders")
print("Silver layer populated successfully.")
```

### Step 5: Build Gold Daily Sales Mart
Create aggregated business metrics:

```sql
CREATE OR REPLACE TABLE retail_prod.gold.daily_store_revenue AS
SELECT 
    CAST(order_date AS DATE) AS sale_date,
    status,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(net_amount), 2) AS total_revenue,
    ROUND(AVG(net_amount), 2) AS average_ticket_size
FROM retail_prod.silver.orders
GROUP BY CAST(order_date AS DATE), status;

OPTIMIZE retail_prod.gold.daily_store_revenue ZORDER BY (sale_date);
```

---

## 🛡️ Tutorial 2: Setting up Automated Quarantine Workflows

In high-volume enterprise pipelines, bad records must be isolated without failing the job, and alerted to data stewards for remediation.

### 1. Define Rules in JSON
In `configs/dq/transactions.json`:
```json
{
  "dataset": "transactions",
  "rules": [
    {
      "rule_name": "positive_amount",
      "rule_type": "range_check",
      "column": "amount",
      "min_value": 0.01
    },
    {
      "rule_name": "valid_currency",
      "rule_type": "allowed_values",
      "column": "currency",
      "allowed_values": ["USD", "EUR", "GBP", "JPY", "INR"]
    }
  ]
}
```

### 2. Inspecting the Quarantine Table
When records fail, LakeForge stores the record alongside metadata:
```sql
SELECT 
    _quarantine_timestamp,
    _failed_rules,
    _failure_reason,
    raw_payload
FROM retail_prod.quarantine.orders_bad
ORDER BY _quarantine_timestamp DESC;
```

### 3. Re-ingesting Corrected Quarantine Records
Once upstream fixes are applied, reload corrected rows back into Silver:
```python
from lakeforge.silver.transformer import SilverTransformer

# Read quarantined records, filter resolved records, and push to Silver
resolved_df = spark.table("retail_prod.quarantine.orders_bad") \
    .filter("status = 'RESOLVED'") \
    .select("corrected_payload.*")

transformer = SilverTransformer(spark=spark)
transformer.upsert_to_silver(resolved_df, target_table="retail_prod.silver.orders", merge_keys=["order_id"])
```

---

## 🏢 Tutorial 3: Multi-Tenant Client Scoping

Implement custom processing rules for specific enterprise clients while sharing common core pipeline code.

### Step 1: Base Configuration
`configs/ingestion/sales.json`:
```json
{
  "format": "parquet",
  "path": "/Volumes/bronze/raw/global_sales/"
}
```

### Step 2: Tenant Override
`configs/clients/client_alpha/ingestion/sales.json`:
```json
{
  "format": "csv",
  "path": "/Volumes/bronze/raw/client_alpha/sales/",
  "options": {
    "delimiter": ";"
  }
}
```

### Step 3: Run for Specific Client via CLI
```bash
lakeforge run --layer bronze --name sales --client client_alpha --env prod
```
LakeForge automatically reads the semicolon-delimited CSV for `client_alpha` while processing standard Parquet for other clients.

---

## 🚀 Tutorial 4: Automated CI/CD Deployments with Databricks Asset Bundles (DABs)

Deploy multi-stage environments (`dev` ➔ `staging` ➔ `prod`) with zero manual UI steps.

### Step 1: Define `databricks.yml`
```yaml
bundle:
  name: lakeforge-enterprise

targets:
  dev:
    workspace:
      host: https://adb-dev.azuredatabricks.net
  prod:
    workspace:
      host: https://adb-prod.azuredatabricks.net

resources:
  jobs:
    lakeforge_daily_etl:
      name: "[${bundle.target}] LakeForge Daily ETL"
      tasks:
        - task_key: bronze_ingest
          spark_python_task:
            python_file: "lakeforge/cli/__main__.py"
            parameters: ["run", "--layer", "bronze", "--env", "${bundle.target}"]
        - task_key: silver_cleanse
          depends_on:
            - task_key: bronze_ingest
          spark_python_task:
            python_file: "lakeforge/cli/__main__.py"
            parameters: ["run", "--layer", "silver", "--env", "${bundle.target}"]
```

### Step 2: Deploy to Production
```bash
# Validate bundle syntax
databricks bundle validate -t prod

# Deploy assets and workflows
databricks bundle deploy -t prod

# Trigger immediate test run
databricks bundle run lakeforge_daily_etl -t prod
```
