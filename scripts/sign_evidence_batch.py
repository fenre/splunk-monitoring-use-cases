#!/usr/bin/env python3
"""Thin wrapper for local / workflow evidence signing.

Equivalent to::

    PYTHONPATH=src python3 -m splunk_uc generate-evidence-signatures --all

With optional GPG fallback when Sigstore is unavailable::

    python3 scripts/sign_evidence_batch.py --gpg
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    argv = ["python3", "-m", "splunk_uc", "generate-evidence-signatures", "--all", *sys.argv[1:]]
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT / "src"))
    result = subprocess.run(argv, cwd=ROOT, env=env, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    sys.exit(main())
