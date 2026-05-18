# ADR-0013: Use Vite + TypeScript + Vitest for the `apps/web/` frontend rebuild scaffold

- **Status:** Accepted
- **Date:** 2026-05-16
- **Deciders:** Repository maintainers
- **Closes plan finding:** P5 first cut — the empty-scaffolding step
  that lets F16 and F17 land as incremental migration PRs instead of
  monolithic "rebuild the frontend" verbs

## Context

The production UI for this catalogue is the monolithic
[`index.html`](../../index.html) at the repository root. At HEAD
`b51023419` (v8.6.4) it is **702 KB raw / 189 KB gzipped** and is
**rewritten in place by [`tools/build/build.py`](../../tools/build/build.py)**
on every build. Five sibling JS modules
(`docs-uc-map.js`, `non-technical-view.js`, `custom-text.js`,
`provenance.js`, `guide-reader.js`) are also at the repo root and are
likewise inlined / referenced from `index.html`.

This shape has two well-documented problems in
[`docs/health-check-2026-progress.md`](../health-check-2026-progress.md):

- **F16** (frontend has no test runner). The only browser-side
  verification today is the Playwright end-to-end suite under
  [`tests/e2e/`](../../tests/e2e/) and the axe-core a11y harness at
  [`tests/a11y/run-axe.mjs`](../../tests/a11y/run-axe.mjs). Both
  exercise the *built* `dist/` artefact; neither runs unit tests
  against frontend modules in isolation.
- **F17** (frontend has no build/bundler step). `tools/build/build.py`
  performs hand-rolled string substitution + JS concatenation. There
  is no tree-shaking, no module graph, no source maps, no type
  checking, no HMR for the maintainer.

**P5** in the canonical progress doc asked for a "first cut of frontend
rebuild scaffolding — empty `apps/web/` with Vite + TS + Vitest config,
a single passing smoke test, and an ADR ratifying the bundler /
framework / migration shape, so F16 and F17 anchor on that scaffold
instead of being monolithic rebuild verbs". This ADR is that
ratification.

The forces in play:

- **Migration safety.** Anything that touches the live `index.html`
  risks breaking the GitHub Pages deployment that downstream MCP /
  RAG / JSON-API consumers depend on. The scaffold must be **purely
  additive**: it must not change any file that `build.py` currently
  produces.
- **Repo culture.** Existing top-level JS modules are vanilla ES,
  no transpilation. Existing Node tests use the stdlib `node --test`
  runner on `.mjs` files (`tests/recommender/`, `tests/oscal/`,
  `tests/a11y/`). ADR-0004 already set a precedent of "Python stdlib
  only" for the Python side; by analogy a "Node stdlib first" instinct
  is reasonable.
- **Future-proofing.** §P4 wants `mypy --strict` floor on the Python
  side. The frontend deserves an equivalent commitment, which
  realistically means TypeScript with a strict compiler config from day
  one.
- **Tooling churn.** Vite 8 (May 2026) and Vitest 4 (May 2026) are
  current stable releases; both are dominant in the post-Webpack
  ecosystem. Pinning them now is low-risk.

## Decision

We will scaffold the future frontend at **`apps/web/`** with:

1. **Vite 8.x** as the dev server, build tool, and module bundler.
2. **TypeScript 6.x** in strict mode
   (`strict: true`, `noUncheckedIndexedAccess: true`,
   `exactOptionalPropertyTypes: true`, `verbatimModuleSyntax: true`).
3. **Vitest 4.x** as the unit-test runner, configured inside
   `vite.config.ts` so test config and build config never drift.
4. **No framework.** Vanilla TypeScript only. The scaffold's only
   opinion is "TypeScript-first, bundler required". Framework
   adoption — React, Vue, Svelte, Lit, or none — is deferred to a
   future ADR once the first real migration target is identified.
5. **No CI wiring yet.** `.github/workflows/` is **not** touched by
   this ADR. The first migration PR that lands real code into
   `apps/web/` introduces the workflow that runs
   `npm test` + `npm run typecheck` from this directory.
6. **No deploy wiring.** `apps/web/dist/` is **not** published. The
   root `dist/` produced by `tools/build/build.py` remains the
   GitHub Pages artefact until a later ADR explicitly swaps it.
7. **Locked dependency versions.** `package.json` pins minimum-major
   versions; `package-lock.json` is **committed** so reproducible
   `npm ci` works for everyone.

This scaffold introduces **one** module
([`src/main.ts`](../../apps/web/src/main.ts)) and **one** test
([`src/__tests__/smoke.test.ts`](../../apps/web/src/__tests__/smoke.test.ts))
purely to prove the toolchain wires up.

## Consequences

**Positive:**

- F16 and F17 acquire an obvious home. Every future migration PR
  becomes a small, reviewable verb: "move X from root `index.html`
  into `apps/web/`, with tests-first".
- TypeScript-strict on day one prevents the "we'll add types later"
  failure mode that left ADR-0004 enforcing Python typing piecemeal.
- Test runner exists from PR #1 of the migration. The first
  migrated module ships with vitest coverage; no retroactive
  "add tests" backlog.
- Bundler exists from PR #1 of the migration. Code-splitting,
  tree-shaking, and source maps are available for free as soon as
  the first real module lands.
- The scaffold is opt-in. Maintainers who only edit catalogue
  content never touch `apps/web/` and never run `npm install` here.
- ADR-0013 unblocks both F16 and F17 in the progress doc without
  shipping any user-visible change. Risk surface is minimal.

**Negative:**

