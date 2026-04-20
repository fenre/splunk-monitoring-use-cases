"""Reusable parser + renderer for `use-cases/cat-*.md` files.

Phase 1.3 migration tooling.

The catalogue markdown files use a repeating block shape:

    ### UC-<id> · <title> [(<clause hint>)]
    - **Criticality:** <emoji> <label>
    - **Difficulty:** <emoji> <label>
    - **Monitoring type:** <csv>
    [...optional fields...]
    - **References:** [title](url), [title](url)

This module exposes two symmetric operations:

* ``parse_uc_block(raw_md_block) -> dict`` – converts a raw markdown block
  (one UC) into a structured dict whose keys line up with
  ``schemas/uc.schema.json``.
* ``render_uc_to_markdown(uc_dict, original_subcategory=None) -> str`` –
  renders the dict back to markdown. When the transform is lossless, the
  rendered markdown equals the original (after applying
  :func:`normalize_for_diff`).

The migration driver uses both directions to run a zero-narrative-loss diff
gate: every UC we migrate must round-trip to byte-identical markdown after
normalisation.

Security note (rule codeguard-0-input-validation-injection):
-----------------------------------------------------------
Regex patterns that parse user-influenced input are anchored, bounded, and
avoid catastrophic-backtracking classes. No dynamic ``re.compile`` is done
on catalogue content. File writes use ``pathlib`` with an explicit target
directory; no shell is invoked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enum-dimension lookups: markdown label -> schema value
# ---------------------------------------------------------------------------

CRITICALITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

DIFFICULTY_EMOJI = {
    "beginner": "🟢",
    "intermediate": "🔵",
    "advanced": "🟠",
    "expert": "🔴",
}

# Reverse lookups are built from the forward dicts so we cannot drift.
_CRIT_LABELS_BY_EMOJI = {v: k for k, v in CRITICALITY_EMOJI.items()}
_DIFF_LABELS_BY_EMOJI = {v: k for k, v in DIFFICULTY_EMOJI.items()}


# ---------------------------------------------------------------------------
# Field ordering: canonical order produced by ``render_uc_to_markdown``.
# ---------------------------------------------------------------------------

CANONICAL_FIELD_ORDER: Tuple[str, ...] = (
    "criticality",
    "difficulty",
    "monitoringType",
    "mitreAttack",
    "industry",
    "splunkPillar",
    "regulations",
    "value",
    "app",
    "premiumApps",
    "dataSources",
    "spl",
    "implementation",
    "visualization",
    "cimModels",
    "cimSpl",
    "knownFalsePositives",
    "references",
)


# Labels are what appear inside the ``- **LABEL:**`` prefix.
FIELD_LABELS: Dict[str, str] = {
    "criticality": "Criticality",
    "difficulty": "Difficulty",
    "monitoringType": "Monitoring type",
    "mitreAttack": "MITRE ATT&CK",
    "industry": "Industry",
    "splunkPillar": "Splunk Pillar",
    "regulations": "Regulations",
    "value": "Value",
    "app": "App/TA",
    "premiumApps": "Premium Apps",
    "dataSources": "Data Sources",
    "spl": "SPL",
    "implementation": "Implementation",
    "visualization": "Visualization",
    "cimModels": "CIM Models",
    "cimSpl": "CIM SPL",
    "knownFalsePositives": "Known false positives",
    "references": "References",
}

# Reverse: label -> key (case-insensitive). We lowercase both at lookup time.
LABEL_TO_KEY: Dict[str, str] = {v.lower(): k for k, v in FIELD_LABELS.items()}


# ---------------------------------------------------------------------------
# Premium app aliasing
# ---------------------------------------------------------------------------
# The schema's ``premiumApps`` enum is strict (short canonical names). The
# markdown sometimes uses the long form ("Splunk IT Service Intelligence
# (ITSI)") or attaches qualifiers ("Splunk Enterprise Security (optional,
# for asset/identity context)"). We canonicalise the machine-readable name
# while preserving the original spelling in ``displayName``/``note`` so
# markdown round-trip stays byte-identical.

_PREMIUM_APP_CANONICAL = {
    "splunk enterprise security": "Splunk Enterprise Security",
    "splunk es": "Splunk Enterprise Security",
    "splunk it service intelligence": "Splunk ITSI",
    "splunk it service intelligence (itsi)": "Splunk ITSI",
    "splunk itsi": "Splunk ITSI",
    "splunk soar": "Splunk SOAR",
    "splunk user behavior analytics": "Splunk User Behavior Analytics",
    "splunk user behavior analytics (uba)": "Splunk User Behavior Analytics",
    "splunk uba": "Splunk User Behavior Analytics",
    "splunk app for pci compliance": "Splunk App for PCI Compliance",
}


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# UC header line: "### UC-22.1.1 · Title ..."
#   Group(1) = id (digits.digits.digits)
#   Group(2) = remainder after " · "
_UC_HEADER_RE = re.compile(r"^###\s+UC-(\d+\.\d+\.\d+)\s+·\s+(.+?)\s*$")

# A "- **Label:**" line where value may be on the same line or a code fence follows.
_FIELD_LINE_RE = re.compile(r"^\s*-\s+\*\*([^*]+?):\*\*\s*(.*)\s*$")

# Markdown link "[title](url)"
_MD_LINK_RE = re.compile(r"\[([^\]]+?)\]\(([^)]+)\)")

# Subcategory header: "### 22.N Name"
_SUBCAT_HEADER_RE = re.compile(r"^###\s+(\d+\.\d+)\s+(.+?)\s*$")

# Category header: "## 22. Name"
_CAT_HEADER_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")

# Horizontal rule separator
_HRULE_RE = re.compile(r"^---\s*$")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedSubcategory:
    """A single ``### 22.N Name`` subcategory with its two preamble paragraphs."""

    id: str
    name: str
    primary_app_ta: Optional[str] = None
    data_sources_preamble: Optional[str] = None
    ucs: List[Dict] = field(default_factory=list)


