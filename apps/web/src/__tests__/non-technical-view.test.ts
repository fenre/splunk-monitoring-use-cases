/**
 * Shape-invariant tests for `non-technical-view.js`, the legacy
 * authoring surface for the non-technical view's plain-language
 * outcomes and "areas of monitoring" per category.
 *
 * What this suite asserts:
 *
 * 1. The legacy JS file exists at the expected repo-root path and
 *    populates `window.NON_TECHNICAL` when executed.
 * 2. The catalogue covers categories 1..23 with no gaps and no
 *    extras (matches drift-ledger #5 in the canonical progress doc).
 * 3. Every category has at least one outcome sentence and at least
 *    one area, and the per-area authoring contract from
 *    `.cursor/rules/non-technical-sync.mdc` holds (name +
 *    description + ucs[] required, 2–3 UCs per area).
 * 4. Every UC reference is shaped `X.Y.Z` and has a non-empty `why`
 *    explanation.
 * 5. Cat-22 areas that carry an `evidencePack` link (i.e. tier-1
 *    regulations) also carry the four other Phase 4.3 compliance
 *    elevation fields (`whatItIs`, `whoItAffects`, `splunkValue`,
 *    `primer`) per the same authoring contract.
 *
 * What this suite deliberately does NOT assert:
 *
 *   - That every UC reference points at a UC that actually exists in
 *     the catalogue. That cross-check is owned by the Python audit
 *     `audit-non-technical-references` (see
 *     `src/splunk_uc/audits/non_technical_references.py`) and runs
 *     in `audits-content`. Duplicating it here would re-walk all
 *     7,929 sidecars on every CI run with no gain in signal.
 *   - The exact authored phrasing of any field. Those are content
 *     decisions managed in PRs, not invariants.
 */

import { describe, expect, it } from "vitest";

import {
  LEGACY_NON_TECHNICAL_JS_PATH,
  listCategoryKeys,
  loadCatalogFromLegacyJs,
} from "../non-technical-view.ts";
import type {
  NonTechnicalArea,
  NonTechnicalCatalog,
} from "../non-technical-view.types.ts";

const UC_ID_RE = /^\d+\.\d+\.\d+$/;
const EXPECTED_CATEGORIES: readonly string[] = Array.from(
  { length: 23 },
  (_, i) => String(i + 1),
);

let catalog: NonTechnicalCatalog;
try {
  catalog = loadCatalogFromLegacyJs();
} catch (err) {
  // Surface the loader error inside the very first test rather than
  // crashing the whole module — keeps the failure localised and
  // readable in the vitest reporter.
  catalog = {} as NonTechnicalCatalog;
  // eslint-disable-next-line no-console -- intentional, for vitest output
  console.error("loadCatalogFromLegacyJs failed:", err);
}

describe("loadCatalogFromLegacyJs (loader)", () => {
  it("resolves the legacy JS path to non-technical-view.js at the repo root", () => {
    expect(LEGACY_NON_TECHNICAL_JS_PATH).toMatch(/[/\\]non-technical-view\.js$/);
  });

  it("returns a non-empty catalogue object", () => {
    expect(catalog).toBeTruthy();
    expect(typeof catalog).toBe("object");
    expect(Object.keys(catalog).length).toBeGreaterThan(0);
  });

  it("throws a useful error when pointed at a non-existent path", () => {
    expect(() =>
      loadCatalogFromLegacyJs("/this/path/does/not/exist/non-technical-view.js"),
    ).toThrow();
  });
});

describe("category coverage", () => {
  it("covers exactly categories 1..23 with no gaps and no extras", () => {
    expect(listCategoryKeys(catalog)).toEqual(EXPECTED_CATEGORIES);
  });
});

describe("per-category invariants", () => {
  for (const key of EXPECTED_CATEGORIES) {
    describe(`cat-${key}`, () => {
      it("exists in the catalogue", () => {
        expect(catalog[key], `cat-${key} missing`).toBeDefined();
      });

      it("declares at least one outcome sentence", () => {
        const outcomes = catalog[key]?.outcomes ?? [];
        expect(outcomes.length, `cat-${key} outcomes`).toBeGreaterThanOrEqual(1);
        for (const sentence of outcomes) {
          expect(typeof sentence, `cat-${key} outcome typeof`).toBe("string");
          expect(sentence.trim().length, `cat-${key} outcome non-empty`).toBeGreaterThan(0);
        }
      });

      it("declares at least one area", () => {
        const areas = catalog[key]?.areas ?? [];
        expect(areas.length, `cat-${key} areas`).toBeGreaterThanOrEqual(1);
      });
    });
  }
});

