# 📦 Installation Guide

LakeForge is packaged as a standard Python distribution compatible with **Python 3.9+**, **PySpark 3.4+**, **Delta Lake 3.x+**, and **Databricks Runtime (DBR) 13.x LTS through 16.x LTS**.

---

## 🛠️ System Prerequisites

Ensure your environment satisfies the following baseline requirements:

| Component | Minimum Requirement | Recommended |
|---|---|---|
| **Python** | `>= 3.9` | `3.10` or `3.11` |
| **Apache Spark / PySpark** | `>= 3.4.0` | `3.5.x` |
| **Delta Lake** | `>= 2.4.0` | `>= 3.0.0` |
| **Databricks Runtime** | DBR `13.3 LTS` | DBR `14.3 LTS` or `15.4 LTS` |
| **Databricks CLI** (optional) | `>= 0.200.0` | Latest |

---

## 🚀 1. Install via Pip

### From GitHub Repository

To install the latest release directly from GitHub:

```bash
pip install git+https://github.com/jayarampogakula/Lakeforge.git
```

To install a specific version tag:

```bash
pip install git+https://github.com/jayarampogakula/Lakeforge.git@v1.0.0
```

### In a Databricks Notebook

Run within the first cell of your notebook:

```python
%pip install git+https://github.com/jayarampogakula/Lakeforge.git
dbutils.library.restartPython()
```

### As a Cluster-Scoped Library

To make LakeForge available to all notebooks and jobs on a Databricks cluster:

1. In Databricks Workspace, navigate to **Compute** ➔ Select your cluster.
2. Click the **Libraries** tab.
3. Click **Install New** ➔ Choose **PyPI**.
4. In the Package field, enter:
   ```text
   git+https://github.com/jayarampogakula/Lakeforge.git
   ```
5. Click **Install**. The library will be installed and cached across cluster restarts.

---

## 💻 2. Local Development & Editable Install

If you are developing custom LakeForge extensions or contributing features:

```bash
# Clone the repository
git clone https://github.com/jayarampogakula/Lakeforge.git
cd Lakeforge

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

Verify your local installation:

```bash
lakeforge --version
# Output: lakeforge 1.0.0

pytest tests/unit_tests/
```

---

## 🐳 3. Docker Container Setup

LakeForge provides a production-ready container image for headless deployments, unit testing in CI, or local execution outside Databricks.

### Dockerfile

Located at `infrastructure/docker/Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install Java runtime for PySpark
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

# Copy dependency specifications (modern pyproject.toml packaging)
COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

# Copy LakeForge codebase
COPY lakeforge/ /app/lakeforge/
COPY configs/ /app/configs/

# Install LakeForge package in editable mode
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["lakeforge"]
CMD ["--help"]
```

### Running with Docker Compose

Run tests and configuration validations in isolated containers:

```bash
cd infrastructure/docker
docker compose build
docker compose run lakeforge-app validate /app/configs --env dev
```

---

## 🏗️ 4. Databricks Asset Bundles (DABs) & Multi-Bundle Layout

LakeForge supports enterprise Databricks Asset Bundles for both global workloads and per-client independent deployments:

### Global Main Bundle (`databricks.yml`)
Deploys the shared framework and cross-catalog Medallion pipeline:
```bash
# Validate bundle syntax
databricks bundle validate -t dev

# Deploy global bundle to dev
databricks bundle deploy -t dev

# Run global pipeline
databricks bundle run lakeforge_global_etl_pipeline -t dev
```

### Per-Client Independent Bundles (`deployments/<client_id>/`)
Deploy only a specific tenant's pipelines without touching the global bundle or other tenants:
```bash
# Navigate to the client's deployment bundle
cd deployments/client_alpha

# Validate and deploy client bundle
databricks bundle validate -t dev
databricks bundle deploy -t dev

# Run client-specific ETL job
databricks bundle run client_alpha_etl_pipeline -t dev
```

---

## ⚙️ 5. Optional Connector Drivers

Depending on your data sources, additional JDBC drivers or client libraries may be required on your cluster:

```bash
# Oracle JDBC Driver (ojdbc8)
pip install cx_Oracle oracledb

# Snowflake connector
pip install snowflake-connector-python snowflake-snowpark-python

# PostgreSQL JDBC
# Included in Databricks Runtime by default

# Kafka Streaming
# Databricks Runtime includes spark-sql-kafka-0-10
```
