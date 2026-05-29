#!/usr/bin/env python3
"""CODEOWNERS coverage auditor.

Walks ``.github/CODEOWNERS``, cross-references it against the tracked
source tree via ``git ls-files``, and surfaces files that no owner is
responsible for. Also flags orphan rules that match zero tracked files.

The committed snapshot is **not** checked in — reports land under
``dist/audits/`` (gitignored) and are regenerated on demand or in CI.

Threshold-ratchet policy
------------------------

CI starts at ``--threshold 0`` (warn-only). As path-specific ownership
rules land, maintainers ratchet the threshold upward so new modules
cannot ship without an owner.

Exit codes
----------

* ``0`` — coverage meets the threshold (or check passed).
* ``1`` — coverage below ``--threshold``.
* ``2`` — usage / I/O error (``git ls-files`` failure, bad paths).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CODEOWNERS_PATH = REPO_ROOT / ".github" / "CODEOWNERS"
DEFAULT_OUT_DIR = REPO_ROOT / "dist" / "audits"
SCHEMA_VERSION = "1.0"

# Lane prefixes for the human markdown rollup (longest match wins).
LANE_PREFIXES: tuple[str, ...] = (
    "src/splunk_uc/",
    "tools/",
    "apps/web/",
    "mcp/",
    "scripts/",
    "docs/",
    "content/",
    "data/",
    "schemas/",
    "tests/",
    ".github/",
)

DEFAULT_REMEDIATION = "* @your-github-handle"


@dataclass(frozen=True)
class CodeownersRule:
    """One ``pattern owner [owner...]`` line from CODEOWNERS."""

    pattern: str
    owners: tuple[str, ...]
    line_number: int


@dataclass(frozen=True)
class OrphanRule:
    """A CODEOWNERS rule that matches zero tracked files."""

    pattern: str
    owners: tuple[str, ...]
    line_number: int


@dataclass
class CoverageReport:
    """Aggregate coverage statistics for the tracked tree."""

    files_total: int
    files_covered: int
    files_uncovered: list[str]
    by_directory: dict[str, dict[str, int]]
    top_uncovered_directories: list[dict[str, Any]] = field(default_factory=list)


def _posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _compile_glob(glob: str) -> str:
    """Translate a CODEOWNERS/gitignore-style glob fragment to regex."""
    i = 0
    n = len(glob)
    out: list[str] = []
    while i < n:
        ch = glob[i]
        if ch == "*":
            if i + 1 < n and glob[i + 1] == "*":
                if i + 2 < n and glob[i + 2] == "/":
                    out.append("(?:.*/)?")
                    i += 3
                else:
                    out.append(".*")
                    i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        elif ch in ".\\+()|^$[]{}":
            out.append("\\" + ch)
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _path_matches_pattern(relpath: str, pattern: str) -> bool:
    """Return whether ``relpath`` matches a GitHub CODEOWNERS ``pattern``."""
    path = _posix(relpath).lstrip("./")
    pat = pattern.strip()
    if not pat:
        return False

    anchored = pat.startswith("/")
    if anchored:
        pat = pat[1:]

    dir_only = pat.endswith("/")
    if dir_only:
        pat = pat.rstrip("/")

    body = _compile_glob(pat)
    if dir_only:
        body += "(?:/.*)?"

    if anchored:
        regex = f"^{body}$"
        return re.match(regex, path) is not None

    if "/" in pat:
        regex = f"(^|/){body}$"
        return re.search(regex, path) is not None

    # No slash: match basename anywhere in the tree.
    basename = PurePosixPath(path).name
    return re.match(f"^{body}$", basename) is not None or re.match(f"^{body}$", path) is not None


def parse_codeowners(path: Path) -> list[CodeownersRule]:
    """Parse CODEOWNERS ``pattern owner [owner...]`` lines in declaration order."""
    if not path.is_file():
        return []

    rules: list[CodeownersRule] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        pattern, *owners = parts
        rules.append(
            CodeownersRule(
                pattern=pattern,
                owners=tuple(owners),
                line_number=line_no,
            )
        )
    return rules


def enumerate_repo_files(root: Path) -> list[Path]:
    """Return tracked files via ``git ls-files`` (repo-relative POSIX paths)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git executable not found; cannot enumerate tracked files") from exc

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"git ls-files failed (exit {proc.returncode})"
            + (f": {stderr}" if stderr else "")
        )

    if not proc.stdout:
        return []

    rel_paths = [part.decode("utf-8") for part in proc.stdout.split(b"\0") if part]
    return sorted(Path(p) for p in rel_paths)