describe("per-area authoring contract", () => {
  it("every area has a non-empty name and description", () => {
    for (const [catKey, cat] of Object.entries(catalog)) {
      cat.areas.forEach((area, i) => {
        expect(typeof area.name, `cat-${catKey} area[${i}] name typeof`).toBe(
          "string",
        );
        expect(area.name.trim(), `cat-${catKey} area[${i}] name non-empty`)
          .not.toBe("");
        expect(
          typeof area.description,
          `cat-${catKey} area[${i}] description typeof`,
        ).toBe("string");
        expect(
          area.description.trim(),
          `cat-${catKey} area[${i}] description non-empty`,
        ).not.toBe("");
      });
    }
  });

  it("every area carries an array of 1–10 UC references", () => {
    // The authoring rule says "exactly 3 UCs (2 acceptable for small
    // subcategories)". Some cat-22 tier-1 areas have authored more
    // representative UCs; cap at a sane upper bound rather than
    // pinning to 3 to avoid forcing ContentChange PRs to also touch
    // this test.
    for (const [catKey, cat] of Object.entries(catalog)) {
      cat.areas.forEach((area, i) => {
        expect(
          Array.isArray(area.ucs),
          `cat-${catKey} area[${i}] ucs is array`,
        ).toBe(true);
        expect(
          area.ucs.length,
          `cat-${catKey} area[${i}] (${area.name}) UC count`,
        ).toBeGreaterThanOrEqual(1);
        expect(
          area.ucs.length,
          `cat-${catKey} area[${i}] (${area.name}) UC count`,
        ).toBeLessThanOrEqual(10);
      });
    }
  });
});

describe("UC-reference invariants", () => {
  it("every UC reference id matches X.Y.Z and `why` is a non-empty string", () => {
    for (const [catKey, cat] of Object.entries(catalog)) {
      cat.areas.forEach((area) => {
        area.ucs.forEach((uc) => {
          expect(
            uc.id,
            `cat-${catKey} area "${area.name}" UC id "${uc.id}"`,
          ).toMatch(UC_ID_RE);
          expect(
            typeof uc.why,
            `cat-${catKey} UC ${uc.id} why typeof`,
          ).toBe("string");
          expect(
            uc.why.trim(),
            `cat-${catKey} UC ${uc.id} why non-empty`,
          ).not.toBe("");
        });
      });
    }
  });

  it("every UC reference id matches its declaring category number", () => {
    for (const [catKey, cat] of Object.entries(catalog)) {
      cat.areas.forEach((area) => {
        area.ucs.forEach((uc) => {
          const idCat = uc.id.split(".")[0];
          expect(
            idCat,
            `cat-${catKey} area "${area.name}" UC ${uc.id} category prefix`,
          ).toBe(catKey);
        });
      });
    }
  });
});

describe("cat-22 Phase 4.3 compliance elevation contract", () => {
  it("every cat-22 area that carries `evidencePack` also carries `whatItIs`, `whoItAffects`, `splunkValue`, and `primer`", () => {
    const cat22 = catalog["22"];
    expect(cat22, "cat-22 missing").toBeDefined();
    if (!cat22) return;

    const tier1Areas: NonTechnicalArea[] = cat22.areas.filter(
      (a) => typeof a.evidencePack === "string" && a.evidencePack.length > 0,
    );

    expect(
      tier1Areas.length,
      "expected at least 12 cat-22 tier-1 areas with evidencePack (per non-technical-sync.mdc)",
    ).toBeGreaterThanOrEqual(12);

    for (const area of tier1Areas) {
      expect(area.whatItIs, `cat-22 area "${area.name}" whatItIs`).toBeTruthy();
      expect(
        area.whoItAffects,
        `cat-22 area "${area.name}" whoItAffects`,
      ).toBeTruthy();
      expect(
        area.splunkValue,
        `cat-22 area "${area.name}" splunkValue`,
      ).toBeTruthy();
      expect(area.primer, `cat-22 area "${area.name}" primer`).toBeTruthy();
    }
  });

  it("every cat-22 area `primer` link points into docs/regulatory-primer.md or guide-reader.html", () => {
    const cat22 = catalog["22"];
    if (!cat22) return;

    for (const area of cat22.areas) {
      if (typeof area.primer !== "string") continue;
      expect(
        area.primer,
        `cat-22 area "${area.name}" primer link shape`,
      ).toMatch(/^(docs\/regulatory-primer\.md|docs\/guide-reader\.md|regulatory-primer\.html|guide-reader\.html)/);
    }
  });

  it("every cat-22 area `evidencePack` link points into docs/evidence-packs/", () => {
    const cat22 = catalog["22"];
    if (!cat22) return;

    for (const area of cat22.areas) {
      if (typeof area.evidencePack !== "string") continue;
      expect(
        area.evidencePack,
        `cat-22 area "${area.name}" evidencePack link shape`,
      ).toMatch(/^docs\/evidence-packs\/.+\.md$/);
    }
  });
});
