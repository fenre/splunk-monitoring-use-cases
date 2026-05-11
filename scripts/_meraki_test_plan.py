"""Generate a JSONL test plan for sweeping every Meraki UC against the live
Splunk server.

Each line in the output is a JSON object:
  {
    "uc_id": "5.1.39",
    "title": "...",
    "path": "content/cat-05-network-infrastructure/UC-5.1.39.json",
    "spl_lines": <int>,
    "spl_chars": <int>,
    "spl": "<the raw SPL>",
    "sourcetypes": ["meraki", "meraki:assurancealerts", ...],
  }

Only includes UCs whose SPL actually targets a Meraki sourcetype (so that
we test the right product's data plane on the customer's Splunk).

Usage:
    python3 scripts/_meraki_test_plan.py > /tmp/meraki-test-plan.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _meraki_lint import is_meraki_uc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"

ST_RE = re.compile(r'sourcetype\s*=\s*"?(meraki[:\w-]*)"?', re.IGNORECASE)


def main() -> int:
    rows = []
    for path in sorted(CONTENT_DIR.glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not is_meraki_uc(payload):
            continue
        spl = payload.get("spl", "") or ""
        if not spl:
            continue
        sts = sorted({m.group(1).lower() for m in ST_RE.finditer(spl)})
        if not sts:
            # UC mentions Meraki only in metadata; SPL targets another product.
            continue
        rows.append({
            "uc_id": payload.get("id", ""),
            "title": payload.get("title", ""),
            "path": str(path.relative_to(ROOT)),
            "spl_lines": spl.count("\n") + 1,
            "spl_chars": len(spl),
            "spl": spl,
            "sourcetypes": sts,
        })
    rows.sort(key=lambda r: tuple(int(p) for p in r["uc_id"].split(".")))
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    print(f"\n# {len(rows)} Meraki UCs in test plan", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
