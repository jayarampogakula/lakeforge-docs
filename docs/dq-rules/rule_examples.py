"""
LakeForge Data Quality (DQ) Rule Definitions & Runnable Examples
Demonstrates defining, configuring, and executing DQ checks across DataFrames.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType


def run_dq_demonstration():
    spark = SparkSession.builder.appName("LakeForge-DQ-Examples").getOrCreate()

    # 1. Create sample dataset with known quality issues (nulls, duplicates, invalid formats)
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("customer_email", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("currency", StringType(), True),
        StructField("status", StringType(), True)
    ])

    data = [
        ("ORD_1001", "valid.user@company.com", 149.99, "USD", "COMPLETED"),
        ("ORD_1002", "john.doe@domain.org", 29.50, "EUR", "SHIPPED"),
        (None, "missing.id@test.com", 55.00, "USD", "COMPLETED"),            # Null check violation
        ("ORD_1001", "duplicate.order@test.com", 149.99, "USD", "COMPLETED"), # Duplicate violation
        ("ORD_1003", "malformed_email", 89.00, "USD", "PENDING"),            # Regex violation
        ("ORD_1004", "negative.amount@test.com", -10.00, "USD", "PENDING"),   # Range violation
        ("ORD_1005", "invalid.currency@test.com", 45.00, "XYZ", "COMPLETED")  # Allowed values violation
    ]

    df = spark.createDataFrame(data, schema)
    print("Initial Ingested DataFrame (7 records):")
    df.show(truncate=False)

    # 2. Define Comprehensive DQ Rules Suite
    rules = [
        {
            "rule_name": "order_id_not_null",
            "rule_type": "null_check",
            "column": "order_id",
            "threshold": 0.0  # 0% null tolerance
        },
        {
            "rule_name": "order_id_unique",
            "rule_type": "duplicate_check",
            "columns": ["order_id"]
        },
        {
            "rule_name": "valid_email_format",
            "rule_type": "regex_check",
            "column": "customer_email",
            "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "threshold": 0.95
        },
        {
            "rule_name": "positive_amount",
            "rule_type": "range_check",
            "column": "amount",
            "min_value": 0.01,
            "max_value": 1000000.0
        },
        {
            "rule_name": "valid_currency_code",
            "rule_type": "allowed_values",
            "column": "currency",
            "allowed_values": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
        }
    ]

    # 3. Import and execute DQEngine
    from lakeforge.dq.dq_engine import DQEngine

    engine = DQEngine(spark=spark, rules=rules)
    valid_df, quarantine_df = engine.validate(df)

    print(f"\nDQ Validation Complete!")
    print(f"Clean Records: {valid_df.count()}")
    valid_df.show(truncate=False)

    print(f"Quarantined Records: {quarantine_df.count()}")
    quarantine_df.show(truncate=False)


if __name__ == "__main__":
    run_dq_demonstration()
