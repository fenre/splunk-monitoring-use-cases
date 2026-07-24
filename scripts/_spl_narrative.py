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
        r"(?:stats|timechart|chart)\b[^|]*?\bby\s+([^|]+?)(?=\s*\||$)", spl, re.I
    ):
        for token in re.split(r"[,\s]+", match.group(1)):
            token = token.strip().strip(",")
            if token and token.lower() not in {"span", "as", "where"} and not token.startswith("span="):
                if token not in ctx.group_by_fields:
                    ctx.group_by_fields.append(token)

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

    for match in re.finditer(r"\|\s*eval\s+(\w+)\s*=", spl, re.I):
        name = match.group(1)
        if name not in ctx.eval_fields:
            ctx.eval_fields.append(name)

    for match in re.finditer(r"`([^`\s|]+)`", spl):
        macro = match.group(1)
        if macro not in ctx.lookups and not macro.startswith("$"):
            ctx.lookups.append(macro)

    dm = re.search(r"from\s+datamodel\s+([^\s|]+)", spl, re.I)
    if dm:
        dm_name = dm.group(1)
        root = dm_name.split(".", 1)[0].lower()
        if root not in ctx.indexes:
            ctx.indexes.append(root)

    return ctx


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


def aggregation_phrase(ctx: SplContext, fallback: str = "count") -> str:
    return ctx.aggregations[0] if ctx.aggregations else fallback
