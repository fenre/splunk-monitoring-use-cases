#!/usr/bin/env python3
"""
Emit Splunk HEC-style NDJSON (one JSON object per line) from eventgen_data/manifest-top10.json
(or another manifest with the same shape). Each line in each sample_template becomes one event.

Usage:
  python3 scripts/generate_manifest_samples.py --manifest eventgen_data/manifest-top10.json \\
    --output /tmp/catalog-top10-events.ndjson

  # stdout:
  python3 scripts/generate_manifest_samples.py --manifest eventgen_data/manifest-top10.json

Environment variables (optional):
  CATALOG_HEC_HOST — default host field (default: catalog-demo)
  CATALOG_HEC_INDEX — default index in fields (unset unless provided)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_sample_lines(sample_path: Path) -> list[str]:
    text = sample_path.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def hec_event(
    raw_event: str,
    *,
    sourcetype: str,
    uc_id: str,
    catalog_category: int,
    host: str,
    index: str | None,
    base_time: float,
    seq: int,
) -> dict:
    """Build one Splunk HEC JSON object (raw event string for _raw)."""
    t = base_time + seq * 0.01
    ev: dict = {
        "time": t,
        "host": host,
        "source": "catalog:datagen",
        "sourcetype": sourcetype,
        "event": raw_event,
        "fields": {
            "uc_id": uc_id,
            "catalog_category": str(catalog_category),
        },
    }
    if index:
        ev["index"] = index
    return ev


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HEC NDJSON from manifest-top10.json")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=repo_root() / "eventgen_data" / "manifest-top10.json",
        help="Path to manifest JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write NDJSON here (default: stdout)",
    )
    parser.add_argument(
        "--eventgen-dir",
        type=Path,
        default=repo_root() / "eventgen_data",
        help="Base directory for sample_template paths",
    )
    parser.add_argument("--host", default=os.environ.get("CATALOG_HEC_HOST", "catalog-demo"))
    parser.add_argument(
        "--index",
        default=os.environ.get("CATALOG_HEC_INDEX"),
        help="Optional index name stored in fields.index",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    rows = manifest.get("use_cases", [])
    if not rows:
        print("ERROR: manifest has no use_cases", file=sys.stderr)
        return 1

    out_lines: list[str] = []
    base_time = time.time()
    seq = 0

    for row in rows:
        rel = row["sample_template"]
        sample_path = args.eventgen_dir / rel
        if not sample_path.is_file():
            print(f"ERROR: missing sample file: {sample_path}", file=sys.stderr)
            return 1
        uc_id = row["uc_id"]
        st = row["sourcetype"]
        cat = int(row["catalog_category"])
        for line in read_sample_lines(sample_path):
            ev = hec_event(
                line,
                sourcetype=st,
                uc_id=uc_id,
                catalog_category=cat,
                host=args.host,
                index=args.index,
                base_time=base_time,
                seq=seq,
            )
            out_lines.append(json.dumps(ev, ensure_ascii=False))
            seq += 1

    text = "\n".join(out_lines) + ("\n" if out_lines else "")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
