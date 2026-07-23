#!/usr/bin/env python3
"""Wave 9A: deepen cat-25 subcategories 25.61–25.85 from 28 to 33 (+5 each)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from gen_cat25_common import CAT25, Cat25Writer, R

TARGET_SUBS = tuple(str(i) for i in range(61, 86))
EXPECTED_PER_SUB = 5


def spl(*lines: str) -> str:
    return "\n".join(lines)


def load_sub_meta() -> dict[str, dict[str, str]]:
    data = json.loads((CAT25 / "_category.json").read_text(encoding="utf-8"))
    meta: dict[str, dict[str, str]] = {}
    for sub in data["subcategories"]:
        num = str(sub["id"]).split(".")[-1]
        if num in TARGET_SUBS:
            meta[num] = {
                "name": sub["name"],
                "app": sub["primaryAppTa"],
                "ds": sub["dataSources"],
            }
    assert len(meta) == len(TARGET_SUBS)
    return meta


def sourcetypes_for_sub(sub: str) -> list[str]:
    found: list[str] = []
    for path in sorted(CAT25.glob(f"UC-25.{sub}.*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for blob in (doc.get("spl", ""), doc.get("dataSources", "")):
            for match in re.finditer(r"sourcetype=(?:\"([^\"]+)\"|(\S+))", str(blob)):
                st = match.group(1) or match.group(2)
                st = st.strip("\"'")
                if st and st not in found:
                    found.append(st)
    return found


def deepen_specs(sub: str, sub_name: str, sts: list[str]) -> list[dict[str, object]]:
    primary = sts[0]
    secondary = sts[1] if len(sts) > 1 else primary
    friendly = sub_name.split("&")[0].strip().lower()
    return [
        {
            "title": f"{sub_name} Quarter-over-Quarter Volume Shift",
            "crit": "low",
            "diff": "intermediate",
            "mtypes": ["Analytics"],
            "spl": spl(
                f"index=personal sourcetype={primary}",
                "| bin _time span=1q",
                "| stats count as events by _time",
                "| streamstats current=f last(events) as prev_q by _time",
                "| eval qoq_pct=round(100*(events-prev_q)/prev_q,1)",
                "| where isnotnull(prev_q) AND prev_q>0",
                "| sort - _time",
            ),
            "desc": f"Compares event volume quarter over quarter for {friendly} telemetry in index=personal.",
            "val": (
                "Seasonal life domains swing a lot; a quarter view separates real habit change "
                "from normal summer/winter noise without overreacting to one bad week."
            ),
            "impl": (
                f"Keep `{primary}` events flowing into `index=personal` with stable timestamps, "
                "then review QoQ percent change during quarterly personal ops reviews."
            ),
            "viz": "Column chart of events by quarter with QoQ percent labels.",
            "grandma_body": (
                f"how much your {friendly} activity changed compared with last quarter "
                "so you can tell a real shift from normal seasonal ups and downs."
            ),
        },
        {
            "title": f"{sub_name} Hour-of-Day Activity Heatmap",
            "crit": "low",
            "diff": "beginner",
            "mtypes": ["Analytics", "Operations"],
            "spl": spl(
                f"index=personal sourcetype={primary}",
                "| eval hour=strftime(_time,\"%H\")",
                "| stats count as events by hour",
                "| sort hour",
            ),
            "desc": f"Shows which hours of the day most {friendly} events typically arrive.",
            "val": (
                "Hour-of-day patterns expose automation schedules, commute windows, "
                "and habits that are easy to miss in daily totals alone."
            ),
            "impl": (
                f"Ingest `{primary}` with accurate `_time` values and chart hourly counts "
                "to see when the feed is naturally busy or quiet."
            ),
            "viz": "Heatmap or bar chart of event count by hour of day.",
            "grandma_body": (
                f"what time of day your {friendly} data is usually busiest "
                "so you can spot routines that moved or feeds that went quiet at the wrong hour."
            ),
        },
        {
            "title": f"{sub_name} Weekend vs Weekday Split",
            "crit": "low",
            "diff": "beginner",
            "mtypes": ["Analytics"],
            "spl": spl(
                f"index=personal sourcetype={primary}",
                '| eval day_type=if(in(strftime(_time,"%u"),"6","7"),"weekend","weekday")',
                "| stats count as events, avg(duration_min) as avg_duration by day_type",
            ),
            "desc": f"Separates {friendly} activity between weekdays and weekends when duration is present.",
            "val": (
                "Weekend/weekday splits quickly show whether a life domain is work-driven, "
                "leisure-driven, or bleeding into the wrong days."
            ),
            "impl": (
                f"Populate optional `duration_min` on `{primary}` events if available; "
                "the search still works on counts alone when duration is missing."
            ),
            "viz": "Side-by-side bar chart of weekday vs weekend event counts.",
            "grandma_body": (
                f"whether your {friendly} activity mostly happens on weekdays or weekends "
                "so you can see if the habit fits the life you actually live."
            ),
        },
        {
            "title": f"{sub_name} Longest Quiet Streak",
            "crit": "medium",
            "diff": "advanced",
            "mtypes": ["Anomaly", "Availability"],
            "spl": spl(
                f"index=personal sourcetype={primary}",
                "| bin _time span=1d",
                "| stats count as events by _time",
                "| sort _time",
                "| streamstats current=f last(_time) as prev_day last(events) as prev_events",
                "| eval gap_days=round((_time-prev_day)/86400,0)",
                "| where isnotnull(prev_day) AND prev_events>0 AND events=0 AND gap_days>=2",
                "| stats max(gap_days) as longest_quiet_streak_days",
            ),
            "desc": f"Finds the longest multi-day gap with zero {friendly} events after activity was previously present.",
            "val": (
                "Quiet streaks often mean a broken export, a forgotten subscription, "
                "or a habit that silently died — all worth catching early."
            ),
            "impl": (
                f"Run daily on `{primary}` after ingestion; investigate streaks that exceed "
                "your normal pause window for this domain."
            ),
            "viz": "Single-value tile for longest quiet streak with supporting timeline.",
            "grandma_body": (
                f"the longest stretch with no {friendly} activity at all "
                "so you can tell when a feed or habit went quiet for too long."
            ),
        },
        {
            "title": f"{sub_name} Cross-Feed Daily Correlation",
            "crit": "low",
            "diff": "advanced",
            "mtypes": ["Analytics"],
            "spl": spl(
                f"(index=personal sourcetype={primary}) OR (index=personal sourcetype={secondary})",
                "| bin _time span=1d",
                f'| eval feed=case(sourcetype="{primary}","primary",sourcetype="{secondary}","secondary",1=1,"other")',
                "| stats count as events by _time feed",
                "| chart sum(events) over _time by feed",
            ),
            "desc": (
                f"Lines up daily volume from {primary} and {secondary} "
                f"to see whether two {friendly} feeds move together."
            ),
            "val": (
                "When two related exports diverge — one busy, one silent — "
                "it usually means a connector broke on only one path."
            ),
            "impl": (
                f"Forward both `{primary}` and `{secondary}` into `index=personal` "
                "and compare daily counts on one chart."
            ),
            "viz": "Dual-line chart of daily events per sourcetype.",
            "grandma_body": (
                f"whether your two main {friendly} data feeds rise and fall together "
                "or if one of them quietly stopped keeping up."
            ),
        },
    ]


def main() -> int:
    meta = load_sub_meta()
    writer = Cat25Writer(append=True)
    created: list[str] = []

    for sub in TARGET_SUBS:
        sts = sourcetypes_for_sub(sub)
        assert sts, f"no sourcetypes found for 25.{sub}"
        specs = deepen_specs(sub, meta[sub]["name"], sts)
        assert len(specs) == EXPECTED_PER_SUB
        for spec in specs:
            created.append(
                writer.U(
                    sub=sub,
                    title=str(spec["title"]),
                    crit=str(spec["crit"]),
                    diff=str(spec["diff"]),
                    mtypes=list(spec["mtypes"]),
                    spl=str(spec["spl"]),
                    desc=str(spec["desc"]),
                    val=str(spec["val"]),
                    impl=str(spec["impl"]),
                    viz=str(spec["viz"]),
                    grandma_body=str(spec["grandma_body"]),
                    refs=R(
                        ("Splunk Search Reference", "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual"),
                    ),
                    app=meta[sub]["app"],
                    ds=meta[sub]["ds"],
                )
            )

    total, by_sub = writer.summary()
    print(f"new_use_cases={total}")
    for sub in TARGET_SUBS:
        print(f"25.{sub}=+{by_sub.get(sub, 0)}")
    print(f"first_id={created[0]}")
    print(f"last_id={created[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
