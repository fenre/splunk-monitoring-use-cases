"""Findings-ledger primitives shared by every review tier.

A ledger record is one JSON object per UC per tier, validated against
``schemas/v2/uc-review-finding.schema.json``. Records are keyed on
``uc_id + content_sha256 + rubric_version`` so a rerun skips UCs whose
content has not changed since they were last reviewed.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
SCHEMA_PATH = REPO_ROOT / "schemas" / "v2" / "uc-review-finding.schema.json"
REVIEW_ROOT = REPO_ROOT / "reports" / "uc-review"
DETERMINISTIC_LEDGER = REVIEW_ROOT / "deterministic.jsonl"

SCHEMA_VERSION = "1.0"
RUBRIC_VERSION = "1.0"

MODEL_TIERS = ("triage", "deep", "adjudication")
TIERS = ("deterministic", *MODEL_TIERS)
SEVERITIES = ("blocker", "major", "minor", "needs_verification")
DIMENSIONS = (
    "clarity",
    "specificity",
    "consistency",
    "correctness",
    "grandma_fidelity",
    "overclaiming",
    "spelling",
)
SCORE_DIMENSIONS = DIMENSIONS[:-1]
FIREWALLED_FIELDS = (
    "spl",
    "cimSpl",
    "compliance",
    "monitoringType",
    "splunkPillar",
    "criticality",
    "difficulty",
    "title",
    "id",
    "mitreAttack",
)


def uc_id_of(uc: dict[str, Any]) -> str:
    raw = str(uc.get("id", "")).strip()
    return raw if raw.startswith("UC-") else f"UC-{raw}"


def content_sha256(uc: dict[str, Any]) -> str:
    """Stable hash of the sidecar content (key order and whitespace independent)."""
    canonical = json.dumps(uc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def category_of(path: Path) -> str:
    try:
        return path.resolve().relative_to(CONTENT_DIR.resolve()).parts[0]
    except ValueError:
        return path.parent.name


def rel_file(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def iter_sidecars(
    *,
    files: list[str] | None = None,
    category: str | None = None,
    content_dir: Path | None = None,
) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Yield ``(path, payload)`` for the selected UC sidecars, sorted by path."""
    root = content_dir or CONTENT_DIR
    if files:
        paths = []
        for raw in files:
            path = Path(raw)
            if not path.is_absolute():
                path = REPO_ROOT / path
            paths.append(path)
    else:
        pattern = f"{category}*/UC-*.json" if category else "cat-*/UC-*.json"
        paths = list(root.glob(pattern))
    for path in sorted(paths):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(payload, dict):
            yield path, payload


def record_path(tier: str, category: str, uc_id: str, *, root: Path | None = None) -> Path:
    """Per-UC ledger path for a model tier: ``reports/uc-review/<tier>/<cat>/UC-X.Y.Z.json``."""
    return (root or REVIEW_ROOT) / tier / category / f"{uc_id}.json"


def new_record(
    *,
    uc: dict[str, Any],
    path: Path,
    tier: str,
    model: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "uc_id": uc_id_of(uc),
        "file": rel_file(path),
        "content_sha256": content_sha256(uc),
        "tier": tier,
        "model": model,
        "rubric_version": RUBRIC_VERSION,
        "findings": [],
        "firewalled_field_flags": [],
    }


def apply_evidence_rule(record: dict[str, Any]) -> dict[str, Any]:
    """Downgrade correctness blockers that cite no evidence to ``needs_verification``."""
    out = copy.deepcopy(record)
    for finding in out.get("findings", []):
        if (
            finding.get("dimension") == "correctness"
            and finding.get("severity") == "blocker"
            and not finding.get("evidence_url")
            and not finding.get("evidence_ref")
        ):
            finding["severity"] = "needs_verification"
    for flag in out.get("firewalled_field_flags", []):
        if (
            flag.get("severity") == "blocker"
            and not flag.get("evidence_url")
            and not flag.get("evidence_ref")
        ):
            flag["severity"] = "needs_verification"
    return out


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_record(record: dict[str, Any]) -> list[str]:
    """Return schema-validation error messages (empty when valid)."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "jsonschema is required for review-record validation: pip install 'splunk-uc[audits]'"
        ) from exc
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path))
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in errors
    ]


def dump_record(record: dict[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_record(record), encoding="utf-8")


def load_record(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def is_current(record: dict[str, Any] | None, *, sha: str) -> bool:
    """True when ``record`` already covers this exact content under the live rubric."""
    return bool(
        record
        and record.get("content_sha256") == sha
        and record.get("rubric_version") == RUBRIC_VERSION
    )


def iter_tier_records(tier: str, *, root: Path | None = None) -> Iterator[dict[str, Any]]:
    """Yield every stored record for one tier (JSONL for deterministic, per-UC JSON otherwise)."""
    base = root or REVIEW_ROOT
    if tier == "deterministic":
        ledger = base / "deterministic.jsonl"
        if not ledger.is_file():
            return
        with ledger.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
        return
    for path in sorted((base / tier).glob("cat-*/UC-*.json")):
        record = load_record(path)
        if record is not None:
            yield record
