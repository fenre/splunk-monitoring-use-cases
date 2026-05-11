#!/usr/bin/env python3
"""Fix the SPL hallucinations identified by ``deep_spl_hallucination_sweep.py``.

This script applies precise, idempotent transformations to specific SPL
patterns that are not valid Splunk Search Processing Language:

  Eval-context:
    * ``concat(a, b, c)``          → ``a . b . c``
    * ``strcat(a, b, c)`` in eval  → ``a . b . c``
    * ``to_string(x)``             → ``tostring(x)``
    * ``hour(_time)``              → ``tonumber(strftime(_time, "%H"))``
    * ``ifnull(...)``              → ``coalesce(...)``

  Aggregator-context:
    * ``stats ... by ..., bin(_time, Nx)``  → ``bin _time span=Nx`` before stats
    * ``streamstats delta(f) as d``         → ``streamstats last(f) as _prev_f
                                              | eval d = f - _prev_f``
    * ``streamstats previous(f) as p``      → ``streamstats first(f) as p`` with
                                              ``global=f`` window=2
    * ``streamstats current(a) as A next(b) as B`` →
        ``streamstats first(a) as A_prev last(b) as B_next`` etc.
    * ``streamstats current(a) as A prev(b) as B`` →
        ``streamstats last(a) as A first(b) as B`` etc.
    * ``mean(x)`` aggregator                 → ``avg(x)``

  Per-UC specials (bespoke):
    * UC-13.7.10: add missing closing paren on the emit_ratio_roll eval
    * UC-22.1.44: replace ``std(bytes_out)`` with a precomputed
      ``stdev(bytes_out) AS std_bytes`` in the preceding eventstats
    * UC-14.3.33, UC-14.3.47: replace ``correlation(temp, current)`` with
      a threshold-based root-cause classifier using eventstats baselines
    * UC-12.4.16: replace ``semver_compare(a, b) < 0`` with a split-on-dot
      manual version comparison
    * UC-23.1.8: replace ``dense_rank(0 - validation_errors)`` with
      ``streamstats count`` after sorting
    * UC-22.8.1, UC-22.8.2: SPL field contains literal Markdown ``\`\`\`spl``
      fences enclosing multiple SPL queries — keep only the first valid
      query.
    * UC-9.4.19, UC-10.13.3, UC-7.1.32: streamstats positional aggregators
      converted to ``first()``/``last()`` over a ``window=2 global=f`` slice.

All edits are idempotent: re-running the script after a clean run is a no-op.
Run via:

    python3 scripts/fix_spl_hallucinations.py --check    # dry-run
    python3 scripts/fix_spl_hallucinations.py            # apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def split_top_level_args(arglist: str) -> list[str]:
    """Split a comma-separated argument list at the top level, ignoring
    commas inside nested parens or strings."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    in_str = False
    quote = ""
    for c in arglist:
        if in_str:
            buf.append(c)
            if c == quote:
                in_str = False
            continue
        if c in ('"', "'"):
            in_str = True
            quote = c
            buf.append(c)
            continue
        if c == "(":
            depth += 1
            buf.append(c)
            continue
        if c == ")" and depth > 0:
            depth -= 1
            buf.append(c)
            continue
        if c == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(c)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def _find_matching_paren(text: str, open_idx: int) -> int:
    """Given the index of an opening ``(`` in ``text``, return the index of
    its matching ``)``. Returns -1 if unbalanced."""
    depth = 0
    in_str = False
    quote = ""
    for i in range(open_idx, len(text)):
        c = text[i]
        if in_str:
            if c == quote and text[i - 1] != "\\":
                in_str = False
            continue
        if c in ('"', "'"):
            in_str = True
            quote = c
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def replace_func_with_concat_op(spl: str, func_name: str) -> tuple[str, int]:
    """Replace ``func_name(a, b, c, ...)`` with ``a . b . c . ...`` inside
    eval/where/fieldformat segments (Splunk concatenation operator).

    Returns ``(new_spl, n_replacements)``. The replacement is idempotent and
    only applies when the function name has no preceding word-character / dot
    so we don't match ``my_strcat(...)``.
    """
    pat = re.compile(
        r"(?<![\w.])" + re.escape(func_name) + r"\(",
        re.IGNORECASE,
    )
    out = []
    i = 0
    n = len(spl)
    n_subs = 0
    while i < n:
        m = pat.search(spl, i)
        if not m:
            out.append(spl[i:])
            break
        out.append(spl[i : m.start()])
        open_idx = m.end() - 1
        close_idx = _find_matching_paren(spl, open_idx)
        if close_idx == -1:
            out.append(spl[m.start() : m.end()])
            i = m.end()
            continue
        args_text = spl[open_idx + 1 : close_idx]
        args = split_top_level_args(args_text)
        if len(args) < 2:
            out.append(spl[m.start() : close_idx + 1])
        else:
            out.append(" . ".join(args))
            n_subs += 1
        i = close_idx + 1
    return "".join(out), n_subs


