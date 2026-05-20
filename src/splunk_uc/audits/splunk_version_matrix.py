#!/usr/bin/env python3
"""Audit the 2-D Splunk-version compatibility matrix.

The catalogue's ``splunkVersions`` sidecar field is a free-form
``array of strings`` per :file:`schemas/uc.schema.json`. In practice
authors converge on a small canonical vocabulary
(:file:`data/splunk-version-vocabulary.json`), but nothing in the
schema prevents a typo (``"9.2"`` instead of ``"9.2+"``) or a stale
token (``"7.x"``) from slipping in.

This audit closes both gaps:

1. **Vocabulary validation.** Every value of every ``splunkVersions``
   array must be one of the canonical IDs declared in
   :file:`data/splunk-version-vocabulary.json`. Unknown tokens fail the
   audit under ``--check`` (CI gate).
2. **2-D coverage rollup.** For each canonical token, count the UCs
   that declare it; for each UC that declares at least one token,
   classify it on the (cloud / on-prem) x (8.x / 9.x / 10.x / cloud)
   matrix. Emit the rollup as JSON for the build pipeline and as
   markdown for human readers.

The 2-D shape that the rollup builds is:

* **rows** \u2014 catalogue category (1\u201323),
* **columns** \u2014 canonical version token (``Cloud``, ``9.2+``, ...).

Coverage is intentionally *not* required to be 100% at this stage.
Most sidecars do not declare ``splunkVersions`` (\u224839% as of v9.1.0)
and that's fine; the audit measures coverage so trends are visible in
the stewardship digest, but it does not block CI on absent fields.

Usage::

    python -m splunk_uc audit-splunk-version-matrix          # human report
    python -m splunk_uc audit-splunk-version-matrix --check  # CI gate
    python -m splunk_uc audit-splunk-version-matrix --json   # machine output

Outputs (relative to repo root, always re-emitted in both modes):

* ``data/splunk-version-matrix.json`` \u2014 SSOT JSON snapshot.
* ``docs/splunk-version-matrix.md``  \u2014 rendered markdown report.

Exit codes:

* 0 \u2014 vocabulary clean.
* 1 \u2014 unknown token(s) detected (``--check`` mode).
* 2 \u2014 unexpected error (missing vocabulary file, malformed sidecar).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
VOCAB_PATH = REPO_ROOT / "data" / "splunk-version-vocabulary.json"
CONTENT_DIR = REPO_ROOT / "content"
MATRIX_JSON_PATH = REPO_ROOT / "data" / "splunk-version-matrix.json"
MATRIX_MD_PATH = REPO_ROOT / "docs" / "splunk-version-matrix.md"


# ----------------------------------------------------------------------
# Vocabulary loader
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class VocabToken:
    """One canonical entry from ``data/splunk-version-vocabulary.json``."""

    id: str
    kind: str  # "cloud" | "on-prem"
    track: str  # "cloud" | "8.x" | "9.x" | "10.x"
    support_phase: str  # "ga" | "supported" | "deprecated"
    description: str


def load_vocabulary(path: Path | None = None) -> dict[str, VocabToken]:
    """Load the canonical token map keyed by ``id``.

    *path* defaults to the module-level :data:`VOCAB_PATH`, but the
    lookup happens at **call time** \u2014 not function-definition time \u2014
    so monkeypatching :data:`VOCAB_PATH` in tests works as expected.

    Raises
    ------
    FileNotFoundError
        The vocabulary file is missing.
    ValueError
        The vocabulary file is malformed (missing top-level ``tokens``,
        duplicate IDs, or a token missing a required field).
    """
    if path is None:
        path = VOCAB_PATH
    if not path.exists():
        raise FileNotFoundError(f"splunk-version vocabulary not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must be a JSON object")
    tokens_raw = raw.get("tokens")
    if not isinstance(tokens_raw, list):
        raise ValueError(f"{path}: 'tokens' must be a JSON array")
    out: dict[str, VocabToken] = {}
    for i, entry in enumerate(tokens_raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: tokens[{i}] is not an object")
        required = ("id", "kind", "track", "support_phase", "description")
        for field_name in required:
            if field_name not in entry:
                raise ValueError(
                    f"{path}: tokens[{i}] is missing required field {field_name!r}"
                )
            if not isinstance(entry[field_name], str):
                raise ValueError(
                    f"{path}: tokens[{i}][{field_name!r}] must be a string"
                )
        tok = VocabToken(
            id=entry["id"],
            kind=entry["kind"],
            track=entry["track"],
            support_phase=entry["support_phase"],
            description=entry["description"],
        )
        if tok.id in out:
            raise ValueError(f"{path}: duplicate token id {tok.id!r}")
        out[tok.id] = tok
    return out


# ----------------------------------------------------------------------
# Sidecar walk
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class SidecarVersionEntry:
    """One UC's contribution to the matrix."""

    uc_id: str  # e.g. "1.1.1"
    category: int
    versions: tuple[str, ...]  # the verbatim declared tokens


