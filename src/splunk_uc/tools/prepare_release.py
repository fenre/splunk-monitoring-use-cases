"""Release preparation -- validate or update version references across synced files.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/prepare_release.py to src/splunk_uc/tools/prepare_release.py.
parents[3] resolves: prepare_release.py -> tools/ -> splunk_uc/ ->
src/ -> repo root. The legacy ``parent.parent`` chain assumed depth
one and is now wrong by two levels. The legacy shim re-exports
``main`` so any direct CLI invocation still works during the soak
period.

Usage::

    python -m splunk_uc prepare-release --check          # CI mode: exit 1 on drift
    python -m splunk_uc prepare-release --version 7.4    # Update VERSION to 7.4
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]

VERSION_FILE = PROJECT_ROOT / "VERSION"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
INDEX_HTML = PROJECT_ROOT / "index.html"
CITATION = PROJECT_ROOT / "CITATION.cff"
OPENAPI = PROJECT_ROOT / "openapi.yaml"


def read_version() -> str:
    """Return the trimmed contents of the ``VERSION`` file."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def check_changelog(version: str) -> str | None:
    """Return an error message if the changelog header for ``version`` is missing."""
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(version)}\]"
    if not re.search(pattern, text, re.MULTILINE):
        return f"CHANGELOG.md: missing ## [{version}] header"
    return None


def check_citation(version: str) -> str | None:
    """Return an error message if ``CITATION.cff`` does not pin ``version``."""
    text = CITATION.read_text(encoding="utf-8")
    if f'version: "{version}"' not in text:
        return f"CITATION.cff: version field does not match {version}"
    return None


def check_openapi(version: str) -> str | None:
    """Return an error message if ``openapi.yaml`` ``info.version`` does not start with ``version``."""
    text = OPENAPI.read_text(encoding="utf-8")
    expected = f'version: "{version}'
    if expected not in text:
        return f"openapi.yaml: info.version does not start with {version}"
    return None


def check_index_html(version: str) -> str | None:
    """Return an error message if ``index.html`` carries no recognisable ``version`` marker."""
    text = INDEX_HTML.read_text(encoding="utf-8")
    if (
        f"v{version}" not in text
        and f"Version {version}" not in text
        and f"[{version}]" not in text
    ):
        return f"index.html: no reference to version {version} in release notes"
    return None


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` is consumed via argparse."""
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0] if __doc__ else None,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check", action="store_true", help="Check mode — exit 1 on drift")
    parser.add_argument("--version", type=str, help="Set all files to this version")
    args = parser.parse_args(argv)

    if args.version:
        VERSION_FILE.write_text(args.version + "\n", encoding="utf-8")
        print(f"VERSION set to {args.version}")
        print(
            "NOTE: CHANGELOG.md, index.html, CITATION.cff, and openapi.yaml must be updated manually."
        )
        return 0

    version = read_version()
    checks: list[str | None] = [
        check_changelog(version),
        check_citation(version),
        check_openapi(version),
        check_index_html(version),
    ]

    errors = [c for c in checks if c is not None]

    if errors:
        print(f"Release check FAILED for version {version}:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        if args.check:
            return 1
    else:
        print(f"Release check PASSED: all files reference version {version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
