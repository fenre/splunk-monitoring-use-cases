#!/usr/bin/env python3
"""Phase 7.x — plain-language ``grandmaExplanation`` generator for UC sidecars.

PROBLEM (Apr 2026):
    The non-technical view has only partial coverage: ``non-technical-view.js``
    ships a curated ``why`` line for ~621 of 6,472 UCs (roughly 10 %) and the
    UC detail panel / UC cards / search results / recently-added list all
    still render the technical ``description``/``value`` copy even when
    non-technical mode is on. Users in non-technical mode therefore see
    strings like "tstats over datamodel=Endpoint" and "MITRE T1078" the
    instant they click into any UC.

FIX:
    Add a first-class, schema-validated ``grandmaExplanation`` string on
    every UC sidecar (one to three sentences, no jargon, "we" voice).
    This generator is its sole writer. It produces deterministic baseline
    text from the already-curated ``title`` / ``description`` / ``value``
    fields (plus ``monitoringType`` and the parent category title) using a
    conservative rule-based rewriter that strips acronyms, code fences,
    clause numbers, and unit labels, then rephrases in first-person
    plural. The output is designed to be "good enough to ship" even when
    no human polishes it — curators can hand-edit any UC afterwards, and
    the generator will not overwrite existing non-empty values unless
    ``--force`` is passed.

CONTRACT:
    - Deterministic: byte-for-byte identical output on re-runs at the same
      catalogue state. Sorted outputs, stable field order (same
      ``_SIDECAR_FIELD_ORDER`` convention as scripts/generate_equipment_tags.py).
    - Curator-respecting: a non-empty existing ``grandmaExplanation`` is
      never touched unless ``--force`` is passed. Curators can edit freely.
    - Schema-compliant: output is always 20..400 chars per
      ``schemas/uc.schema.json`` (v1.5.0+). The generator falls back to a
      short safe sentence if the composed text would violate the bounds.
    - Idempotent: rerunning without source changes is a no-op.
    - --check mode for CI drift guards (exit 1 + list of UCs missing the
      field, so a PR that adds a new UC without running the generator
      fails fast).
    - No API keys required. Uses the existing ``description``/``value``
      text which is already curator-authored; the rewriter is a small
      vocabulary of drop-list patterns + simple voice conversions.

USAGE:
    scripts/generate_grandma_explanations.py              # write missing fields
    scripts/generate_grandma_explanations.py --check      # exit 1 on drift
    scripts/generate_grandma_explanations.py --force      # overwrite existing
    scripts/generate_grandma_explanations.py --only 1.1.1 # one UC
    scripts/generate_grandma_explanations.py --category 22  # one category
    scripts/generate_grandma_explanations.py --report     # print per-UC status
    scripts/generate_grandma_explanations.py --dry-run    # print changes, write nothing
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# Repo root = this file's parent's parent.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONTENT_ROOT = _REPO_ROOT / "content"
_CATEGORY_META_FILE = "_category.json"

# Canonical sidecar field order. Keep in sync with
# scripts/generate_equipment_tags.py so repeated runs of all generators
# keep sidecars byte-comparable. ``grandmaExplanation`` slots in just
# after ``value`` — right between the two "why does this matter" fields
# (``description``, ``value``) and the "how do we build it" fields
# (``implementation``, ``detailedImplementation``).
_SIDECAR_FIELD_ORDER: Tuple[str, ...] = (
    "$schema",
    "id",
    "title",
    "criticality",
    "difficulty",
    "wave",
    "prerequisiteUseCases",
    "subcategory",
    "monitoringType",
    "splunkPillar",
    "industry",
    "owner",
    "controlFamily",
    "exclusions",
    "evidence",
    "compliance",
    "controlTest",
    "dataSources",
    "app",
    "spl",
    "cimSpl",
    "cimModels",
    "dataModelAcceleration",
    "description",
    "value",
    "grandmaExplanation",
    "implementation",
    "detailedImplementation",
    "scriptExample",
    "visualization",
    "references",
    "knownFalsePositives",
    "mitreAttack",
    "detectionType",
    "securityDomain",
    "requiredFields",
    "equipment",
    "equipmentModels",
    "hardware",
    "telcoUseCase",
    "status",
    "lastReviewed",
    "splunkVersions",
    "reviewer",
    "premiumApps",
    "attackTechnique",
)

# Schema contract — keep in sync with schemas/uc.schema.json.
_MIN_LEN = 20
_MAX_LEN = 400

# ---------------------------------------------------------------------------
# Jargon and acronym clean-up
# ---------------------------------------------------------------------------

# Acronyms / tool names that should never appear in non-technical copy.
# Patterns are case-insensitive; surrounding whitespace is handled by the
# regex join. Each entry maps a source pattern to either an empty
# replacement (drop the token) or a plain-language phrase.
_JARGON_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    # Splunk product names / acronyms — drop parenthetical mentions.
    (r"\bSplunk\s+(Enterprise\s+Security|ES)\b", "our monitoring platform"),
    (r"\bSplunk\s+ITSI\b", "our monitoring platform"),
    (r"\bSplunk\s+SOAR\b", "our automation platform"),
    (r"\bSplunk\s+Enterprise\b", "our monitoring platform"),
    (r"\bSplunk\s+Cloud\b", "our monitoring platform"),
    (r"\bSplunk\b", "our monitoring platform"),
    # Query / data-model jargon
    (r"\btstats\b", "a fast search"),
    (r"\bSPL\b", "a search"),
    (r"\bCIM\b", ""),
    (r"\bdata\s*model\b", "a summary"),
    (r"\bdatamodel\b", "a summary"),
    (r"\bsourcetype(?:s)?\b", "log type"),
    (r"\bsource\s+type(?:s)?\b", "log type"),
    (r"\bindex(?:es)?\b", "data"),
    (r"\bforwarder(?:s)?\b", "agent"),
    (r"\bUniversal\s+Forwarder(?:s)?\b", "agent"),
    (r"\bHeavy\s+Forwarder(?:s)?\b", "agent"),
    (r"\bHEC\b", ""),
    (r"\bHTTP\s+Event\s+Collector\b", ""),
    (r"\bsummariesonly\b", ""),
    # MITRE / attack taxonomy
    (r"\bMITRE\s+ATT&CK\b", "known attack techniques"),
    (r"\bMITRE\b", "known attack techniques"),
    (r"\bATT&CK\b", "known attack techniques"),
    (r"\bT\d{4}(?:\.\d{3})?\b", ""),
    # Add-ons / TAs
    (r"\bTA[-_][A-Za-z0-9_-]+\b", ""),
    (r"\b(?:add[-\s]?on|Splunk[-_]TA[-_][A-Za-z0-9_-]+)\b", ""),
    # OS / infra acronyms that sound scary to non-technical folks
    (r"\bOCSF\b", ""),
    (r"\bOSCAL\b", ""),
    (r"\bCSF\b", ""),
    # OT / industrial
    (r"\bOPC\s*UA\b", "our sensors"),
    (r"\bModbus\b", "our sensors"),
    (r"\bBACnet\b", "our sensors"),
    (r"\bSNMP\b", "network signals"),
    (r"\bMQTT\b", "sensor messages"),
    # Regulation clause references (keep regulation name, drop the numbers)
    (r"\b(Arts?\.|Articles?|Clauses?|Sections?|§)\s*\d+(?:[.\-]\d+)*\b", ""),
    (r"\bAnnex\s+[IVXLCDM]+\b", ""),
    # Additional technical acronyms / protocols that slip through
    (r"\bRADIUS\b", ""),
    (r"\bLDAP\b", ""),
    (r"\bSAML\b", ""),
    (r"\bOAuth\b", ""),
    (r"\bDNS\b", ""),
    (r"\bDHCP\b", ""),
    (r"\bVPN\b", "remote access"),
    (r"\bSSH\b", "remote login"),
    (r"\bRDP\b", "remote desktop"),
    (r"\bICMP\b", ""),
    (r"\bNTP\b", ""),
    (r"\bIAM\b", "access control"),
    (r"\bIDS\b", ""),
    (r"\bIPS\b", ""),
    (r"\bSIEM\b", "our monitoring platform"),
    (r"\bSOAR\b", ""),
    (r"\bNDR\b", ""),
    (r"\bEDR\b", ""),
    (r"\bXDR\b", ""),
    (r"\bAPI(?:s)?\b", ""),
    (r"\bAPT(?:s)?\b", "attackers"),
    (r"\bDDoS\b", "overload attacks"),
    (r"\bIoC(?:s)?\b", "attacker signals"),
    (r"\bIOC(?:s)?\b", "attacker signals"),
    (r"\bTTP(?:s)?\b", "attack patterns"),
    (r"\bCVE[-_]\d+[-_]\d+\b", ""),
    (r"\bSSN(?:s)?\b", "government IDs"),
    (r"\bPII\b", "personal data"),
    (r"\bPHI\b", "health data"),
    (r"\bPCI(?:-DSS)?\b", ""),
    (r"\bSOX\b", ""),
    (r"\bMFA\b", "multi-factor sign-in"),
    (r"\b2FA\b", "multi-factor sign-in"),
    (r"\bSSO\b", "single sign-in"),
    (r"\bTLS\b", "secure connections"),
    (r"\bSSL\b", "secure connections"),
    (r"\bVLAN(?:s)?\b", "network segments"),
    (r"\bNAT\b", ""),
    (r"\bBGP\b", ""),
    (r"\bOSPF\b", ""),
    (r"\bPKI\b", "digital certificates"),
    (r"\bKMS\b", ""),
    (r"\bHSM\b", ""),
    (r"\bIPv[46]\b", ""),
    # Performance / business acronyms
    (r"\bat\s+the\s+P\d{2,3}(?:\s*/\s*P\d{2,3})?\s+level\b", ""),
    (r"\bP\d{2,3}(?:\s*/\s*P\d{2,3})?\s+(?:latency|performance)\b", "slowness"),
    (r"\bP\d{2,3}(?:\s*/\s*P\d{2,3})?\b", ""),
    (r"\bSLA(?:s)?\b", "service promises"),
    (r"\bSLO(?:s)?\b", "service goals"),
    (r"\bKPI(?:s)?\b", "key numbers"),
    (r"\bROI\b", "return on investment"),
    (r"\bRTO\b", "recovery time"),
    (r"\bRPO\b", "recovery point"),
    # Cloud / infra acronyms
    (r"\bIAM\b", "access control"),
    (r"\bEC2\b", "cloud servers"),
    (r"\bS3\b", "cloud storage"),
    (r"\bRDS\b", "cloud databases"),
    (r"\bK8s\b", "clusters"),
    (r"\bGKE\b", "clusters"),
    (r"\bAKS\b", "clusters"),
    (r"\bEKS\b", "clusters"),
    (r"\bHVAC\b", "heating and cooling"),
    # Filler
    (r"\bvia\b", "using"),
    (r"\be\.g\.,?\s*", ""),
    (r"\bi\.e\.,?\s*", ""),
    # Dangling prepositions left over after clause/article drops
    (r"\b(?:under|per|for|in|during|against)\s*([.\-—,;:])", r"\1"),
    (r"\b(?:under|per|against)\s+(so\b|because\b|when\b|and\b|or\b|to\b)", r"\1"),
    (r"\s+(the|a|an)\s+([.\-—,;:])", r"\2"),
)

_COMPILED_REPLACEMENTS: Tuple[Tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pat, flags=re.IGNORECASE), repl)
    for pat, repl in _JARGON_REPLACEMENTS
)

# Strip backtick-fenced code and inline code spans entirely.
_CODE_FENCE_RE = re.compile(r"```.*?```", flags=re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
# Strip markdown link syntax, keep the anchor text.
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
# Collapse runs of whitespace.
_WHITESPACE_RE = re.compile(r"\s+")
# Collapse punctuation noise like ", ," / "  ." / " ," left behind after
# drops.
_PUNCT_NOISE_RE = re.compile(r"\s+([,.;:!?])")
_DOUBLE_PUNCT_RE = re.compile(r"([,.;:])\1+")
_EMPTY_PARENS_RE = re.compile(r"\(\s*\)")
_TRAILING_COMMAS_RE = re.compile(r",+\s*([.?!])")

# "Detects" → "We catch". Rewrites at the very front of a sentence only;
# avoids accidentally rewording the middle of technical paragraphs.
_VERB_REWRITES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Detects\s+", re.IGNORECASE), "We catch "),
    (re.compile(r"^Identifies\s+", re.IGNORECASE), "We spot "),
    (re.compile(r"^Monitors\s+", re.IGNORECASE), "We keep an eye on "),
    (re.compile(r"^Tracks\s+", re.IGNORECASE), "We track "),
    (re.compile(r"^Alerts\s+on\s+", re.IGNORECASE), "We warn you about "),
    (re.compile(r"^Flags\s+", re.IGNORECASE), "We flag "),
    (re.compile(r"^Prevents\s+", re.IGNORECASE), "We help you prevent "),
    (re.compile(r"^Ensures\s+", re.IGNORECASE), "We help you make sure "),
    (re.compile(r"^Enables\s+", re.IGNORECASE), "We let you "),
    (re.compile(r"^Provides\s+", re.IGNORECASE), "We give you "),
    (re.compile(r"^Captures\s+", re.IGNORECASE), "We record "),
    (re.compile(r"^Reports\s+", re.IGNORECASE), "We report "),
    (re.compile(r"^Validates\s+", re.IGNORECASE), "We check "),
    (re.compile(r"^Verifies\s+", re.IGNORECASE), "We check "),
    (re.compile(r"^Baselines\s+", re.IGNORECASE), "We learn normal "),
    (re.compile(r"^Trends\s+", re.IGNORECASE), "We track changes in "),
)

# Category-flavoured fallback sentences when the rewriter can't produce
# a usable sentence from description/value. Keyed by category id (int).
# First entry is the generic; second is the "so that" clause.
_CATEGORY_FALLBACK: Dict[int, Tuple[str, str]] = {
    1: ("We keep an eye on your servers", "so you find out before users do when something is slowing down or breaking."),
    2: ("We watch your virtual machines and hosts", "so you catch performance or capacity problems before they hurt real work."),
    3: ("We watch your containers and clusters", "so you know when an app is crashing, stuck, or running somewhere it should not."),
    4: ("We watch your cloud accounts", "so risky changes, runaway spending, and suspicious logins do not go unnoticed."),
    5: ("We watch your network gear", "so outages, slowdowns, and risky changes get flagged in time to act."),
    6: ("We watch your storage and backups", "so you know that your data is safe, backed up, and actually restorable."),
    7: ("We watch your databases and data platforms", "so slow queries, failed backups, and odd changes surface early."),
    8: ("We watch your applications", "so broken requests, slow pages, and errors get caught before customers complain."),
    9: ("We watch how people sign in and use their accounts", "so we can catch stolen logins, risky access, and sign-ins that skip the extra security check."),
    10: ("We watch your security tools and controls", "so we know when protection is off, out of date, or bypassed."),
    11: ("We watch your email and collaboration tools", "so phishing, data leaks, and account misuse do not slip through."),
    12: ("We watch your build and deploy pipelines", "so code changes that fail, leak secrets, or skip checks are caught early."),
    13: ("We watch the health of the monitoring itself", "so you always trust the numbers you are looking at."),
    14: ("We watch your IoT and factory-floor devices", "so faults, tampering, and safety issues are spotted right away."),
    15: ("We watch your data-centre facility", "so power, cooling, and physical access problems are found before they hurt uptime."),
    16: ("We watch your IT service-management tooling", "so tickets, changes, and incidents are on track and nothing is silently missed."),
    17: ("We watch your zero-trust and network-security controls", "so unsafe traffic and policy bypasses are caught quickly."),
    18: ("We watch your data-centre network fabric", "so traffic problems, routing mistakes, and risky changes surface fast."),
    19: ("We watch your hyper-converged and compute infrastructure", "so hardware faults and capacity problems do not take services down."),
    20: ("We watch your cost and capacity", "so you know where money and resources are being wasted or running out."),
    21: ("We watch the systems that run your industry's daily operations", "so the things customers and regulators care about stay running and accountable."),
    22: ("We make it easy to prove, at audit time, that the rules are being followed", "so you can show exactly what is being watched and when something went wrong."),
    23: ("We watch the business metrics that matter to the board", "so revenue, usage, and customer trends are visible in near-real-time."),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iter_sidecars() -> Iterable[Tuple[Path, int]]:
    """Yield every canonical UC sidecar together with its category id.

    Returns (path, category_id). Category id is read from the parent
    directory's ``_category.json`` so we can tailor the fallback sentence
    without re-parsing every UC's ``id`` field.
    """
    if not _CONTENT_ROOT.is_dir():
        return
    for cat_dir in sorted(p for p in _CONTENT_ROOT.iterdir() if p.is_dir()):
        meta_path = cat_dir / _CATEGORY_META_FILE
        cat_id: Optional[int] = None
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                cat_id = int(meta.get("id"))
            except (OSError, ValueError, TypeError):
                cat_id = None
        for uc_path in sorted(cat_dir.glob("UC-*.json")):
            yield uc_path, cat_id if cat_id is not None else 0


def _read_sidecar(path: Path) -> Optional[Dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARN: could not parse {path.relative_to(_REPO_ROOT)}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict) or "id" not in data:
        return None
    return data


_GRAMMAR_FIXUPS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    # "government IDs patterns" → "government ID patterns" (when a
    # multi-word replacement ending in a plural is followed by another
    # noun modifier).
    (re.compile(r"\bgovernment\s+IDs\s+patterns\b"), "government-ID patterns"),
    (re.compile(r"\bpersonal\s+data\s+(?:information|data)\b"), "personal data"),
    (re.compile(r"\bhealth\s+data\s+(?:information|data|records)\b"), "health data"),
    (re.compile(r"\bmulti-factor\s+sign-in\s+authentication\b"), "multi-factor sign-in"),
    (re.compile(r"\bservice\s+promises\s+commitments?\b"), "service promises"),
    (re.compile(r"\bservice\s+promises\s+agreements?\b"), "service promises"),
    (re.compile(r"\baccess\s+control\s+controls?\b"), "access controls"),
    # Strip "... and " at end of sentences caused by dropped trailing
    # acronyms.
    (re.compile(r"\s*(?:and|or)\s*[.?!]\s*$"), "."),
    # Collapse double spaces around em-dashes.
    (re.compile(r"\s*—\s*"), " — "),
    # Remove isolated orphans like " - " at end of string
    (re.compile(r"\s[-—]\s*$"), "."),
)


def _strip_jargon(text: str) -> str:
    """Apply the cleanup rules; see _JARGON_REPLACEMENTS above."""
    if not text:
        return ""
    out = _CODE_FENCE_RE.sub(" ", text)
    out = _INLINE_CODE_RE.sub(" ", out)
    out = _MD_LINK_RE.sub(r"\1", out)
    for pat, repl in _COMPILED_REPLACEMENTS:
        out = pat.sub(repl, out)
    out = _EMPTY_PARENS_RE.sub("", out)
    out = _WHITESPACE_RE.sub(" ", out).strip()
    out = _PUNCT_NOISE_RE.sub(r"\1", out)
    out = _DOUBLE_PUNCT_RE.sub(r"\1", out)
    out = _TRAILING_COMMAS_RE.sub(r"\1", out)
    out = _WHITESPACE_RE.sub(" ", out).strip()
    for pat, repl in _GRAMMAR_FIXUPS:
        out = pat.sub(repl, out)
    out = _WHITESPACE_RE.sub(" ", out).strip()
    return out


def _first_sentence(text: str) -> str:
    if not text:
        return ""
    # Find the first sentence terminator that is not inside a number
    # (e.g. "v1.2").
    m = re.search(r"[.!?](?=\s|$)", text)
    first = text[: m.end()].strip() if m else text.strip()
    # If the first sentence itself is too long for a 1-line summary,
    # look for a semicolon or " — " earlier in the sentence and truncate
    # there (treating the clause after it as elaboration the non-technical
    # reader doesn't need).
    if len(first) > 200:
        for sep in (";", " — ", " - "):
            if sep in first:
                head, _, _ = first.partition(sep)
                head = head.strip().rstrip(",;:")
                if _MIN_LEN <= len(head) <= 200:
                    first = head + "."
                    break
    return first


def _rewrite_voice(sentence: str) -> str:
    if not sentence:
        return ""
    for pat, repl in _VERB_REWRITES:
        new = pat.sub(repl, sentence)
        if new != sentence:
            return new
    return sentence


def _compose(title: str, source_text: str, cat_id: int) -> str:
    """Compose a single-sentence plain-language summary.

    Strategy:
        1. Strip jargon/acronyms/code/links from the source text.
        2. Keep the first sentence.
        3. Rewrite the leading verb in "we" voice if we recognise the
           pattern.
        4. If the result is empty or too short (<20 chars), use the
           per-category fallback sentence.
    """
    cleaned = _strip_jargon(source_text or "")
    first = _first_sentence(cleaned)
    first = _rewrite_voice(first)
    if first and len(first) >= _MIN_LEN:
        # Ensure it ends with a period/!/?.
        if not re.search(r"[.!?]$", first):
            first = first.rstrip(",;:") + "."
    else:
        first = ""

    generic, because = _CATEGORY_FALLBACK.get(
        cat_id,
        ("We watch this part of your environment", "so problems are spotted early."),
    )
    fallback = f"{generic} — {because}"
    if not first:
        first = fallback

    # If we have the composed sentence but it's missing the "why it
    # matters" flavour the curated views expect, append the category
    # "because" clause as long as we stay under _MAX_LEN.
    if first and not first.lower().endswith(because.lower()):
        candidate = f"{first.rstrip('.')} — {because}"
        if len(candidate) <= _MAX_LEN and len(first) < _MAX_LEN - 40:
            first = candidate

    # Final safety: enforce schema bounds.
    if len(first) < _MIN_LEN:
        first = fallback
    if len(first) > _MAX_LEN:
        # Trim on word boundaries.
        trimmed = first[: _MAX_LEN].rsplit(" ", 1)[0].rstrip(",;:")
        if not re.search(r"[.!?]$", trimmed):
            trimmed += "."
        first = trimmed
    # Capitalise first letter.
    if first and first[0].isalpha() and first[0].islower():
        first = first[0].upper() + first[1:]
    return first


def _compute_grandma(sidecar: Dict, cat_id: int) -> str:
    """Deterministic baseline for a single UC sidecar."""
    title = str(sidecar.get("title") or "").strip()
    # Prefer ``value`` (business-facing) over ``description`` (occasionally
    # duplicated but authored for a technical audience). Fall back to
    # whichever is present.
    value = str(sidecar.get("value") or "").strip()
    description = str(sidecar.get("description") or "").strip()
    source = value or description
    return _compose(title, source, cat_id)


def _reorder_sidecar(sidecar: Dict) -> Dict:
    """Return a dict with keys in _SIDECAR_FIELD_ORDER then sorted extras."""
    ordered: Dict = {}
    for k in _SIDECAR_FIELD_ORDER:
        if k in sidecar:
            ordered[k] = sidecar[k]
    for k in sorted(sidecar.keys()):
        if k not in ordered:
            ordered[k] = sidecar[k]
    return ordered


def _apply(sidecar: Dict, value: str) -> Dict:
    out = dict(sidecar)
    out["grandmaExplanation"] = value
    return _reorder_sidecar(out)


def _serialise(sidecar: Dict) -> str:
    return json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _matches_filter(
    uc_id: str, cat_id: int, only: Optional[str], category: Optional[int]
) -> bool:
    if only and uc_id != only:
        return False
    if category is not None and cat_id != category:
        return False
    return True


def _process(
    *,
    check: bool,
    force: bool,
    dry_run: bool,
    only: Optional[str],
    category: Optional[int],
    report: bool,
) -> int:
    processed = 0
    written = 0
    missing: List[str] = []
    changed_paths: List[Path] = []

    for path, cat_id in _iter_sidecars():
        sidecar = _read_sidecar(path)
        if sidecar is None:
            continue
        uc_id = str(sidecar.get("id") or "")
        if not _matches_filter(uc_id, cat_id, only, category):
            continue
        processed += 1

        existing = sidecar.get("grandmaExplanation") or ""
        if isinstance(existing, str) and existing.strip() and not force:
            if report:
                print(f"  kept UC-{uc_id}: {existing[:60]}...")
            continue

        new_value = _compute_grandma(sidecar, cat_id)
        if not new_value or len(new_value) < _MIN_LEN:
            # Shouldn't happen — _compose always produces at least the
            # category fallback — but guard regardless.
            missing.append(uc_id)
            continue

        if isinstance(existing, str) and existing.strip() == new_value and not force:
            continue

        changed_paths.append(path)
        if check:
            missing.append(uc_id)
            continue
        if dry_run:
            print(f"  would set UC-{uc_id}: {new_value}")
            continue
        new_sidecar = _apply(sidecar, new_value)
        path.write_text(_serialise(new_sidecar), encoding="utf-8")
        written += 1
        if report:
            print(f"  set UC-{uc_id}: {new_value}")

    if check:
        if missing:
            print(
                f"FATAL: {len(missing)} UCs have no grandmaExplanation "
                "(or produce drift). Re-run scripts/generate_grandma_explanations.py "
                "to refresh.",
                file=sys.stderr,
            )
            for uid in missing[:25]:
                print(f"  UC-{uid}", file=sys.stderr)
            if len(missing) > 25:
                print(f"  ... and {len(missing) - 25} more", file=sys.stderr)
            return 1
        print(f"OK: {processed} UCs have an up-to-date grandmaExplanation.")
        return 0

    if dry_run:
        print(f"DRY RUN: would update {len(changed_paths)} of {processed} sidecars.")
        return 0

    print(f"Processed {processed} sidecars, updated {written}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing; exit 1 if any UC sidecar would change.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-empty grandmaExplanation values.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the new values that would be written; do not touch the filesystem.",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Process only the UC with this id (e.g. '1.1.1').",
    )
    parser.add_argument(
        "--category",
        type=int,
        default=None,
        help="Process only UCs in this category (e.g. 22).",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print per-UC status (kept/set) after running.",
    )
    args = parser.parse_args()

    if args.check and (args.force or args.dry_run):
        print("ERROR: --check is mutually exclusive with --force / --dry-run.", file=sys.stderr)
        return 2

    return _process(
        check=args.check,
        force=args.force,
        dry_run=args.dry_run,
        only=args.only,
        category=args.category,
        report=args.report,
    )


if __name__ == "__main__":
    sys.exit(main())
