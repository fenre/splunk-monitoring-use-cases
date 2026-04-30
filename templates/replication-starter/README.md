# Replication Starter Template

The **production** catalog uses canonical UC files under **`content/cat-*/UC-*.json`** and builds with **`make build`** or **`python3 tools/build/build.py --out dist`** (see [`AGENTS.md`](../../AGENTS.md) at the repo root).

This directory also ships a **tiny markdown-only demo** (`build.py` + `use-cases/`) so you can run a minimal parser in isolation before adopting the full `tools/build/` pipeline.

## Production pattern (forking for real)

1. Copy **`content/`**, **`tools/build/`**, **`schemas/`**, and **`Makefile`** from the parent repo.
2. Run **`make build`** → outputs land in **`dist/`** plus repo-root artefacts (`catalog.json`, etc., per your CI).
3. Author new UCs as JSON validated against **`schemas/uc.schema.json`**.

## Run the minimal stub (optional)

```bash
cd templates/replication-starter
python3 build.py
python3 -m http.server 8080
# open http://localhost:8080/
```

Edit **`use-cases/cat-01-example.md`**, rerun `build.py`, refresh the browser.

## Files

| File | Purpose |
|---|---|
| `tools/build/build.py` *(repo root)* | Full v7 pipeline: `content/` → `dist/` + APIs + exports |
| `content/cat-*/UC-*.json` *(repo root)* | Canonical UC records (this starter folder does not include a full tree) |
| `build.py` *(this folder only)* | ~30 LOC demo that parses `use-cases/cat-*.md` into `data.js` + `catalog.json` |
| `use-cases/cat-01-example.md` | One category with two example use cases (demo markdown) |
| `index.html` | Minimal dashboard: filter strip, card grid |
| `catalog.schema.json` | JSON shape emitted by the **stub** `build.py` |

## Next steps for your fork

1. **Add your content.** Prefer UC JSON under **`content/`** (not the starter markdown) for parity with CI and schemas.
2. **Build:** use **`make build`** from the repo root, not the stub, once you adopt `tools/build/`.
3. **Add audits.** Copy a script from the parent repo's `scripts/` directory. Start with `audit_uc_ids.py`.
4. **Add CI.** Copy `.github/workflows/validate.yml` from the parent repo.
5. **Add exports.** Depending on your target platform, write a `scripts/build_<platform>_pack.py` that reads **`catalog.json`** and emits the platform's deployable artefact.

See [../../docs/replication-guide.md](../../docs/replication-guide.md) for worked examples (Sentinel / Datadog / Chronicle).
