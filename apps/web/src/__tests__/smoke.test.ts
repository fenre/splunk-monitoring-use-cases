import { describe, expect, it } from "vitest";
import { SCAFFOLD_VERSION, mountScaffoldBanner } from "../main.ts";

describe("apps/web scaffold smoke test", () => {
  it("exports a stable scaffold version", () => {
    expect(SCAFFOLD_VERSION).toBe("0.1.0-scaffold");
  });

  it("mounts a labelled banner element into the provided target", () => {
    const target = document.createElement("section");
    mountScaffoldBanner(target);

    const banner = target.querySelector<HTMLDivElement>(
      "[data-role='scaffold-banner']",
    );
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toMatch(/apps\/web scaffold/);
    expect(banner?.textContent).toMatch(/ADR-0013/);
  });
});
