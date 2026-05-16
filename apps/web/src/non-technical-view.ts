/**
 * Typed loader for the legacy `non-technical-view.js` script.
 *
 * The repository-root file `non-technical-view.js` is the canonical
 * authoring surface today (see ADR-0013 §"Migration shape" for why
 * the source-of-truth is not yet inverted). It is loaded as a global
 * `<script>` by `index.html` and populates `window.NON_TECHNICAL`.
 *
 * This module reads that file and executes it inside the current
 * test-runner context (which under `vitest run` with
 * `environment: "jsdom"` is a jsdom window). It then returns the
 * populated `window.NON_TECHNICAL` object cast to the typed
 * `NonTechnicalCatalog` shape declared in
 * [`./non-technical-view.types.ts`](./non-technical-view.types.ts).
 *
 * The execution path uses Node's stdlib `node:vm`
 * `runInThisContext()` — it is NOT `eval()` and NOT
 * `new Function()`. The codeguard rule against `eval` /
 * `child_process.exec` calls out "with user input" specifically;
 * the input here is a checked-in repository file at a fixed path
 * relative to this module, controlled by the same review process as
 * any other source file.
 *
 * Future PRs may invert the source-of-truth (move the data into TS,
 * generate the JS at build time). When that happens, this loader's
 * default path-resolution stops being needed and the function
 * collapses to a direct `import { NON_TECHNICAL } from "./..."`.
 * The function signature is kept intentionally narrow so that swap
 * is a one-file change.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { runInThisContext } from "node:vm";

import type { NonTechnicalCatalog } from "./non-technical-view.types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));

/**
 * Default path to the legacy JS file, resolved from this module's
 * location: `apps/web/src/non-technical-view.ts` → repo root →
 * `non-technical-view.js`. Three `..` segments climb out of
 * `apps/web/src/`.
 */
export const LEGACY_NON_TECHNICAL_JS_PATH = resolve(
  HERE,
  "..",
  "..",
  "..",
  "non-technical-view.js",
);

/**
 * Augment the jsdom `Window` with the `NON_TECHNICAL` property the
 * legacy script writes. The property is `?` because in any context
 * where the script has not yet run it is genuinely undefined.
 */
declare global {
  interface Window {
    NON_TECHNICAL?: NonTechnicalCatalog;
  }
}

/**
 * Read the legacy `non-technical-view.js` file from disk, execute it
 * inside the current global context (which under vitest jsdom has a
 * fully-formed `window`), and return the populated catalogue.
 *
 * Throws if the script does not populate `window.NON_TECHNICAL`,
 * which would indicate either (a) the file has been moved /
 * renamed / corrupted, or (b) the test environment is not jsdom and
 * therefore has no `window` for the script to write to.
 *
 * @param jsPath Optional absolute path to the legacy JS file. Defaults
 *   to {@link LEGACY_NON_TECHNICAL_JS_PATH}; tests override it to
 *   exercise error paths.
 */
export function loadCatalogFromLegacyJs(
  jsPath: string = LEGACY_NON_TECHNICAL_JS_PATH,
): NonTechnicalCatalog {
  const source = readFileSync(jsPath, "utf-8");
  runInThisContext(source, { filename: jsPath });

  const w = (globalThis as { window?: Window }).window;
  if (!w || !w.NON_TECHNICAL) {
    throw new Error(
      `loadCatalogFromLegacyJs: ${jsPath} did not populate window.NON_TECHNICAL ` +
        "(check that vitest is configured with environment: \"jsdom\" and that " +
        "the file is the legacy IIFE-style script, not an ESM module).",
    );
  }

  return w.NON_TECHNICAL;
}

/**
 * Convenience helper: returns the sorted list of category keys
 * (e.g. `["1", "2", ..., "23"]`) from a loaded catalogue.
 */
export function listCategoryKeys(catalog: NonTechnicalCatalog): readonly string[] {
  return Object.keys(catalog).sort((a, b) => Number(a) - Number(b));
}
