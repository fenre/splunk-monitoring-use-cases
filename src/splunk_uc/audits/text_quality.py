#!/usr/bin/env python3
"""Deterministic text-quality pre-pass for the UC review (Phase 0, no LLM).

Writes one review record per UC to ``reports/uc-review/deterministic.jsonl``
(schema ``schemas/v2/uc-review-finding.schema.json``, ``tier=deterministic``)
plus a roll-up in ``reports/uc-review/deterministic-summary.json``. The model
tiers receive these findings pre-attached so they do not spend tokens
re-discovering template residue.

Checks
------

* ``template_v1:<flag>`` / ``template_v2:<flag>`` — bulk-enricher template
  families from ``_template_fingerprints``.
* ``skeleton_cluster:<field>`` — the opening sentence of a narrative field
  shares a masked skeleton with at least ``--min-cluster`` other UCs.
* ``title_token_salad`` — a comma list made only of title words stands in
  for prose.
* ``premium_app_pillar_mismatch`` — a security-only premium app on a
  non-security UC.
* ``cim_models_missing`` / ``cim_models_mismatch`` / ``cim_models_malformed``
  — ``cimModels`` disagrees with the datamodel queried in ``cimSpl``.
* ``splunkbase_name_mismatch`` / ``splunkbase_deprecated`` /
  ``splunkbase_unknown_id`` — a cited Splunkbase ID versus the cached
  ``data/splunkbase-catalog.json`` listing.
* ``duplicate_prose`` — two narrative fields say nearly the same thing.
* ``spelling`` — codespell dictionary hits in prose (optional dependency;
  allow-list in ``data/text-quality-spelling-allowlist.txt``).

Usage::

    PYTHONPATH=src python3 -m splunk_uc audit-text-quality
    PYTHONPATH=src python3 -m splunk_uc audit-text-quality --category cat-15
    PYTHONPATH=src python3 -m splunk_uc audit-text-quality --files content/cat-05-network-infrastructure/UC-5.1.1.json --stdout
    PYTHONPATH=src python3 -m splunk_uc audit-text-quality --check --max-major 200000
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any

from splunk_uc.audits._template_fingerprints import (
    V2_FAMILIES,
    detect_template_flags,
    detect_template_flags_v2,
)
from splunk_uc.audits.cim_spl_alignment import (
    CANONICAL_DATAMODELS,
    TOKEN_NORMALISATION,
)
from splunk_uc.review._ledger import (
    DETERMINISTIC_LEDGER,
    REPO_ROOT,
    REVIEW_ROOT,
    iter_sidecars,
    new_record,
)

MODEL_ID = "deterministic:audit-text-quality"
SUMMARY_PATH = REVIEW_ROOT / "deterministic-summary.json"
SPLUNKBASE_CATALOG = REPO_ROOT / "data" / "splunkbase-catalog.json"
SPELLING_ALLOWLIST = REPO_ROOT / "data" / "text-quality-spelling-allowlist.txt"
QUOTE_MAX = 200

V1_FLAG_FIELDS = {
    "generic_kfp": "knownFalsePositives",
    "generic_controlTest": "controlTest",
    "generic_exclusions": "exclusions",
    "generic_evidence": "evidence",
    "generic_visualization": "visualization",
    "generic_references": "references",
}

HEADLINE_FIELDS = ("description", "value", "grandmaExplanation")
CLUSTER_FIELDS = (
    "description",
    "value",
    "grandmaExplanation",
    "implementation",
    "exclusions",
    "evidence",
    "visualization",
    "controlTest.positiveScenario",
    "controlTest.negativeScenario",
)
DUPLICATE_PAIRS = (
    ("description", "value"),
    ("description", "implementation"),
    ("description", "grandmaExplanation"),
    ("value", "grandmaExplanation"),
)
SPELLING_FIELDS = (
    "title",
    "description",
    "value",
    "implementation",
    "detailedImplementation",
    "grandmaExplanation",
    "knownFalsePositives",
    "exclusions",
    "evidence",
    "visualization",
)

SECURITY_ONLY_PREMIUM_APPS = frozenset(
    {
        "Splunk Enterprise Security",
        "Splunk User Behavior Analytics",
        "Splunk SOAR",
        "Splunk OT Security Add-on",
    }
)

SPLUNKBASE_MENTION_RE = re.compile(
    r"(?P<name>(?:[\w&./+-]+ ){0,7}[\w&./+-]+)\s*"
    r"\((?:`[^`]+`,\s*)?Splunkbase\s*(?:app\s*|ID\s*|#)?(?P<id>\d{2,6})\)",
    re.IGNORECASE,
)
MENTION_SPLIT_RE = re.compile(
    r"\b(?:via|with|using|through|from|into|and|or|by|in|plus|alongside|the|"
    r"Collected|Ingested|collected|ingested|locally)\b|[\u2014\u2013:;.,]"
)
NAME_STOPWORDS = frozenset(
    {
        "splunk",
        "add",
        "on",
        "addon",
        "app",
        "apps",
        "for",
        "the",
        "and",
        "of",
        "ta",
        "technology",
        "supporting",
        "a",
        "an",
        "to",
        "in",
        "by",
    }
)
NAME_ABBREVIATIONS = {
    "aws": ("amazon", "web", "services"),
    "gcp": ("google", "cloud", "platform"),
    "ot": ("operational", "technology"),
    "cim": ("common", "information", "model"),
    "o365": ("office", "365"),
    "m365": ("microsoft", "365"),
    "k8s": ("kubernetes",),
    "esxi": ("vmware",),
}
NAME_MATCH_MIN = 0.6
MENTION_LEAD_NOISE = frozenset(
    {
        "install",
        "deploy",
        "keep",
        "stand",
        "up",
        "enable",
        "configure",
        "use",
        "uses",
        "optional",
        "its",
        "ingestion",
        "over",
        "qualified",
        "normalizer",
    }
)

DATAMODEL_RE = re.compile(r"datamodel\s*[=:]\s*[`\"']?([A-Za-z][A-Za-z0-9_]*)", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")
WORD_RE = re.compile(r"(?<![-'\u2019/])\b[A-Za-z][a-z]{2,}\b(?![-'\u2019/])")
PLACEHOLDER_TOKEN_RE = re.compile(
    r"\b(?:Metric|Field|Sensor|Param|Placeholder)\s?\d+\b", re.IGNORECASE
)
PLACEHOLDER_SOURCETYPE_RE = re.compile(
    r"sourcetype\s*=\s*[\"']?([\w:.-]*(?:metric|field|param|placeholder)\d+[\w:.-]*)", re.IGNORECASE
)
COMMA_LIST_RE = re.compile(r"(?:[A-Z][\w/+.&-]*, ){2,}[A-Z][\w/+.&-]*")


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _field_text(uc: dict[str, Any], field: str) -> str:
    if "." in field:
        parent, child = field.split(".", 1)
        node = uc.get(parent)
        return _as_str(node.get(child)) if isinstance(node, dict) else ""
    return _as_str(uc.get(field))


def _quote(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= QUOTE_MAX else text[: QUOTE_MAX - 1] + "…"


def _finding(
    *,
    field: str,
    dimension: str,
    severity: str,
    check: str,
    explanation: str,
    quote: str = "",
    suggested_fix: str = "",
    evidence_ref: str = "",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "field": field,
        "dimension": dimension,
        "severity": severity,
        "check": check,
        "explanation": explanation,
    }
    if quote:
        out["quote"] = _quote(quote)
    if suggested_fix:
        out["suggested_fix"] = suggested_fix
    if evidence_ref:
        out["evidence_ref"] = evidence_ref
    return out


# --------------------------------------------------------------------------
# Template families
# --------------------------------------------------------------------------


def check_templates(uc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for flag in detect_template_flags(uc):
        field = V1_FLAG_FIELDS.get(flag, "cross_field")
        findings.append(
            _finding(
                field=field,
                dimension="specificity",
                severity="major",
                check=f"template_v1:{flag}",
                explanation=f"Bulk-enricher v1 template residue ({flag}).",
                quote=_field_text(uc, field) if field != "references" else "",
                suggested_fix="Hand-write this field from the UC's actual SPL, data source and product behaviour.",
            )
        )
    for flag in detect_template_flags_v2(uc):
        field, description = V2_FAMILIES[flag]
        findings.append(
            _finding(
                field=field,
                dimension="specificity",
                severity="major",
                check=f"template_v2:{flag}",
                explanation=f"Generated template residue: {description}.",
                quote=_v2_quote(uc, flag, field),
                suggested_fix=V2_FIXES.get(flag, V2_DEFAULT_FIX),
            )
        )
    return findings


V2_DEFAULT_FIX = (
    "Replace the generated sentence with use-case-specific prose; "
    "never cite the UC's own ID inside narrative fields."
)
V2_FIXES = {
    "v2_lantern_root_reference": "Cite the specific Lantern article for this use case, or drop the reference.",
    "v2_exception_register": "Name the real suppression mechanism (lookup, macro, or allow-list) this deployment would use.",
    "v2_controlTest_variant": "Describe concrete input values and the expected alert rows; drop the 'Variant N' sentence.",
}
_V2_NEEDLES: dict[str, str] = {
    "v2_description_purpose_built": r"Purpose-built for",
    "v2_description_title_salad": r"UC-\d+\.\d+\.\d+ — (?:[A-Z][\w/+.&-]*, )+",
    "v2_controlTest_variant": r"\bVariant \d+ confirms",
    "v2_controlTest_skeleton": r"UC-\d+\.\d+\.\d+ (?:positive|negative) \(",
    "v2_kfp_selfref_heading": r"\*\*[^*\n]*UC-\d+\.\d+\.\d+[^*\n]*\*\*",
    "v2_exception_register": r"ops_exception_register\.csv",
}


def _v2_quote(uc: dict[str, Any], flag: str, field: str) -> str:
    """The sentence that carries the template residue."""
    if field == "references":
        return "https://lantern.splunk.com/"
    if field == "controlTest":
        raw_ct = uc.get("controlTest")
        ct: dict[str, Any] = raw_ct if isinstance(raw_ct, dict) else {}
        text = f"{_as_str(ct.get('positiveScenario'))}\n{_as_str(ct.get('negativeScenario'))}"
    else:
        text = _field_text(uc, field)
    needle = _V2_NEEDLES.get(flag)
    if needle is None and flag.endswith("_selfref"):
        needle = re.escape(f"UC-{str(uc.get('id', '')).removeprefix('UC-')}")
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    if needle:
        for sentence in sentences:
            if re.search(needle, sentence):
                return sentence
    return sentences[0] if sentences else ""


# --------------------------------------------------------------------------
# Skeleton clustering (corpus-level)
# --------------------------------------------------------------------------


def sentence_skeleton(text: str, *, words: int = 12) -> str:
    """Mask variable tokens in the first sentence so generated siblings collide."""
    first = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0] if text.strip() else ""
    masked = INLINE_CODE_RE.sub("X", first)
    masked = re.sub(r"'[^']*'", "Y", masked)
    masked = re.sub(r'"[^"]*"', "Y", masked)
    masked = re.sub(r"UC-\d+\.\d+\.\d+", "U", masked)
    masked = re.sub(r"\d+(?:\.\d+)*", "N", masked)
    tokens = masked.lower().split()
    if len(tokens) < 5:
        return ""
    return " ".join(tokens[:words])


def build_skeleton_index(
    sidecars: list[tuple[Path, dict[str, Any]]],
) -> dict[str, Counter[str]]:
    index: dict[str, Counter[str]] = {field: Counter() for field in CLUSTER_FIELDS}
    for _, uc in sidecars:
        for field in CLUSTER_FIELDS:
            skeleton = sentence_skeleton(_field_text(uc, field))
            if skeleton:
                index[field][skeleton] += 1
    return index


def check_skeleton_clusters(
    uc: dict[str, Any],
    index: dict[str, Counter[str]],
    *,
    min_cluster: int,
    skip_fields: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for field in CLUSTER_FIELDS:
        base_field = field.split(".", 1)[0]
        if base_field in skip_fields:
            continue
        text = _field_text(uc, field)
        skeleton = sentence_skeleton(text)
        size = index.get(field, Counter()).get(skeleton, 0) if skeleton else 0
        if size < min_cluster:
            continue
        findings.append(
            _finding(
                field=base_field,
                dimension="specificity",
                severity="major" if base_field in HEADLINE_FIELDS else "minor",
                check=f"skeleton_cluster:{field}",
                explanation=(
                    f"Opening sentence of {field} shares its skeleton with {size - 1} "
                    "other UCs (generated sentence pattern)."
                ),
                quote=re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0],
                suggested_fix="Rewrite the opening sentence around this UC's specific signal and outcome.",
            )
        )
    return findings


# --------------------------------------------------------------------------
# Title-token salad
# --------------------------------------------------------------------------


def check_title_token_salad(uc: dict[str, Any], *, skip_fields: set[str]) -> list[dict[str, Any]]:
    title_words = {w.lower() for w in re.findall(r"[\w/+.&-]+", _as_str(uc.get("title")))}
    if not title_words:
        return []
    findings: list[dict[str, Any]] = []
    for field in ("description", "controlTest.positiveScenario", "controlTest.negativeScenario"):
        base_field = field.split(".", 1)[0]
        if base_field in skip_fields:
            continue
        for match in COMMA_LIST_RE.finditer(_field_text(uc, field)):
            tokens = [t.strip().lower() for t in match.group(0).split(",")]
            if len(tokens) >= 3 and all(t in title_words for t in tokens):
                findings.append(
                    _finding(
                        field=base_field,
                        dimension="clarity",
                        severity="major",
                        check="title_token_salad",
                        explanation="A comma list of title words stands in for a sentence.",
                        quote=match.group(0),
                        suggested_fix="Describe the behaviour in a sentence instead of listing title tokens.",
                    )
                )
                break
    return findings


# --------------------------------------------------------------------------
# Placeholder tokens in firewalled identity / SPL fields
# --------------------------------------------------------------------------


def check_placeholders(uc: dict[str, Any]) -> list[dict[str, Any]]:
    """Firewalled-field flags: placeholder tokens a human must replace in title / SPL."""
    flags: list[dict[str, Any]] = []
    title = _as_str(uc.get("title"))
    match = PLACEHOLDER_TOKEN_RE.search(title)
    if match:
        flags.append(
            {
                "field": "title",
                "issue": f"Title carries the generator placeholder '{match.group(0)}' instead of a real metric name.",
                "severity": "major",
            }
        )
    for field in ("spl", "cimSpl"):
        st = PLACEHOLDER_SOURCETYPE_RE.search(_as_str(uc.get(field)))
        if st:
            flags.append(
                {
                    "field": field,
                    "issue": f"{field} queries placeholder sourcetype '{st.group(1)}'.",
                    "severity": "major",
                }
            )
    return flags


# --------------------------------------------------------------------------
# premiumApps vs pillar
# --------------------------------------------------------------------------


def check_premium_apps(uc: dict[str, Any]) -> list[dict[str, Any]]:
    pillar = _as_str(uc.get("splunkPillar"))
    if not pillar or pillar == "Security":
        return []
    findings: list[dict[str, Any]] = []
    for entry in uc.get("premiumApps") or []:
        name = entry.get("name") if isinstance(entry, dict) else entry
        if isinstance(name, str) and name in SECURITY_ONLY_PREMIUM_APPS:
            findings.append(
                _finding(
                    field="premiumApps",
                    dimension="correctness",
                    severity="major",
                    check="premium_app_pillar_mismatch",
                    explanation=(
                        f"Security-only premium app '{name}' is attached to a "
                        f"splunkPillar={pillar} use case."
                    ),
                    suggested_fix="Remove the premium app unless the SPL or implementation genuinely depends on it.",
                )
            )
    return findings


# --------------------------------------------------------------------------
# CIM models vs cimSpl
# --------------------------------------------------------------------------


def _canonical_cim(token: str) -> str | None:
    token = token.strip()
    if token in TOKEN_NORMALISATION:
        return TOKEN_NORMALISATION[token]
    root = token.split(".", 1)[0].replace(" ", "_").replace("-", "_")
    if root in CANONICAL_DATAMODELS:
        return root
    aliases = {"Data_Loss_Prevention": "DLP", "Incident_Management": "Incident_Management"}
    return aliases.get(root)


def check_cim(uc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    declared_raw = [m for m in uc.get("cimModels") or [] if isinstance(m, str)]
    declared: set[str] = set()
    for token in declared_raw:
        canonical = _canonical_cim(token)
        if canonical:
            declared.add(canonical)
        elif not re.fullmatch(r"[A-Z][A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", token.strip()):
            findings.append(
                _finding(
                    field="cimModels",
                    dimension="consistency",
                    severity="major",
                    check="cim_models_malformed",
                    explanation=f"cimModels entry '{token}' is not a datamodel name (split or truncated text).",
                    quote=token,
                    suggested_fix="Replace with the canonical CIM datamodel name, e.g. Network_Traffic.",
                )
            )
    queried = {
        m.group(1).split(".", 1)[0] for m in DATAMODEL_RE.finditer(_as_str(uc.get("cimSpl")))
    }
    queried_canonical = {q for q in queried if q in CANONICAL_DATAMODELS}
    if queried_canonical and not declared_raw:
        findings.append(
            _finding(
                field="cimModels",
                dimension="consistency",
                severity="major",
                check="cim_models_missing",
                explanation=(
                    "cimSpl queries datamodel "
                    + ", ".join(sorted(queried_canonical))
                    + " but cimModels is empty."
                ),
                suggested_fix="Declare the datamodel in cimModels, or confirm the CIM mapping fits this signal.",
            )
        )
    elif queried_canonical and declared and not (queried_canonical & declared):
        findings.append(
            _finding(
                field="cimModels",
                dimension="consistency",
                severity="major",
                check="cim_models_mismatch",
                explanation=(
                    f"cimSpl queries {sorted(queried_canonical)} but cimModels declares "
                    f"{sorted(declared)}."
                ),
                suggested_fix="Align cimModels with the datamodel actually queried (cimSpl itself is firewalled).",
            )
        )
    return findings


# --------------------------------------------------------------------------
# Splunkbase IDs
# --------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_splunkbase_catalog() -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(SPLUNKBASE_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    apps = payload.get("apps") if isinstance(payload, dict) else None
    return apps if isinstance(apps, dict) else {}


def _raw_tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t}


def _name_tokens(text: str) -> set[str]:
    return _raw_tokens(text) - NAME_STOPWORDS


def mention_segment(mentioned: str) -> str:
    """The product-name part of the words preceding '(Splunkbase N)'."""
    words = MENTION_SPLIT_RE.split(mentioned)[-1].split()
    while words and words[0].lower() in MENTION_LEAD_NOISE:
        words.pop(0)
    return " ".join(words)


def splunkbase_name_overlap(mentioned: str, listing: dict[str, Any]) -> float | None:
    """Fraction of significant mention tokens found in the catalog listing (None = nothing to compare)."""
    segment = mention_segment(mentioned)
    wanted = _name_tokens(segment)
    if not wanted:
        return None
    listing_text = f"{listing.get('displayName', '')} {listing.get('name', '')}"
    squashed_listing = re.sub(r"[^a-z0-9]", "", listing_text.lower())
    squashed_mention = re.sub(
        r"[^a-z0-9]",
        "",
        " ".join(
            t for t in re.split(r"[^a-z0-9]+", segment.lower()) if t and t not in NAME_STOPWORDS
        ),
    )
    if squashed_mention and squashed_mention in squashed_listing:
        return 1.0
    have_raw = _raw_tokens(listing_text)
    have = have_raw - NAME_STOPWORDS
    hits = 0
    for token in wanted:
        expansion = NAME_ABBREVIATIONS.get(token)
        if token in have or (expansion and all(part in have_raw for part in expansion)):
            hits += 1
            continue
        if any(token in NAME_ABBREVIATIONS.get(h, ()) for h in have):
            hits += 1
    return hits / len(wanted)


def check_splunkbase(uc: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = load_splunkbase_catalog()
    if not catalog:
        return []
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for field in ("app", "dataSources", "implementation"):
        for match in SPLUNKBASE_MENTION_RE.finditer(_as_str(uc.get(field))):
            app_id = match.group("id")
            mentioned = match.group("name")
            key = (app_id, mention_segment(mentioned).lower())
            if key in seen:
                continue
            seen.add(key)
            listing = catalog.get(app_id)
            if listing is None:
                findings.append(
                    _finding(
                        field=field,
                        dimension="correctness",
                        severity="needs_verification",
                        check="splunkbase_unknown_id",
                        explanation=(
                            f"Splunkbase {app_id} is not in the cached data/splunkbase-catalog.json; "
                            "verify the ID points at the add-on named here."
                        ),
                        quote=match.group(0),
                    )
                )
                continue
            display = str(listing.get("displayName") or listing.get("name") or "")
            if display.upper().startswith(("DEPRECATED", "ARCHIVED")):
                findings.append(
                    _finding(
                        field=field,
                        dimension="correctness",
                        severity="major",
                        check="splunkbase_deprecated",
                        explanation=f"Splunkbase {app_id} is listed as '{display}'.",
                        quote=match.group(0),
                        suggested_fix="Point at the supported successor add-on.",
                        evidence_ref="data/splunkbase-catalog.json",
                    )
                )
                continue
            overlap = splunkbase_name_overlap(mentioned, listing)
            if overlap is not None and overlap < NAME_MATCH_MIN:
                findings.append(
                    _finding(
                        field=field,
                        dimension="correctness",
                        severity="major",
                        check="splunkbase_name_mismatch",
                        explanation=(
                            f"Text names '{mention_segment(mentioned)}' but "
                            f"Splunkbase {app_id} is '{display}'."
                        ),
                        quote=match.group(0),
                        suggested_fix="Use the Splunkbase ID of the add-on actually named, or rename to match the listing.",
                        evidence_ref="data/splunkbase-catalog.json",
                    )
                )
    return findings


# --------------------------------------------------------------------------
# Duplicate prose across fields
# --------------------------------------------------------------------------


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", INLINE_CODE_RE.sub("X", text)).strip().lower()


def check_duplicate_prose(uc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for left, right in DUPLICATE_PAIRS:
        a, b = _normalise(_as_str(uc.get(left))), _normalise(_as_str(uc.get(right)))
        if len(a) < 40 or len(b) < 40:
            continue
        matcher = SequenceMatcher(None, a, b, autojunk=False)
        if matcher.quick_ratio() < 0.75:
            continue
        ratio = matcher.ratio()
        if ratio < 0.75:
            continue
        findings.append(
            _finding(
                field=right,
                dimension="specificity",
                severity="major" if ratio >= 0.9 else "minor",
                check="duplicate_prose",
                explanation=f"{right} repeats {left} ({ratio:.0%} similar).",
                quote=_as_str(uc.get(right)),
                suggested_fix=f"Make {right} add information {left} does not already give.",
            )
        )
    return findings


# --------------------------------------------------------------------------
# Spelling
# --------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_spelling_dictionary() -> dict[str, str]:
    """codespell's main dictionary minus the repo allow-list ({} when codespell is absent)."""
    try:
        import codespell_lib
    except ImportError:
        return {}
    path = Path(codespell_lib.__file__).parent / "data" / "dictionary.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    allow: set[str] = set()
    if SPELLING_ALLOWLIST.is_file():
        allow = {
            line.strip().lower()
            for line in SPELLING_ALLOWLIST.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }
    mapping: dict[str, str] = {}
    for line in lines:
        if "->" not in line:
            continue
        wrong, right = line.split("->", 1)
        wrong = wrong.strip().lower()
        if wrong and wrong not in allow:
            mapping[wrong] = right.split(",")[0].strip()
    return mapping


