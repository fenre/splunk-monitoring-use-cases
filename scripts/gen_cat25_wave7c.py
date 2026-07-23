#!/usr/bin/env python3
"""Append wave-7c cat-25 use cases for subcategories 25.41-25.60."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from gen_cat25_common import CAT25, Cat25Writer, R

SCRIPT_PATH = Path(__file__).resolve()
TARGET_SUBS = tuple(str(i) for i in range(41, 61))
EXPECTED_START = 18
EXPECTED_PER_SUB = 15
EXPECTED_END = EXPECTED_START + EXPECTED_PER_SUB

ANALYTICS = ["Analytics"]
AVAIL = ["Availability"]
AVAIL_ANALYTICS = ["Availability", "Analytics"]
ANOM = ["Anomaly", "Analytics"]
BUSINESS = ["Business", "Analytics"]


def S(
    title: str,
    crit: str,
    diff: str,
    mtypes: list[str],
    spl: str,
    desc: str,
    val: str,
    impl: str,
    viz: str,
    grandma_body: str,
) -> dict[str, object]:
    return {
        "title": title,
        "crit": crit,
        "diff": diff,
        "mtypes": mtypes,
        "spl": spl,
        "desc": desc,
        "val": val,
        "impl": impl,
        "viz": viz,
        "grandma_body": grandma_body,
    }


def _search(source: str, filters: str = "") -> str:
    filters = filters.strip()
    if filters:
        return f"index=personal sourcetype={source} {filters}"
    return f"index=personal sourcetype={source}"


def _alias(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "value"


def avg_by(
    title: str,
    source: str,
    filters: str,
    metric_field: str,
    metric_label: str,
    by_field: str,
    by_label: str,
    subject: str,
    crit: str = "low",
    diff: str = "intermediate",
    mtypes: list[str] | None = None,
    sort_desc: bool = True,
) -> dict[str, object]:
    alias = f"avg_{_alias(metric_field)}"
    sort_prefix = "-" if sort_desc else ""
    return S(
        title,
        crit,
        diff,
        mtypes or ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| stats avg({metric_field}) as {alias}, count as events by {by_field}\n"
            f"| sort {sort_prefix} {alias}"
        ),
        f"Shows average {metric_label} by {by_label} for {subject}.",
        f"Average {metric_label} by {by_label} helps compare {subject} across the factors that matter most.",
        f"Capture `{metric_field}` on `{source}` events and normalize `{by_field}` so Splunk can summarize performance by {by_label}.",
        f"Bar chart of average {metric_label} by {by_label}.",
        f"the average {metric_label} for each {by_label} so you can see what works best for {subject}.",
    )


def rate_by(
    title: str,
    source: str,
    filters: str,
    success_cond: str,
    success_label: str,
    by_field: str,
    by_label: str,
    event_label: str,
    crit: str = "low",
    diff: str = "intermediate",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    alias = f"{_alias(success_label)}_pct"
    return S(
        title,
        crit,
        diff,
        mtypes or ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| stats count as total, sum(eval(if({success_cond},1,0))) as matched by {by_field}\n"
            f"| eval {alias}=round(100*matched/total,1)\n"
            f"| sort - {alias}"
        ),
        f"Measures the percentage of {event_label} that end with {success_label} by {by_label}.",
        f"Completion and exception percentages make it easier to spot which {by_label} are helping or hurting {event_label}.",
        f"Store a normalized flag for `{success_label}` on `{source}` events and summarize the hit rate by `{by_field}`.",
        f"Table of {by_label} with percentage of {event_label} ending with {success_label}.",
        f"how often {success_label} happens for each {by_label} so you can see where {event_label} go smoothly or get stuck.",
    )


def count_by(
    title: str,
    source: str,
    filters: str,
    by_field: str,
    by_label: str,
    event_label: str,
    subject: str,
    crit: str = "low",
    diff: str = "beginner",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    return S(
        title,
        crit,
        diff,
        mtypes or ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| stats count as { _alias(event_label) } by {by_field}\n"
            f"| sort - { _alias(event_label) }"
        ),
        f"Ranks {by_label} by {event_label} volume for {subject}.",
        f"Volume rankings show which {by_label} are producing the most activity, demand, or friction inside {subject}.",
        f"Capture each {event_label} as a `{source}` event and normalize `{by_field}` so the totals are comparable.",
        f"Bar chart of {event_label} volume by {by_label}.",
        f"which {by_label} show up the most in {subject} so you know where the busiest areas are.",
    )


def lag_by(
    title: str,
    source: str,
    filters: str,
    lag_expr: str,
    lag_label: str,
    by_field: str,
    by_label: str,
    subject: str,
    unit: str = "hours",
    divisor: int = 3600,
    crit: str = "low",
    diff: str = "intermediate",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    alias = f"lag_{unit}"
    return S(
        title,
        crit,
        diff,
        mtypes or AVAIL_ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| eval {alias}=round(({lag_expr})/{divisor},1)\n"
            f"| stats avg({alias}) as avg_{alias}, max({alias}) as worst_{alias} by {by_field}\n"
            f"| sort - avg_{alias}"
        ),
        f"Measures {lag_label} by {by_label} for {subject}.",
        f"Lag tracking shows which {by_label} create the slowest handoffs, syncs, or review loops inside {subject}.",
        f"Capture the timestamps needed to compute `{lag_label}` on `{source}` events and aggregate them by `{by_field}`.",
        f"Table of {by_label} with average and worst {lag_label}.",
        f"how long things take for each {by_label} so you can see where {subject} slows down.",
    )


def backlog_by(
    title: str,
    source: str,
    filters: str,
    pending_cond: str,
    by_field: str,
    by_label: str,
    item_label: str,
    subject: str,
    crit: str = "low",
    diff: str = "beginner",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    return S(
        title,
        crit,
        diff,
        mtypes or AVAIL,
        (
            f"{_search(source, filters)}\n"
            f"| stats sum(eval(if({pending_cond},1,0))) as backlog, count as total by {by_field}\n"
            f"| where backlog>0\n"
            f"| sort - backlog"
        ),
        f"Lists pending {item_label} backlog by {by_label} for {subject}.",
        f"Backlog counts expose where small unfinished tasks accumulate and create hidden drag inside {subject}.",
        f"Mark each `{source}` record with a pending-state flag and summarize backlog totals by `{by_field}`.",
        f"Table of {by_label} with pending {item_label} counts.",
        f"where unfinished {item_label} are piling up so you can clear the biggest queues in {subject}.",
    )


def trend_by_month(
    title: str,
    source: str,
    filters: str,
    agg_expr: str,
    metric_label: str,
    by_field: str,
    by_label: str,
    subject: str,
    crit: str = "low",
    diff: str = "intermediate",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    return S(
        title,
        crit,
        diff,
        mtypes or ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| bin _time span=1mon\n"
            f"| stats {agg_expr} as metric by _time {by_field}\n"
            f"| sort 0 _time {by_field}"
        ),
        f"Trends monthly {metric_label} by {by_label} for {subject}.",
        f"Monthly trend lines show whether {subject} are improving, stalling, or becoming unbalanced over time.",
        f"Normalize `{by_field}` on `{source}` events and store the fields needed to calculate monthly {metric_label}.",
        f"Line chart of monthly {metric_label} by {by_label}.",
        f"how {metric_label} changes month by month for each {by_label} so you can see whether {subject} are heading the right way.",
    )


def share_by(
    title: str,
    source: str,
    filters: str,
    by_field: str,
    by_label: str,
    item_label: str,
    subject: str,
    crit: str = "low",
    diff: str = "beginner",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    return S(
        title,
        crit,
        diff,
        mtypes or ANALYTICS,
        (
            f"{_search(source, filters)}\n"
            f"| stats count as items by {by_field}\n"
            f"| eventstats sum(items) as total\n"
            f"| eval share_pct=round(100*items/total,1)\n"
            f"| sort - share_pct"
        ),
        f"Shows how {item_label} split across {by_label} for {subject}.",
        f"Share-of-total views make it easier to see imbalance, over-concentration, and neglected areas inside {subject}.",
        f"Capture each {item_label} event in `{source}` and normalize `{by_field}` so Splunk can compute the share by {by_label}.",
        f"Table of {by_label} with item count and share percentage.",
        f"how {item_label} are divided across {by_label} so you can tell if one part of {subject} is taking over.",
    )


def expiry_watch(
    title: str,
    source: str,
    filters: str,
    expiry_field: str,
    open_cond: str,
    item_fields: list[str],
    item_label: str,
    subject: str,
    unit: str = "hours",
    divisor: int = 3600,
    crit: str = "low",
    diff: str = "beginner",
    mtypes: list[str] | None = None,
) -> dict[str, object]:
    alias = f"{unit}_left"
    table_fields = " ".join(item_fields + [alias])
    return S(
        title,
        crit,
        diff,
        mtypes or AVAIL,
        (
            f"{_search(source, filters)}\n"
            f"| eval {alias}=round(({expiry_field}-now())/{divisor},1)\n"
            f"| where {open_cond}\n"
            f"| table {table_fields}\n"
            f"| sort {alias}"
        ),
        f"Lists open {item_label} with time remaining for {subject}.",
        f"Time-left monitoring helps prevent quiet deadline misses across the operational details that support {subject}.",
        f"Store an expiry timestamp on `{source}` events and filter for open or unfinished {item_label}.",
        f"Table of open {item_label} sorted by time remaining.",
        f"which {item_label} are about to run out of time so you can deal with them before {subject} slips.",
    )


META = {
    "41": {
        "app": "Micro-mobility and action-sports telemetry — Onewheel ride exports, legacy Boosted board logs, Surfline forecast snapshots, and Strava segment efforts — streamed to Splunk HEC via vendor exports and scripted inputs.",
        "ds": "Rides (`ride:session`), charge sessions (`ride:charge`), ride exports (`ride:export`), surf forecasts (`surf:forecast`), ride incidents (`ride:incident`), segment efforts (`fitness:segment`).",
        "refs": R(
            ("Onewheel — boards", "https://onewheel.com/"),
            ("Boosted — electric skateboards", "https://boostedusa.com/"),
            ("Surfline — surf reports", "https://www.surfline.com/"),
            ("Strava — segments", "https://www.strava.com/"),
        ),
    },
    "42": {
        "app": "Aviation and flight-sim telemetry — ForeFlight exports, SimBrief flight plans, VATSIM session logs, and checkride-prep trackers — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Flight logs (`flight:log`), flight-plan snapshots (`simbrief:plan`), network sessions (`vatsim:session`), prep tasks (`checkride:prep`), export syncs (`flight:export`).",
        "refs": R(
            ("ForeFlight — flight bag", "https://foreflight.com/"),
            ("SimBrief — flight planning", "https://www.simbrief.com/home/"),
            ("VATSIM — virtual ATC", "https://vatsim.net/"),
            ("FAA — Airman Certification Standards", "https://www.faa.gov/training_testing/testing/acs"),
        ),
    },
    "43": {
        "app": "Boating and marine telemetry — Victron BMV battery exports, AIS transponder logs, shore-power meter readings, and NOAA tide tables — streamed to Splunk HEC via NMEA exports and scripted inputs.",
        "ds": "Battery telemetry (`marine:battery`), AIS traffic (`marine:ais`), shore power (`marina:power`), tide forecasts (`tide:table`), export syncs (`marine:export`).",
        "refs": R(
            ("Victron Energy — BMV battery monitors", "https://www.victronenergy.com/battery-monitors"),
            ("Garmin AIS 800 — transponder", "https://www.garmin.com/en-US/p/624973"),
            ("SmartPlug — shore power", "https://www.smartplug.com/"),
            ("NOAA Tides and Currents", "https://tidesandcurrents.noaa.gov/"),
        ),
    },
    "44": {
        "app": "Fishing, hunting, foraging, and outdoor-cooking telemetry — Fishbrain catch logs, onX Hunt map exports, iNaturalist observations, and ThermoWorks smoker probes — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Catch trips (`outdoor:trip`), hunt map activity (`hunt:map`), foraging observations (`forage:observation`), smoker sessions (`cook:smoker`), harvest queues (`outdoor:queue`).",
        "refs": R(
            ("Fishbrain — fishing app", "https://fishbrain.com/"),
            ("onX Hunt — maps", "https://www.onxmaps.com/hunt/app"),
            ("iNaturalist — observations", "https://www.inaturalist.org/"),
            ("ThermoWorks Signals — smoker telemetry", "https://www.thermoworks.com/signals/"),
        ),
    },
    "45": {
        "app": "Music-making and creator telemetry — DistroKid release exports, Bandcamp sales activity, Cockos Reaper project stats, and Spotify for Artists analytics — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Release events (`music:distribution`), Bandcamp activity (`music:bandcamp`), project exports (`music:project`), streaming analytics (`music:streaming`), metadata tasks (`music:ops`).",
        "refs": R(
            ("DistroKid — music distribution", "https://distrokid.com/"),
            ("Bandcamp — artist sales", "https://bandcamp.com/"),
            ("REAPER — digital audio workstation", "https://www.reaper.fm/"),
            ("Spotify for Artists", "https://artists.spotify.com/"),
        ),
    },
    "46": {
        "app": "Tabletop campaign telemetry — D&D Beyond character exports, Roll20 session logs, initiative trackers, and campaign asset checklists — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Character sheets (`rpg:character`), VTT sessions (`rpg:session`), initiative rounds (`rpg:initiative`), encounters (`rpg:combat`), campaign ops (`rpg:ops`).",
        "refs": R(
            ("D&D Beyond — digital tools", "https://www.dndbeyond.com/"),
            ("Roll20 — virtual tabletop", "https://roll20.net/"),
            ("Improved Initiative — encounter tracker", "https://www.improved-initiative.com/"),
        ),
    },
    "47": {
        "app": "Reading and second-brain telemetry — Readwise review exports, Kindle highlights, Goodreads shelves, and Zotero research libraries — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Highlights (`reading:highlight`), book activity (`reading:book`), reviews (`reading:review`), paper libraries (`research:paper`), sync states (`reading:sync`).",
        "refs": R(
            ("Readwise — review workflow", "https://readwise.io/"),
            ("Amazon Kindle", "https://www.amazon.com/kindle-dbs/fd/kcp"),
            ("Goodreads", "https://www.goodreads.com/"),
            ("Zotero", "https://www.zotero.org/"),
        ),
    },
    "48": {
        "app": "Language-learning telemetry — Anki review logs, Duolingo lessons, Babbel course exports, immersion-hour trackers, and tutor-session notes — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Reviews (`language:review`), lessons (`language:lesson`), immersion sessions (`language:immersion`), tutor sessions (`language:tutor`), sync states (`language:sync`).",
        "refs": R(
            ("Anki", "https://apps.ankiweb.net/"),
            ("Duolingo", "https://www.duolingo.com/"),
            ("Babbel", "https://www.babbel.com/"),
            ("italki", "https://www.italki.com/"),
        ),
    },
    "49": {
        "app": "Wardrobe and beauty telemetry — Stylebook closet exports, dry-cleaning reminders, shoe-rotation logs, and makeup inventory audits — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Closet activity (`style:wardrobe`), cleaning tasks (`style:cleaning`), shoe wears (`style:shoes`), beauty inventory (`beauty:product`), audits (`style:audit`).",
        "refs": R(
            ("Stylebook", "https://stylebookapp.com/"),
            ("Google Calendar", "https://calendar.google.com/"),
            ("Notion", "https://www.notion.so/"),
        ),
    },
    "50": {
        "app": "Sustainability telemetry — Olio sharing activity, Repair Cafe repair logs, compost-weight records, and solar-offset telemetry — streamed to Splunk HEC via APIs, exports, and smart-home integrations.",
        "ds": "Sharing activity (`sustain:share`), repairs (`sustain:repair`), compost logs (`sustain:compost`), solar telemetry (`sustain:solar`), sustainability audits (`sustain:audit`).",
        "refs": R(
            ("Olio", "https://olioapp.com/"),
            ("Repair Cafe", "https://www.repaircafe.org/en/"),
            ("Home Assistant", "https://www.home-assistant.io/"),
            ("Enphase", "https://enphase.com/"),
        ),
    },
    "51": {
        "app": "Chronic-condition self-management telemetry — insulin-pump events, A1c lab imports, physical-therapy rep logs, and symptom diaries — streamed to Splunk HEC via device exports and scripted inputs.",
        "ds": "Pump telemetry (`health:glucose`), lab results (`health:lab`), therapy sessions (`health:pt`), symptom diaries (`health:symptom`), care tasks (`health:ops`).",
        "refs": R(
            ("Omnipod", "https://www.omnipod.com/"),
            ("Dexcom Clarity", "https://clarity.dexcom.com/"),
            ("Labcorp OnDemand", "https://www.ondemand.labcorp.com/"),
            ("Bearable", "https://bearable.app/"),
        ),
    },
    "52": {
        "app": "Elder-care and accessibility telemetry — PERS pendant alerts, medication blister-pack reminders, and wandering geofence signals — streamed to Splunk HEC via caregiver apps, exports, and scripted inputs.",
        "ds": "Pendant alerts (`care:pendant`), medication adherence (`care:medication`), wandering alerts (`care:geofence`), check-ins (`care:checkin`), care-plan follow-up (`care:ops`).",
        "refs": R(
            ("Medical Guardian", "https://www.medicalguardian.com/"),
            ("Hero — medication dispenser", "https://herohealth.com/"),
            ("Apple Find My", "https://www.apple.com/icloud/find-my/"),
            ("Home Assistant Person", "https://www.home-assistant.io/integrations/person/"),
        ),
    },
    "53": {
        "app": "Wedding and event-planning telemetry — The Knot checklist exports, seating-chart revisions, vendor deposit schedules, and RSVP operations — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Planning tasks (`event:checklist`), seating revisions (`event:seating`), vendor contracts (`event:vendor`), deposits (`event:deposit`), planning syncs (`event:sync`).",
        "refs": R(
            ("The Knot", "https://www.theknot.com/"),
            ("AllSeated", "https://www.allseated.com/"),
            ("Zola", "https://www.zola.com/"),
            ("HoneyBook", "https://www.honeybook.com/"),
        ),
    },
    "54": {
        "app": "Home-renovation project telemetry — Gantt plans, punch-list updates, inspection photo logs, and permit expiry trackers — streamed to Splunk HEC via builder-tool exports and scripted inputs.",
        "ds": "Schedules (`reno:gantt`), punch lists (`reno:punchlist`), photo logs (`reno:photo`), permits (`reno:permit`), project controls (`reno:ops`).",
        "refs": R(
            ("Buildertrend", "https://buildertrend.com/"),
            ("Trello", "https://trello.com/"),
            ("Notion", "https://www.notion.so/"),
        ),
    },
    "55": {
        "app": "Genealogy and family-history telemetry — Ancestry hints, cemetery visit logs, and photo-restoration queues — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Hints (`genealogy:hint`), cemetery visits (`genealogy:cemetery`), family-photo work (`genealogy:photo`), research ops (`genealogy:ops`).",
        "refs": R(
            ("Ancestry", "https://www.ancestry.com/"),
            ("Find a Grave", "https://www.findagrave.com/"),
            ("MyHeritage Photo Enhancer", "https://www.myheritage.com/photo-enhancer"),
        ),
    },
    "56": {
        "app": "Spiritual-practice telemetry — rosary counters, meditation-retreat schedules, church-attendance logs, and fasting journals — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Prayer sessions (`faith:rosary`), retreat events (`faith:retreat`), attendance logs (`faith:attendance`), fasting journals (`faith:fast`), practice reviews (`faith:ops`).",
        "refs": R(
            ("Hallow", "https://hallow.com/"),
            ("Church Center", "https://www.churchcenter.com/"),
            ("YouVersion", "https://www.youversion.com/the-bible-app/"),
        ),
    },
    "57": {
        "app": "Community-service telemetry — food-bank shift logs, blood-donation records, and mutual-aid request maps — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Volunteer shifts (`community:shift`), donations (`community:donation`), mutual-aid requests (`community:mutualaid`), service ops (`community:impact`).",
        "refs": R(
            ("VolunteerMatch", "https://www.volunteermatch.org/"),
            ("American Red Cross — blood donation", "https://www.redcrossblood.org/"),
            ("Mutual Aid Hub", "https://www.mutualaidhub.org/"),
        ),
    },
    "58": {
        "app": "Life-logging and memory telemetry — Google Photos Takeout archives, journal OCR queues, and postcard collection logs — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Photo archives (`memory:takeout`), journal OCR (`memory:journal`), postcard records (`memory:postcard`), memory linking (`memory:photo`), archive checks (`memory:ops`).",
        "refs": R(
            ("Google Photos", "https://photos.google.com/"),
            ("Google Takeout", "https://takeout.google.com/"),
            ("Day One", "https://dayoneapp.com/"),
            ("Tesseract OCR", "https://tesseract-ocr.github.io/"),
        ),
    },
    "59": {
        "app": "Personal life-OS telemetry — Habitica quest logs, Streaks app habit chains, Beeminder goal data, and personal OKR reviews — streamed to Splunk HEC via APIs, exports, and scripted inputs.",
        "ds": "Habit activity (`lifeos:habit`), streaks (`lifeos:streak`), Beeminder goals (`lifeos:beeminder`), OKRs (`lifeos:okr`), planning syncs (`lifeos:ops`).",
        "refs": R(
            ("Habitica", "https://habitica.com/"),
            ("Streaks", "https://streaksapp.com/"),
            ("Beeminder", "https://www.beeminder.com/"),
            ("Notion", "https://www.notion.so/"),
        ),
    },
    "60": {
        "app": "Personal forecasting telemetry — Metaculus personal predictions, private prediction-journal entries, and calibration-bin scoring — streamed to Splunk HEC via exports and scripted inputs.",
        "ds": "Forecasts (`forecast:personal`), journal reviews (`forecast:journal`), resolved outcomes (`forecast:resolution`), calibration scores (`forecast:calibration`), ops reviews (`forecast:ops`).",
        "refs": R(
            ("Metaculus", "https://www.metaculus.com/"),
            ("Good Judgment", "https://goodjudgment.com/"),
            ("PredictionBook", "https://predictionbook.com/"),
        ),
    },
}


SPECS = {
    "41": [
        avg_by("Onewheel Range by Tire-Pressure Band", "ride:session", 'platform="onewheel" tire_psi_band=* range_miles=*', "range_miles", "range miles", "tire_psi_band", "tire-pressure band", "Onewheel rides"),
        avg_by("Onewheel Battery Sag After Firmware Updates", "ride:session", 'platform="onewheel" firmware_version=* battery_sag_pct=*', "battery_sag_pct", "battery sag percentage", "firmware_version", "firmware version", "Onewheel rides", diff="advanced", mtypes=ANOM),
        avg_by("Boosted Board Commute Delay by Battery Band", "ride:session", 'platform="boosted" battery_pct_band=* delay_min=*', "delay_min", "commute delay minutes", "battery_pct_band", "battery band", "Boosted board commutes", mtypes=AVAIL_ANALYTICS),
        rate_by("Boosted Charger Session Completion Rate", "ride:charge", 'platform="boosted" charger_type=* charge_completed=*', 'charge_completed="yes"', "a full charge", "charger_type", "charger type", "Boosted charge sessions", mtypes=AVAIL_ANALYTICS),
        avg_by("Surfline Forecast Confidence vs Go Sessions", "surf:forecast", 'spot=* forecast_confidence_pct=* session_started=*', "forecast_confidence_pct", "forecast confidence percentage", "spot", "surf spot", "Surfline forecast decisions"),
        avg_by("Surfline Rideable Hours by Swell Direction", "surf:forecast", 'swell_direction=* rideable_hours=*', "rideable_hours", "rideable hours", "swell_direction", "swell direction", "surf-forecast windows"),
        rate_by("Strava Segment PR Attempt Density", "fitness:segment", 'segment_name=* is_pr=*', 'is_pr="yes"', "a personal record", "segment_name", "Strava segment", "segment attempts"),
        avg_by("Strava Segment Recovery Gap After PRs", "fitness:segment", 'segment_name=* is_pr="yes" recovery_hours=*', "recovery_hours", "recovery hours", "segment_name", "Strava segment", "post-PR recovery"),
        rate_by("Helmet Reminder Compliance by Ride Mode", "ride:session", 'ride_mode=* helmet_worn=*', 'helmet_worn="yes"', "a helmet worn", "ride_mode", "ride mode", "micro-mobility rides", mtypes=AVAIL_ANALYTICS),
        lag_by("Ride Export Freshness Across Onewheel and Boosted", "ride:export", 'platform=* export_epoch=* event_epoch=*', "export_epoch-event_epoch", "ride export lag", "platform", "platform", "ride-data syncs"),
        avg_by("Carve Session Duration by Surface Type", "ride:session", 'surface_type=* session_duration_min=*', "session_duration_min", "session duration minutes", "surface_type", "surface type", "carve sessions"),
        avg_by("Onewheel vs Boosted Range per Temperature Band", "ride:session", '(platform="onewheel" OR platform="boosted") temperature_band=* range_miles=*', "range_miles", "range miles", "temperature_band", "temperature band", "micro-mobility range planning"),
        rate_by("Surf Session Abort Rate After Red-Flag Forecasts", "surf:forecast", 'spot=* red_flag=* session_aborted=*', 'session_aborted="yes"', "an aborted session", "spot", "surf spot", "forecasted surf sessions", mtypes=ANOM),
        avg_by("Strava Segment Time Improvement by Weekday", "fitness:segment", 'weekday=* seconds_saved=*', "seconds_saved", "seconds saved", "weekday", "weekday", "segment-improvement attempts"),
        backlog_by("Micro-Mobility Incident Notes Backlog", "ride:incident", 'platform=* incident_state=*', 'incident_state!="closed"', "platform", "platform", "incident follow-ups", "micro-mobility safety reviews", mtypes=AVAIL_ANALYTICS),
    ],
    "42": [
        lag_by("ForeFlight Export Freshness by Tail Number", "flight:log", 'tail_number=* export_epoch=* flight_end_epoch=*', "export_epoch-flight_end_epoch", "ForeFlight export lag", "tail_number", "tail number", "electronic-flight-bag syncs"),
        rate_by("ForeFlight Checklist Completion Gap", "flight:log", 'checklist_name=* all_items_completed=*', 'all_items_completed="yes"', "every checklist item complete", "checklist_name", "checklist", "ForeFlight checklist runs", mtypes=AVAIL_ANALYTICS),
        avg_by("SimBrief Planned vs Actual Block Time", "simbrief:plan", 'route_type=* block_delta_min=*', "block_delta_min", "block-time delta minutes", "route_type", "route type", "SimBrief plan accuracy"),
        avg_by("SimBrief Fuel Reserve Margin by Route Type", "simbrief:plan", 'route_type=* reserve_margin_min=*', "reserve_margin_min", "fuel reserve margin minutes", "route_type", "route type", "flight-plan reserve tracking", crit="medium"),
        trend_by_month("VATSIM Hours Burn-Up vs Rating Goal", "vatsim:session", 'rating_goal=* session_hours=*', "sum(session_hours)", "session hours", "rating_goal", "rating goal", "VATSIM progression"),
        avg_by("VATSIM Session Time by FIR", "vatsim:session", 'fir=* session_hours=*', "session_hours", "session hours", "fir", "FIR", "virtual ATC sessions"),
        backlog_by("Checkride Prep Task Backlog", "checkride:prep", 'topic=* task_state=*', 'task_state!="done"', "topic", "checkride topic", "prep tasks", "checkride preparation", crit="medium", mtypes=AVAIL_ANALYTICS),
        rate_by("Checkride Weak-Area Repeat Rate", "checkride:prep", 'topic=* repeated_miss=*', 'repeated_miss="yes"', "a repeated miss", "topic", "checkride topic", "mock-checkride drills", crit="medium"),
        lag_by("ForeFlight Route Briefing Lag", "flight:log", 'aircraft_type=* route_built_epoch=* briefing_complete_epoch=*', "briefing_complete_epoch-route_built_epoch", "route-briefing lag", "aircraft_type", "aircraft type", "route briefings"),
        rate_by("SimBrief Alternate Airport Usage Rate", "simbrief:plan", 'route_type=* alternate_used=*', 'alternate_used="yes"', "an alternate airport", "route_type", "route type", "SimBrief flight plans"),
        rate_by("VATSIM Peak ATC Coverage Match Rate", "vatsim:session", 'airport_class=* planned_coverage_met=*', 'planned_coverage_met="yes"', "planned ATC coverage", "airport_class", "airport class", "peak VATSIM sessions"),
        trend_by_month("Checkride Mock-Oral Score Trend", "checkride:prep", 'subject=* mock_oral_score=*', "avg(mock_oral_score)", "mock-oral score", "subject", "checkride subject", "checkride study blocks", crit="medium"),
        avg_by("ForeFlight Crosswind Practice Mix", "flight:log", 'airport=* crosswind_practice_min=*', "crosswind_practice_min", "crosswind practice minutes", "airport", "airport", "crosswind training sessions"),
        rate_by("Flight Plan Filing Rework Rate", "flight:log", 'route_type=* refiled=*', 'refiled="yes"', "a refile", "route_type", "route type", "flight-plan filings", mtypes=ANOM),
        lag_by("Aviation Data Source Staleness Watch", "flight:export", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "source-sync lag", "source_name", "data source", "aviation telemetry feeds", mtypes=AVAIL),
    ],
    "43": [
        avg_by("Victron BMV Overnight Battery Draw", "marine:battery", 'battery_bank=* overnight_draw_ah=*', "overnight_draw_ah", "overnight amp-hour draw", "battery_bank", "battery bank", "overnight marine power use", crit="medium"),
        avg_by("Victron BMV Charge Recovery After Shore Power", "marine:battery", 'shore_power_cycle=* recovered_ah=*', "recovered_ah", "recovered amp-hours", "shore_power_cycle", "shore-power cycle", "battery recharge sessions", crit="medium"),
        avg_by("AIS Transponder Closest-Approach Alerts", "marine:ais", 'zone=* closest_approach_nm=*', "closest_approach_nm", "closest-approach nautical miles", "zone", "navigation zone", "AIS traffic safety", crit="medium", sort_desc=False, mtypes=ANOM),
        count_by("AIS Traffic Density by Marina Entrance", "marine:ais", 'entrance_name=*', "entrance_name", "marina entrance", "AIS contacts", "marina approaches"),
        lag_by("Marina Electricity Outage Duration", "marina:power", 'pedestal_id=* outage_start_epoch=* outage_end_epoch=*', "outage_end_epoch-outage_start_epoch", "shore-power outage duration", "pedestal_id", "power pedestal", "marina electricity reliability", crit="medium", mtypes=AVAIL),
        avg_by("Shore-Power Pedestal Load by Slip", "marina:power", 'slip_id=* load_amps=*', "load_amps", "load amps", "slip_id", "slip", "marina electricity use", crit="medium"),
        avg_by("NOAA Tide Slack-Window Match by Harbor", "tide:table", 'harbor=* slack_window_min=*', "slack_window_min", "slack-water window minutes", "harbor", "harbor", "tide-planning windows"),
        avg_by("Tide Height vs Departure Delay", "tide:table", 'harbor=* departure_delay_min=*', "departure_delay_min", "departure delay minutes", "harbor", "harbor", "tide-aware departures", mtypes=AVAIL_ANALYTICS),
        rate_by("Bilge Callout vs Low-Voltage Correlation", "marine:battery", 'battery_bank=* bilge_followup=*', 'bilge_followup="yes"', "a bilge follow-up", "battery_bank", "battery bank", "battery events", mtypes=ANOM),
        avg_by("Anchoring Window by Tide State", "tide:table", 'tide_state=* anchor_window_min=*', "anchor_window_min", "anchor window minutes", "tide_state", "tide state", "anchoring opportunities"),
        rate_by("AIS Stationary-Vessel Drift Watch", "marine:ais", 'anchorage=* drift_alert=*', 'drift_alert="yes"', "a drift alert", "anchorage", "anchorage", "stationary-vessel intervals", crit="medium", mtypes=ANOM),
        trend_by_month("Victron Charge Cycle Efficiency Trend", "marine:battery", 'charge_source=* charge_efficiency_pct=*', "avg(charge_efficiency_pct)", "charge efficiency percentage", "charge_source", "charge source", "battery maintenance"),
        avg_by("Marina Power Cost per Weekend Stay", "marina:power", 'marina_name=* weekend_cost_usd=*', "weekend_cost_usd", "weekend power cost", "marina_name", "marina", "weekend marina stays", mtypes=BUSINESS),
        lag_by("Tide Forecast Freshness Watch", "marine:export", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "tide-data sync lag", "source_name", "data source", "marine data exports", mtypes=AVAIL),
        backlog_by("Marine Telemetry Export Gap", "marine:export", 'source_name=* export_state=*', 'export_state!="complete"', "source_name", "data source", "export jobs", "marine telemetry operations", mtypes=AVAIL),
    ],
    "44": [
        avg_by("Fishbrain Species Yield by Lure", "outdoor:trip", 'platform="fishbrain" lure=* fish_caught=*', "fish_caught", "fish caught", "lure", "lure", "Fishbrain catch sessions"),
        avg_by("Fishbrain Catch Window by Weather Band", "outdoor:trip", 'platform="fishbrain" weather_band=* catch_window_min=*', "catch_window_min", "catch-window minutes", "weather_band", "weather band", "catch timing"),
        count_by("onX Hunt Stand Visit Heatmap", "hunt:map", 'stand_name=*', "stand_name", "stand", "stand visits", "onX Hunt activity"),
        rate_by("onX Hunt Property Boundary Near-Miss Alerts", "hunt:map", 'property_name=* near_miss=*', 'near_miss="yes"', "a boundary near miss", "property_name", "property", "hunt-map traversals", crit="medium", mtypes=ANOM),
        lag_by("iNaturalist Foraging Identification Lag", "forage:observation", 'species_group=* observed_epoch=* identified_epoch=*', "identified_epoch-observed_epoch", "identification lag", "species_group", "species group", "foraging observations"),
        rate_by("iNaturalist Observation Confidence by Species", "forage:observation", 'species=* community_id_agrees=*', 'community_id_agrees="yes"', "community agreement", "species", "species", "foraging observations"),
        rate_by("Smoker Temperature Excursion Rate", "cook:smoker", 'probe_name=* temp_excursion=*', 'temp_excursion="yes"', "a temperature excursion", "probe_name", "smoker probe", "smoker sessions", crit="medium", mtypes=ANOM),
        avg_by("Smoker Stall Duration by Meat Cut", "cook:smoker", 'meat_cut=* stall_duration_min=*', "stall_duration_min", "stall duration minutes", "meat_cut", "meat cut", "smoker cooks"),
        lag_by("Fishbrain Skunk-Recovery Time", "outdoor:trip", 'waterbody=* last_skunk_epoch=* trip_start_epoch=* outcome="catch"', "trip_start_epoch-last_skunk_epoch", "skunk-recovery lag", "waterbody", "waterbody", "return-to-success cycles", unit="days", divisor=86400),
        lag_by("onX Hunt Scouting-to-Harvest Lag", "hunt:map", 'zone=* scouting_epoch=* harvest_epoch=* harvest_epoch=*', "harvest_epoch-scouting_epoch", "scouting-to-harvest lag", "zone", "hunt zone", "scouting workflows", unit="days", divisor=86400),
        rate_by("Foraging Blacklist Violation Watch", "forage:observation", 'region=* restricted_species_flag=*', 'restricted_species_flag="yes"', "a restricted-species flag", "region", "region", "foraging records", crit="medium", mtypes=ANOM),
        avg_by("Smoker Pellet Consumption per Session", "cook:smoker", 'fuel_type=* pellets_lb=*', "pellets_lb", "pellet pounds", "fuel_type", "fuel type", "smoker sessions", mtypes=BUSINESS),
        backlog_by("Cross-App Spot Note Backlog", "outdoor:queue", 'source_app=* note_state=*', 'note_state!="linked"', "source_app", "source app", "spot notes", "outdoor research logs"),
        backlog_by("Harvest Processing Queue Age", "outdoor:queue", 'item_type="harvest" processing_state=*', 'processing_state!="complete"', "processing_state", "processing state", "harvest items", "post-trip processing"),
        lag_by("Outdoor Season Prep Checklist Freshness", "outdoor:queue", 'season=* last_update_epoch=* checklist_due_epoch=*', "checklist_due_epoch-last_update_epoch", "prep-checklist freshness gap", "season", "season", "season-opening readiness", unit="days", divisor=86400, mtypes=AVAIL),
    ],
    "45": [
        lag_by("DistroKid Release Approval Lag", "music:distribution", 'release_type=* submitted_epoch=* approved_epoch=*', "approved_epoch-submitted_epoch", "release approval lag", "release_type", "release type", "DistroKid release operations", unit="hours", divisor=3600, mtypes=AVAIL_ANALYTICS),
        trend_by_month("DistroKid Stream Spike After Pitching", "music:distribution", 'pitch_channel=* stream_lift_pct=*', "avg(stream_lift_pct)", "stream lift percentage", "pitch_channel", "pitch channel", "release campaigns", mtypes=BUSINESS),
        rate_by("Bandcamp Friday Conversion Rate", "music:bandcamp", 'campaign_day=* purchased=*', 'purchased="yes"', "a purchase", "campaign_day", "campaign day", "Bandcamp visits", mtypes=BUSINESS),
        rate_by("Bandcamp Wishlist-to-Purchase Ratio", "music:bandcamp", 'release_name=* purchased_after_wishlist=*', 'purchased_after_wishlist="yes"', "a wishlist conversion", "release_name", "release", "wishlist events", mtypes=BUSINESS),
        rate_by("Reaper Project Bounce Failure Hotspots", "music:project", 'project_template=* bounce_failed=*', 'bounce_failed="yes"', "a failed bounce", "project_template", "project template", "Reaper export attempts", mtypes=ANOM),
        avg_by("Reaper Track Count vs Export Time", "music:project", 'project_size=* export_time_min=*', "export_time_min", "export time minutes", "project_size", "project size band", "Reaper project exports"),
        rate_by("Spotify for Artists Save-to-Stream Ratio", "music:streaming", 'track_name=* saved_after_stream=*', 'saved_after_stream="yes"', "a save after streaming", "track_name", "track", "Spotify listener sessions", mtypes=BUSINESS),
        trend_by_month("Spotify for Artists Playlist Lift Persistence", "music:streaming", 'playlist_name=* stream_lift_pct=*', "avg(stream_lift_pct)", "playlist lift percentage", "playlist_name", "playlist", "playlist placement effects", mtypes=BUSINESS),
        expiry_watch("Release Calendar Gap Watch", "music:ops", 'release_name=* planned_release_epoch=* release_state=*', "planned_release_epoch", 'release_state!="released"', ["release_name", "release_state"], "scheduled releases", "release calendar coverage", unit="days", divisor=86400, mtypes=AVAIL),
        backlog_by("Catalog Metadata Correction Backlog", "music:ops", 'store_name=* metadata_state=*', 'metadata_state!="clean"', "store_name", "store", "metadata fixes", "catalog operations"),
        trend_by_month("Cross-Platform Revenue Mix Trend", "music:distribution", 'platform=* payout_usd=*', "sum(payout_usd)", "payout dollars", "platform", "platform", "creator revenue mix", mtypes=BUSINESS),
        trend_by_month("Single-to-Album Follower Lift", "music:streaming", 'release_format=* follower_lift=*', "avg(follower_lift)", "follower lift", "release_format", "release format", "audience growth", mtypes=BUSINESS),
        avg_by("Mastering Revision Cycle Count", "music:project", 'engineer=* revision_cycles=*', "revision_cycles", "revision cycles", "engineer", "mastering engineer", "mastering rounds"),
        rate_by("Bandcamp Merch Attach Rate", "music:bandcamp", 'merch_bundle=* merch_attached=*', 'merch_attached="yes"', "merch attached", "merch_bundle", "merch bundle", "Bandcamp orders", mtypes=BUSINESS),
        lag_by("Creator Analytics Export Freshness", "music:ops", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "analytics export lag", "source_name", "data source", "creator analytics feeds", mtypes=AVAIL),
    ],
    "46": [
        avg_by("D&D Beyond Character Sheet HP Drift", "rpg:character", 'class_name=* hp_drift=*', "hp_drift", "HP drift", "class_name", "class", "character-sheet health tracking", crit="medium"),
        avg_by("D&D Beyond Spell Slot Burn Rate", "rpg:character", 'class_name=* spell_slot_burn_pct=*', "spell_slot_burn_pct", "spell-slot burn percentage", "class_name", "class", "spell resource usage"),
        lag_by("Roll20 Session Start Delay", "rpg:session", 'campaign=* scheduled_start_epoch=* actual_start_epoch=*', "actual_start_epoch-scheduled_start_epoch", "session start delay", "campaign", "campaign", "Roll20 session starts", mtypes=AVAIL),
        rate_by("Roll20 Handout Review Completion Rate", "rpg:session", 'handout_type=* reviewed_before_session=*', 'reviewed_before_session="yes"', "pre-session review", "handout_type", "handout type", "Roll20 handouts"),
        avg_by("Initiative Tracker Slow-Round Hotspots", "rpg:initiative", 'encounter_type=* round_duration_sec=*', "round_duration_sec", "round duration seconds", "encounter_type", "encounter type", "initiative rounds", mtypes=ANOM),
        avg_by("Initiative Tracker Boss Encounter Pace", "rpg:initiative", 'boss_name=* round_duration_sec=*', "round_duration_sec", "round duration seconds", "boss_name", "boss encounter", "boss fights"),
        backlog_by("D&D Beyond Level-Up Backlog", "rpg:character", 'class_name=* levelup_state=*', 'levelup_state!="applied"', "class_name", "class", "pending level-ups", "character administration"),
        avg_by("Roll20 Player Attendance vs Prep Load", "rpg:session", 'campaign=* prep_load_min=*', "prep_load_min", "prep-load minutes", "campaign", "campaign", "GM preparation"),
        lag_by("Character Sheet Condition Note Freshness", "rpg:character", 'condition_name=* condition_recorded_epoch=* last_verified_epoch=*', "last_verified_epoch-condition_recorded_epoch", "condition-note freshness", "condition_name", "condition", "character status notes", unit="days", divisor=86400, mtypes=AVAIL),
        avg_by("Encounter Damage Spike Watch", "rpg:combat", 'encounter_name=* damage_spike_pct=*', "damage_spike_pct", "damage-spike percentage", "encounter_name", "encounter", "combat burst damage", crit="medium", mtypes=ANOM),
        rate_by("Session-Zero Contract Review Freshness", "rpg:ops", 'campaign=* contract_review_current=*', 'contract_review_current="yes"', "a current social contract", "campaign", "campaign", "session-zero agreements", mtypes=AVAIL),
        avg_by("HP Recovery Between Long Rests", "rpg:character", 'class_name=* hp_recovered_pct=*', "hp_recovered_pct", "HP recovered percentage", "class_name", "class", "long-rest recovery"),
        avg_by("Initiative Order Advantage by Player Count", "rpg:initiative", 'player_count_band=* encounter_outcome_score=*', "encounter_outcome_score", "encounter outcome score", "player_count_band", "player-count band", "initiative-order outcomes"),
        rate_by("Roll20 API Error Burst Watch", "rpg:session", 'campaign=* api_error_burst=*', 'api_error_burst="yes"', "an API error burst", "campaign", "campaign", "Roll20 sessions", mtypes=ANOM),
        backlog_by("Campaign Asset Archive Gap", "rpg:ops", 'asset_type=* archive_state=*', 'archive_state!="archived"', "asset_type", "asset type", "campaign assets", "campaign record-keeping", mtypes=AVAIL),
    ],
    "47": [
        backlog_by("Readwise Daily Review Backlog", "reading:highlight", 'source_app="readwise" review_state=*', 'review_state!="done"', "source_app", "source app", "daily reviews", "Readwise processing"),
        lag_by("Kindle Highlight Export Freshness", "reading:highlight", 'source_app="kindle" highlight_epoch=* export_epoch=*', "export_epoch-highlight_epoch", "Kindle export lag", "source_app", "source app", "highlight syncs", mtypes=AVAIL),
        avg_by("Goodreads TBR Age by Shelf", "reading:book", 'platform="goodreads" shelf=* tbr_age_days=*', "tbr_age_days", "TBR age days", "shelf", "shelf", "Goodreads reading backlog"),
        lag_by("Goodreads Review Completion Lag", "reading:review", 'shelf=* finished_epoch=* review_epoch=*', "review_epoch-finished_epoch", "review completion lag", "shelf", "shelf", "Goodreads reviews", unit="days", divisor=86400),
        rate_by("Zotero Paper Read-to-Cite Rate", "research:paper", 'collection=* cited_in_notes=*', 'cited_in_notes="yes"', "a citation in notes", "collection", "collection", "Zotero papers"),
        backlog_by("Zotero Attachment Missing File Watch", "research:paper", 'collection=* attachment_present=*', 'attachment_present="no"', "collection", "collection", "missing attachments", "Zotero library hygiene", mtypes=AVAIL),
        rate_by("Readwise Highlight Tag Coverage", "reading:highlight", 'source_app="readwise" tag_applied=*', 'tag_applied="yes"', "a tag", "source_app", "source app", "Readwise highlights"),
        avg_by("Kindle Highlight Density by Book", "reading:highlight", 'source_app="kindle" book_title=* highlights_per_100_pages=*', "highlights_per_100_pages", "highlights per 100 pages", "book_title", "book", "Kindle annotation density"),
        trend_by_month("Goodreads Genre Drift by Quarter", "reading:book", 'platform="goodreads" genre=*', "count", "books finished", "genre", "genre", "reading mix over time"),
        backlog_by("Zotero Duplicate Paper Queue", "research:paper", 'library_name=* duplicate_flag=*', 'duplicate_flag="yes"', "library_name", "library", "duplicate papers", "research library cleanup"),
        lag_by("Zotero Note Capture Lag", "research:paper", 'collection=* first_opened_epoch=* first_note_epoch=*', "first_note_epoch-first_opened_epoch", "note-capture lag", "collection", "collection", "paper-to-note workflows", unit="days", divisor=86400),
        rate_by("Readwise Review Streak Reliability", "reading:highlight", 'review_weekday=* streak_held=*', 'streak_held="yes"', "the streak held", "review_weekday", "weekday", "Readwise review days"),
        rate_by("Goodreads Buddy-Read Completion Rate", "reading:book", 'buddy_name=* completed=*', 'completed="yes"', "a completed buddy read", "buddy_name", "buddy", "buddy-read attempts"),
        backlog_by("Annotation OCR Correction Backlog", "reading:sync", 'source_name=* ocr_state=*', 'ocr_state!="corrected"', "source_name", "source", "OCR corrections", "annotation cleanup"),
        rate_by("Second-Brain Sync Failure Watch", "reading:sync", 'target_system=* sync_failed=*', 'sync_failed="yes"', "a failed sync", "target_system", "target system", "second-brain sync jobs", mtypes=ANOM),
    ],
    "48": [
        rate_by("Anki New-Card Suspension Rate", "language:review", 'deck=* card_state=*', 'card_state="suspended"', "a suspension", "deck", "deck", "new Anki cards"),
        avg_by("Anki Mature-Card Retention by Deck", "language:review", 'deck=* mature_retention_pct=*', "mature_retention_pct", "mature-card retention percentage", "deck", "deck", "mature Anki reviews"),
        rate_by("Duolingo Lesson Skip Friction", "language:lesson", 'course=* lesson_skipped=*', 'lesson_skipped="yes"', "a skipped lesson", "course", "course", "Duolingo lesson attempts", mtypes=ANOM),
        share_by("Duolingo XP vs Speaking Minutes Balance", "language:lesson", 'balance_bucket=*', "balance_bucket", "balance bucket", "learning sessions", "Duolingo and speaking balance"),
        lag_by("Babbel Lesson Completion Lag", "language:lesson", 'provider="babbel" lesson_started_epoch=* lesson_completed_epoch=* lesson_name=*', "lesson_completed_epoch-lesson_started_epoch", "lesson completion lag", "lesson_name", "lesson", "Babbel lessons"),
        rate_by("Babbel Review Reactivation Rate", "language:lesson", 'provider="babbel" review_set=* reactivated=*', 'reactivated="yes"', "a reactivated review set", "review_set", "review set", "Babbel reviews"),
        trend_by_month("Immersion Hours by Media Type", "language:immersion", 'media_type=* hours=*', "sum(hours)", "immersion hours", "media_type", "media type", "immersion practice"),
        count_by("Tutor Session Correction Theme Rank", "language:tutor", 'feedback_theme=*', "feedback_theme", "feedback theme", "correction notes", "tutor feedback"),
        backlog_by("Anki Leech Queue Age", "language:review", 'deck=* leech_state=*', 'leech_state="open"', "deck", "deck", "leech cards", "deck maintenance"),
        share_by("Cross-App Study Mix Balance", "language:sync", 'study_source=*', "study_source", "study source", "study events", "cross-app learning balance"),
        trend_by_month("Speaking Confidence Trend After Tutor Sessions", "language:tutor", 'language=* confidence_score=*', "avg(confidence_score)", "confidence score", "language", "language", "speaking practice"),
        lag_by("Immersion Streak Break Recovery Time", "language:immersion", 'language=* streak_break_epoch=* streak_resume_epoch=*', "streak_resume_epoch-streak_break_epoch", "streak-recovery lag", "language", "language", "immersion habit recovery", unit="days", divisor=86400),
        lag_by("Vocabulary Export Freshness Watch", "language:sync", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "vocabulary export lag", "source_name", "data source", "language-learning syncs", mtypes=AVAIL),
        rate_by("Tutor Homework Closure Rate", "language:tutor", 'tutor_name=* homework_closed=*', 'homework_closed="yes"', "closed homework", "tutor_name", "tutor", "tutor homework items", mtypes=AVAIL_ANALYTICS),
        trend_by_month("CEFR Goal Burn-Up Across Apps", "language:sync", 'goal_level=* progress_points=*', "sum(progress_points)", "progress points", "goal_level", "CEFR goal", "cross-app CEFR progress", mtypes=BUSINESS),
    ],
    "49": [
        lag_by("Stylebook Outfit Repeat Gap", "style:wardrobe", 'category=* last_worn_epoch=* worn_epoch=*', "worn_epoch-last_worn_epoch", "outfit repeat gap", "category", "category", "wardrobe rotation", unit="days", divisor=86400),
        share_by("Stylebook Closet Category Imbalance", "style:wardrobe", 'category=*', "category", "category", "closet items", "Stylebook inventory"),
        lag_by("Dry-Clean Pickup Delay", "style:cleaning", 'cleaner_name=* ready_epoch=* picked_up_epoch=*', "picked_up_epoch-ready_epoch", "dry-clean pickup delay", "cleaner_name", "cleaner", "dry-cleaning pickups", unit="days", divisor=86400, mtypes=AVAIL),
        avg_by("Dry-Clean Spend by Garment Type", "style:cleaning", 'garment_type=* spend_usd=*', "spend_usd", "dry-clean spend", "garment_type", "garment type", "cleaning bills", mtypes=BUSINESS),
        lag_by("Shoe Rotation Rest Days by Pair", "style:shoes", 'pair_name=* last_wear_epoch=* wear_epoch=*', "wear_epoch-last_wear_epoch", "rest days", "pair_name", "shoe pair", "shoe rotation", unit="days", divisor=86400),
        rate_by("Shoe Rotation Wear-Out Risk", "style:shoes", 'pair_name=* wearout_flag=*', 'wearout_flag="yes"', "a wear-out flag", "pair_name", "shoe pair", "shoe wear intervals", mtypes=ANOM),
        expiry_watch("Makeup Expiry Queue by Month", "beauty:product", 'product_name=* expiry_epoch=* status=*', "expiry_epoch", 'status!="discarded"', ["product_name", "category", "status"], "makeup products", "beauty inventory", unit="days", divisor=86400, mtypes=AVAIL),
        rate_by("Makeup Product Open-to-Finish Rate", "beauty:product", 'category=* finished=*', 'finished="yes"', "a finished product", "category", "category", "opened beauty products", mtypes=BUSINESS),
        lag_by("Outfit Photo Logging Freshness", "style:wardrobe", 'source_name=* worn_epoch=* photo_logged_epoch=*', "photo_logged_epoch-worn_epoch", "outfit photo lag", "source_name", "capture source", "outfit photo logging", mtypes=AVAIL),
        rate_by("Seasonal Capsule Completion Rate", "style:wardrobe", 'season=* capsule_ready=*', 'capsule_ready="yes"', "a complete capsule", "season", "season", "capsule wardrobes"),
        lag_by("Laundry-to-Closet Return Lag", "style:cleaning", 'garment_type=* cleaned_epoch=* returned_epoch=*', "returned_epoch-cleaned_epoch", "laundry return lag", "garment_type", "garment type", "laundry turnaround", unit="days", divisor=86400),
        rate_by("Travel Packing Rewear Coverage", "style:wardrobe", 'trip_name=* rewear_covered=*', 'rewear_covered="yes"', "rewear coverage", "trip_name", "trip", "packing plans"),
        rate_by("Stylebook Wishlist Conversion Rate", "style:wardrobe", 'wishlist_group=* purchased=*', 'purchased="yes"', "a purchase", "wishlist_group", "wishlist group", "Stylebook wishlist items", mtypes=BUSINESS),
        share_by("Heels vs Sneaker Utilization Split", "style:shoes", 'shoe_family=*', "shoe_family", "shoe family", "shoe wears", "footwear use balance"),
        lag_by("Beauty Inventory Audit Staleness", "style:audit", 'area_name=* last_audit_epoch=* now_epoch=*', "now_epoch-last_audit_epoch", "inventory audit staleness", "area_name", "storage area", "beauty-inventory reviews", unit="days", divisor=86400, mtypes=AVAIL),
    ],
    "50": [
        rate_by("Olio Listing-to-Pickup Conversion", "sustain:share", 'listing_type=* picked_up=*', 'picked_up="yes"', "a pickup", "listing_type", "listing type", "Olio listings", mtypes=BUSINESS),
        lag_by("Olio Donation Response Lag", "sustain:share", 'item_category=* listed_epoch=* first_response_epoch=*', "first_response_epoch-listed_epoch", "response lag", "item_category", "item category", "shared items", mtypes=AVAIL_ANALYTICS),
        rate_by("Repair Cafe Fix Success Rate", "sustain:repair", 'item_type=* fixed=*', 'fixed="yes"', "a successful fix", "item_type", "item type", "repair attempts", crit="medium", mtypes=BUSINESS),
        backlog_by("Repair Cafe Part-Revisit Backlog", "sustain:repair", 'repair_station=* revisit_state=*', 'revisit_state!="closed"', "repair_station", "repair station", "revisit jobs", "repair workflows"),
        trend_by_month("Compost Weight Trend by Month", "sustain:compost", 'bin_name=* weight_kg=*', "sum(weight_kg)", "compost kilograms", "bin_name", "bin", "composting progress"),
        rate_by("Compost Contamination Incident Rate", "sustain:compost", 'bin_name=* contamination_flag=*', 'contamination_flag="yes"', "a contamination incident", "bin_name", "bin", "compost drops", mtypes=ANOM),
        trend_by_month("Solar Offset vs Home Load", "sustain:solar", 'inverter_name=* offset_kwh=*', "sum(offset_kwh)", "offset kilowatt-hours", "inverter_name", "inverter", "solar self-offset"),
        rate_by("Solar Export Clipping Hours", "sustain:solar", 'inverter_name=* clipping_hour=*', 'clipping_hour="yes"', "a clipping hour", "inverter_name", "inverter", "solar production hours", mtypes=ANOM),
        rate_by("Zero-Waste Goal Scorecard by Week", "sustain:audit", 'goal_name=* goal_met=*', 'goal_met="yes"', "a met goal", "goal_name", "goal", "weekly zero-waste goals"),
        avg_by("Refill Station Trip Payback Time", "sustain:share", 'station_name=* payback_trips=*', "payback_trips", "payback trips", "station_name", "refill station", "refill habits", mtypes=BUSINESS),
        share_by("Community Share vs Disposal Balance", "sustain:share", 'disposition=*', "disposition", "disposition", "shared-item outcomes", "reuse versus disposal"),
        lag_by("Compost Bin Collection Freshness", "sustain:compost", 'collection_point=* last_collection_epoch=* current_snapshot_epoch=*', "current_snapshot_epoch-last_collection_epoch", "collection freshness", "collection_point", "collection point", "compost collection coverage", unit="days", divisor=86400, mtypes=AVAIL),
        backlog_by("Repair Queue Age by Item Type", "sustain:repair", 'item_type=* repair_state=*', 'repair_state!="closed"', "item_type", "item type", "repair queue items", "repair backlogs"),
        rate_by("Solar Inverter Offline Watch", "sustain:solar", 'inverter_name=* offline_flag=*', 'offline_flag="yes"', "an offline interval", "inverter_name", "inverter", "solar telemetry intervals", crit="medium", mtypes=AVAIL),
        lag_by("Sustainability Evidence Export Freshness", "sustain:audit", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "evidence export lag", "source_name", "data source", "sustainability evidence feeds", mtypes=AVAIL),
    ],
    "51": [
        rate_by("Insulin Pump Basal Override Frequency", "health:glucose", 'pump_profile=* basal_override=*', 'basal_override="yes"', "a basal override", "pump_profile", "pump profile", "insulin-pump intervals", crit="medium"),
        lag_by("Insulin Pump Pod Change Delay", "health:glucose", 'site_region=* change_due_epoch=* change_completed_epoch=*', "change_completed_epoch-change_due_epoch", "pod-change delay", "site_region", "site region", "infusion set changes", unit="hours", divisor=3600, crit="medium", mtypes=AVAIL),
        trend_by_month("A1c Result Trend by Quarter", "health:lab", 'lab_source=* a1c_value=*', "avg(a1c_value)", "A1c result", "lab_source", "lab source", "quarterly A1c checks", crit="medium"),
        lag_by("Lab Result Upload Freshness", "health:lab", 'lab_source=* collected_epoch=* uploaded_epoch=*', "uploaded_epoch-collected_epoch", "lab upload lag", "lab_source", "lab source", "lab-result imports", crit="medium", mtypes=AVAIL),
        rate_by("Physical Therapy Rep Completion Rate", "health:pt", 'exercise_name=* target_met=*', 'target_met="yes"', "the prescribed reps complete", "exercise_name", "exercise", "physical-therapy sessions", crit="medium"),
        rate_by("PT Pain Spike by Exercise", "health:pt", 'exercise_name=* pain_spike=*', 'pain_spike="yes"', "a pain spike", "exercise_name", "exercise", "physical-therapy sessions", crit="medium", mtypes=ANOM),
        lag_by("Symptom Diary Entry Freshness", "health:symptom", 'symptom_family=* symptom_epoch=* logged_epoch=*', "logged_epoch-symptom_epoch", "symptom logging lag", "symptom_family", "symptom family", "symptom diaries", crit="medium", mtypes=AVAIL),
        trend_by_month("Symptom Flare vs Glucose Variance", "health:symptom", 'symptom_family=* glucose_variance=*', "avg(glucose_variance)", "glucose variance", "symptom_family", "symptom family", "flare tracking", crit="medium"),
        rate_by("Missed Bolus Window by Meal Type", "health:glucose", 'meal_type=* bolus_on_time=*', 'bolus_on_time="no"', "a missed bolus window", "meal_type", "meal type", "meal bolus events", crit="medium", mtypes=ANOM),
        avg_by("Overnight Glucose Stability Score", "health:glucose", 'overnight_profile=* stability_score=*', "stability_score", "stability score", "overnight_profile", "overnight profile", "overnight glucose control", crit="medium"),
        rate_by("Exercise-Adherence Streak After PT Plan Updates", "health:pt", 'plan_version=* streak_kept=*', 'streak_kept="yes"', "an adherence streak kept", "plan_version", "plan version", "exercise streaks", crit="medium"),
        backlog_by("Care-Team Question Backlog", "health:ops", 'question_type=* response_state=*', 'response_state!="answered"', "question_type", "question type", "care-team questions", "care coordination", crit="medium", mtypes=AVAIL),
        rate_by("Sensor Calibration Exception Rate", "health:glucose", 'sensor_type=* calibration_exception=*', 'calibration_exception="yes"', "a calibration exception", "sensor_type", "sensor type", "sensor readings", crit="medium", mtypes=ANOM),
        expiry_watch("Medication Supply Days Remaining", "health:ops", 'medication_name=* supply_exhaust_epoch=* active=*', "supply_exhaust_epoch", 'active="yes"', ["medication_name", "active"], "medication supplies", "medication coverage", unit="days", divisor=86400, crit="medium", mtypes=AVAIL),
        rate_by("Self-Management Dashboard Coverage Gap", "health:ops", 'signal_name=* currently_tracked=*', 'currently_tracked="yes"', "currently tracked coverage", "signal_name", "signal", "self-management signals", crit="medium"),
    ],
    "52": [
        lag_by("PERS Pendant Test-Call Freshness", "care:pendant", 'device_id=* last_test_epoch=* snapshot_epoch=*', "snapshot_epoch-last_test_epoch", "test-call freshness", "device_id", "device", "pendant readiness", unit="days", divisor=86400, crit="medium", mtypes=AVAIL),
        lag_by("PERS Alert Response Time by Contact", "care:pendant", 'contact_name=* alert_epoch=* acknowledged_epoch=*', "acknowledged_epoch-alert_epoch", "alert response time", "contact_name", "contact", "PERS alerts", crit="medium", mtypes=AVAIL),
        rate_by("Medication Blister Pack Completion Rate", "care:medication", 'dose_window=* dose_taken=*', 'dose_taken="yes"', "a taken dose", "dose_window", "dose window", "blister-pack reminders", crit="medium"),
        rate_by("Missed Dose Pocket Pattern", "care:medication", 'pocket_name=* dose_taken=*', 'dose_taken="no"', "a missed dose", "pocket_name", "blister pocket", "blister-pack doses", crit="medium", mtypes=ANOM),
        rate_by("Wandering Geofence Exit Frequency", "care:geofence", 'zone_name=* exit_alert=*', 'exit_alert="yes"', "a geofence exit", "zone_name", "zone", "location intervals", crit="medium", mtypes=ANOM),
        lag_by("Geofence Safe-Return Lag", "care:geofence", 'zone_name=* exit_epoch=* return_epoch=*', "return_epoch-exit_epoch", "safe-return lag", "zone_name", "zone", "wandering episodes", crit="medium", mtypes=AVAIL),
        rate_by("Overnight Door Activity vs Geofence Alerts", "care:geofence", 'door_zone=* overnight_alert=*', 'overnight_alert="yes"', "an overnight alert", "door_zone", "door zone", "overnight movement intervals", crit="medium", mtypes=ANOM),
        rate_by("Check-In Call Miss Rate", "care:checkin", 'contact_name=* call_answered=*', 'call_answered="no"', "a missed check-in", "contact_name", "contact", "care check-in calls", crit="medium", mtypes=ANOM),
        trend_by_month("Mobility Visit Coverage by Week", "care:checkin", 'visit_type=* visits_completed=*', "sum(visits_completed)", "completed visits", "visit_type", "visit type", "weekly support coverage", crit="medium"),
        rate_by("Pendant Battery Low Incident Trend", "care:pendant", 'device_id=* battery_low=*', 'battery_low="yes"', "a low-battery incident", "device_id", "device", "pendant battery intervals", crit="medium", mtypes=ANOM),
        backlog_by("Appointment Escort Coordination Gap", "care:ops", 'appointment_type=* escort_state=*', 'escort_state!="assigned"', "appointment_type", "appointment type", "escort assignments", "appointment coordination", crit="medium", mtypes=AVAIL),
        expiry_watch("Medication Refill Lead Time", "care:medication", 'medication_name=* refill_due_epoch=* active=*', "refill_due_epoch", 'active="yes"', ["medication_name", "active"], "medication refills", "medication continuity", unit="days", divisor=86400, crit="medium", mtypes=AVAIL),
        lag_by("Geofence Location Export Freshness", "care:geofence", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "geofence export lag", "source_name", "data source", "care-location feeds", crit="medium", mtypes=AVAIL),
        backlog_by("Care Plan Note Follow-Up Backlog", "care:ops", 'note_type=* followup_state=*', 'followup_state!="closed"', "note_type", "note type", "care-plan follow-ups", "care-plan administration", crit="medium", mtypes=AVAIL),
        rate_by("Caregiver Contact Drill Completion Rate", "care:checkin", 'drill_name=* completed=*', 'completed="yes"', "a completed drill", "drill_name", "drill", "caregiver contact drills", crit="medium", mtypes=AVAIL),
    ],
    "53": [
        rate_by("The Knot Checklist Completion Burn-Up", "event:checklist", 'milestone_name=* completed=*', 'completed="yes"', "a completed task", "milestone_name", "milestone", "The Knot checklist tasks", mtypes=BUSINESS),
        backlog_by("The Knot Task Overdue Hotspots", "event:checklist", 'task_bucket=* task_state=* overdue=*', 'overdue="yes"', "task_bucket", "task bucket", "overdue tasks", "planning workloads", mtypes=AVAIL),
        rate_by("Seating Chart Table Reassignment Rate", "event:seating", 'table_name=* reassigned=*', 'reassigned="yes"', "a reassignment", "table_name", "table", "seating assignments"),
        rate_by("Seating Chart Family Balance Gaps", "event:seating", 'family_group=* balanced=*', 'balanced="no"', "an imbalance", "family_group", "family group", "seating groups", mtypes=ANOM),
        expiry_watch("Vendor Deposit Due-Soon Watch", "event:deposit", 'vendor_name=* due_epoch=* payment_state=*', "due_epoch", 'payment_state!="paid"', ["vendor_name", "vendor_type", "payment_state"], "vendor deposits", "deposit deadlines", unit="days", divisor=86400, crit="medium", mtypes=AVAIL),
        lag_by("Deposit Payment Lag by Vendor Type", "event:deposit", 'vendor_type=* invoice_epoch=* paid_epoch=*', "paid_epoch-invoice_epoch", "deposit payment lag", "vendor_type", "vendor type", "vendor deposit payments", unit="days", divisor=86400, crit="medium"),
        rate_by("RSVP Meal Choice Coverage", "event:vendor", 'meal_option=* meal_choice_captured=*', 'meal_choice_captured="yes"', "a captured meal choice", "meal_option", "meal option", "RSVP records"),
        backlog_by("Contract Signature Backlog", "event:vendor", 'vendor_type=* contract_state=*', 'contract_state!="signed"', "vendor_type", "vendor type", "unsigned contracts", "vendor contracting", crit="medium", mtypes=AVAIL),
        lag_by("Invitation Mail-to-RSVP Lag", "event:vendor", 'guest_group=* mailed_epoch=* rsvp_epoch=*', "rsvp_epoch-mailed_epoch", "mail-to-RSVP lag", "guest_group", "guest group", "RSVP response timing", unit="days", divisor=86400),
        trend_by_month("Final Headcount Volatility by Week", "event:vendor", 'week_bucket=* headcount_delta=*', "sum(headcount_delta)", "headcount delta", "week_bucket", "week bucket", "headcount planning", mtypes=BUSINESS),
        rate_by("Seating Chart Revision Freeze Breach", "event:seating", 'week_bucket=* freeze_breach=*', 'freeze_breach="yes"', "a revision freeze breach", "week_bucket", "week bucket", "late seating edits", mtypes=ANOM),
        avg_by("Budget vs Deposit Exposure", "event:deposit", 'vendor_type=* deposit_exposure_pct=*', "deposit_exposure_pct", "deposit exposure percentage", "vendor_type", "vendor type", "budget exposure", crit="medium", mtypes=BUSINESS),
        lag_by("Ceremony Rehearsal Checklist Freshness", "event:checklist", 'owner=* last_review_epoch=* rehearsal_epoch=*', "rehearsal_epoch-last_review_epoch", "rehearsal-checklist freshness", "owner", "owner", "ceremony rehearsal prep", unit="days", divisor=86400, mtypes=AVAIL),
        backlog_by("Vendor Insurance Certificate Gap", "event:vendor", 'vendor_type=* insurance_state=*', 'insurance_state!="received"', "vendor_type", "vendor type", "insurance certificates", "vendor compliance", crit="medium", mtypes=AVAIL),
        lag_by("Wedding Planning Export Freshness", "event:sync", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "planning export lag", "source_name", "data source", "wedding-planning feeds", mtypes=AVAIL),
    ],
    "54": [
        rate_by("Gantt Milestone Slip Rate", "reno:gantt", 'phase_name=* slipped=*', 'slipped="yes"', "a slipped milestone", "phase_name", "phase", "Gantt milestones", crit="medium", mtypes=ANOM),
        backlog_by("Critical Path Task Age", "reno:gantt", 'phase_name=* critical_open=*', 'critical_open="yes"', "phase_name", "phase", "open critical-path tasks", "critical path management", crit="medium", mtypes=AVAIL),
        rate_by("Punch List Closure Rate", "reno:punchlist", 'room=* closed=*', 'closed="yes"', "a closed punch item", "room", "room", "punch-list items", crit="medium"),
        rate_by("Punch List Reopen Frequency", "reno:punchlist", 'room=* reopened=*', 'reopened="yes"', "a reopened item", "room", "room", "closed punch-list items", crit="medium", mtypes=ANOM),
        lag_by("Inspection Photo Log Upload Lag", "reno:photo", 'trade=* captured_epoch=* uploaded_epoch=*', "uploaded_epoch-captured_epoch", "photo upload lag", "trade", "trade", "inspection photo logs", mtypes=AVAIL),
        rate_by("Photo Evidence Missing-Room Coverage", "reno:photo", 'room=* evidence_complete=*', 'evidence_complete="no"', "missing evidence", "room", "room", "inspection photo sets", mtypes=ANOM),
        expiry_watch("Permit Expiry Risk by Trade", "reno:permit", 'permit_name=* expiry_epoch=* permit_state=*', "expiry_epoch", 'permit_state="active"', ["permit_name", "trade", "permit_state"], "active permits", "permit compliance", unit="days", divisor=86400, crit="medium", mtypes=AVAIL),
        trend_by_month("Permit Renewal Lead-Time Trend", "reno:permit", 'trade=* renewal_lead_days=*', "avg(renewal_lead_days)", "renewal lead days", "trade", "trade", "permit renewals", crit="medium"),
        lag_by("Contractor Daily Log Freshness", "reno:ops", 'contractor_name=* workday_epoch=* log_submitted_epoch=*', "log_submitted_epoch-workday_epoch", "daily-log lag", "contractor_name", "contractor", "contractor reporting", mtypes=AVAIL),
        lag_by("Material Delivery vs Gantt Dependency Gap", "reno:ops", 'dependency_name=* material_arrival_epoch=* dependency_need_epoch=*', "material_arrival_epoch-dependency_need_epoch", "material dependency gap", "dependency_name", "dependency", "material deliveries", unit="days", divisor=86400, crit="medium", mtypes=AVAIL_ANALYTICS),
        count_by("Inspection Failure Theme Rank", "reno:photo", 'failure_theme=*', "failure_theme", "failure theme", "inspection failures", "inspection findings"),
        count_by("Punch List Density by Room", "reno:punchlist", 'room=*', "room", "room", "punch-list items", "room-level work"),
        lag_by("Change Order Approval Cycle Time", "reno:ops", 'change_type=* requested_epoch=* approved_epoch=*', "approved_epoch-requested_epoch", "approval cycle time", "change_type", "change type", "change orders", unit="days", divisor=86400, crit="medium"),
        backlog_by("Permit Document Archive Backlog", "reno:permit", 'trade=* archive_state=*', 'archive_state!="archived"', "trade", "trade", "permit files", "permit record-keeping", mtypes=AVAIL),
        rate_by("Renovation Control Tower Scorecard", "reno:ops", 'workstream=* on_track=*', 'on_track="yes"', "on-track status", "workstream", "workstream", "renovation workstreams", crit="medium", mtypes=BUSINESS),
    ],
    "55": [
        backlog_by("Ancestry Hint Triage Backlog", "genealogy:hint", 'hint_type=* triage_state=*', 'triage_state!="done"', "hint_type", "hint type", "untriaged hints", "Ancestry hint review"),
        rate_by("Hint Acceptance vs Rejection Ratio", "genealogy:hint", 'record_collection=* accepted=*', 'accepted="yes"', "an accepted hint", "record_collection", "record collection", "Ancestry hints"),
        share_by("Cemetery Visit Coverage by Ancestor Line", "genealogy:cemetery", 'ancestor_line=*', "ancestor_line", "ancestor line", "cemetery visits", "family-line coverage"),
        lag_by("Grave Photo Request Completion Lag", "genealogy:cemetery", 'memorial_site=* requested_epoch=* fulfilled_epoch=*', "fulfilled_epoch-requested_epoch", "photo-request lag", "memorial_site", "memorial site", "grave-photo requests", unit="days", divisor=86400),
        backlog_by("Photo Restoration Queue Age", "genealogy:photo", 'format_type=* restoration_state=*', 'restoration_state!="done"', "format_type", "format type", "restoration jobs", "family-photo restoration"),
        avg_by("Restoration Approval Cycle Count", "genealogy:photo", 'vendor_name=* approval_cycles=*', "approval_cycles", "approval cycles", "vendor_name", "restoration vendor", "restoration reviews"),
        backlog_by("Source Citation Gap After Hint Acceptance", "genealogy:hint", 'record_collection=* citation_added=* accepted=*', 'accepted="yes" AND citation_added="no"', "record_collection", "record collection", "accepted hints without citations", "research proofing"),
        lag_by("Family Group Sheet Update Lag", "genealogy:ops", 'branch_name=* accepted_epoch=* sheet_updated_epoch=*', "sheet_updated_epoch-accepted_epoch", "family-sheet update lag", "branch_name", "branch", "family group sheets", unit="days", divisor=86400),
        rate_by("Cemetery GPS Log Missing Coordinates", "genealogy:cemetery", 'cemetery_name=* coordinates_present=*', 'coordinates_present="no"', "missing coordinates", "cemetery_name", "cemetery", "cemetery visit logs", mtypes=ANOM),
        trend_by_month("Photo Scan Throughput by Album", "genealogy:photo", 'album_name=* scans_completed=*', "sum(scans_completed)", "scans completed", "album_name", "album", "photo scanning"),
        backlog_by("Obituary Retrieval Backlog", "genealogy:ops", 'newspaper_title=* retrieval_state=*', 'retrieval_state!="done"', "newspaper_title", "newspaper", "obituary requests", "document retrieval"),
        count_by("Ancestor Line Brick-Wall Heatmap", "genealogy:ops", 'ancestor_line=* brick_wall="yes"', "ancestor_line", "ancestor line", "brick-wall cases", "stalled family lines"),
        lag_by("Restoration Vendor Turnaround by Format", "genealogy:photo", 'format_type=* submitted_epoch=* returned_epoch=*', "returned_epoch-submitted_epoch", "vendor turnaround", "format_type", "format type", "restoration vendors", unit="days", divisor=86400),
        avg_by("Research Trip Expense vs Record Yield", "genealogy:ops", 'trip_name=* cost_per_record_usd=*', "cost_per_record_usd", "cost per record", "trip_name", "research trip", "research travel efficiency", mtypes=BUSINESS),
        lag_by("Genealogy Export Freshness Watch", "genealogy:ops", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "export lag", "source_name", "data source", "genealogy data feeds", mtypes=AVAIL),
    ],
    "56": [
        rate_by("Rosary Session Streak Reliability", "faith:rosary", 'weekday=* streak_kept=*', 'streak_kept="yes"', "the rosary streak held", "weekday", "weekday", "rosary sessions"),
        share_by("Rosary Mystery Coverage Balance", "faith:rosary", 'mystery=*', "mystery", "mystery", "rosary sessions", "mystery coverage"),
        rate_by("Meditation Retreat Attendance vs Registration", "faith:retreat", 'retreat_name=* attended=*', 'attended="yes"', "an attended retreat", "retreat_name", "retreat", "retreat registrations"),
        lag_by("Retreat Reflection Publishing Lag", "faith:retreat", 'retreat_name=* retreat_end_epoch=* reflection_epoch=*', "reflection_epoch-retreat_end_epoch", "reflection publishing lag", "retreat_name", "retreat", "retreat follow-up", unit="days", divisor=86400),
        trend_by_month("Church Attendance Trend by Month", "faith:attendance", 'service_type=* attended=*', "sum(eval(if(attended=\"yes\",1,0)))", "attended services", "service_type", "service type", "church attendance"),
        lag_by("Service Missed-Streak Recovery Time", "faith:attendance", 'service_type=* miss_epoch=* return_epoch=*', "return_epoch-miss_epoch", "missed-streak recovery time", "service_type", "service type", "attendance recovery", unit="days", divisor=86400),
        rate_by("Fasting Plan Completion Rate", "faith:fast", 'fast_type=* completed=*', 'completed="yes"', "a completed fast", "fast_type", "fast type", "fasting plans"),
        avg_by("Fast Break-Time Variance", "faith:fast", 'fast_type=* break_time_variance_min=*', "break_time_variance_min", "break-time variance minutes", "fast_type", "fast type", "fast completion timing"),
        rate_by("Scripture Reading Coupled With Rosary Days", "faith:ops", 'weekday=* coupled_day=*', 'coupled_day="yes"', "a day with both practices", "weekday", "weekday", "daily practice logs"),
        lag_by("Retreat Packing Checklist Freshness", "faith:retreat", 'retreat_name=* last_check_epoch=* departure_epoch=*', "departure_epoch-last_check_epoch", "packing-check freshness", "retreat_name", "retreat", "retreat preparation", unit="days", divisor=86400, mtypes=AVAIL),
        lag_by("Attendance Check-In Export Gap", "faith:attendance", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "attendance export lag", "source_name", "data source", "attendance feeds", mtypes=AVAIL),
        backlog_by("Fasting Symptom Note Backlog", "faith:fast", 'symptom_type=* note_state=*', 'note_state!="reviewed"', "symptom_type", "symptom type", "fasting notes", "fasting reviews", mtypes=AVAIL),
        rate_by("Parish Event Overlap Conflicts", "faith:ops", 'event_type=* overlap_conflict=*', 'overlap_conflict="yes"', "an overlap conflict", "event_type", "event type", "parish calendar events", mtypes=ANOM),
        rate_by("Retreat-to-Routine Carryover Rate", "faith:retreat", 'retreat_name=* routine_kept=*', 'routine_kept="yes"', "a habit carried home", "retreat_name", "retreat", "post-retreat routines"),
        rate_by("Spiritual Practice Dashboard Freshness", "faith:ops", 'signal_name=* signal_current=*', 'signal_current="yes"', "a current signal", "signal_name", "practice signal", "spiritual practice tracking", mtypes=AVAIL),
    ],
    "57": [
        rate_by("Food Bank Shift Fill Rate", "community:shift", 'shift_role=* filled=*', 'filled="yes"', "a filled shift", "shift_role", "shift role", "food-bank shifts"),
        rate_by("Food Bank No-Show Risk by Slot", "community:shift", 'slot_name=* no_show=*', 'no_show="yes"', "a no-show", "slot_name", "shift slot", "scheduled shifts", mtypes=ANOM),
        expiry_watch("Blood Donation Eligibility Countdown", "community:donation", 'donor_name=* eligible_again_epoch=* active=*', "eligible_again_epoch", 'active="yes"', ["donor_name", "donation_type"], "donor records", "blood-donation planning", unit="days", divisor=86400, mtypes=AVAIL),
        lag_by("Donation Recovery Symptom Log Freshness", "community:donation", 'donation_type=* donation_epoch=* symptom_logged_epoch=*', "symptom_logged_epoch-donation_epoch", "recovery-log lag", "donation_type", "donation type", "donation recovery notes", mtypes=AVAIL),
        rate_by("Mutual Aid Request Closure Rate", "community:mutualaid", 'request_type=* closed=*', 'closed="yes"', "a closed request", "request_type", "request type", "mutual-aid requests"),
        lag_by("Mutual Aid Response Lag by Need Type", "community:mutualaid", 'need_type=* requested_epoch=* first_response_epoch=*', "first_response_epoch-requested_epoch", "response lag", "need_type", "need type", "mutual-aid requests", mtypes=AVAIL_ANALYTICS),
        share_by("Volunteer Hours vs Household Capacity Balance", "community:impact", 'capacity_band=*', "capacity_band", "capacity band", "service weeks", "household volunteering balance"),
        count_by("Pantry Inventory Shortage Request Hotspots", "community:mutualaid", 'item_name=* shortage_flag="yes"', "item_name", "item", "shortage requests", "pantry shortages"),
        trend_by_month("Repeat Donor Interval Trend", "community:donation", 'donation_type=* interval_days=*', "avg(interval_days)", "repeat-donation interval days", "donation_type", "donation type", "donation cadence"),
        avg_by("Community Partner Referral Yield", "community:impact", 'partner_name=* referrals_closed=*', "referrals_closed", "closed referrals", "partner_name", "community partner", "partner outcomes"),
        rate_by("Shift Swap Friction by Site", "community:shift", 'site_name=* swap_needed=*', 'swap_needed="yes"', "a shift swap", "site_name", "site", "scheduled shifts", mtypes=ANOM),
        trend_by_month("Blood Donation Milestone Burn-Up", "community:donation", 'milestone_name=* milestone_points=*', "sum(milestone_points)", "milestone points", "milestone_name", "milestone", "blood-donation goals"),
        backlog_by("Mutual Aid Map Coverage Gaps", "community:mutualaid", 'region=* coverage_state=*', 'coverage_state!="covered"', "region", "region", "coverage gaps", "mutual-aid mapping", mtypes=AVAIL),
        backlog_by("Follow-Up Thank-You Backlog", "community:impact", 'channel=* thank_you_state=*', 'thank_you_state!="sent"', "channel", "channel", "thank-you notes", "follow-up operations", mtypes=AVAIL),
        lag_by("Community Service Export Freshness", "community:impact", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "service export lag", "source_name", "data source", "community-service feeds", mtypes=AVAIL),
    ],
    "58": [
        lag_by("Google Photos Takeout Backup Freshness", "memory:takeout", 'archive_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "Takeout backup lag", "archive_name", "archive", "Google Photos backups", unit="days", divisor=86400, mtypes=AVAIL),
        rate_by("Google Photos Album Download Failure Rate", "memory:takeout", 'album_name=* download_failed=*', 'download_failed="yes"', "a failed album download", "album_name", "album", "Takeout album exports", mtypes=ANOM),
        backlog_by("Journal OCR Correction Backlog", "memory:journal", 'journal_name=* ocr_state=*', 'ocr_state!="corrected"', "journal_name", "journal", "OCR corrections", "journal digitization", mtypes=AVAIL),
        avg_by("OCR Confidence by Journal Source", "memory:journal", 'journal_source=* ocr_confidence_pct=*', "ocr_confidence_pct", "OCR confidence percentage", "journal_source", "journal source", "journal OCR quality"),
        rate_by("Postcard Collection Catalog Completion", "memory:postcard", 'collection_name=* catalogued=*', 'catalogued="yes"', "a catalogued postcard", "collection_name", "collection", "postcard records"),
        share_by("Postcard Origin-Country Heatmap", "memory:postcard", 'origin_country=*', "origin_country", "origin country", "postcards", "collection geography"),
        rate_by("Photo-to-Journal Linking Rate", "memory:photo", 'journal_name=* linked_to_entry=*', 'linked_to_entry="yes"', "a linked journal entry", "journal_name", "journal", "photo moments"),
        lag_by("Memory Captioning Lag", "memory:photo", 'capture_source=* captured_epoch=* captioned_epoch=*', "captioned_epoch-captured_epoch", "captioning lag", "capture_source", "capture source", "photo captioning", unit="days", divisor=86400),
        backlog_by("Duplicate Scan Queue Age", "memory:ops", 'format_type=* dedupe_state=*', 'dedupe_state!="resolved"', "format_type", "format type", "duplicate scans", "archive cleanup", mtypes=AVAIL),
        trend_by_month("Travel Memory Coverage by Month", "memory:photo", 'trip_name=* moments_logged=*', "sum(moments_logged)", "logged moments", "trip_name", "trip", "travel memory capture"),
        trend_by_month("Handwritten Entry Transcription Throughput", "memory:journal", 'journal_name=* pages_transcribed=*', "sum(pages_transcribed)", "pages transcribed", "journal_name", "journal", "handwritten-journal transcription"),
        lag_by("Postcard Condition Review Freshness", "memory:postcard", 'storage_box=* last_review_epoch=* snapshot_epoch=*', "snapshot_epoch-last_review_epoch", "condition-review freshness", "storage_box", "storage box", "postcard preservation", unit="days", divisor=86400, mtypes=AVAIL),
        share_by("Shared Family Album Contribution Balance", "memory:photo", 'contributor=*', "contributor", "contributor", "family album uploads", "shared album participation"),
        trend_by_month("Export Size Growth Trend", "memory:takeout", 'archive_name=* export_size_gb=*', "sum(export_size_gb)", "export size GB", "archive_name", "archive", "backup growth", mtypes=BUSINESS),
        rate_by("Life-Logging Archive Integrity Score", "memory:ops", 'archive_name=* integrity_passed=*', 'integrity_passed="yes"', "an integrity pass", "archive_name", "archive", "archive validation checks", mtypes=AVAIL),
    ],
    "59": [
        rate_by("Habitica Daily Completion Rate", "lifeos:habit", 'habit_name=* daily_completed=*', 'daily_completed="yes"', "a completed daily", "habit_name", "habit", "Habitica dailies"),
        share_by("Habitica Quest Damage Contribution Balance", "lifeos:habit", 'party_member=* quest_damage=*', "party_member", "party member", "quest actions", "party quest contribution"),
        lag_by("Streaks App Chain Break Recovery Time", "lifeos:streak", 'habit_name=* chain_break_epoch=* chain_resume_epoch=*', "chain_resume_epoch-chain_break_epoch", "chain-break recovery time", "habit_name", "habit", "Streaks recovery", unit="days", divisor=86400),
        trend_by_month("Streaks App Habit Load by Day", "lifeos:streak", 'weekday=* habits_due=*', "avg(habits_due)", "habits due", "weekday", "weekday", "Streaks workload"),
        rate_by("Beeminder Pledge Increase Risk", "lifeos:beeminder", 'goal_slug=* pledge_increased=*', 'pledge_increased="yes"', "a pledge increase", "goal_slug", "goal", "Beeminder checkpoints", mtypes=ANOM),
        count_by("Beeminder Derailment Theme Rank", "lifeos:beeminder", 'derailment_theme=*', "derailment_theme", "derailment theme", "derailments", "Beeminder failures"),
        trend_by_month("Personal OKR Milestone Burn-Up", "lifeos:okr", 'objective_name=* milestone_points=*', "sum(milestone_points)", "milestone points", "objective_name", "objective", "OKR progress", mtypes=BUSINESS),
        lag_by("OKR Check-In Freshness", "lifeos:okr", 'objective_name=* last_checkin_epoch=* snapshot_epoch=*', "snapshot_epoch-last_checkin_epoch", "OKR check-in freshness", "objective_name", "objective", "OKR reviews", unit="days", divisor=86400, mtypes=AVAIL),
        backlog_by("Cross-System Goal Overlap Duplicates", "lifeos:ops", 'system_name=* overlap_resolved=*', 'overlap_resolved="no"', "system_name", "system", "duplicate goals", "cross-system goal hygiene", mtypes=AVAIL),
        share_by("Focus Area Balance Across Habits", "lifeos:habit", 'focus_area=*', "focus_area", "focus area", "habit completions", "focus-area balance"),
        lag_by("Weekly Planning-to-Execution Lag", "lifeos:ops", 'plan_bucket=* planned_epoch=* first_done_epoch=*', "first_done_epoch-planned_epoch", "planning-to-execution lag", "plan_bucket", "plan bucket", "weekly planning", unit="hours", divisor=3600),
        backlog_by("Reward Claim Backlog", "lifeos:habit", 'reward_type=* reward_claimed=*', 'reward_claimed="no"', "reward_type", "reward type", "unclaimed rewards", "gamified rewards", mtypes=AVAIL),
        rate_by("Habitica Party Check-In Reliability", "lifeos:habit", 'party_name=* checkin_done=*', 'checkin_done="yes"', "a completed party check-in", "party_name", "party", "party coordination"),
        trend_by_month("OKR Confidence Drift by Quarter", "lifeos:okr", 'objective_name=* confidence_score=*', "avg(confidence_score)", "confidence score", "objective_name", "objective", "OKR confidence"),
        lag_by("Life-OS Export Freshness", "lifeos:ops", 'source_name=* source_event_epoch=* export_epoch=*', "export_epoch-source_event_epoch", "life-OS export lag", "source_name", "data source", "life-OS sync feeds", mtypes=AVAIL),
    ],
    "60": [
        trend_by_month("Metaculus Personal Forecast Volume by Horizon", "forecast:personal", 'horizon_bucket=*', "count", "forecast count", "horizon_bucket", "horizon bucket", "personal forecasting"),
        lag_by("Prediction Journal Resolution Lag", "forecast:journal", 'topic_name=* forecast_epoch=* resolved_epoch=*', "resolved_epoch-forecast_epoch", "resolution lag", "topic_name", "topic", "prediction journal entries", unit="days", divisor=86400),
        rate_by("Calibration Bin Underconfidence Watch", "forecast:calibration", 'bin_name=* underconfident=*', 'underconfident="yes"', "underconfidence", "bin_name", "calibration bin", "calibration reviews", mtypes=ANOM),
        rate_by("Calibration Bin Overconfidence Watch", "forecast:calibration", 'bin_name=* overconfident=*', 'overconfident="yes"', "overconfidence", "bin_name", "calibration bin", "calibration reviews", mtypes=ANOM),
        trend_by_month("Brier Score Trend by Quarter", "forecast:resolution", 'quarter=* brier_score=*', "avg(brier_score)", "Brier score", "quarter", "quarter", "resolved forecasts"),
        share_by("Forecast Topic Coverage Balance", "forecast:journal", 'topic_name=*', "topic_name", "topic", "journal forecasts", "topic coverage"),
        backlog_by("Resolution Evidence Backlog", "forecast:resolution", 'source_name=* evidence_attached=*', 'evidence_attached="no"', "source_name", "evidence source", "unattached evidence items", "forecast resolution proofing", mtypes=AVAIL),
        rate_by("Confidence Update Rate Before Deadlines", "forecast:personal", 'horizon_bucket=* confidence_updated=*', 'confidence_updated="yes"', "a confidence update", "horizon_bucket", "horizon bucket", "open forecasts"),
        lag_by("Long-Horizon Forecast Survival Curve", "forecast:personal", 'horizon_bucket=* created_epoch=* still_open_epoch=*', "still_open_epoch-created_epoch", "open-forecast age", "horizon_bucket", "horizon bucket", "long-horizon forecasts", unit="days", divisor=86400),
        rate_by("Journal vs Platform Forecast Agreement", "forecast:journal", 'topic_name=* agreement_yes=*', 'agreement_yes="yes"', "agreement", "topic_name", "topic", "paired journal and platform forecasts"),
        rate_by("Surprise Event Miss Rate", "forecast:resolution", 'topic_name=* surprise_miss=*', 'surprise_miss="yes"', "a surprise miss", "topic_name", "topic", "resolved forecasts", mtypes=ANOM),
        lag_by("Forecast Review Cadence Freshness", "forecast:ops", 'horizon_bucket=* last_review_epoch=* snapshot_epoch=*', "snapshot_epoch-last_review_epoch", "review freshness", "horizon_bucket", "horizon bucket", "forecast review cycles", unit="days", divisor=86400, mtypes=AVAIL),
        backlog_by("Outcome Source Citation Gap", "forecast:resolution", 'source_name=* citation_added=*', 'citation_added="no"', "source_name", "outcome source", "missing citations", "resolution write-ups", mtypes=AVAIL),
        rate_by("Forecast Retirement Without Resolution Rate", "forecast:personal", 'retirement_reason=* resolved=*', 'resolved="no"', "retired without resolution", "retirement_reason", "retirement reason", "retired forecasts", mtypes=ANOM),
        rate_by("Personal Forecasting Dashboard Consistency", "forecast:ops", 'dashboard_name=* data_current=*', 'data_current="yes"', "current data", "dashboard_name", "dashboard", "forecasting dashboards", mtypes=AVAIL),
    ],
}


def current_counts() -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for path in CAT25.glob("UC-25.*.*.json"):
        match = re.match(r"UC-25\.(\d+)\.(\d+)\.json$", path.name)
        if match:
            counts[match.group(1)] += 1
    return counts


def refresh_category_counts() -> None:
    counts: dict[str, int] = defaultdict(int)
    total = 0
    for path in CAT25.glob("UC-25.*.*.json"):
        match = re.match(r"UC-25\.(\d+)\.(\d+)\.json$", path.name)
        if not match:
            continue
        counts[match.group(1)] += 1
        total += 1

    category_path = CAT25 / "_category.json"
    data = json.loads(category_path.read_text(encoding="utf-8"))
    for subcat in data.get("subcategories", []):
        sub_id = str(subcat.get("id", "")).split(".")[-1]
        if sub_id in TARGET_SUBS:
            subcat["useCaseCount"] = counts.get(sub_id, 0)
    data["useCaseCount"] = total
    category_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    assert set(SPECS) == set(TARGET_SUBS)
    for sub, items in SPECS.items():
        assert len(items) == EXPECTED_PER_SUB, f"expected {EXPECTED_PER_SUB} specs for 25.{sub}, found {len(items)}"
    assert sum(len(items) for items in SPECS.values()) == EXPECTED_PER_SUB * len(TARGET_SUBS)

    before = current_counts()
    for sub in TARGET_SUBS:
        assert before.get(sub, 0) == EXPECTED_START, f"expected 25.{sub} to start at {EXPECTED_START}, found {before.get(sub, 0)}"

    writer = Cat25Writer(append=True)
    created: list[str] = []
    for sub in TARGET_SUBS:
        meta = META[sub]
        for spec in SPECS[sub]:
            created.append(
                writer.U(
                    sub=sub,
                    title=spec["title"],
                    crit=spec["crit"],
                    diff=spec["diff"],
                    mtypes=spec["mtypes"],
                    spl=spec["spl"],
                    desc=spec["desc"],
                    val=spec["val"],
                    impl=spec["impl"],
                    viz=spec["viz"],
                    grandma_body=spec["grandma_body"],
                    refs=meta["refs"],
                    app=meta["app"],
                    ds=meta["ds"],
                )
            )

    refresh_category_counts()

    after = current_counts()
    for sub in TARGET_SUBS:
        assert after.get(sub, 0) == EXPECTED_END, f"expected 25.{sub} to end at {EXPECTED_END}, found {after.get(sub, 0)}"

    total_added, by_sub = writer.summary()
    print(f"script_path={SCRIPT_PATH}")
    print(f"new_use_cases={total_added}")
    for sub in TARGET_SUBS:
        print(f"25.{sub}=+{by_sub.get(sub, 0)} total={after.get(sub, 0)}")
    print(f"first_id={created[0]}")
    print(f"last_id={created[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