def replace_func_name_only(spl: str, old: str, new: str) -> tuple[str, int]:
    """Replace ``old(...)`` with ``new(...)`` (function name only)."""
    pat = re.compile(r"(?<![\w.])" + re.escape(old) + r"\(", re.IGNORECASE)
    n = len(pat.findall(spl))
    out = pat.sub(new + "(", spl)
    return out, n


def fix_hour_func(spl: str) -> tuple[str, int]:
    """``hour(<expr>)`` → ``tonumber(strftime(<expr>, "%H"))`` (inside eval
    and where segments only). Idempotent."""
    pat = re.compile(r"(?<![\w.])hour\(", re.IGNORECASE)
    out: list[str] = []
    i = 0
    n_subs = 0
    while i < len(spl):
        m = pat.search(spl, i)
        if not m:
            out.append(spl[i:])
            break
        open_idx = m.end() - 1
        close_idx = _find_matching_paren(spl, open_idx)
        if close_idx == -1:
            out.append(spl[i : m.end()])
            i = m.end()
            continue
        out.append(spl[i : m.start()])
        inner = spl[open_idx + 1 : close_idx]
        out.append(f'tonumber(strftime({inner}, "%H"))')
        i = close_idx + 1
        n_subs += 1
    return "".join(out), n_subs


def fix_bin_in_stats_by(spl: str) -> tuple[str, int]:
    """Replace ``stats <aggregators> BY <fields>[, ] bin(_time, <span>)``
    with ``| bin _time span=<span> | stats … BY …, _time``.

    Handles both the comma-prefix case (``by foo, bin(_time, 5m)``) and the
    sole-grouping case (``by bin(_time, 5m)``). The replacement preserves
    the original aggregator list, prefixes the segment with a separate
    ``| bin _time span=<span>`` pipe, and emits a trailing newline so the
    next pipe segment in the SPL stays on its own line.
    """
    pat = re.compile(
        r"(?P<lead>\|\s*)(?P<cmd>stats|eventstats)(?P<body>\b[^|]*?)\bby(?P<bypart>[^|]*?)(?:,\s*|\s+)bin\(\s*_time\s*,\s*(?P<span>[^\s\)]+)\s*\)",
        re.IGNORECASE,
    )

    def _repl(m: re.Match[str]) -> str:
        cmd = m.group("cmd")
        body = m.group("body").rstrip()
        bypart = m.group("bypart").rstrip()
        if bypart.endswith(","):
            bypart = bypart[:-1].rstrip()
        span = m.group("span")
        if bypart:
            return f"| bin _time span={span}\n| {cmd}{body} by {bypart}, _time"
        return f"| bin _time span={span}\n| {cmd}{body} by _time"

    new_spl, n = pat.subn(_repl, spl)
    return new_spl, n


