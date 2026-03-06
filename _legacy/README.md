# Legacy / archival content

This folder contains **outdated or superseded** assets and is **not** part of the active build or dashboard.

| File | Description |
|------|-------------|
| `use-cases-enriched.md` | Older single-file use case source (superseded by `use-cases/cat-*.md`) |
| `use-cases-full.md` | Supplementary legacy use case content |
| `infrastructure-categories.md` | Old category taxonomy (superseded by `use-cases/INDEX.md`) |
| `cim-enrichments.json` | Legacy CIM enrichment data |
| `cat-meta-raw.js` / `cat-starters-raw.js` | Old generated JS fragments |
| `use-case-dashboard.html` | Previous single-file dashboard (superseded by `index.html` + `data.js`) |
| `index.html.bak` | Backup of an older index |
| `enrich_cim.py` | Old script used for CIM enrichment |

**Do not** rely on these for the current repo. The live pipeline is: `use-cases/*.md` + `build.py` → `data.js` → `index.html`.