def _winning_rule(relpath: str, rules: list[CodeownersRule]) -> CodeownersRule | None:
    winner: CodeownersRule | None = None
    for rule in rules:
        if _path_matches_pattern(relpath, rule.pattern):
            winner = rule
    return winner


def _lane_for(path: str) -> str:
    for prefix in LANE_PREFIXES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return prefix
    return "other/"


def _directory_key(path: str) -> str:
    parent = str(PurePosixPath(path).parent)
    return parent if parent != "." else "(root)"


def evaluate_coverage(files: list[Path], rules: list[CodeownersRule]) -> CoverageReport:
    """Compute covered / uncovered files and directory rollups."""
    covered: list[str] = []
    uncovered: list[str] = []
    by_lane: dict[str, dict[str, int]] = {
        prefix: {"total": 0, "covered": 0, "uncovered": 0} for prefix in LANE_PREFIXES
    }
    by_lane["other/"] = {"total": 0, "covered": 0, "uncovered": 0}
    dir_uncovered: dict[str, int] = defaultdict(int)
    dir_total: dict[str, int] = defaultdict(int)

    for file_path in files:
        rel = _posix(file_path)
        lane = _lane_for(rel)
        by_lane[lane]["total"] += 1
        dir_key = _directory_key(rel)
        dir_total[dir_key] += 1

        winner = _winning_rule(rel, rules)
        if winner is not None and winner.owners:
            covered.append(rel)
            by_lane[lane]["covered"] += 1
        else:
            uncovered.append(rel)
            by_lane[lane]["uncovered"] += 1
            dir_uncovered[dir_key] += 1

    top_dirs = [
        {
            "directory": directory,
            "uncovered": dir_uncovered[directory],
            "total": dir_total[directory],
        }
        for directory in sorted(dir_uncovered, key=lambda d: (-dir_uncovered[d], d))
    ]

    return CoverageReport(
        files_total=len(files),
        files_covered=len(covered),
        files_uncovered=sorted(uncovered),
        by_directory=by_lane,
        top_uncovered_directories=top_dirs,
    )


def evaluate_orphan_rules(rules: list[CodeownersRule], files: list[Path]) -> list[OrphanRule]:
    """Return rules that match zero tracked files."""
    rel_paths = [_posix(f) for f in files]
    orphans: list[OrphanRule] = []
    for rule in rules:
        if not any(_path_matches_pattern(rel, rule.pattern) for rel in rel_paths):
            orphans.append(
                OrphanRule(
                    pattern=rule.pattern,
                    owners=rule.owners,
                    line_number=rule.line_number,
                )
            )
    return orphans


def _coverage_percent(report: CoverageReport) -> float:
    if report.files_total == 0:
        return 100.0
    return round(100.0 * report.files_covered / report.files_total, 4)


def _generated_timestamp() -> str:
    return (
        _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def _build_report(
    *,
    rules: list[CodeownersRule],
    coverage: CoverageReport,
    orphans: list[OrphanRule],
    codeowners_exists: bool,
    directory_cap: int,
) -> dict[str, Any]:
    capped_dirs = coverage.top_uncovered_directories[:directory_cap]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": _generated_timestamp(),
        "codeowners_path": _posix(CODEOWNERS_PATH.relative_to(REPO_ROOT)),
        "codeowners_exists": codeowners_exists,
        "coverage_percent": _coverage_percent(coverage),
        "files_total": coverage.files_total,
        "files_covered": coverage.files_covered,
        "files_uncovered_count": len(coverage.files_uncovered),
        "files_uncovered": coverage.files_uncovered,
        "by_directory": coverage.by_directory,
        "top_uncovered_directories": capped_dirs,
        "orphan_rules": [
            {
                "pattern": o.pattern,
                "owners": list(o.owners),
                "line_number": o.line_number,
            }
            for o in orphans
        ],
        "rules_count": len(rules),
    }