def _prose_only(text: str) -> str:
    text = CODE_FENCE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    return URL_RE.sub(" ", text)


def check_spelling(uc: dict[str, Any], dictionary: dict[str, str]) -> list[dict[str, Any]]:
    if not dictionary:
        return []
    findings: list[dict[str, Any]] = []
    for field in SPELLING_FIELDS:
        hits: dict[str, str] = {}
        for word in WORD_RE.findall(_prose_only(_as_str(uc.get(field)))):
            fix = dictionary.get(word.lower())
            if fix and word.lower() not in hits:
                hits[word.lower()] = fix
        if hits:
            pairs = ", ".join(f"{w} -> {f}" for w, f in sorted(hits.items())[:8])
            findings.append(
                _finding(
                    field=field,
                    dimension="spelling",
                    severity="minor",
                    check="spelling",
                    explanation=f"Likely misspellings: {pairs}.",
                    quote=", ".join(sorted(hits)[:8]),
                )
            )
    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def review_uc(
    path: Path,
    uc: dict[str, Any],
    *,
    skeleton_index: dict[str, Counter[str]] | None,
    min_cluster: int,
    spelling: dict[str, str],
) -> dict[str, Any]:
    record = new_record(uc=uc, path=path, tier="deterministic", model=MODEL_ID)
    findings = check_templates(uc)
    templated_fields = {f["field"] for f in findings}
    if skeleton_index is not None:
        findings += check_skeleton_clusters(
            uc, skeleton_index, min_cluster=min_cluster, skip_fields=templated_fields
        )
    findings += check_title_token_salad(
        uc,
        skip_fields={
            f["field"] for f in findings if f["check"] == "template_v2:v2_description_title_salad"
        },
    )
    findings += check_premium_apps(uc)
    findings += check_cim(uc)
    findings += check_splunkbase(uc)
    findings += check_duplicate_prose(uc)
    findings += check_spelling(uc, spelling)
    record["findings"] = findings
    record["firewalled_field_flags"] = check_placeholders(uc)
    return record


