# 📋 Code & Configuration Examples

This page provides production-ready code snippets and JSON configuration examples for the most common LakeForge data engineering patterns.

---

## 🗄️ 1. Relational Database Ingestion (Oracle / PostgreSQL)

### Ingestion Configuration (`configs/ingestion/transactions.json`)
```json
{
  "source_name": "oracle_erp_transactions",
  "source_type": "database",
  "database_type": "oracle",
  "connection": {
    "host": "oracle.corp.internal",
    "port": 1521,
    "service_name": "PROD_ERP",
    "secret_scope": "lakeforge_secrets",
    "username_key": "oracle_user",
    "password_key": "oracle_password"
  },
  "query": "SELECT order_id, customer_id, order_date, total_amount, currency, status FROM ERP.ORDERS WHERE order_date >= TO_DATE('2026-01-01', 'YYYY-MM-DD')",
  "partitioning": {
    "partition_column": "order_id",
    "lower_bound": 1,
    "upper_bound": 50000000,
    "num_partitions": 16
  },
  "target": {
    "catalog": "bronze",
    "schema": "raw",
    "table": "transactions",
    "mode": "append",
    "partition_by": ["_ingestion_date"]
  }
}
```

### Python SDK Execution
```python
from pyspark.sql import SparkSession
from lakeforge.ingestion.databases.oracle_loader import OracleLoader
from lakeforge.bronze.bronze_writer import BronzeWriter

spark = SparkSession.builder.appName("OracleIngest").getOrCreate()

# Initialize loader using Databricks secret management
loader = OracleLoader(
    spark=spark,
    host="oracle.corp.internal",
    port=1521,
    service_name="PROD_ERP",
    user=dbutils.secrets.get("lakeforge_secrets", "oracle_user"),
    password=dbutils.secrets.get("lakeforge_secrets", "oracle_password")
)

# Parallel partitioned JDBC extract
df_raw = loader.load_table(
    table="ERP.ORDERS",
    partition_column="order_id",
    lower_bound=1,
    upper_bound=50000000,
    num_partitions=16
)

# Write to Bronze with audit columns
writer = BronzeWriter(spark=spark)
df_with_audit = writer.add_audit_columns(df_raw, source_system="oracle_erp")
writer.write_to_bronze(
    df=df_with_audit,
    target_table="bronze.raw.transactions",
    mode="append",
    partition_cols=["_ingestion_date"]
)
```

---

## ☁️ 2. Cloud Storage Auto Loader (AWS S3 / ADLS Gen2)

### Ingestion Configuration (`configs/ingestion/sample_csv_ingestion.json`)
```json
{
  "source_name": "landing_storage_csv",
  "source_type": "cloud_storage",
  "format": "csv",
  "path": "/Volumes/bronze/raw/landing_files/",
  "autoloader": {
    "enabled": true,
    "cloudFiles.format": "csv",
    "cloudFiles.schemaLocation": "/Volumes/bronze/raw/checkpoints/schema_sales",
    "cloudFiles.schemaEvolutionMode": "addNewColumns"
  },
  "options": {
    "header": "true",
    "inferSchema": "false",
    "delimiter": ","
  },
  "target": {
    "catalog": "bronze",
    "schema": "raw",
    "table": "sales_stream",
    "mode": "append"
  }
}
```

---

## ⚡ 3. Real-Time Kafka Structured Streaming

```python
from lakeforge.ingestion.streaming.kafka_loader import KafkaLoader
from lakeforge.bronze.bronze_writer import BronzeWriter

kafka_loader = KafkaLoader(spark=spark)

stream_df = kafka_loader.load_stream(
    kafka_bootstrap_servers="kafka-broker.corp:9092",
    topic="telemetry.iot.events",
    starting_offsets="latest",
    value_format="json",
    schema="device_id STRING, event_time TIMESTAMP, metric_val DOUBLE, status STRING"
)

writer = BronzeWriter(spark=spark)
query = writer.write_stream_to_bronze(
    df=stream_df,
    target_table="bronze.raw.iot_telemetry",
    checkpoint_location="/Volumes/bronze/raw/checkpoints/iot_stream",
    source_system="iot_gateway"
)
```

