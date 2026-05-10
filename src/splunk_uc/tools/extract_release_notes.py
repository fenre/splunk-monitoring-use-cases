"""Extract a release-notes body from ``CHANGELOG.md`` for a given version.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/extract_release_notes.py to
src/splunk_uc/tools/extract_release_notes.py. parents[3] resolves:
extract_release_notes.py -> tools/ -> splunk_uc/ -> src/ -> repo
root. The legacy ``os.path.dirname(__file__)/os.pardir`` chain
assumed depth one and is now wrong by two levels. The legacy shim
re-exports ``main`` so any direct CLI invocation still works during
the soak period.

Usage::

    python -m splunk_uc extract-release-notes <version>           # to stdout
    python -m splunk_uc extract-release-notes <version> out.md    # to file

* ``<version>`` must match the ``## [x.y.z]`` heading in CHANGELOG.md
  exactly (without the square brackets).
* If the version heading is not found the script writes a minimal
  fall-back body so the release workflow never fails "empty".
* The extracted section is appended with a boilerplate paragraph that
  lists the three content packs produced by the release workflow; this
  keeps GitHub Release pages self-contained.

Side-effect-free apart from writing the target file when an output path
is provided. Safe to re-run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
CHANGELOG = _REPO_ROOT / "CHANGELOG.md"

BOILERPLATE = """

## Splunk content packs

This release ships three self-contained Splunk apps:

- `TA-splunk-use-cases-{ver}.spl` — Quick-Start saved searches for the Splunk search head.
- `DA-ITSI-monitoring-use-cases-{ver}.spl` — KPI base searches, thresholds and service templates for Splunk ITSI.
- `DA-ESS-monitoring-use-cases-{ver}.spl` — Correlation searches, MITRE mappings and analytic stories for Splunk Enterprise Security.

See `SHA256SUMS.txt` for integrity verification, and the
[Enterprise deployment guide](docs/enterprise-deployment.md) for installation
instructions and upgrade paths.
"""


def extract_section(version: str) -> str | None:
    """Return the markdown body for ``## [version]`` from CHANGELOG.md, or ``None``."""
    try:
        src = CHANGELOG.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    # Match "## [VER] ..." up to the next "## [" header (or EOF).
    pattern = re.compile(
        rf"(^##\s+\[{re.escape(version)}\][^\n]*\n)(?P<body>.+?)(?=^##\s+\[|\Z)",
        re.M | re.S,
    )
    m = pattern.search(src)
    if not m:
        return None
    return m.group("body").rstrip() + "\n"


def build_body(version: str) -> str:
    """Compose the full release-notes body (extracted section + content-pack boilerplate)."""
    section = extract_section(version)
    if section is None:
        section = f"## {version}\n\nRelease notes are documented in [CHANGELOG.md](CHANGELOG.md).\n"
    return section + BOILERPLATE.format(ver=version)


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` is consumed positionally: ``[<version>, [<output>]]``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: extract-release-notes <version> [output]", file=sys.stderr)
        return 2
    version = args[0]
    body = build_body(version)
    if len(args) > 1:
        # Path-confine the output to the workspace via Path.resolve().
        out_path = Path(args[1]).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")
        print(f"wrote {out_path} ({len(body)} chars)")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
