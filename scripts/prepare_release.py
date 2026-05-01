#!/usr/bin/env python3
"""Release preparation — validates or updates version references across all synced files.

Usage:
    python3 scripts/prepare_release.py --check       # CI mode: exit 1 on drift
    python3 scripts/prepare_release.py --version 7.4 # Update all files to 7.4
"""

import argparse
import pathlib
import re
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

VERSION_FILE = PROJECT_ROOT / "VERSION"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
INDEX_HTML = PROJECT_ROOT / "index.html"
CITATION = PROJECT_ROOT / "CITATION.cff"
OPENAPI = PROJECT_ROOT / "openapi.yaml"


def read_version():
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def check_changelog(version):
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(version)}\]"
    if not re.search(pattern, text, re.MULTILINE):
        return f"CHANGELOG.md: missing ## [{version}] header"
    return None


def check_citation(version):
    text = CITATION.read_text(encoding="utf-8")
    if f'version: "{version}"' not in text:
        return f"CITATION.cff: version field does not match {version}"
    return None


def check_openapi(version):
    text = OPENAPI.read_text(encoding="utf-8")
    expected = f'version: "{version}'
    if expected not in text:
        return f"openapi.yaml: info.version does not start with {version}"
    return None


def check_index_html(version):
    text = INDEX_HTML.read_text(encoding="utf-8")
    if (
        f"v{version}" not in text
        and f"Version {version}" not in text
        and f"[{version}]" not in text
    ):
        return f"index.html: no reference to version {version} in release notes"
    return None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check", action="store_true", help="Check mode — exit 1 on drift"
    )
    parser.add_argument("--version", type=str, help="Set all files to this version")
    args = parser.parse_args()

    if args.version:
        VERSION_FILE.write_text(args.version + "\n", encoding="utf-8")
        print(f"VERSION set to {args.version}")
        print(
            "NOTE: CHANGELOG.md, index.html, CITATION.cff, and openapi.yaml must be updated manually."
        )
        return

    version = read_version()
    checks = [
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
            sys.exit(1)
    else:
        print(f"Release check PASSED: all files reference version {version}.")


if __name__ == "__main__":
    main()
