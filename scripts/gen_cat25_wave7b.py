#!/usr/bin/env python3
"""Append 15 real-data use cases to cat-25 subcategories 25.21-25.40."""
from __future__ import annotations

from pathlib import Path

from gen_cat25_common import Cat25Writer, R

SCRIPT_PATH = Path(__file__).resolve()
EXPECTED_PER_SUB = 15
TARGET_SUBS = [str(sub) for sub in range(21, 41)]

LOW = "low"
MED = "medium"
HIGH = "high"
BEG = "beginner"
INT = "intermediate"
ADV = "advanced"

AN = ["Analytics"]
AAN = ["Analytics", "Anomaly"]
AV = ["Availability"]
AQ = ["Quality"]
AR = ["Reliability"]
AP = ["Performance"]
AI = ["Inventory"]
AC = ["Cost", "Analytics"]
AK = ["Analytics", "Risk"]
AO = ["Analytics", "Operations"]
RES = ["Analytics", "Resilience"]
AUD = ["Audit"]
COMP = ["Compliance"]


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


def q(source: str, *lines: str) -> str:
    return "\n".join([f"index=personal sourcetype={source}", *lines])


def first_alias(stats_expr: str, fallback: str) -> str:
    if " as " not in stats_expr:
        return fallback
    return stats_expr.split(" as ", 1)[1].split()[0]


def ts(
    title: str,
    source: str,
    subject: str,
    span: str,
    stats_expr: str,
    *,
    group_fields: str = "",
    group_label: str | None = None,
    search: str | None = None,
    crit: str = LOW,
    diff: str = BEG,
    mtypes: list[str] = AN,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    lines: list[str] = []
    if search:
        lines.append(f"| search {search}")
    lines.append(f"| bin _time span={span}")
    by = "_time"
    if group_fields:
        by += f" {group_fields}"
    lines.append(f"| stats {stats_expr} by {by}")
    lines.append("| sort - _time")
    label = group_label or group_fields
    desc = f"Tracks {subject} over time"
    if label:
        desc += f" and breaks it out by {label}."
    else:
        desc += "."
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        desc,
        why or f"A time-based view makes it easier to spot surges, gaps, and slow drift in {subject} before the pattern disappears into raw logs.",
        action or f"Send {subject} events to `index=personal` with the fields used in the breakdown and review the resulting trend at {span} granularity.",
        viz or (f"Stacked time chart of {subject} by {label}." if label else f"Time chart of {subject}."),
        grandma or f"how {subject} changes over time so the busy spells and quiet spells stand out.",
    )


def rk(
    title: str,
    source: str,
    subject: str,
    stats_expr: str,
    entity_fields: str,
    entity_label: str,
    *,
    search: str | None = None,
    where: str | None = None,
    crit: str = LOW,
    diff: str = BEG,
    mtypes: list[str] = AN,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    lines: list[str] = []
    if search:
        lines.append(f"| search {search}")
    lines.append(f"| stats {stats_expr} by {entity_fields}")
    if where:
        lines.append(f"| where {where}")
    lines.append(f"| sort 0 - {first_alias(stats_expr, 'count')}")
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        f"Ranks {entity_label}s by {subject}.",
        why or f"A ranked view quickly shows which {entity_label}s deserve attention first instead of hiding the worst outliers in the middle of a dashboard.",
        action or f"Send {subject} events to `index=personal` and keep `{entity_fields.split()[0]}` populated so the leaderboard stays actionable.",
        viz or f"Bar chart of {subject} by {entity_label}.",
        grandma or f"which {entity_label}s stand out most for {subject}.",
    )


def stale(
    title: str,
    source: str,
    subject: str,
    entity_field: str,
    entity_label: str,
    *,
    search: str | None = None,
    unit: str = "hours",
    divisor: int = 3600,
    crit: str = MED,
    diff: str = BEG,
    mtypes: list[str] = AV,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    lines: list[str] = []
    if search:
        lines.append(f"| search {search}")
    lines.extend(
        [
            f"| stats latest(_time) as last_seen count as events by {entity_field}",
            f"| eval {unit}_since=round((now()-last_seen)/{divisor},1)",
            f"| sort - {unit}_since",
        ]
    )
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        f"Shows which {entity_label}s have gone quiet for {subject}.",
        why or f"Silence is often the first sign of a broken workflow, disconnected device, or fading habit, so stale entities are worth surfacing explicitly.",
        action or f"Send {subject} events to `index=personal` and alert when the gap since the last event grows beyond the expected cadence.",
        viz or f"Table of {entity_label}s with time since last event.",
        grandma or f"which {entity_label}s have gone quiet longer than they should for {subject}.",
    )


def lat(
    title: str,
    source: str,
    subject: str,
    duration_field: str,
    *,
    group_fields: str = "",
    group_label: str | None = None,
    search: str | None = None,
    span: str | None = None,
    crit: str = MED,
    diff: str = INT,
    mtypes: list[str] = AP,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    lines: list[str] = []
    if search:
        lines.append(f"| search {search}")
    by_parts: list[str] = []
    if span:
        lines.append(f"| bin _time span={span}")
        by_parts.append("_time")
    if group_fields:
        by_parts.append(group_fields)
    by = f" by {' '.join(by_parts)}" if by_parts else ""
    lines.append(
        f"| stats avg({duration_field}) as avg_{duration_field} perc90({duration_field}) as p90_{duration_field} count as samples{by}"
    )
    lines.append(f"| sort 0 - avg_{duration_field}")
    label = group_label or group_fields
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        f"Measures {subject}" + (f" by {label}." if label else "."),
        why or f"Delay and tail-latency metrics show where {subject} is becoming sticky even when the average still looks acceptable.",
        action or f"Send the relevant duration field for {subject} to `index=personal` and review both average and p90 latency instead of relying on single examples.",
        viz or (f"Time chart of average and p90 {subject} by {label}." if span else f"Table of average and p90 {subject}."),
        grandma or f"how long {subject} usually takes, so slowdowns are obvious instead of anecdotal.",
    )


def rate(
    title: str,
    source: str,
    subject: str,
    span: str,
    success_condition: str,
    *,
    group_fields: str = "",
    group_label: str | None = None,
    search: str | None = None,
    crit: str = MED,
    diff: str = INT,
    mtypes: list[str] = AAN,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    lines: list[str] = []
    if search:
        lines.append(f"| search {search}")
    lines.append(f"| bin _time span={span}")
    by = "_time"
    if group_fields:
        by += f" {group_fields}"
    lines.extend(
        [
            f"| stats count as attempts count(eval({success_condition})) as successful by {by}",
            "| eval success_pct=if(attempts>0,round(100*successful/attempts,1),0)",
            "| sort - _time",
        ]
    )
    label = group_label or group_fields
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        f"Tracks success rate for {subject}" + (f" by {label}." if label else "."),
        why or f"Completion percentage is usually more useful than raw volume because it shows whether the workflow is still landing cleanly.",
        action or f"Capture explicit outcome states for {subject} events in `index=personal` and review both attempts and success percentage over time.",
        viz or (f"Time chart of success percentage for {subject} by {label}." if label else f"Time chart of success percentage for {subject}."),
        grandma or f"how often {subject} works the way you expect instead of quietly failing.",
    )


def manual(
    title: str,
    source: str,
    subject: str,
    lines: list[str],
    *,
    crit: str = LOW,
    diff: str = BEG,
    mtypes: list[str] = AN,
    why: str | None = None,
    action: str | None = None,
    viz: str | None = None,
    grandma: str | None = None,
) -> dict[str, object]:
    return S(
        title,
        crit,
        diff,
        mtypes,
        q(source, *lines),
        f"Examines {subject}.",
        why or f"It gives a direct read on {subject} so drift, gaps, and outliers are easier to catch early.",
        action or f"Send {subject} events to `index=personal` with the fields used in this SPL and review the outliers or trend breaks regularly.",
        viz or f"Table or chart of {subject}, depending on the selected time range.",
        grandma or f"what is happening with {subject}, so odd changes stand out quickly.",
    )


T = ts
K = rk
G = stale
L = lat
P = rate
M = manual

DEFAULTS: dict[str, dict[str, object]] = {
    "21": {
        "app": "Weak-signal and decoder telemetry from WSJT-X FT8, JS8Call, PSKReporter, Direwolf TNC, NOAA APT pass schedulers, and station-control scripts sent to Splunk HEC via APIs, ADIF/log exports, and MQTT.",
        "ds": "FT8 spots (`ft8:spot`), JS8Call messages (`js8call:message`), PSKReporter receptions (`pskreporter:spot`), Direwolf TNC telemetry (`direwolf:packet`), and NOAA APT pass events (`noaaapt:pass`).",
        "refs": R(
            ("WSJT-X", "https://wsjt.sourceforge.io/wsjtx.html"),
            ("JS8Call", "https://js8call.com/"),
            ("PSK Reporter", "https://pskreporter.info/"),
            ("Dire Wolf TNC", "https://github.com/wb2osz/direwolf"),
            ("NOAA satellites", "https://www.nesdis.noaa.gov/our-satellites/currently-flying"),
        ),
    },
    "22": {
        "app": "Astrophotography session telemetry from N.I.N.A., KStars/Ekos, PHD2, plate-solving tools, ASCOM gear, and filter-wheel controllers sent to Splunk HEC via logs and scripted inputs.",
        "ds": "NINA sequences (`nina:sequence`), NINA autofocus runs (`nina:autofocus`), Ekos scheduler and device events (`ekos:scheduler`, `ekos:device`), PHD2 guiding telemetry (`phd2:guide`), plate solves (`platesolve:run`), filter wheel events (`filterwheel:event`), and flat frames (`flatlib:frame`).",
        "refs": R(
            ("N.I.N.A.", "https://nighttime-imaging.eu/"),
            ("KStars / Ekos", "https://edu.kde.org/kstars/"),
            ("PHD2 Guiding", "https://openphdguiding.org/"),
            ("Astrometry.net", "https://astrometry.net/"),
            ("ASCOM", "https://ascom-standards.org/"),
        ),
    },
    "23": {
        "app": "Family-routine telemetry from Nanit sleep exports, Hatch routine data, school calendars, allowance and chore apps, and Apple Screen Time sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Nanit sleep sessions (`nanit:sleep`), Hatch routines (`hatch:routine`), school calendar events (`schoolcalendar:event`), allowance transactions (`allowance:txn`), and kid screen usage (`screentime:usage`).",
        "refs": R(
            ("Nanit", "https://www.nanit.com/"),
            ("Hatch Rest", "https://www.hatch.co/rest-plus/"),
            ("Google Calendar API", "https://developers.google.com/workspace/calendar/api/guides/overview"),
            ("Greenlight", "https://greenlight.com/"),
            ("Apple Screen Time", "https://support.apple.com/guide/iphone/get-started-with-screen-time-iphbfa595995/ios"),
        ),
    },
    "24": {
        "app": "Smallholding and backyard telemetry from Flow Hive scales, chicken coop counters, RFID goat tags, compost thermometers, and camera-driven chore logs sent to Splunk HEC via MQTT and scripted inputs.",
        "ds": "Hive metrics (`flowhive:reading`), egg counter events (`eggcounter:event`), goat RFID visits (`goattag:scan`), goat watering and feed logs (`goatcare:event`), and compost readings (`compost:reading`).",
        "refs": R(
            ("Flow Hive", "https://www.honeyflow.com/"),
            ("Frigate", "https://frigate.video/"),
            ("Allflex Livestock Intelligence", "https://www.allflex.global/"),
            ("REOTEMP compost thermometers", "https://reotemp.com/products/compost-thermometers/"),
        ),
    },
    "25": {
        "app": "Personal health telemetry from Oura, OSCAR CPAP exports, oral thermometer readings, and smart body-composition scales sent to Splunk HEC via APIs and CSV exports.",
        "ds": "Oura stress and recovery (`oura:stress`), CPAP therapy sessions (`cpap:session`), oral thermometer readings (`thermometer:reading`), and body-composition scale snapshots (`bodycomp:reading`).",
        "refs": R(
            ("Oura", "https://oura.com/"),
            ("OSCAR CPAP analysis", "https://www.sleepfiles.com/OSCAR/"),
            ("Kinsa", "https://home.kinsahealth.com/"),
            ("Withings scales", "https://www.withings.com/us/en/scales"),
        ),
    },
    "26": {
        "app": "Backyard biodiversity telemetry from iNaturalist exports, moth-trap image batches, AudioMoth bat detectors, and trail-camera AI labeling pipelines sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "iNaturalist observations (`inat:observation`), moth trap sessions (`mothtrap:session`), bat detections (`batdetector:pass`), and trail-cam label events (`trailcam:label`).",
        "refs": R(
            ("iNaturalist", "https://www.inaturalist.org/"),
            ("AudioMoth", "https://www.openacousticdevices.info/audiomoth"),
            ("MegaDetector", "https://megadetector.readthedocs.io/"),
            ("Frigate", "https://frigate.video/"),
        ),
    },
    "27": {
        "app": "Aquarium and terrarium telemetry from Neptune Apex, Seneye, reptile thermostats, and misting systems sent to Splunk HEC via controller APIs, MQTT, and scripted inputs.",
        "ds": "Apex controller readings (`apex:reading`), Seneye measurements (`seneye:reading`), reptile thermostat events (`reptilethermostat:event`), and misting-system cycles (`mister:cycle`).",
        "refs": R(
            ("Neptune Apex", "https://www.neptunesystems.com/apex/"),
            ("Seneye", "https://seneye.com/"),
            ("Herpstat", "https://spyderrobotics.com/index.php?main_page=index&cPath=1"),
            ("MistKing", "https://mistking.com/"),
        ),
    },
    "28": {
        "app": "Training telemetry from Whoop, Garmin power meters, Stryd running power, and gymnastics skill trackers maintained in Sheets or app exports sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Whoop recovery and strain (`whoop:day`), Garmin ride power (`powermeter:ride`), Stryd runs (`stryd:run`), and gymnastics skill attempts (`gymnastics:skill`).",
        "refs": R(
            ("WHOOP", "https://www.whoop.com/"),
            ("Garmin Rally", "https://www.garmin.com/en-US/p/658594"),
            ("Stryd", "https://www.stryd.com/"),
            ("Google Sheets API", "https://developers.google.com/sheets/api"),
        ),
    },
    "29": {
        "app": "Gaming and play telemetry from Steam, Chess.com, Online-Go servers, and poker home-game logs sent to Splunk HEC via APIs and export files.",
        "ds": "Steam activity and achievements (`steam:activity`), Chess.com games (`chesscom:game`), online-go matches (`ogs:game`), and poker home-game hands or settlements (`pokerhome:session`).",
        "refs": R(
            ("Steam Web API", "https://developer.valvesoftware.com/wiki/Steam_Web_API"),
            ("Chess.com Published Data API", "https://www.chess.com/news/view/published-data-api"),
            ("Online-Go Server", "https://online-go.com/"),
            ("PokerNow", "https://www.pokernow.club/"),
        ),
    },
    "30": {
        "app": "Collection telemetry from Discogs, Comic Vine, coin and stamp catalogues, and watch-collection trackers sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Discogs collection entries (`discogs:item`), comics (`comic:item`), coin catalogue entries (`coin:item`), stamp album entries (`stamp:item`), and watch logs (`watch:item`).",
        "refs": R(
            ("Discogs API", "https://www.discogs.com/developers"),
            ("Comic Vine API", "https://comicvine.gamespot.com/api/"),
            ("Numista", "https://en.numista.com/"),
            ("Colnect", "https://colnect.com/"),
            ("Chrono24", "https://www.chrono24.com/"),
        ),
    },
    "31": {
        "app": "Wellbeing journaling telemetry from Daylio exports, CBT thought records, breathwork apps, and therapy homework trackers sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Mood entries (`daylio:entry`), CBT thought records (`cbt:record`), breathwork sessions (`breathwork:session`), and therapy homework items (`therapy:homework`).",
        "refs": R(
            ("Daylio", "https://daylio.net/"),
            ("Psychology Tools thought record", "https://www.psychologytools.com/resource/thought-record/"),
            ("Breathwrk", "https://www.breathwrk.com/"),
            ("SimplePractice", "https://www.simplepractice.com/"),
        ),
    },
    "32": {
        "app": "Relationship and togetherness telemetry from shared calendars, gift budgets, message and call logs, and long-distance touchpoint trackers sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Shared calendar events (`sharedcalendar:event`), gift budget items (`giftbudget:item`), touchpoint logs (`touchpoint:log`), and relationship rituals (`relationship:ritual`).",
        "refs": R(
            ("Google Calendar API", "https://developers.google.com/workspace/calendar/api/guides/overview"),
            ("Splitwise", "https://www.splitwise.com/"),
            ("Agape", "https://loveagape.com/"),
            ("TouchNote", "https://touchnote.com/"),
        ),
    },
    "33": {
        "app": "Habit-boundary telemetry for Dry January, caffeine cutoffs, screen-before-bed limits, and fasting windows sent to Splunk HEC via apps, shortcuts, and scripted inputs.",
        "ds": "Alcohol habit events (`habit:alcohol`), caffeine intake (`habit:caffeine`), screen-time sessions (`habit:screen`), and fasting windows (`habit:fasting`).",
        "refs": R(
            ("Drinkaware", "https://www.drinkaware.co.uk/"),
            ("Apple Screen Time", "https://support.apple.com/guide/iphone/get-started-with-screen-time-iphbfa595995/ios"),
            ("ZERO fasting", "https://www.zerofasting.com/"),
            ("Oura", "https://oura.com/"),
        ),
    },
    "34": {
        "app": "Micro-finance telemetry for latte-factor spending, cashback apps, price tracking, and tip logging sent to Splunk HEC via finance exports and scripted inputs.",
        "ds": "Micro-spend transactions (`microspend:txn`), cashback events (`cashback:event`), price tracker alerts (`pricetrack:alert`), and tip logs (`tiplog:shift`).",
        "refs": R(
            ("Firefly III", "https://www.firefly-iii.org/"),
            ("Rakuten", "https://www.rakuten.com/"),
            ("CamelCamelCamel", "https://camelcamelcamel.com/"),
            ("Google Sheets API", "https://developers.google.com/sheets/api"),
        ),
    },
    "35": {
        "app": "Symptom telemetry for allergy diaries, migraine aura tracking, bathroom frequency logging, and sleep-talking review sent to Splunk HEC via apps and scripted inputs.",
        "ds": "Allergy symptoms (`allergy:entry`), migraine records (`migraine:entry`), bathroom visits (`bathroom:visit`), and sleep-talking events (`sleeptalk:event`).",
        "refs": R(
            ("Bearable", "https://bearable.app/"),
            ("Migraine Buddy", "https://migrainebuddy.com/"),
            ("Cara Care", "https://cara.care/"),
            ("Sleep Cycle", "https://www.sleepcycle.com/"),
        ),
    },
    "36": {
        "app": "Household logistics telemetry from Amazon order history, meal-plan inventory tools, and pharmacy refill portals sent to Splunk HEC via exports and scripted inputs.",
        "ds": "Amazon order records (`amazon:order`), meal-plan inventory (`mealplan:item`), and pharmacy refill events (`pharmacy:refill`).",
        "refs": R(
            ("Amazon", "https://www.amazon.com/"),
            ("Mealie", "https://mealie.io/"),
            ("Paprika", "https://www.paprikaapp.com/"),
            ("CVS Pharmacy", "https://www.cvs.com/"),
        ),
    },
    "37": {
        "app": "Home health telemetry from radon monitors, sump humidity probes, HVAC filter tracking, and roof leak sensors sent to Splunk HEC via MQTT and scripted inputs.",
        "ds": "Radon readings (`radon:reading`), sump humidity events (`sump:humidity`), HVAC filter telemetry (`hvacfilter:reading`), and roof leak events (`roofleak:event`).",
        "refs": R(
            ("Airthings", "https://www.airthings.com/"),
            ("ESPHome", "https://esphome.io/"),
            ("Filtrete", "https://www.filtrete.com/"),
            ("Govee water detectors", "https://us.govee.com/products/govee-water-detectors"),
        ),
    },
    "38": {
        "app": "Personal security telemetry from Have I Been Pwned, password-age exports, backup restore drills, and DNS leak checks sent to Splunk HEC via APIs and scripted inputs.",
        "ds": "Breach alerts (`hibp:alert`), password age snapshots (`passwordage:account`), backup restore tests (`backuprestore:test`), and DNS leak checks (`dnsleak:check`).",
        "refs": R(
            ("Have I Been Pwned API", "https://haveibeenpwned.com/API/v3"),
            ("Bitwarden", "https://bitwarden.com/"),
            ("restic", "https://restic.net/"),
            ("DNS Leak Test", "https://www.dnsleaktest.com/"),
        ),
        "pillar": "Security",
    },
    "39": {
        "app": "Seasonal household telemetry from decoration timers, birthday spending trackers, and fireworks noise sensors sent to Splunk HEC via Home Assistant, budget exports, and scripted inputs.",
        "ds": "Decoration timers (`holidaytimer:event`), birthday spending (`birthday:spend`), and fireworks noise events (`fireworks:noise`).",
        "refs": R(
            ("Home Assistant", "https://www.home-assistant.io/"),
            ("YNAB", "https://www.ynab.com/"),
            ("ESPHome", "https://esphome.io/"),
        ),
    },
    "40": {
        "app": "Meta-monitoring for every `index=personal` stream, turning cross-signal correlations, anomaly-day scoring, and personal SLA dashboards into Splunk-native analytics.",
        "ds": "Cross-stream correlations (`correlation:pair`), anomaly-day rollups (`anomalyday:score`), personal SLA checks (`personalsla:status`), and daily life scores (`lifescore:daily`).",
        "refs": R(
            ("Google SRE book - SLOs", "https://sre.google/sre-book/service-level-objectives/"),
            ("Splunk Observability", "https://docs.splunk.com/observability/"),
            ("Splunk Search Reference", "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual"),
        ),
    },
}

