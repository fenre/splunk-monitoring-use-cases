# `starter-pack.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released | Stability | Notes |
|---------|----------|-----------|-------|
| 1.0.0   | 2026-Q4  | preview   | Initial release (guided onboarding Phase 1). Required `goal` (`security` \| `operations`), `status` (`draft` \| `published`), `pairId`, `equipment[]`, `requiredData` (Splunkbase apps, sourcetypes, internal indexes, licence/role notes), `industrySources[]`, ordered `steps[]` (`ucId` + `order` only, no SPL override), `nextPacks[]`. Optional `curationNotes[]`. Gated by `audit-starter-packs`; published under `/api/v1/starter-packs/`. |

## Stability commitment

`x-stability: preview` — shape may evolve while the first ten packs are curated and the wizard matures.
Treat as locked once promoted to `stable`.
