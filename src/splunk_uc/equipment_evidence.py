"""Search-evidence helpers for evidence-gated equipment tags.

An equipment registry entry (``tools/build/enrichment.py`` ``EQUIPMENT``)
opts into evidence gating by carrying an ``evidence`` block, on the vendor
entry and on each model::

    "evidence": {
        "sourcetypes": ["cisco:asa*"],   # fnmatch globs, lowercase
        "indexes": ["cisco_aci*"],
        "macros": ["cisco_asa*"],
        "cimModels": ["Network_Traffic"],  # data models the add-on populates
        "references": ["https://splunk.github.io/splunk-add-on-for-cisco-asa/DataTypes/"]
    }

For gated vendors a model tag needs proof in the search itself (``spl`` /
``cimSpl`` / a matching ``splVariants`` entry): a sourcetype, index or
macro that the model produces. A product named in ``app`` only counts when
the search does not name a specific sourcetype of its own (CIM data model,
macro, or generic syslog / SNMP / NetFlow searches). Words in the prose
fields never count.

Used by ``generators.equipment_tags`` (the tag writer) and
``audits.cisco_tag_evidence`` (the CSV work list and the CI gate).
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# Sourcetypes that any vendor can emit; they neither prove nor disprove a
# vendor. Kept deliberately short.
NEUTRAL_SOURCETYPES: tuple[str, ...] = (
    "syslog",
    "syslog:*",
    "snmp",
    "snmp:*",
    "snmptrap*",
    "snmp_ta*",
    "sc4snmp*",
    "radius*",
    "netflow*",
    "ipfix*",
    "sflow*",
    "stream:*",
    "gnmi*",
    "telegraf*",
    "otel*",
    "prometheus*",
    "json",
    "_json",
    "csv",
    "http*",
    "hec*",
    "script*",
    "rest*",
    "metrics*",
    "stash",
)

# Sourcetype / index tokens of vendors that compete with a Cisco product.
# A search that only reads one of these, in a use case whose ``app`` field
# also lists a Cisco product, is a multi-vendor use case that needs a Cisco
# variant (category B / E2) rather than an unrelated mis-tag (category C).
PEER_VENDOR_TOKENS: tuple[str, ...] = (
    "pan:",
    "pan_",
    "paloalto",
    "palo_alto",
    "fgt",
    "fortigate",
    "fortinet",
    "fortianalyzer",
    "fortiweb",
    "cp_log",
    "checkpoint",
    "opsec",
    "juniper",
    "junos",
    "aruba",
    "f5:",
    "f5_",
    "bigip",
    "zscaler",
    "sophos",
    "sonicwall",
    "barracuda",
    "watchguard",
    "netskope",
    "bluecoat",
    "symantec",
    "infoblox",
    "arista",
    "extreme",
    "ruckus",
    "mist",
    "versa",
    "silverpeak",
    "velocloud",
    "avaya",
    "zoom",
    "ms:teams",
    "microsoft:teams",
    "crowdstrike",
    "sentinelone",
    "carbonblack",
    "okta",
    "proofpoint",
    "mimecast",
    "nozomi",
    "claroty",
    "dragos",
    "citrix",
    "netscaler",
    "nsx",
    "nutanix",
    "brocade",
    "hpe",
    "gigamon",
)

_SOURCETYPE_EQ = re.compile(
    r"""(?<![\w.!])sourcetype\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s|)\]"',]+))""",
    re.IGNORECASE,
)
_SOURCETYPE_IN = re.compile(r"(?<![\w.])sourcetype\s+IN\s*\(([^)]*)\)", re.IGNORECASE)
_INDEX_EQ = re.compile(
    r"""(?<![\w.!])index\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s|)\]"',]+))""",
    re.IGNORECASE,
)
_INDEX_IN = re.compile(r"(?<![\w.])index\s+IN\s*\(([^)]*)\)", re.IGNORECASE)
_MACRO = re.compile(r"`([A-Za-z0-9_\-]+)(?:\([^`]*\))?`")
_DATAMODEL = re.compile(
    r"(?:datamodel\s*[=:]|from\s+datamodel|\|\s*datamodel\s|\btstats\b[^|]*\bnodename\s*=)",
    re.IGNORECASE,
)
# Captures ``datamodel=Network_Traffic.All_Traffic``, ``from datamodel Risk``,
# ``datamodel:Change``, and ``| datamodel Authentication``. The caller folds
# a dotted dataset down to the root model.
_DATAMODEL_NAME = re.compile(
    r"""(?ix)
    (?:
        \bdatamodel\s*[=:]\s*["'`]?([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)
      | \bfrom\s+datamodel\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)
      | \|\s*datamodel\s+([A-Za-z_][A-Za-z0-9_]*)
    )
    """
)
_LIST_ITEM = re.compile(r"""\"([^\"]+)\"|'([^']+)'|([^\s,\"']+)""")
# Macros that wrap a CIM / ES accelerated data model search.
_CIM_MACROS: tuple[str, ...] = (
    "summariesonly",
    "security_content_summariesonly",
    "drop_dm_object_name",
    "cim_*",
)
_TOKEN_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"


