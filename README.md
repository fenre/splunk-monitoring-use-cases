# Splunk Infrastructure Monitoring — Use Case Repository

A searchable repository of **3,000+** IT infrastructure monitoring use cases for Splunk: criticality, example SPL, implementation notes, CIM mappings, equipment tagging, and recommended visualizations.

## Quick start

1. **Browse the dashboard**  
   Open `index.html` in a browser (or serve the repo statically). No server required.

2. **Rebuild after editing use cases**  
   ```bash
   python3 build.py
   ```  
   This reads `use-cases/*.md` and `use-cases/INDEX.md`, then writes `data.js` and `catalog.json`. Refresh the dashboard to see changes.

3. **Validate markdown structure**  
   ```bash
   python3 validate_md.py
   ```  
   Checks UC-ID consistency, category numbering, and code block balance.

4. **Change dashboard copy without it being overwritten**  
   Edit **`custom-text.js`** to change hero text, roadmap labels, filter chip names, and other Overview strings. This file is **not** generated or modified by `build.py`.

## Repository layout

| Path | Purpose |
|------|---------|
| `use-cases/` | Source of truth: `cat-00-preamble.md`, `cat-01` … `cat-20`, and `INDEX.md`. Only files with a top-level heading `# N.` or `## N.` become categories (20 total). `cat-00` is preamble/legend (skipped by the build). See [category files and names](docs/category-files-and-names.md). |
| `build.py` | Parses markdown → emits `data.js` (DATA, CAT_META, CAT_GROUPS, EQUIPMENT) and `catalog.json` |
| `validate_md.py` | Validates use case markdown structure and UC-ID consistency |
| `data.js` | Generated data consumed by the dashboard |
| `catalog.json` | Generated JSON catalog (same data as `data.js`, for external tooling) |
| `index.html` | Single-page dashboard UI |
| `custom-text.js` | User-editable site text (hero, roadmap, labels); not overwritten by build |
| `docs/` | [Use case fields](docs/use-case-fields.md), [Implementation guide](docs/implementation-guide.md), [CIM and data models](docs/cim-and-data-models.md), [Equipment table](docs/equipment-table.md), [Category files](docs/category-files-and-names.md), [GitHub Pages setup](docs/github-pages-setup.md), [Splunk apps comparison](docs/splunk-apps-use-cases-comparison.md) |
| `CODEBASE-DIAGRAM.md` | Mermaid diagrams of structure and data flow |

## Requirements

- **Python 3** (for `build.py` and `validate_md.py` only; no extra packages).
- **Browser** to view `index.html` (no Node/npm).

## Hosting

To host on **GitHub Pages**: commit `index.html`, `data.js`, and `custom-text.js`, enable Pages from the default branch (e.g. `main`), root. See [docs/github-pages-setup.md](docs/github-pages-setup.md) for step-by-step instructions.

## License

Use and adapt the use cases and code as needed for your environment.
