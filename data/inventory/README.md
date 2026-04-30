# data/inventory/

CSV and JSON exports produced from the catalogue for audits and gap analysis. Because they require the full regeneration pipeline, the committed files are **historical point-in-time snapshots**, not live mirrors of the current UC count.

- **`ucs.csv`** — Tabular inventory aligned with an older catalogue slice (6,304 rows in the committed file vs ~7,364 UCs in the current catalogue). Use for reproducible analysis of that snapshot only; regenerate when the pipeline is available for up-to-date rows.
- **`gap-analysis.json`** — Gap metrics for the same era (see the top-level `$comment` and `totalUseCases` in that file). For current numbers, regenerate with `scripts/audit_content_gaps.py` once the full pipeline is run.