def fix_streamstats_delta(spl: str) -> tuple[str, int]:
    """Replace every ``delta(field) AS alias`` aggregator inside any
    ``| streamstats …`` segment with ``last(field) AS _ss_prev_<field>`` and
    append ``| eval alias = field - _ss_prev_<field>`` after the segment.

    Also injects ``current=f`` into the streamstats so ``last()`` returns
    the *previous* row's value, which is what ``delta()`` was trying to
    express. Multiple ``delta()`` calls in the same streamstats segment are
    all transformed, with eval statements emitted in order.
    """
    seg_pat = re.compile(
        r"(\|\s*streamstats[^|]*?)(?=\||$)",
        re.IGNORECASE | re.DOTALL,
    )
    delta_pat = re.compile(
        r"\bdelta\(\s*([A-Za-z_][\w]*)\s*\)\s+AS\s+([A-Za-z_][\w]*)",
        re.IGNORECASE,
    )

    total_n = 0

    def _rewrite_segment(m: re.Match[str]) -> str:
        nonlocal total_n
        seg = m.group(1)
        deltas = list(delta_pat.finditer(seg))
        if not deltas:
            return seg
        # Replace each delta(f) AS alias with last(f) AS _ss_prev_<f>
        evals: list[str] = []
        new_seg = seg
        for d in deltas:
            field = d.group(1)
            alias = d.group(2)
            old_text = d.group(0)
            replacement = f"last({field}) AS _ss_prev_{field}"
            new_seg = new_seg.replace(old_text, replacement, 1)
            evals.append(f"| eval {alias} = {field} - _ss_prev_{field}")
            total_n += 1
        # Inject current=f if absent
        if not re.search(r"\bcurrent\s*=\s*[ft]\b", new_seg, re.IGNORECASE):
            new_seg = re.sub(
                r"(\|\s*streamstats)\b", r"\1 current=f", new_seg, count=1
            )
        else:
            new_seg = re.sub(
                r"\bcurrent\s*=\s*t\b", "current=f", new_seg, flags=re.IGNORECASE
            )
        return new_seg + "\n" + "\n".join(evals) + " "

    new_spl = seg_pat.sub(_rewrite_segment, spl)
    return new_spl, total_n


def fix_streamstats_previous(spl: str) -> tuple[str, int]:
    """Generic translation of ``streamstats <opts> previous(field) AS alias``
    to the canonical ``current=f global=f last(field) AS alias`` form.

    With ``current=f``, ``last()`` always returns the *previous* row's
    value, which is the semantic the operator intended when writing
    ``previous()`` (an invented function).
    """
    pat = re.compile(
        r"(\|\s*streamstats\b)([^|]*?)\bprevious\(\s*([A-Za-z_][\w]*)\s*\)\s+AS\s+([A-Za-z_][\w]*)",
        re.IGNORECASE,
    )

    def _repl(m: re.Match[str]) -> str:
        head = m.group(1)
        opts = m.group(2)
        field = m.group(3)
        alias = m.group(4)
        if not re.search(r"\bcurrent\s*=\s*[ft]\b", opts, re.IGNORECASE):
            opts = " current=f" + opts
        else:
            opts = re.sub(r"\bcurrent\s*=\s*t\b", "current=f", opts, flags=re.IGNORECASE)
        if not re.search(r"\bglobal\s*=", opts, re.IGNORECASE):
            opts = opts + " global=f "
        # Ensure exactly one space between the last option and the aggregator
        if not opts.endswith(" "):
            opts = opts + " "
        return f"{head}{opts}last({field}) AS {alias}"

    new_spl, n = pat.subn(_repl, spl)
    return new_spl, n


def fix_mean_aggregator(spl: str) -> tuple[str, int]:
    """Replace ``mean(x)`` aggregator in stats-family commands with
    ``avg(x)``."""
    pat = re.compile(r"(?<![\w.])mean\(", re.IGNORECASE)
    n = len(pat.findall(spl))
    return pat.sub("avg(", spl), n


def fix_ifnull(spl: str) -> tuple[str, int]:
    """``ifnull(...)`` → ``coalesce(...)``."""
    pat = re.compile(r"(?<![\w.])ifnull\(", re.IGNORECASE)
    n = len(pat.findall(spl))
    return pat.sub("coalesce(", spl), n


# ──────────────────────────────────────────────────────────────────────────────
# Per-UC bespoke fixes
# ──────────────────────────────────────────────────────────────────────────────