---

## 🛡️ 4. Data Quality Rules & Quarantine

### Configuration (`configs/dq/customers.json`)
```json
{
  "dataset": "customers",
  "source_table": "bronze.raw.customers",
  "target_table": "silver.cleaned.customers",
  "quarantine_table": "bronze.quarantine.customers_quarantine",
  "rules": [
    {
      "rule_name": "customer_id_not_null",
      "rule_type": "null_check",
      "column": "customer_id",
      "threshold": 0.0
    },
    {
      "rule_name": "customer_id_unique",
      "rule_type": "duplicate_check",
      "columns": ["customer_id"]
    },
    {
      "rule_name": "valid_email",
      "rule_type": "regex_check",
      "column": "email",
      "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$",
      "threshold": 0.98
    },
    {
      "rule_name": "valid_country_code",
      "rule_type": "allowed_values",
      "column": "country_code",
      "allowed_values": ["US", "CA", "GB", "DE", "IN", "AU"]
    }
  ]
}
```

---

## ⏳ 5. Slowly Changing Dimension Type 2 (SCD2)

### Configuration (`configs/transformations/customers_clean.json`)
```json
{
  "target_table": "silver.dim.customers",
  "scd_type": 2,
  "primary_keys": ["customer_id"],
  "track_history_columns": ["address", "city", "postal_code", "segment", "credit_limit"],
  "effective_start_date_col": "effective_start_date",
  "effective_end_date_col": "effective_end_date",
  "is_current_col": "is_current",
  "transformations": [
    {
      "type": "standardize",
      "column": "email",
      "operation": "lowercase"
    },
    {
      "type": "derived_column",
      "column": "full_name",
      "expression": "CONCAT(first_name, ' ', last_name)"
    }
  ]
}
```

### Python SDK Execution
```python
from lakeforge.silver.scd_type2 import SCDType2Manager

scd2_manager = SCDType2Manager(spark=spark)

scd2_manager.merge_scd2(
    source_df=cleansed_updates_df,
    target_table="silver.dim.customers",
    primary_keys=["customer_id"],
    tracked_columns=["address", "city", "postal_code", "credit_limit"],
    effective_start_col="effective_start_date",
    effective_end_col="effective_end_date",
    is_current_col="is_current"
)
```

---

## 📊 6. Declarative Gold Aggregation

### Configuration (`configs/aggregations/daily_revenue.json`)
```json
{
  "target_table": "gold.marts.daily_revenue",
  "source_tables": [
    {
      "alias": "t",
      "table": "silver.cleaned.transactions"
    },
    {
      "alias": "c",
      "table": "silver.dim.customers",
      "join_type": "inner",
      "join_condition": "t.customer_id = c.customer_id AND c.is_current = true"
    }
  ],
  "group_by": [
    "CAST(t.order_date AS DATE) AS sale_date",
    "c.country_code",
    "c.segment"
  ],
  "metrics": [
    "COUNT(DISTINCT t.order_id) AS total_orders",
    "SUM(t.total_amount) AS total_gross_revenue",
    "ROUND(AVG(t.total_amount), 2) AS average_order_value",
    "MIN(t.order_date) AS first_order_time",
    "MAX(t.order_date) AS last_order_time"
  ],
  "z_order_columns": ["sale_date", "country_code"]
}
```

---

## 🔒 7. Unity Catalog Governance & Row-Level Masking

### Configuration (`configs/governance/access_control.json`)
```json
{
  "catalogs": {
    "silver": {
      "grants": [
        {
          "principals": ["data_analysts_group"],
          "privileges": ["USE CATALOG", "USE SCHEMA", "SELECT"]
        }
      ]
    }
  },
  "tables": {
    "silver.cleaned.customers": {
      "column_masks": [
        {
          "column": "ssn",
          "mask_function": "lakeforge_security.mask_ssn"
        },
        {
          "column": "email",
          "mask_function": "lakeforge_security.hash_email"
        }
      ],
      "row_filters": [
        {
          "filter_function": "lakeforge_security.region_filter(country_code)"
        }
      ]
    }
  }
}
```