@dataclass(frozen=True)
class SplEvidence:
    """Data sources a search names explicitly."""

    sourcetypes: frozenset[str] = field(default_factory=frozenset)
    indexes: frozenset[str] = field(default_factory=frozenset)
    macros: frozenset[str] = field(default_factory=frozenset)
    uses_datamodel: bool = False
    datamodels: frozenset[str] = field(default_factory=frozenset)

    @property
    def specific_sourcetypes(self) -> frozenset[str]:
        return frozenset(s for s in self.sourcetypes if not is_neutral_sourcetype(s))


def _list_values(body: str) -> list[str]:
    out = []
    for m in _LIST_ITEM.finditer(body):
        val = next(g for g in m.groups() if g)
        if val.upper() != "OR":
            out.append(val)
    return out


def extract_spl_evidence(*spl_texts: str | None) -> SplEvidence:
    """Return the sourcetypes, indexes and macros named in the given searches."""
    sourcetypes: set[str] = set()
    indexes: set[str] = set()
    macros: set[str] = set()
    datamodels: set[str] = set()
    uses_dm = False
    for text in spl_texts:
        if not text:
            continue
        for m in _SOURCETYPE_EQ.finditer(text):
            sourcetypes.add(next(g for g in m.groups() if g).strip().lower())
        for m in _SOURCETYPE_IN.finditer(text):
            sourcetypes.update(v.lower() for v in _list_values(m.group(1)))
        for m in _INDEX_EQ.finditer(text):
            indexes.add(next(g for g in m.groups() if g).strip().lower())
        for m in _INDEX_IN.finditer(text):
            indexes.update(v.lower() for v in _list_values(m.group(1)))
        for m in _MACRO.finditer(text):
            macros.add(m.group(1).lower())
        for m in _DATAMODEL_NAME.finditer(text):
            datamodels.add(next(g for g in m.groups() if g))
        if _DATAMODEL.search(text):
            uses_dm = True
    if any(_glob_any(mac, _CIM_MACROS) for mac in macros):
        uses_dm = True
    return SplEvidence(
        frozenset(sourcetypes),
        frozenset(indexes),
        frozenset(macros),
        uses_dm,
        frozenset(datamodels),
    )


def _glob_any(value: str, globs: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(value, g) for g in globs)


def is_neutral_sourcetype(sourcetype: str) -> bool:
    st = sourcetype.lower()
    return st.strip("*") == "" or _glob_any(st, NEUTRAL_SOURCETYPES)


def is_peer_vendor_token(value: str) -> bool:
    v = value.lower()
    return any(tok in v for tok in PEER_VENDOR_TOKENS)


