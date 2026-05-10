# Replication Starter Template

The **production** catalog uses canonical UC sidecars under **`content/cat-*/UC-*.json`** and builds with **`make build`** or **`python3 tools/build/build.py --out dist`** (see [`AGENTS.md`](../../AGENTS.md) at the repo root).

This directory ships a **tiny JSON-only demo** (`build.py` + `content/`) so you can run a minimal SSOT parser in isolation before adopting the full `tools/build/` pipeline.

## Production pattern (forking for real)

1. Copy **`content/`**, **`tools/build/`**, **`schemas/`**, and **`Makefile`** from the parent repo.
2. Run **`make build`** → outputs land in **`dist/`** (catalog.json, data.js, llms.txt, the per-UC HTML/JSON/MD twins, etc.).
3. Author new UCs as JSON validated against **`schemas/uc.schema.json`**.

## Run the minimal stub (optional)

```bash
cd templates/replication-starter
python3 build.py
python3 -m http.server 8080
# open http://localhost:8080/
```

Edit any **`content/cat-01-example/UC-*.json`** sidecar (or the matching `_category.json` shell), rerun `build.py`, refresh the browser.

## Files

| File | Purpose |
|---|---|
| `tools/build/build.py` *(repo root)* | Full v8 pipeline: `content/` → `dist/` + APIs + exports |
| `content/cat-*/UC-*.json` *(repo root)* | Canonical UC records (this starter folder ships a one-category fixture) |
| `build.py` *(this folder only)* | ~80 LOC demo that walks `content/cat-*/UC-*.json` into `data.js` + `catalog.json` |
| `content/cat-01-example/_category.json` | One example category shell (id, name, subcategory list) |
| `content/cat-01-example/UC-1.1.1.json` | First example use case (failed login spike) |
| `content/cat-01-example/UC-1.1.2.json` | Second example use case (disk usage) |
| `index.html` | Minimal dashboard: filter strip, card grid |
| `catalog.schema.json` | JSON shape emitted by the **stub** `build.py` |

## Next steps for your fork

1. **Add your content.** Author new sidecars under **`content/cat-NN-<slug>/UC-X.Y.Z.json`** so they validate against the parent repo's `schemas/uc.schema.json` and graduate to the full pipeline without rework.
2. **Build:** use **`make build`** from the repo root, not the stub, once you adopt `tools/build/`.
3. **Add audits.** Copy a script from the parent repo's `scripts/` directory. Start with `audit_uc_ids.py`.
4. **Add CI.** Copy `.github/workflows/validate.yml` from the parent repo.
5. **Add exports.** Depending on your target platform, write a `scripts/build_<platform>_pack.py` that reads **`catalog.json`** and emits the platform's deployable artefact.

See [../../docs/replication-guide.md](../../docs/replication-guide.md) for worked examples (Sentinel / Datadog / Chronicle).