---

## 🛡️ 8. Data Protection & Tag-Based Masking (`configs/governance/data_protection.json`)

```json
{
  "pii_policies": {
    "tags": {
      "pii_restricted": {
        "description": "Restricted personally identifiable information",
        "masking_rule": "SHA256"
      },
      "financial_confidential": {
        "description": "Card numbers and bank account references",
        "masking_rule": "REDACT_FULL"
      }
    },
    "column_tags": {
      "sales": {
        "customer_email": ["pii_restricted"],
        "credit_card": ["financial_confidential"]
      }
    }
  }
}
```

---

## 🏢 9. Per-Client Independent Databricks Asset Bundle (`deployments/client_alpha/databricks.yml`)

```yaml
bundle:
  name: lakeforge-client-alpha

include:
  - resources/*.yml
  - resources/*.json

sync:
  paths:
    - "../../pipelines"
    - "../../configs"
    - "../../lakeforge"

targets:
  dev:
    workspace:
      root_path: ~/.lakeforge/${bundle.name}
  test:
    mode: production
    workspace:
      root_path: /Workspace/Shared/.bundle/${bundle.name}/test
  prod:
    mode: production
    workspace:
      root_path: /Workspace/Shared/.bundle/${bundle.name}/prod
```


---

## 🐍 10. Custom Python Transformation (`lakeforge/transformations/client_alpha/custom.py`)

### Python Transformation Function
```python
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def clean_client_alpha_sales(df: DataFrame, tax_rate: float = 0.08) -> DataFrame:
    """Custom regional cleansing and tax computation for Client Alpha."""
    return (
        df.filter(F.col("order_status") != "VOID")
          .withColumn("net_amount", F.round(F.col("gross_amount") * (1 + tax_rate), 2))
          .withColumn("client_tenant_tag", F.lit("client_alpha"))
    )
```

### Configuration Calling Custom Python (`configs/transformations/client_alpha/sales_clean.json`)
```json
{
  "source_table": "bronze.client_alpha.sales",
  "target_table": "silver.client_alpha.sales_clean",
  "custom_module": "lakeforge.transformations.client_alpha.custom",
  "custom_function": "clean_client_alpha_sales",
  "params": {
    "tax_rate": 0.085
  }
}
```

---

## 🥇 11. Custom Python Gold Mart Aggregation (`lakeforge/aggregations/client_alpha/custom.py`)

### Python Aggregation Function
```python
from typing import Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def compute_client_alpha_daily_mart(source_dfs: Dict[str, DataFrame]) -> DataFrame:
    """Aggregates sales and customer data into a high-level executive mart."""
    sales_df = source_dfs["sales"]
    customers_df = source_dfs["customers"]

    return (
        sales_df.join(customers_df, on="customer_id", how="inner")
                .groupBy("sale_date", "region", "tier")
                .agg(
                    F.count("order_id").alias("total_orders"),
                    F.sum("net_amount").alias("total_revenue"),
                    F.round(F.avg("net_amount"), 2).alias("avg_order_value")
                )
    )
```

---

## 📜 12. External SQL File Support

Instead of embedding multi-line SQL strings inside JSON, reference an external `.sql` file:

### Configuration (`configs/aggregations/sales_summary.json`)
```json
{
  "target_table": "gold.marts.sales_summary",
  "query_file": "configs/queries/gold_sales_summary.sql",
  "merge_strategy": "overwrite"
}
```

---

## 🎛️ 13. Stage Registry & Multi-Account Host Configuration (`configs/environments/env_settings.json`)

```json
{
  "dev": {
    "catalogs": {
      "lakehouse": {
        "bronze_schema": "bronze",
        "silver_schema": "silver",
        "gold_schema": "gold",
        "monitoring_schema": "monitoring"
      }
    }
  },
  "prod": {
    "workspace_host": "https://dbc-enterprise-prod.cloud.databricks.com",
    "catalogs": {
      "lakehouse_prod": {
        "bronze_schema": "bronze",
        "silver_schema": "silver",
        "gold_schema": "gold",
        "monitoring_schema": "monitoring"
      }
    }
  }
}
```