@dataclass
class ParsedCategory:
    """Top-level ``## 22. Regulatory and Compliance Frameworks`` block."""

    id: str
    name: str
    subcategories: List[ParsedSubcategory] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public parsing API
# ---------------------------------------------------------------------------

def parse_category_markdown(md_text: str) -> ParsedCategory:
    """Parse the full cat-22 markdown file into a typed tree."""

    lines = md_text.splitlines()
    i = 0
    n = len(lines)

    cat_id: Optional[str] = None
    cat_name: Optional[str] = None
    subcategories: List[ParsedSubcategory] = []
    current_sub: Optional[ParsedSubcategory] = None

    while i < n:
        line = lines[i]

        m = _CAT_HEADER_RE.match(line)
        if m:
            cat_id, cat_name = m.group(1), m.group(2)
            i += 1
            continue

        m = _SUBCAT_HEADER_RE.match(line)
        if m:
            current_sub = ParsedSubcategory(id=m.group(1), name=m.group(2))
            subcategories.append(current_sub)
            i += 1

            while i < n:
                ln = lines[i]
                if ln.startswith("### UC-") or _SUBCAT_HEADER_RE.match(ln):
                    break
                ms = re.match(r"^\*\*Primary App/TA:\*\*\s*(.+)$", ln)
                if ms and current_sub.primary_app_ta is None:
                    current_sub.primary_app_ta = ms.group(1).strip()
                md = re.match(r"^\*\*Data Sources:\*\*\s*(.+)$", ln)
                if md and current_sub.data_sources_preamble is None:
                    current_sub.data_sources_preamble = md.group(1).strip()
                i += 1
            continue

        m = _UC_HEADER_RE.match(line)
        if m:
            block_lines: List[str] = [line]
            i += 1
            while i < n:
                ln = lines[i]
                if _UC_HEADER_RE.match(ln) or _SUBCAT_HEADER_RE.match(ln):
                    break
                if _HRULE_RE.match(ln):
                    i += 1
                    break
                block_lines.append(ln)
                i += 1
            uc_dict = parse_uc_block("\n".join(block_lines))
            if current_sub is not None:
                current_sub.ucs.append(uc_dict)
            continue

        i += 1

    if cat_id is None or cat_name is None:
        raise ValueError("No '## N. Name' category header found in markdown.")

    return ParsedCategory(id=cat_id, name=cat_name, subcategories=subcategories)


