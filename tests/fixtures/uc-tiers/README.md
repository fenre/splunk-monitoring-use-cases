# UC quality-tier fixtures (category 99)

Synthetic use-case sidecars covering every **quality tier × criticality** combination.
They live under `tests/fixtures/uc-tiers/` and use reserved IDs `99.99.1`–`99.99.9`
(display form `UC-99.99.N`). Category **99** is fixture-only and never overlaps
production catalogue content under `content/cat-*/`.

## Matrix

| File | Tier | Criticality | UC ID |
|------|------|-------------|-------|
| `gold-high-criticality.json` | gold | high | UC-99.99.1 |
| `gold-medium-criticality.json` | gold | medium | UC-99.99.2 |
| `gold-low-criticality.json` | gold | low | UC-99.99.3 |
| `silver-high-criticality.json` | silver | high | UC-99.99.4 |
| `silver-medium-criticality.json` | silver | medium | UC-99.99.5 |
| `silver-low-criticality.json` | silver | low | UC-99.99.6 |
| `bronze-high-criticality.json` | bronze | high | UC-99.99.7 |
| `bronze-medium-criticality.json` | bronze | medium | UC-99.99.8 |
| `bronze-low-criticality.json` | bronze | low | UC-99.99.9 |

## Design intent

- **Gold** — full rubric depth per `schemas/uc-profile-gold.json`: all gold-required
  fields populated, best-practice SPL (early filters, pipe-per-line, `where` after
  `stats`), product-specific `detailedImplementation`, and every optional schema
  field that makes sense for a realistic sidecar.
- **Silver** — silver-required fields plus ~70 % of optional enrichments (CIM
  variants, false-positive notes, control tests, etc.) without gold-only fields
  like `equipmentModels` or `visualization`.
- **Bronze** — schema minimum plus bronze rubric fields only; SPL deliberately
  carries anti-patterns (`makeresults`, `join`, `random()`, one-liner pipes,
  `search` after `stats`) for negative testing.

Every fixture includes `grandmaExplanation` (required for non-technical UI parity).

## Consumers

Downstream lanes discover fixtures via `MANIFEST.json`:

| Lane | Purpose |
|------|---------|
| **B-2** | SPL anti-pattern and grammar audits |
| **B-6** | Description vs value distinctness and depth scoring |
| **B-8** | Schema-cycle validation harness |
| **H-2** | Dashboard Studio template seeds |
| **H-4** | Alert template seeds |
| **K-2** | Adversarial / negative testing |

## Validation

```bash
python -m pytest tests/splunk_uc/test_uc_tier_fixtures.py -v
```

Each JSON file must validate against `schemas/uc.schema.json`. The manifest must
stay byte-synchronized with the on-disk fixture set (see round-trip test).

## Adding a new fixture

1. Pick the next free `99.99.N` id (never reuse; never use category ≠ 99).
2. Name the file `{tier}-{criticality}-criticality.json` to match siblings.
3. Add a manifest entry with `tier`, `criticality`, and `consumers[]`.
4. Extend `tests/splunk_uc/test_uc_tier_fixtures.py` if new invariants apply.
5. Run the pytest module above before committing.

Do **not** place fixtures under `content/` — Lane N owns production sidecars.
