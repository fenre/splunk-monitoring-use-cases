# Splunk Infrastructure Monitoring Use Cases

A curated collection of **5,225+ IT infrastructure monitoring use cases** for Splunk, organized across 23 technology domains. Each use case includes criticality rating, example SPL queries, implementation guidance, CIM data model mappings, equipment tagging, and visualization recommendations.

Browse them in the **interactive dashboard** or use the **machine-readable catalog** (`catalog.json`) for automation and integrations.

**Live dashboard:** [fenre.github.io/splunk-monitoring-use-cases](https://fenre.github.io/splunk-monitoring-use-cases/)

**Feedback:** In the dashboard, open any use case (technical or plain-language view) and click **Report issue on GitHub** to open a new issue with the UC id, source markdown link, and current page URL pre-filled. Forks can set `window.SITE_CUSTOM.siteRepoUrl` in `index.html` to point at their repository.

---

## Getting Started

### Browse the Dashboard

Open `index.html` in any browser. No server, build tools, or dependencies are required.

### Rebuild After Editing Use Cases

```bash
python3 build.py
```

This reads `use-cases/*.md` and `use-cases/INDEX.md`, then outputs `data.js` and `catalog.json`. Refresh the dashboard to see your changes.

### Validate Markdown Structure

```bash
python3 validate_md.py
```

Checks UC-ID consistency, category numbering, and code-block balance across all use case files.

### Random “Splunk fortune” (fun)

```bash
python3 scripts/splunk_fortune.py
```

Prints a random use case from `catalog.json` with a sample SPL line — like a fortune cookie for operators. Use `-n 3` for three picks.

### Customize Dashboard Text

Edit `custom-text.js` to change hero text, roadmap labels, filter chip names, footer, and other UI strings. This file is never overwritten by `build.py`.

### CIM-style fields in SPL examples

Use-case searches prefer **CIM-aligned names** (`src`, `dest`, `user`, …) over vendor `*_ip` fields where practical. See **`docs/cim-and-data-models.md`** and optional bulk helper **`scripts/normalize_cim_fields.py`**.

### Splunk Dashboard Studio (optional)

The **`dashboards/`** folder includes **Dashboard Studio** JSON exports with **synthetic** `makeresults` data — for example **`catalog-quick-start-top2.json`**, which has **one labeled chart per** Quick-Start use case (**44** panels = top 2 × 22 categories from `use-cases/INDEX.md`). See **`dashboards/README.md`** for UI import and **`scripts/deploy_dashboard_studio_rest.py`** to push the dashboard to a Splunk server via the **REST** API (`data/ui/views`). Regenerate the JSON with **`scripts/generate_catalog_dashboard.py`** after changing Quick Start lists.

### Data Sizing Assessment Tool

Open **`tools/data-sizing/`** (or click "Data Sizing Tool" in the dashboard footer) to estimate Splunk data ingest volume. Select equipment and data sources from a catalog of 206+ entries, configure endpoints/tags and polling rates, and get GB/day, EPS, license tier recommendations, and storage estimates. Exports a CSV sizing report. Key data sources link back to relevant use cases in the main catalog.

### Cribl / Splunk datagen (POC)

**`docs/guides/datagen-top10-use-cases.md`** describes how to drive **Cribl Stream Datagen** (or HEC) for **ten** representative catalog use cases, with **`eventgen_data/manifest-top10.json`**, sample lines under **`eventgen_data/samples/`**, and scripts **`scripts/generate_manifest_samples.py`** and **`scripts/parse_uc_catalog.py`**. See **`eventgen_data/README.md`**.

---

## Repository Structure

```
.
├── use-cases/              Source of truth: 23 category files + INDEX.md
│   ├── INDEX.md            Category metadata (icons, descriptions, quick starters)
│   ├── cat-00-preamble.md  Legend and field descriptions (not a category)
│   ├── cat-01-server-compute.md
│   ├── ...
│   ├── cat-20-cost-capacity-management.md
│   ├── cat-21-industry-verticals.md
│   ├── cat-22-regulatory-compliance.md
│   └── cat-23-business-analytics.md
├── build.py                Parses markdown, emits data.js and catalog.json
├── validate_md.py          Validates structure and UC-ID consistency
├── scripts/                Utilities (e.g. deploy Dashboard Studio via REST, regenerate catalog JSON)
├── index.html              Single-page dashboard UI
├── data.js                 Dashboard data (rebuild with build.py)
├── catalog.json            Machine-readable catalog (same data, JSON format)
├── custom-text.js          User-editable site text (not overwritten by build)
├── non-technical-view.js   Plain-language outcomes per category
├── llms.txt                AI-readable site index
├── llms-full.txt           Complete UC listing for LLMs
├── sitemap.xml             Search engine sitemap
├── robots.txt              Crawler directives
├── tools/                  Companion tools
│   └── data-sizing/        Data Sizing Assessment — ingest volume estimator
├── dashboards/             Optional Splunk Dashboard Studio JSON (synthetic demo data)
│   ├── README.md           Import instructions
│   ├── catalog-quick-start-top2.json
│   └── executive-health-dashboard.json
├── docs/                   Documentation
│   ├── guides/
│   │   └── datagen-top10-use-cases.md   Cribl/Splunk datagen POC (10 UCs)
│   ├── use-case-fields.md
│   ├── implementation-guide.md
│   ├── cim-and-data-models.md
│   ├── equipment-table.md
│   ├── category-files-and-names.md
│   ├── catalog-schema.md
│   ├── github-pages-setup.md
│   └── splunk-apps-use-cases-comparison.md
├── eventgen_data/          Datagen manifest + per-family sample logs (POC)
├── config/
│   └── uc_to_log_family.json   Default log family per category (manifest-all)
├── other/                  Environment-specific files (not part of the core catalog)
├── CODEBASE-DIAGRAM.md     Mermaid diagrams of architecture and data flow
├── CHANGELOG.md            Release history
└── LICENSE                 MIT License
```

---

## Technology Domains (23 Categories)

| # | Category | Examples |
|---|----------|----------|
| 1 | Server & Compute | Linux, Windows, macOS |
| 2 | Virtualization | VMware vSphere, Hyper-V |
| 3 | Containers & Orchestration | Kubernetes, Docker |
| 4 | Cloud Infrastructure | AWS, Azure, GCP |
| 5 | Network Infrastructure | Cisco, Palo Alto, Fortinet, F5 |
| 6 | Storage & Backup | SAN, NAS, object storage, backup |
| 7 | Database & Data Platforms | SQL Server, Oracle, PostgreSQL, Kafka |
| 8 | Application Infrastructure | Web servers, app servers, message queues |
| 9 | Identity & Access Management | Active Directory, Okta, CyberArk |
| 10 | Security Infrastructure | Firewalls, EDR, email security, SIEM |
| 11 | Email & Collaboration | Exchange, M365, Google Workspace, Webex |
| 12 | DevOps & CI/CD | Jenkins, GitHub, artifact registries |
| 13 | Observability & Monitoring Stack | Splunk platform health, ITSI |
| 14 | IoT & Operational Technology | HVAC, PLCs, sensors, Edge Hub |
| 15 | Data Center Physical Infrastructure | Power, cooling, physical security |
| 16 | Service Management (ITSM) | ServiceNow, incident/change management |
| 17 | Network Security & Zero Trust | NAC, VPN, device posture |
| 18 | Data Center Fabric & SDN | Cisco ACI, VMware NSX |
| 19 | Compute Infrastructure (HCI/Converged) | Nutanix, UCS, blade chassis |
| 20 | Cost & Capacity Management | Cloud cost, rightsizing, forecasting |
| 21 | Industry Verticals | Energy, manufacturing, healthcare, telecom, transportation, retail, aviation, insurance |
| 22 | Regulatory & Compliance Frameworks | GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, SOC 2 |
| 23 | Business Analytics | Executive dashboards, KPI tracking, data quality |

---

## Use Case Format

Each use case follows a structured markdown format with these fields:

| Field | Description |
|-------|-------------|
| **Criticality** | Critical, High, Medium, or Low |
| **Difficulty** | Beginner, Intermediate, Advanced, or Expert |
| **Value** | Why this use case matters |
| **App/TA** | Required Splunk add-ons or apps |
| **Data Sources** | Index and sourcetype requirements |
| **SPL** | Ready-to-use Splunk search query |
| **CIM Models** | Splunk Common Information Model mappings |
| **CIM SPL** | Accelerated tstats/datamodel query (where applicable) |
| **Implementation** | Deployment guidance |
| **Visualization** | Recommended dashboard panels |

Additional fields are available for security use cases (MITRE ATT&CK, detection type, known false positives) and for hardware-specific use cases (equipment models). See [docs/use-case-fields.md](docs/use-case-fields.md) for the complete field reference.

---

## Dashboard Features

- **Unified filter strip** with pillar, criticality, difficulty, regulation, monitoring type, and sort controls
- **Grouped sidebar navigation** with 6 collapsible sections (Infrastructure, Security, Cloud, Applications, Industry Verticals, Regulatory & Compliance)
- **Deep linking** with hash-based URLs — share links to categories, use cases, or search results
- **Search** across all use cases by keyword, UC-ID, or SPL content (Cmd/Ctrl+K shortcut)
- **Filter by equipment** you have (e.g. "Cisco", "AWS", "VMware") with optional model-level drill-down
- **Sort** by criticality, difficulty, name, or category
- **Virtual scrolling** for large lists (5,225+ use cases rendered on demand)
- **Non-technical view** with plain-language outcomes per category
- **Quick-win starters** highlighted per category for fast implementation
- **Print-friendly** layout with dedicated print stylesheet
- **Mobile-first** with off-canvas sidebar drawer, safe-area support, and 44px touch targets
- **Light/dark mode** with accessible contrast and ambient visual effects
- **Expandable details** with full SPL, CIM queries, and step-by-step implementation guides

---

## Machine-Readable Catalog

`catalog.json` contains all use case data in JSON format for scripting and integrations. See [docs/catalog-schema.md](docs/catalog-schema.md) for the schema and usage examples.

```python
import json

with open("catalog.json") as f:
    catalog = json.load(f)

for cat in catalog["DATA"]:
    for sub in cat["s"]:
        for uc in sub["u"]:
            print(f"UC-{uc['i']}: {uc['n']} ({uc.get('c', 'N/A')})")
```

---

## Hosting on GitHub Pages

The dashboard runs as a static site with no server-side dependencies:

1. Ensure `index.html`, `data.js`, `custom-text.js`, and `non-technical-view.js` are committed
2. Enable GitHub Pages from the repository settings (deploy from `main` branch, root)
3. The site is live at `https://<username>.github.io/<repo>/`

A GitHub Actions workflow (`.github/workflows/pages.yml`) is included for automatic deployment on push. See [docs/github-pages-setup.md](docs/github-pages-setup.md) for step-by-step instructions.

---

## Requirements

- **Python 3** for `build.py` and `validate_md.py` (standard library only, no extra packages)
- **Any modern browser** to view the dashboard

---

## Contributing

1. Edit or add use cases in `use-cases/cat-NN-*.md` following the format in [docs/use-case-fields.md](docs/use-case-fields.md)
2. Update `use-cases/INDEX.md` if adding quick-start entries or changing category metadata
3. Run `python3 build.py` to regenerate `data.js` and `catalog.json`
4. Run `python3 validate_md.py` to verify structure
5. Open a pull request

---

## Documentation

| Document | Description |
|----------|-------------|
| [Use Case Fields](docs/use-case-fields.md) | Complete field reference for use case markdown |
| [Implementation Guide](docs/implementation-guide.md) | Splunk directory layout, app installation, inputs, scripted inputs |
| [CIM and Data Models](docs/cim-and-data-models.md) | CIM, Data Model Acceleration, and OCSF reference |
| [Equipment Table](docs/equipment-table.md) | How the equipment filter works and how to add entries |
| [Category Files](docs/category-files-and-names.md) | File naming conventions and how categories map to the dashboard |
| [Catalog Schema](docs/catalog-schema.md) | catalog.json structure and scripting examples |
| [GitHub Pages Setup](docs/github-pages-setup.md) | Step-by-step hosting instructions |
| [Splunk Apps Comparison](docs/splunk-apps-use-cases-comparison.md) | How this repo relates to IT Essentials, ITSI content packs, and ESCU |
| [Architecture Diagrams](CODEBASE-DIAGRAM.md) | Mermaid diagrams of the build pipeline and data flow |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
