# apps/web — Frontend Rebuild Scaffold

This directory is the staged home for the frontend rebuild called out in
plan items **P5**, **F16**, and **F17**. It is **not** the production UI
today.

The production UI is still the monolithic
[`index.html`](../../index.html) at the repository root (≈702 KB raw,
189 KB gzipped, rewritten in-place by `tools/build/build.py`). Migrating
modules out of that file is intentional and incremental. See
[`docs/adr/0013-frontend-rebuild-scaffold.md`](../../docs/adr/0013-frontend-rebuild-scaffold.md)
for the bundler / language / test-runner decision and its alternatives.

## Quick start

```bash
cd apps/web
npm install
npm run test       # vitest run — single passing smoke test
npm run typecheck  # tsc --noEmit (strict)
npm run dev        # vite dev server on :5173
npm run build      # vite build → apps/web/dist/
```

The smoke test in [`src/__tests__/smoke.test.ts`](src/__tests__/smoke.test.ts)
exists only to guarantee the toolchain is wired correctly. Real
migration PRs replace it.

## What lives here

| File | Purpose |
|------|---------|
| `package.json` | Pinned Vite + Vitest + TypeScript. Tooling-only. |
| `tsconfig.json` | Strict TS config (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, …). |
| `vite.config.ts` | Vite build + Vitest config in one place. |
| `index.html` | Minimal Vite entry. |
| `src/main.ts` | Placeholder entrypoint with one exported function. |
| `src/__tests__/smoke.test.ts` | Single passing smoke test (3 assertions). |

## What does NOT live here yet

Anything from the root `index.html`, `docs-uc-map.js`,
`non-technical-view.js`, `custom-text.js`, `provenance.js`, or
`guide-reader.js`. Those move in subsequent PRs, one module at a time,
each guarded by a tests-first migration PR. See
[F16](../../docs/health-check-2026-progress.md) for the migration plan.

## Out of scope

- **CI**: deliberately not wired into `.github/workflows/` yet.
  The scaffold is opt-in for now; the first migration PR introduces a
  CI job that runs `npm test` + `npm run typecheck` from this directory.
- **Deployment**: `apps/web/dist/` is **not** published to GitHub Pages.
  The root `dist/` is still the published artefact.
- **Framework**: no React / Vue / Svelte. Vanilla TS only.
  ADR-0013 §"Alternatives considered" explains why.

## Why no framework?

The current production UI is vanilla JS by convention. Layering a
framework on day one would couple the rebuild scaffold to a choice that
is much easier to revisit after the first real migration target is
identified. The scaffold's only opinion is "TypeScript-first, bundler
required"; framework adoption is deferred to its own ADR.
