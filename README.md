# Splunk Infrastructure Monitoring — Use Case Repository

A searchable repository of **1,000+** IT infrastructure monitoring use cases for Splunk: criticality, example SPL, implementation notes, CIM mappings, and recommended visualizations.

## Quick start

1. **Browse the dashboard**  
   Open `index.html` in a browser (or serve the repo statically). No server required.

2. **Rebuild after editing use cases**  
   ```bash
   python3 build.py
   ```  
   This reads `use-cases/*.md` and `use-cases/INDEX.md`, then writes `data.js`. Refresh the dashboard to see changes.

## Repository layout

| Path | Purpose |
|------|---------|
| `use-cases/` | Source of truth: `cat-00-preamble.md`, `cat-01` … `cat-20` (per-category use cases), `INDEX.md` (category metadata, quick starters) |
| `build.py` | Parses markdown → emits `data.js` (DATA, CAT_META, CAT_STARTERS, CAT_GROUPS) |
| `data.js` | Generated data consumed by the dashboard |
| `index.html` | Single-page dashboard UI |
| `docs/` | Extra docs (GitHub Pages setup, LLM recreation prompt) |
| `_legacy/` | Archival content; not used by the build (see `_legacy/README.md`) |
| `CODEBASE-DIAGRAM.md` | Mermaid diagrams of structure and data flow |

## Requirements

- **Python 3** (for `build.py` only; no extra packages).
- **Browser** to view `index.html` (no Node/npm).

## Hosting

To host on **GitHub Pages**: commit `index.html` and `data.js`, enable Pages from the default branch (e.g. `main`), root. See [docs/github-pages-setup.md](docs/github-pages-setup.md) for step-by-step instructions.

## License

Use and adapt the use cases and code as needed for your environment.
