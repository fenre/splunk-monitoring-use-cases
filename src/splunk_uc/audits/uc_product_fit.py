#!/usr/bin/env python3
"""Find use cases whose SPL does not implement them on the Splunk platform.

ADR-0017 Phase 2. A use case is a *candidate* when any of these hold:

* ``makeresults-only`` — the SPL starts from ``| makeresults`` and never
  reads indexed data, a lookup file, REST, or a data model, so it can only
  return the rows it hard-codes (checklists, static tables).
* ``undocumented-sourcetype`` / ``undocumented-index`` — the SPL reads a
  sourcetype or index that ``data/product-fit-rules.json`` attributes to
  another Splunk product, but that product's documentation does not name it
  as a default ingest path into the Splunk platform.
* ``configures-product`` — the SPL reads another product's data and the
  implementation prose configures that product (product name and one of its
  registry ``artifactTypes`` in the same sentence), so the SPL may only
  report on a mirror of where the work is really done. Skipped for products
  whose registry row applies SPL audits, because their work is SPL.

Candidates are reviewed into ``data/product-fit-review.json``. The audit is
warn-only until the migration finishes: ``--check`` fails on a malformed
rules or review file, and ``--strict`` also fails on unreviewed candidates.

Usage::

    python -m splunk_uc audit-uc-product-fit             # summary + report
    python -m splunk_uc audit-uc-product-fit --check     # CI (warn-only)
    python -m splunk_uc audit-uc-product-fit --strict    # fail on unreviewed
    python -m splunk_uc audit-uc-product-fit --json      # report to stdout
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import jsonschema

from splunk_uc import products
from splunk_uc.audits import _spl_parse as parse

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_ROOT = REPO_ROOT / "content"
RULES_PATH = REPO_ROOT / "data" / "product-fit-rules.json"
REVIEW_PATH = REPO_ROOT / "data" / "product-fit-review.json"
RULES_SCHEMA_PATH = REPO_ROOT / "schemas" / "product-fit-rules.schema.json"
REVIEW_SCHEMA_PATH = REPO_ROOT / "schemas" / "product-fit-review.schema.json"
DEFAULT_OUT = REPO_ROOT / "dist" / "audits" / "product-fit-candidates.json"

_SPL_FIELDS = ("spl", "cimSpl")
_PROSE_FIELDS = ("implementation", "detailedImplementation")

# Commands that read data the search did not construct itself.
_DATA_COMMANDS = frozenset(
    {
        "datamodel",
        "dbinspect",
        "dbxquery",
        "eventcount",
        "from",
        "inputcsv",
        "inputlookup",
        "loadjob",
        "mcatalog",
        "metadata",
        "metasearch",
        "mpreview",
        "mstats",
        "multisearch",
        "pivot",
        "rest",
        "savedsearch",
        "search",
        "tstats",
        "union",
    }
)
_IMPLICIT_SEARCH_RE = re.compile(
    r"\b(index|sourcetype|source|eventtype|tag)\s*(=|\bIN\s*\()", re.IGNORECASE
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;!?])\s+|\n+")


@dataclass(frozen=True)
class Reason:
    kind: str
    product: str | None
    detail: str


@dataclass(frozen=True)
class Candidate:
    id: str
    title: str
    products: list[str]
    reasons: list[Reason]


def _load_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def iter_ucs(content_root: Path) -> Iterator[dict[str, Any]]:
    for path in sorted(content_root.glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("id"):
            yield payload


def validate_rules(rules: Mapping[str, Any]) -> list[str]:
    issues = [
        f"product-fit-rules: {err.message} (at /{'/'.join(map(str, err.absolute_path))})"
        for err in jsonschema.Draft202012Validator(_load_json(RULES_SCHEMA_PATH)).iter_errors(
            rules
        )
    ]
    known = set(products.product_ids())
    for pid, rule in rules.get("products", {}).items():
        if pid not in known:
            issues.append(f"product-fit-rules: unknown product {pid!r}")
        if pid == products.default_product_id():
            issues.append(f"product-fit-rules: {pid!r} is the default product and needs no rule")
        for marker in rule.get("dataMarkers", []):
            try:
                re.compile(marker)
            except re.error as exc:
                issues.append(f"product-fit-rules: {pid} marker {marker!r} is not a regex ({exc})")
    return issues


def validate_review(review: Mapping[str, Any], uc_ids: set[str]) -> list[str]:
    issues = [
        f"product-fit-review: {err.message} (at /{'/'.join(map(str, err.absolute_path))})"
        for err in jsonschema.Draft202012Validator(_load_json(REVIEW_SCHEMA_PATH)).iter_errors(
            review
        )
    ]
    known = set(products.product_ids())
    seen: set[str] = set()
    for entry in review.get("entries", []):
        uc_id = entry.get("id")
        if uc_id in seen:
            issues.append(f"product-fit-review: UC-{uc_id} is reviewed more than once")
        seen.add(uc_id)
        if uc_id not in uc_ids:
            issues.append(f"product-fit-review: UC-{uc_id} does not exist")
        for pid in entry.get("products", []):
            if pid not in known:
                issues.append(f"product-fit-review: UC-{uc_id} names unknown product {pid!r}")
    return issues


def _spl_text(uc: Mapping[str, Any]) -> str:
    return "\n".join(str(uc.get(k) or "") for k in _SPL_FIELDS)


def _is_makeresults_only(spl: str) -> bool:
    commands = set(parse.extract_commands(spl))
    if "makeresults" not in commands or commands & _DATA_COMMANDS:
        return False
    return not _IMPLICIT_SEARCH_RE.search(parse.strip_comments(spl))


def _product_name_pattern(pid: str, rule: Mapping[str, Any]) -> re.Pattern[str]:
    row = products.product(pid)
    names = {row["name"], row["shortName"], *rule.get("aliases", [])}
    alternation = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"\b({alternation})\b", re.IGNORECASE)


def _artifact_pattern(pid: str) -> re.Pattern[str] | None:
    nouns = [t.replace("-", " ") for t in products.product(pid)["artifactTypes"]]
    if not nouns:
        return None
    alternation = "|".join(re.escape(n) for n in nouns)
    return re.compile(rf"\b({alternation})s?\b", re.IGNORECASE)


def _data_reasons(spl: str, pid: str, rule: Mapping[str, Any]) -> tuple[bool, list[Reason]]:
    markers = [re.compile(m, re.IGNORECASE) for m in rule["dataMarkers"]]
    documented = rule["documentedIngest"]

    def is_product_data(value: str) -> bool:
        return any(m.search(value) for m in markers)

    reads_product = bool(set(parse.extract_commands(spl)) & set(documented["commands"]))
    reasons: list[Reason] = []
    seen: set[tuple[str, str]] = set()
    for kind, refs, allowed in (
        ("undocumented-sourcetype", parse.extract_sourcetypes(spl), documented["sourcetypes"]),
        ("undocumented-index", parse.extract_indexes(spl), documented["indexes"]),
    ):
        for ref in refs:
            if ref.is_wildcard or not is_product_data(ref.value):
                continue
            reads_product = True
            if ref.value in allowed or (kind, ref.value) in seen:
                continue
            seen.add((kind, ref.value))
            reasons.append(Reason(kind=kind, product=pid, detail=ref.value))
    return reads_product, reasons


def _configures_reason(uc: Mapping[str, Any], pid: str, rule: Mapping[str, Any]) -> Reason | None:
    # A product implemented in SPL (ITSI KPI base searches) is configured
    # *and* searched on the platform, so prose about its objects is expected.
    if products.applies({"products": [pid]}, "spl"):
        return None
    artifact_re = _artifact_pattern(pid)
    if artifact_re is None:
        return None
    name_re = _product_name_pattern(pid, rule)
    prose = "\n".join(str(uc.get(k) or "") for k in _PROSE_FIELDS)
    for sentence in _SENTENCE_SPLIT_RE.split(prose):
        if name_re.search(sentence) and artifact_re.search(sentence):
            return Reason(kind="configures-product", product=pid, detail=sentence.strip()[:240])
    return None


def find_candidates(
    ucs: Iterator[dict[str, Any]] | list[dict[str, Any]], rules: Mapping[str, Any]
) -> list[Candidate]:
    out: list[Candidate] = []
    for uc in ucs:
        spl = _spl_text(uc)
        reasons: list[Reason] = []
        if spl.strip() and _is_makeresults_only(spl):
            reasons.append(
                Reason(
                    kind="makeresults-only",
                    product=None,
                    detail="SPL builds its rows with makeresults and reads no data",
                )
            )
        for pid, rule in sorted(rules.get("products", {}).items()):
            reads_product, data_reasons = _data_reasons(spl, pid, rule)
            reasons.extend(data_reasons)
            if reads_product:
                configures = _configures_reason(uc, pid, rule)
                if configures is not None:
                    reasons.append(configures)
        if reasons:
            out.append(
                Candidate(
                    id=str(uc["id"]),
                    title=str(uc.get("title", "")),
                    products=products.products_of(uc),
                    reasons=reasons,
                )
            )
    return out


def build_report(candidates: list[Candidate], review: Mapping[str, Any]) -> dict[str, Any]:
    verdicts = {e["id"]: e["verdict"] for e in review.get("entries", [])}
    by_kind: dict[str, int] = {}
    by_product: dict[str, int] = {}
    rows = []
    for cand in candidates:
        for reason in cand.reasons:
            by_kind[reason.kind] = by_kind.get(reason.kind, 0) + 1
        for pid in sorted({r.product for r in cand.reasons if r.product}):
            by_product[pid] = by_product.get(pid, 0) + 1
        row = asdict(cand)
        row["verdict"] = verdicts.get(cand.id)
        rows.append(row)
    return {
        "candidates": len(candidates),
        "unreviewed": sum(1 for r in rows if r["verdict"] is None),
        "byReason": dict(sorted(by_kind.items())),
        "byProduct": dict(sorted(by_product.items())),
        "entries": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="Fail on malformed rules/review.")
    parser.add_argument(
        "--strict", action="store_true", help="Also fail when a candidate has no review entry."
    )
    parser.add_argument("--json", action="store_true", help="Print the report to stdout.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Report path.")
    args = parser.parse_args(argv)

    rules = _load_json(RULES_PATH)
    review = _load_json(REVIEW_PATH) if REVIEW_PATH.is_file() else {"entries": []}
    ucs = list(iter_ucs(CONTENT_ROOT))
    rule_issues = validate_rules(rules)
    issues = rule_issues + validate_review(review, {str(u["id"]) for u in ucs})

    candidates = [] if rule_issues else find_candidates(ucs, rules)
    report = build_report(candidates, review)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf-8")
        print(
            f"audit-uc-product-fit: {report['candidates']} candidate(s), "
            f"{report['unreviewed']} unreviewed; report at {args.out}"
        )
        for kind, count in report["byReason"].items():
            print(f"  {kind}: {count}")

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    if issues and (args.check or args.strict):
        return 1
    if args.strict and report["unreviewed"]:
        unreviewed = [r["id"] for r in report["entries"] if r["verdict"] is None]
        print(
            f"FAIL: {len(unreviewed)} candidate(s) lack a data/product-fit-review.json entry: "
            + ", ".join(f"UC-{i}" for i in unreviewed[:20])
            + (" ..." if len(unreviewed) > 20 else ""),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