def fix_uc_13_7_10(spl: str) -> str:
    """Add the missing closing paren on the emit_ratio_roll eval line."""
    bad = (
        "| eval emit_ratio_roll=if(isnotnull(emit_ratio),emit_ratio,"
        "if(prev_inp>0 AND prev_ml>=0,round(prev_ml/max(prev_inp,1),5),null())"
    )
    good = (
        "| eval emit_ratio_roll=if(isnotnull(emit_ratio),emit_ratio,"
        "if(prev_inp>0 AND prev_ml>=0,round(prev_ml/max(prev_inp,1),5),null()))"
    )
    if good in spl:
        return spl
    return spl.replace(bad, good)


def fix_uc_22_1_44(spl: str) -> str:
    """Add ``stdev(bytes_out) as std_bytes`` to the eventstats and use
    ``std_bytes`` instead of the invalid ``std(bytes_out)``."""
    old_eventstats = "| eventstats median(bytes_out) as med by Country"
    new_eventstats = (
        "| eventstats median(bytes_out) as med stdev(bytes_out) as std_bytes by Country"
    )
    if new_eventstats in spl:
        return spl
    spl = spl.replace(old_eventstats, new_eventstats)
    spl = spl.replace("std(bytes_out)", "std_bytes")
    return spl


def fix_uc_14_3_33(spl: str) -> str:
    """Replace correlation()-based logic with a threshold-based classifier
    using eventstats baselines (the original intent — detect thermal
    overload when temp and motor_current both exceed their normal range)."""
    old = (
        "| eval correlation=correlation(temp, motor_current)\n"
        "| where correlation > 0.8"
    )
    new = (
        "| eventstats avg(temp) as avg_t, avg(motor_current) as avg_mc, "
        "stdev(temp) as sd_t, stdev(motor_current) as sd_mc by equipment_id\n"
        "| where temp > avg_t + sd_t AND motor_current > avg_mc + sd_mc"
    )
    if "correlation(temp, motor_current)" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_14_3_47(spl: str) -> str:
    """Same pattern as UC-14.3.33 but with sensor_temp / api_air_temp."""
    old = (
        "| eval correlation=correlation(sensor_temp, api_air_temp)\n"
    )
    new = (
        "| eventstats avg(sensor_temp) as avg_st, avg(api_air_temp) as avg_at, "
        "stdev(sensor_temp) as sd_st, stdev(api_air_temp) as sd_at by site_id\n"
        "| eval temp_drift_z=if(sd_st>0,abs((sensor_temp - api_air_temp) / sd_st),0)\n"
    )
    if "correlation(sensor_temp" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_12_4_16(spl: str) -> str:
    """Replace ``semver_compare(a, b) < 0`` with a manual major/minor/patch
    integer comparison."""
    old = "| where semver_compare(module_version, min_version) < 0"
    new = (
        "| eval mv=split(module_version, \".\"), miv=split(min_version, \".\")\n"
        "| eval mv_maj=tonumber(mvindex(mv,0)), mv_min=tonumber(mvindex(mv,1)), "
        "mv_pat=tonumber(mvindex(mv,2))\n"
        "| eval mi_maj=tonumber(mvindex(miv,0)), mi_min=tonumber(mvindex(miv,1)), "
        "mi_pat=tonumber(mvindex(miv,2))\n"
        "| where (mv_maj<mi_maj) OR (mv_maj=mi_maj AND mv_min<mi_min) OR "
        "(mv_maj=mi_maj AND mv_min=mi_min AND mv_pat<mi_pat)"
    )
    if "semver_compare" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_23_1_8(spl: str) -> str:
    """Replace ``dense_rank(0 - x)`` with ``streamstats count``."""
    old = "| eval friction_rank=dense_rank(0-validation_errors)"
    new = (
        "| sort 0 - validation_errors\n"
        "| streamstats count as friction_rank"
    )
    if "dense_rank" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_9_4_19(spl: str) -> str:
    """Detect concurrent CyberArk sessions from different source IPs on the
    same target account using a valid streamstats pattern.

    The original SPL used invented ``current()``/``next()`` aggregators; the
    canonical Splunk approach is to remember the previous row's *src* and
    *end_time* with ``current=f window=2`` and check whether the current
    session started before the previous session ended.
    """
    old = (
        "| streamstats window=2 current(src) as ip1 next(src) as ip2 "
        "current(_time) as t1 next(_time) as t2 by target_account\n"
        "| where ip1!=ip2 AND t2 < end_time"
    )
    new = (
        "| streamstats window=2 current=f global=f "
        "last(src) as prev_src last(end_time) as prev_end "
        "by target_account\n"
        "| where isnotnull(prev_src) AND src != prev_src AND _time < prev_end"
    )
    if "current(src)" not in spl:
        return spl
    spl = spl.replace(old, new)
    spl = spl.replace(
        "| table target_account, ip1, ip2, t1, t2",
        "| table target_account, prev_src, src, _time, prev_end",
    )
    return spl