def parse_uc_block(block: str) -> Dict:
    """Parse a single UC block into a dict.

    The dict keys are already schema-aligned (``id``, ``title``,
    ``criticality`` etc.). Field values that appear as comma-separated lists
    in markdown are returned as ``list[str]`` so that downstream validation
    and rendering stay simple.
    """

    lines = block.splitlines()
    if not lines:
        raise ValueError("Empty UC block.")

    header = lines[0]
    m = _UC_HEADER_RE.match(header)
    if not m:
        raise ValueError(f"First line is not a UC header: {header!r}")

    uc_id, title_with_clause = m.group(1), m.group(2)
    title, clause_hint = _split_title_and_clause_hint(title_with_clause)

    uc: Dict = {"id": uc_id, "title": title}
    if clause_hint is not None:
        uc["_clauseHint"] = clause_hint

    i = 1
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        fm = _FIELD_LINE_RE.match(line)
        if not fm:
            i += 1
            continue

        label = fm.group(1).strip()
        value_inline = fm.group(2).strip()
        key = LABEL_TO_KEY.get(label.lower())

        if key is None:
            i += 1
            continue

        if key in ("spl", "cimSpl") and not value_inline:
            code, advance = _consume_consecutive_code_fences(lines, i + 1)
            uc[key] = code
            i = advance
            continue

        if key == "premiumApps":
            uc[key] = _parse_premium_apps(value_inline)
        elif key in ("mitreAttack", "monitoringType", "cimModels"):
            uc[key] = _split_csv(value_inline)
        elif key == "references":
            uc[key] = _parse_references(value_inline)
        else:
            uc[key] = value_inline
        i += 1

    _post_process_enum_fields(uc)
    return uc


# ---------------------------------------------------------------------------
# Public rendering API
# ---------------------------------------------------------------------------

def render_uc_to_markdown(uc: Dict) -> str:
    """Render a parsed UC dict back to markdown.

    The output follows :data:`CANONICAL_FIELD_ORDER`. For UCs whose source
    is already canonical-ordered, the output equals the input (after
    :func:`normalize_for_diff`).
    """

    if "id" not in uc or "title" not in uc:
        raise ValueError("UC dict needs at least 'id' and 'title'.")

    out: List[str] = []
    title = uc["title"]
    if uc.get("_clauseHint"):
        title = f"{title} ({uc['_clauseHint']})"
    out.append(f"### UC-{uc['id']} · {title}")

    for key in CANONICAL_FIELD_ORDER:
        if key not in uc:
            continue
        out.extend(_render_field(key, uc[key]))

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Normalisation for diff gate
# ---------------------------------------------------------------------------

def normalize_for_diff(md_text: str) -> str:
    """Apply idempotent normalisations so that two equivalent markdowns match.

    Only *formatting-only* changes are normalised. Anything that changes
    wording must NOT be masked here – those divergences should surface in
    the migration report for manual review.

    Normalisations:

    * strip trailing whitespace on every line
    * drop blank lines that appear outside a fenced code block – within a UC
      body, the cat-22 source mixes styles (some UCs have a blank line before
      "Known false positives" or after a ```spl fence close, others don't)
      and the two shapes are semantically identical

    Inside a ``` ... ``` fence, whitespace is preserved so that SPL content
    compares exactly.
    """

    lines = [ln.rstrip() for ln in md_text.splitlines()]

    result: List[str] = []
    in_fence = False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            result.append(ln)
            continue
        if ln == "" and not in_fence:
            continue
        result.append(ln)

    while result and result[-1] == "":
        result.pop()

    return "\n".join(result) + "\n"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_title_and_clause_hint(title_with_clause: str) -> Tuple[str, Optional[str]]:
    """Extract a trailing parenthesised clause hint, if present.

    ``"GDPR PII Detection in Application Log Data (Art. 5/6)"`` -> ("GDPR PII
    Detection in Application Log Data", "Art. 5/6").
    """

    s = title_with_clause.rstrip()
    if not s.endswith(")"):
        return s, None

    depth = 0
    open_idx = -1
    for idx in range(len(s) - 1, -1, -1):
        ch = s[idx]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
            if depth == 0:
                open_idx = idx
                break
    if open_idx == -1:
        return s, None
    title = s[:open_idx].rstrip()
    hint = s[open_idx + 1 : -1].strip()
    return title, hint


