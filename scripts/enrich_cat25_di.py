#!/usr/bin/env python3
"""
Batch enrich cat-25 (Personal & Hobbyist Monitoring) use cases to Silver tier.

For each UC under content/cat-25-personal-hobbyist-monitoring/:
  1. Repair common SPL syntax issues (missing pipes, stray sourcetype parens).
  2. Write a 5-step detailedImplementation grounded in the UC's SPL and metadata.
  3. Add Silver-required fields when absent: wave, prerequisiteUseCases, equipment.

Reuses the SPL parser from enrich_di_gold_v2.py.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from enrich_di_gold_v2 import (  # noqa: E402
    SplAnalysis,
    classify_spl_pattern,
    fmt_time_window,
    integrate_visualization,
    parse_spl,
)
from equipment_lib import compile_patterns, load_equipment, match_equipment  # noqa: E402

BASE = _REPO / "content" / "cat-25-personal-hobbyist-monitoring"
CATEGORY_JSON = BASE / "_category.json"

SPL_CMDS = re.compile(
    r"^(eval|stats|where|bin|chart|timechart|sort|table|fields|rename|dedup|head|tail|"
    r"join|lookup|eventstats|streamstats|transaction|append|fillnull|coalesce|rex|"
    r"spath|mvexpand|makemv|convert|replace|regex|format|outlier|predict|trendline|"
    r"contingency|correlation|delta)\b",
    re.IGNORECASE,
)

# Prefix → ingestion playbook for personal/hobbyist sourcetypes.
PERSONAL_KB: dict[str, dict] = {
    "strava": {
        "product": "Strava",
        "method": "REST API or webhook → Splunk HEC scripted input",
        "endpoint": "GET https://www.strava.com/api/v3/athlete/activities",
        "interval": "900s (or push via Strava webhook subscription)",
        "key_fields": "type, distance_km, moving_time_s, start_date, athlete_id",
        "validate_ui": "Strava app → You → Activities list for the same week totals",
    },
    "garmin": {
        "product": "Garmin Connect",
        "method": "Garmin Health API or third-party export → HEC",
        "endpoint": "Garmin Connect IQ / Health API activity summaries",
        "interval": "3600s",
        "key_fields": "activityType, distance, duration, startTimeGMT",
        "validate_ui": "Garmin Connect → Activities calendar",
    },
    "fitbit": {
        "product": "Fitbit Web API",
        "method": "OAuth2 REST poll → HEC",
        "endpoint": "GET /1/user/-/activities/list.json",
        "interval": "3600s",
        "key_fields": "activityName, distance, duration, startTime",
        "validate_ui": "Fitbit app → Exercise history",
    },
    "tesla": {
        "product": "Tesla Fleet API / TeslaMate",
        "method": "TeslaMate MQTT/Postgres export or Fleet API poll → HEC",
        "endpoint": "vehicle_data / charge_state endpoints",
        "interval": "300s while charging, 900s otherwise",
        "key_fields": "battery_level, charge_rate, charge_energy_added, latitude, longitude",
        "validate_ui": "Tesla app → Energy / Charging screen",
    },
    "homeassistant": {
        "product": "Home Assistant",
        "method": "HA Splunk integration, webhook, or MQTT → HEC",
        "endpoint": "POST /api/events/state_changed or logbook stream",
        "interval": "real-time (event-driven)",
        "key_fields": "entity_id, state, attributes, domain",
        "validate_ui": "Home Assistant → Developer Tools → States",
    },
    "hue": {
        "product": "Philips Hue",
        "method": "Hue API poll or Zigbee2MQTT → HEC",
        "endpoint": "GET /api/<username>/events or MQTT zigbee2mqtt/#",
        "interval": "60s",
        "key_fields": "device_name, state, brightness, color_temp",
        "validate_ui": "Hue app → Rooms → device state",
    },
    "plex": {
        "product": "Plex / Tautulli",
        "method": "Tautulli webhook or API → HEC",
        "endpoint": "Tautulli API get_activity / notify script",
        "interval": "real-time on play/stop",
        "key_fields": "user, title, media_type, duration, percent_complete",
        "validate_ui": "Tautulli → History or Now Playing",
    },
    "proxmox": {
        "product": "Proxmox VE",
        "method": "Universal Forwarder + collectd/telegraf or API poll → HEC",
        "endpoint": "GET /api2/json/nodes/{node}/qemu",
        "interval": "300s",
        "key_fields": "vmid, name, cpu, mem, disk, status",
        "validate_ui": "Proxmox web UI → node summary",
    },
    "docker": {
        "product": "Docker",
        "method": "Docker stats via telegraf or scripted input on host → HEC",
        "endpoint": "docker stats --no-stream JSON",
        "interval": "60s",
        "key_fields": "container_name, cpu_percent, mem_usage, mem_limit",
        "validate_ui": "Portainer or `docker stats` on the host",
    },
    "oura": {
        "product": "Oura Ring",
        "method": "Oura Cloud API v2 → HEC scripted input",
        "endpoint": "GET /v2/usercollection/daily_sleep",
        "interval": "86400s (daily sync)",
        "key_fields": "score, contributors, heart_rate, hrv",
        "validate_ui": "Oura app → Readiness / Sleep tabs",
    },
    "apple": {
        "product": "Apple Health",
        "method": "Health Auto Export app or Shortcuts automation → HEC",
        "endpoint": "iOS shortcut POST JSON batch nightly",
        "interval": "86400s",
        "key_fields": "metric, value, unit, sourceName, startDate",
        "validate_ui": "Apple Health app → Browse → metric category",
    },
    "solaredge": {
        "product": "SolarEdge",
        "method": "SolarEdge Monitoring API → HEC",
        "endpoint": "GET /site/{siteId}/overview",
        "interval": "900s",
        "key_fields": "currentPower, energyToday, energyLifetime",
        "validate_ui": "SolarEdge app → Dashboard kWh today",
    },
    "pihole": {
        "product": "Pi-hole",
        "method": "Pi-hole API / tail FTL log → UF or HEC",
        "endpoint": "GET /admin/api.php?summaryRaw&auth=<token>",
        "interval": "300s",
        "key_fields": "domains_being_blocked, ads_blocked_today, dns_queries_today",
        "validate_ui": "Pi-hole admin → Dashboard main counters",
    },
    "spotify": {
        "product": "Spotify",
        "method": "Spotify Web API recently-played → HEC",
        "endpoint": "GET /v1/me/player/recently-played",
        "interval": "900s",
        "key_fields": "track.name, artist, played_at, duration_ms",
        "validate_ui": "Spotify app → Recently played",
    },
    "personal": {
        "product": "Personal HEC index",
        "method": "HTTP Event Collector token on index=personal",
        "endpoint": "POST https://<splunk>:8088/services/collector/event",
        "interval": "depends on upstream connector",
        "key_fields": "sourcetype-specific — see search filters",
        "validate_ui": "Splunk Search → index=personal | stats count by sourcetype",
    },
}


def load_subcategories() -> dict[str, dict]:
    with open(CATEGORY_JSON) as f:
        data = json.load(f)
    return {s["id"]: s for s in data.get("subcategories", [])}


def lookup_personal_kb(sourcetypes: list[str], indexes: list[str]) -> dict:
    for st in sourcetypes:
        prefix = st.split(":")[0].lower()
        if prefix in PERSONAL_KB:
            return PERSONAL_KB[prefix]
    if "personal" in indexes:
        return PERSONAL_KB["personal"]
    return PERSONAL_KB["personal"]


def fix_spl(spl: str) -> str:
    """Repair common cat-25 SPL syntax defects."""
    if not spl:
        return spl
    spl = re.sub(
        r'sourcetype="([a-z0-9_]+:[a-z0-9_]+)\)"',
        r'sourcetype="\1"',
        spl,
    )
    lines = spl.split("\n")
    if lines:
        first = lines[0].rstrip()
        if first.endswith("))") and " OR " in first:
            first = first[:-1]
        lines[0] = first
    out: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        if i > 0 and not stripped.startswith("|") and SPL_CMDS.match(stripped):
            out.append("| " + stripped)
        else:
            out.append(stripped)
    return "\n".join(out)


def _spl_fields(a: SplAnalysis) -> list[str]:
    fields = list(a.fields)
    for t in a.thresholds:
        if t["field"] not in fields:
            fields.append(t["field"])
    for e in a.eval_constants:
        if e[0] not in fields:
            fields.append(e[0])
    for g in a.group_by_fields:
        if g not in fields and g not in ("_time",):
            fields.append(g)
    return fields[:10]


def _step2_commentary(a: SplAnalysis, pattern: str, title: str, spl: str) -> str:
    tw = fmt_time_window(a.time_window)
    idx = a.indexes[0] if a.indexes else "personal"
    st = a.sourcetypes[0] if a.sourcetypes else "your_sourcetype"
    aggr = ", ".join(a.aggregations[:4]) if a.aggregations else "aggregation"
    group = ", ".join(f"`{g}`" for g in a.group_by_fields[:4]) if a.group_by_fields else "the time bucket"

    intro = (
        f"This search implements **{title}** over `{idx}` data "
        f"(primarily `sourcetype={st}`) across {tw}. "
    )

    threshold_note = (
        f"It applies numeric thresholds on `{a.thresholds[0]['field']}` "
        f"({a.thresholds[0]['op']} {a.thresholds[0]['value']}) after "
        f"{aggr} — tune these constants to your household baseline."
        if a.thresholds
        else f"It evaluates computed metrics with `{aggr}` — tune constants in `eval` "
        f"clauses to match your personal targets."
    )
    join_note = (
        f"The `| join` correlates two feeds on `{a.joins[0]['on'] if a.joins else 'shared key'}`; "
        f"verify subsearch row limits if results look truncated."
        if a.joins
        else "The search correlates multiple event streams — verify both feeds share a common key."
    )
    lookup_note = (
        f"Lookup `{a.lookups[0]['name']}` enriches events — refresh the CSV/KV store on the same "
        f"cadence as your upstream export."
        if a.lookups
        else "Lookup enrichment is referenced — ensure the lookup definition is deployed to the search app."
    )
    pattern_notes = {
        "threshold": threshold_note,
        "stats-window": (
            f"`eventstats` / `streamstats` compute rolling baselines before filtering outliers; "
            f"window size controls sensitivity (smaller window = noisier alerts)."
        ),
        "join": join_note,
        "lookup": lookup_note,
        "lookup-threshold": lookup_note,
        "aggregate": (
            f"The `{aggr}` aggregation groups by {group}; change the `by` clause if you want "
            f"per-device, per-room, or per-user breakdowns instead."
        ),
    }
    body = pattern_notes.get(pattern, pattern_notes["aggregate"])

    fields = _spl_fields(a)
    field_note = ""
    if fields:
        field_note = (
            f"\n\n**Fields this search depends on:** "
            + ", ".join(f"`{f}`" for f in fields)
            + ". Confirm each is populated before scheduling alerts."
        )

    return (
        intro + body + field_note
        + f"\n\n```spl\n{spl.strip()}\n```"
    )


def _build_prerequisites(kb: dict, sub: Optional[dict], a: SplAnalysis) -> str:
    lines = [
        "• **Splunk**: Splunk Enterprise ≥9.0 or Splunk Cloud — a single-instance home lab is fine. "
        "Create `index=personal` with 90–365 day retention (`indexes.conf`).",
        "• **HEC token**: Settings → Data Inputs → HTTP Event Collector → New Token → index `personal`. "
        "Store the token in your connector's environment (never commit it to git).",
        f"• **Upstream product**: {kb['product']} — {kb['method']}.",
    ]
    if sub:
        lines.append(
            f"• **Subcategory context**: {sub['name']} — typical feeds: {sub.get('dataSources', '')[:200]}."
        )
    if a.sourcetypes:
        st_list = ", ".join(f"`{s}`" for s in a.sourcetypes[:4])
        lines.append(f"• **Sourcetypes in this search**: {st_list}.")
    lines.append(
        "• **Network**: The connector host must reach both the vendor API/MQTT broker and your Splunk HEC port (8088/tcp)."
    )
    return "\n".join(lines)


def _build_step1(kb: dict, impl: str, a: SplAnalysis, sub: Optional[dict]) -> str:
    idx = a.indexes[0] if a.indexes else "personal"
    st = a.sourcetypes[0] if a.sourcetypes else "your:export"
    app_hint = sub.get("primaryAppTa", "") if sub else ""

    parts = [
        f"Route **{kb['product']}** events into `index={idx}` with `sourcetype={st}`.",
        f"**Collection method:** {kb['method']}.",
        f"**Reference endpoint / path:** `{kb['endpoint']}`.",
        f"**Suggested poll interval:** {kb['interval']}.",
        f"**Key fields to extract:** `{kb['key_fields']}`.",
    ]
    if app_hint:
        parts.append(f"**Typical connector stack:** {app_hint[:300]}.")
    if impl:
        parts.append(f"**Author notes:** {impl}")
    parts.append(
        f"\nExample HEC payload shape:\n\n"
        f"```json\n"
        f'{{"index": "{idx}", "sourcetype": "{st}", "event": {{ ... vendor fields ... }}}}\n'
        f"```\n\n"
        f"Verify ingestion with:\n\n"
        f"```spl\n"
        f"index={idx} sourcetype={st} earliest=-24h | head 20\n"
        f"```"
    )
    return "\n\n".join(parts)


def _build_validation(kb: dict, a: SplAnalysis) -> str:
    idx = a.indexes[0] if a.indexes else "personal"
    st = a.sourcetypes[0] if a.sourcetypes else "your:export"
    fields = _spl_fields(a)
    field_table = ", ".join(fields[:8]) if fields else "_time, sourcetype, host"

    parts = [
        f"**(a) Compare to vendor UI:** {kb['validate_ui']}. Totals for the same day/week should "
        f"match within connector lag (usually one poll interval).",
        f"**(b) Field presence:**\n\n```spl\n"
        f"index={idx} sourcetype={st} earliest=-7d\n"
        f"| head 50\n"
        f"| table {field_table}\n"
        f"```\n\n"
        f"Every column the detection uses should be non-null on recent rows.",
        f"**(c) Volume sanity:**\n\n```spl\n"
        f"index={idx} sourcetype={st} earliest=-30d\n"
        f"| timechart span=1d count\n"
        f"```\n\n"
        f"Flatlines usually mean a broken token, expired OAuth refresh, or HEC URL change.",
    ]
    if a.thresholds:
        t = a.thresholds[0]
        parts.append(
            f"**(d) Threshold calibration:** Profile `{t['field']}` before alerting:\n\n"
            f"```spl\n"
            f"index={idx} sourcetype={st} earliest=-30d\n"
            f"| stats perc50({t['field']}) AS p50 perc90({t['field']}) AS p90 "
            f"perc99({t['field']}) AS p99 max({t['field']}) AS hi\n"
            f"```"
        )
    return "\n\n".join(parts)


def _build_troubleshooting(kb: dict, a: SplAnalysis, pattern: str) -> str:
    idx = a.indexes[0] if a.indexes else "personal"
    st = a.sourcetypes[0] if a.sourcetypes else "your:export"
    product = kb["product"]
    lines = [
        f"**{product} — no {product} events / missing fields:** If `{st}` stops updating, re-check HEC token, "
        f"index `{idx}`, and firewall to port 8088. Search "
        f"`index=_internal sourcetype=splunkd group=http_event_collector` for rejection reasons. "
        f"Confirm the {product} connector script is still running (`systemctl status` or cron log).",
        f"**{product} — NULL values in extracted fields:** The {product} JSON export shape drifted — "
        f"compare a raw event (`index={idx} sourcetype={st} | head 1 | spath`) against the field names "
        f"in Step 2. Re-map in the connector before changing the SPL.",
        f"**{product} — API error / auth denied (401/403):** Refresh tokens expire on most consumer APIs — "
        f"re-authorize the scripted input, update `passwords.conf` / env vars, and verify the "
        f"vendor developer app is not in sandbox mode.",
        f"**{product} — endpoint timeout / HTTP 429 throttling:** Back off the poll interval in the connector; "
        f"{product} APIs often cap requests per 15 minutes on free tiers.",
    ]
    if pattern == "join":
        lines.append(
            "**Join returns nothing:** Inner subsearch may have hit the 50k row cap — narrow time range "
            "or pre-aggregate with `| stats` before joining."
        )
    if pattern == "stats-window":
        lines.append(
            "**Everything is an outlier:** Baseline window is too short or `stdev=0` — require minimum "
            "sample count (`where count>=5`) before computing z-scores."
        )
    if a.span:
        lines.append(
            f"**Bucket misalignment:** `span={a.span}` buckets on UTC by default — if your routine is "
            f"local-time based, add `| eval _time=_time + (local_offset)` or use `@d` / `@w` snap."
        )
    lines.append(
        f"**Stale dashboard:** Confirm the saved search `dispatch.earliest_time` covers enough history "
        f"for your `{a.span or 'aggregation'}` buckets."
    )
    return "\n\n".join(lines)


def assemble_di(uc: dict, sub: Optional[dict]) -> str:
    spl = uc.get("spl", "")
    title = uc.get("title", "")
    impl = uc.get("implementation", "")
    viz = uc.get("visualization", "")
    uc_id = uc.get("id", "")

    a = parse_spl(spl)
    pattern = classify_spl_pattern(a)
    kb = lookup_personal_kb(a.sourcetypes, a.indexes)

    prereqs = _build_prerequisites(kb, sub, a)
    step1 = _build_step1(kb, impl, a, sub)
    step2 = _step2_commentary(a, pattern, title, spl)
    step3 = _build_validation(kb, a)
    step4 = integrate_visualization(viz, uc_id, "Personal")
    step5 = _build_troubleshooting(kb, a, pattern)

    return (
        "## Prerequisites\n\n"
        f"{prereqs}\n\n"
        "## Step 1 — Configure data collection\n\n"
        f"{step1}\n\n"
        "## Step 2 — Create the search and alert\n\n"
        f"{step2}\n\n"
        "## Step 3 — Validate\n\n"
        f"{step3}\n\n"
        "## Step 4 — Operationalize\n\n"
        f"{step4}\n\n"
        "## Step 5 — Troubleshooting\n\n"
        f"{step5}"
    )


def infer_equipment(uc: dict, patterns) -> list[str]:
    if uc.get("equipment"):
        return uc["equipment"]
    blob = " ".join(
        str(uc.get(k, "")) for k in ("title", "description", "app", "dataSources", "spl")
    )
    eq, _models = match_equipment(blob, patterns)
    return sorted(eq)[:5]


def infer_wave(difficulty: str) -> str:
    d = (difficulty or "").lower()
    if d in ("advanced", "expert"):
        return "run"
    if d in ("intermediate",):
        return "walk"
    return "crawl"


def expand_description(uc: dict) -> str:
    """Ensure description meets Silver minLength (60) without duplicating value."""
    desc = uc.get("description", "")
    if len(desc) >= 60:
        return desc
    title = uc.get("title", "this use case")
    value = uc.get("value", "")
    extra = (
        f"Runs scheduled SPL against `index=personal` to surface **{title}** "
        f"so you can spot drift before it becomes a habit."
    )
    combined = f"{desc.rstrip('.')}. {extra}" if desc else extra
    if value and combined != value:
        return combined[:280]
    return combined[:280]


def enrich_uc(uc: dict, sub: Optional[dict], patterns) -> dict:
    uc = dict(uc)
    fixed_spl = fix_spl(uc.get("spl", ""))
    if fixed_spl != uc.get("spl"):
        uc["spl"] = fixed_spl
    uc["description"] = expand_description(uc)
    uc["detailedImplementation"] = assemble_di(uc, sub)
    if "wave" not in uc:
        uc["wave"] = infer_wave(uc.get("difficulty", "beginner"))
    if "prerequisiteUseCases" not in uc:
        uc["prerequisiteUseCases"] = []
    if "equipment" not in uc:
        uc["equipment"] = infer_equipment(uc, patterns)
    return uc


def sub_for_uc(uc_id: str, subs: dict[str, dict]) -> Optional[dict]:
    parts = uc_id.split(".")
    if len(parts) >= 2:
        key = f"{parts[0]}.{parts[1]}"
        return subs.get(key)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Enrich cat-25 UCs to Silver tier.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", type=str, help="Process files matching substring")
    args = ap.parse_args()

    subs = load_subcategories()
    patterns = compile_patterns(load_equipment())
    files = sorted(glob.glob(str(BASE / "UC-25.*.json")))
    if args.only:
        files = [f for f in files if args.only in f]
    if args.limit:
        files = files[: args.limit]

    changed = 0
    spl_fixed = 0
    for fp in files:
        with open(fp) as f:
            data = json.load(f)
        orig_spl = data.get("spl", "")
        new_data = enrich_uc(data, sub_for_uc(data["id"], subs), patterns)
        if new_data.get("spl") != orig_spl:
            spl_fixed += 1
        if new_data == data:
            continue
        changed += 1
        if not args.dry_run:
            with open(fp, "w") as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

    print(f"Processed {len(files)} files, changed={changed}, spl_fixed={spl_fixed}")


if __name__ == "__main__":
    main()
