/**
 * Emit `non-technical-view.js` at the repo root from the canonical
 * typed source `apps/web/src/data/non-technical-view.data.ts`.
 *
 * Why this script exists:
 *
 *   Pre-2026-05-17 the repo-root file `non-technical-view.js` was the
 *   authoring surface. The data was hand-edited as a JS object literal
 *   and consumed by `index.html` as a global script. ADR-0013
 *   §"Migration shape" earmarked the source-of-truth inversion as the
 *   next bite after the typed loader + 81-assertion Vitest suite
 *   landed (2026-05-16).
 *
 *   This script closes that inversion. The typed `NON_TECHNICAL`
 *   constant in `src/data/non-technical-view.data.ts` is now the
 *   canonical source; the repo-root `non-technical-view.js` is a
 *   generated artefact. A CI step (in `validate.yml`'s `frontend`
 *   job) runs `npm run emit:legacy` and `git diff --exit-code` to
 *   block drift between the two.
 *
 * Output-format contract:
 *
 *   Byte-identical to the pre-inversion `non-technical-view.js` so
 *   the inversion commit shows ONLY the `[generated]` header tweak
 *   on the JS side, not a 3000-line reformat. The legacy format is:
 *
 *     - 2-space indent, LF line endings, single trailing newline.
 *     - Top-level keys quoted ("1": ... "23":), area-level keys
 *       unquoted (name: description: whatItIs: etc).
 *     - Each area opens on a single line ending in `ucs: [`, with
 *       UCs each on their own line, closed by `      ]}`. Empty-line-
 *       free.
 *     - JSON.stringify-style string emission: `"` and `\` escaped,
 *       Unicode characters preserved as raw bytes (the existing file
 *       has 0 backslash-escape sequences inside string values, verified
 *       2026-05-17).
 *     - Trailing commas on every element EXCEPT the last in each
 *       collection (outcomes, ucs, areas, top-level cats).
 *     - Area field order (when present): name, description, whatItIs,
 *       whoItAffects, splunkValue, primer, evidencePack, ucs.
 *
 * Invariants asserted in CI (validate.yml frontend job):
 *
 *   1. `cd apps/web && npm run emit:legacy` produces a file at the
 *      repo-root path returned by `LEGACY_OUTPUT_PATH` below.
 *   2. `git diff --exit-code non-technical-view.js` is clean after
 *      step 1, i.e. the typed source round-trips byte-identical.
 *   3. The existing 81-assertion shape suite in
 *      `apps/web/src/__tests__/non-technical-view.test.ts` continues
 *      to pass — it loads `non-technical-view.js` (the *generated*
 *      file) and validates the catalogue structure, which gives us
 *      defense-in-depth against accidental emitter regressions.
 */

import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { NON_TECHNICAL } from "../src/data/non-technical-view.data.ts";
import type {
  NonTechnicalArea,
  NonTechnicalCatalog,
  NonTechnicalCategory,
  NonTechnicalUcRef,
} from "../src/non-technical-view.types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));

/**
 * Absolute path to the repo-root `non-technical-view.js`. From this
 * file (`apps/web/scripts/emit-legacy.ts`) climb three levels to the
 * repo root: scripts/ → apps/web/ → apps/ → <repo>/.
 */
export const LEGACY_OUTPUT_PATH = resolve(
  HERE,
  "..",
  "..",
  "..",
  "non-technical-view.js",
);

/**
 * The fixed header rendered at the top of `non-technical-view.js`.
 * Preserves the pre-inversion authoring header so consumers familiar
 * with that file see a near-identical prologue.
 *
 * The trailing newline is intentional: the existing file has a blank
 * line between the closing of its doc-block (which immediately
 * precedes the assignment) and the `window.NON_TECHNICAL` opener.
 */
const HEADER = [
  "/**",
  ' * Non-technical view: plain-language outcomes and "areas of monitoring" per category.',
  " * Used when the user selects \"Non-technical\" in the header.",
  " */",
  "",
].join("\n");

/**
 * The fixed footer: closes the object literal and the assignment.
 * Single trailing newline matches the pre-inversion file.
 */
const FOOTER = "};\n";

/**
 * Render a single UC reference as one indented line.
 * Output shape: `        { id: "X.Y.Z", why: "..." }`
 * The trailing comma (if any) is added by `emitArea`.
 */
function emitUc(uc: NonTechnicalUcRef): string {
  return `        { id: ${JSON.stringify(uc.id)}, why: ${JSON.stringify(uc.why)} }`;
}

