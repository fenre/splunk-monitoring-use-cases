#!/usr/bin/env python3
"""Write graph-data.json from the fabric relationship layer.

The aggregated file is what graph.html renders. Pillars are a presentation
rollup. Use ``python -m splunk_uc build-fabric --out dist`` for the full
node/edge export that includes use cases.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from splunk_uc.fabric.graph import presentation_graph, write_graph_file  # noqa: E402
from splunk_uc.fabric.resolve import resolve  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build graph data from the fabric")
    parser.add_argument("--out", default=".", help="Output directory")
    args = parser.parse_args()
    fabric = resolve()
    graph = presentation_graph(fabric)
    out = Path(args.out) / "graph-data.json"
    write_graph_file(graph, out)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