SPECS: dict[str, list[dict[str, object]]] = {
    "21": [
        T("FT8 Spot Volume by Band", "ft8:spot", "FT8 spot volume", "1d", "count as spots, dc(dx_call) as dx_stations", group_fields="band", group_label="band", search="mode=FT8", why="Band-level spot counts show where propagation is really carrying your station."),
        K("FT8 Grid Reach After Sunset", "ft8:spot", "after-dark FT8 spots", "count as spots, dc(dx_call) as dx_stations", "grid", "grid squares", search="mode=FT8 hour_local>=18", why="Evening grid reach is a practical check on when the station is most effective for casual DX."),
        G("JS8Call Heartbeat Silence by Station", "js8call:message", "JS8Call heartbeats", "station_id", "stations", search="msg_type=heartbeat", unit="hours", why="Heartbeat gaps usually mean the app, radio path, or relay script stopped behaving as expected."),
        L("JS8Call Directed Message Turnaround", "js8call:message", "JS8Call directed-message turnaround", "reply_latency_sec", group_fields="peer_call", group_label="peer call", search="msg_type=directed reply_latency_sec=*", why="Turnaround time shows which contacts are flowing naturally and which ones are becoming store-and-forward conversations."),
        T("PSKReporter Heard-Station Diversity by Hour", "pskreporter:spot", "heard-station diversity", "1h", "dc(dx_call) as heard_calls, dc(grid) as heard_grids", group_fields="band", group_label="band", why="Unique-station counts are often a better propagation indicator than raw spot volume."),
        T("PSKReporter Band Opening Duration", "pskreporter:spot", "PSKReporter band opening minutes", "1d", "sum(open_minutes) as open_minutes", group_fields="band", group_label="band", why="Daily opening duration helps show which bands are actually usable instead of merely noisy."),
        P("Direwolf Packet Decode Error Rate", "direwolf:packet", "Direwolf packet decodes", "1d", 'decode_status="ok"', group_fields="tnc_port", group_label="TNC port", why="A decode success percentage catches antenna, audio, or level problems before the APRS map obviously empties out."),
        L("Direwolf APRS Gate Delay by Port", "direwolf:packet", "Direwolf packet-to-gate delay", "gate_delay_sec", group_fields="tnc_port", group_label="TNC port", search="gate_delay_sec=*", why="Packet-to-gate latency helps separate RF trouble from local TNC or relay bottlenecks."),
        T("NOAA APT Pass SNR Trend", "noaaapt:pass", "NOAA APT pass SNR", "1d", "avg(pass_snr_db) as avg_pass_snr_db max(pass_snr_db) as max_pass_snr_db", group_fields="satellite", group_label="satellite", why="SNR trends show whether antenna position, receiver health, or weather are changing decode quality over time."),
        G("NOAA APT Image Decode Gap Days", "noaaapt:pass", "successful NOAA APT image decodes", "satellite", "satellites", search='image_status="decoded"', unit="days", divisor=86400, why="A long gap since the last decoded image usually means a capture or demodulation workflow needs attention."),
        K("PSKReporter Grid Square Repeat Rate", "pskreporter:spot", "repeat receptions", "avg(repeat_hits) as avg_repeat_hits max(repeat_hits) as max_repeat_hits", "grid", "grid squares", search="repeat_hits=*", why="Repeated hits from the same grids can confirm reliable paths versus one-off openings."),
        G("Direwolf KISS Client Disconnect Tracker", "direwolf:packet", "KISS client sessions", "client_name", "clients", search='event="kiss_disconnect"', unit="days", divisor=86400, why="Client disconnect recency helps you spot unattended software that is quietly dropping off the packet path."),
        P("NOAA APT Scheduled Pass Miss Rate", "noaaapt:pass", "scheduled NOAA APT captures", "1w", 'captured="true"', group_fields="satellite", group_label="satellite", why="Missed scheduled passes often reveal rotator, scheduler, or SDR availability issues rather than propagation problems."),
        M("FT8 CQ-to-Answer Ratio", "ft8:spot", "FT8 CQ answer rate by band", [
            '| search mode=FT8',
            '| bin _time span=1d',
            '| stats count(eval(msg_type="CQ")) as cq_calls count(eval(answered="true")) as answered by _time band',
            '| eval answer_pct=if(cq_calls>0,round(100*answered/cq_calls,1),0)',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=AK, why="CQ answer rate is a grounded way to compare how operator timing and band choice affect results."),
        M("JS8Call Inbox Volume by Daypart", "js8call:message", "JS8Call inbox volume by daypart", [
            '| eval daypart=case(hour_local<6,"overnight",hour_local<12,"morning",hour_local<18,"afternoon",true(),"evening")',
            '| stats count as messages dc(peer_call) as peers by daypart',
            '| sort - messages',
        ], why="Daypart patterns make it easier to schedule skeds and know when asynchronous traffic tends to pile up."),
    ],
    "22": [
        P("NINA Sequence Completion Rate", "nina:sequence", "NINA imaging sequences", "1w", 'status="complete"', group_fields="target_name", group_label="target", why="Completion rate shows whether long automation runs are actually landing instead of only starting."),
        K("NINA Meridian Flip Failure Queue", "nina:sequence", "meridian-flip failures", 'count(eval(meridian_flip_status="failed")) as failed_flips count as sequences', "mount_name", "mounts", crit=MED, diff=INT, mtypes=AAN, why="Meridian flip failures can ruin a whole night, so a ranked queue helps you see whether one mount profile is the main offender."),
        L("NINA Autofocus Run Variance", "nina:autofocus", "NINA autofocus run time", "run_sec", group_fields="profile_name", group_label="profile", search="run_sec=*", why="Autofocus latency grows when seeing, focuser health, or configuration quality drifts."),
        P("Ekos Scheduler Missed Imaging Windows", "ekos:scheduler", "Ekos scheduler windows", "1w", 'window_status="captured"', group_fields="target_name", group_label="target", why="Window capture success shows whether the scheduler is taking advantage of the nights you planned for."),
        T("Ekos Device Reconnect Churn", "ekos:device", "Ekos device reconnects", "1d", "count as reconnects", group_fields="device_type", group_label="device type", search='event="reconnect"', crit=MED, diff=INT, mtypes=AR, why="Reconnect churn is a simple signal that USB, power, or driver stability is degrading."),
        K("PHD2 Guiding RMS by Target Altitude", "phd2:guide", "guiding RMS", "avg(total_rms_arcsec) as avg_rms_arcsec max(total_rms_arcsec) as max_rms_arcsec", "target_name altitude_bucket", "target-altitude combinations", search="total_rms_arcsec=*", crit=MED, diff=INT, mtypes=AP, why="Altitude often explains guiding quality, so splitting by target and bucket makes the mechanical limits easier to see."),
        T("PHD2 Star-Lost Burst by Filter", "phd2:guide", "PHD2 star-loss events", "1d", "count as star_lost_events", group_fields="filter_name", group_label="filter", search='event="star_lost"', crit=MED, diff=INT, mtypes=AAN, why="Star-loss bursts often correlate with one filter, poor focus, or cloud bands that would otherwise be blamed on everything else."),
        L("PHD2 Dither Settle Time Drift", "phd2:guide", "PHD2 dither settle time", "settle_sec", group_fields="target_name", group_label="target", span="1d", search='event="dither_settle" settle_sec=*', why="Settle-time drift reveals when mount balance, aggressiveness, or seeing are costing real imaging time."),
        L("Plate Solve Latency by Solver", "platesolve:run", "plate solve time", "solve_sec", group_fields="solver_name", group_label="solver", search="solve_sec=*", why="Solver latency matters during framing changes and recovery workflows, so it helps to know which backend is dragging."),
        P("Plate Solve Failure by Sky Region", "platesolve:run", "plate solves", "1w", 'status="solved"', group_fields="sky_region", group_label="sky region", why="Failure rate by region can expose poor metadata, star-starved fields, or horizon obstructions."),
        K("Plate Solve Sync Offset After Slew", "platesolve:run", "sync offset after slew", "avg(sync_error_arcmin) as avg_sync_error_arcmin max(sync_error_arcmin) as max_sync_error_arcmin", "mount_name", "mounts", search="sync_error_arcmin=*", crit=MED, diff=INT, mtypes=AP, why="Large sync offsets after slews often point to pointing model or driver issues that are easy to ignore until a target is lost."),
        K("Filter Wheel Position Mismatch Alert", "filterwheel:event", "filter-wheel mismatches", 'count(eval(expected_slot!=actual_slot)) as mismatches count as moves', "wheel_name", "filter wheels", crit=HIGH, diff=INT, mtypes=AR, why="Slot mismatches are one of the fastest ways to invalidate an entire capture set, so they deserve a clean leaderboard."),
        T("Filter Wheel Exposure Share by Filter", "filterwheel:event", "exposure time by filter", "1w", "sum(exposure_sec) as exposure_sec", group_fields="filter_name", group_label="filter", search='event="exposure_open" exposure_sec=*', why="Filter share makes it easier to spot whether narrowband or luminance plans are drifting away from what you intended."),
        G("Flat Library Staleness by Filter", "flatlib:frame", "flat-library refreshes", "filter_name", "filters", search="frame_type=flat", unit="days", divisor=86400, why="Stale flats are a common hidden cause of calibration trouble, especially after changing dust motes or optical trains."),
        T("Weather Safety Interruptions per Night", "ekos:scheduler", "weather safety interruptions", "1d", "count as safety_stops", group_fields="reason", group_label="reason", search="safety_stop=true", crit=MED, diff=INT, mtypes=AK, why="Reason-coded safety stops help separate a cautious observatory from one that is frequently losing nights to one flaky sensor or rule."),
    ],
    "23": [
        M("Nanit Night Wake Cluster by Hour", "nanit:sleep", "Nanit night wakes by hour", [
            '| eval hour=tonumber(strftime(_time,"%H"))',
            '| where hour>=19 OR hour<7',
            '| stats count as wakes avg(awake_min) as avg_awake_min by hour',
            '| sort hour',
        ], why="Hour-by-hour wake clustering shows when the nursery routine is most fragile instead of only telling you that sleep was rough."),
        G("Nanit Breathing-Motion Gap Alert", "nanit:sleep", "Nanit breathing-motion captures", "child_name", "children", search="breathing_status=tracked", unit="hours", why="A long gap in tracked breathing-motion events is a simple cue that the sensor, placement, or export workflow needs checking."),
        T("Hatch Routine Start-Time Drift", "hatch:routine", "Hatch routine start time drift", "1w", "avg(start_offset_min) as avg_start_offset_min max(start_offset_min) as max_start_offset_min", group_fields="routine_name", group_label="routine", search="start_offset_min=*", why="Routine drift often predicts bedtime friction before the whole week feels chaotic."),
        P("Hatch White-Noise Coverage by Night", "hatch:routine", "overnight white-noise coverage", "1w", 'coverage_status="complete"', group_fields="child_name", group_label="child", search='routine_type="white_noise"', why="Coverage percentage shows whether the comfort routine is actually lasting through the night or cutting out early."),
        M("School Calendar Early-Start Readiness", "schoolcalendar:event", "early-start school mornings", [
            '| search event_type=school_day early_start=true',
            '| stats count as early_days avg(ready_buffer_min) as avg_ready_buffer_min by child_name',
            '| sort avg_ready_buffer_min',
        ], crit=MED, diff=INT, mtypes=AO, why="Early-start readiness helps you see which mornings need more prep the night before."),
        K("School Calendar Double-Booking for Caregivers", "schoolcalendar:event", "caregiver double-bookings", 'count(eval(conflict="true")) as conflicts dc(event_id) as events', "caregiver_name", "caregivers", crit=MED, diff=INT, mtypes=AK, why="Calendar conflict counts highlight where the family handoff plan is too brittle."),
        L("Allowance App Chore-to-Payout Latency", "allowance:txn", "chore payout latency", "payout_delay_hr", group_fields="child_name", group_label="child", search='event_type="chore_payout" payout_delay_hr=*', why="Slow payout erodes trust in the system, so a simple latency view helps keep the reward loop credible."),
        T("Allowance Spend Rate After Payday", "allowance:txn", "allowance spending after payday", "1w", "sum(amount) as spend count as txns", group_fields="child_name", group_label="child", search='event_type="spend"', crit=LOW, diff=BEG, mtypes=AC, why="Post-payday spend velocity helps you coach pacing instead of only discovering an empty balance later."),
        T("Screen Time Overage by App Category", "screentime:usage", "screen-time overages", "1d", "sum(over_limit_min) as over_limit_min", group_fields="app_category", group_label="app category", search="over_limit_min>0", crit=MED, diff=BEG, mtypes=AK, why="Category-level overages show whether the problem is games, video, or everything equally."),
        P("Screen-Free Bedtime Compliance for Kids", "screentime:usage", "screen-free bedtime windows", "1w", 'screen_free_ok="true"', group_fields="child_name", group_label="child", search="bedtime_window=true", crit=MED, diff=INT, mtypes=COMP, why="A clear bedtime compliance rate is much more actionable than arguing about individual nights."),
        M("Nanit Sleep Improvement After Hatch Routine", "nanit:sleep", "sleep quality after completed Hatch routines", [
            '| search hatch_completed=* sleep_score=*',
            '| stats avg(sleep_score) as avg_sleep_score avg(total_sleep_min) as avg_sleep_min by hatch_completed',
            '| sort hatch_completed',
        ], crit=MED, diff=INT, mtypes=RES, why="Comparing sleep quality with and without the routine shows whether the effort is earning its place."),
        K("School Absence Recovery Task Backlog", "schoolcalendar:event", "make-up task backlog", "sum(recovery_tasks_open) as open_tasks max(days_since_absence) as max_days_since_absence", "child_name", "children", search='event_type="absence_recovery"', crit=MED, diff=INT, mtypes=AO, why="Absence recovery work compounds fast, so a ranked backlog helps you focus on the child who needs the most support first."),
        K("Allowance Savings-Goal Progress by Child", "allowance:txn", "allowance savings progress", "latest(goal_pct) as goal_pct latest(balance) as balance", "child_name", "children", search="goal_pct=*", crit=LOW, diff=BEG, mtypes=AN, why="Goal progress makes the allowance data useful for coaching patience rather than only logging transactions."),
        M("Screen Time Weekend Blowout Days", "screentime:usage", "weekend screen spikes", [
            '| where match(strftime(_time,"%w"),"0|6")',
            '| bin _time span=1d',
            '| stats sum(minutes) as minutes sum(over_limit_min) as over_limit_min by _time child_name',
            '| sort - over_limit_min',
        ], crit=MED, diff=BEG, mtypes=AAN, why="Weekend blowout days are where guardrails usually fail first, so they are worth surfacing separately from weekdays."),
        P("Bedtime Routine Completion Before School Nights", "hatch:routine", "bedtime routines before school nights", "1w", 'status="complete"', group_fields="child_name", group_label="child", search="school_night=true routine_type=bedtime", crit=MED, diff=INT, mtypes=COMP, why="Completion before school nights is one of the clearest ways to measure whether the evening system is actually holding together."),
    ],
    "24": [
        T("Flow Hive Super Weight Jump Watch", "flowhive:reading", "Flow Hive super-weight change", "1d", "avg(weight_delta_kg) as avg_weight_delta_kg max(weight_delta_kg) as max_weight_delta_kg", group_fields="hive_id", group_label="hive", search="weight_delta_kg=*", crit=MED, diff=INT, mtypes=AAN, why="Weight jumps help you spot nectar surges, harvest windows, or unexpected disturbances without opening the hive."),
        K("Flow Hive Harvest Readiness Window", "flowhive:reading", "harvest readiness", "latest(capped_frame_pct) as capped_frame_pct latest(weight_kg) as weight_kg", "hive_id", "hives", search="capped_frame_pct=*", crit=MED, diff=INT, mtypes=AO, why="Capped-frame readiness is a more practical harvest cue than guessing from a single inspection note."),
        M("Chicken Nest-Box Visit vs Egg Count Gap", "eggcounter:event", "nest-box visits versus egg counts", [
            '| stats sum(nest_visits) as nest_visits sum(eggs_counted) as eggs_counted by coop_id',
            '| eval visit_to_egg_gap=nest_visits-eggs_counted',
            '| sort - visit_to_egg_gap',
        ], crit=MED, diff=INT, mtypes=AK, why="A widening visit-to-egg gap often signals false triggers, hidden laying spots, or counter tuning issues."),
        L("Chicken Egg Collection Delay After Lay", "eggcounter:event", "egg collection delay", "collect_delay_min", group_fields="coop_id", group_label="coop", search="collect_delay_min=*", why="Collection delay matters for cleanliness, breakage risk, and whether the morning routine is aligned with when eggs actually arrive."),
        G("Goat RFID Visit Gaps by Animal", "goattag:scan", "goat tag check-ins", "goat_name", "goats", unit="days", divisor=86400, why="A missing tag check-in can be the first sign of a broken reader, fence issue, or animal that is off routine."),
        L("Goat Feed Station Queue Time", "goatcare:event", "goat feed-station waiting time", "queue_sec", group_fields="station_id", group_label="feed station", search='event_type="feed_queue" queue_sec=*', why="Queue time shows whether one station is becoming a bottleneck or bullying hotspot."),
        T("Compost Thermometer Heat-Up After Turn", "compost:reading", "compost heat-up after turning", "1d", "avg(temp_gain_24h_c) as avg_temp_gain_24h_c max(temp_gain_24h_c) as max_temp_gain_24h_c", group_fields="pile_id", group_label="pile", search="temp_gain_24h_c=*", crit=MED, diff=INT, mtypes=RES, why="Heat-up after turning is a practical sign that the pile still has the air and moisture it needs."),
        K("Compost Cool-Core Alert", "compost:reading", "cool-core readings", "latest(core_temp_c) as core_temp_c latest(moisture_pct) as moisture_pct", "pile_id", "piles", search="core_temp_c<40", crit=MED, diff=BEG, mtypes=AK, why="A persistently cool core can point to a dry pile, poor mix, or material that is no longer actively composting."),
        T("Flow Hive Bee Traffic vs Temperature", "flowhive:reading", "hive entrance traffic and temperature", "1d", "avg(bee_traffic_per_min) as avg_bee_traffic_per_min avg(external_temp_c) as avg_external_temp_c", group_fields="hive_id", group_label="hive", search="bee_traffic_per_min=*", why="Traffic alongside temperature helps separate normal weather effects from true colony weakness."),
        P("Egg Counter Sensor Miss Rate", "eggcounter:event", "egg counter detections", "1w", 'verified="true"', group_fields="sensor_id", group_label="sensor", why="Verification rate tells you whether the coop counter is trustworthy enough to automate around."),
        M("Goat Tag Location Drift by Paddock", "goattag:scan", "goat tag location drift by paddock", [
            '| stats dc(paddock_id) as paddocks_seen latest(paddock_id) as latest_paddock by goat_name',
            '| sort - paddocks_seen',
        ], crit=LOW, diff=BEG, mtypes=AN, why="Paddock diversity is a simple way to confirm rotation plans or spot animals escaping their usual pattern."),
        L("Compost Maturity Hold-Time", "compost:reading", "compost maturity hold time", "days_in_cure", group_fields="pile_id", group_label="pile", search='stage="curing" days_in_cure=*', why="Hold time in curing helps you avoid using compost that looks done but has not stabilized long enough."),
        M("Flow Hive Night Weight Loss Alert", "flowhive:reading", "overnight hive weight loss", [
            '| search night_window=true weight_delta_kg=*',
            '| stats avg(weight_delta_kg) as avg_night_delta_kg min(weight_delta_kg) as min_night_delta_kg by hive_id',
            '| sort avg_night_delta_kg',
        ], crit=MED, diff=INT, mtypes=AAN, why="Unexpected overnight weight loss can hint at robbing, leaks, or scale issues that deserve a closer look."),
        T("Chicken Egg Size Trend by Flock", "eggcounter:event", "average egg size", "1w", "avg(egg_weight_g) as avg_egg_weight_g", group_fields="flock_name", group_label="flock", search="egg_weight_g=*", why="Egg-size trend adds quality context to plain count data and can reveal feed or health changes."),
        T("Goat Water Intake Change by Tag", "goatcare:event", "goat water intake", "1d", "sum(water_l) as water_l", group_fields="goat_name", group_label="goat", search='event_type="water" water_l=*', crit=MED, diff=BEG, mtypes=AAN, why="Daily water change is one of the fastest low-effort indicators that an animal's routine has shifted."),
    ],
    "25": [
        T("Oura Daytime Stress Load by Hour", "oura:stress", "Oura daytime stress load", "1h", "avg(stress_score) as avg_stress_score max(stress_score) as max_stress_score", group_fields="hour_bucket", group_label="hour bucket", search="stress_score=*", crit=MED, diff=BEG, mtypes=AK, why="Hour-level stress patterns help pinpoint when work, commuting, or recovery habits are driving the load."),
        M("Oura Resilience Recovery Gap After Hard Days", "oura:stress", "recovery gap after high-stress days", [
            '| sort 0 _time',
            '| eval hard_day=if(stress_score>=80,1,0), recovered=if(recovery_score>=70,1,0)',
            '| streamstats current=f last(eval(if(hard_day=1,_time,null()))) as last_hard_day',
            '| where recovered=1 AND isnotnull(last_hard_day)',
            '| eval recovery_days=round((_time-last_hard_day)/86400,1)',
            '| stats avg(recovery_days) as avg_recovery_days perc90(recovery_days) as p90_recovery_days',
        ], crit=MED, diff=INT, mtypes=RES, why="Recovery lag says more about resilience than a single stressful day ever will."),
        T("CPAP Apnea Event Spike After Late Meals", "cpap:session", "apnea events after late meals", "1d", "avg(apnea_events) as avg_apnea_events", group_fields="late_meal", group_label="late-meal flag", search="apnea_events=*", crit=MED, diff=INT, mtypes=AK, why="Late-meal splits make it easier to see whether a controllable habit is worsening the night."),
        K("CPAP Mask Leak vs Apnea Burden", "cpap:session", "mask leak and apnea burden", "avg(mask_leak_lpm) as avg_mask_leak_lpm avg(apnea_events) as avg_apnea_events", "mask_type", "mask types", crit=MED, diff=INT, mtypes=AP, why="Leak burden often travels with worse therapy quality, and ranking by mask type helps focus troubleshooting."),
        M("Oral Thermometer Fever Clearance Time", "thermometer:reading", "oral-thermometer fever clearance time", [
            '| search illness_id=* temp_c>=37.8',
            '| stats earliest(_time) as fever_start latest(eval(if(temp_c<37.5,_time,null()))) as fever_clear by illness_id',
            '| eval clearance_hours=round((fever_clear-fever_start)/3600,1)',
            '| sort - clearance_hours',
        ], crit=MED, diff=INT, mtypes=RES, why="Clearance time turns scattered thermometer readings into a useful illness recovery measure."),
        M("Oral Temperature Morning-Evening Spread", "thermometer:reading", "morning versus evening oral temperature spread", [
            '| eval daypart=if(tonumber(strftime(_time,"%H"))<12,"morning","evening")',
            '| stats avg(temp_c) as avg_temp_c count as readings by daypart',
            '| eventstats avg(avg_temp_c) as overall',
            '| eval delta_from_overall=round(avg_temp_c-overall,2)',
        ], crit=LOW, diff=BEG, mtypes=AN, why="Comparing morning and evening readings gives a cleaner baseline for spotting real deviations later."),
        K("Body Fat Scale Hydration vs Weight Swing", "bodycomp:reading", "weight swing with hydration context", "avg(weight_delta_kg) as avg_weight_delta_kg avg(hydration_pct) as avg_hydration_pct", "day_of_week", "days of week", crit=LOW, diff=INT, mtypes=AN, why="Hydration context helps keep normal fluid swings from being misread as body-composition changes."),
        T("Body Fat Scale Trend Break After Travel", "bodycomp:reading", "body-composition trend breaks after travel", "1d", "avg(weight_kg) as avg_weight_kg avg(body_fat_pct) as avg_body_fat_pct", group_fields="post_travel", group_label="post-travel flag", search="weight_kg=*", why="Travel often distorts the scale signal, so isolating those days keeps the long trend honest."),
        K("Oura Stress vs HRV Deviation", "oura:stress", "stress and HRV deviation", "avg(stress_score) as avg_stress_score avg(hrv_delta_ms) as avg_hrv_delta_ms", "day_type", "day types", crit=MED, diff=INT, mtypes=RES, why="Stress plus HRV deviation shows whether the body is absorbing load or struggling under it."),
        P("CPAP Therapy Usage Consistency", "cpap:session", "CPAP therapy nights", "1w", 'usage_hours>=4', group_fields="mask_type", group_label="mask type", crit=MED, diff=BEG, mtypes=COMP, why="A 4-hour consistency rate is a practical way to see whether the therapy routine is holding."),
        G("Thermometer Reading Gap During Illness", "thermometer:reading", "illness monitoring readings", "illness_id", "illness episodes", search="illness_id=*", unit="hours", why="During an active illness, long gaps between readings can hide whether things are improving or escalating."),
        G("Body Composition Update Staleness", "bodycomp:reading", "body-composition weigh-ins", "profile_name", "profiles", unit="days", divisor=86400, why="Stale weigh-ins are useful to surface because the trendline becomes noise long before anyone notices."),
        T("Oura Sleep Score vs Next-Day Stress", "oura:stress", "sleep score and next-day stress", "1d", "avg(sleep_score) as avg_sleep_score avg(stress_score) as avg_stress_score", group_fields="weekday", group_label="weekday", crit=MED, diff=INT, mtypes=RES, why="Putting sleep score beside next-day stress helps confirm whether recovery habits are actually paying off."),
        M("Apnea Events by Sleep Position", "cpap:session", "apnea events by sleep position", [
            '| search sleep_position=* apnea_events=*',
            '| stats avg(apnea_events) as avg_apnea_events avg(mask_leak_lpm) as avg_mask_leak_lpm by sleep_position',
            '| sort - avg_apnea_events',
        ], crit=MED, diff=INT, mtypes=AK, why="Position splits can show whether therapy problems are mostly positional instead of purely equipment-driven."),
        M("Resting Temperature vs Oral Thermometer Confirmation", "thermometer:reading", "resting temperature versus oral confirmation", [
            '| search oura_temp_delta_c=* temp_c=*',
            '| stats avg(temp_c) as avg_oral_temp_c avg(oura_temp_delta_c) as avg_oura_temp_delta_c by illness_state',
            '| sort illness_state',
        ], crit=LOW, diff=INT, mtypes=AN, why="Comparing wearable and oral readings shows whether the wearable trend is dependable enough to trust as an early warning."),
    ],
    "26": [
        G("iNaturalist Export Backlog by Project", "inat:observation", "iNaturalist exports", "project_name", "projects", search='export_status="queued"', unit="days", divisor=86400, why="Queued exports piling up means the downstream archive or labeling workflow is falling behind."),
        P("iNaturalist Species ID Agreement Rate", "inat:observation", "iNaturalist identifications", "1w", 'community_agrees="true"', group_fields="taxon_group", group_label="taxon group", why="Community agreement rate is a grounded way to see which observation types need cleaner photos or more review."),
        T("Moth Trap Catch Volume by Night Temperature", "mothtrap:session", "moth trap catch volume", "1d", "sum(catch_count) as catch_count avg(night_temp_c) as avg_night_temp_c", group_fields="trap_id", group_label="trap", why="Catch volume next to night temperature helps separate seasonal ecology from equipment changes."),
        K("Moth Trap New-Species Night Finder", "mothtrap:session", "new-species nights", "sum(new_species_count) as new_species_count sum(catch_count) as catch_count", "trap_id", "traps", search="new_species_count>0", crit=MED, diff=INT, mtypes=AN, why="Ranking new-species nights helps you learn which conditions produce the most interesting catches."),
        T("AudioMoth Bat Passes by Hour", "batdetector:pass", "bat passes", "1h", "count as bat_passes dc(species_guess) as species_guess_count", group_fields="site_name", group_label="site", why="Hour-level bat activity shows when each site actually comes alive after dark."),
        M("Bat Detector Quiet-Night Deviation", "batdetector:pass", "quiet-night deviation for bat passes", [
            '| bin _time span=1d',
            '| stats count as bat_passes by _time site_name',
            '| streamstats window=7 avg(bat_passes) as trailing_avg by site_name',
            '| eval deviation_pct=if(trailing_avg>0,round(100*(bat_passes-trailing_avg)/trailing_avg,1),0)',
            '| sort deviation_pct',
        ], crit=MED, diff=INT, mtypes=AAN, why="Quiet-night deviation helps you notice weather or hardware problems before a whole survey period is lost."),
        K("Trail Cam AI Label Confidence Drift", "trailcam:label", "AI label confidence drift", "avg(confidence) as avg_confidence min(confidence) as min_confidence", "camera_id label", "camera-label pairs", crit=MED, diff=INT, mtypes=AAN, why="Confidence drift is a fast signal that one camera angle or lighting setup is eroding model quality."),
        T("Trail Cam Human Intrusion by Camera", "trailcam:label", "trail-cam human detections", "1d", "count as human_events", group_fields="camera_id", group_label="camera", search='label="person"', crit=MED, diff=BEG, mtypes=AK, why="Human detections often matter operationally as much as wildlife, especially near feeders or nesting areas."),
        L("iNaturalist Research-Grade Conversion Lag", "inat:observation", "research-grade conversion lag", "research_grade_delay_hr", group_fields="taxon_group", group_label="taxon group", search="research_grade_delay_hr=*", why="Conversion lag shows which groups need better evidence or more patient reviewing."),
        G("Moth Trap Photo Processing Backlog", "mothtrap:session", "moth-trap photo processing", "trap_id", "traps", search='processing_status="complete"', unit="days", divisor=86400, why="A long gap since the last processed session means the classification backlog is outrunning the field work."),
        K("AudioMoth Species Diversity by Site", "batdetector:pass", "bat species diversity", "dc(species_guess) as species_count count as bat_passes", "site_name", "sites", why="Species diversity by site helps separate busy but repetitive activity from genuinely rich acoustic locations."),
        P("Trail Cam Empty-Frame Waste Rate", "trailcam:label", "trail-cam frames", "1w", 'label!="empty"', group_fields="camera_id", group_label="camera", why="A usable-frame percentage shows whether one camera is mostly burning storage on wind and shadows."),
        T("iNaturalist Observation Burst After Rain", "inat:observation", "iNaturalist observation bursts after rain", "1d", "count as observations", group_fields="rain_window", group_label="rain window", search="observation_id=*", why="Post-rain bursts help you see whether the best fieldwork windows are matching how you actually go outside."),
        T("Bat Passes After Sunset Offset Through Season", "batdetector:pass", "time from sunset to first bat pass", "1w", "avg(minutes_after_sunset) as avg_minutes_after_sunset", group_fields="month", group_label="month", search="minutes_after_sunset=*", why="Seasonal offset from sunset is a practical timing cue for when the detectors should already be live."),
        K("AI Label Review Queue by Animal Class", "trailcam:label", "manual AI label review queue", 'count(eval(review_status="pending")) as pending_reviews count as labels', "animal_class", "animal classes", crit=MED, diff=BEG, mtypes=AO, why="A class-level review queue helps you spend manual effort where the model is generating the most unresolved work."),
    ],
    "27": [
        T("Apex Temperature Control Overshoot", "apex:reading", "Apex temperature overshoot", "1d", "avg(temp_overshoot_c) as avg_temp_overshoot_c max(temp_overshoot_c) as max_temp_overshoot_c", group_fields="tank_name", group_label="tank", search="temp_overshoot_c=*", crit=MED, diff=INT, mtypes=AAN, why="Overshoot trends show when heaters, chillers, or control tuning are becoming too aggressive."),
        L("Apex Feeding Mode Overrun", "apex:reading", "Apex feeding-mode duration", "feed_mode_sec", group_fields="tank_name", group_label="tank", search='event="feed_mode" feed_mode_sec=*', why="Feed-mode overrun can leave pumps paused too long and quietly destabilize tank conditions."),
        T("Seneye Ammonia Rise Between Checks", "seneye:reading", "Seneye ammonia rise", "1d", "avg(ammonia_delta_ppm) as avg_ammonia_delta_ppm max(ammonia_delta_ppm) as max_ammonia_delta_ppm", group_fields="tank_name", group_label="tank", search="ammonia_delta_ppm=*", crit=HIGH, diff=INT, mtypes=AK, why="Ammonia rise between normal checks is one of the most actionable early warnings in aquatic systems."),
        K("Seneye Light PAR Drift by Tank", "seneye:reading", "PAR drift", "avg(par_delta_pct) as avg_par_delta_pct max(par_delta_pct) as max_par_delta_pct", "tank_name", "tanks", search="par_delta_pct=*", crit=MED, diff=INT, mtypes=AAN, why="PAR drift helps you notice aging bulbs, dirty covers, or programming changes before corals or plants do."),
        T("Reptile Thermostat Hot-Side Stability", "reptilethermostat:event", "hot-side temperature stability", "1d", "avg(hot_side_delta_c) as avg_hot_side_delta_c max(hot_side_delta_c) as max_hot_side_delta_c", group_fields="enclosure_name", group_label="enclosure", search="hot_side_delta_c=*", crit=MED, diff=INT, mtypes=AR, why="Hot-side stability is a core husbandry check, especially for species that depend on a reliable basking gradient."),
        P("Reptile Thermostat Night-Drop Compliance", "reptilethermostat:event", "night-drop windows", "1w", 'night_drop_ok="true"', group_fields="enclosure_name", group_label="enclosure", crit=MED, diff=BEG, mtypes=COMP, why="Night-drop compliance makes it clear whether the enclosure is following the intended circadian profile."),
        G("Misting System Missed Cycle Alert", "mister:cycle", "misting cycles", "zone_name", "zones", search='cycle_status="completed"', unit="hours", why="A missed misting cycle is often the earliest visible failure in a humidity-dependent enclosure."),
        K("Misting Nozzle Runtime Imbalance", "mister:cycle", "misting nozzle runtime", "avg(runtime_sec) as avg_runtime_sec max(runtime_sec) as max_runtime_sec", "zone_name nozzle_id", "zone-nozzle pairs", search="runtime_sec=*", crit=MED, diff=INT, mtypes=AR, why="Runtime imbalance can expose clogs, poor pressure, or zones receiving much more water than intended."),
        T("Apex pH Swing After Dosing", "apex:reading", "pH swing after dosing", "1d", "avg(ph_swing_post_dose) as avg_ph_swing_post_dose max(ph_swing_post_dose) as max_ph_swing_post_dose", group_fields="tank_name", group_label="tank", search="ph_swing_post_dose=*", crit=MED, diff=INT, mtypes=AK, why="Post-dose pH swing helps show whether the dosing schedule is too abrupt for the system volume."),
        L("Seneye Water-Change Recovery Time", "seneye:reading", "water-change recovery time", "recovery_sec", group_fields="tank_name", group_label="tank", search="recovery_sec=*", why="Recovery time after a water change shows how quickly the system settles back into its normal range."),
        T("Reptile Humidity Recovery After Door Open", "reptilethermostat:event", "humidity recovery after door-open events", "1d", "avg(recovery_min) as avg_recovery_min max(recovery_min) as max_recovery_min", group_fields="enclosure_name", group_label="enclosure", search='event="door_open" recovery_min=*', why="Recovery after disturbance is more informative than absolute humidity alone because it tests the enclosure's resilience."),
        K("Misting Reservoir Days-to-Empty", "mister:cycle", "misting reservoir runway", "latest(days_to_empty) as days_to_empty latest(fill_level_pct) as fill_level_pct", "reservoir_name", "reservoirs", search="days_to_empty=*", crit=LOW, diff=BEG, mtypes=AI, why="Days-to-empty is the easiest way to avoid surprise dry reservoirs on busy weeks."),
        K("Thermostat Probe Disagreement by Enclosure", "reptilethermostat:event", "probe disagreement", "avg(probe_delta_c) as avg_probe_delta_c max(probe_delta_c) as max_probe_delta_c", "enclosure_name", "enclosures", search="probe_delta_c=*", crit=HIGH, diff=INT, mtypes=AK, why="Probe disagreement is a strong hint that one sensor placement or device is no longer trustworthy."),
        K("Apex Leak Alarm Repeat Offenders", "apex:reading", "Apex leak alarms", 'count(eval(leak_alarm="true")) as leak_alarms count as samples', "location_name", "locations", crit=HIGH, diff=BEG, mtypes=AK, why="A repeat-offender list for leak alarms helps you fix the cabinet or plumbing spot that keeps flirting with disaster."),
        M("Combined Habitat Safety Score", "apex:reading", "combined habitat safety score", [
            '| search safety_score=*',
            '| bin _time span=1d',
            '| stats avg(safety_score) as avg_safety_score min(safety_score) as min_safety_score by _time tank_name',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=AN, why="A combined safety score gives you one fast daily read without losing the option to drill back into the individual sensors later."),
    ],
    "28": [
        T("Whoop Strain-to-Recovery Mismatch Days", "whoop:day", "Whoop strain-to-recovery mismatch", "1d", "avg(strain_minus_recovery) as avg_strain_minus_recovery max(strain_minus_recovery) as max_strain_minus_recovery", group_fields="training_block", group_label="training block", search="strain_minus_recovery=*", crit=MED, diff=BEG, mtypes=AK, why="Mismatch days show when you are training as if recovered even though the physiology data says otherwise."),
        T("Whoop Sleep Debt Before High Strain", "whoop:day", "sleep debt before high-strain days", "1d", "avg(sleep_debt_min) as avg_sleep_debt_min count as days", group_fields="high_strain_day", group_label="high-strain flag", search="sleep_debt_min=*", crit=MED, diff=BEG, mtypes=RES, why="This split helps reveal whether the hardest days are being stacked on top of poor sleep."),
        T("Garmin Power Meter Left-Right Balance Drift", "powermeter:ride", "left-right balance drift", "1w", "avg(balance_delta_pct) as avg_balance_delta_pct max(balance_delta_pct) as max_balance_delta_pct", group_fields="bike_name", group_label="bike", search="balance_delta_pct=*", crit=MED, diff=INT, mtypes=AAN, why="Balance drift can point to fatigue, fit issues, or sensor zeroing problems before they become obvious elsewhere."),
        T("Garmin Power Meter Sprint Fade by Interval", "powermeter:ride", "sprint fade across intervals", "1w", "avg(power_fade_pct) as avg_power_fade_pct max(power_fade_pct) as max_power_fade_pct", group_fields="workout_name", group_label="workout", search="power_fade_pct=*", crit=MED, diff=INT, mtypes=AP, why="Sprint fade makes it easier to see whether repeatability is improving instead of only looking at your best number."),
        T("Stryd Power Decoupling on Long Runs", "stryd:run", "Stryd power decoupling", "1w", "avg(decoupling_pct) as avg_decoupling_pct max(decoupling_pct) as max_decoupling_pct", group_fields="route_name", group_label="route", search="decoupling_pct=*", crit=MED, diff=INT, mtypes=AP, why="Decoupling turns long-run durability into a trend you can compare across routes and blocks."),
        K("Stryd Form Power Change by Shoe", "stryd:run", "form power", "avg(form_power_w) as avg_form_power_w avg(power_per_kg) as avg_power_per_kg", "shoe_name", "shoes", crit=LOW, diff=INT, mtypes=AN, why="Shoe splits help show whether a change in gear is affecting running economy rather than just pace."),
        T("Gymnastics Skill Attempt Volume by Apparatus", "gymnastics:skill", "gymnastics skill attempts", "1w", "count as attempts", group_fields="apparatus", group_label="apparatus", why="Attempt volume by apparatus shows whether practice time matches the priorities for the current block."),
        P("Gymnastics Skill Hit Rate by Skill Level", "gymnastics:skill", "gymnastics skill attempts", "1w", 'result="hit"', group_fields="skill_level", group_label="skill level", why="Hit rate by level is a good way to check whether progression is moving faster than consistency."),
        T("Whoop HRV Recovery After Travel", "whoop:day", "HRV recovery after travel", "1d", "avg(hrv_delta_ms) as avg_hrv_delta_ms", group_fields="post_travel", group_label="post-travel flag", search="hrv_delta_ms=*", crit=MED, diff=INT, mtypes=RES, why="Travel splits help confirm how much disruption each trip is costing the next training days."),
        K("Garmin Cadence vs Power Efficiency", "powermeter:ride", "cadence and power efficiency", "avg(cadence_rpm) as avg_cadence_rpm avg(power_efficiency_pct) as avg_power_efficiency_pct", "workout_name", "workouts", crit=LOW, diff=INT, mtypes=AN, why="Cadence plus efficiency helps you see which sessions are teaching good power delivery instead of just producing fatigue."),
        T("Stryd Critical Power Trend by Block", "stryd:run", "critical power", "1w", "avg(critical_power_w) as avg_critical_power_w", group_fields="training_block", group_label="training block", search="critical_power_w=*", crit=MED, diff=INT, mtypes=RES, why="Critical power by block is a clean read on whether the training cycle is moving the needle."),
        G("Gymnastics Practice Gap Before Meet Week", "gymnastics:skill", "gymnastics practice logs", "apparatus", "apparatus", search='meet_week="true"', unit="days", divisor=86400, why="A stale apparatus heading into meet week is worth knowing before confidence or routine sharpness drops."),
        M("Whoop Recovery vs Perceived Effort Divergence", "whoop:day", "Whoop recovery versus perceived effort divergence", [
            '| search recovery_score=* rpe=*',
            '| bin _time span=1d',
            '| stats avg(recovery_score) as avg_recovery_score avg(rpe) as avg_rpe by _time',
            '| eval divergence=round(avg_rpe-(avg_recovery_score/10),2)',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=RES, why="Divergence days show when the wearable and the athlete story are disagreeing in a useful way."),
        P("Power Meter Zero-Offset Failure Queue", "powermeter:ride", "power-meter zero-offset checks", "1w", 'zero_offset_ok="true"', group_fields="bike_name", group_label="bike", crit=MED, diff=BEG, mtypes=AR, why="Zero-offset success rate keeps calibration hygiene visible instead of assuming the numbers are always trustworthy."),
        K("Gymnastics Progression Readiness by Prerequisite", "gymnastics:skill", "progression readiness", "avg(readiness_pct) as readiness_pct count as tracked_skills", "prerequisite_skill", "prerequisite skills", crit=LOW, diff=INT, mtypes=AO, why="Prerequisite-based readiness helps coaches and athletes know what must be stable before the next skill jump makes sense."),
    ],
    "29": [
        K("Steam Achievement Completion by Franchise", "steam:activity", "achievement completion", "avg(achievement_pct) as achievement_pct sum(playtime_min) as playtime_min", "franchise", "franchises", search="achievement_pct=*", crit=LOW, diff=BEG, mtypes=AN, why="Franchise completion helps show where you are actually finishing games instead of just sampling them."),
        G("Steam Backlog Age for Installed Games", "steam:activity", "played installed games", "game_name", "games", search='installed="true" last_played=*', unit="days", divisor=86400, why="Backlog age for installed games surfaces the titles using storage and attention without ever getting a real session."),
        T("Chess.com Blunder Cluster by Time Control", "chesscom:game", "Chess.com blunders", "1w", "sum(blunders) as blunders avg(accuracy_pct) as avg_accuracy_pct", group_fields="time_control", group_label="time control", search="blunders=*", crit=MED, diff=BEG, mtypes=AK, why="Time-control splits are one of the cleanest ways to see whether the mistakes are really about speed pressure."),
        M("Chess.com Puzzle Streak Recovery Time", "chesscom:game", "puzzle streak recovery time", [
            '| search puzzle_mode=true streak_reset=true recovery_days=*',
            '| stats avg(recovery_days) as avg_recovery_days perc90(recovery_days) as p90_recovery_days by player_name',
            '| sort - avg_recovery_days',
        ], crit=LOW, diff=INT, mtypes=RES, why="Recovery time after a reset says more about practice resilience than the peak streak alone."),
        T("OGS Joseki Loss by Opening", "ogs:game", "OGS opening losses", "1w", "count as games avg(loss_flag) as loss_rate", group_fields="opening_name", group_label="opening", search="opening_name=*", crit=MED, diff=INT, mtypes=AK, why="Opening-level loss rate helps you decide whether one joseki choice is creating recurring trouble."),
        T("OGS Timeout Risk by Hour", "ogs:game", "OGS timeout risk", "1h", "avg(timeout_flag) as timeout_rate count as games", group_fields="hour_bucket", group_label="hour", search="timeout_flag=*", crit=MED, diff=BEG, mtypes=AK, why="Timeout rate by hour is a practical scheduling signal for correspondence or live games."),
        K("Poker Home Game Buy-In vs Net Result", "pokerhome:session", "home-game net results", "avg(buyin_amount) as avg_buyin_amount sum(net_result) as net_result", "player_name", "players", search="net_result=*", crit=LOW, diff=BEG, mtypes=AC, why="Buy-in and net-result splits show whether one format or one player pool is changing the economics of the night."),
        T("Poker Home Game Rebuy Pressure Nights", "pokerhome:session", "rebuy-heavy poker nights", "1w", "sum(rebuy_count) as rebuys avg(net_result) as avg_net_result", group_fields="venue_name", group_label="venue", search="rebuy_count=*", crit=MED, diff=INT, mtypes=AK, why="Rebuy pressure helps distinguish a wild loose night from a more controlled social game."),
        T("Steam Session Length vs Achievement Yield", "steam:activity", "achievement yield per Steam session", "1w", "avg(session_min) as avg_session_min avg(achievements_unlocked) as avg_achievements_unlocked", group_fields="game_name", group_label="game", search="session_min=* achievements_unlocked=*", crit=LOW, diff=INT, mtypes=AN, why="Session length next to unlock yield makes it easier to see which games reward focused sessions versus endless grind."),
        T("Chess.com Accuracy Drift After Midnight", "chesscom:game", "post-midnight chess accuracy", "1w", "avg(accuracy_pct) as avg_accuracy_pct count as games", group_fields="after_midnight", group_label="after-midnight flag", search="accuracy_pct=*", crit=MED, diff=BEG, mtypes=AAN, why="A late-night split often reveals when fatigue is turning games into training data for bad habits."),
        K("OGS Resignation Rate by Rank Gap", "ogs:game", "resignation rate", "avg(resigned_flag) as resignation_rate count as games", "rank_gap_bucket", "rank-gap buckets", crit=LOW, diff=INT, mtypes=AN, why="Rank-gap resignation rate shows where confidence or patience breaks first."),
        P("Poker Player Attendance Reliability", "pokerhome:session", "home-game attendance RSVPs", "1w", 'attended="true"', group_fields="player_name", group_label="player", crit=LOW, diff=BEG, mtypes=AR, why="Attendance reliability keeps your invite list grounded in who actually shows up."),
        T("Steam Wishlist-to-Play Conversion", "steam:activity", "wishlist conversion to play", "1w", 'count(eval(wishlist_state="wishlisted")) as wishlisted count(eval(first_played="true")) as played_from_wishlist', group_fields="genre", group_label="genre", search="genre=*", crit=LOW, diff=INT, mtypes=AN, why="Wishlist conversion shows whether sales watching is turning into real play or just expanding the backlog."),
        M("Cross-Game Tilt Spillover After Losses", "chesscom:game", "tilt spillover into later sessions", [
            '| search next_session_game=* tilt_score=*',
            '| stats avg(tilt_score) as avg_tilt_score count as sessions by next_session_game',
            '| sort - avg_tilt_score',
        ], crit=MED, diff=INT, mtypes=AK, why="Spillover after losses helps show whether frustration is staying inside one game or contaminating the next one too."),
        G("Home Game Balance Settlement Aging", "pokerhome:session", "settled poker balances", "player_name", "players", search='settlement_status="complete"', unit="days", divisor=86400, why="Settlement aging keeps a fun home game from quietly accumulating awkward unpaid balances."),
    ],
    "30": [
        K("Discogs Median Price Gap to Paid Cost", "discogs:item", "Discogs market gap versus paid cost", "avg(median_price-paid_price) as avg_gap sum(median_price-paid_price) as total_gap", "collection_name", "collections", search="median_price=* paid_price=*", crit=LOW, diff=INT, mtypes=AC, why="The market gap tells you whether the collection is being built below, above, or roughly at the current median."),
        P("Discogs Wantlist to Purchase Conversion", "discogs:item", "Discogs wantlist items", "1w", 'purchased="true"', group_fields="genre", group_label="genre", search="wantlist=true", crit=LOW, diff=BEG, mtypes=AN, why="Wantlist conversion shows whether the saved targets are realistically moving into the shelf."),
        K("Comic Vine Series Gap by Publisher", "comic:item", "missing comic issues", "sum(missing_issue_count) as missing_issue_count count as tracked_series", "publisher", "publishers", search="missing_issue_count=*", crit=LOW, diff=INT, mtypes=AI, why="Publisher-level gap counts help decide where finishing a run may be easier or more expensive."),
        K("Comic Issue Read Backlog by Arc", "comic:item", "comic read backlog", 'count(eval(read_status!="read")) as unread_issues count as issues', "story_arc", "story arcs", crit=LOW, diff=BEG, mtypes=AI, why="Backlog by arc helps you pick up a story where it actually makes narrative sense instead of chasing issue numbers blindly."),
        K("Numista Country Coverage Progress", "coin:item", "country coverage", "dc(country) as countries count as coins", "era_name", "eras", crit=LOW, diff=INT, mtypes=AN, why="Country coverage shows whether the collection is broadening or just deepening in the same places."),
        K("Coin Duplicate Rate by Denomination", "coin:item", "coin duplicates", 'count(eval(duplicate=true)) as duplicates count as coins', "denomination", "denominations", crit=LOW, diff=BEG, mtypes=AI, why="Duplicate rate helps you spot trade stock versus categories that are simply overrepresented."),
        T("Colnect Stamp Condition Drift", "stamp:item", "stamp condition drift", "1w", "avg(condition_score) as avg_condition_score min(condition_score) as min_condition_score", group_fields="album_name", group_label="album", search="condition_score=*", crit=LOW, diff=INT, mtypes=AAN, why="Condition drift lets you see whether one album or storage method is aging worse than the rest."),
        K("Stamp Album Missing Year Run", "stamp:item", "missing-year runs", "sum(missing_years) as missing_years count as countries", "album_name", "albums", search="missing_years=*", crit=LOW, diff=INT, mtypes=AI, why="Missing-year runs make it easier to choose a completion target that is coherent instead of random."),
        G("Watch Collection Service Interval Aging", "watch:item", "watch service records", "watch_name", "watches", search="service_due_date=*", unit="days", divisor=86400, crit=MED, diff=BEG, mtypes=AV, why="Aging since service matters because the watch that is rarely worn is also easy to forget maintaining."),
        K("Watch Wear Rotation Imbalance", "watch:item", "watch wear imbalance", "avg(wear_share_pct) as wear_share_pct count as wear_events", "brand", "brands", search="wear_share_pct=*", crit=LOW, diff=BEG, mtypes=AN, why="Rotation imbalance helps show whether the collection is giving you variety or just expensive favorites."),
        K("Discogs Seller Defect Rate by Source", "discogs:item", "seller defect rate", 'avg(defect_flag) as defect_rate count as purchases', "seller_name", "sellers", crit=MED, diff=INT, mtypes=AK, why="Seller defect rate quickly shows which source is adding grading surprises or shipping problems."),
        K("Comic Key-Issue Insurance Photo Gaps", "comic:item", "insurance photo gaps", 'count(eval(photo_present=false)) as missing_photos count(eval(key_issue=true)) as key_issues', "storage_box", "storage boxes", crit=MED, diff=BEG, mtypes=AUD, why="Insurance coverage is most important on key issues, so missing photos deserve a direct queue."),
        K("Coin Melt Value vs Catalog Value Spread", "coin:item", "melt versus catalog spread", "avg(catalog_value-melt_value) as avg_value_gap max(catalog_value-melt_value) as max_value_gap", "metal_type", "metal types", search="catalog_value=* melt_value=*", crit=LOW, diff=INT, mtypes=AC, why="The spread helps show whether a category is being held for bullion logic or for numismatic interest."),
        K("Stamp Trade-Out Candidates by Duplicate Count", "stamp:item", "duplicate stamp count", 'count(eval(duplicate=true)) as duplicates count as stamps', "country", "countries", crit=LOW, diff=BEG, mtypes=AI, why="A trade-out list turns duplicate accumulation into a practical next action instead of shelf clutter."),
        K("Watch Value Concentration by Brand", "watch:item", "watch collection value concentration", "sum(insured_value) as insured_value count as watches", "brand", "brands", search="insured_value=*", crit=LOW, diff=INT, mtypes=AC, why="Value concentration shows whether the risk and attention of the collection is dominated by one brand or line."),
    ],
    "31": [
        T("Daylio Mood Drop After Missed Breathwork", "daylio:entry", "mood after missed breathwork", "1d", "avg(mood_score) as avg_mood_score", group_fields="breathwork_done", group_label="breathwork flag", search="mood_score=*", crit=MED, diff=BEG, mtypes=RES, why="Comparing mood with and without breathwork helps show whether the routine is actually protective."),
        G("Daylio Streak Break Before Therapy Week", "daylio:entry", "Daylio entries before therapy weeks", "profile_name", "profiles", search="therapy_week=true", unit="days", divisor=86400, why="A journaling gap right before therapy often means the week you most need context is the week with the least evidence."),
        L("Thought Record Completion Lag After Trigger", "cbt:record", "CBT thought-record completion lag", "completion_delay_min", group_fields="trigger_type", group_label="trigger type", search="completion_delay_min=*", why="Completion lag shows whether the thought-record habit is being used while the event is still fresh enough to help."),
        K("Thought Distortion Hotspots by Type", "cbt:record", "thought distortions", "count as records avg(distress_before) as avg_distress_before", "distortion_type", "distortion types", why="A distortion leaderboard shows which cognitive habits are recurring often enough to deserve focused work."),
        T("Breathwork Session Length by Time of Day", "breathwork:session", "breathwork session length", "1w", "avg(minutes) as avg_minutes count as sessions", group_fields="daypart", group_label="time of day", search="minutes=*", why="Time-of-day splits help you place breathwork where it naturally fits instead of where it sounds ideal."),
        T("Breathwork Rescue-Session Frequency During Stress", "breathwork:session", "rescue breathwork sessions during stress windows", "1w", "count as sessions", group_fields="stress_window", group_label="stress window", search='session_type="rescue"', crit=MED, diff=INT, mtypes=RES, why="Rescue-session frequency shows when coping support is being used exactly where life feels most demanding."),
        P("Therapy Homework Completion Rate", "therapy:homework", "therapy homework assignments", "1w", 'status="complete"', group_fields="theme", group_label="theme", crit=MED, diff=BEG, mtypes=COMP, why="Completion rate shows whether the work between sessions is really happening instead of staying aspirational."),
        G("Therapy Homework Carryover Aging", "therapy:homework", "open therapy homework", "theme", "themes", search='status="open"', unit="days", divisor=86400, crit=MED, diff=BEG, mtypes=AO, why="Aging open homework highlights where one theme is repeatedly getting postponed."),
        T("Daylio Mood Recovery After CBT Thought Record", "daylio:entry", "mood recovery after CBT thought records", "1d", "avg(post_record_mood_delta) as avg_post_record_mood_delta", group_fields="record_completed", group_label="thought-record flag", search="post_record_mood_delta=*", crit=MED, diff=INT, mtypes=RES, why="Mood delta after a completed record is a grounded way to check whether the tool is helping in practice."),
        T("Breathwork vs Sleep Quality Lift", "breathwork:session", "sleep lift after breathwork days", "1w", "avg(next_sleep_score_delta) as avg_next_sleep_score_delta", group_fields="session_done", group_label="breathwork flag", search="next_sleep_score_delta=*", crit=LOW, diff=INT, mtypes=RES, why="Sleep lift after breathwork helps you decide whether the routine belongs in the evening, not just the app."),
        G("Session Note Export Backlog", "therapy:homework", "session note exports", "provider_name", "providers", search='event_type="session_note_export"', unit="days", divisor=86400, crit=LOW, diff=BEG, mtypes=AV, why="An export backlog means useful context is staying trapped in one tool instead of feeding your review habit."),
        L("Trigger-to-Reflection Turnaround", "cbt:record", "trigger-to-reflection turnaround", "turnaround_min", group_fields="trigger_type", group_label="trigger type", search="turnaround_min=*", why="Turnaround from trigger to reflection is a practical measure of how quickly you are catching the pattern."),
        K("Therapy Goal Progress by Theme", "therapy:homework", "therapy goal progress", "avg(progress_pct) as progress_pct count as goals", "theme", "themes", search="progress_pct=*", crit=LOW, diff=INT, mtypes=AN, why="Goal progress by theme keeps broad therapy work from feeling too abstract to measure."),
        G("Check-In Gap Before Low Mood Cluster", "daylio:entry", "mood check-ins before low-mood stretches", "profile_name", "profiles", search="low_mood_cluster=true", unit="hours", why="Missing check-ins before a low-mood cluster is a useful signal that monitoring drops away when it may be needed most."),
        K("Homework Assignment Variety by Month", "therapy:homework", "homework assignment variety", "dc(assignment_type) as assignment_types count as assignments", "month", "months", crit=LOW, diff=BEG, mtypes=AN, why="Assignment variety shows whether the between-session work is broad enough to keep building different skills."),
    ],
    "32": [
        P("Shared Calendar Protected Date-Night Rate", "sharedcalendar:event", "protected date nights", "1w", 'status="kept"', group_fields="month", group_label="month", search='event_type="date_night"', crit=LOW, diff=BEG, mtypes=COMP, why="A protected date-night rate shows whether good intentions are surviving the real calendar."),
        K("Shared Calendar Conflict with Family Events", "sharedcalendar:event", "calendar conflicts", 'count(eval(conflict="true")) as conflicts count as events', "event_type", "event types", crit=MED, diff=INT, mtypes=AK, why="Conflict counts help show which kinds of commitments are crowding out time together the most."),
        T("Gift Budget Burn Rate by Occasion", "giftbudget:item", "gift-budget burn rate", "1w", "sum(spend_amount) as spend_amount avg(budget_remaining) as avg_budget_remaining", group_fields="occasion", group_label="occasion", search="spend_amount=*", crit=LOW, diff=BEG, mtypes=AC, why="Burn rate by occasion is the easiest way to spot a celebration getting expensive too early."),
        K("Gift Budget Overrun by Recipient", "giftbudget:item", "gift-budget overruns", "sum(overrun_amount) as overrun_amount count as items", "recipient_name", "recipients", search="overrun_amount>0", crit=MED, diff=INT, mtypes=AC, why="Recipient-level overruns show where generosity is drifting past the plan and needs a reset."),
        G("Long-Distance Touchpoint Gap by Person", "touchpoint:log", "long-distance touchpoints", "person_name", "people", unit="days", divisor=86400, why="A gap view keeps meaningful contact from becoming something everyone assumes someone else handled."),
        T("Message vs Call Mix Across Time Zones", "touchpoint:log", "message versus call mix", "1w", "count as touchpoints", group_fields="channel", group_label="channel", search="timezone_gap_hr=*", why="Channel mix across time zones shows whether the communication method still fits the distance and schedules involved."),
        T("Shared Calendar Travel Countdown Readiness", "sharedcalendar:event", "travel countdown readiness", "1d", "avg(readiness_pct) as readiness_pct", group_fields="trip_name", group_label="trip", search='event_type="travel" readiness_pct=*', crit=LOW, diff=INT, mtypes=AO, why="A readiness trend for each trip helps separate fun anticipation from last-minute scramble."),
        L("Surprise Planning Lead Time", "giftbudget:item", "surprise planning lead time", "lead_time_days", group_fields="occasion", group_label="occasion", search='surprise="true" lead_time_days=*', crit=LOW, diff=INT, mtypes=AO, why="Lead time helps show whether surprises are being planned calmly or assembled under deadline pressure."),
        T("Missed Anniversary Reminder Near Misses", "sharedcalendar:event", "anniversary near misses", "1w", "count as near_misses", group_fields="reminder_type", group_label="reminder type", search='event_type="anniversary" near_miss=true', crit=MED, diff=INT, mtypes=AK, why="Near misses matter because they show the reminder system barely working before it actually fails."),
        T("Quality-Time Hours by Week Type", "relationship:ritual", "quality-time hours", "1w", "sum(duration_hr) as duration_hr", group_fields="week_type", group_label="week type", search='ritual_type="quality_time" duration_hr=*', crit=LOW, diff=BEG, mtypes=AN, why="Week-type splits help you see whether busier weeks still protect any real togetherness."),
        P("Gift Idea to Purchase Conversion for Visits", "giftbudget:item", "gift ideas for long-distance visits", "1w", 'status="purchased"', group_fields="visit_name", group_label="visit", search='occasion_type="visit"', crit=LOW, diff=INT, mtypes=AN, why="Conversion from idea to purchase shows whether thoughtful intentions are becoming real gestures in time."),
        L("Touchpoint Response Latency by Channel", "touchpoint:log", "touchpoint response latency", "response_delay_hr", group_fields="channel", group_label="channel", search="response_delay_hr=*", why="Latency by channel shows whether one communication method is quietly becoming too slow to feel connecting."),
        T("Shared Photo-or-Note Frequency by Month", "touchpoint:log", "shared notes and photo touchpoints", "1mon", "count as touchpoints", group_fields="touchpoint_type", group_label="touchpoint type", search='touchpoint_type="photo" OR touchpoint_type="note"', why="Lightweight touchpoints often keep closeness alive between bigger conversations, so their frequency matters."),
        K("Budget Left Before Next Birthday Cluster", "giftbudget:item", "budget remaining before birthday clusters", "latest(budget_remaining) as budget_remaining count as recipients", "month", "months", search='occasion_type="birthday"', crit=LOW, diff=BEG, mtypes=AC, why="Birthday clusters are when the gift budget gets tested hardest, so the remaining buffer matters."),
        M("Connection Scorecard Across Rituals", "relationship:ritual", "connection score across relationship rituals", [
            '| bin _time span=1w',
            '| stats avg(connection_score) as avg_connection_score dc(ritual_type) as ritual_variety by _time',
            '| sort - _time',
        ], crit=LOW, diff=INT, mtypes=AN, why="A combined scorecard keeps the relationship dashboard honest without reducing everything to one metric forever."),
    ],
    "33": [
        T("Dry January Slip Pattern by Weekday", "habit:alcohol", "Dry January slips", "1w", "count as slip_events", group_fields="weekday", group_label="weekday", search='challenge="dry_january" event_type="drink"', crit=MED, diff=BEG, mtypes=AK, why="Weekday patterning helps you see whether the challenge is failing from routine stress or social weekends."),
        L("Alcohol-Free Streak Recovery After Social Events", "habit:alcohol", "alcohol-free streak recovery", "recovery_days", group_fields="event_name", group_label="social event", search="recovery_days=*", crit=MED, diff=INT, mtypes=RES, why="Recovery time after a social event shows whether one slip is staying isolated or dragging into a longer slide."),
        T("Caffeine Cutoff Breach by Beverage", "habit:caffeine", "caffeine cutoff breaches", "1w", "count as breaches avg(caffeine_mg) as avg_caffeine_mg", group_fields="beverage_name", group_label="beverage", search="cutoff_breach=true", crit=MED, diff=BEG, mtypes=AK, why="Breach counts by beverage reveal whether the problem is one favorite drink or the whole routine."),
        T("Caffeine Half-Life Risk Before Bedtime", "habit:caffeine", "remaining caffeine at bedtime", "1d", "avg(estimated_active_mg) as avg_active_mg max(estimated_active_mg) as max_active_mg", group_fields="weekday", group_label="weekday", search="estimated_active_mg=*", crit=MED, diff=INT, mtypes=AK, why="Estimated active caffeine at bedtime makes the invisible carryover of a late cup much easier to respect."),
        T("Screen-Before-Bed Overage by App Category", "habit:screen", "screen-before-bed overage", "1d", "sum(overage_min) as overage_min", group_fields="app_category", group_label="app category", search="bed_window=true overage_min>0", crit=MED, diff=BEG, mtypes=AK, why="App-category overage tells you whether the last-hour leak is mainly social, video, or gaming."),
        P("Screen-Free Last-Hour Compliance", "habit:screen", "screen-free last hours", "1w", 'screen_free_ok="true"', group_fields="weekday", group_label="weekday", search="bed_window=true", crit=MED, diff=BEG, mtypes=COMP, why="A weekly compliance rate turns a fuzzy bedtime ambition into a hard habit measure."),
        T("Fasting Window Start-Time Drift", "habit:fasting", "fasting start-time drift", "1w", "avg(start_offset_min) as avg_start_offset_min max(start_offset_min) as max_start_offset_min", group_fields="weekday", group_label="weekday", search="start_offset_min=*", crit=LOW, diff=BEG, mtypes=AN, why="Start-time drift shows whether the eating window has quietly become too negotiable to mean much."),
        P("Fasting Window Completion by Weekday", "habit:fasting", "fasting windows", "1w", 'completed="true"', group_fields="weekday", group_label="weekday", crit=MED, diff=BEG, mtypes=COMP, why="Completion by weekday helps separate schedule-related misses from motivation issues."),
        T("Late Coffee vs Sleep Score Drop", "habit:caffeine", "sleep-score drop after late coffee", "1d", "avg(next_sleep_score_delta) as avg_next_sleep_score_delta", group_fields="late_caffeine", group_label="late-caffeine flag", search="next_sleep_score_delta=*", crit=MED, diff=INT, mtypes=RES, why="Linking late coffee to next-sleep score makes the tradeoff concrete instead of theoretical."),
        T("Alcohol-Free Savings vs Goal", "habit:alcohol", "alcohol-free savings", "1w", "sum(saved_amount) as saved_amount avg(goal_pct) as avg_goal_pct", group_fields="goal_name", group_label="goal", search="saved_amount=*", crit=LOW, diff=BEG, mtypes=AC, why="Savings versus goal gives the cutback effort a reinforcing financial story, not just deprivation."),
        K("Binge-Trigger Map for Cutoff Breaches", "habit:caffeine", "cutoff-breach triggers", "count as breaches avg(caffeine_mg) as avg_caffeine_mg", "trigger_name", "triggers", search="cutoff_breach=true", crit=MED, diff=INT, mtypes=AK, why="A trigger map helps you design around the moments that keep breaking the rule."),
        T("Fasting Breaker Foods by Hour", "habit:fasting", "foods ending a fast", "1w", "count as fast_breaks", group_fields="break_food", group_label="break food", search="break_food=*", crit=LOW, diff=BEG, mtypes=AN, why="Breaker-food counts show whether the fasting window usually ends deliberately or impulsively."),
        T("Bedtime Phone Pickup Burst", "habit:screen", "bedtime phone pickups", "1d", "sum(pickups) as pickups", group_fields="daypart", group_label="daypart", search="bed_window=true pickups=*", crit=MED, diff=BEG, mtypes=AAN, why="Pickup bursts are a strong indicator that the screen habit is mechanical rather than intentional."),
        K("Dry Month Social Venue Risk Ranking", "habit:alcohol", "dry-month venue risk", "count as visit_count avg(drink_event_flag) as drink_rate", "venue_name", "venues", search='challenge="dry_january"', crit=MED, diff=INT, mtypes=AK, why="Venue risk helps you see which social context is most likely to bend the rule."),
        M("Habit Interference Days Across Alcohol Caffeine and Screen", "habit:screen", "multi-habit interference days", [
            '| search alcohol_breach=* caffeine_breach=* screen_breach=*',
            '| bin _time span=1d',
            '| stats max(alcohol_breach) as alcohol_breach max(caffeine_breach) as caffeine_breach max(screen_breach) as screen_breach by _time',
            '| eval interference_count=alcohol_breach+caffeine_breach+screen_breach',
            '| sort - interference_count',
        ], crit=MED, diff=INT, mtypes=AK, why="Seeing the habits collide on the same days explains why some evenings unravel more than others."),
    ],
    "34": [
        T("Latte Factor Weekly Cost Leak", "microspend:txn", "latte-factor spending", "1w", "sum(amount) as spend count as purchases", group_fields="merchant_name", group_label="merchant", search='habit_tag="latte_factor"', crit=LOW, diff=BEG, mtypes=AC, why="Weekly spend on routine small treats is the classic leakage pattern that feels invisible one purchase at a time."),
        L("Cashback Claim Delay by App", "cashback:event", "cashback claim delay", "claim_delay_hr", group_fields="app_name", group_label="app", search="claim_delay_hr=*", crit=LOW, diff=INT, mtypes=AC, why="Claim delay shows which cashback app is creating friction instead of easy savings."),
        K("Cashback Missed Opportunity by Merchant", "cashback:event", "missed cashback opportunities", "sum(missed_amount) as missed_amount count as misses", "merchant_name", "merchants", search="missed_amount>0", crit=MED, diff=INT, mtypes=AC, why="A merchant leaderboard for missed value shows where one reminder or browser tool would pay for itself."),
        P("Price Tracker Target Hit Rate", "pricetrack:alert", "price targets", "1w", 'target_hit="true"', group_fields="store_name", group_label="store", crit=LOW, diff=BEG, mtypes=AN, why="Hit rate tells you whether the target thresholds are realistic or set so low they almost never matter."),
        L("Price Drop Wait-Time Before Purchase", "pricetrack:alert", "wait time from price drop to purchase", "purchase_delay_days", group_fields="category", group_label="category", search="purchase_delay_days=*", crit=LOW, diff=INT, mtypes=AN, why="Wait time reveals whether alerts are helping you buy deliberately or simply giving you more things to watch."),
        G("Tip Logging Missing Shift Days", "tiplog:shift", "tip logging", "job_name", "jobs", search='shift_logged="true"', unit="days", divisor=86400, why="A missing shift day means the cash and tax picture is already getting fuzzier than it should be."),
        T("Tip Variance by Day of Week", "tiplog:shift", "tips by day of week", "1w", "avg(tips_amount) as avg_tips_amount max(tips_amount) as max_tips_amount", group_fields="weekday", group_label="weekday", search="tips_amount=*", crit=LOW, diff=BEG, mtypes=AC, why="Day-of-week variance helps with staffing expectations, cash planning, and whether weekends are truly carrying the month."),
        T("Small Treat Spend vs Budget Buffer", "microspend:txn", "small-treat spend against budget buffer", "1w", "sum(amount) as spend avg(buffer_remaining) as avg_buffer_remaining", group_fields="mood_tag", group_label="mood tag", search='category="treat" amount=*', crit=LOW, diff=INT, mtypes=AC, why="Putting treat spend next to remaining buffer helps show when mood spending is genuinely threatening the plan."),
        K("Subscription-Like Cafe Habit by Location", "microspend:txn", "repeat cafe spend", "count as visits sum(amount) as spend", "merchant_name", "cafes", search='category="coffee_shop"', crit=LOW, diff=BEG, mtypes=AC, why="Visit counts make it obvious when a cafe habit is functioning like a subscription you never meant to sign up for."),
        M("Bulk Buy Savings vs Waste", "microspend:txn", "bulk-buy savings versus waste", [
            '| search bulk_buy=true',
            '| stats sum(estimated_savings) as estimated_savings sum(wasted_amount) as wasted_amount by category',
            '| eval net_bulk_value=estimated_savings-wasted_amount',
            '| sort net_bulk_value',
        ], crit=LOW, diff=INT, mtypes=AC, why="Net bulk value keeps bargain pride honest by pricing the food or stock that expired unused."),
        K("Cashback Payout Concentration by Program", "cashback:event", "cashback payout concentration", "sum(payout_amount) as payout_amount count as payouts", "program_name", "programs", search='event_type="payout"', crit=LOW, diff=BEG, mtypes=AC, why="Payout concentration shows which program is actually worth your attention and which ones are just noise."),
        P("Price Alert Fatigue and Ignore Rate", "pricetrack:alert", "price alerts", "1w", 'action_taken="true"', group_fields="category", group_label="category", crit=LOW, diff=INT, mtypes=AAN, why="An ignore rate helps you prune alerts that are no longer adding value and are just training you to scroll past them."),
        T("Tip Tax Set-Aside Coverage", "tiplog:shift", "tip tax set-aside coverage", "1w", "sum(set_aside_amount) as set_aside_amount sum(recommended_set_aside) as recommended_set_aside", group_fields="job_name", group_label="job", search="recommended_set_aside=*", crit=MED, diff=BEG, mtypes=AC, why="Coverage against a recommended set-aside helps keep cash tips from becoming a tax surprise later."),
        T("Discounted Purchase Regret Rate", "microspend:txn", "regretted discounted purchases", "1w", "count as regretted_buys avg(discount_pct) as avg_discount_pct", group_fields="category", group_label="category", search="discounted=true regretted=true", crit=LOW, diff=INT, mtypes=AK, why="Discounted regret shows whether sales are helping you save or simply accelerating low-value purchases."),
        T("Micro-Luxury Spend by Mood Tag", "microspend:txn", "micro-luxury spending", "1w", "sum(amount) as spend count as purchases", group_fields="mood_tag", group_label="mood tag", search='category="micro_luxury"', crit=LOW, diff=INT, mtypes=AC, why="Mood tags make it easier to see when the tiny luxury habit is comfort, celebration, or avoidance."),
    ],
    "35": [
        T("Allergy Diary Flare by Pollen Day", "allergy:entry", "allergy flares", "1d", "avg(severity_score) as avg_severity_score count as entries", group_fields="pollen_level", group_label="pollen level", search="severity_score=*", crit=MED, diff=BEG, mtypes=AK, why="Pollen-level splits help confirm whether the diary is matching the environment or pointing to indoor triggers instead."),
        L("Antihistamine Relief Lag by Symptom", "allergy:entry", "antihistamine relief lag", "relief_delay_min", group_fields="symptom_type", group_label="symptom type", search="relief_delay_min=*", crit=MED, diff=INT, mtypes=RES, why="Relief lag helps show which symptoms respond well and which may need a different strategy."),
        L("Migraine Aura Lead Time Before Pain", "migraine:entry", "migraine aura lead time", "aura_lead_min", group_fields="trigger_type", group_label="trigger type", search="aura_lead_min=*", crit=MED, diff=INT, mtypes=AK, why="Lead time after aura is one of the most useful practical windows for deciding whether to medicate or change plans."),
        K("Migraine Trigger Recurrence by Trigger", "migraine:entry", "migraine trigger recurrence", "count as episodes avg(pain_score) as avg_pain_score", "trigger_type", "triggers", crit=MED, diff=BEG, mtypes=AK, why="A trigger leaderboard keeps you focused on the few patterns that are truly recurring."),
        T("Bathroom Frequency Overnight Escalation", "bathroom:visit", "overnight bathroom visits", "1w", "count as visits", group_fields="sleep_window", group_label="sleep window", search="overnight=true", crit=MED, diff=BEG, mtypes=AAN, why="Nighttime escalation is often what makes a bathroom pattern feel disruptive instead of merely notable."),
        T("Bathroom Visit Gap After Fluid Cutoff", "bathroom:visit", "bathroom visits after fluid cutoff", "1w", "avg(minutes_since_cutoff) as avg_minutes_since_cutoff count as visits", group_fields="after_cutoff", group_label="after-cutoff flag", search="minutes_since_cutoff=*", crit=LOW, diff=INT, mtypes=AN, why="The gap after a fluid cutoff helps test whether the routine is making any real difference."),
        T("Sleep Talking Episode Cluster by Stress Tag", "sleeptalk:event", "sleep-talking episodes", "1w", "count as episodes avg(duration_sec) as avg_duration_sec", group_fields="stress_tag", group_label="stress tag", search="duration_sec=*", crit=LOW, diff=INT, mtypes=AK, why="Stress tags help turn a quirky log into a clue about what is loading the day before sleep."),
        G("Sleep Talking Recording Coverage Gaps", "sleeptalk:event", "sleep-talking recordings", "device_name", "devices", unit="days", divisor=86400, why="Coverage gaps matter because silence might mean a calm night or simply a dead recorder."),
        P("Allergy-Free Day Streak", "allergy:entry", "symptom-free allergy days", "1w", 'symptom_free="true"', group_fields="trigger_season", group_label="season", crit=LOW, diff=BEG, mtypes=RES, why="Symptom-free streaks make progress visible during seasons that otherwise feel uniformly bad."),
        L("Aura-to-Medication Turnaround", "migraine:entry", "aura-to-medication turnaround", "medication_delay_min", group_fields="medication_name", group_label="medication", search="medication_delay_min=*", crit=MED, diff=INT, mtypes=RES, why="Turnaround from aura to medication is a practical measure of how usable your rescue plan really is."),
        T("Bathroom Urgency Spike After Caffeine", "bathroom:visit", "bathroom urgency after caffeine", "1d", "avg(urgency_score) as avg_urgency_score count as visits", group_fields="post_caffeine_window", group_label="post-caffeine flag", search="urgency_score=*", crit=MED, diff=INT, mtypes=AK, why="A post-caffeine split helps show whether one routine habit is driving a disproportionate share of the disruption."),
        G("Symptom Journal Missing-Day Risk", "allergy:entry", "symptom journaling", "profile_name", "profiles", unit="days", divisor=86400, why="A missing-day view helps catch the point where the journal stops being reliable before you try to learn from it."),
        T("Sleep Talking vs Sleep Quality Drop", "sleeptalk:event", "sleep quality after sleep talking", "1w", "avg(next_sleep_score_delta) as avg_next_sleep_score_delta", group_fields="episode_flag", group_label="episode flag", search="next_sleep_score_delta=*", crit=LOW, diff=INT, mtypes=AN, why="Putting next-day sleep quality beside episode presence shows whether the events are just novel or truly disruptive."),
        L("Migraine Recovery Duration by Trigger", "migraine:entry", "migraine recovery duration", "recovery_hr", group_fields="trigger_type", group_label="trigger type", search="recovery_hr=*", crit=MED, diff=INT, mtypes=RES, why="Recovery duration by trigger helps you plan around the attacks that cost the most time after the pain itself ends."),
        M("Cross-Symptom Flare Days", "allergy:entry", "days where multiple symptom systems flare together", [
            '| search migraine_flag=* bathroom_spike=* sleep_talk_flag=* allergy_flare=*',
            '| bin _time span=1d',
            '| stats max(allergy_flare) as allergy_flare max(migraine_flag) as migraine_flag max(bathroom_spike) as bathroom_spike max(sleep_talk_flag) as sleep_talk_flag by _time',
            '| eval flare_count=allergy_flare+migraine_flag+bathroom_spike+sleep_talk_flag',
            '| sort - flare_count',
        ], crit=MED, diff=INT, mtypes=AK, why="Cross-symptom days are often where a general overload story becomes visible across otherwise separate journals."),
    ],
    "36": [
        T("Amazon Order Burst Before Pantry Stockouts", "amazon:order", "Amazon orders before pantry stockouts", "1w", "count as orders avg(stockout_risk_pct) as avg_stockout_risk_pct", group_fields="category", group_label="category", search="stockout_risk_pct=*", crit=LOW, diff=INT, mtypes=AO, why="Order bursts before stockouts show where buying is happening reactively instead of from a stable household plan."),
        T("Amazon Return Rate by Category", "amazon:order", "Amazon return rate", "1w", "count as orders avg(return_flag) as return_rate", group_fields="category", group_label="category", search="return_flag=*", crit=LOW, diff=BEG, mtypes=AK, why="A category-level return rate highlights where repeat purchases are not matching expectations or sizing reality."),
        P("Meal Plan Ingredient Coverage for the Week", "mealplan:item", "meal-plan ingredient coverage", "1w", 'on_hand="true"', group_fields="week_name", group_label="week", crit=MED, diff=BEG, mtypes=COMP, why="Coverage percentage shows whether the meal plan is genuinely supported by inventory or still mostly aspirational."),
        K("Meal Plan Pantry Duplication Waste", "mealplan:item", "pantry duplication waste", "sum(duplicate_qty) as duplicate_qty sum(duplicate_cost) as duplicate_cost", "ingredient_name", "ingredients", search="duplicate_qty>0", crit=LOW, diff=INT, mtypes=AC, why="Duplicate pantry buys are one of the clearest signs that the inventory system is not steering shopping well enough."),
        G("Pharmacy Refill Lead Time Before Empty", "pharmacy:refill", "pharmacy refills before empty", "med_name", "medications", search='refill_status="submitted"', unit="days", divisor=86400, crit=MED, diff=BEG, mtypes=AK, why="Lead time before empty is a practical safety buffer metric for any recurring medication."),
        L("Refill Pickup Delay by Prescription", "pharmacy:refill", "refill pickup delay", "pickup_delay_hr", group_fields="med_name", group_label="medication", search="pickup_delay_hr=*", crit=MED, diff=INT, mtypes=AO, why="Pickup delay shows whether the refill step is breaking at the pharmacy, the reminder, or the household schedule."),
        P("Subscribe-and-Save Miss Rate", "amazon:order", "Subscribe-and-Save deliveries", "1w", 'delivered_on_time="true"', group_fields="category", group_label="category", search='order_type="subscribe_save"', crit=LOW, diff=INT, mtypes=AR, why="Delivery reliability is what makes Subscribe-and-Save convenient instead of just more invisible reordering."),
        T("Household Staples Reorder Interval Drift", "amazon:order", "staple reorder interval drift", "1w", "avg(reorder_interval_days) as avg_reorder_interval_days", group_fields="item_name", group_label="item", search="reorder_interval_days=*", crit=LOW, diff=INT, mtypes=AN, why="Drifting reorder intervals often reveal either changing usage or inventory practices that no longer match reality."),
        T("Meal Plan Leftover Utilisation by Week", "mealplan:item", "leftover utilisation", "1w", "avg(leftover_use_pct) as avg_leftover_use_pct count as meal_items", group_fields="week_name", group_label="week", search="leftover_use_pct=*", crit=LOW, diff=BEG, mtypes=AN, why="Leftover utilisation is a simple truth-teller for whether the plan is reducing waste or just moving it around."),
        L("Order-to-Consumption Lag for Pantry Goods", "mealplan:item", "order-to-consumption lag", "consume_delay_days", group_fields="category", group_label="category", search="consume_delay_days=*", crit=LOW, diff=INT, mtypes=AI, why="Lag from purchase to use shows which goods are being stocked thoughtfully and which are just sitting."),
        K("Pharmacy Refill Synchronisation Opportunities", "pharmacy:refill", "refill synchronization opportunities", "count as meds avg(next_due_gap_days) as avg_next_due_gap_days", "household_member", "household members", search="next_due_gap_days=*", crit=LOW, diff=INT, mtypes=AO, why="Grouping refill cadence by household member can reveal obvious chances to reduce trips and missed pickups."),
        T("Backorder Impact on Meal Plan Changes", "mealplan:item", "meal-plan changes after backorders", "1w", "count as changed_meals", group_fields="backorder_flag", group_label="backorder flag", search="changed_meals=*", crit=MED, diff=INT, mtypes=AK, why="This split shows whether supply hiccups are materially reshaping the plan or just causing minor substitutions."),
        T("Purchase Price Drift for Repeat Essentials", "amazon:order", "purchase price drift for repeat essentials", "1w", "avg(unit_price) as avg_unit_price", group_fields="item_name", group_label="item", search="repeat_essential=true unit_price=*", crit=LOW, diff=BEG, mtypes=AC, why="Price drift on essentials is where quiet inflation hits the household most reliably."),
        T("Delivery Day Clustering and Missed Home Windows", "amazon:order", "delivery clustering and missed-home windows", "1w", "count as deliveries sum(missed_home_flag) as missed_home_count", group_fields="delivery_day", group_label="delivery day", search="delivery_day=*", crit=LOW, diff=INT, mtypes=AO, why="Clustered deliveries may be efficient on paper but annoying if they repeatedly miss when someone is home."),
        M("Refill Adherence Score", "pharmacy:refill", "pharmacy refill adherence score", [
            '| bin _time span=1w',
            '| stats avg(adherence_score) as avg_adherence_score min(adherence_score) as min_adherence_score by _time household_member',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=AN, why="A simple adherence score gives you a weekly snapshot of whether the refill system is supporting the routine or undermining it."),
    ],
    "37": [
        T("Radon Level Weekend vs Weekday Occupancy", "radon:reading", "radon levels by occupancy type", "1w", "avg(radon_bq_m3) as avg_radon_bq_m3 max(radon_bq_m3) as max_radon_bq_m3", group_fields="day_type", group_label="day type", search="radon_bq_m3=*", crit=MED, diff=BEG, mtypes=AK, why="Weekend versus weekday splits help reveal whether occupancy and ventilation habits are moving the radon baseline."),
        T("Radon Seasonal Drift", "radon:reading", "seasonal radon drift", "1w", "avg(radon_bq_m3) as avg_radon_bq_m3", group_fields="season", group_label="season", search="radon_bq_m3=*", crit=MED, diff=BEG, mtypes=AAN, why="Seasonal drift is often the dominant pattern in radon data and sets the context for every alert threshold."),
        T("Sump Pit Humidity Rise Before Pump Cycles", "sump:humidity", "sump humidity rise before pump cycles", "1d", "avg(pre_pump_humidity_rise_pct) as avg_pre_pump_humidity_rise_pct max(pre_pump_humidity_rise_pct) as max_pre_pump_humidity_rise_pct", group_fields="pit_name", group_label="pit", search="pre_pump_humidity_rise_pct=*", crit=MED, diff=INT, mtypes=AK, why="Humidity rise before pump cycles can give you more warning than waiting for standing water or alarms."),
        G("Sump Humidity Sensor Silence Alert", "sump:humidity", "sump humidity updates", "sensor_name", "sensors", unit="hours", why="A silent moisture sensor is dangerous because it removes the only early signal you expected to have."),
        K("HVAC Filter Runtime to Pressure Drop", "hvacfilter:reading", "HVAC filter pressure drop", "avg(pressure_drop_pa) as avg_pressure_drop_pa latest(runtime_hours) as runtime_hours", "filter_id", "filters", search="pressure_drop_pa=* runtime_hours=*", crit=MED, diff=INT, mtypes=AR, why="Pressure drop against runtime is the clearest way to know whether a filter is genuinely loading up."),
        T("Filter Change Effect on Airflow Recovery", "hvacfilter:reading", "airflow recovery after filter changes", "1w", "avg(airflow_delta_pct) as avg_airflow_delta_pct", group_fields="change_window", group_label="change window", search="airflow_delta_pct=*", crit=LOW, diff=INT, mtypes=RES, why="Airflow recovery shows whether changing the filter materially improved the system or merely satisfied the calendar."),
        K("Roof Leak Sensor Repeat Damp Spots", "roofleak:event", "roof leak damp spots", 'count(eval(wet=true)) as wet_events count as samples', "location_name", "locations", crit=HIGH, diff=BEG, mtypes=AK, why="A repeat location list helps you focus inspection and repair effort on the spots proving they are not one-off events."),
        L("Roof Leak Dry-Out Duration After Rain", "roofleak:event", "roof leak dry-out duration", "dryout_hr", group_fields="location_name", group_label="location", search="dryout_hr=*", crit=MED, diff=INT, mtypes=RES, why="Dry-out duration helps tell the difference between a splash event and a place that stays wet too long."),
        T("Radon Spike After Basement Vent Changes", "radon:reading", "radon after basement vent changes", "1d", "avg(radon_bq_m3) as avg_radon_bq_m3", group_fields="vent_change_window", group_label="vent-change flag", search="vent_change_window=*", crit=MED, diff=INT, mtypes=AK, why="Post-change spikes show whether the ventilation adjustment helped, hurt, or simply changed the daily pattern."),
        T("Sump Humidity vs Rainfall Correlation", "sump:humidity", "sump humidity during rainfall windows", "1d", "avg(relative_humidity_pct) as avg_relative_humidity_pct avg(rain_mm) as avg_rain_mm", group_fields="rain_window", group_label="rain window", search="rain_mm=*", crit=MED, diff=INT, mtypes=AN, why="Rain-window splits help confirm whether the moisture problem is really weather-driven or more constant."),
        K("Filter Inventory Days Remaining", "hvacfilter:reading", "filter inventory runway", "latest(days_of_spares_remaining) as days_of_spares_remaining latest(spares_count) as spares_count", "filter_type", "filter types", search="days_of_spares_remaining=*", crit=LOW, diff=BEG, mtypes=AI, why="Days remaining on spare filters keeps maintenance from being blocked by an avoidable stockout."),
        G("Leak Sensor Battery Replacement Aging", "roofleak:event", "leak-sensor battery replacements", "sensor_name", "sensors", search='event="battery_change"', unit="days", divisor=86400, crit=LOW, diff=BEG, mtypes=AR, why="Battery aging matters because a dead leak sensor usually fails silently until the worst possible moment."),
        M("Combined Basement Moisture Risk Index", "sump:humidity", "combined basement moisture risk", [
            '| search moisture_risk_index=*',
            '| bin _time span=1d',
            '| stats avg(moisture_risk_index) as avg_moisture_risk_index max(moisture_risk_index) as max_moisture_risk_index by _time zone_name',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=AN, why="A combined risk index is useful when several mediocre warning signs together tell a clearer story than any one sensor does alone."),
        T("Air Handler Runtime Before Filter Threshold", "hvacfilter:reading", "air handler runtime before filter threshold", "1w", "avg(runtime_to_threshold_hr) as avg_runtime_to_threshold_hr", group_fields="unit_name", group_label="unit", search="runtime_to_threshold_hr=*", crit=LOW, diff=INT, mtypes=AN, why="Runtime to threshold shows whether one unit is consuming filters at an unexpectedly fast pace."),
        K("Storm-Day Leak Escalation Queue", "roofleak:event", "storm-day leak escalation", "sum(wet_events) as wet_events max(severity_score) as max_severity_score", "location_name", "locations", search="storm_day=true", crit=HIGH, diff=INT, mtypes=AK, why="Storm-day escalation helps you identify the roof area most likely to demand immediate work during the next bad weather event."),
    ],
    "38": [
        T("HIBP Breach Count Change by Identity", "hibp:alert", "breach count change", "1w", "max(total_breaches) as total_breaches min(total_breaches) as earliest_breaches", group_fields="identity_name", group_label="identity", crit=MED, diff=BEG, mtypes=AK, why="Change in breach count by identity shows whether one alias is accumulating far more exposure than the others."),
        K("Password Rotation Age Over Target", "passwordage:account", "password age over target", "avg(days_since_rotation) as avg_days_since_rotation max(days_since_rotation) as max_days_since_rotation", "account_category", "account categories", search="days_since_rotation=*", crit=MED, diff=BEG, mtypes=AK, why="Age over target keeps the riskiest stale-password categories visible instead of treating every account equally."),
        K("Stale Passwords on Critical Accounts", "passwordage:account", "stale critical passwords", 'count(eval(days_since_rotation>rotation_target_days)) as stale_passwords count as accounts', "criticality", "criticality tiers", crit=HIGH, diff=BEG, mtypes=AK, why="Critical accounts with stale passwords deserve a queue of their own because the blast radius is different."),
        P("Backup Test Restore Success Rate", "backuprestore:test", "backup test restores", "1w", 'status="success"', group_fields="backup_set", group_label="backup set", crit=HIGH, diff=INT, mtypes=COMP, why="Restore success rate is more important than backup-job success because it proves the data can come back."),
        L("Restore Duration by Backup Set", "backuprestore:test", "backup restore duration", "restore_sec", group_fields="backup_set", group_label="backup set", search="restore_sec=*", crit=MED, diff=INT, mtypes=AP, why="Restore duration matters because a backup that works too slowly may still fail the real-world need."),
        K("Restore Integrity Failure Queue", "backuprestore:test", "restore integrity failures", 'count(eval(integrity_ok="false")) as failures count as tests', "backup_set", "backup sets", crit=HIGH, diff=INT, mtypes=AK, why="Integrity failures deserve a clean queue because they turn a comforting green backup badge into false confidence."),
        K("DNS Leak Endpoint Diversity by Network", "dnsleak:check", "DNS leak endpoint diversity", "dc(resolver_ip) as resolver_count count as checks", "network_name", "networks", crit=MED, diff=BEG, mtypes=AK, why="Unexpected resolver diversity can show that one network is ignoring VPN assumptions or switching paths unpredictably."),
        T("DNS Resolver Drift After VPN Connect", "dnsleak:check", "DNS resolver drift after VPN connection", "1d", "count as checks dc(resolver_ip) as resolver_count", group_fields="vpn_connected", group_label="VPN flag", search="resolver_ip=*", crit=MED, diff=INT, mtypes=AAN, why="Comparing resolver drift with and without VPN gives a direct read on whether the tunnel is doing what you think it is."),
        L("HIBP Alert-to-Password-Change Latency", "hibp:alert", "time from breach alert to password change", "remediation_hr", group_fields="identity_name", group_label="identity", search="remediation_hr=*", crit=MED, diff=INT, mtypes=RES, why="Response latency matters because the risk window after a breach alert is where the value of monitoring is proven."),
        G("Backup Freshness vs Restore Confidence", "backuprestore:test", "successful backup restore tests", "backup_set", "backup sets", search='status="success" integrity_ok="true"', unit="days", divisor=86400, crit=MED, diff=BEG, mtypes=AV, why="Days since the last clean restore is the simplest way to keep backup confidence from becoming stale theater."),
        K("Password Age Concentration by Category", "passwordage:account", "password age concentration", "avg(days_since_rotation) as avg_days_since_rotation sum(days_since_rotation) as total_age_days", "account_category", "account categories", crit=LOW, diff=INT, mtypes=AN, why="Age concentration by category helps you choose one cleanup campaign that will actually retire a meaningful slice of risk."),
        K("DNS Leak Exposure by Device", "dnsleak:check", "DNS leak exposure", 'count(eval(leak_detected="true")) as leak_checks count as checks', "device_name", "devices", crit=MED, diff=BEG, mtypes=AK, why="Device-level leak exposure helps separate one misconfigured laptop or phone from a whole-network issue."),
        K("Failed Restore Repeat Offenders", "backuprestore:test", "failed restore repetitions", 'count(eval(status!="success")) as failed_restores count as tests', "backup_set", "backup sets", crit=HIGH, diff=INT, mtypes=AK, why="Repeat offenders show where to spend backup engineering time first instead of chasing isolated failures."),
        K("Breached Alias with Old Password Risk", "hibp:alert", "breached aliases still tied to old passwords", "count as breach_alerts avg(password_age_days) as avg_password_age_days", "identity_name", "identities", search="password_age_days=*", crit=HIGH, diff=INT, mtypes=AK, why="Combining breach exposure with old-password age creates a much more realistic personal risk queue."),
        M("Personal Security Hygiene Scorecard", "passwordage:account", "personal security hygiene score", [
            '| bin _time span=1w',
            '| stats avg(hygiene_score) as avg_hygiene_score min(hygiene_score) as min_hygiene_score by _time profile_name',
            '| sort - _time',
        ], crit=MED, diff=INT, mtypes=AN, why="A weekly hygiene score gives you one top-line trend while still letting each component stay auditable underneath."),
    ],
    "39": [
        T("Decoration Timer Overrun After Midnight", "holidaytimer:event", "decoration timer overruns", "1d", "sum(overrun_min) as overrun_min count as events", group_fields="zone_name", group_label="zone", search="overrun_min>0", crit=LOW, diff=BEG, mtypes=AC, why="After-midnight overrun is the easiest way to spot holiday automation quietly wasting energy."),
        T("Decoration Power Use by Holiday Zone", "holidaytimer:event", "decoration power use", "1w", "sum(kwh) as kwh", group_fields="zone_name", group_label="zone", search="kwh=*", crit=LOW, diff=BEG, mtypes=AC, why="Zone-level power use helps you decide which display is worth the visual payoff."),
        T("Birthday Spend Burn Rate by Month", "birthday:spend", "birthday spending", "1mon", "sum(amount) as spend count as purchases", group_fields="month", group_label="month", search="amount=*", crit=LOW, diff=BEG, mtypes=AC, why="Monthly burn rate shows whether birthday generosity is smooth or bunching into financially awkward stretches."),
        L("Birthday Gift Prep Lead Time", "birthday:spend", "birthday gift prep lead time", "lead_time_days", group_fields="recipient_group", group_label="recipient group", search="lead_time_days=*", crit=LOW, diff=INT, mtypes=AO, why="Lead time reveals whether gifts are being planned thoughtfully or rescued at the last second."),
        T("Fireworks Noise Peak by Hour", "fireworks:noise", "fireworks noise peaks", "1h", "max(db_peak) as db_peak avg(db_avg) as db_avg", group_fields="zone_name", group_label="zone", search="db_peak=*", crit=MED, diff=BEG, mtypes=AK, why="Peak noise by hour shows when the disruption window really sits instead of relying on memory or annoyance."),
        T("Fireworks Quiet-Down Time by Neighborhood", "fireworks:noise", "time fireworks settle down", "1d", "avg(last_noise_hour) as avg_last_noise_hour max(last_noise_hour) as max_last_noise_hour", group_fields="zone_name", group_label="neighborhood", search="last_noise_hour=*", crit=MED, diff=INT, mtypes=AK, why="Quiet-down time helps set realistic expectations for pets, children, and sleep planning."),
        T("Timer Schedule Drift After Manual Overrides", "holidaytimer:event", "timer schedule drift after manual overrides", "1w", "avg(schedule_drift_min) as avg_schedule_drift_min max(schedule_drift_min) as max_schedule_drift_min", group_fields="zone_name", group_label="zone", search='event_type="manual_override" schedule_drift_min=*', crit=LOW, diff=INT, mtypes=AAN, why="Override drift shows whether the automation still matches real life or keeps needing human correction."),
        P("Decoration Outage During Prime Hours", "holidaytimer:event", "prime-hour decoration uptime", "1w", 'powered="true"', group_fields="zone_name", group_label="zone", search="prime_hour=true", crit=LOW, diff=INT, mtypes=AR, why="Prime-hour uptime is the moment that matters most if the display is meant to be seen and enjoyed."),
        K("Birthday Budget Overrun by Recipient Group", "birthday:spend", "birthday budget overrun", "sum(overrun_amount) as overrun_amount count as recipients", "recipient_group", "recipient groups", search="overrun_amount>0", crit=LOW, diff=INT, mtypes=AC, why="Recipient-group overruns show where generosity is repeatedly outpacing the envelope you intended."),
        T("Noise Sensor Saturation During Major Nights", "fireworks:noise", "noise sensor saturation", "1h", "count as saturated_events", group_fields="sensor_name", group_label="sensor", search="saturated=true", crit=LOW, diff=BEG, mtypes=AR, why="Saturation counts tell you when the sensor itself stopped being able to represent the true intensity of the night."),
        P("Decoration Automation Failure Rate", "holidaytimer:event", "decoration automation runs", "1w", 'status="success"', group_fields="zone_name", group_label="zone", crit=LOW, diff=BEG, mtypes=AR, why="Failure rate keeps the novelty setup maintainable instead of leaving you to rediscover which plug or automation broke."),
        G("Post-Holiday Takedown Lag", "holidaytimer:event", "holiday takedown events", "zone_name", "zones", search='event_type="takedown"', unit="days", divisor=86400, crit=LOW, diff=BEG, mtypes=AO, why="Takedown lag is a gentle reality check on whether seasonal setups are being closed out cleanly."),
        K("Fireworks Complaints vs dBA Threshold", "fireworks:noise", "high-noise complaint risk", "count as noisy_windows avg(complaint_flag) as complaint_rate", "zone_name", "zones", search="db_peak>=85", crit=MED, diff=INT, mtypes=AK, why="Putting complaints beside high-dBA windows shows whether the measured noise is also socially disruptive."),
        P("Seasonal Event Readiness Checklist Completion", "birthday:spend", "seasonal readiness checklist items", "1w", 'completed="true"', group_fields="event_name", group_label="event", search='item_type="checklist"', crit=LOW, diff=BEG, mtypes=COMP, why="Checklist completion rate keeps small celebrations from slipping because of one forgotten setup step."),
        M("Holiday Joy vs Cost Dashboard", "birthday:spend", "holiday joy versus cost", [
            '| search delight_score=* amount=*',
            '| bin _time span=1w',
            '| stats avg(delight_score) as avg_delight_score sum(amount) as spend by _time event_type',
            '| sort - _time',
        ], crit=LOW, diff=INT, mtypes=AC, why="Putting delight beside spend keeps seasonal extras aligned with what people actually value, not just what was purchased."),
    ],
    "40": [
        K("Cross-Stream Correlation Leaderboard", "correlation:pair", "cross-stream correlations", "avg(correlation_score) as avg_correlation_score max(correlation_score) as max_correlation_score", "left_signal right_signal", "signal pairs", crit=MED, diff=INT, mtypes=AN, why="A correlation leaderboard helps you see which signals actually move together instead of assuming connections by intuition."),
        T("Personal Anomaly Day Finder", "anomalyday:score", "personal anomaly-day scores", "1d", "avg(anomaly_score) as avg_anomaly_score max(anomaly_score) as max_anomaly_score", group_fields="domain", group_label="domain", search="anomaly_score=*", crit=MED, diff=INT, mtypes=AAN, why="Day-level anomaly scoring is the cleanest way to find the weird days worth explaining across the whole personal index."),
        T("Personal SLA Breach Count by Signal", "personalsla:status", "personal SLA breaches", "1w", "sum(breach_count) as breach_count", group_fields="signal_name", group_label="signal", search="breach_count=*", crit=MED, diff=BEG, mtypes=COMP, why="Breach count by signal shows which promise to yourself is failing most often."),
        T("Late Data Feed Impact on Daily Score", "lifescore:daily", "daily life score after late feeds", "1d", "avg(life_score) as avg_life_score", group_fields="late_feed_flag", group_label="late-feed flag", search="life_score=*", crit=LOW, diff=INT, mtypes=AN, why="This split helps you see whether score instability comes from life changes or simply data arriving too late."),
        K("Correlated Sleep and Spend Deviation", "correlation:pair", "sleep-and-spend deviation", "avg(correlation_score) as avg_correlation_score avg(delta_strength) as avg_delta_strength", "window_name", "time windows", search='left_signal="sleep" right_signal="spend"', crit=MED, diff=INT, mtypes=AK, why="Sleep versus spend deviation helps test whether bad nights are predictably showing up in financial behavior the next day."),
        K("Health-to-Productivity Tradeoff Days", "anomalyday:score", "health-to-productivity tradeoff days", "count as days avg(tradeoff_score) as avg_tradeoff_score", "tradeoff_type", "tradeoff types", search="tradeoff_score=*", crit=MED, diff=INT, mtypes=AK, why="Tradeoff days are where high output may be borrowing from recovery in a way that is not sustainable."),
        K("Weather-Sensitive Routine Failure Map", "correlation:pair", "weather-sensitive routine failures", "avg(correlation_score) as avg_correlation_score count as windows", "weather_factor routine_name", "weather-routine pairs", search='left_domain="weather"', crit=LOW, diff=INT, mtypes=AN, why="A weather failure map shows which routines genuinely depend on conditions and deserve a fallback plan."),
        P("Weekend Recovery SLA Attainment", "personalsla:status", "weekend recovery SLAs", "1w", 'status="met"', group_fields="sla_name", group_label="SLA", search='sla_domain="recovery" weekend=true', crit=MED, diff=BEG, mtypes=COMP, why="Weekend attainment tells you whether the days meant for recovery are actually doing their job."),
        P("Daily Score Model Input Coverage", "lifescore:daily", "daily score model inputs", "1w", 'input_complete="true"', group_fields="input_domain", group_label="input domain", crit=LOW, diff=BEG, mtypes=AV, why="Input coverage is the fastest way to know whether a daily score is trustworthy before you react to it."),
        K("Best-Day Pattern Reuse Candidates", "lifescore:daily", "best-day pattern reuse", "count as days avg(life_score) as avg_life_score", "pattern_name", "patterns", search="best_day=true", crit=LOW, diff=INT, mtypes=AN, why="Reusable best-day patterns turn a good day from luck into something you can intentionally recreate."),
        K("Worst-Day Contributing Signals", "anomalyday:score", "worst-day contributing signals", "sum(contribution_pct) as contribution_pct count as days", "signal_name", "signals", search="worst_day=true", crit=MED, diff=INT, mtypes=AK, why="A contributing-signal list is the fastest path from a bad day score to a specific hypothesis about why it happened."),
        T("Routine Drift Before Bad Days", "lifescore:daily", "routine drift before bad days", "1d", "avg(routine_drift_pct) as avg_routine_drift_pct", group_fields="bad_day_next", group_label="next-day bad flag", search="routine_drift_pct=*", crit=MED, diff=INT, mtypes=AAN, why="Drift before bad days is where prevention becomes possible instead of just post-mortem analysis."),
        K("Cross-Signal Lag Correlation", "correlation:pair", "cross-signal lag correlation", "avg(lag_hours) as avg_lag_hours avg(correlation_score) as avg_correlation_score", "left_signal right_signal", "signal pairs", search="lag_hours=*", crit=LOW, diff=INT, mtypes=AN, why="Lag correlation matters because cause-and-effect patterns often arrive hours later rather than at the same timestamp."),
        G("Personal Dashboard Freshness Guard", "personalsla:status", "dashboard freshness checks", "dashboard_name", "dashboards", search='freshness_ok="true"', unit="hours", crit=MED, diff=BEG, mtypes=AV, why="A freshness guard keeps the meta-dashboard from telling a stale story about the rest of the system."),
        T("Daily Life Score Stability Trend", "lifescore:daily", "daily life score stability", "1w", "avg(stability_score) as avg_stability_score min(stability_score) as min_stability_score", group_fields="month", group_label="month", search="stability_score=*", crit=LOW, diff=INT, mtypes=RES, why="Stability over time is often a better goal than constant improvement because it captures how reliably the system supports you."),
    ],
}


def emit_specs(writer: Cat25Writer, sub: str, specs: list[dict[str, object]]) -> None:
    defaults = DEFAULTS[sub]
    for spec in specs:
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
            refs=defaults["refs"],
            app=defaults["app"],
            ds=defaults["ds"],
            pillar=str(defaults.get("pillar", "Platform")),
        )


def build() -> int:
    writer = Cat25Writer(append=True)
    for sub in TARGET_SUBS:
        emit_specs(writer, sub, SPECS[sub])
    total, counts = writer.summary()
    expected_total = EXPECTED_PER_SUB * len(TARGET_SUBS)
    assert total == expected_total, f"expected {expected_total} UCs, wrote {total}"
    for sub in TARGET_SUBS:
        assert counts.get(sub, 0) == EXPECTED_PER_SUB, f"subcategory 25.{sub} wrote {counts.get(sub, 0)}"
    return total


def main() -> int:
    total = build()
    print(f"{SCRIPT_PATH}\t{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
