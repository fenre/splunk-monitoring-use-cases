"""Cross the Cisco portfolio capability map with UC sidecars.

Reads ``data/cisco-portfolio.json`` and every ``content/**/UC-*.json``
sidecar, then writes:

- ``reports/cisco-coverage/matrix.json`` — per product: tagged UC count,
  per-capability coverage (covering UCs, CIM-backed UCs, status), and the
  ordered gap list that drives authoring.
- ``reports/cisco-coverage/matrix.md`` — the same data as tables.

A UC covers a capability when its ``capabilities[]`` names
``<slug>.<capability id>``. A capability that declares CIM models is
only fully covered when at least one covering UC lists one of those
models in ``cimModels`` and carries a ``cimSpl``.

The output carries no timestamp so ``--check`` is byte-stable.

Usage::

    python -m splunk_uc generate-cisco-coverage
    python -m splunk_uc generate-cisco-coverage --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO = Path(__file__).resolve().parents[3]
PORTFOLIO = REPO / "data" / "cisco-portfolio.json"
OUT_DIR = REPO / "reports" / "cisco-coverage"
GENERATOR = "python -m splunk_uc generate-cisco-coverage"

STATUS_COVERED = "covered"
STATUS_CIM_GAP = "cim_gap"
STATUS_UNCOVERED = "uncovered"
STATUS_NOT_OBSERVABLE = "not_observable"


def _uc_sort_key(uc_id: str) -> tuple[int, ...]:
    parts = uc_id.removeprefix("UC-").split(".")
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def load_portfolio(path: Path = PORTFOLIO) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def collect_ucs() -> list[dict[str, Any]]:
    """Return the sidecar fields the matrix needs, one dict per UC."""
    from splunk_uc.generators.equipment_tags import with_resolved_tags

    out: list[dict[str, Any]] = []
    for _path, sc in iter_uc_sidecars():
        sc = with_resolved_tags(sc)
        out.append(
            {
                "id": f"UC-{sc.get('id', '')}",
                "equipmentModels": list(sc.get("equipmentModels") or []),
                "capabilities": list(sc.get("capabilities") or []),
                "cimModels": list(sc.get("cimModels") or []),
                "hasCimSpl": bool(str(sc.get("cimSpl") or "").strip()),
            }
        )
    return out


def build_matrix(portfolio: dict[str, Any], ucs: list[dict[str, Any]]) -> dict[str, Any]:
    known: set[str] = set()
    for prod in portfolio.get("products", []):
        for cap in prod.get("capabilities", []):
            known.add(f"{prod['slug']}.{cap['id']}")

    by_model: dict[str, list[str]] = {}
    by_cap: dict[str, list[dict[str, Any]]] = {}
    unknown: list[dict[str, str]] = []
    for uc in ucs:
        for model in uc["equipmentModels"]:
            by_model.setdefault(model, []).append(uc["id"])
        for ref in uc["capabilities"]:
            if ref in known:
                by_cap.setdefault(ref, []).append(uc)
            else:
                unknown.append({"useCase": uc["id"], "capability": ref})

    products: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    totals = {
        "products": 0,
        "productsWithUseCases": 0,
        "capabilities": 0,
        "observableCapabilities": 0,
        "coveredCapabilities": 0,
        "cimCapabilities": 0,
        "cimCoveredCapabilities": 0,
    }
    for prod in portfolio.get("products", []):
        slug = prod["slug"]
        tagged = sorted(set(by_model.get(prod["equipmentModel"], [])), key=_uc_sort_key)
        caps_out: list[dict[str, Any]] = []
        for cap in prod.get("capabilities", []):
            ref = f"{slug}.{cap['id']}"
            covering = by_cap.get(ref, [])
            cov_ids = sorted({u["id"] for u in covering}, key=_uc_sort_key)
            want_cim = set(cap.get("cimModels") or [])
            cim_ids = sorted(
                {u["id"] for u in covering if u["hasCimSpl"] and want_cim & set(u["cimModels"])},
                key=_uc_sort_key,
            )
            observable = bool(cap.get("observable"))
            if not observable:
                status = STATUS_NOT_OBSERVABLE
            elif not cov_ids:
                status = STATUS_UNCOVERED
            elif want_cim and not cim_ids:
                status = STATUS_CIM_GAP
            else:
                status = STATUS_COVERED
            totals["capabilities"] += 1
            if observable:
                totals["observableCapabilities"] += 1
                if cov_ids:
                    totals["coveredCapabilities"] += 1
                if want_cim:
                    totals["cimCapabilities"] += 1
                    if cim_ids:
                        totals["cimCoveredCapabilities"] += 1
            entry: dict[str, Any] = {
                "id": cap["id"],
                "ref": ref,
                "name": cap["name"],
                "observable": observable,
                "cimModels": sorted(want_cim),
                "status": status,
                "useCases": cov_ids,
                "cimUseCases": cim_ids,
            }
            if not observable:
                entry["notObservableReason"] = cap.get("notObservableReason", "")
            caps_out.append(entry)
            if status in (STATUS_UNCOVERED, STATUS_CIM_GAP):
                gaps.append(
                    {
                        "tier": prod.get("tier"),
                        "product": slug,
                        "capability": ref,
                        "name": cap["name"],
                        "status": status,
                        "cimModels": sorted(want_cim),
                    }
                )
        totals["products"] += 1
        if tagged:
            totals["productsWithUseCases"] += 1
        products.append(
            {
                "slug": slug,
                "name": prod["name"],
                "family": prod["family"],
                "tier": prod.get("tier"),
                "equipmentModel": prod["equipmentModel"],
                "capabilityMap": prod.get("capabilityMap"),
                "useCaseCount": len(tagged),
                "useCases": tagged,
                "capabilities": caps_out,
                "uncovered": [c["ref"] for c in caps_out if c["status"] == STATUS_UNCOVERED],
            }
        )

    gaps.sort(key=lambda g: (g["tier"] if g["tier"] is not None else 99, g["product"], g["capability"]))
    return {
        "$comment": f"Generated by `{GENERATOR}` from data/cisco-portfolio.json and content/**/UC-*.json. Do not hand-edit.",
        "portfolioVersion": portfolio.get("version"),
        "requestCoverageUrl": portfolio.get("requestCoverageUrl"),
        "summary": totals,
        "products": products,
        "gaps": gaps,
        "unknownCapabilityRefs": sorted(unknown, key=lambda u: (_uc_sort_key(u["useCase"]), u["capability"])),
    }


def render_markdown(matrix: dict[str, Any]) -> str:
    s = matrix["summary"]
    lines = [
        f"<!-- Generated by `{GENERATOR}`; do not hand-edit. -->",
        "",
        "# Cisco portfolio coverage",
        "",
        f"_Generated by `{GENERATOR}`. Do not hand-edit._ Source: `data/cisco-portfolio.json` and the UC sidecars' `capabilities[]` tags.",
        "",
        f"- Products: {s['products']} ({s['productsWithUseCases']} with at least one tagged use case)",
        f"- Observable capabilities covered: {s['coveredCapabilities']} of {s['observableCapabilities']}",
        f"- CIM-backed coverage where a CIM model applies: {s['cimCoveredCapabilities']} of {s['cimCapabilities']}",
        "",
        "## Products",
        "",
        "| Tier | Product | Tagged UCs | Capabilities covered | Capability map |",
        "|---|---|---:|---|---|",
    ]
    for p in sorted(matrix["products"], key=lambda p: (p["tier"] if p["tier"] is not None else 99, p["slug"])):
        obs = [c for c in p["capabilities"] if c["observable"]]
        covered = [c for c in obs if c["useCases"]]
        tier = str(p["tier"]) if p["tier"] is not None else "—"
        cov = f"{len(covered)} / {len(obs)}" if p["capabilities"] else "—"
        lines.append(f"| {tier} | {p['name']} (`{p['slug']}`) | {p['useCaseCount']} | {cov} | {p['capabilityMap']} |")

    lines += ["", "## Capabilities", ""]
    for p in sorted(matrix["products"], key=lambda p: (p["tier"] if p["tier"] is not None else 99, p["slug"])):
        if not p["capabilities"]:
            continue
        lines += [
            f"### {p['name']}",
            "",
            "| Capability | Status | CIM | Use cases |",
            "|---|---|---|---|",
        ]
        for c in p["capabilities"]:
            cim = ", ".join(c["cimModels"]) or "—"
            ucs = ", ".join(c["useCases"]) or "—"
            status = c["status"].replace("_", " ")
            if c["status"] == STATUS_NOT_OBSERVABLE:
                status += f": {c.get('notObservableReason', '')}"
            lines.append(f"| `{c['ref']}` {c['name']} | {status} | {cim} | {ucs} |")
        lines.append("")

    lines += ["## Gap list", "", "Ordered by tier, then product. This is the authoring queue.", ""]
    if matrix["gaps"]:
        lines += ["| Tier | Capability | Gap | CIM |", "|---|---|---|---|"]
        for g in matrix["gaps"]:
            gap = "no use case" if g["status"] == STATUS_UNCOVERED else "no CIM-backed use case"
            lines.append(f"| {g['tier']} | `{g['capability']}` {g['name']} | {gap} | {', '.join(g['cimModels']) or '—'} |")
    else:
        lines.append("No gaps.")
    if matrix["unknownCapabilityRefs"]:
        lines += ["", "## Unknown capability references", ""]
        for u in matrix["unknownCapabilityRefs"]:
            lines.append(f"- {u['useCase']}: `{u['capability']}`")
    return "\n".join(lines) + "\n"


def render(portfolio: dict[str, Any], ucs: list[dict[str, Any]]) -> dict[str, str]:
    matrix = build_matrix(portfolio, ucs)
    return {
        "matrix.json": json.dumps(matrix, indent=2, ensure_ascii=False) + "\n",
        "matrix.md": render_markdown(matrix),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-cisco-coverage",
        description="Write reports/cisco-coverage/ from data/cisco-portfolio.json and UC capabilities[] tags.",
    )
    parser.add_argument("--check", action="store_true", help="Exit 1 if the reports are out of date.")
    args = parser.parse_args(argv)

    outputs = render(load_portfolio(), collect_ucs())
    stale = []
    for name, text in outputs.items():
        path = OUT_DIR / name
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            for p in stale:
                print(f"STALE: {p.relative_to(REPO)} — run `{GENERATOR}`", file=sys.stderr)
            return 1
        print("OK: reports/cisco-coverage is up to date.")
        return 0
    for p in stale:
        print(f"wrote {p.relative_to(REPO)}")
    if not stale:
        print("reports/cisco-coverage already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
