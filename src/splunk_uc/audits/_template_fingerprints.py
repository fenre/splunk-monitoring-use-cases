"""Detect bulk-enricher template fingerprints in UC sidecars.

Shared by ``audit-template-provenance`` and ``lift-validate --require-handcraft``.
Fingerprints mirror strings emitted by:

* ``scripts/enrich_gold_v2_bulk.py`` (GENERIC_KFP, controlTest, exclusions, evidence)
* ``scripts/enrich_gold_v1_backfill.py`` (visualization stub, DEFAULT_REFS)
* ``scripts/uplift_remaining_compliance.py`` (compliance KFP skeleton)
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Literal

Priority = Literal["P0", "P1", "P2", "P3", "P4"]

GENERIC_KFP_PREFIX = "1. **Scheduled maintenance windows**"
GENERIC_CONTROLTEST_PHRASE = "On a lab host or staging index"
GENERIC_EXCLUSIONS_PHRASE = "Does not replace enterprise SIEM correlation"
GENERIC_EVIDENCE_RE = re.compile(
    r"Saved search uc_\d+_\d+_\d+_.*, dashboard panel tied to this UC, "
    r"weekly CSV export archived to index=evidence",
    re.IGNORECASE,
)
VISUALIZATION_STUB_RE = re.compile(
    r"top row single-value tiles for alert count",
    re.IGNORECASE,
)
BANNED_LOOKUP_NAMES = (
    "operational_exceptions.csv",
    "monitoring_exceptions.csv",
)

GENERIC_REF_URLS = (
    "https://docs.splunk.com/Documentation/Splunk",
    "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/What'sInThisManual",
    "https://docs.splunk.com/Documentation/CIM",
    "https://splunkbase.splunk.com/app/617",
)

INDEX_TOKEN_RE = re.compile(r"index\s*=\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)
SOURCETYPE_TOKEN_RE = re.compile(
    r"sourcetype\s*[=:]\s*['\"]?([a-zA-Z0-9_:\-\.]+)", re.IGNORECASE
)
SPLUNKBASE_TOKEN_RE = re.compile(
    r"(?:Splunkbase\s+(\d{2,5})|splunkbase\.splunk\.com/app/(\d+))",
    re.IGNORECASE,
)
TITLE_WORD_RE = re.compile(r"\b[a-zA-Z]{4,}\b")

FULL_V2_TEMPLATE_FLAGS = frozenset(
    {
        "generic_kfp",
        "generic_controlTest",
        "generic_exclusions",
        "generic_evidence",
    }
)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _reference_urls(references: Any) -> list[str]:
    if not isinstance(references, list):
        return []
    urls: list[str] = []
    for entry in references:
        if isinstance(entry, dict):
            url = entry.get("url")
            if isinstance(url, str) and url.strip():
                urls.append(url.strip())
    return urls


def detect_template_flags(uc: dict[str, Any]) -> list[str]:
    """Return sorted template-fingerprint flag IDs present on this sidecar."""
    flags: set[str] = set()

    kfp = _as_str(uc.get("knownFalsePositives"))
    if kfp.startswith(GENERIC_KFP_PREFIX):
        flags.add("generic_kfp")
    for banned in BANNED_LOOKUP_NAMES:
        if banned in kfp:
            flags.add("generic_kfp")

    ct = uc.get("controlTest")
    if isinstance(ct, dict):
        pos = _as_str(ct.get("positiveScenario"))
        neg = _as_str(ct.get("negativeScenario"))
        if GENERIC_CONTROLTEST_PHRASE in pos:
            flags.add("generic_controlTest")
        if "operational_exceptions.csv" in neg:
            flags.add("generic_controlTest")

    exclusions = _as_str(uc.get("exclusions"))
    if GENERIC_EXCLUSIONS_PHRASE in exclusions:
        flags.add("generic_exclusions")

    evidence = _as_str(uc.get("evidence"))
    if GENERIC_EVIDENCE_RE.search(evidence):
        flags.add("generic_evidence")

    visualization = _as_str(uc.get("visualization"))
    if VISUALIZATION_STUB_RE.search(visualization):
        flags.add("generic_visualization")

    ref_urls = _reference_urls(uc.get("references"))
    generic_ref_hits = sum(1 for url in ref_urls if url in GENERIC_REF_URLS)
    if generic_ref_hits >= 3 and len(ref_urls) <= 4:
        flags.add("generic_references")

    return sorted(flags)


def is_fully_templated_v2(flags: list[str] | set[str]) -> bool:
    """True when all four v2 bulk narrative fingerprints are present."""
    return FULL_V2_TEMPLATE_FLAGS.issubset(set(flags))


def extract_domain_tokens(uc: dict[str, Any]) -> set[str]:
    """Tokens an agent must reflect in hand-crafted narrative fields."""
    tokens: set[str] = set()
    for field_name in ("spl", "dataSources", "app", "title", "implementation"):
        text = _as_str(uc.get(field_name))
        for match in INDEX_TOKEN_RE.finditer(text):
            tokens.add(match.group(1).lower())
        for match in SOURCETYPE_TOKEN_RE.finditer(text):
            tokens.add(match.group(1).lower())
        for match in SPLUNKBASE_TOKEN_RE.finditer(text):
            sid = match.group(1) or match.group(2)
            if sid:
                tokens.add(f"splunkbase_{sid}")
    title = _as_str(uc.get("title"))
    for word in TITLE_WORD_RE.findall(title):
        lowered = word.lower()
        if lowered not in {"monitoring", "detection", "alert", "use", "case"}:
            tokens.add(lowered)
    return tokens


def count_domain_token_hits(text: str, tokens: set[str]) -> int:
    """How many domain tokens appear in ``text`` (case-insensitive)."""
    if not text or not tokens:
        return 0
    lowered = text.lower()
    return sum(1 for token in tokens if token in lowered)


def check_domain_token_binding(
    uc: dict[str, Any],
    *,
    kfp_min: int = 2,
    control_test_min: int = 2,
    di_min: int = 4,
) -> list[str]:
    """Return human-readable refusal reasons when narrative fields lack domain tokens."""
    tokens = extract_domain_tokens(uc)
    if len(tokens) < 2:
        return [
            "domain-token binding: insufficient tokens in spl/dataSources/app/title to verify hand-craft"
        ]

    reasons: list[str] = []
    kfp = _as_str(uc.get("knownFalsePositives"))
    if count_domain_token_hits(kfp, tokens) < kfp_min:
        reasons.append(
            f"domain-token binding: knownFalsePositives mentions fewer than {kfp_min} "
            f"tokens from this UC's SPL/dataSources ({sorted(tokens)[:8]}…)"
        )

    ct = uc.get("controlTest")
    if isinstance(ct, dict):
        combined = _as_str(ct.get("positiveScenario")) + " " + _as_str(ct.get("negativeScenario"))
        if count_domain_token_hits(combined, tokens) < control_test_min:
            reasons.append(
                f"domain-token binding: controlTest mentions fewer than {control_test_min} "
                "domain tokens from this UC's SPL/dataSources"
            )

    di = _as_str(uc.get("detailedImplementation"))
    if count_domain_token_hits(di, tokens) < di_min:
        reasons.append(
            f"domain-token binding: detailedImplementation mentions fewer than {di_min} "
            "domain tokens from this UC's SPL/dataSources"
        )

    combined_narrative = " ".join(
        [
            kfp,
            _as_str(uc.get("exclusions")),
            _as_str(uc.get("evidence")),
            di,
        ]
    )
    for banned in BANNED_LOOKUP_NAMES:
        if banned in combined_narrative:
            reasons.append(f"domain-token binding: banned template lookup {banned!r} still present")
    if GENERIC_EXCLUSIONS_PHRASE in _as_str(uc.get("exclusions")):
        reasons.append("domain-token binding: generic exclusions boilerplate still present")

    return reasons


def normalized_narrative_blob(uc: dict[str, Any]) -> str:
    """Concatenate lift-surface narrative fields for similarity checks."""
    parts = [
        _as_str(uc.get("knownFalsePositives")),
        _as_str(uc.get("detailedImplementation")),
        _as_str(uc.get("description")),
        _as_str(uc.get("value")),
    ]
    ct = uc.get("controlTest")
    if isinstance(ct, dict):
        parts.append(_as_str(ct.get("positiveScenario")))
        parts.append(_as_str(ct.get("negativeScenario")))
    blob = " ".join(parts).lower()
    blob = re.sub(r"\s+", " ", blob).strip()
    return blob


def narrative_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    """SequenceMatcher ratio between two UCs' narrative blobs (0..1)."""
    left = normalized_narrative_blob(a)
    right = normalized_narrative_blob(b)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def check_minimum_substantive_delta(
    original: dict[str, Any],
    lifted: dict[str, Any],
    lifted_field_names: set[str],
) -> list[str]:
    """Ensure templated UCs change materially, not cosmetically."""
    reasons: list[str] = []
    orig_flags = set(detect_template_flags(original))
    if not orig_flags:
        return reasons

    if len(lifted_field_names) < 3:
        reasons.append(
            "minimum delta: templated UC requires at least 3 lifted_fields "
            f"(got {len(lifted_field_names)})"
        )

    if "knownFalsePositives" in lifted_field_names:
        before = _as_str(original.get("knownFalsePositives"))
        after = _as_str(lifted.get("knownFalsePositives"))
        if before and after:
            ratio = SequenceMatcher(None, before, after).ratio()
            if ratio >= 0.45:
                reasons.append(
                    f"minimum delta: knownFalsePositives too similar to pre-lift template "
                    f"(similarity {ratio:.2f} >= 0.45)"
                )
    return reasons


def infer_priority(uc: dict[str, Any], *, rel_path: str = "") -> Priority:
    """Queue priority for hand-craft burndown."""
    flags = detect_template_flags(uc)
    if not flags:
        return "P4"

    compliance = uc.get("compliance")
    if isinstance(compliance, list):
        for entry in compliance:
            if not isinstance(entry, dict):
                continue
            assurance = _as_str(entry.get("assurance")).lower()
            if assurance == "full":
                return "P0"

    if "cat-10-" in rel_path or "cat-17-" in rel_path or "cat-09-" in rel_path:
        return "P1"
    if "cat-25-" in rel_path:
        return "P3"
    return "P2"
