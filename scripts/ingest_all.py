#!/usr/bin/env python3
"""Run every authoritative ingest driver, emitting deterministic outputs.

Invokes, in order:
  1. ingest_oscal.py    — NIST OSCAL catalogues (CSF 2.0, 800-53 rev5 + baselines,
                          800-171 rev3, 800-218 SSDF).
  2. ingest_attack.py   — MITRE ATT&CK Enterprise, ICS, Mobile STIX bundles.
  3. ingest_d3fend.py   — MITRE D3FEND ontology + full ATT&CK mappings.
  4. ingest_atomic.py   — Red Canary Atomic Red Team master index.
  5. ingest_olir.py     — Cross-framework OLIR-style crosswalks via CTID
                          Mappings Explorer (NIST 800-53, CRI Profile, CSA CCM).

Each driver is idempotent thanks to the shared manifest-based cache, so
re-running this orchestrator after a successful pass does no network I/O
unless vendor files have been deleted.

Exit code:
  0 if all drivers succeed, non-zero on the first failure.
"""

from __future__ import annotations

import importlib
import pathlib
import sys
import time

_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[1]
INGEST_DIR = _HERE.parent / "ingest"
if str(INGEST_DIR) not in sys.path:
    sys.path.insert(0, str(INGEST_DIR))

DRIVERS = [
    "ingest_oscal",
    "ingest_attack",
    "ingest_d3fend",
    "ingest_atomic",
    "ingest_olir",
]


def main() -> int:
    overall_rc = 0
    for name in DRIVERS:
        print(f"\n=== {name} ===", flush=True)
        start = time.monotonic()
        module = importlib.import_module(name)
        rc = module.run()
        elapsed = time.monotonic() - start
        print(f"=== {name}: rc={rc} ({elapsed:.1f}s) ===", flush=True)
        if rc != 0 and overall_rc == 0:
            overall_rc = rc
    manifest = _REPO / "data" / "provenance" / "ingest-manifest.json"
    if manifest.exists():
        print(f"\nManifest: {manifest.relative_to(_REPO)}", flush=True)
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
