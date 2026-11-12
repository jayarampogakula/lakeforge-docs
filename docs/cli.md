# 💻 Command Line Interface (CLI)

The `lakeforge` CLI is a unified command-line tool for project initialization, configuration validation, pipeline execution, governance enforcement, and cross-stage deployments.

---

## 📌 Global Usage & Options

```bash
lakeforge [--version | -v] [--help | -h] <subcommand> [options]
```

### Display Help & Version
```bash
# Check installed CLI version
lakeforge --version

# Display general CLI documentation
lakeforge --help
```

---

## 🛠️ Subcommand: `lakeforge init`

Scaffolds a new LakeForge project structure with starter templates and boilerplate configuration files.

### Syntax
```bash
lakeforge init [target_dir] [-f | --force]
```

### Options
- `target_dir`: Path to create the project directory (defaults to current directory `.`).
- `-f`, `--force`: Overwrite existing configuration files if directory is not empty.

### Example
```bash
lakeforge init my_lakehouse
cd my_lakehouse
```

Generated directory layout:
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

## 🔍 Subcommand: `lakeforge validate`

Validates LakeForge JSON configurations against JSON schema rules, checking for required keys, valid data types, table naming formats, and environmental settings.

### Syntax
```bash
lakeforge validate [config_path] [--env <env>] [--client <client_id>]
```

### Options
- `config_path`: Directory or specific JSON file to validate (defaults to `configs`).
- `--env`: Environment context to validate (`dev`, `test`, `staging`, `prod`; default: `dev`).
- `--client`: Client ID / Tenant scope to validate client-specific overrides.

### Examples
```bash
# Validate entire configs directory for dev
lakeforge validate configs --env dev

# Validate for production
lakeforge validate configs --env prod

# Validate tenant-specific configuration
lakeforge validate configs --env prod --client client_alpha

# Validate a single file
lakeforge validate configs/ingestion/transactions.json
```

---

## 🚀 Subcommand: `lakeforge run`

Executes or tests a specific pipeline stage in the Medallion architecture.

### Syntax
```bash
lakeforge run --layer <layer> [options]
```

### Required Options
- `--layer`: Pipeline layer to execute:
  - `bronze`: Ingest raw data from source connector into Bronze Delta table.
  - `silver`: Execute DQ validations, cleanse, transform, and merge into Silver Delta table.
  - `gold`: Run dimensional aggregations into Gold business marts.
  - `views`: Create or replace semantic reporting SQL views.
  - `governance`: Apply Unity Catalog grants, column masks, and row filters.

### Additional Options
- `--name`: Ingestion source name (Bronze) or target table name (Silver/Gold) or view name (Views).
- `--source`: Source table name for Silver layer transformations (e.g. `bronze.raw.sales`).
- `--env`: Environment to target (`dev`, `test`, `staging`, `prod`; default: `dev`).
- `--client`: Tenant identifier to resolve multi-tenant configuration overrides.
- `--config-dir`: Path to configuration directory (default: `configs`).
- `--scd2`: Enable Slowly Changing Dimension Type 2 history merge on Silver target.
- `--dry-run`: Preview SQL statements, changes, and plans without writing to Delta tables.

### Examples
```bash
# 1. Run Bronze Ingestion
lakeforge run --layer bronze --name transactions --env dev

# 2. Run Silver Transformation with SCD Type 2
lakeforge run --layer silver --name customers_clean --source bronze.raw.customers --scd2 --env dev

# 3. Run Gold Aggregation for Tenant client_alpha
lakeforge run --layer gold --name daily_revenue --client client_alpha --env prod

# 4. Dry-run Governance Policies
lakeforge run --layer governance --env prod --dry-run
```

---

## 📦 Subcommand: `lakeforge deploy`

Packages and deploys LakeForge configurations, Databricks workflows, views, and governance policies to a target environment stage. Stages are dynamically resolved from the central Stage Registry (`configs/environments/env_settings.json`).

### Syntax
```bash
lakeforge deploy --stage <stage> [options]
```

### Options
- `--stage`, `-s`: Target deployment stage (e.g. `dev`, `test`, `staging`, `prod`). **Required**. Read dynamically from `env_settings.json`.
- `--component`: Component to deploy (`all`, `pipelines`, `views`, `governance`, `package`; default: `all`).
- `--client`, `-c`: Client ID / Tenant scope (e.g. `client_alpha`). Deploys tenant-specific bundle resources.
- `--config-dir`: Configuration root directory (default: `configs`).
- `--target-workspace`: Target Databricks workspace path.
- `--dry-run`: Simulates the deployment and reports actions without applying changes.

