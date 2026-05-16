/**
 * Type definitions for the non-technical view catalogue.
 *
 * Mirrors the data structure authored in the repository-root file
 * `non-technical-view.js`, which is loaded as a global script by
 * `index.html` and populates `window.NON_TECHNICAL`.
 *
 * Source-of-truth contract: `non-technical-view.js` is still the
 * canonical authoring surface — see
 * `.cursor/rules/non-technical-sync.mdc` and
 * `docs/adr/0013-frontend-rebuild-scaffold.md` §"Migration shape".
 * This module exists so that future `apps/web/` modules can consume
 * the catalogue with type safety, and so that `vitest` can run shape
 * invariants over the live data via
 * `loadCatalogFromLegacyJs()` (see `./non-technical-view.ts`).
 */

export interface NonTechnicalUcRef {
  /** Use-case id in `X.Y.Z` form. Must point at a real UC in the catalog. */
  readonly id: string;
  /** Plain-language explanation of why this UC matters in the area. */
  readonly why: string;
}

export interface NonTechnicalArea {
  /** Short plain-language area name (e.g. "Performance & capacity"). */
  readonly name: string;
  /** 1–2 sentence non-technical description of what the area covers. */
  readonly description: string;
  /** Two or three representative UCs for the area. */
  readonly ucs: readonly NonTechnicalUcRef[];

  /**
   * Cat-22 tier-1 / cross-cutting compliance areas additionally carry
   * five plain-language fields aimed at privacy, legal, risk, and
   * executive readers. See
   * `.cursor/rules/non-technical-sync.mdc` §"Cat-22 compliance
   * elevation fields (Phase 4.3)" for the authoring contract.
   */

  /** One sentence defining the regulation in plain English. */
  readonly whatItIs?: string;
  /** One sentence naming the obligated entities (size / sector / jurisdiction). */
  readonly whoItAffects?: string;
  /** One sentence describing what the Splunk catalogue delivers for this area. */
  readonly splunkValue?: string;
  /** Repo-relative path with optional `#anchor` into `docs/regulatory-primer.md`. */
  readonly primer?: string;
  /** Repo-relative path to the auditor-facing evidence pack under `docs/evidence-packs/`. */
  readonly evidencePack?: string;
}

export interface NonTechnicalCategory {
  /** 2–4 plain-language sentences summarising the category's value. */
  readonly outcomes: readonly string[];
  /** One entry per subcategory under this top-level category. */
  readonly areas: readonly NonTechnicalArea[];
}

/**
 * The full catalogue, keyed by category number rendered as a string
 * (e.g. `"1"`, `"22"`). Categories run from 1 to 23 inclusive at HEAD;
 * see [`docs/health-check-2026-progress.md`](../../../docs/health-check-2026-progress.md)
 * drift-ledger #5 for the live count.
 */
export type NonTechnicalCatalog = Readonly<Record<string, NonTechnicalCategory>>;