def evidence_block(entry: dict[str, Any]) -> dict[str, list[str]]:
    block = entry.get("evidence") or {}
    return {
        k: [str(v).lower() for v in block.get(k) or []]
        for k in ("sourcetypes", "indexes", "macros")
    } | {
        "cimModels": [str(v) for v in block.get("cimModels") or []],
        "references": [str(v) for v in block.get("references") or []],
    }


def matches_evidence(ev: SplEvidence, block: dict[str, list[str]]) -> bool:
    """True when the search names a sourcetype, index or macro from ``block``."""
    return (
        any(_glob_any(s, block["sourcetypes"]) for s in ev.sourcetypes)
        or any(_glob_any(i, block["indexes"]) for i in ev.indexes)
        or any(_glob_any(m, block["macros"]) for m in ev.macros)
    )


def matches_sourcetype(ev: SplEvidence, block: dict[str, list[str]]) -> bool:
    return any(_glob_any(s, block["sourcetypes"]) for s in ev.sourcetypes)


def token_contains(haystack_lower: str, pattern_lower: str) -> bool:
    """Case-folded containment that refuses matches inside a longer word.

    ``aci`` matches ``Splunk_TA_cisco-ACI`` and ``Cisco ACI`` but not
    ``capacity`` or ``Modacity``; ``cisco:ios`` does not match
    ``cisco:iosxe``. Only letters and digits count as word characters.
    """
    if not pattern_lower:
        return False
    start = 0
    n = len(pattern_lower)
    while True:
        i = haystack_lower.find(pattern_lower, start)
        if i < 0:
            return False
        before = haystack_lower[i - 1] if i > 0 else ""
        after = haystack_lower[i + n] if i + n < len(haystack_lower) else ""
        edge_ok_before = not (before and before in _TOKEN_CHARS and pattern_lower[0] in _TOKEN_CHARS)
        edge_ok_after = not (after and after in _TOKEN_CHARS and pattern_lower[-1] in _TOKEN_CHARS)
        if edge_ok_before and edge_ok_after:
            return True
        start = i + 1


def gated_entries(equipment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Registry entries that opt into evidence gating."""
    return [e for e in equipment if e.get("evidence")]


def _app_mentions(app_lower: str, tas: Iterable[str]) -> bool:
    return any(token_contains(app_lower, str(p).lower()) for p in tas)


def search_allows_app_evidence(ev: SplEvidence, vendor_block: dict[str, list[str]]) -> bool:
    """Whether a product named in ``app`` may stand in for search evidence.

    Only when the search names no vendor-specific sourcetype at all (it
    reads a CIM data model, a macro, a generic syslog / SNMP / NetFlow
    feed, or an index) and does not read a competing vendor's index.
    """
    if ev.specific_sourcetypes:
        return False
    if any(is_peer_vendor_token(i) for i in ev.indexes) and not any(
        _glob_any(i, vendor_block["indexes"]) for i in ev.indexes
    ):
        return False
    return True


def compute_gated_tags(
    entry: dict[str, Any],
    app_text: str,
    ev: SplEvidence,
    variant_models: Iterable[str] = (),
) -> tuple[bool, set[str]]:
    """Return (vendor_tagged, model_compounds) for one gated registry entry."""
    eq_id = entry["id"]
    app_lower = (app_text or "").replace("`", "").lower()
    vendor_block = evidence_block(entry)
    app_ok = search_allows_app_evidence(ev, vendor_block)
    variants = set(variant_models)

    models: set[str] = set()
    for model in entry.get("models") or []:
        compound = f"{eq_id}_{model['id']}"
        block = evidence_block(model)
        if compound in variants or matches_evidence(ev, block):
            models.add(compound)
        elif app_ok and _app_mentions(app_lower, model.get("tas") or []):
            models.add(compound)

    vendor = bool(models) or matches_evidence(ev, vendor_block)
    if not vendor and app_ok and _app_mentions(app_lower, entry.get("tas") or []):
        vendor = True
    return vendor, models