def _iter_sidecars(content_dir: Path | None = None) -> Iterable[Path]:
    """Yield every committed UC sidecar path, sorted for determinism.

    *content_dir* defaults to the module-level :data:`CONTENT_DIR`,
    resolved at call time so tests can monkeypatch the constant.
    """
    if content_dir is None:
        content_dir = CONTENT_DIR
    return sorted(content_dir.glob("cat-*/UC-*.json"))


def _parse_uc_id(uc_id_or_path: str | Path, source: Path) -> tuple[str, int]:
    """Validate that *uc_id_or_path*'s id is ``X.Y.Z`` and pull category int.

    Returns ``(uc_id, category)``. Raises ``ValueError`` on a bad shape.
    """
    if isinstance(uc_id_or_path, Path):
        raise TypeError("pass the id string, not the path")
    parts = uc_id_or_path.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{source}: invalid UC id {uc_id_or_path!r}")
    return uc_id_or_path, int(parts[0])


def collect_entries(
    content_dir: Path | None = None,
) -> tuple[list[SidecarVersionEntry], list[str]]:
    """Walk every UC sidecar and pull the ``splunkVersions`` field.

    Returns
    -------
    entries
        One entry per UC that declares a non-empty ``splunkVersions``
        array.
    parse_errors
        Sidecars that could not be parsed at all (malformed JSON,
        missing ``id``). These are not unknown-token errors \u2014 they
        are corruption errors that should be flagged separately.
    """
    if content_dir is None:
        content_dir = CONTENT_DIR
    entries: list[SidecarVersionEntry] = []
    parse_errors: list[str] = []
    for path in _iter_sidecars(content_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            parse_errors.append(f"{path}: malformed JSON: {exc}")
            continue
        if not isinstance(data, dict):
            parse_errors.append(f"{path}: top-level is not an object")
            continue
        uc_id_raw = data.get("id")
        if not isinstance(uc_id_raw, str):
            parse_errors.append(f"{path}: missing or non-string 'id'")
            continue
        try:
            uc_id, category = _parse_uc_id(uc_id_raw, path)
        except ValueError as exc:
            parse_errors.append(str(exc))
            continue
        versions = data.get("splunkVersions")
        if versions is None:
            continue
        if not isinstance(versions, list):
            parse_errors.append(
                f"{path}: 'splunkVersions' must be an array; got "
                f"{type(versions).__name__}"
            )
            continue
        if not versions:
            continue
        valid_versions: list[str] = []
        for v in versions:
            if not isinstance(v, str):
                parse_errors.append(
                    f"{path}: 'splunkVersions' element is not a string: {v!r}"
                )
                continue
            valid_versions.append(v)
        if valid_versions:
            entries.append(
                SidecarVersionEntry(
                    uc_id=uc_id,
                    category=category,
                    versions=tuple(valid_versions),
                )
            )
    return entries, parse_errors


# ----------------------------------------------------------------------
# Matrix construction
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class UnknownTokenFinding:
    """A UC declared a ``splunkVersions`` value not in the vocabulary."""

    uc_id: str
    token: str
    similar: tuple[str, ...]  # closest canonical IDs by edit distance


@dataclass
class Matrix:
    """Aggregate result of one audit run."""

    total_sidecars: int
    sidecars_with_versions: int
    per_token_counts: dict[str, int] = field(default_factory=dict)
    per_track_counts: dict[str, int] = field(default_factory=dict)
    per_kind_counts: dict[str, int] = field(default_factory=dict)
    per_category: dict[int, dict[str, int]] = field(default_factory=dict)
    unknown_findings: list[UnknownTokenFinding] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


def _closest(token: str, vocab_ids: Iterable[str]) -> tuple[str, ...]:
    """Return up to 3 vocab IDs closest to *token* by edit distance.

    Uses :func:`difflib.get_close_matches`; falls back to an empty
    tuple if no suggestion clears the default 0.6 ratio.
    """
    from difflib import get_close_matches

    return tuple(get_close_matches(token, list(vocab_ids), n=3, cutoff=0.6))


def build_matrix(
    entries: list[SidecarVersionEntry],
    parse_errors: list[str],
    vocab: Mapping[str, VocabToken],
    total_sidecars: int,
) -> Matrix:
    """Roll ``entries`` up into a :class:`Matrix`.

    Unknown tokens land in :attr:`Matrix.unknown_findings` and are
    *also* counted under :attr:`Matrix.per_token_counts` under a
    synthetic ``"<unknown:X>"`` key so the rollup totals always add
    back to the same UC counts.
    """
    matrix = Matrix(
        total_sidecars=total_sidecars,
        sidecars_with_versions=len(entries),
        parse_errors=list(parse_errors),
    )
    vocab_ids = set(vocab.keys())
    for entry in entries:
        per_cat = matrix.per_category.setdefault(entry.category, {})
        for tok in entry.versions:
            matrix.per_token_counts[tok] = matrix.per_token_counts.get(tok, 0) + 1
            per_cat[tok] = per_cat.get(tok, 0) + 1
            if tok in vocab_ids:
                v = vocab[tok]
                matrix.per_kind_counts[v.kind] = matrix.per_kind_counts.get(v.kind, 0) + 1
                matrix.per_track_counts[v.track] = (
                    matrix.per_track_counts.get(v.track, 0) + 1
                )
            else:
                matrix.unknown_findings.append(
                    UnknownTokenFinding(
                        uc_id=entry.uc_id,
                        token=tok,
                        similar=_closest(tok, vocab_ids),
                    )
                )
    return matrix


# ----------------------------------------------------------------------
# Serialization
# ----------------------------------------------------------------------


def _matrix_to_json(matrix: Matrix, vocab: Mapping[str, VocabToken]) -> dict[str, Any]:
    """Render the matrix as the on-disk JSON shape."""
    vocab_tokens = sorted(vocab.keys())
    try:
        vocab_path_str = str(VOCAB_PATH.relative_to(REPO_ROOT))
    except ValueError:
        # In tests, VOCAB_PATH may be monkeypatched to a tmp dir
        # outside the repo. Fall back to the full path string.
        vocab_path_str = str(VOCAB_PATH)
    return {
        "$schema_version": "1.0",
        "vocabulary_path": vocab_path_str,
        "total_sidecars": matrix.total_sidecars,
        "sidecars_with_versions": matrix.sidecars_with_versions,
        "coverage_percent": (
            round(100 * matrix.sidecars_with_versions / matrix.total_sidecars, 2)
            if matrix.total_sidecars
            else 0.0
        ),
        "per_token_counts": {
            tok: matrix.per_token_counts.get(tok, 0) for tok in vocab_tokens
        },
        "unknown_token_counts": {
            tok: count
            for tok, count in sorted(matrix.per_token_counts.items())
            if tok not in vocab
        },
        "per_track_counts": dict(sorted(matrix.per_track_counts.items())),
        "per_kind_counts": dict(sorted(matrix.per_kind_counts.items())),
        "per_category": {
            str(cat): dict(sorted(buckets.items()))
            for cat, buckets in sorted(matrix.per_category.items())
        },
        "unknown_findings": [
            {
                "uc_id": f.uc_id,
                "token": f.token,
                "did_you_mean": list(f.similar),
            }
            for f in sorted(matrix.unknown_findings, key=lambda f: (f.uc_id, f.token))
        ],
        "parse_errors": list(matrix.parse_errors),
    }


def _render_markdown(matrix: Matrix, vocab: Mapping[str, VocabToken]) -> str:
    """Render the matrix as a markdown report for ``docs/``."""
    lines: list[str] = [
        "# Splunk version compatibility matrix",
        "",
        (
            "Auto-generated by "
            "`python3 -m splunk_uc audit-splunk-version-matrix`. "
            "Do not edit by hand."
        ),
        "",
        "## Summary",
        "",
        f"- Total UC sidecars: **{matrix.total_sidecars:,}**",
        (
            f"- Sidecars declaring `splunkVersions`: "
            f"**{matrix.sidecars_with_versions:,}** "
            f"({100 * matrix.sidecars_with_versions / max(matrix.total_sidecars, 1):.1f}%)"
        ),
        f"- Unknown-token findings: **{len(matrix.unknown_findings)}**",
        f"- Parse errors: **{len(matrix.parse_errors)}**",
        "",
        "## Canonical vocabulary",
        "",
        "| ID | Kind | Track | Phase | Description |",
        "| -- | ---- | ----- | ----- | ----------- |",
    ]
    for tok in sorted(vocab.values(), key=lambda t: (t.track, t.id)):
        lines.append(
            f"| `{tok.id}` | {tok.kind} | {tok.track} | {tok.support_phase} "
            f"| {tok.description} |"
        )

    lines.extend(
        [
            "",
            "## Coverage by token",
            "",
            "| Token | UCs declaring it |",
            "| ----- | ---------------- |",
        ]
    )
    for tok_id in sorted(vocab.keys()):
        lines.append(f"| `{tok_id}` | {matrix.per_token_counts.get(tok_id, 0):,} |")

    if matrix.per_track_counts:
        lines.extend(
            [
                "",
                "## Coverage by track",
                "",
                "| Track | UCs |",
                "| ----- | --- |",
            ]
        )
        for track, count in sorted(matrix.per_track_counts.items()):
            lines.append(f"| `{track}` | {count:,} |")

    if matrix.per_category:
        # Build the dense 2-D table: rows = category, cols = vocab tokens.
        token_ids = sorted(vocab.keys())
        header = " | ".join(["Category", *(f"`{t}`" for t in token_ids)])
        sep = " | ".join(["---"] * (len(token_ids) + 1))
        lines.extend(["", "## Per-category 2-D matrix", "", f"| {header} |", f"| {sep} |"])
        for cat in sorted(matrix.per_category):
            row = [f"{cat}"]
            for tok_id in token_ids:
                count = matrix.per_category[cat].get(tok_id, 0)
                row.append(str(count) if count else "\u2013")
            lines.append("| " + " | ".join(row) + " |")

    if matrix.unknown_findings:
        lines.extend(
            [
                "",
                "## Unknown-token findings",
                "",
                "| UC | Unknown token | Did you mean? |",
                "| -- | ------------- | ------------- |",
            ]
        )
        for f in sorted(matrix.unknown_findings, key=lambda f: (f.uc_id, f.token)):
            sug = ", ".join(f"`{s}`" for s in f.similar) or "\u2014"
            lines.append(f"| `UC-{f.uc_id}` | `{f.token}` | {sug} |")

    if matrix.parse_errors:
        lines.extend(["", "## Parse errors", ""])
        for err in matrix.parse_errors[:50]:
            lines.append(f"- {err}")
        if len(matrix.parse_errors) > 50:
            lines.append(f"- \u2026 and {len(matrix.parse_errors) - 50} more")

    lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _argv_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit-splunk-version-matrix",
        description="Audit the 2-D Splunk-version compatibility matrix.",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit non-zero if any unknown-token finding exists.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit the matrix JSON to stdout instead of the markdown report.",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help=(
            "Always (re-)write data/splunk-version-matrix.json and "
            "docs/splunk-version-matrix.md. On by default unless --check is set."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = _argv_parser()
    args = parser.parse_args(argv)

    try:
        vocab = load_vocabulary()
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    entries, parse_errors = collect_entries()
    total = sum(1 for _ in _iter_sidecars())
    matrix = build_matrix(entries, parse_errors, vocab, total)

    rendered_json = _matrix_to_json(matrix, vocab)
    rendered_md = _render_markdown(matrix, vocab)

    if args.json:
        print(json.dumps(rendered_json, indent=2, sort_keys=True))
    else:
        print(rendered_md)

    write_outputs = args.write or not args.check
    if write_outputs:
        MATRIX_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        MATRIX_JSON_PATH.write_text(
            json.dumps(rendered_json, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        MATRIX_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        MATRIX_MD_PATH.write_text(rendered_md, encoding="utf-8")

    if matrix.parse_errors:
        print(
            f"WARNING: {len(matrix.parse_errors)} sidecar(s) failed to parse "
            f"(see docs/splunk-version-matrix.md).",
            file=sys.stderr,
        )

    if args.check and matrix.unknown_findings:
        unknown_tokens = sorted({f.token for f in matrix.unknown_findings})
        sample = Counter(f.token for f in matrix.unknown_findings).most_common(5)
        print(
            f"ERROR: {len(matrix.unknown_findings)} unknown-token "
            f"finding(s) across {len(unknown_tokens)} distinct token(s). "
            f"Top: {sample}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - dispatcher-driven
    raise SystemExit(main())
