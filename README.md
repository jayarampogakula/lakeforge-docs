# 🌊 LakeForge Documentation Portal

[![Documentation Site](https://img.shields.io/badge/docs-online-blue.svg)](https://jayarampogakula.github.io/lakeforge-docs/)
[![LakeForge Repository](https://img.shields.io/badge/code-Lakeforge-brightgreen.svg)](https://github.com/jayarampogakula/Lakeforge)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)
[![Databricks Runtime](https://img.shields.io/badge/Databricks-13.3%20LTS%20%7C%2014.3%20LTS%20%7C%2015.4%20LTS-orange)](https://docs.databricks.com/)

Welcome to the **Official Documentation Repository** for [**LakeForge**](https://github.com/jayarampogakula/Lakeforge) — the enterprise metadata-driven Data Lakehouse framework on Databricks and Delta Lake.

---

## 🌐 Official Documentation Site

👉 **Access the Live Interactive Documentation Site:**  
### **[https://jayarampogakula.github.io/lakeforge-docs/](https://jayarampogakula.github.io/lakeforge-docs/)**

You can also browse the documentation locally by opening [`index.html`](index.html) in any web browser.

---

## 📚 Documentation Table of Contents

| Section | Description | Markdown Guide |
|---|---|---|
| 🚀 **[Getting Started](docs/getting-started.md)** | 5-minute quickstart, catalog setup, and running your first pipeline | [`docs/getting-started.md`](docs/getting-started.md) |
| 📦 **[Installation](docs/installation.md)** | Pip, Databricks cluster libraries, Docker, and Databricks Asset Bundles (DABs) | [`docs/installation.md`](docs/installation.md) |
| 🏗️ **[Architecture](docs/architecture.md)** | Medallion architecture deep dive: Bronze, Silver, Gold, Views, and Trust Engine | [`docs/architecture.md`](docs/architecture.md) |
| 💡 **[Concepts](docs/concepts.md)** | Declarative pipelines, multi-tenancy, schema drift, quarantine pattern, and SCD2 | [`docs/concepts.md`](docs/concepts.md) |
| 💻 **[CLI Reference](docs/cli.md)** | LakeForge CLI syntax: `init`, `validate`, `run`, and `deploy` commands | [`docs/cli.md`](docs/cli.md) |
| 📋 **[Examples](docs/examples.md)** | Code and JSON configs for Oracle, Kafka, Auto Loader, SCD2, and PII masking | [`docs/examples.md`](docs/examples.md) |
| 🎓 **[Tutorials](docs/tutorials.md)** | Step-by-step end-to-end retail lakehouse, quarantine workflows, and CI/CD | [`docs/tutorials.md`](docs/tutorials.md) |
| ⭐ **[Best Practices](docs/best-practices.md)** | Delta Lake tuning, Liquid clustering, secrets security, and micro-batching | [`docs/best-practices.md`](docs/best-practices.md) |
| ❓ **[FAQ](docs/faq.md)** | Frequently asked questions on DLT comparison, Spark portability, and errors | [`docs/faq.md`](docs/faq.md) |
| 🗺️ **[Roadmap](docs/roadmap.md)** | Product roadmap: Phase 1 through Phase 4 (AI, UniForm, and Data Mesh) | [`docs/roadmap.md`](docs/roadmap.md) |
| 🏷️ **[Releases](docs/releases.md)** | Release notes, v1.0.0 changelog, semantic versioning, and upgrade guides | [`docs/releases.md`](docs/releases.md) |

---

## 🔌 Connectors & Technical Guides

In addition to the 11 core sections above, this repository also houses the comprehensive technical deep dives migrated from the core repository:

| Guide | Description | Markdown Link |
|---|---|---|
| 🔌 **Source Connectors** | Detailed configs for all 16 storage, database, and SaaS connectors | [`docs/ingestion/README.md`](docs/ingestion/README.md) |
| 🛡️ **Data Quality Catalog** | Complete reference of DQ rules, thresholds, and quarantine metrics | [`docs/dq-rules/README.md`](docs/dq-rules/README.md) |
| 🧩 **Module Guide** | Python package internals, functions, and architecture | [`docs/MODULE_GUIDE.md`](docs/MODULE_GUIDE.md) |
| 🧪 **Testing Suite** | Unit test suite, integration tests, and CI/CD validation | [`docs/testing/TESTING_GUIDE.md`](docs/testing/TESTING_GUIDE.md) |
| 📖 **Implementation Guide** | Complete implementation architecture and design decisions | [`docs/getting-started/Implementation_guide.md`](docs/getting-started/Implementation_guide.md) |
| 💻 **API Reference Manual** | Full HTML function and module reference manual | [`docs/index.html`](docs/index.html) |

---

## 💻 Running the Documentation Site Locally

Clone this documentation repository and open `index.html`:

```bash
git clone https://github.com/jayarampogakula/lakeforge-docs.git
cd lakeforge-docs

# Open in browser (Windows PowerShell)
Start-Process index.html

# Or serve via Python HTTP server
python -m http.server 8000
# Visit http://localhost:8000 in your browser
```

---

## 🤝 Contributing to LakeForge Docs

We welcome contributions to improve the documentation!
1. Fork this repository: `https://github.com/jayarampogakula/lakeforge-docs`
2. Create a feature branch: `git checkout -b docs/add-new-guide`
3. Commit your edits: `git commit -m "docs: improve tutorial on SCD2"`
4. Push to your branch and submit a Pull Request.

---

## 📄 License

This documentation is licensed under the Apache 2.0 License.
