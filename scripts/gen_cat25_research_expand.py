#!/usr/bin/env python3
"""Expand cat-25 subcategories to research-driven variable targets (max 100 each).

Reads scripts/cat25_research_manifest.json and appends new UCs per subcategory
until each reaches its researched target count.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from gen_cat25_common import CAT25, Cat25Writer, R, scan_existing
from gen_cat25_wave8a import G, S, _case, _spl

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "scripts" / "cat25_research_manifest.json"
CATEGORY = CAT25 / "_category.json"

MAX_PER_SUB = 100


def G_alt(source: dict[str, object]) -> list[dict[str, object]]:
    """Six additional metric templates per source (distinct from base G())."""
    label = str(source["label"])
    friendly = str(source["friendly"])
    st = str(source["st"])
    tag = st.replace(":", " ").replace("_", " ").title()
    group_field = str(source["group_field"])
    group_desc = str(source["group_desc"])
    value_field = str(source["value_field"])
    value_title = str(source["value_title"])
    duration_field = str(source["duration_field"])
    duration_title = str(source["duration_title"])

    return [
        _case(
            f"{tag} Monthly Rollup",
            "low",
            "beginner",
            ["Analytics"],
            _spl(
                f"index=personal sourcetype={st}",
                "| bin _time span=1mon",
                f"| stats count as events, sum({value_field}) as total_{value_field} by _time",
                "| sort _time",
            ),
            f"Summarises monthly event volume and total {value_title.lower()} for {friendly} data.",
            "Monthly rollups smooth daily noise and show seasonal shifts in personal activity.",
            f"Aggregate {friendly} events monthly and chart count plus total {value_title.lower()}.",
            "Column chart of monthly events with total value overlay.",
            f"how your {friendly} activity added up each month instead of day by day.",
        ),
        _case(
            f"{tag} Hour-of-Day Pattern",
            "low",
            "intermediate",
            ["Analytics"],
            _spl(
                f"index=personal sourcetype={st}",
                '| eval hour=strftime(_time,"%H")',
                f"| stats count as events by hour {group_field}",
                "| sort hour",
            ),
            f"Shows which hours of the day {friendly} events most often occur for each {group_desc}.",
            "Hour-of-day patterns reveal routine anchors, timezone drift, and automation misfires.",
            f"Extract hour from `_time` on {friendly} events and chart counts by {group_desc}.",
            "Heatmap or bar chart of events by hour.",
            f"what time of day your {friendly} feed is busiest and when it goes quiet.",
        ),
        _case(
            f"{tag} High {value_title} Outliers",
            "medium",
            "intermediate",
            ["Anomaly", "Analytics"],
            _spl(
                f"index=personal sourcetype={st} {value_field}=*",
                f"| eventstats perc90({value_field}) as p90, perc10({value_field}) as p10",
                f"| where {value_field}>=p90 OR {value_field}<=p10",
                f"| table _time {group_field} {value_field} p90 p10",
            ),
            f"Surfaces the highest and lowest {value_title.lower()} outliers in {friendly} events.",
            "Tail events often explain spikes in cost, effort, or risk that averages hide.",
            f"Compute percentile bands on `{value_field}` and review extreme {friendly} records.",
            f"Scatter plot of {value_title.lower()} with percentile bands.",
            f"the unusually high or low {value_title.lower()} moments in your {friendly} history.",
        ),
        _case(
            f"{tag} Rolling 7-Day {value_title} Average",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            _spl(
                f"index=personal sourcetype={st} {value_field}=*",
                "| bin _time span=1d",
                f"| stats avg({value_field}) as daily_avg by _time",
                "| streamstats window=7 avg(daily_avg) as rolling_7d",
                "| sort _time",
            ),
            f"Tracks a seven-day rolling average of daily {value_title.lower()} for {friendly} data.",
            "Rolling averages highlight gradual drift without overreacting to one-off days.",
            f"Compute daily average `{value_field}` then a seven-day rolling mean for {friendly} events.",
            f"Line chart of daily and rolling average {value_title.lower()}.",
            f"the smoothed week-long trend in your {value_title.lower()} from {friendly}.",
        ),
        _case(
            f"{tag} Weekend vs Weekday Split",
            "low",
            "beginner",
            ["Analytics"],
            _spl(
                f"index=personal sourcetype={st}",
                '| eval dow=strftime(_time,"%u")',
                '| eval bucket=if(dow>=6,"weekend","weekday")',
                f"| stats count as events, avg({value_field}) as avg_{value_field} by bucket",
            ),
            f"Compares weekend versus weekday event counts and average {value_title.lower()} for {friendly}.",
            "Weekend/weekday splits expose lifestyle rhythm changes and work-life boundary shifts.",
            f"Tag {friendly} events as weekend or weekday and compare volume and `{value_field}`.",
            "Side-by-side bar chart for weekend vs weekday.",
            f"whether your {friendly} activity looks different on weekends compared with weekdays.",
        ),
        _case(
            f"{tag} Field Completeness Score",
            "low",
            "intermediate",
            ["Data Quality"],
            _spl(
                f"index=personal sourcetype={st}",
                f"| eval complete=if(isnotnull({value_field}) AND isnotnull({duration_field}),1,0)",
                "| stats sum(complete) as complete_rows, count as total",
                "| eval completeness_pct=round(100*complete_rows/total,1)",
            ),
            f"Measures how often {friendly} events include both {value_title.lower()} and {duration_title.lower()}.",
            "Incomplete exports break joins and dashboards; completeness scoring catches schema drift early.",
            f"Require `{value_field}` and `{duration_field}` on {friendly} events and track completeness percentage.",
            "Single-value gauge of field completeness percent.",
            f"how often your {friendly} exports arrive with the key numbers filled in.",
        ),
    ]


def parse_sourcetypes(text: str) -> list[str]:
    return re.findall(r"`([a-z0-9:_-]+)`", text)


def default_source(st: str, idx: int) -> dict[str, object]:
    parts = st.split(":")
    label = parts[0].replace("_", " ").title()
    if len(parts) > 1:
        label = f"{label} {parts[1].replace('_', ' ').title()}"
    if idx:
        label = f"{label} ({idx})"
    return {
        "label": f"{label} Feed",
        "friendly": label.lower(),
        "st": st,
        "group_field": "source_id",
        "group_desc": "source",
        "value_field": "value",
        "value_title": "Value",
        "duration_field": "duration_min",
        "duration_title": "Duration",
        "status_field": "status",
        "sync_hours": 168,
    }


def special_from_dict(raw: dict[str, object], friendly: str) -> dict[str, object]:
    title = str(raw["title"])
    hint = str(raw.get("spl_hint") or raw.get("spl", ""))
    parts = [p.strip() for p in hint.split("|") if p.strip()]
    if parts and not parts[0].startswith("index="):
        parts[0] = "index=personal " + parts[0]
    elif not parts:
        st = raw.get("st", "personal:event")
        parts = [f"index=personal sourcetype={st}", "| stats count by _time"]
    spl_lines = tuple(parts)
    desc = str(raw.get("desc") or raw.get("desc_one_line") or f"Monitors {title.lower()} in index=personal.")
    return S(
        title,
        str(raw.get("crit", "medium")),
        str(raw.get("diff", "intermediate")),
        list(raw.get("mtypes", ["Analytics"])),  # type: ignore[arg-type]
        spl_lines,
        desc,
        str(raw.get("val") or f"Surfacing {title.lower()} helps you act before small issues become habits."),
        str(raw.get("impl") or f"Ingest the relevant {friendly} export into `index=personal` and schedule this search weekly."),
        str(raw.get("viz") or "Table or chart of key fields."),
        str(raw.get("grandma_body") or f"when {title.lower()} matters for your routine."),
    )


def special_from_title(title: str, st: str, friendly: str) -> dict[str, object]:
    return S(
        title,
        "medium",
        "intermediate",
        ["Analytics"],
        (
            f"index=personal sourcetype={st}",
            "| stats count as events, latest(_time) as last_seen",
            "| sort - events",
        ),
        f"Tracks {title.lower()} patterns from {friendly} telemetry in index=personal.",
        f"{title} gives early warning when your {friendly} routine drifts from what you intended.",
        f"Forward {friendly} events with the fields used in the SPL to `index=personal` and review weekly.",
        "Table sorted by event count.",
        f"patterns around {title.lower()} in your {friendly} data.",
    )


def load_category_meta() -> dict[str, dict[str, str]]:
    data = json.loads(CATEGORY.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for sub in data["subcategories"]:
        num = sub["id"].split(".")[1]
        out[num] = {
            "id": sub["id"],
            "name": sub["name"],
            "app": sub.get("primaryAppTa", ""),
            "ds": sub.get("dataSources", ""),
        }
    return out


def existing_sourcetypes(sub: str) -> set[str]:
    sts: set[str] = set()
    for p in CAT25.glob(f"UC-25.{sub}.*.json"):
        text = p.read_text(encoding="utf-8")
        sts.update(re.findall(r"sourcetype=([a-z0-9:_-]+)", text))
    return sts


def build_gap_specs(
    sub: str,
    gap: int,
    entry: dict[str, object],
    meta: dict[str, str],
) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    friendly = meta["name"].lower()

    for raw in entry.get("specials", []):
        if isinstance(raw, dict):
            specs.append(special_from_dict(raw, friendly))
        elif isinstance(raw, str):
            sts = parse_sourcetypes(meta["ds"])
            st = sts[0] if sts else "personal:event"
            specs.append(special_from_title(raw, st, friendly))

    for src in entry.get("extra_sources", []):
        if isinstance(src, dict) and "st" in src:
            specs.extend(G(src))
            if len(specs) >= gap:
                break

    used_sts = existing_sourcetypes(sub)
    manifest_sts = {str(s.get("st")) for s in entry.get("extra_sources", []) if isinstance(s, dict)}
    for st in parse_sourcetypes(meta["ds"]):
        if st in used_sts or st in manifest_sts:
            continue
        src = default_source(st, len(specs))
        specs.extend(G_alt(src))
        if len(specs) >= gap:
            break

    idx = 0
    while len(specs) < gap:
        sts = parse_sourcetypes(meta["ds"])
        st = sts[idx % len(sts)] if sts else "personal:event"
        src = default_source(f"{st.split(':')[0]}:metric{idx}", idx)
        specs.extend(G_alt(src))
        idx += 1
        if idx > 40:
            break

    return specs[:gap]


def main() -> int:
    if not MANIFEST.exists():
        print("Run scripts/build_cat25_research_manifest.py first.", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cat_meta = load_category_meta()
    writer = Cat25Writer(append=True)
    max_z, _, _ = scan_existing()
    new_sts: set[str] = set()
    summary: dict[str, int] = {}

    for sub_key in sorted(manifest["subcategories"], key=lambda x: int(x)):
        entry = manifest["subcategories"][sub_key]
        target = min(int(entry["target"]), MAX_PER_SUB)
        current = max_z.get(sub_key, 0)
        gap = target - current
        if gap <= 0:
            continue
        meta = cat_meta[sub_key]
        specs = build_gap_specs(sub_key, gap, entry, meta)
        refs = R(("Splunk HTTP Event Collector", "https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector"))
        added = 0
        prefix = meta["name"].split("&")[0].split(",")[0].strip()[:40]
        for spec in specs:
            title = str(spec["title"])
            if title in writer.titles:
                title = f"{prefix}: {title}"
            if title in writer.titles:
                title = f"{title} ({sub_key}.{current + added + 1})"
            writer.U(
                sub=sub_key,
                title=title,
                crit=str(spec["crit"]),
                diff=str(spec["diff"]),
                mtypes=list(spec["mtypes"]),  # type: ignore[arg-type]
                spl=str(spec["spl"]),
                desc=str(spec["desc"]),
                val=str(spec["val"]),
                impl=str(spec["impl"]),
                viz=str(spec["viz"]),
                grandma_body=str(spec["grandma_body"]),
                refs=refs,
                app=meta["app"],
                ds=meta["ds"],
            )
            added += 1
            for m in re.findall(r"sourcetype=([a-z0-9:_-]+)", str(spec["spl"])):
                new_sts.add(m)
        summary[sub_key] = added
        print(f"25.{sub_key}: +{added} (now {current + added}/{target})")

    total, by_sub = writer.summary()
    print(f"TOTAL_ADDED={total}")
    print(f"NEW_SOURCETYPES={json.dumps(sorted(new_sts))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
