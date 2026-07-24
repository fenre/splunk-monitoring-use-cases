"""Lightweight SPL context extraction for UC-unique narrative generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

sys_path_added = False


@dataclass
class SplContext:
    indexes: list[str] = field(default_factory=list)
    sourcetypes: list[str] = field(default_factory=list)
    group_by_fields: list[str] = field(default_factory=list)
    thresholds: list[dict[str, str]] = field(default_factory=list)
    aggregations: list[str] = field(default_factory=list)
    lookups: list[str] = field(default_factory=list)
    span: str | None = None
    time_window: str | None = None
    event_code: str | None = None
    eval_fields: list[str] = field(default_factory=list)
    stats_outputs: list[str] = field(default_factory=list)
    event_types: list[str] = field(default_factory=list)
    datamodel: str | None = None
    search_filters: list[str] = field(default_factory=list)
    filter_macros: list[str] = field(default_factory=list)
    lookup_tables: list[str] = field(default_factory=list)


_COMMON_MACROS = frozenset(
    {
        "security_content_ctime",
        "security_content_summariesonly",
        "drop_dm_object_name",
        "drop_dm_object_name(Processes)",
    }
)


def build_spl_context(uc: dict) -> SplContext:
    """Extract narrative tokens from a UC sidecar SPL and related fields."""
    spl = str(uc.get("spl", ""))
    ctx = SplContext()

    for match in re.finditer(r"index\s*=\s*([a-zA-Z0-9_\-]+)", spl, re.I):
        idx = match.group(1)
        if idx not in ctx.indexes:
            ctx.indexes.append(idx)
    for match in re.finditer(r'sourcetype\s*=\s*"([^"]+)"', spl, re.I):
        st = match.group(1)
        if st not in ctx.sourcetypes:
            ctx.sourcetypes.append(st)
    if not ctx.sourcetypes:
        match = re.search(r"sourcetype\s*=\s*([a-zA-Z0-9_:\-\.]+)", spl, re.I)
        if match:
            ctx.sourcetypes.append(match.group(1))

    ec = re.search(r"EventCode\s*=\s*(\d+)", spl, re.I)
    if ec:
        ctx.event_code = ec.group(1)

    for match in re.finditer(
        r"(?:stats|timechart|chart|tstats)\b[^|]*?\bby\s+([^|]+?)(?=\s*\||$)", spl, re.I
    ):
        for token in re.split(r"[,\s]+", match.group(1)):
            token = token.strip().strip(",")
            if (
                token
                and token.lower() not in {"span", "as", "where", "from"}
                and not token.startswith("span=")
            ):
                if token not in ctx.group_by_fields:
                    ctx.group_by_fields.append(token)

    for match in re.finditer(
        r"\b(?:count|sum|avg|dc|min|max|median|stdev)\([^)]*\)\s+as\s+(\w+)",
        spl,
        re.I,
    ):
        alias = match.group(1)
        if alias not in ctx.stats_outputs:
            ctx.stats_outputs.append(alias)

    for match in re.finditer(r"eventType\s*=\s*\"([^\"]+)\"", spl, re.I):
        et = match.group(1)
        if et not in ctx.event_types:
            ctx.event_types.append(et)

    for match in re.finditer(r"\b(count|avg|sum|max|min|dc|values|stdev|median)\s*\(", spl, re.I):
        fn = match.group(1).lower()
        if fn not in ctx.aggregations:
            ctx.aggregations.append(fn)

    for match in re.finditer(r"\b([a-zA-Z_]\w+)\s*([><=!]{1,2})\s*(-?\d+(?:\.\d+)?)", spl):
        field_name = match.group(1)
        if field_name in ("earliest", "latest", "span", "interval"):
            continue
        if match.group(2) in ("=", "==", "!="):
            continue
        ctx.thresholds.append(
            {"field": field_name, "op": match.group(2), "value": match.group(3)}
        )

    for match in re.finditer(r"\|\s*lookup\s+(\S+)", spl, re.I):
        if match.group(1) not in ctx.lookups:
            ctx.lookups.append(match.group(1))
    for match in re.finditer(r"\|\s*inputlookup\s+(\S+)", spl, re.I):
        if match.group(1) not in ctx.lookups:
            ctx.lookups.append(match.group(1))

    span = re.search(r"span\s*=\s*(\d+[smhdw])", spl, re.I)
    if span:
        ctx.span = span.group(1)

    tw = re.search(r"earliest\s*=\s*(-?\d+[smhdw]|@\w+)", spl, re.I)
    if tw:
        ctx.time_window = tw.group(1)
    sh = re.search(r"starthoursago\s*=\s*(\d+)", spl, re.I)
    if sh:
        ctx.time_window = f"{sh.group(1)}h lookback"

    for match in re.finditer(r"\|\s*eval\s+(\w+)\s*=", spl, re.I):
        name = match.group(1)
        if name not in ctx.eval_fields:
            ctx.eval_fields.append(name)

    for match in re.finditer(r"`([^`\s|]+)`", spl):
        macro = match.group(1)
        if macro.startswith("$"):
            continue
        base = macro.split("(", 1)[0]
        if base in _COMMON_MACROS or macro in _COMMON_MACROS:
            continue
        if macro not in ctx.lookups:
            ctx.lookups.append(macro)
        if macro not in ctx.filter_macros:
            ctx.filter_macros.append(macro)

    for match in re.finditer(r"\blookup\s+(?:update=\w+\s+)?(\S+)", spl, re.I):
        table = match.group(1)
        if table not in ctx.lookup_tables:
            ctx.lookup_tables.append(table)

    for match in re.finditer(r"\|\s*search\s+([^|]+)", spl, re.I):
        predicate = " ".join(match.group(1).split())
        if predicate and predicate not in ctx.search_filters:
            ctx.search_filters.append(predicate[:120])

    dm = re.search(r"from\s+datamodel\s*=?\s*([^\s|]+)", spl, re.I)
    if dm:
        ctx.datamodel = dm.group(1)
        root = dm.group(1).split(".", 1)[0].lower()
        if root not in ctx.indexes:
            ctx.indexes.append(root)

    return ctx


def stats_output_phrase(ctx: SplContext, fallback: str = "metric") -> str:
    return ", ".join(f"`{name}`" for name in ctx.stats_outputs[:3]) or f"`{fallback}`"


def group_fields_phrase(ctx: SplContext, fallback: str = "host") -> str:
    if not ctx.group_by_fields:
        return f"`{fallback}`"
    return ", ".join(f"`{field}`" for field in ctx.group_by_fields[:4])


def unique_spl_signature(ctx: SplContext) -> str:
    """Compact UC-specific SPL tokens for narrative differentiation."""
    parts: list[str] = []
    if ctx.filter_macros:
        parts.append(f"macro `{ctx.filter_macros[-1]}`")
    if ctx.lookup_tables:
        parts.append(f"lookup `{ctx.lookup_tables[0]}`")
    if ctx.search_filters:
        parts.append(f"filter `{ctx.search_filters[-1][:60]}`")
    if ctx.event_types:
        parts.append(f"eventType `{ctx.event_types[0]}`")
    return ", ".join(parts)


def primary_index(ctx: SplContext, fallback: str = "target_index") -> str:
    return ctx.indexes[0] if ctx.indexes else fallback


def primary_sourcetype(ctx: SplContext, fallback: str = "configured_sourcetype") -> str:
    return ctx.sourcetypes[0] if ctx.sourcetypes else fallback


def primary_group_field(ctx: SplContext, fallback: str = "host") -> str:
    return ctx.group_by_fields[0] if ctx.group_by_fields else fallback


def threshold_phrase(ctx: SplContext, fallback: str = "configured threshold") -> str:
    if not ctx.thresholds:
        return fallback
    t = ctx.thresholds[0]
    return f"`{t['field']}` {t['op']} {t['value']}"


def all_thresholds_phrase(ctx: SplContext, fallback: str = "configured threshold") -> str:
    if not ctx.thresholds:
        return fallback
    if len(ctx.thresholds) == 1:
        return threshold_phrase(ctx, fallback)
    parts = [f"`{t['field']}` {t['op']} {t['value']}" for t in ctx.thresholds[:4]]
    return ", ".join(parts[:-1]) + f", or {parts[-1]}"


def aggregation_phrase(ctx: SplContext, fallback: str = "count") -> str:
    return ctx.aggregations[0] if ctx.aggregations else fallback
