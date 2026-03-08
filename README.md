# Splunk Infrastructure Monitoring — Use Case Repository

A searchable repository of **1,000+** IT infrastructure monitoring use cases for Splunk: criticality, example SPL, implementation notes, CIM mappings, and recommended visualizations.

## Quick start

1. **Browse the dashboard**  
   Open `index.html` in a browser (or serve the repo statically). No server required.

2. **Rebuild after editing use cases**  
   ```bash
   python3 build.py
   ```  
   This reads `use-cases/*.md` and `use-cases/INDEX.md`, then writes `data.js`. Refresh the dashboard to see changes. To validate markdown structure and UC-ID consistency first, run `python3 use-cases/validate_md.py`.

3. **Change dashboard copy without it being overwritten**  
   Edit **`custom-text.js`** to change hero text, roadmap labels, filter chip names, and other Overview strings. This file is **not** generated or modified by `build.py` or by automated updates, so your edits stay in place.

4. **Import Splunk Security Essentials (SSE) use cases**  
   The [Splunk security_content](https://github.com/splunk/security_content) repo has 1,900+ detections. Import with `use-cases/import_sse_detections.py`, then run `use-cases/redistribute_sse_ucs.py` to place them in the best subcategory (10.1–10.8). See [docs/sse-import.md](docs/sse-import.md).

## Repository layout

| Path | Purpose |
|------|---------|
| `use-cases/` | Source of truth: `cat-00-preamble.md`, `cat-01` … `cat-20`. Only files with a top-level heading `# N.` or `## N.` become categories (20 total). **cat-00** is preamble/legend (skipped). Security (cat-10) holds all use cases in subcategories 10.1–10.8 (including ESCU/SSE content that was previously redistributed there); the separate import file was removed to avoid duplication. See [category files and names](docs/category-files-and-names.md). |
| `build.py` | Parses markdown → emits `data.js` (DATA, CAT_META, CAT_STARTERS, CAT_GROUPS) |
| `data.js` | Generated data consumed by the dashboard |
| `index.html` | Single-page dashboard UI |
| `custom-text.js` | User-editable site text (hero, roadmap, labels); not overwritten by build or tooling |
| `docs/` | Extra docs (GitHub Pages setup, [Implementation guide](docs/implementation-guide.md), [CIM and data models](docs/cim-and-data-models.md) (CIM, DMA, OCSF), [category files and display names](docs/category-files-and-names.md), [SSE import](docs/sse-import.md), [use case fields](docs/use-case-fields.md), [Splunk apps use cases comparison](docs/splunk-apps-use-cases-comparison.md)) |
| `_legacy/` | Archival content; not used by the build (see `_legacy/README.md`) |
| `CODEBASE-DIAGRAM.md` | Mermaid diagrams of structure and data flow |

## Requirements

- **Python 3** (for `build.py` only; no extra packages).
- **Browser** to view `index.html` (no Node/npm).

## Hosting

To host on **GitHub Pages**: commit `index.html` and `data.js`, enable Pages from the default branch (e.g. `main`), root. See [docs/github-pages-setup.md](docs/github-pages-setup.md) for step-by-step instructions.

## Splunk apps (sample v0.0.1)

- **Classic (iframe):** **`imucl/`** — Embeds the static dashboard in an iframe. Run `./build_app.sh --package` and install `imucl-0.0.1.spl`. See [imucl/README.md](imucl/README.md).
- **UI Toolkit (React):** **`imucl_uitoolkit/`** — React SPA built with Vite; no iframe. Run `./build_uitoolkit_app.sh` and install `imucl-uitoolkit-0.0.1.spl`. See [imucl_uitoolkit/README.md](imucl_uitoolkit/README.md). Use this if the classic app shows an empty dashboard.

The design for a full app (UCC-based layout, catalog lookup, saved searches) is in [docs/splunk-app-design.md](docs/splunk-app-design.md).

## Improving the resource

For ideas on making this repo even more useful for IT teams (starter paths, prerequisites, time estimates, doc links, checklists), see [docs/improvement-tips.md](docs/improvement-tips.md).

## License

Use and adapt the use cases and code as needed for your environment.