def _render_markdown(report: dict[str, Any], *, directory_cap: int) -> str:
    lines: list[str] = []
    lines.append("# CODEOWNERS coverage audit")
    lines.append("")
    lines.append(
        f"_Generated: {report['generated_utc']}_ by "
        "`python -m splunk_uc audit-codeowners-coverage`. Do not hand-edit."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Coverage**: {report['coverage_percent']:.2f}%")
    lines.append(f"- **Tracked files**: {report['files_total']}")
    lines.append(f"- **Covered**: {report['files_covered']}")
    lines.append(f"- **Uncovered**: {report['files_uncovered_count']}")
    lines.append(f"- **CODEOWNERS rules**: {report['rules_count']}")
    lines.append(f"- **Orphan rules**: {len(report['orphan_rules'])}")
    lines.append("")

    if not report["codeowners_exists"]:
        lines.append("## Remediation")
        lines.append("")
        lines.append(
            "`.github/CODEOWNERS` is missing. Add a catch-all rule so every "
            "tracked path has an owner who receives review requests:"
        )
        lines.append("")
        lines.append("```")
        lines.append(DEFAULT_REMEDIATION)
        lines.append("```")
        lines.append("")

    if report["orphan_rules"]:
        lines.append("## Orphan rules")
        lines.append("")
        lines.append("These patterns match zero tracked files (likely stale):")
        lines.append("")
        lines.append("| Line | Pattern | Owners |")
        lines.append("|-----:|---------|--------|")
        for row in report["orphan_rules"]:
            owners = " ".join(row["owners"]) if row["owners"] else "—"
            lines.append(f"| {row['line_number']} | `{row['pattern']}` | {owners} |")
        lines.append("")

    lines.append("## Lane rollups")
    lines.append("")
    lines.append("| Lane | Total | Covered | Uncovered |")
    lines.append("|------|------:|--------:|----------:|")
    for lane in (*LANE_PREFIXES, "other/"):
        stats = report["by_directory"][lane]
        if stats["total"] == 0:
            continue
        lines.append(
            f"| `{lane}` | {stats['total']} | {stats['covered']} | {stats['uncovered']} |"
        )
    lines.append("")

    top_dirs = report["top_uncovered_directories"][:directory_cap]
    lines.append(f"## Top uncovered directories (cap {directory_cap})")
    lines.append("")
    if not top_dirs:
        lines.append("_No uncovered files — every tracked path has an owner._")
    else:
        lines.append("| Directory | Uncovered | Total |")
        lines.append("|-----------|----------:|------:|")
        for row in top_dirs:
            lines.append(
                f"| `{row['directory']}` | {row['uncovered']} | {row['total']} |"
            )
    lines.append("")

    uncovered = report["files_uncovered"]
    if uncovered:
        lines.append("## Sample uncovered files")
        lines.append("")
        sample = uncovered[:25]
        for path in sample:
            lines.append(f"- `{path}`")
        if len(uncovered) > len(sample):
            lines.append(f"- _… and {len(uncovered) - len(sample)} more_")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "See [`docs/codeowners-coverage.md`](../docs/codeowners-coverage.md) "
        "for the threshold-ratchet policy and maintainer workflow."
    )
    return "\n".join(lines) + "\n"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write_reports(out_dir: Path, payload: dict[str, Any], *, directory_cap: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "codeowners-coverage.json"
    md_path = out_dir / "codeowners-coverage.md"
    json_path.write_text(_canonical_json(payload), encoding="utf-8")
    md_path.write_text(_render_markdown(payload, directory_cap=directory_cap), encoding="utf-8")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when coverage is below --threshold.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum coverage percent required (default: 0).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"Output directory for JSON + markdown (default: {DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--directory-cap",
        type=int,
        default=25,
        dest="directory_cap",
        help="Cap top-N uncovered directories in the report (default: 25).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    codeowners_exists = CODEOWNERS_PATH.is_file()
    if not codeowners_exists:
        print(
            f"WARN: {CODEOWNERS_PATH.relative_to(REPO_ROOT)} not found — "
            f"emitting remediation suggestion: {DEFAULT_REMEDIATION}",
            file=sys.stderr,
        )

    rules = parse_codeowners(CODEOWNERS_PATH)

    try:
        files = enumerate_repo_files(REPO_ROOT)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    coverage = evaluate_coverage(files, rules)
    orphans = evaluate_orphan_rules(rules, files)
    payload = _build_report(
        rules=rules,
        coverage=coverage,
        orphans=orphans,
        codeowners_exists=codeowners_exists,
        directory_cap=args.directory_cap,
    )

    out_dir = args.out if args.out is not None else DEFAULT_OUT_DIR
    if args.out is not None or not args.check:
        _write_reports(out_dir, payload, directory_cap=args.directory_cap)
        print(
            f"Wrote {out_dir / 'codeowners-coverage.json'} and "
            f"{out_dir / 'codeowners-coverage.md'}"
        )

    pct = payload["coverage_percent"]
    print(
        f"CODEOWNERS coverage: {pct:.2f}% "
        f"({payload['files_covered']}/{payload['files_total']} files covered, "
        f"{payload['files_uncovered_count']} uncovered, "
        f"{len(payload['orphan_rules'])} orphan rules)"
    )

    if args.check and pct < args.threshold:
        print(
            f"FAIL: coverage {pct:.2f}% is below threshold {args.threshold:.2f}%",
            file=sys.stderr,
        )
        return 1

    if args.check:
        print(f"OK: coverage meets threshold {args.threshold:.2f}%.")

    return 0
