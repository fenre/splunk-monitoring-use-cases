"""Build the deterministic fabric from sidecar facts.

``--check`` resolves the catalogue, fails when entity counts or edges are
inconsistent, and fails when the app or sourcetype resolution rate drops
below ``data/fabric-resolution-baseline.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from splunk_uc.fabric.graph import full_export, presentation_graph, write_graph_file
from splunk_uc.fabric.publish import write_api, write_facets, write_parquet
from splunk_uc.fabric.resolve import (
    CONTENT,
    REGISTRIES,
    REPO_ROOT,
    Fabric,
    invariant_errors,
    resolve,
)

BASELINE = REPO_ROOT / "data" / "fabric-resolution-baseline.json"
_RATE_KEYS = ("appRate", "sourcetypeRate")


def _baseline_view(rates: dict[str, Any]) -> dict[str, Any]:
    return {key: rates[key] for key in (
        "ucCount",
        "appWithSignal",
        "appResolved",
        "appRate",
        "sourcetypeWithSignal",
        "sourcetypeResolved",
        "sourcetypeRate",
        "definition",
    ) if key in rates}


def _check_baseline(rates: dict[str, Any]) -> list[str]:
    if not BASELINE.is_file():
        return [f"missing {BASELINE.relative_to(REPO_ROOT)}; run build-fabric --write-baseline"]
    committed = json.loads(BASELINE.read_text(encoding="utf-8"))
    errors = []
    for key in _RATE_KEYS:
        live = float(rates[key])
        previous = float(committed[key])
        if live + 1e-9 < previous:
            errors.append(f"{key} dropped from {previous} to {live}")
    return errors


def _write_outputs(fabric: Fabric, out_dir: Path | None, api_root: Path | None, graph_path: Path | None) -> None:
    if out_dir is not None:
        fabric_dir = out_dir / "fabric"
        wrote = write_parquet(fabric, fabric_dir)
        write_facets(fabric, fabric_dir / "facets.json")
        (fabric_dir / "resolution.json").write_text(
            json.dumps(
                {"parquet": wrote, "rates": fabric.rates, "report": fabric.report},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        write_graph_file(full_export(fabric), fabric_dir / "graph-full.json")
        write_graph_file(presentation_graph(fabric), out_dir / "graph-data.json")
    if api_root is not None:
        write_api(fabric, api_root)
        write_facets(fabric, api_root / "facets.json")
    if graph_path is not None:
        write_graph_file(presentation_graph(fabric), graph_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on inconsistent fabric or a lower resolution rate.")
    parser.add_argument("--write-baseline", action="store_true", help="Rewrite data/fabric-resolution-baseline.json.")
    parser.add_argument("--write-graph", action="store_true", help="Rewrite repo-root graph-data.json.")
    parser.add_argument("--out", type=Path, default=None, help="Write dist fabric artefacts under this directory.")
    parser.add_argument("--api", type=Path, default=None, help="Write the fabric JSON API under this directory.")
    parser.add_argument("--content", type=Path, default=CONTENT)
    parser.add_argument("--registries", type=Path, default=REGISTRIES)
    args = parser.parse_args(argv)

    fabric = resolve(content=args.content, registries=args.registries)
    errors = invariant_errors(fabric, args.registries)
    if args.check:
        errors.extend(_check_baseline(fabric.rates))
    if args.write_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            json.dumps(_baseline_view(fabric.rates), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    graph_path = REPO_ROOT / "graph-data.json" if args.write_graph else None
    if args.out or args.api or graph_path:
        _write_outputs(fabric, args.out, args.api, graph_path)
    if errors:
        print("fabric: FAIL", file=sys.stderr)
        for line in errors[:40]:
            print(f"  - {line}", file=sys.stderr)
        if len(errors) > 40:
            print(f"  - … {len(errors) - 40} more", file=sys.stderr)
        return 1
    rates = fabric.rates
    print(
        "fabric: OK "
        f"usecases={rates['ucCount']} entities={len(fabric.entities)} "
        f"edges={len(fabric.relationships)} "
        f"app={rates['appResolved']}/{rates['appWithSignal']} ({rates['appRate']}) "
        f"sourcetype={rates['sourcetypeResolved']}/{rates['sourcetypeWithSignal']} ({rates['sourcetypeRate']})"
    )
    return 0