### Examples
```bash
# Preview deployment to staging
lakeforge deploy --stage staging --dry-run

# Deploy all components to production
lakeforge deploy --stage prod --component all

# Deploy only client_alpha's bundle resources to dev
lakeforge deploy --stage dev --client client_alpha

# Deploy only governance and view security to test
lakeforge deploy --stage test --component governance
```

---

## 🔄 Subcommand: `lakeforge sync-stages`

Synchronizes bundle stage targets across the repository from the central Stage Registry (`configs/environments/env_settings.json`). Regenerates `targets:` blocks in:
1. Root `databricks.yml`
2. Client template blueprint (`deployments/_template/databricks.yml`)
3. Every active tenant bundle (`deployments/<client_id>/databricks.yml`)

### Syntax
```bash
lakeforge sync-stages [--check] [--config-dir <dir>]
```

### Options
- `--check`: Dry-run mode: checks for stage drift and reports un-synchronized bundle targets without writing files. Exits with code 1 if drift exists (ideal for CI/CD checks).
- `--config-dir`: Path to configuration directory containing `environments/env_settings.json` (default: `configs`).

### Examples
```bash
# Synchronize all Databricks Asset Bundle targets with env_settings.json
lakeforge sync-stages

# Run drift check in CI/CD pipeline
lakeforge sync-stages --check
```

---

## 🧐 Subcommand: `lakeforge pr-review`

Automated pull request code reviewer and quality gatekeeper. Performs:
- **AST-based duplicate function detection**: Detects identical or copy-pasted Python logic across modules.
- **Test coverage verification**: Asserts that new features and connectors include corresponding unit/integration tests.
- **Branch policy enforcement**: Verifies that non-dev deployments target `main` only.
- **Configuration schema validation**: Ensures all modified JSON files strictly adhere to schema definitions.

### Syntax
```bash
lakeforge pr-review [--base-ref <ref>] [--repo-root <dir>] [--post-comment] [--fail-on-duplicate]
```

### Options
- `--base-ref`: Base git reference to compare diff against (default: `origin/main`).
- `--repo-root`: Repository root directory (default: `.`).
- `--post-comment`: Posts automated markdown review summary directly to GitHub / Azure DevOps PR.
- `--fail-on-duplicate`: Fails the CI job with exit code 1 if duplicate function implementations are detected.

### Examples
```bash
# Run local code review against main
lakeforge pr-review

# Run in CI workflow with failure on duplicate functions
lakeforge pr-review --base-ref origin/main --fail-on-duplicate --post-comment
```

---

## 🤖 CI/CD Integration & Workflow Suite

LakeForge provides 4 mirrored, production-ready workflows across both **GitHub Actions** (`.github/workflows/`) and **Azure DevOps** (`azure-pipelines/workflows/`):

1. **`ci_cd.yml`**: Linting, unit tests, integration tests, branch guardrails, and automated deployment.
2. **`pr_review.yml`**: Automated PR code review, duplicate function detection, and config validation.
3. **`dab_deploy.yml`**: Databricks Asset Bundle deployment with optional `run_setup` initial provisioning.
4. **`dab_export.yml`**: Reverse-engineers live Databricks Workflows into version-controlled DAB manifests.

### GitHub Actions Workflow Example (`.github/workflows/ci_cd.yml`)

```yaml
name: LakeForge CI/CD

on:
  push:
    branches: [ main, dev, "feature/**", "bugfix/**" ]
  pull_request:
    branches: [ main ]

jobs:
  validate-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Validate Configurations
        run: |
          lakeforge validate configs --env dev
          lakeforge validate configs --env prod
      - name: Stage Registry Drift Check
        run: lakeforge sync-stages --check
      - name: Run Unit Tests
        run: pytest tests/unit_tests/
```

### Azure DevOps Pipeline Example (`azure-pipelines/workflows/ci_cd.yml`)

```yaml
trigger:
  branches:
    include:
      - main
      - dev
      - feature/*
      - bugfix/*

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.10'

- script: |
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
  displayName: 'Install LakeForge and Dependencies'

- script: |
    lakeforge validate configs --env dev
    lakeforge sync-stages --check
    pytest tests/unit_tests/
  displayName: 'Validate and Test'
```