def fix_uc_10_13_3(spl: str) -> str:
    old = (
        "| streamstats window=2 global=f current(Country) as cur_c "
        "prev(Country) as prev_c current(_time) as ts prev(_time) as pts by user"
    )
    new = (
        "| streamstats window=2 global=f last(Country) as cur_c "
        "first(Country) as prev_c last(_time) as ts first(_time) as pts by user"
    )
    if "current(Country)" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_7_1_32(spl: str) -> str:
    """No-op — the generic ``fix_streamstats_previous`` already converts
    ``previous(last_lsn) AS prev_last`` to ``current=f global=f
    last(last_lsn) AS prev_last``. This entry stays in ``PER_UC_FIXES``
    so the audit report still attributes the fix to UC-7.1.32, but the
    transformation is performed generically.
    """
    return spl


def fix_uc_22_8_x(spl: str) -> str:
    """Remove Markdown code-fence blocks from the SPL field. The SPL author
    inadvertently dropped multiple ``\`\`\`spl … \`\`\``-fenced examples into
    the ``spl`` field, which is supposed to be a single executable query.
    We keep the first valid query and drop the rest.
    """
    if "```" not in spl:
        return spl
    # The first fence delimits the end of the first query. Take everything
    # before the first ``` line.
    out_lines: list[str] = []
    for line in spl.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            break
        out_lines.append(line)
    return "\n".join(out_lines).rstrip() + "\n"


def fix_uc_6_4_25(spl: str) -> str:
    """Dedup-ratio 7-day drop detection. ``current(dr)`` isn't a streamstats
    aggregator; ``last(dr)`` with default ``current=t`` returns the current
    row's value, which is what we want for ``dr_now``."""
    old = (
        "| streamstats window=7 global=f current(dr) as dr_now "
        "earliest(dr) as dr_7dago"
    )
    new = (
        "| streamstats window=7 global=f last(dr) as dr_now "
        "earliest(dr) as dr_7dago"
    )
    if "current(dr)" not in spl:
        return spl
    return spl.replace(old, new)


def fix_uc_9_5_11(spl: str) -> str:
    """Okta impossible-travel detection. The original streamstats was
    incorrect — with ``window=1`` and default ``current=t``, ``last()`` just
    returns the current row's value, not the previous row's. The valid form
    uses ``current=f`` so ``last()`` returns the previous row's value.
    """
    old = (
        "| streamstats window=1 last(client.geographicalContext.country) "
        "as prev_country last(_time) as prev_time last(client.ipAddress) "
        "as prev_ip current(client.geographicalContext.country) as country "
        "by actor.alternateId"
    )
    new = (
        "| streamstats window=1 current=f global=f "
        "last(client.geographicalContext.country) as prev_country "
        "last(_time) as prev_time last(client.ipAddress) as prev_ip "
        "by actor.alternateId\n"
        "| eval country = 'client.geographicalContext.country'"
    )
    if "current(client.geographicalContext" not in spl:
        return spl
    return spl.replace(old, new)


PER_UC_FIXES = {
    "13.7.10": fix_uc_13_7_10,
    "22.1.44": fix_uc_22_1_44,
    "14.3.33": fix_uc_14_3_33,
    "14.3.47": fix_uc_14_3_47,
    "12.4.16": fix_uc_12_4_16,
    "23.1.8": fix_uc_23_1_8,
    "9.4.19": fix_uc_9_4_19,
    "10.13.3": fix_uc_10_13_3,
    "7.1.32": fix_uc_7_1_32,
    "22.8.1": fix_uc_22_8_x,
    "22.8.2": fix_uc_22_8_x,
    "6.4.25": fix_uc_6_4_25,
    "9.5.11": fix_uc_9_5_11,
}


