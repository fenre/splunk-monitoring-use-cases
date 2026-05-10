"""Run every authoritative ingest driver, emitting deterministic outputs.

P6 (scripts taxonomy, 2026-05-10) relocated this orchestrator from
scripts/ingest_all.py to src/splunk_uc/ingest/run_all.py. parents[3]
resolves: run_all.py -> ingest/ -> splunk_uc/ -> src/ -> repo root.
The legacy ``parents[1]`` chain assumed depth one and is now wrong by
two levels. The legacy shim at scripts/ingest_all.py re-exports
``main`` so existing CI / maintainer notes still work unchanged
during the soak period.

Module name is ``run_all`` rather than ``all`` because ``all`` shadows
the Python built-in.

Invokes, in order:
  1. ingest-oscal    -- NIST OSCAL catalogues (CSF 2.0, 800-53 rev5 +
                        baselines, 800-171 rev3, 800-218 SSDF).
  2. ingest-attack   -- MITRE ATT&CK Enterprise, ICS, Mobile STIX bundles.
  3. ingest-d3fend   -- MITRE D3FEND ontology + full ATT&CK mappings.
  4. ingest-atomic   -- Red Canary Atomic Red Team master index.
  5. ingest-olir     -- Cross-framework OLIR-style crosswalks via CTID
                        Mappings Explorer (NIST 800-53, CRI Profile, CSA
                        CCM).

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
from typing import Protocol


class _IngestDriver(Protocol):
    def run(self) -> int: ...


_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[3]

DRIVERS = [
    "splunk_uc.ingest.oscal",
    "splunk_uc.ingest.attack",
    "splunk_uc.ingest.d3fend",
    "splunk_uc.ingest.atomic",
    "splunk_uc.ingest.olir",
]


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` accepted for the registry contract; the orchestrator takes no flags."""
    del argv
    overall_rc = 0
    for name in DRIVERS:
        short = name.rsplit(".", 1)[-1]
        print(f"\n=== {short} ===", flush=True)
        start = time.monotonic()
        module: _IngestDriver = importlib.import_module(name)
        rc = module.run()
        elapsed = time.monotonic() - start
        print(f"=== {short}: rc={rc} ({elapsed:.1f}s) ===", flush=True)
        if rc != 0 and overall_rc == 0:
            overall_rc = rc
    manifest = _REPO / "data" / "provenance" / "ingest-manifest.json"
    if manifest.exists():
        print(f"\nManifest: {manifest.relative_to(_REPO)}", flush=True)
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