- We now have **two** Node toolchains in the repo: the root
  `package.json` (Puppeteer + Playwright + ajv + axe-core + jsdom for
  test harnesses) and `apps/web/package.json` (Vite + Vitest + TS).
  This is intentional — the root toolchain serves
  *built-artefact* validation, the `apps/web` toolchain serves
  *source-module* development — but it does increase the surface area
  the maintainer has to think about. See the §"Alternatives
  considered" §3 trade-off.
- The team commits to TypeScript-strict for all new frontend code.
  That is a real, ongoing cost. The mitigation is that strict mode
  pays for itself the moment the first migration PR catches a runtime
  bug at compile time.
- Vite + Vitest pin us to the Vite ecosystem release cadence.
  Mitigated by Vite's strong stability track record and by the fact
  that the scaffold is small enough that swapping to another bundler
  (esbuild standalone, Rolldown standalone, swc + Rollup) is a
  bounded refactor.
- One more `node_modules/` to disk-cache locally. Mitigated by the
  `apps/web/.gitignore` excluding it and by the root `.cursorignore`
  already excluding nested `node_modules/`.

## Alternatives considered

1. **Webpack 5 + ts-loader + Jest.** Mature, well-known, but
   heavy. ESM-first Vite makes Webpack feel dated; Jest's CommonJS
   bias plus need for `babel-jest` adds friction in a TypeScript-only
   project. Rejected on ergonomic grounds, not technical grounds.

2. **esbuild + tsc, no test runner.** Smallest possible surface
   area. Rejected because it would re-introduce F16 (no test runner)
   on day one — exactly the problem this ADR is meant to close.

3. **Node stdlib only — `node --test` against `.mts` files,
   bundle by hand.** Maximises alignment with ADR-0004's "Python
   stdlib only" instinct and with the existing `tests/*.mjs`
   patterns. Rejected because (a) Node's `--test` runner has no
   DOM environment, which any real frontend module will need;
   (b) hand-bundling re-introduces the F17 problem; (c) the
   maintainer would spend more time on the toolchain than on
   migrating modules. The principle "we prefer stdlib" still holds
   for the *root* `package.json`; this ADR scopes the trade-off to
   the new `apps/web/` tree only.

4. **Next.js / Remix / SvelteKit / similar full-stack framework.**
   Out of scope. The catalogue UI is static-first by ADR-0002 and
   the JSON API surface is already stable. A full-stack framework
   would force an SSR / routing model we do not need.

5. **Wait until F16 / F17 are tackled in a single PR.** This is
   what the canonical doc had pencilled in until this scaffold
   landed. Rejected because a monolithic "rebuild the frontend" PR
   is exactly the kind of change that becomes un-reviewable, drifts
   for months, and never merges. The whole point of P5 is to
   replace that monolith with a series of small, mergeable verbs.

6. **Put the scaffold at `frontend/` or `web/` or `ui/` instead of
   `apps/web/`.** The `apps/` prefix anticipates that more than one
   deliverable may live under the same Node-tooling umbrella in
   future (`apps/web/`, `apps/admin/`, `apps/print/`). Even if only
   `apps/web/` ever exists, the layout costs us nothing extra today.

## Migration shape (informative, not part of the decision)

The expected migration sequence for the modules currently at the
repo root, in dependency order:

1. `non-technical-view.js` → `apps/web/src/non-technical-view.ts`
   (pure data, easiest first migration, validates the toolchain on
   real code).
2. `docs-uc-map.js` → `apps/web/src/docs-uc-map.ts`
   (pure data, mostly mechanical).
3. `custom-text.js` → `apps/web/src/custom-text.ts`
   (pure data).
4. `provenance.js` → `apps/web/src/provenance.ts`
   (small surface area).
5. `guide-reader.js` → `apps/web/src/guide-reader.ts`
   (medium surface, owns the markdown reader UI).
6. The remaining inline JS inside the root `index.html`
   (catalogue search, sidebar, panel rendering) — likely several
   PRs, one per UI surface.

Each step is its own PR. Each step keeps the root `index.html`
continuing to function until the very last PR cuts the
GitHub-Pages-served entrypoint over to
`apps/web/dist/index.html`. **That** cutover is its own ADR — it is
explicitly out of scope here.

## Links

- Related code:
  [`apps/web/`](../../apps/web/),
  [`apps/web/package.json`](../../apps/web/package.json),
  [`apps/web/tsconfig.json`](../../apps/web/tsconfig.json),
  [`apps/web/vite.config.ts`](../../apps/web/vite.config.ts),
  [`apps/web/src/main.ts`](../../apps/web/src/main.ts),
  [`apps/web/src/__tests__/smoke.test.ts`](../../apps/web/src/__tests__/smoke.test.ts)
- Related ADRs:
  [ADR-0002](0002-static-single-page-app.md) (static SPA shape — preserved),
  [ADR-0004](0004-python-stdlib-only.md) (analogous tooling-restraint norm for the Python side),
  [ADR-0009](0009-generated-artefact-policy.md) (`apps/web/dist/` falls under the same "generated artefact" policy)
- Superseded by: —
- Closes: P5 (plan progress doc, scaffolding bullet);
  unblocks F16 and F17 (which now anchor on `apps/web/` instead of
  being monolithic "rebuild" verbs)

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Related repository documents

- [`docs/adr/0002-static-single-page-app.md`](0002-static-single-page-app.md)
- [`docs/adr/0004-python-stdlib-only.md`](0004-python-stdlib-only.md)
- [`docs/adr/0009-generated-artefact-policy.md`](0009-generated-artefact-policy.md)

### Cited by

- [`docs/adr/README.md`](README.md)
- [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md)

<!-- END-AUTOGENERATED-SOURCES -->
