# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] - 2026-03-16

First public release of the Splunk Infrastructure Monitoring Use Case Repository.

### Added

- **3,000+ use cases** across 20 IT infrastructure categories, each with criticality, difficulty, SPL queries, CIM mappings, implementation guidance, and visualization recommendations.
- **Interactive single-page dashboard** (`index.html`) with search, filtering by category/equipment/criticality, non-technical view, and expandable details.
- **Build pipeline** (`build.py`) that compiles use case markdown into `data.js` and `catalog.json`.
- **Validation script** (`validate_md.py`) for structure and UC-ID consistency checks.
- **Machine-readable catalog** (`catalog.json`) for scripting and external integrations.
- **Equipment filter** with 30+ technology vendors/platforms and model-level drill-down.
- **Non-technical view** (`non-technical-view.js`) with plain-language outcomes per category.
- **Customizable site text** (`custom-text.js`) for hero, roadmap, and UI labels.
- **GitHub Pages deployment** via included GitHub Actions workflow.
- **Documentation** covering use case fields, implementation guide, CIM/DMA/OCSF reference, equipment table, catalog schema, and hosting setup.
- **SSE-aligned fields** (MITRE ATT&CK, detection type, known false positives, security domain) for security use cases.
- **CIM SPL** (tstats/datamodel queries) for use cases with CIM data model support.
