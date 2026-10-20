"""Pull fabric candidates out of a use-case sidecar without guessing.

Sourcetypes count only from an explicit ``sourcetype=`` token in ``spl``,
``cimSpl``, or ``dataSources``, or from a quoted sourcetype in
``dataSources``. Wildcards and tokens that are not sourcetype names are
returned as ambiguous candidates.
"""

from __future__ import annotations

import re
from typing import Any

_SOURCETYPE_EQ = re.compile(
    r"""sourcetype\s*=\s*(?:`([^`\n]+)`|"([^"\n]+)"|'([^'\n]+)'|([^\s|,;)\]}]+))""",
    re.IGNORECASE,
)
_QUOTED = re.compile(r"`([^`\n]+)`|\"([^\"\n]+)\"|'([^'\n]+)'")
_DATAMODEL = re.compile(
    r"datamodel\s*=\s*([A-Za-z][A-Za-z0-9_]*)(?:\.([A-Za-z][A-Za-z0-9_]*))?",
    re.IGNORECASE,
)
_SPLUNKBASE_ID = re.compile(
    r"(?:splunkbase(?:\.splunk\.com/app)?\s*[/\s]*|Splunkbase\s+)(\d{3,6})",
    re.IGNORECASE,
)
_TA_TOKEN = re.compile(r"(?<![A-Za-z0-9_])((?:TA-|Splunk_TA_|SA-)[A-Za-z0-9_-]+)")
_TOKEN_OK = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{1,80}$")
_FIELD_DOT = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\.([A-Za-z][A-Za-z0-9_]*)\b")

# Words that show up after sourcetype= when the search is a fragment, not a name.
_NOT_SOURCETYPES = frozenset(
    {
        "sourcetype",
        "source",
        "index",
        "host",
        "eval",
        "stats",
        "where",
        "search",
        "table",
        "rename",
        "rex",
        "or",
        "and",
        "not",
        "by",
        "as",
        "the",
        "from",
        "into",
        "over",
        "null",
        "none",
        "n/a",
        "na",
        "tbd",
        "unknown",
        "various",
        "multiple",
        "any",
    }
)


def _pick(match: re.Match[str]) -> str:
    return next(group for group in match.groups() if group)


def _looks_like_address(token: str) -> bool:
    """MAC addresses and IPv6 literals are not sourcetype names."""
    parts = token.split(":")
    if len(parts) < 3:
        return False
    return all(re.fullmatch(r"[0-9a-fA-F]{0,4}", part) for part in parts)


def classify_sourcetype_token(raw: str) -> tuple[str, str]:
    """Return ``(kind, value)`` where kind is ``keep`` or ``ambiguous``.

    ``value`` is the stripped token. The caller records a reason for
    ambiguous tokens.
    """
    token = raw.strip().strip("`").strip("\"'")
    token = token.strip()
    if not token:
        return "ambiguous", raw
    lowered = token.casefold()
    if _looks_like_address(token):
        return "ambiguous", token
    if any(char in token for char in "*?$<>{}|[]"):
        return "ambiguous", token
    if " " in token or "\\" in token or "=" in token:
        return "ambiguous", token
    if lowered in _NOT_SOURCETYPES or len(token) < 3:
        return "ambiguous", token
    if not _TOKEN_OK.match(token):
        return "ambiguous", token
    return "keep", token


def sourcetype_candidates(*texts: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Return ``(kept tokens, ambiguous (token, reason) pairs)``."""
    kept: list[str] = []
    ambiguous: list[tuple[str, str]] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for match in _SOURCETYPE_EQ.finditer(text):
            kind, token = classify_sourcetype_token(_pick(match))
            key = token.casefold()
            if key in seen:
                continue
            seen.add(key)
            if kind == "keep":
                kept.append(token)
            else:
                ambiguous.append((token, _sourcetype_reject_reason(token)))
    return kept, ambiguous


def quoted_datasources(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Quoted sourcetypes in ``dataSources`` that are not already ``sourcetype=``.

    A quoted token counts only when it sits near the word sourcetype or
    contains a colon, which is how vendor add-ons name sourcetypes
    (``pan:traffic``). Bare quoted product names stay out of this list.
    """
    if not text:
        return [], []
    kept: list[str] = []
    ambiguous: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in _QUOTED.finditer(text):
        token = _pick(match).strip()
        window_start = max(0, match.start() - 48)
        window = text[window_start : match.end() + 16].casefold()
        looks_named = ":" in token or "sourcetype" in window
        if not looks_named:
            continue
        kind, cleaned = classify_sourcetype_token(token)
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        if kind == "keep":
            kept.append(cleaned)
        else:
            reason = _sourcetype_reject_reason(cleaned)
            if reason == "not-a-sourcetype-token":
                reason = "quoted-not-a-sourcetype"
            ambiguous.append((cleaned, reason))
    return kept, ambiguous


def _sourcetype_reject_reason(token: str) -> str:
    if _looks_like_address(token):
        return "looks-like-address"
    if any(char in token for char in "*?"):
        return "wildcard"
    return "not-a-sourcetype-token"


def datamodel_refs(text: str) -> list[tuple[str, str | None]]:
    """Return ``(Model, Dataset|None)`` pairs from ``datamodel=`` clauses."""
    if not text:
        return []
    found: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for match in _DATAMODEL.finditer(text):
        pair = (match.group(1), match.group(2))
        if pair not in seen:
            seen.add(pair)
            found.append(pair)
    return found


def dotted_fields(text: str) -> list[tuple[str, str]]:
    """Return ``Dataset.field`` pairs written in SPL or requiredFields."""
    if not text:
        return []
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in _FIELD_DOT.finditer(text):
        pair = (match.group(1), match.group(2))
        if pair not in seen:
            seen.add(pair)
            found.append(pair)
    return found


def splunkbase_ids(*texts: str) -> list[int]:
    found: list[int] = []
    seen: set[int] = set()
    for text in texts:
        if not text:
            continue
        for match in _SPLUNKBASE_ID.finditer(text):
            value = int(match.group(1))
            if value not in seen:
                seen.add(value)
                found.append(value)
    return found


def ta_tokens(*texts: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for match in _TA_TOKEN.finditer(text):
            token = match.group(1)
            key = token.casefold()
            if key not in seen:
                seen.add(key)
                found.append(token)
    return found


def as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
