# Replication Starter Template

A minimum-viable fork of the splunk-monitoring-use-cases product: one category, one use case, a ~30-line `build.py`, a ~60-line `index.html`. Everything else is layered on top of this.

## What this is

A working static catalog dashboard that:

1. Reads `use-cases/cat-*.md` (one file per category) with a fixed heading + bulleted-field schema.
2. Compiles the markdown into `data.js` (a global `DATA` constant) and `catalog.json`.
3. Renders a filterable card grid in a browser.

It has no audits, no API shards, no exports, no LLM index, no CI. The full reference is the parent repo; the parent demonstrates all those layered features.

## Run it

```bash
python3 build.py
python3 -m http.server 8080
# open http://localhost:8080/
```

Edit `use-cases/cat-01-example.md`, rerun `build.py`, refresh the browser.

## Files

| File | Purpose |
|---|---|
| `build.py` | ~30 LOC Python stdlib script that parses markdown and emits `data.js` + `catalog.json` |
| `use-cases/cat-01-example.md` | One category with two example use cases |
| `index.html` | Minimal dashboard: filter strip, card grid |
| `catalog.schema.json` | JSON shape emitted by `build.py` |

## Next steps for your fork

1. **Add your content.** Copy `use-cases/cat-01-example.md` to `use-cases/cat-02-...`, `cat-03-...`, etc. Rerun `build.py`.
2. **Add a query language.** The starter does not prescribe a query language. If you want to carry SPL / KQL / DQL / YARA-L, add a `- **Query:**` field with a fenced block and wire it in `build.py`.
3. **Add audits.** Copy a script from the parent repo's `scripts/` directory. Start with `audit_uc_ids.py`.
4. **Add CI.** Copy `.github/workflows/validate.yml` from the parent repo.
5. **Add exports.** Depending on your target platform, write a `scripts/build_<platform>_pack.py` that reads `catalog.json` and emits the platform's deployable artefact.

See [../../docs/replication-guide.md](../../docs/replication-guide.md) for worked examples (Sentinel / Datadog / Chronicle).