# ──────────────────────────────────────────────────────────────────────────────
# Generic fix application order
# ──────────────────────────────────────────────────────────────────────────────


def apply_generic_fixes(spl: str) -> tuple[str, dict[str, int]]:
    """Apply order-sensitive generic fixes. The order matters:

      1. ``concat()``/``strcat()`` rewrites must run before any subsequent
         function rewrite so they don't get confused by injected dots.
      2. ``to_string()`` rename is purely textual and idempotent.
      3. ``hour()`` rewrite swaps in a ``strftime`` containing literal ``"%H"``
         — must run after concat/strcat so it isn't itself rewritten.
      4. ``bin()`` in stats BY is a multi-line restructure.
      5. streamstats ``delta()``/``previous()`` are last so they see fully
         cleaned eval expressions.
    """
    counts: dict[str, int] = defaultdict(int)
    spl, n = replace_func_with_concat_op(spl, "concat")
    counts["concat→."] += n
    spl, n = replace_func_with_concat_op(spl, "strcat")
    counts["strcat→."] += n
    spl, n = replace_func_name_only(spl, "to_string", "tostring")
    counts["to_string→tostring"] += n
    spl, n = fix_ifnull(spl)
    counts["ifnull→coalesce"] += n
    spl, n = fix_hour_func(spl)
    counts["hour()→strftime"] += n
    spl, n = fix_bin_in_stats_by(spl)
    counts["bin()_in_stats→pre-bin"] += n
    spl, n = fix_streamstats_delta(spl)
    counts["streamstats_delta→last+eval"] += n
    spl, n = fix_streamstats_previous(spl)
    counts["streamstats_previous→first"] += n
    spl, n = fix_mean_aggregator(spl)
    counts["mean→avg"] += n
    return spl, dict(counts)


# ──────────────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="Dry-run; no writes")
    p.add_argument("--verbose", action="store_true", help="Print per-file edits")
    args = p.parse_args(argv)

    n_files = 0
    n_changed = 0
    total_counts: dict[str, int] = defaultdict(int)
    changed_files: list[tuple[str, dict[str, int]]] = []

    for sidecar in sorted(CONTENT_DIR.rglob("UC-*.json")):
        try:
            text = sidecar.read_text(encoding="utf-8")
            uc = json.loads(text)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR parsing {sidecar}: {exc}", file=sys.stderr)
            continue
        n_files += 1
        uc_id = str(uc.get("id", ""))
        before = dict(uc)
        per_uc_counts: dict[str, int] = defaultdict(int)
        for fld in ("spl", "cimSpl"):
            spl = uc.get(fld, "") or ""
            if not spl:
                continue
            new_spl, gcounts = apply_generic_fixes(spl)
            # Per-UC bespoke
            if uc_id in PER_UC_FIXES and fld == "spl":
                fixed = PER_UC_FIXES[uc_id](new_spl)
                if fixed != new_spl:
                    per_uc_counts[f"per_uc[{uc_id}]"] += 1
                new_spl = fixed
            for k, v in gcounts.items():
                if v:
                    per_uc_counts[k] += v
            if new_spl != spl:
                uc[fld] = new_spl
        if uc != before:
            n_changed += 1
            for k, v in per_uc_counts.items():
                total_counts[k] += v
            changed_files.append((str(sidecar.relative_to(REPO_ROOT)), dict(per_uc_counts)))
            if not args.check:
                sidecar.write_text(
                    json.dumps(uc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"Scanned {n_files} sidecars; {n_changed} would change "
          f"(dry-run={args.check}).")
    print()
    print("Edit counts:")
    for k, v in sorted(total_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:36s} {v}")
    if args.verbose:
        print()
        print("Changed files:")
        for path, counts in changed_files[:200]:
            kind = ", ".join(f"{k}={v}" for k, v in counts.items() if v)
            print(f"  {path}  ({kind})")
        if len(changed_files) > 200:
            print(f"  ... and {len(changed_files) - 200} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