def _consume_code_fence(lines: List[str], start: int) -> Tuple[str, int]:
    """Collect a single fenced ``` ... ``` block and return (body, next_index)."""

    if start >= len(lines):
        return "", start

    first = lines[start].strip()
    if not first.startswith("```"):
        return "", start

    body: List[str] = []
    i = start + 1
    while i < len(lines):
        if lines[i].strip().startswith("```"):
            i += 1
            return "\n".join(body), i
        body.append(lines[i])
        i += 1
    return "\n".join(body), i


def _consume_consecutive_code_fences(lines: List[str], start: int) -> Tuple[str, int]:
    """Collect one-or-more back-to-back ``` ... ``` blocks.

    Some cat-22 UCs emit two SPL fences under a single ``- **SPL:**`` label
    because the search is two stacked pipelines. To round-trip losslessly,
    we accumulate all consecutive fences (ignoring blank lines between them)
    and return them joined by a fence-close/fence-open pair.
    """

    i = start
    fences: List[str] = []
    while i < len(lines):
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        if i >= len(lines):
            break
        if not lines[i].strip().startswith("```"):
            break
        body, i = _consume_code_fence(lines, i)
        fences.append(body)
    if not fences:
        return "", start
    return "\n```\n```spl\n".join(fences), i


def _split_csv(s: str) -> List[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


def _split_csv_respecting_parens(s: str) -> List[str]:
    """Split on commas *outside* parentheses.

    Used for premium-apps and other fields where a single token may
    legitimately contain a comma inside ``(...)`` (e.g.
    ``Splunk Enterprise Security (optional, for asset/identity context)``).
    """

    tokens: List[str] = []
    buf: List[str] = []
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            tokens.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        tokens.append(tail)
    return [t for t in tokens if t]


_TRAILING_PAREN_RE = re.compile(r"^(?P<base>.+?)\s*\((?P<note>[^()]+)\)\s*$")


def _parse_premium_apps(value_inline: str) -> List:
    """Parse the ``Premium Apps:`` line into schema-shaped items.

    Each comma-separated token becomes either:

    * a plain canonical string (if the source text already matches the
      short enum name, e.g. ``"Splunk ITSI"``); or
    * an object ``{"name", ...}`` with the canonical short name plus a
      ``displayName`` and/or ``note`` preserving the source spelling.

    The goal is zero narrative loss on markdown round-trip while giving
    downstream consumers a clean canonical identifier.
    """

    out: List = []
    for raw in _split_csv_respecting_parens(value_inline):
        base = raw
        note: Optional[str] = None
        m = _TRAILING_PAREN_RE.match(raw)
        if m:
            base_candidate = m.group("base").strip()
            note_candidate = m.group("note").strip()
            if base_candidate.lower() in _PREMIUM_APP_CANONICAL:
                base = base_candidate
                canonical = _PREMIUM_APP_CANONICAL[base_candidate.lower()]
                if note_candidate.lower() == canonical.split()[-1].lower() or (
                    canonical == "Splunk ITSI" and note_candidate.upper() == "ITSI"
                ) or (
                    canonical == "Splunk User Behavior Analytics"
                    and note_candidate.upper() == "UBA"
                ):
                    note = None
                else:
                    note = note_candidate
            else:
                base = base_candidate
                note = note_candidate
        canonical = _PREMIUM_APP_CANONICAL.get(base.lower(), base)
        if raw == canonical:
            out.append(canonical)
            continue
        item: Dict[str, str] = {"name": canonical, "displayName": raw}
        if note is not None:
            item["note"] = note
        out.append(item)
    return out


def _render_premium_apps(items) -> str:
    if not isinstance(items, list):
        items = [items]
    parts: List[str] = []
    for it in items:
        if isinstance(it, str):
            parts.append(it)
            continue
        if not isinstance(it, dict):
            parts.append(str(it))
            continue
        if it.get("displayName"):
            parts.append(it["displayName"])
        elif it.get("note"):
            parts.append(f"{it['name']} ({it['note']})")
        else:
            parts.append(it["name"])
    return ", ".join(parts)


def _parse_references(s: str) -> List[Dict]:
    refs = []
    for link_m in _MD_LINK_RE.finditer(s):
        refs.append({"title": link_m.group(1).strip(), "url": link_m.group(2).strip()})
    if not refs and s.strip():
        refs.append({"url": s.strip()})
    return refs


def _post_process_enum_fields(uc: Dict) -> None:
    if "criticality" in uc:
        uc["criticality"] = _strip_emoji_label(uc["criticality"], _CRIT_LABELS_BY_EMOJI)
    if "difficulty" in uc:
        uc["difficulty"] = _strip_emoji_label(uc["difficulty"], _DIFF_LABELS_BY_EMOJI)


def _strip_emoji_label(value: str, emoji_to_label: Dict[str, str]) -> str:
    parts = value.split(maxsplit=1)
    if not parts:
        return value.lower()
    first = parts[0]
    if first in emoji_to_label:
        label = parts[1].strip() if len(parts) > 1 else emoji_to_label[first].title()
        return label.lower()
    return value.strip().lower()


# ---------------------------------------------------------------------------
# Field rendering
# ---------------------------------------------------------------------------

def _render_field(key: str, value) -> List[str]:
    label = FIELD_LABELS[key]

    if key == "criticality":
        emoji = CRITICALITY_EMOJI.get(str(value).lower(), "")
        return [f"- **{label}:** {emoji} {str(value).title()}".rstrip()]
    if key == "difficulty":
        emoji = DIFFICULTY_EMOJI.get(str(value).lower(), "")
        return [f"- **{label}:** {emoji} {str(value).title()}".rstrip()]
    if key == "premiumApps":
        return [f"- **{label}:** {_render_premium_apps(value)}"]
    if key in ("monitoringType", "mitreAttack", "cimModels"):
        if not isinstance(value, list):
            value = [value]
        return [f"- **{label}:** {', '.join(value)}"]
    if key in ("spl", "cimSpl"):
        body = str(value).rstrip("\n")
        return [f"- **{label}:**", "```spl", body, "```"]
    if key == "references":
        if isinstance(value, list):
            parts = []
            for r in value:
                if isinstance(r, dict) and r.get("title") and r.get("url"):
                    parts.append(f"[{r['title']}]({r['url']})")
                elif isinstance(r, dict) and r.get("url"):
                    parts.append(r["url"])
                elif isinstance(r, str):
                    parts.append(r)
            return [f"- **{label}:** {', '.join(parts)}"]
        return [f"- **{label}:** {value}"]
    return [f"- **{label}:** {value}"]


# ---------------------------------------------------------------------------
# Schema-alignment helper used by the migration driver
# ---------------------------------------------------------------------------

def to_schema_payload(uc: Dict) -> Dict:
    """Return a dict that excludes presentation-only keys (``_clauseHint``)."""
    return {k: v for k, v in uc.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Convenience I/O
# ---------------------------------------------------------------------------

def load_category(path: Path) -> ParsedCategory:
    return parse_category_markdown(path.read_text(encoding="utf-8"))
