# `category.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released  | Stability | Notes                                                                                                  |
|---------|-----------|-----------|--------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-Q2   | stable    | Initial schema formalizing the `_category.json` file structure that has been in use since v7.0. Requires: `$schema`, `id`, `name`, `slug`, `shortSlug`, `src`, `icon`, `description`, `quickTip`, `quickStart`, `subcategories`, `useCaseCount`. Subcategory items require `id` and `name`; optional fields include `useCaseCount`, `primaryAppTa`, `guide`, `dataSources`. |
