/**
 * Entrypoint for the apps/web/ frontend rebuild scaffold.
 *
 * This file intentionally does nothing user-visible. It exists so that
 * the Vite dev server and `vite build` have something to chew on, and
 * so that future PRs migrating modules out of the monolithic root
 * index.html have an obvious place to land.
 *
 * See: docs/adr/0013-frontend-rebuild-scaffold.md
 */

export const SCAFFOLD_VERSION = "0.1.0-scaffold" as const;

export function mountScaffoldBanner(target: HTMLElement): void {
  const banner = document.createElement("div");
  banner.dataset.role = "scaffold-banner";
  banner.textContent = `apps/web scaffold ${SCAFFOLD_VERSION} — see ADR-0013`;
  target.append(banner);
}

if (typeof document !== "undefined") {
  const root = document.getElementById("app");
  if (root) {
    mountScaffoldBanner(root);
  }
}