def summarise(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_check: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    ucs_with_findings = 0
    for record in records:
        category = (
            record.get("file", "").split("/")[1] if "/" in record.get("file", "") else "unknown"
        )
        by_category[category]["ucs"] += 1
        if record["findings"]:
            ucs_with_findings += 1
            by_category[category]["ucs_with_findings"] += 1
        for flag in record.get("firewalled_field_flags", []):
            by_check[f"firewalled:{flag['field']}"] += 1
        for finding in record["findings"]:
            family = finding["check"].split(":", 1)[0]
            check = finding["check"] if family.startswith("template") else family
            by_check[check] += 1
            by_severity[finding["severity"]] += 1
            by_category[category][finding["severity"]] += 1
    return {
        "$comment": "Roll-up of reports/uc-review/deterministic.jsonl (audit-text-quality).",
        "schema_version": "1.0",
        "model": MODEL_ID,
        "ucs": len(records),
        "ucs_with_findings": ucs_with_findings,
        "by_severity": dict(sorted(by_severity.items())),
        "by_check": dict(sorted(by_check.items())),
        "by_category": {k: dict(sorted(v.items())) for k, v in sorted(by_category.items())},
    }


def run(
    *,
    files: list[str] | None,
    category: str | None,
    min_cluster: int,
    clusters: bool,
    spelling: bool,
) -> list[dict[str, Any]]:
    selected = list(iter_sidecars(files=files, category=category))
    skeleton_index = None
    if clusters:
        corpus = selected if not (files or category) else list(iter_sidecars())
        skeleton_index = build_skeleton_index(corpus)
    dictionary = load_spelling_dictionary() if spelling else {}
    return [
        review_uc(
            path,
            uc,
            skeleton_index=skeleton_index,
            min_cluster=min_cluster,
            spelling=dictionary,
        )
        for path, uc in selected
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc audit-text-quality",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--files", nargs="*", help="Specific UC sidecar paths")
    parser.add_argument("--category", help="Limit to one category prefix, e.g. cat-15")
    parser.add_argument(
        "--min-cluster", type=int, default=50, help="Skeleton cluster size that counts as templated"
    )
    parser.add_argument(
        "--no-clusters", action="store_true", help="Skip corpus skeleton clustering"
    )
    parser.add_argument(
        "--no-spelling", action="store_true", help="Skip codespell dictionary checks"
    )
    parser.add_argument("--out", type=Path, default=DETERMINISTIC_LEDGER, help="JSONL ledger path")
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH, help="Summary JSON path")
    parser.add_argument("--no-write", action="store_true", help="Print the summary only")
    parser.add_argument(
        "--stdout", action="store_true", help="Print records as JSONL to stdout instead of writing"
    )
    parser.add_argument("--check", action="store_true", help="Apply --max-* caps to the exit code")
    parser.add_argument(
        "--max-major", type=int, default=None, help="Fail --check above this many major findings"
    )
    parser.add_argument(
        "--max-blocker",
        type=int,
        default=None,
        help="Fail --check above this many blocker findings",
    )
    args = parser.parse_args(argv)

    records = run(
        files=args.files,
        category=args.category,
        min_cluster=args.min_cluster,
        clusters=not args.no_clusters,
        spelling=not args.no_spelling,
    )
    summary = summarise(records)

    if args.stdout:
        for record in records:
            print(json.dumps(record, sort_keys=True, ensure_ascii=False))
    elif not args.no_write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Wrote {args.out} and {args.summary}", file=sys.stderr)

    sev = summary["by_severity"]
    print(
        f"audit-text-quality: {summary['ucs']} UCs, {summary['ucs_with_findings']} with findings; "
        + ", ".join(f"{k}={v}" for k, v in sev.items()),
        file=sys.stderr,
    )

    if args.check:
        if args.max_blocker is not None and sev.get("blocker", 0) > args.max_blocker:
            print(
                f"FAIL: blocker {sev.get('blocker', 0)} > max {args.max_blocker}", file=sys.stderr
            )
            return 1
        if args.max_major is not None and sev.get("major", 0) > args.max_major:
            print(f"FAIL: major {sev.get('major', 0)} > max {args.max_major}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
