# `baselines.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes                                                                                                                          |
|---------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2  | preview   | Initial release. Validates `data/baselines/v<VERSION>.json` snapshots captured by `tools/capture_baselines.py` for the repo-overhaul plan §7. Internal contract — used to ground later "X% smaller / Y× faster" claims in a measured floor. Marked `preview` until at least one downstream consumer outside the build pipeline depends on its shape. |

## Stability commitment

`x-stability: preview` — this schema is internal. The shape may evolve
without a major bump while the repo-overhaul plan iterates. Treat it as
locked once it becomes `stable`.
