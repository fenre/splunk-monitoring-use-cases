#!/usr/bin/env python3
"""Generate cat-25 wave8b use cases for subcategories 25.74-25.85."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from gen_cat25_common import CAT25, Cat25Writer, R

SCRIPT_PATH = Path(__file__).resolve()
META_PATH = SCRIPT_PATH.with_name("wave8b_subcategories.json")
TARGET_SUBS = tuple(str(i) for i in range(74, 86))
EXPECTED_PER_SUB = 28


def spl(*lines: str) -> str:
    return "\n".join(lines)


def S(
    title: str,
    crit: str,
    diff: str,
    mtypes: list[str],
    spl_query: str,
    desc: str,
    val: str,
    impl: str,
    viz: str,
    grandma_body: str,
    pillar: str = "Platform",
) -> dict[str, object]:
    return {
        "title": title,
        "crit": crit,
        "diff": diff,
        "mtypes": mtypes,
        "spl": spl_query,
        "desc": desc,
        "val": val,
        "impl": impl,
        "viz": viz,
        "grandma_body": grandma_body,
        "pillar": pillar,
    }


def base_search(focus: dict[str, object]) -> str:
    extra = str(focus.get("extra_search", "")).strip()
    clause = f"index=personal sourcetype={focus['source']}"
    if extra:
        clause = f"{clause} {extra}"
    return clause


def load_subcategory_meta() -> dict[str, dict[str, object]]:
    rows = json.loads(META_PATH.read_text(encoding="utf-8"))
    meta: dict[str, dict[str, object]] = {}
    for row in rows:
        sid = str(row["id"]).split(".")[-1]
        meta[sid] = row
    assert set(meta) == set(TARGET_SUBS)
    return meta


def clear_existing_targets() -> None:
    for sub in TARGET_SUBS:
        for path in CAT25.glob(f"UC-25.{sub}.*.json"):
            path.unlink()


def sync_category_metadata(meta: dict[str, dict[str, object]]) -> None:
    category_path = CAT25 / "_category.json"
    data = json.loads(category_path.read_text(encoding="utf-8"))
    by_id = {sub["id"]: sub for sub in data["subcategories"]}
    for sub in meta.values():
        payload = {
            "id": sub["id"],
            "name": sub["name"],
            "useCaseCount": sub["useCaseCount"],
            "primaryAppTa": sub["primaryAppTa"],
            "dataSources": sub["dataSources"],
        }
        if payload["id"] in by_id:
            by_id[payload["id"]].update(payload)
        else:
            data["subcategories"].append(payload)
    data["subcategories"].sort(
        key=lambda item: [int(part) for part in str(item["id"]).split(".")[1:]]
    )

    counts: Counter[str] = Counter()
    for path in CAT25.glob("UC-25.*.*.json"):
        match = re.match(r"UC-25\.(\d+)\.(\d+)\.json$", path.name)
        if match and match.group(1) in TARGET_SUBS:
            counts[match.group(1)] += 1

    for sub in data["subcategories"]:
        sub_num = str(sub["id"]).split(".")[-1]
        if sub_num in TARGET_SUBS:
            sub["useCaseCount"] = counts.get(sub_num, 0)
    data["useCaseCount"] = sum(int(sub["useCaseCount"]) for sub in data["subcategories"])
    category_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def performance_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus["metric_field"])
    metric_label = str(focus["metric_label"])
    group_field = str(focus.get("group_field", "category"))
    group_label = str(focus.get("group_label", "category"))
    actor_field = str(focus.get("actor_field", "athlete"))
    goal_value = float(focus.get("goal_value", 100))
    threshold_value = float(focus.get("threshold_value", goal_value))
    duration_field = str(focus.get("duration_field", "duration_min"))
    freshness_hours = int(focus.get("freshness_hours", 72))
    best_mode = str(focus.get("best_mode", "max"))
    better_word = "higher" if best_mode == "max" else "lower"
    sort_expr = "- avg_value" if best_mode == "max" else "avg_value"
    stream_fn = "max" if best_mode == "max" else "min"
    best_cmp = ">" if best_mode == "max" else "<"
    goal_eval = (
        f'| eval pct_of_goal=round(100*actual/{goal_value},1), goal_label="{goal_value:g}"'
        if best_mode == "max"
        else f'| eval pct_of_goal=round(100*{goal_value}/actual,1), goal_label="{goal_value:g}"'
    )
    return [
        S(
            f"{display} Weekly Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1w",
                f"| stats sum({metric}) as total_value avg({metric}) as avg_value count as sessions by _time",
                "| sort - _time",
            ),
            f"Trends {metric_label} week by week so you can see whether {display.lower()} is building, fading, or plateauing.",
            f"A weekly view turns isolated workouts or events into a training signal, making it easier to spot whether {display.lower()} is moving in the right direction.",
            f"Forward {display.lower()} into `index=personal`, keep `{metric}` populated, and review the weekly trend before planning the next block.",
            f"Line chart of weekly total and average {metric_label}.",
            f"how {display.lower()} changes from week to week so you can tell whether training or racing is moving the right way.",
        ),
        S(
            f"{display} Baseline Drift Alert",
            "medium",
            "advanced",
            ["Anomaly", "Risk"],
            spl(
                search,
                f"| timechart span=1d avg({metric}) as metric",
                "| eventstats avg(metric) as base, stdev(metric) as sd",
                "| eval delta=round(metric-base,2), drift=if(abs(delta)>2*sd,1,0)",
                "| where drift=1",
            ),
            f"Flags days where {display.lower()} moved far away from your recent baseline instead of staying within normal variation.",
            f"Large baseline drift is a quick way to surface bad days, breakout days, or sensor issues without waiting for a coach's manual review.",
            f"Schedule this daily after ingesting {display.lower()} events and investigate any drift days alongside notes about fatigue, travel, or conditions.",
            f"Timechart of daily {metric_label} with baseline and drift markers.",
            f"when {display.lower()} suddenly looks very different from your normal pattern.",
        ),
        S(
            f"{display} Goal Adherence by {group_label.title()}",
            "low",
            "intermediate",
            ["Analytics", "Business"],
            spl(
                search,
                f"| stats avg({metric}) as actual count as sessions by {group_field}",
                goal_eval,
                "| sort pct_of_goal",
            ),
            f"Compares average {metric_label} with a simple target for each {group_label}, showing where {display.lower()} is meeting plan and where it is lagging.",
            f"Splitting target adherence by {group_label} shows which contexts are helping you hit the plan and which ones need adjustment.",
            f"Set the target value in the query to match your routine, then review low-adherence {group_label} values before the next session block.",
            f"Table of {group_label} values with average {metric_label} and percent of goal.",
            f"which {group_label} settings help you hit your target for {display.lower()} and which ones fall short.",
        ),
        S(
            f"{display} {group_label.title()} Leaderboard",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as avg_value max({metric}) as peak_value count as sessions by {group_field}",
                f"| sort {sort_expr}",
            ),
            f"Ranks {group_label} values by average and peak {metric_label}, helping you see where {display.lower()} performs best.",
            f"A simple leaderboard is an easy way to see which {group_label} contexts are producing the strongest outcomes without deep analysis.",
            f"Populate `{group_field}` consistently from your export pipeline so the leaderboard can compare like with like.",
            f"Leaderboard table of {group_label}, average {metric_label}, and peak {metric_label}.",
            f"which {group_label} areas give you the strongest {display.lower()} results.",
        ),
        S(
            f"{display} Personal Best Detection",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            spl(
                search,
                "| sort 0 _time",
                f"| streamstats {stream_fn}({metric}) as prior_best current=f",
                f"| where isnotnull(prior_best) AND {metric}{best_cmp}prior_best",
                f"| table _time {group_field} {metric} prior_best",
            ),
            f"Scans your {display.lower()} history in time order and highlights any entry that set a new personal best using the {better_word} metric direction.",
            f"Automatic personal-best detection turns long history tables into a clean milestone log that is motivating and easy to review.",
            f"Keep the underlying metric normalized across sessions so the best-detection logic compares like events with like events.",
            f"Table of personal-best events with the previous best beside the new value.",
            f"the moments when {display.lower()} reached a new best for you.",
        ),
        S(
            f"{display} Import Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {actor_field}",
                '| eval hours_since=round((now()-last_seen)/3600,1)',
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects athletes, devices, or exports that have stopped sending {display.lower()} data within the expected freshness window.",
            f"Stale performance data hides missed sessions and broken syncs, so a freshness alert protects the trend lines you rely on.",
            f"Review this at least daily and tune the freshness threshold to the normal cadence of the underlying app or export job.",
            f"Table of {actor_field} values by hours since the last {display.lower()} event.",
            f"when data for {display.lower()} has stopped arriving and probably needs a sync check.",
        ),
        S(
            f"{display} Monthly Rollup",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1mon",
                f"| stats sum({metric}) as total_value avg({duration_field}) as avg_duration count as sessions by _time",
                "| sort - _time",
            ),
            f"Summarizes {display.lower()} by month so you can review season-to-date volume without digging through individual sessions.",
            f"A monthly rollup is useful for spotting big directional changes and for keeping a simple log of a long season.",
            f"Retain at least a season of history so month-over-month comparisons stay meaningful.",
            f"Column chart of monthly totals with average session duration overlaid.",
            f"the bigger month-by-month picture for {display.lower()} instead of one session at a time.",
        ),
    ]


def admin_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    item_plural = str(focus.get("item_plural", "items"))
    item_singular = str(focus.get("item_singular", "item"))
    status_field = str(focus.get("status_field", "status"))
    group_field = str(focus.get("group_field", "category"))
    group_label = str(focus.get("group_label", "category"))
    owner_field = str(focus.get("owner_field", "owner"))
    due_field = str(focus.get("due_field", "due_epoch"))
    complete_value = str(focus.get("complete_value", "complete"))
    freshness_hours = int(focus.get("freshness_hours", 168))
    return [
        S(
            f"{display} Sync Freshness Gap",
            "low",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {owner_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Shows which owners or feeds have stopped updating {display.lower()} records inside the expected time window.",
            f"Admin workflows fall apart quietly when the feed goes stale, so a freshness check is the easiest way to keep the tracker trustworthy.",
            f"Set the freshness threshold to match how often the admin system or checklist should update.",
            f"Table of {owner_field} values by hours since last {display.lower()} update.",
            f"when the records for {display.lower()} have gone quiet and might no longer be reliable.",
        ),
        S(
            f"{display} Due-Soon Queue",
            "medium",
            "beginner",
            ["Risk", "Compliance"],
            spl(
                search,
                f"| eval days_to_due=round(({due_field}-now())/86400,1)",
                f'| where days_to_due>=0 AND days_to_due<=14 AND {status_field}!="{complete_value}"',
                f"| table _time {group_field} {status_field} days_to_due",
                "| sort days_to_due",
            ),
            f"Builds a queue of {item_plural} that are due soon but not yet marked complete.",
            f"Due-soon queues are what keep small admin tasks from turning into expensive or embarrassing misses.",
            f"Populate `{due_field}` and normalize `{status_field}` so the queue only shows genuinely actionable work.",
            f"Table of due-soon {item_plural} sorted by days remaining.",
            f"which {item_plural} are coming due soon and still need attention.",
        ),
        S(
            f"{display} Overdue Aging by Status",
            "medium",
            "intermediate",
            ["Risk", "Analytics"],
            spl(
                search,
                f"| eval days_overdue=round((now()-{due_field})/86400,1)",
                "| where days_overdue>0",
                f"| stats avg(days_overdue) as avg_days_overdue max(days_overdue) as max_days_overdue count as items by {status_field}",
                "| sort - avg_days_overdue",
            ),
            f"Measures how long overdue {display.lower()} work is staying stuck in each status.",
            f"Aging by status shows whether the bottleneck is waiting on you, a vendor, a family member, or missing paperwork.",
            f"Review this weekly and tighten the workflow stage that owns the oldest overdue records.",
            f"Bar chart of average overdue days by status.",
            f"where overdue {item_plural} are getting stuck instead of moving to done.",
        ),
        S(
            f"{display} Monthly Throughput Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1mon",
                f'| stats count as items sum(eval(if({status_field}="{complete_value}",1,0))) as completed by _time',
                "| sort - _time",
            ),
            f"Tracks how many {item_plural} entered the system each month and how many actually got completed.",
            f"Throughput trend lines show whether the queue is shrinking, flat, or quietly becoming a backlog.",
            f"Use this after any process cleanup to see whether the change actually improved completion volume.",
            f"Column chart of monthly created versus completed {item_plural}.",
            f"whether you are clearing {item_plural} as fast as they arrive each month.",
        ),
        S(
            f"{display} Status Breakdown",
            "low",
            "beginner",
            ["Analytics", "Business"],
            spl(
                search,
                f"| stats count as items by {status_field}",
                "| eventstats sum(items) as total",
                "| eval pct=round(100*items/total,1)",
                "| sort - items",
            ),
            f"Shows the current mix of {display.lower()} records by status so blocked or incomplete work stands out quickly.",
            f"A status split is the fastest way to explain the shape of the queue without reading every record.",
            f"Keep status names small and well controlled so the split is readable and action-oriented.",
            f"Pie chart or bar chart of current records by status.",
            f"how your {item_plural} are spread across waiting, done, and stuck states.",
        ),
        S(
            f"{display} Completion SLA Drift",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            spl(
                search,
                "| where completion_hours=*",
                f"| stats avg(completion_hours) as avg_completion_hours max(completion_hours) as worst_completion_hours count as items by {group_field}",
                "| sort - avg_completion_hours",
            ),
            f"Compares how long different {group_label} groups of {item_plural} take to finish once they are started.",
            f"Completion-time drift reveals which classes of admin work are easy, which are annoying, and which need a better checklist.",
            f"Send `completion_hours` from your workflow export or derive it from created and completed timestamps.",
            f"Table of average and worst completion hours by {group_label}.",
            f"which kinds of {item_plural} take the longest to get over the finish line.",
        ),
        S(
            f"{display} Missing Metadata Exception Rate",
            "medium",
            "intermediate",
            ["Data Quality", "Audit"],
            spl(
                search,
                "| where required_fields_missing=*",
                f"| stats sum(required_fields_missing) as missing_fields count as items by {group_field}",
                "| eval avg_missing=round(missing_fields/items,2)",
                "| where avg_missing>0",
                "| sort - avg_missing",
            ),
            f"Highlights {display.lower()} records that routinely arrive with required fields missing.",
            f"Bad metadata is why personal admin trackers become untrustworthy, so exception rate is a useful hygiene metric.",
            f"Count missing required fields during ingest and write the total into `required_fields_missing` for each record.",
            f"Table of {group_label} values by average missing fields per record.",
            f"where the records behind {display.lower()} are missing important details and need cleanup.",
        ),
    ]


def finance_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    amount_field = str(focus.get("amount_field", "amount_usd"))
    client_field = str(focus.get("client_field", "client"))
    status_field = str(focus.get("status_field", "status"))
    final_value = str(focus.get("final_value", "paid"))
    group_field = str(focus.get("group_field", "category"))
    group_label = str(focus.get("group_label", "category"))
    due_field = str(focus.get("due_field", "due_epoch"))
    forecast_field = str(focus.get("forecast_field", "forecast_amount_usd"))
    lag_field = str(focus.get("lag_field", "lag_days"))
    freshness_hours = int(focus.get("freshness_hours", 72))
    return [
        S(
            f"{display} Monthly Amount Trend",
            "low",
            "beginner",
            ["Analytics", "Business"],
            spl(
                search,
                "| bin _time span=1mon",
                f"| stats sum({amount_field}) as amount count as records by _time",
                "| sort - _time",
            ),
            f"Trends the monthly dollar impact behind {display.lower()} so growth, slumps, and seasonality are obvious.",
            f"Month-level financial trending is the cleanest way to see whether a side hustle or household flow is genuinely changing.",
            f"Keep values normalized to a single currency before loading them into Splunk.",
            "Column chart of monthly amount with record counts.",
            f"how the money behind {display.lower()} changes month by month.",
        ),
        S(
            f"{display} Outstanding Balance by {client_field.title()}",
            "medium",
            "beginner",
            ["Risk", "Cost"],
            spl(
                search,
                f'| where {status_field}!="{final_value}"',
                f"| stats sum({amount_field}) as outstanding_amount count as open_records by {client_field}",
                "| sort - outstanding_amount",
            ),
            f"Ranks open {display.lower()} balances so you can see where the most money is still not settled.",
            f"Outstanding-balance ranking focuses your follow-up time where it matters most instead of on whatever record you looked at last.",
            f"Normalize `{status_field}` so only genuinely unresolved records remain in the outstanding queue.",
            f"Bar chart of outstanding amount by {client_field}.",
            f"who still owes money or has unresolved financial work in {display.lower()}.",
        ),
        S(
            f"{display} Overdue Alert",
            "high",
            "beginner",
            ["Risk", "Business"],
            spl(
                search,
                f'| where {status_field}!="{final_value}"',
                f"| eval days_overdue=round((now()-{due_field})/86400,1)",
                "| where days_overdue>0",
                f"| table _time {client_field} {amount_field} days_overdue",
                "| sort - days_overdue",
            ),
            f"Lists unresolved {display.lower()} records that are already past due and likely need immediate action.",
            f"Overdue financial items are where cashflow pain starts, so a short queue of exceptions is more useful than a long ledger.",
            f"Populate `{due_field}` from the source system and alert on anything beyond your tolerance.",
            f"Table of overdue records with amount and overdue age.",
            f"which {display.lower()} items are already late and need chasing now.",
        ),
        S(
            f"{display} Processing Lag Trend",
            "medium",
            "intermediate",
            ["Analytics", "Quality"],
            spl(
                search,
                f"| where {lag_field}=*",
                "| bin _time span=1mon",
                f"| stats avg({lag_field}) as avg_lag_days max({lag_field}) as worst_lag_days by _time",
                "| sort - _time",
            ),
            f"Tracks how long {display.lower()} items are taking to close, get paid, or get resolved.",
            f"Lag trend is a practical health metric because it shows whether the financial workflow is getting smoother or more clogged.",
            f"Write a numeric lag field during ingest or derive it from created and resolved timestamps.",
            "Line chart of monthly average and worst lag days.",
            f"whether {display.lower()} is getting handled quickly or dragging on too long.",
        ),
        S(
            f"{display} Forecast vs Actual",
            "medium",
            "intermediate",
            ["Analytics", "Business"],
            spl(
                search,
                f"| where {forecast_field}=*",
                "| bin _time span=1mon",
                f"| stats sum({forecast_field}) as forecast_amount sum({amount_field}) as actual_amount by _time",
                "| eval variance=round(actual_amount-forecast_amount,2)",
                "| sort - _time",
            ),
            f"Compares expected and actual amounts for {display.lower()} so planning accuracy becomes measurable.",
            f"Forecast variance helps you stop treating optimistic assumptions as plans and quickly shows which months missed badly.",
            f"Keep forecast values close to the event records they belong to instead of in a separate spreadsheet.",
            "Dual-axis chart of forecast, actual, and variance by month.",
            f"how close your expectations for {display.lower()} were to what really happened.",
        ),
        S(
            f"{display} {group_label.title()} Concentration",
            "low",
            "intermediate",
            ["Analytics", "Risk"],
            spl(
                search,
                f"| stats sum({amount_field}) as amount count as records by {group_field}",
                "| eventstats sum(amount) as total_amount",
                "| eval pct_of_total=round(100*amount/total_amount,1)",
                "| sort - pct_of_total",
            ),
            f"Shows how concentrated {display.lower()} value is in each {group_label} bucket.",
            f"Concentration risk matters in personal businesses because too much dependence on one {group_label} can make a quiet month painful.",
            f"Use stable group labels such as client segment, quarter, or service line for consistent trending.",
            f"Treemap or bar chart of amount share by {group_label}.",
            f"whether too much of {display.lower()} depends on one {group_label} bucket.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {client_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects source feeds or counterparties that have stopped producing {display.lower()} events inside the expected ingestion window.",
            f"Financial blind spots often start with a broken import, so freshness monitoring protects every report built on top of the feed.",
            f"Tune the freshness threshold to how often your invoicing, billing, or pipeline data should refresh.",
            f"Table of {client_field} values by hours since the last event.",
            f"when the stream for {display.lower()} has gone stale and might hide missing records.",
        ),
    ]


def weather_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus["metric_field"])
    metric_label = str(focus["metric_label"])
    freshness_hours = int(focus.get("freshness_hours", 36))
    return [
        S(
            f"{display} vs Temperature Correlation",
            "low",
            "intermediate",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as metric_value avg(temp_c) as avg_temp by day",
                "| stats corr(metric_value, avg_temp) as corr_value",
            ),
            f"Measures how strongly {metric_label} moves with local temperature across your daily weather-impact rollups.",
            f"Temperature correlation is the fastest way to test whether a weather hunch about {metric_label} is real or just memorable.",
            f"Build one daily record per day with both the personal metric and matched weather fields before running the correlation.",
            f"Single-value correlation panel for {metric_label} versus temperature.",
            f"whether hotter or colder weather usually goes along with better or worse {metric_label}.",
        ),
        S(
            f"{display} vs Humidity Correlation",
            "low",
            "intermediate",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as metric_value avg(humidity_pct) as avg_humidity by day",
                "| stats corr(metric_value, avg_humidity) as corr_value",
            ),
            f"Measures whether humidity is a meaningful driver of changes in {metric_label}.",
            f"Humidity can matter more than temperature for comfort, sleep, or activity, so it deserves its own correlation view.",
            f"Include indoor or outdoor humidity consistently from the same weather source when building the daily rollups.",
            f"Single-value correlation panel for {metric_label} versus humidity.",
            f"whether muggy days usually help or hurt your {metric_label}.",
        ),
        S(
            f"{display} Best Weather Window",
            "low",
            "beginner",
            ["Analytics", "Business"],
            spl(
                search,
                f"| stats avg({metric}) as avg_metric count as days by condition_bucket",
                "| sort - avg_metric",
            ),
            f"Ranks weather-condition buckets by average {metric_label} so your best-performing conditions are easy to spot.",
            f"This helps turn personal intuition into a decision aid for when to run, work, walk, or recover.",
            f"Define readable condition buckets such as cool-dry, warm-humid, windy, or rainy during the daily rollup stage.",
            f"Leaderboard of condition buckets by average {metric_label}.",
            f"which kinds of weather usually line up with your best {metric_label}.",
        ),
        S(
            f"{display} Poor-Weather Deviation Alert",
            "medium",
            "advanced",
            ["Anomaly", "Risk"],
            spl(
                search,
                f"| eventstats avg({metric}) as base, stdev({metric}) as sd by condition_bucket",
                f"| eval delta=round({metric}-base,2)",
                '| where severe_weather="yes" AND abs(delta)>2*sd',
                "| table _time condition_bucket severe_weather temp_c humidity_pct delta",
                "| sort - _time",
            ),
            f"Flags days where {metric_label} moved unusually far from its normal value during severe or uncomfortable weather.",
            f"Deviation alerts help separate ordinary bad days from weather-linked hits that are worth planning around.",
            f"Tag severe-weather days during ingest so the search can focus on the conditions most likely to matter.",
            f"Exception table of weather-stressed days and metric deviation.",
            f"when rough weather seems to have pushed your {metric_label} far away from normal.",
        ),
        S(
            f"{display} Condition Bucket Split",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as avg_metric count as days by condition_bucket",
                "| eventstats sum(days) as total_days",
                "| eval pct_days=round(100*days/total_days,1)",
                "| sort - days",
            ),
            f"Shows how much data you have in each weather bucket and what average {metric_label} looked like there.",
            f"Knowing the sample size behind each weather bucket helps you trust or discount apparent patterns.",
            f"Review sparse buckets carefully before acting on them; a tiny sample is often just noise.",
            f"Table of condition buckets with day counts and average {metric_label}.",
            f"how much of your data happened in each kind of weather and what your {metric_label} looked like there.",
        ),
        S(
            f"{display} Seasonal Baseline Drift",
            "low",
            "advanced",
            ["Analytics", "Anomaly"],
            spl(
                search,
                f"| stats avg({metric}) as avg_metric by season",
                "| eventstats avg(avg_metric) as overall_avg",
                "| eval delta=round(avg_metric-overall_avg,2)",
                "| sort - delta",
            ),
            f"Compares seasonal averages for {metric_label} against your overall norm so slow weather-linked drift becomes visible.",
            f"Seasonal drift is where long, subtle weather effects show up even when daily correlation looks weak.",
            f"Write a season label onto each daily record during ingest for easier quarterly review.",
            f"Bar chart of seasonal average {metric_label} versus overall baseline.",
            f"whether one season tends to push your {metric_label} noticeably up or down.",
        ),
        S(
            f"{display} Daily Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                "| stats max(_time) as last_seen by source_name",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects weather-impact feeds that have stopped producing daily records on schedule.",
            f"Correlation reports are useless when a weather or personal metric feed has quietly gone missing, so freshness has to come first.",
            f"Use a stable `source_name` field for each upstream weather or personal summary feed.",
            "Table of daily feeds by hours since last record.",
            f"when the data behind {display.lower()} is no longer arriving reliably each day.",
        ),
    ]


def community_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus.get("metric_field", "duration_hours"))
    metric_label = str(focus.get("metric_label", "participation"))
    member_field = str(focus.get("member_field", "member"))
    group_field = str(focus.get("group_field", "event_type"))
    group_label = str(focus.get("group_label", "event type"))
    location_field = str(focus.get("location_field", "location"))
    gap_days = int(focus.get("gap_days", 21))
    freshness_hours = int(focus.get("freshness_hours", 168))
    return [
        S(
            f"{display} Weekly Participation Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1w",
                f"| stats count as events sum({metric}) as total_metric by _time",
                "| sort - _time",
            ),
            f"Tracks weekly participation volume for {display.lower()} so momentum is easy to see.",
            f"Communities thrive on consistency, and a weekly trend shows whether the habit is strengthening or slipping.",
            f"Keep `{metric}` populated with the most meaningful contribution metric for the activity, such as miles, pages, or hours.",
            f"Column chart of weekly events and total {metric_label}.",
            f"whether {display.lower()} is happening regularly enough to stay part of your routine.",
        ),
        S(
            f"{display} No-Show Rate",
            "low",
            "intermediate",
            ["Analytics", "Risk"],
            spl(
                search,
                f"| stats count as rsvps sum(eval(if(attended=\"no\",1,0))) as no_shows by {location_field}",
                "| eval no_show_pct=round(100*no_shows/rsvps,1)",
                "| sort - no_show_pct",
            ),
            f"Calculates where {display.lower()} plans are most likely to turn into no-shows.",
            f"No-show tracking helps reveal whether the issue is venue, timing, commitment level, or overbooking.",
            f"Write a simple `attended=yes/no` field during event logging or check-in capture.",
            f"Table of {location_field} values by no-show percentage.",
            f"where plans around {display.lower()} most often fall through.",
        ),
        S(
            f"{display} Participation Gap Alert",
            "medium",
            "beginner",
            ["Availability", "Business"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {member_field}",
                "| eval days_since=round((now()-last_seen)/86400,1)",
                f"| where days_since>{gap_days}",
                "| sort - days_since",
            ),
            f"Flags members or households that have gone quiet on {display.lower()} longer than expected.",
            f"Gaps matter because belonging usually fades gradually; a gentle alert can help restart the habit before it disappears.",
            f"Adjust the gap threshold to the normal cadence of the club or activity.",
            f"Table of {member_field} values by days since last participation.",
            f"who has drifted away from {display.lower()} long enough to merit a nudge.",
        ),
        S(
            f"{display} {group_label.title()} Mix",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats count as events sum({metric}) as total_metric by {group_field}",
                "| sort - events",
            ),
            f"Shows how {display.lower()} is split across different {group_label} buckets.",
            f"Mix analysis makes it easy to see whether the activity is diverse and healthy or concentrated in one stale format.",
            f"Use stable group labels like club type, route, venue, or meeting format to keep the trend comparable over time.",
            f"Bar chart of events and total {metric_label} by {group_label}.",
            f"what kinds of {display.lower()} you do most often.",
        ),
        S(
            f"{display} Monthly Contribution Rollup",
            "low",
            "beginner",
            ["Analytics", "Business"],
            spl(
                search,
                "| bin _time span=1mon",
                f"| stats sum({metric}) as total_metric count as events dc({member_field}) as active_members by _time",
                "| sort - _time",
            ),
            f"Summarizes the monthly contribution behind {display.lower()}, including activity volume and active-member count.",
            f"Monthly rollups give you a simple stewardship view without needing to inspect every meeting or visit.",
            f"Review active-member count alongside the main metric to separate a busy month from one carried by a small core group.",
            f"Monthly chart of total {metric_label} and distinct active members.",
            f"the bigger monthly picture for {display.lower()} and how many people were involved.",
        ),
        S(
            f"{display} Guest Return Rate",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            spl(
                search,
                f"| stats sum(eval(if(guest_visit=\"yes\",1,0))) as guest_visits sum(eval(if(returned_after_guest=\"yes\",1,0))) as returned_guests by {group_field}",
                "| eval return_rate=round(100*returned_guests/guest_visits,1)",
                "| sort - return_rate",
            ),
            f"Measures how often first-time or guest visits to {display.lower()} turn into a return visit.",
            f"Return rate is a simple health metric for social groups because it captures whether the experience feels welcoming enough to repeat.",
            f"Capture a guest flag and a return flag during event logging or member check-in.",
            f"Table of {group_label} values by guest return rate.",
            f"which kinds of {display.lower()} make newcomers want to come back.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {location_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects stale check-in or attendance feeds for {display.lower()} before a whole week of activity disappears.",
            f"Personal community reporting only works when the check-ins keep flowing, so freshness monitoring protects every downstream chart.",
            f"Use a consistent location or source identifier for each check-in path or import job.",
            f"Table of sources or locations by hours since the last event.",
            f"when the data stream for {display.lower()} has stopped updating.",
        ),
    ]


def utility_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    amount_field = str(focus.get("amount_field", "bill_amount"))
    usage_field = str(focus.get("usage_field", "usage_units"))
    provider_field = str(focus.get("provider_field", "provider"))
    due_field = str(focus.get("due_field", "due_epoch"))
    rate_field = str(focus.get("rate_field", "unit_rate"))
    freshness_hours = int(focus.get("freshness_hours", 744))
    return [
        S(
            f"{display} Monthly Cost Trend",
            "medium",
            "beginner",
            ["Analytics", "Cost"],
            spl(
                search,
                "| bin _time span=1mon",
                f"| stats sum({amount_field}) as total_cost avg({usage_field}) as avg_usage by _time",
                "| sort - _time",
            ),
            f"Trends monthly cost and average usage behind {display.lower()} so household utility drift is easy to spot.",
            f"Monthly utility views catch slow bill creep that is hard to see when statements arrive one at a time.",
            f"Normalize units per commodity during ingest so monthly usage stays comparable.",
            "Dual-axis chart of monthly total cost and average usage.",
            f"how the cost behind {display.lower()} changes over time.",
        ),
        S(
            f"{display} Statement vs Meter Variance",
            "medium",
            "intermediate",
            ["Audit", "Data Quality"],
            spl(
                search,
                "| where statement_vs_meter_pct=*",
                f"| stats avg(statement_vs_meter_pct) as avg_variance_pct max(statement_vs_meter_pct) as worst_variance_pct by {provider_field}",
                "| sort - worst_variance_pct",
            ),
            f"Compares billed amounts or billed usage with your captured meter data for {display.lower()}.",
            f"Variance tracking is useful for catching bad reads, estimated bills, or a broken capture pipeline.",
            f"Write a precomputed `statement_vs_meter_pct` field during bill reconciliation or ingest processing.",
            f"Table of {provider_field} values by average and worst variance percent.",
            f"when the official statement for {display.lower()} does not match the usage you expected.",
        ),
        S(
            f"{display} Rate Change Watch",
            "medium",
            "beginner",
            ["Analytics", "Risk"],
            spl(
                search,
                f"| stats earliest({rate_field}) as start_rate latest({rate_field}) as current_rate by {provider_field}",
                "| eval rate_change_pct=round(100*(current_rate-start_rate)/start_rate,1)",
                "| sort - abs(rate_change_pct)",
            ),
            f"Measures how much the effective rate behind {display.lower()} has moved over the captured history.",
            f"Rate-plan changes are often where bill surprises start, so watching the rate itself is cleaner than only watching the total bill.",
            f"Store the effective unit rate for each bill or tariff update even when the provider site only shows the statement total.",
            f"Table of providers with starting rate, current rate, and percent change.",
            f"when the price behind {display.lower()} has changed more than you realized.",
        ),
        S(
            f"{display} Payment Overdue Alert",
            "high",
            "beginner",
            ["Risk", "Business"],
            spl(
                search,
                "| eval days_overdue=round((now()-due_epoch)/86400,1)",
                '| where payment_status!="paid" AND days_overdue>0',
                f"| table _time {provider_field} {amount_field} days_overdue",
                "| sort - days_overdue",
            ),
            f"Lists unpaid {display.lower()} items that are already past due.",
            f"Late utility payments are one of the easiest household problems to prevent with a small exception queue.",
            f"Map provider payment state into a simple `payment_status` field and populate `due_epoch` from the statement.",
            "Table of overdue utility payments by provider and overdue age.",
            f"which {display.lower()} bills are already late and should be handled first.",
        ),
        S(
            f"{display} Seasonal Usage Baseline",
            "low",
            "intermediate",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({usage_field}) as avg_usage by season",
                "| eventstats avg(avg_usage) as overall_usage",
                "| eval delta=round(avg_usage-overall_usage,2)",
                "| sort - delta",
            ),
            f"Shows how the usage behind {display.lower()} shifts by season compared with the annual average.",
            f"Seasonal baselines tell you whether a bill spike is expected weather behavior or a true anomaly worth investigating.",
            f"Populate a simple season field during ingest so the chart stays readable.",
            "Bar chart of seasonal average usage versus overall average.",
            f"whether one season regularly makes {display.lower()} much heavier or lighter than normal.",
        ),
        S(
            f"{display} Provider Mix",
            "low",
            "beginner",
            ["Analytics", "Cost"],
            spl(
                search,
                f"| stats sum({amount_field}) as total_cost avg({usage_field}) as avg_usage count as statements by {provider_field}",
                "| sort - total_cost",
            ),
            f"Compares providers or household accounts for {display.lower()} in one place.",
            f"A provider mix view makes it easy to see which account is driving the biggest share of household spend.",
            f"Use one provider or account label across bill, payment, and meter feeds so the mix aligns cleanly.",
            f"Bar chart of total cost by {provider_field}.",
            f"which providers or accounts drive most of your {display.lower()} cost.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {provider_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects providers or import paths that have stopped sending {display.lower()} data on time.",
            f"Bill tracking loses trust quickly when one portal or export quietly breaks, so freshness monitoring is essential.",
            f"Set the freshness threshold to your normal statement or tariff refresh cadence.",
            "Table of providers by hours since last utility event.",
            f"when the data feed for {display.lower()} has gone stale.",
        ),
    ]


def accessibility_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus.get("metric_field", "battery_pct"))
    metric_label = str(focus.get("metric_label", "device health"))
    device_field = str(focus.get("device_field", "device"))
    location_field = str(focus.get("location_field", "location"))
    due_field = str(focus.get("due_field", "next_service_epoch"))
    threshold_value = float(focus.get("threshold_value", 20))
    freshness_hours = int(focus.get("freshness_hours", 72))
    return [
        S(
            f"{display} Low-Level Alert",
            "high",
            "beginner",
            ["Safety", "Availability"],
            spl(
                search,
                f"| stats latest({metric}) as metric_value by {device_field}",
                f"| where metric_value<{threshold_value}",
                "| sort metric_value",
            ),
            f"Shows {display.lower()} devices that have fallen below a safe {metric_label} threshold.",
            f"Low-level alerts are essential for accessibility gear because failure usually becomes urgent at the worst possible moment.",
            f"Tune the threshold to the minimum safe operating level for each device family.",
            f"Table of devices with current {metric_label}.",
            f"which {display.lower()} devices are getting low enough to need attention soon.",
        ),
        S(
            f"{display} Daily Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| timechart span=1d avg({metric}) as avg_metric by {device_field}",
            ),
            f"Trends {metric_label} daily for {display.lower()} so slow deterioration is visible before it becomes an outage.",
            f"Daily trend lines are more useful than isolated checks because they show whether a problem is stable, worsening, or solved.",
            f"Retain at least a few weeks of history so you can compare normal decay with unusual drops.",
            f"Timechart of daily average {metric_label} by device.",
            f"how {display.lower()} health changes day by day.",
        ),
        S(
            f"{display} Service Due-Soon Queue",
            "medium",
            "beginner",
            ["Risk", "Compliance"],
            spl(
                search,
                f"| eval days_to_service=round(({due_field}-now())/86400,1)",
                "| where days_to_service>=0 AND days_to_service<=30",
                f"| table _time {device_field} {location_field} days_to_service",
                "| sort days_to_service",
            ),
            f"Builds a queue of {display.lower()} equipment with service or replacement due in the next month.",
            f"Service-due reminders keep support equipment dependable without relying on memory alone.",
            f"Feed the next service or replacement date from the vendor portal, care plan, or your own checklist export.",
            "Table of devices ordered by days until service.",
            f"which {display.lower()} items need servicing soon.",
        ),
        S(
            f"{display} Incident Rate",
            "medium",
            "intermediate",
            ["Reliability", "Analytics"],
            spl(
                search,
                "| where incident_count=*",
                "| bin _time span=1mon",
                f"| stats sum(incident_count) as incidents by _time {device_field}",
                "| where incidents>0",
                "| sort - _time",
            ),
            f"Tracks service incidents, faults, or problem reports for {display.lower()} by month.",
            f"Incident counts show which aid or device is quietly becoming unreliable, even before it fully fails.",
            f"Count any breakdown, missed alert, jam, or user-reported problem into `incident_count` during ingest.",
            "Monthly table of incidents by device.",
            f"which {display.lower()} devices are causing repeated trouble.",
        ),
        S(
            f"{display} Test Coverage",
            "low",
            "intermediate",
            ["Audit", "Quality"],
            spl(
                search,
                '| stats sum(eval(if(test_result="pass",1,0))) as passed count as tests by device',
                "| eval pass_pct=round(100*passed/tests,1)",
                "| sort - pass_pct",
            ),
            f"Measures how consistently {display.lower()} checks are being run and passing.",
            f"Regular testing matters because safety and mobility aids often look fine right up until they are not.",
            f"Write a simple `test_result=pass/fail` field whenever a manual or automatic test is recorded.",
            "Table of devices with total tests and pass percentage.",
            f"whether {display.lower()} checks are happening regularly and passing cleanly.",
        ),
        S(
            f"{display} Location Comparison",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as avg_metric count as readings by {location_field}",
                "| sort - avg_metric",
            ),
            f"Compares average {metric_label} across locations or contexts for {display.lower()} equipment.",
            f"Location comparison can surface one room, route, or usage pattern that is harder on the equipment than the rest.",
            f"Use stable location labels such as upstairs, vehicle, office, or travel kit during ingest.",
            "Bar chart of average metric by location.",
            f"where {display.lower()} performs best and where it seems more stressed.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {device_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects accessibility-device feeds that have stopped reporting inside the expected window.",
            f"A silent telemetry gap on support gear can hide low battery or missed service, so freshness should alert early.",
            f"Set freshness thresholds according to how often each device normally checks in.",
            "Table of devices by hours since last update.",
            f"when a {display.lower()} feed has gone quiet and may need checking.",
        ),
    ]


def property_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus.get("metric_field", "metric_value"))
    metric_label = str(focus.get("metric_label", "value"))
    group_field = str(focus.get("group_field", "segment"))
    group_label = str(focus.get("group_label", "segment"))
    status_field = str(focus.get("status_field", "status"))
    due_field = str(focus.get("due_field", "due_epoch"))
    threshold_expression = str(focus.get("threshold_expression", "metric>=0"))
    freshness_hours = int(focus.get("freshness_hours", 168))
    return [
        S(
            f"{display} Monthly Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| timechart span=1mon avg({metric}) as avg_metric",
            ),
            f"Trends {metric_label} for {display.lower()} over time so gradual drift is obvious.",
            f"Property decisions usually move slowly, which makes month-level trending more useful than isolated snapshots.",
            f"Retain enough history to compare current conditions with earlier seasons or search phases.",
            f"Line chart of monthly average {metric_label}.",
            f"how {display.lower()} is moving over time.",
        ),
        S(
            f"{display} Threshold Alert",
            "medium",
            "beginner",
            ["Risk", "Cost"],
            spl(
                search,
                f"| eval metric={metric}",
                f"| where {threshold_expression}",
                f"| table _time {group_field} metric",
                "| sort - _time",
            ),
            f"Flags records where {display.lower()} crossed a threshold you care about.",
            f"Threshold alerts are a practical way to turn slow property monitoring into timely action, whether the threshold is a rate, fee, or value band.",
            f"Set the threshold expression to match the trigger you actually care about before scheduling the search.",
            f"Exception table of threshold-crossing {display.lower()} records.",
            f"when {display.lower()} crosses a limit that matters to you.",
        ),
        S(
            f"{display} Baseline Drift",
            "low",
            "intermediate",
            ["Analytics", "Anomaly"],
            spl(
                search,
                f"| eventstats avg({metric}) as base, stdev({metric}) as sd",
                f"| eval delta=round({metric}-base,2)",
                "| where abs(delta)>2*sd",
                f"| table _time {group_field} {metric} delta",
                "| sort - _time",
            ),
            f"Highlights unusually large movement in {display.lower()} compared with its own baseline.",
            f"Baseline drift helps you see when a signal stopped behaving like background noise and started becoming decision-worthy.",
            f"Use this with a few months of history so the baseline is meaningful rather than fragile.",
            f"Table of outlier {display.lower()} records and delta from baseline.",
            f"when {display.lower()} moves much more than usual.",
        ),
        S(
            f"{display} Status Queue",
            "low",
            "beginner",
            ["Analytics", "Business"],
            spl(
                search,
                f"| stats count as records by {status_field}",
                "| sort - records",
            ),
            f"Shows the current shape of the workflow behind {display.lower()} using status counts.",
            f"A status queue is a useful control panel for slow, paperwork-heavy property processes because it shows what is waiting and what is done.",
            f"Map upstream statuses into a small, stable set to keep the chart readable.",
            "Bar chart of records by workflow status.",
            f"how work around {display.lower()} is spread across waiting and done states.",
        ),
        S(
            f"{display} {group_label.title()} Comparison",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats avg({metric}) as avg_metric count as records by {group_field}",
                "| sort - avg_metric",
            ),
            f"Compares {display.lower()} across {group_label} buckets in one place.",
            f"Side-by-side comparisons help you see whether one lender, area, fee type, or jurisdiction looks meaningfully different from the rest.",
            f"Use stable grouping values and clean them during ingest so the comparison stays trustworthy.",
            f"Comparison table of average {metric_label} by {group_label}.",
            f"which {group_label} buckets look best or worst for {display.lower()}.",
        ),
        S(
            f"{display} Due-Soon Queue",
            "medium",
            "beginner",
            ["Risk", "Compliance"],
            spl(
                search,
                f"| eval days_to_due=round(({due_field}-now())/86400,1)",
                "| where days_to_due>=0 AND days_to_due<=30",
                f"| table _time {group_field} days_to_due",
                "| sort days_to_due",
            ),
            f"Builds a short queue of upcoming deadlines tied to {display.lower()}.",
            f"Property work is deadline-heavy, so a due-soon queue keeps you from missing payments, approvals, or decision windows.",
            f"Populate `due_epoch` from the upstream portal or your checklist export.",
            "Table of upcoming deadlines by days remaining.",
            f"which {display.lower()} deadlines are coming up soon.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                f"| stats max(_time) as last_seen by {group_field}",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects stale feeds or segments for {display.lower()} before a key rate or deadline update gets missed.",
            f"Property dashboards are only useful when the feeds keep refreshing, especially when you are comparing active opportunities.",
            f"Set the freshness threshold to the natural cadence of the source, such as daily for rate watches or monthly for tax updates.",
            "Table of segments by hours since last update.",
            f"when the feed behind {display.lower()} has stopped updating on schedule.",
        ),
    ]


def knowledge_specs(focus: dict[str, object]) -> list[dict[str, object]]:
    search = base_search(focus)
    display = str(focus["display"])
    metric = str(focus.get("metric_field", "count_value"))
    metric_label = str(focus.get("metric_label", "output"))
    group_field = str(focus.get("group_field", "project"))
    group_label = str(focus.get("group_label", "project"))
    backlog_field = str(focus.get("backlog_field", "review_backlog"))
    orphan_field = str(focus.get("orphan_field", "orphan_pct"))
    streak_field = str(focus.get("streak_field", "streak_days"))
    freshness_hours = int(focus.get("freshness_hours", 48))
    return [
        S(
            f"{display} Weekly Output Trend",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1w",
                f"| stats sum({metric}) as total_output avg({metric}) as avg_output by _time",
                "| sort - _time",
            ),
            f"Tracks weekly {metric_label} for {display.lower()} so bursts and dry spells are easy to spot.",
            f"Knowledge work often feels fuzzy, and a simple output trend gives it a visible rhythm without overcomplicating things.",
            f"Choose a single primary metric per source, such as new notes, words, tasks completed, or notes reviewed.",
            f"Line chart of weekly total and average {metric_label}.",
            f"how much {display.lower()} output you are producing week by week.",
        ),
        S(
            f"{display} Review Backlog Alert",
            "medium",
            "intermediate",
            ["Risk", "Quality"],
            spl(
                search,
                f"| stats latest({backlog_field}) as review_backlog by vault",
                "| where review_backlog>0",
                "| sort - review_backlog",
            ),
            f"Shows where unread, unrevised, or unreviewed material is building up in {display.lower()}.",
            f"A review backlog is where note systems quietly turn from helpful to cluttered, so it is worth monitoring directly.",
            f"Write a numeric backlog count per vault, graph, or workspace during the daily export.",
            "Bar chart of review backlog by vault or workspace.",
            f"where {display.lower()} has started to pile up faster than you review it.",
        ),
        S(
            f"{display} Orphan or Untagged Rate",
            "low",
            "intermediate",
            ["Data Quality", "Analytics"],
            spl(
                search,
                f"| stats avg({orphan_field}) as orphan_rate by {group_field}",
                "| sort - orphan_rate",
            ),
            f"Measures how much of {display.lower()} is isolated, untagged, or otherwise hard to find later.",
            f"An orphan rate is a practical quality metric for second-brain systems because it captures future retrievability, not just raw volume.",
            f"Derive the orphan or untagged percentage during your vault export and store it alongside the summary event.",
            f"Table of {group_label} values by orphan or untagged percentage.",
            f"which parts of {display.lower()} are hardest to reconnect to later.",
        ),
        S(
            f"{display} Graph Growth by Month",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                "| bin _time span=1mon",
                f"| stats max({metric}) as month_end_value by _time",
                "| sort - _time",
            ),
            f"Shows month-end growth for the main {display.lower()} metric so long-term accumulation is easy to see.",
            f"Growth-by-month is a useful antidote to daily noise because it keeps the focus on the steady build of the knowledge base.",
            f"Use a stable month-end summary event if the source emits many small updates each day.",
            f"Line chart of month-end {metric_label}.",
            f"how your {display.lower()} system is growing over the long run.",
        ),
        S(
            f"{display} Streak Gap Alert",
            "medium",
            "beginner",
            ["Availability", "Business"],
            spl(
                search,
                f"| stats latest({streak_field}) as streak_days, max(_time) as last_seen by user",
                "| eval days_since=round((now()-last_seen)/86400,1)",
                "| where days_since>2",
                "| sort - days_since",
            ),
            f"Flags breaks in the routine behind {display.lower()} before a useful habit disappears.",
            f"Small habit gaps matter in note-taking systems because consistency usually drives the value more than occasional big sprints.",
            f"Capture a simple streak count or at least a last-activity timestamp during export.",
            "Table of users by current streak and days since last activity.",
            f"when the habit behind {display.lower()} has started to slip.",
        ),
        S(
            f"{display} {group_label.title()} Mix",
            "low",
            "beginner",
            ["Analytics"],
            spl(
                search,
                f"| stats sum({metric}) as total_output count as records by {group_field}",
                "| sort - total_output",
            ),
            f"Shows which {group_label} buckets account for most of the activity in {display.lower()}.",
            f"A mix view helps you see whether the system is supporting a balanced set of topics or collapsing into one narrow area.",
            f"Map project, tag, graph, or notebook labels consistently so the mix stays meaningful across exports.",
            f"Bar chart of total {metric_label} by {group_label}.",
            f"which {group_label} buckets dominate your {display.lower()} activity.",
        ),
        S(
            f"{display} Feed Freshness Gap",
            "medium",
            "beginner",
            ["Availability", "Data Quality"],
            spl(
                search,
                "| stats max(_time) as last_seen by source_name",
                "| eval hours_since=round((now()-last_seen)/3600,1)",
                f"| where hours_since>{freshness_hours}",
                "| sort - hours_since",
            ),
            f"Detects vault scans or export jobs that have stopped updating {display.lower()} on time.",
            f"Freshness monitoring matters because stale exports make a note system look healthier or busier than it really is.",
            f"Write a stable `source_name` for each exporter or workspace connector.",
            "Table of exporters by hours since last event.",
            f"when the data feed for {display.lower()} has gone stale.",
        ),
    ]


BUILDERS = {
    "performance": performance_specs,
    "admin": admin_specs,
    "finance": finance_specs,
    "weather": weather_specs,
    "community": community_specs,
    "utility": utility_specs,
    "accessibility": accessibility_specs,
    "property": property_specs,
    "knowledge": knowledge_specs,
}


REFS = {
    "74": R(
        ("TrainingPeaks", "https://www.trainingpeaks.com/"),
        ("RunSignup API", "https://runsignup.com/API"),
        ("World Athletics", "https://worldathletics.org/"),
    ),
    "75": R(
        ("KAYA", "https://kayaclimb.com/"),
        ("MoonBoard", "https://www.moonboard.com/"),
        ("8a.nu", "https://www.8a.nu/"),
        ("Tension Climbing", "https://tensionclimbing.com/"),
    ),
    "76": R(
        ("SwingVision", "https://swing.vision/"),
        ("UTR Sports", "https://www.utrsports.net/"),
        ("USA Pickleball", "https://usapickleball.org/"),
    ),
    "77": R(
        ("Arccos Golf", "https://www.arccosgolf.com/"),
        ("UDisc", "https://udisc.com/"),
        ("Garmin Golf", "https://www.garmin.com/en-US/c/sports-fitness/golf-gps-devices-smartwatches/"),
    ),
    "78": R(
        ("U.S. Department of State - Passports", "https://travel.state.gov/content/travel/en/passports.html"),
        ("FTC - Warranties", "https://consumer.ftc.gov/articles/warranties"),
        ("Vote.gov", "https://vote.gov/"),
    ),
    "79": R(
        ("IRS - Estimated taxes", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes"),
        ("FreshBooks - freelancer invoicing", "https://www.freshbooks.com/hub/invoicing/how-to-invoice-as-a-freelancer"),
        ("Upwork - freelance proposals", "https://www.upwork.com/resources/how-to-write-a-proposal"),
    ),
    "80": R(
        ("NOAA Weather API", "https://www.weather.gov/documentation/services-web-api"),
        ("Tempest API", "https://weatherflow.github.io/Tempest/api/"),
        ("CDC - Sleep", "https://www.cdc.gov/sleep/about_sleep/how_much_sleep.html"),
    ),
    "81": R(
        ("Meetup", "https://www.meetup.com/"),
        ("StoryGraph - book clubs", "https://thestorygraph.com/"),
        ("Makerspace.com", "https://makerspace.com/"),
    ),
    "82": R(
        ("U.S. Energy Information Administration", "https://www.eia.gov/"),
        ("EPA WaterSense", "https://www.epa.gov/watersense"),
        ("Home Assistant Utility Meter", "https://www.home-assistant.io/integrations/utility_meter/"),
    ),
    "83": R(
        ("NIDCD - Hearing aids", "https://www.nidcd.nih.gov/health/hearing-aids"),
        ("MedlinePlus - Wheelchairs", "https://medlineplus.gov/wheelchairsandmobilityaids.html"),
        ("ADA National Network", "https://adata.org/"),
    ),
    "84": R(
        ("CFPB - Mortgages", "https://www.consumerfinance.gov/owning-a-home/"),
        ("Zillow", "https://www.zillow.com/"),
        ("NAR - Home Buyers and Sellers", "https://www.nar.realtor/"),
    ),
    "85": R(
        ("Obsidian", "https://obsidian.md/"),
        ("Roam Research", "https://roamresearch.com/"),
        ("Logseq", "https://logseq.com/"),
        ("Zettelkasten Method", "https://zettelkasten.de/"),
    ),
}


FOCUSES = {
    "74": [
        {
            "kind": "performance",
            "display": "Race Result Finish Time",
            "source": "raceresult:event",
            "metric_field": "finish_time_min",
            "metric_label": "finish time in minutes",
            "group_field": "event_name",
            "group_label": "event",
            "actor_field": "athlete",
            "goal_value": 240,
            "threshold_value": 300,
            "duration_field": "distance_km",
            "best_mode": "min",
        },
        {
            "kind": "performance",
            "display": "TrainingPeaks TSS",
            "source": "trainingpeaks:workout",
            "metric_field": "tss",
            "metric_label": "training stress score",
            "group_field": "workout_type",
            "group_label": "workout type",
            "actor_field": "athlete",
            "goal_value": 65,
            "threshold_value": 110,
            "duration_field": "duration_min",
        },
        {
            "kind": "performance",
            "display": "Marathon Split Pace",
            "source": "race:split",
            "metric_field": "split_pace_min",
            "metric_label": "split pace in minutes per kilometre",
            "group_field": "checkpoint",
            "group_label": "checkpoint",
            "actor_field": "athlete",
            "goal_value": 5.3,
            "threshold_value": 6.0,
            "duration_field": "segment_km",
            "best_mode": "min",
        },
        {
            "kind": "admin",
            "display": "Bib Collection Readiness",
            "source": "race:bib",
            "item_plural": "bib pickups",
            "item_singular": "bib pickup",
            "status_field": "pickup_status",
            "group_field": "race_name",
            "group_label": "race",
            "owner_field": "athlete",
            "due_field": "pickup_deadline_epoch",
            "complete_value": "collected",
        },
    ],
    "75": [
        {
            "kind": "performance",
            "display": "Kaya Session Volume",
            "source": "kaya:session",
            "metric_field": "problems_completed",
            "metric_label": "problems completed",
            "group_field": "gym_area",
            "group_label": "gym area",
            "actor_field": "climber",
            "goal_value": 12,
            "threshold_value": 6,
            "duration_field": "duration_min",
        },
        {
            "kind": "performance",
            "display": "MoonBoard Benchmark Score",
            "source": "moonboard:session",
            "metric_field": "benchmark_points",
            "metric_label": "benchmark points",
            "group_field": "benchmark_grade",
            "group_label": "benchmark grade",
            "actor_field": "climber",
            "goal_value": 10,
            "threshold_value": 5,
            "duration_field": "attempts",
        },
        {
            "kind": "performance",
            "display": "8a.nu Send Grade",
            "source": "eighta:send",
            "metric_field": "grade_index",
            "metric_label": "send grade index",
            "group_field": "style",
            "group_label": "style",
            "actor_field": "climber",
            "goal_value": 18,
            "threshold_value": 12,
            "duration_field": "attempt_count",
        },
        {
            "kind": "performance",
            "display": "Hangboard Protocol Load",
            "source": "hangboard:protocol",
            "metric_field": "load_kg",
            "metric_label": "added load in kilograms",
            "group_field": "grip_type",
            "group_label": "grip type",
            "actor_field": "climber",
            "goal_value": 20,
            "threshold_value": 10,
            "duration_field": "hang_seconds",
        },
    ],
    "76": [
        {
            "kind": "performance",
            "display": "SwingVision Match Quality",
            "source": "swingvision:session",
            "metric_field": "shot_quality_score",
            "metric_label": "shot quality score",
            "group_field": "surface",
            "group_label": "surface",
            "actor_field": "player",
            "goal_value": 75,
            "threshold_value": 55,
            "duration_field": "duration_min",
        },
        {
            "kind": "performance",
            "display": "UTR Rating",
            "source": "utr:rating",
            "metric_field": "rating_value",
            "metric_label": "UTR rating",
            "group_field": "season",
            "group_label": "season",
            "actor_field": "player",
            "goal_value": 7,
            "threshold_value": 5,
            "duration_field": "match_count",
        },
        {
            "kind": "performance",
            "display": "Racket Session Duration",
            "source": "racket:session",
            "metric_field": "duration_min",
            "metric_label": "session duration in minutes",
            "group_field": "sport",
            "group_label": "sport",
            "actor_field": "player",
            "goal_value": 90,
            "threshold_value": 45,
            "duration_field": "rally_count",
        },
        {
            "kind": "admin",
            "display": "Racket Stringing Service",
            "source": "stringing:service",
            "item_plural": "stringing jobs",
            "item_singular": "stringing job",
            "status_field": "service_status",
            "group_field": "racket_name",
            "group_label": "racket",
            "owner_field": "player",
            "due_field": "next_restring_epoch",
            "complete_value": "done",
        },
    ],
    "77": [
        {
            "kind": "performance",
            "display": "Golf Round Strokes Gained",
            "source": "golf:round",
            "metric_field": "strokes_gained_total",
            "metric_label": "strokes gained",
            "group_field": "course_name",
            "group_label": "course",
            "actor_field": "player",
            "goal_value": 0.5,
            "threshold_value": -2,
            "duration_field": "round_minutes",
        },
        {
            "kind": "performance",
            "display": "UDisc Round Rating",
            "source": "udisc:round",
            "metric_field": "round_rating",
            "metric_label": "round rating",
            "group_field": "course_name",
            "group_label": "course",
            "actor_field": "player",
            "goal_value": 930,
            "threshold_value": 850,
            "duration_field": "throws",
        },
        {
            "kind": "performance",
            "display": "Launch Monitor Ball Speed",
            "source": "launchmonitor:shot",
            "metric_field": "ball_speed_mph",
            "metric_label": "ball speed in miles per hour",
            "group_field": "club",
            "group_label": "club",
            "actor_field": "player",
            "goal_value": 145,
            "threshold_value": 120,
            "duration_field": "carry_yards",
        },
        {
            "kind": "performance",
            "display": "Handicap Index",
            "source": "handicap:index",
            "metric_field": "handicap_index",
            "metric_label": "handicap index",
            "group_field": "season",
            "group_label": "season",
            "actor_field": "player",
            "goal_value": 12,
            "threshold_value": 20,
            "duration_field": "round_count",
            "best_mode": "min",
        },
    ],
    "78": [
        {
            "kind": "admin",
            "display": "Passport Renewal Status",
            "source": "passport:status",
            "item_plural": "passport records",
            "item_singular": "passport record",
            "status_field": "renewal_status",
            "group_field": "family_member",
            "group_label": "family member",
            "owner_field": "household",
            "due_field": "expiry_epoch",
            "complete_value": "renewed",
        },
        {
            "kind": "admin",
            "display": "Warranty Registration Workflow",
            "source": "warranty:registration",
            "item_plural": "warranty registrations",
            "item_singular": "warranty registration",
            "status_field": "registration_status",
            "group_field": "product_type",
            "group_label": "product type",
            "owner_field": "household",
            "due_field": "registration_deadline_epoch",
            "complete_value": "registered",
        },
        {
            "kind": "admin",
            "display": "Document Scan Index",
            "source": "documentscan:index",
            "item_plural": "document scans",
            "item_singular": "document scan",
            "status_field": "index_status",
            "group_field": "document_type",
            "group_label": "document type",
            "owner_field": "household",
            "due_field": "review_due_epoch",
            "complete_value": "indexed",
        },
        {
            "kind": "admin",
            "display": "Voter Registration Readiness",
            "source": "voter:registration",
            "item_plural": "voter records",
            "item_singular": "voter record",
            "status_field": "registration_status",
            "group_field": "jurisdiction",
            "group_label": "jurisdiction",
            "owner_field": "household",
            "due_field": "election_deadline_epoch",
            "complete_value": "registered",
        },
    ],
    "79": [
        {
            "kind": "finance",
            "display": "Freelance Invoice Cashflow",
            "source": "freelance:invoice",
            "amount_field": "amount_usd",
            "client_field": "client",
            "status_field": "invoice_status",
            "final_value": "paid",
            "group_field": "service_line",
            "group_label": "service line",
            "due_field": "due_epoch",
            "forecast_field": "forecast_amount_usd",
            "lag_field": "paid_lag_days",
        },
        {
            "kind": "finance",
            "display": "Billed Hours Utilization",
            "source": "freelance:hours",
            "amount_field": "hours_billed",
            "client_field": "client",
            "status_field": "billing_status",
            "final_value": "invoiced",
            "group_field": "project",
            "group_label": "project",
            "due_field": "invoice_due_epoch",
            "forecast_field": "planned_hours",
            "lag_field": "capture_lag_days",
        },
        {
            "kind": "finance",
            "display": "Quarterly Tax Estimate",
            "source": "freelance:tax",
            "amount_field": "tax_due_usd",
            "client_field": "tax_year",
            "status_field": "payment_status",
            "final_value": "paid",
            "group_field": "quarter",
            "group_label": "quarter",
            "due_field": "quarter_due_epoch",
            "forecast_field": "projected_tax_usd",
            "lag_field": "filing_lag_days",
        },
        {
            "kind": "finance",
            "display": "Client Pipeline Value",
            "source": "freelance:lead",
            "amount_field": "pipeline_value_usd",
            "client_field": "lead_name",
            "status_field": "lead_status",
            "final_value": "won",
            "group_field": "stage",
            "group_label": "stage",
            "due_field": "next_action_epoch",
            "forecast_field": "expected_value_usd",
            "lag_field": "stage_age_days",
        },
    ],
    "80": [
        {
            "kind": "weather",
            "display": "Sleep Hours Weather Impact",
            "source": "personalweather:sleep",
            "metric_field": "sleep_hours",
            "metric_label": "sleep hours",
        },
        {
            "kind": "weather",
            "display": "Step Count Weather Impact",
            "source": "personalweather:steps",
            "metric_field": "steps",
            "metric_label": "daily steps",
        },
        {
            "kind": "weather",
            "display": "Mood Score Weather Impact",
            "source": "personalweather:mood",
            "metric_field": "mood_score",
            "metric_label": "mood score",
        },
        {
            "kind": "weather",
            "display": "Outdoor Comfort Score",
            "source": "personalweather:daily",
            "metric_field": "outdoor_comfort_score",
            "metric_label": "outdoor comfort score",
        },
    ],
    "81": [
        {
            "kind": "community",
            "display": "Book Club Attendance",
            "source": "bookclub:meeting",
            "metric_field": "pages_read",
            "metric_label": "pages read",
            "member_field": "member",
            "group_field": "book_title",
            "group_label": "book",
            "location_field": "venue",
        },
        {
            "kind": "community",
            "display": "Running Club Miles",
            "source": "runningclub:session",
            "metric_field": "distance_km",
            "metric_label": "club kilometres",
            "member_field": "runner",
            "group_field": "route_name",
            "group_label": "route",
            "location_field": "meet_point",
        },
        {
            "kind": "community",
            "display": "Maker Space Visits",
            "source": "makerspace:visit",
            "metric_field": "duration_hours",
            "metric_label": "visit hours",
            "member_field": "member",
            "group_field": "shop_area",
            "group_label": "shop area",
            "location_field": "site",
        },
        {
            "kind": "community",
            "display": "Social Club Attendance",
            "source": "club:attendance",
            "metric_field": "attendance_count",
            "metric_label": "attendance count",
            "member_field": "member",
            "group_field": "club_type",
            "group_label": "club type",
            "location_field": "venue",
        },
    ],
    "82": [
        {
            "kind": "utility",
            "display": "Electric Bill Tracking",
            "source": "utility:bill",
            "extra_search": 'bill_type="electric"',
            "amount_field": "bill_amount",
            "usage_field": "usage_kwh",
            "provider_field": "provider",
            "rate_field": "rate_per_kwh",
        },
        {
            "kind": "utility",
            "display": "Gas Bill Tracking",
            "source": "utility:bill",
            "extra_search": 'bill_type="gas"',
            "amount_field": "bill_amount",
            "usage_field": "usage_therms",
            "provider_field": "provider",
            "rate_field": "rate_per_therm",
        },
        {
            "kind": "utility",
            "display": "Water Bill Tracking",
            "source": "utility:bill",
            "extra_search": 'bill_type="water"',
            "amount_field": "bill_amount",
            "usage_field": "usage_gallons",
            "provider_field": "provider",
            "rate_field": "rate_per_gallon",
        },
        {
            "kind": "utility",
            "display": "Utility Rate Plan",
            "source": "utility:rate",
            "amount_field": "estimated_bill_amount",
            "usage_field": "projected_usage_units",
            "provider_field": "provider",
            "rate_field": "unit_rate",
        },
    ],
    "83": [
        {
            "kind": "accessibility",
            "display": "Wheelchair Battery Health",
            "source": "wheelchair:battery",
            "metric_field": "battery_pct",
            "metric_label": "battery percentage",
            "device_field": "chair_id",
            "location_field": "location",
            "due_field": "next_service_epoch",
            "threshold_value": 25,
        },
        {
            "kind": "accessibility",
            "display": "Stairlift Service Readiness",
            "source": "stairlift:service",
            "metric_field": "health_score",
            "metric_label": "health score",
            "device_field": "stairlift_id",
            "location_field": "home_area",
            "due_field": "next_service_epoch",
            "threshold_value": 80,
        },
        {
            "kind": "accessibility",
            "display": "Hearing Aid Battery Cycle",
            "source": "hearingaid:battery",
            "metric_field": "battery_pct",
            "metric_label": "battery percentage",
            "device_field": "aid_id",
            "location_field": "kit_name",
            "due_field": "replacement_due_epoch",
            "threshold_value": 20,
        },
        {
            "kind": "accessibility",
            "display": "Pendant Alert Test Reliability",
            "source": "pendant:test",
            "metric_field": "signal_strength_pct",
            "metric_label": "signal strength percentage",
            "device_field": "pendant_id",
            "location_field": "test_zone",
            "due_field": "next_test_epoch",
            "threshold_value": 70,
        },
    ],
    "84": [
        {
            "kind": "property",
            "display": "Mortgage Rate Watch",
            "source": "mortgage:rate",
            "metric_field": "rate_pct",
            "metric_label": "mortgage rate percentage",
            "group_field": "lender",
            "group_label": "lender",
            "status_field": "quote_status",
            "due_field": "lock_expiry_epoch",
            "threshold_expression": "metric<=6.0",
        },
        {
            "kind": "property",
            "display": "Zestimate Trend",
            "source": "property:listing",
            "metric_field": "zestimate_usd",
            "metric_label": "Zestimate in dollars",
            "group_field": "zip_code",
            "group_label": "zip code",
            "status_field": "listing_status",
            "due_field": "offer_deadline_epoch",
            "threshold_expression": "metric>=750000",
        },
        {
            "kind": "property",
            "display": "HOA Fee Drift",
            "source": "hoa:fee",
            "metric_field": "fee_amount_usd",
            "metric_label": "HOA fee in dollars",
            "group_field": "association_name",
            "group_label": "association",
            "status_field": "fee_status",
            "due_field": "next_due_epoch",
            "threshold_expression": "metric>=450",
        },
        {
            "kind": "property",
            "display": "Property Tax Installment",
            "source": "propertytax:installment",
            "metric_field": "installment_amount_usd",
            "metric_label": "installment amount in dollars",
            "group_field": "county",
            "group_label": "county",
            "status_field": "payment_status",
            "due_field": "installment_due_epoch",
            "threshold_expression": "metric>=3000",
        },
    ],
    "85": [
        {
            "kind": "knowledge",
            "display": "Obsidian Graph Stats",
            "source": "obsidian:stats",
            "metric_field": "new_notes",
            "metric_label": "new notes",
            "group_field": "vault",
            "group_label": "vault",
            "backlog_field": "review_backlog",
            "orphan_field": "orphan_pct",
            "streak_field": "streak_days",
        },
        {
            "kind": "knowledge",
            "display": "Roam Daily Notes",
            "source": "roam:daily",
            "metric_field": "daily_note_words",
            "metric_label": "daily note words",
            "group_field": "graph_name",
            "group_label": "graph",
            "backlog_field": "review_backlog",
            "orphan_field": "untagged_pct",
            "streak_field": "streak_days",
        },
        {
            "kind": "knowledge",
            "display": "Logseq Task Throughput",
            "source": "logseq:task",
            "metric_field": "completed_tasks",
            "metric_label": "completed tasks",
            "group_field": "project",
            "group_label": "project",
            "backlog_field": "open_task_backlog",
            "orphan_field": "unlinked_pct",
            "streak_field": "streak_days",
        },
        {
            "kind": "knowledge",
            "display": "Zettelkasten Note Count",
            "source": "zettel:note",
            "metric_field": "notes_added",
            "metric_label": "notes added",
            "group_field": "slipbox",
            "group_label": "slipbox",
            "backlog_field": "review_backlog",
            "orphan_field": "orphan_pct",
            "streak_field": "streak_days",
        },
    ],
}


def build_specs_for_sub(sub: str) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for focus in FOCUSES[sub]:
        specs.extend(BUILDERS[str(focus["kind"])](focus))
    assert len(specs) == EXPECTED_PER_SUB, f"expected {EXPECTED_PER_SUB} specs for 25.{sub}, found {len(specs)}"
    return specs


def main() -> int:
    meta = load_subcategory_meta()
    clear_existing_targets()
    writer = Cat25Writer(append=False)
    created: list[str] = []
    for sub in TARGET_SUBS:
        specs = build_specs_for_sub(sub)
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
                    refs=REFS[sub],
                    app=str(meta[sub]["primaryAppTa"]),
                    ds=str(meta[sub]["dataSources"]),
                    pillar=str(spec["pillar"]),
                )
            )
    sync_category_metadata(meta)
    total_added, by_sub = writer.summary()
    print(f"script_path={SCRIPT_PATH}")
    print(f"new_use_cases={total_added}")
    for sub in TARGET_SUBS:
        print(f"25.{sub}=+{by_sub.get(sub, 0)}")
    print(f"first_id={created[0]}")
    print(f"last_id={created[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