/**
 * Render a single area as a multi-line block. The first line carries
 * `{ name: ..., ucs: [` (with every present optional field interleaved
 * in canonical order); subsequent lines carry one UC each; the closing
 * line is `      ]}` (with optional trailing comma).
 *
 * @param isLast - True for the final area in the category. Last areas
 *   omit the trailing comma after `]}`.
 */
function emitArea(area: NonTechnicalArea, isLast: boolean): string {
  const fields: string[] = [
    `name: ${JSON.stringify(area.name)}`,
    `description: ${JSON.stringify(area.description)}`,
  ];
  if (area.whatItIs !== undefined) {
    fields.push(`whatItIs: ${JSON.stringify(area.whatItIs)}`);
  }
  if (area.whoItAffects !== undefined) {
    fields.push(`whoItAffects: ${JSON.stringify(area.whoItAffects)}`);
  }
  if (area.splunkValue !== undefined) {
    fields.push(`splunkValue: ${JSON.stringify(area.splunkValue)}`);
  }
  if (area.primer !== undefined) {
    fields.push(`primer: ${JSON.stringify(area.primer)}`);
  }
  if (area.evidencePack !== undefined) {
    fields.push(`evidencePack: ${JSON.stringify(area.evidencePack)}`);
  }
  fields.push("ucs: [");

  const ucs = area.ucs.map(emitUc).join(",\n");
  const close = `      ]}${isLast ? "" : ","}`;
  return `      { ${fields.join(", ")}\n${ucs}\n${close}`;
}

/**
 * Render one category block: the `outcomes: [...]` array, then the
 * `areas: [...]` array. Both are emitted with their own 4-space
 * indents (i.e. two indent levels in: top object → cat object).
 */
function emitCategory(cat: NonTechnicalCategory): string {
  const outcomes = cat.outcomes
    .map((o) => `      ${JSON.stringify(o)}`)
    .join(",\n");

  const areas = cat.areas
    .map((a, i) => emitArea(a, i === cat.areas.length - 1))
    .join("\n");

  return [
    "    outcomes: [",
    outcomes,
    "    ],",
    "    areas: [",
    areas,
    "    ]",
  ].join("\n");
}

/**
 * Render the full catalogue to the legacy `non-technical-view.js`
 * byte sequence (UTF-8, LF line endings, single trailing newline).
 *
 * Categories are emitted in numeric order (1, 2, ... 23) regardless
 * of source order, so the data module can be reordered without
 * breaking the round-trip.
 */
export function renderLegacy(catalog: NonTechnicalCatalog): string {
  const keys = Object.keys(catalog).sort((a, b) => Number(a) - Number(b));
  const blocks: string[] = [];

  keys.forEach((k, i) => {
    const cat = catalog[k];
    if (cat === undefined) {
      // Should be unreachable given Object.keys+lookup, but the type
      // system widens record access to `T | undefined`.
      throw new Error(`emit-legacy: catalog["${k}"] missing after Object.keys`);
    }
    const isLast = i === keys.length - 1;
    blocks.push(`  ${JSON.stringify(k)}: {\n${emitCategory(cat)}\n  }${isLast ? "" : ","}`);
  });

  return `${HEADER}window.NON_TECHNICAL = {\n${blocks.join("\n")}\n${FOOTER}`;
}

/**
 * Write the emitted legacy JS to disk. Idempotent: re-running with the
 * same input yields the same bytes.
 */
export function main(): void {
  const out = renderLegacy(NON_TECHNICAL);
  writeFileSync(LEGACY_OUTPUT_PATH, out, "utf-8");
  // Single concise success line for CI logs; the diff guard does the
  // actual verification.
  // eslint-disable-next-line no-console -- intentional for CLI output
  console.log(
    `emit-legacy: wrote ${out.length} bytes to ${LEGACY_OUTPUT_PATH}`,
  );
}

/**
 * Only run main() when the script is invoked directly (e.g. via
 * `npm run emit:legacy` or `tsx scripts/emit-legacy.ts`). When the
 * module is imported by `__tests__/emit-legacy.test.ts` for the
 * `renderLegacy` pure function, side-effecting on disk would silently
 * overwrite the file under test.
 *
 * `import.meta.url` resolves to the URL of this module; `process.argv[1]`
 * is the script that the Node/tsx process was launched with. They
 * match iff this is the entry point.
 */
const isMain = (() => {
  const arg = process.argv[1];
  if (arg === undefined) return false;
  return import.meta.url === pathToFileURL(arg).href;
})();

if (isMain) {
  main();
}
