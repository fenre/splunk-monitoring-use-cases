#!/usr/bin/env python3
"""Capture size/timing baselines for the Phase 0 hygiene PR.

Writes ``data/baselines/v<VERSION>.json`` against the current repo state.
The repo-overhaul plan §7 references these numbers as the floor for every
later "X% smaller" or "Y× faster" target — without a baseline file those
targets are unverifiable.

Usage:
    python3 tools/capture_baselines.py
    python3 tools/capture_baselines.py --output data/baselines/custom.json

Captures:
  * Repo-side numbers: file counts, gzipped + raw sizes, content/ tree size.
  * Schema/test footprint: schema count, python+mjs test count.
  * Build pipeline footprint: legacy build.py size, modular build size.
  * Optional timing: `make build` wall-clock if --build is passed.

Anything that requires a browser (Lighthouse) or a live network (link-check)
is recorded as ``null`` here; capture those numbers manually and add them
under the ``timing`` block.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files whose gzipped + raw byte sizes we track. These are the user-facing
# downloads on the GitHub Pages bundle plus the largest committed sources.
# Per ADR-0009 and P1 step 5c, the canonical home for the generated
# artefacts (catalog.json, llms*.txt) is dist/. The legacy project-root
# copies are gone in v8.x; the dist/ copies are the SSOT-derived ones
# we want to track.
#
# Note: the v6/v7-era ``dist/data.js`` artefact is no longer produced
# by the build (`tools/build/build.py` actively evicts any stale copy);
# it was removed from this list in v8.2.0 to avoid recording a
# perpetual ``null`` entry in every captured baseline. The size delta
# is captured for posterity by ``data/baselines/v7.4.2.json`` (≈43 MiB
# raw / ≈3.7 MiB gzipped) versus its absence from ``v8.2.0.json``.
TRACKED_FILES = [
    "index.html",
    "dist/catalog.json",
    "scorecard.html",
    "compliance-story.html",
    "clause-navigator.html",
    "regulatory-primer.html",
    "docs.html",
    "guide-reader.html",
    "graph.html",
    "api-docs.html",
    "dist/llms.txt",
    "dist/llms-full.txt",
    "tools/build/build.py",
    "tools/build/parse_content.py",
    "tools/build/enrichment.py",
]


def _file_sizes(path: Path) -> dict[str, int | None]:
    if not path.exists():
        return {"raw": None, "gzipped": None}
    raw = path.stat().st_size
    with path.open("rb") as fh:
        gzipped = len(gzip.compress(fh.read(), compresslevel=6))
    return {"raw": raw, "gzipped": gzipped}


def _du_kb(path: Path) -> int | None:
    if not path.exists():
        return None
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total // 1024


def _count_files(pattern: str, root: Path = REPO_ROOT) -> int:
    return len(list(root.rglob(pattern)))


def _count_uc_headings() -> int:
    use_cases = REPO_ROOT / "use-cases"
    if not use_cases.exists():
        return 0
    total = 0
    for md in use_cases.glob("cat-*.md"):
        with md.open(encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("### UC-"):
                    total += 1
    return total


def _validate_yml_steps() -> int | None:
    path = REPO_ROOT / ".github" / "workflows" / "validate.yml"
    if not path.exists():
        return None
    count = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.lstrip()
            if stripped.startswith("- name:"):
                count += 1
    return count


def _git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
            timeout=5,
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def _maybe_run_build() -> dict[str, float | str | None]:
    cmd = [sys.executable, "tools/build/build.py", "--out", "dist"]
    started = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except subprocess.SubprocessError as exc:
        return {"wall_seconds": None, "exit_code": None, "error": str(exc)}
    return {
        "wall_seconds": round(time.monotonic() - started, 2),
        "exit_code": result.returncode,
        "stderr_tail": result.stderr.splitlines()[-3:] if result.stderr else [],
    }


def capture(*, run_build: bool, version: str | None) -> dict[str, object]:
    if version is None:
        version_path = REPO_ROOT / "VERSION"
        version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "unknown"

    sizes = {p: _file_sizes(REPO_ROOT / p) for p in TRACKED_FILES}

    counts = {
        "uc_json_sidecars": _count_files("UC-*.json", REPO_ROOT / "content"),
        # ``uc_md_companions`` was deprecated on 2026-05-18 (F21 close).
        # The per-UC ``content/cat-*/UC-*.md`` companions were deleted
        # from git; the LLM markdown twin now lives only in
        # ``dist/uc/UC-X.Y.Z/uc.md``. The counter is retained at 0 for
        # backward-compat with the
        # ``data/baselines/repo-baseline.json`` schema; remove the
        # field in the next baseline-schema bump.
        "uc_md_companions": 0,
        "use_cases_md_headings": _count_uc_headings(),
        "scripts_total": len([
            p for p in (REPO_ROOT / "scripts").iterdir() if p.is_file() or p.is_dir()
        ]) if (REPO_ROOT / "scripts").exists() else 0,
        "categories": _count_files("_category.json", REPO_ROOT / "content"),
        "schemas": _count_files("*.schema.json", REPO_ROOT / "schemas"),
        "tests_python": _count_files("test_*.py", REPO_ROOT / "tests")
                       + _count_files("*_test.py", REPO_ROOT / "tests"),
        "tests_mjs": _count_files("*.test.mjs", REPO_ROOT / "tests"),
        "workflows": _count_files("*.yml", REPO_ROOT / ".github" / "workflows"),
        "validate_yml_steps": _validate_yml_steps(),
        "samples_dirs": len([p for p in (REPO_ROOT / "samples").iterdir() if p.is_dir()])
                       if (REPO_ROOT / "samples").exists() else 0,
        "sample_data_files": _count_files("*.json", REPO_ROOT / "sample-data"),
    }

    tree_sizes_kb = {
        "content": _du_kb(REPO_ROOT / "content"),
        "use-cases": _du_kb(REPO_ROOT / "use-cases"),
        "data": _du_kb(REPO_ROOT / "data"),
        "schemas": _du_kb(REPO_ROOT / "schemas"),
        "splunk-apps": _du_kb(REPO_ROOT / "splunk-apps"),
    }

    timing: dict[str, object] = {
        "make_build_wall_seconds": None,
        "validate_yml_wall_seconds": None,
        "lighthouse_index_html": None,
        "lighthouse_scorecard_html": None,
        "mcp_search_p50_ms": None,
        "mcp_search_p99_ms": None,
    }
    if run_build:
        timing["make_build"] = _maybe_run_build()

    return {
        "$schema": "../../schemas/baselines.schema.json",
        "version": version,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git_head(),
        "tracked_file_sizes_bytes": sizes,
        "counts": counts,
        "tree_sizes_kb": tree_sizes_kb,
        "timing": timing,
        "notes": (
            "Lighthouse + MCP latency numbers are captured manually; see "
            "docs/baselines-howto.md once Phase 16 lands. Anything left as "
            "null here means 'not measured at this revision'."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path. Defaults to data/baselines/v<VERSION>.json.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Also run `tools/build/build.py --out dist` and record wall-clock.",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Override version label (defaults to VERSION file).",
    )
    args = parser.parse_args(argv)

    snapshot = capture(run_build=args.build, version=args.version)

    if args.output is None:
        baseline_dir = REPO_ROOT / "data" / "baselines"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        args.output = baseline_dir / f"v{snapshot['version']}.json"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote baseline to {args.output.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
