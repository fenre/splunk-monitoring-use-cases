#!/usr/bin/env python3
"""Generate cat-25 depth-wave UCs for subcategories 25.31-25.45."""
from __future__ import annotations

from pathlib import Path

from gen_cat25_common import Cat25Writer, R

SCRIPT_PATH = Path(__file__).resolve()
EXPECTED_PER_SUB = 8
TARGET_SUBS = [str(sub) for sub in range(31, 46)]


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


DEFAULTS: dict[str, dict[str, object]] = {
    "31": {
        "app": (
            "Mood, mindfulness and journaling apps — Daylio / How We Feel mood exports, "
            "Headspace / Insight Timer meditation logs, journaling and gratitude entries — "
            "sent to Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Mood entries (`mood:entry`), meditation sessions (`meditation:session`), "
            "journal entries (`journal:entry`), gratitude logs (`gratitude:log`)."
        ),
        "refs": R(
            ("Daylio — mood diary", "https://daylio.net/"),
            ("Headspace — meditation and mindfulness", "https://www.headspace.com/"),
        ),
    },
    "32": {
        "app": (
            "Relationship and togetherness logs — shared check-in apps, date-night and "
            "gift-idea lists, and stay-in-touch reminders — sent to Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Relationship check-ins (`relationship:checkin`), date nights (`datenight:log`), "
            "gift ideas (`giftidea:item`), keep-in-touch contacts (`keptintouch:contact`)."
        ),
        "refs": R(
            ("Home Assistant — REST integration", "https://www.home-assistant.io/integrations/rest/"),
            ("Gottman Institute — relationships", "https://www.gottman.com/"),
        ),
    },
    "33": {
        "app": (
            "Habit and sobriety trackers, alcohol-unit and hydration logs, vaping/smoking cessation "
            "apps, and a smart swear jar — sent to Splunk HEC via scripted inputs and MQTT."
        ),
        "ds": (
            "Alcohol drinks (`alcohol:drink`), vice logs (`vice:log`), hydration intake "
            "(`hydration:intake`), swear-jar entries (`swearjar:entry`)."
        ),
        "refs": R(
            ("NHS — alcohol units", "https://www.nhs.uk/live-well/alcohol-advice/calculating-alcohol-units/"),
            ("Drinkaware — alcohol advice", "https://www.drinkaware.co.uk/"),
        ),
    },
    "34": {
        "app": (
            "Bank-transaction exports categorised for micro-spending, no-spend-day trackers, "
            "price-per-use logs, and cash-back / rewards feeds — sent to Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Micro-spend transactions (`microspend:txn`), no-spend days (`nospend:day`), "
            "price-per-use items (`priceperuse:item`), cash-back rewards (`cashback:reward`)."
        ),
        "refs": R(
            ("Firefly III — personal finance", "https://www.firefly-iii.org/"),
            ("YNAB — budgeting", "https://www.ynab.com/"),
        ),
    },
    "35": {
        "app": (
            "Everyday body-signal logs — posture sensors, symptom and allergy journals, "
            "hydration-linked bathroom logs, and quirky personal counters — sent to Splunk HEC "
            "via wearables, MQTT, and scripted inputs."
        ),
        "ds": (
            "Posture readings (`posture:reading`), symptom logs (`symptom:log`), "
            "bathroom visits (`bathroom:visit`), sneeze events (`sneeze:event`)."
        ),
        "refs": R(
            ("Upright — posture training", "https://www.uprightpose.com/"),
            ("CDC — symptoms", "https://www.cdc.gov/"),
        ),
    },
    "36": {
        "app": (
            "Household logistics feeds — smart-scale consumable trackers, parcel/delivery "
            "tracking APIs, council bin-collection calendars, and gift-card balance logs — "
            "sent to Splunk HEC via scripted inputs and MQTT."
        ),
        "ds": (
            "Consumable levels (`supply:level`), parcels (`delivery:parcel`), "
            "bin collections (`bincollection:event`), gift-card balances (`giftcard:balance`)."
        ),
        "refs": R(
            ("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/"),
            ("AfterShip — shipment tracking", "https://www.aftership.com/"),
        ),
    },
    "37": {
        "app": (
            "Building-health sensors — indoor humidity / mould-risk monitors, crack and tilt "
            "meters, HVAC filter-life trackers, and damp sensors — streamed to Splunk HEC via "
            "MQTT and ESPHome."
        ),
        "ds": (
            "Mould risk (`mould:risk`), crack meters (`crackmeter:reading`), HVAC filter life "
            "(`hvacfilter:life`), structural tilt (`structural:tilt`)."
        ),
        "refs": R(
            ("ESPHome — DIY sensors", "https://esphome.io/"),
            ("Home Assistant — climate", "https://www.home-assistant.io/integrations/climate/"),
        ),
    },
    "38": {
        "app": (
            "Personal cybersecurity feeds — Have-I-Been-Pwned breach alerts, personal email/inbox "
            "stats, cloud-storage usage APIs, and personal TLS-certificate expiry checks — "
            "sent to Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Breach alerts (`breach:alert`), inbox stats (`inbox:stats`), cloud-drive usage "
            "(`clouddrive:usage`), certificate expiry (`certexpiry:check`)."
        ),
        "refs": R(
            ("Have I Been Pwned — API", "https://haveibeenpwned.com/API/v3"),
            ("NCSC — cyber aware", "https://www.ncsc.gov.uk/cyberaware/home"),
        ),
        "pillar": "Security",
    },
    "39": {
        "app": (
            "Seasonal novelty feeds — smart Christmas-light power meters, a Halloween candy "
            "counter, advent/holiday countdowns, and festive trackers — streamed to Splunk HEC "
            "via MQTT and smart plugs."
        ),
        "ds": (
            "Festive lights (`festive:lights`), candy counter (`candy:counter`), "
            "countdown events (`countdown:event`), Santa tracker (`santa:tracker`)."
        ),
        "refs": R(
            ("Home Assistant — utility meter", "https://www.home-assistant.io/integrations/utility_meter/"),
            ("NORAD Tracks Santa", "https://www.noradsanta.org/"),
        ),
    },
    "40": {
        "app": (
            "The meta layer — correlating every `index=personal` feed (sleep, activity, mood, "
            "weather, spend, productivity, home telemetry) into daily life scores, personal "
            "SLOs, and cross-signal anomaly detection, all computed in Splunk."
        ),
        "ds": (
            "Daily life scores (`lifescore:daily`), personal SLO status (`personalslo:status`), "
            "cross-signal correlations (`correlation:pair`), plus every other `index=personal` "
            "sourcetype as input."
        ),
        "refs": R(
            ("Google — SRE book (SLOs)", "https://sre.google/sre-book/service-level-objectives/"),
            ("Splunk Observability concepts", "https://docs.splunk.com/observability/"),
        ),
    },
    "41": {
        "app": (
            "Micro-mobility and action-sport trackers — e-bike / e-scooter apps (VanMoof, "
            "Bosch eBike Flow), and skate / surf / snow session trackers (Trace, Slopes, Xensr) "
            "with IMU sensors — streamed to Splunk HEC via APIs and scripted inputs."
        ),
        "ds": (
            "E-bike rides (`ebike:ride`), scooter trips (`scooter:trip`), skate sessions "
            "(`skate:session`), surf sessions (`surf:session`), snow runs (`snow:run`)."
        ),
        "refs": R(
            ("Bosch eBike Flow — app", "https://www.bosch-ebike.com/"),
            ("Slopes — ski/snowboard tracking", "https://getslopes.com/"),
        ),
    },
    "42": {
        "app": (
            "Pilot and flight-sim telemetry — electronic logbooks (ForeFlight, LogTen Pro), "
            "Stratux / GDL90 avionics receivers, and Microsoft Flight Simulator / X-Plane "
            "SimConnect sessions — streamed to Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Pilot logbook (`flightlog:entry`), avionics telemetry (`avionics:telemetry`), "
            "flight-sim sessions (`flightsim:session`), pre-flight checklists (`preflight:check`)."
        ),
        "refs": R(
            ("ForeFlight — pilot app", "https://foreflight.com/"),
            ("FAA — Airman Certification", "https://www.faa.gov/pilots/training/airman_education"),
        ),
    },
    "43": {
        "app": (
            "Marine electronics — NMEA 2000 / SignalK boat networks, bilge, battery and "
            "shore-power sensors, anchor-watch GPS, and marine weather feeds — streamed to "
            "Splunk HEC via SignalK and scripted inputs."
        ),
        "ds": (
            "NMEA/SignalK data (`nmea:reading`), bilge pump (`bilge:event`), mooring/anchor watch "
            "(`mooring:status`), marine weather (`marineweather:forecast`)."
        ),
        "refs": R(
            ("SignalK — open marine data", "https://signalk.org/"),
            ("NOAA — marine forecasts", "https://marine.weather.gov/"),
        ),
    },
    "44": {
        "app": (
            "Outdoor logs — fishing apps (Fishbrain), sonar / fishfinder exports, game/trail "
            "cameras, and foraging journals — streamed to Splunk HEC via APIs and scripted inputs."
        ),
        "ds": (
            "Fishing catches (`fishing:catch`), fishfinder sonar (`fishfinder:reading`), "
            "foraging finds (`foraging:find`), game-cam triggers (`gamecam:trigger`)."
        ),
        "refs": R(
            ("Fishbrain — fishing app", "https://fishbrain.com/"),
            ("iNaturalist — species observations", "https://www.inaturalist.org/"),
        ),
    },
    "45": {
        "app": (
            "Music and creator telemetry — practice-tracker apps (Modacity), DAW project logs, "
            "and streaming/creator analytics (Spotify for Artists, YouTube Studio) — streamed "
            "to Splunk HEC via APIs and scripted inputs."
        ),
        "ds": (
            "Practice sessions (`practice:session`), DAW sessions (`daw:session`), release/streaming "
            "stats (`release:stats`), gig setlists (`setlist:play`)."
        ),
        "refs": R(
            ("Modacity — practice app", "https://modacity.co/"),
            ("Spotify for Artists — API", "https://artists.spotify.com/"),
        ),
    },
}


SPECS: dict[str, list[dict[str, object]]] = {
    "31": [
        S(
            "Mood Volatility and Whiplash Days",
            "medium",
            "beginner",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=mood:entry\n"
            "| bin _time span=1d\n"
            "| stats avg(mood_score) as mood by _time\n"
            "| delta mood as day_change\n"
            "| eval swing=if(abs(day_change)>=2,1,0)\n"
            "| sort - _time",
            "Flags days where your mood swung sharply up or down compared with the day before.",
            "Large mood jumps can be just as informative as low moods because they often reveal stressors, recovery patterns, or inconsistent routines.",
            "Ingest daily mood scores into `index=personal`; review daily deltas and alert on unusually large swings.",
            "Line chart of daily mood with markers on high-swing days.",
            "sharp mood swings between days, helping you notice emotional whiplash instead of just the average.",
        ),
        S(
            "Journal Prompt Completion Rate",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=journal:entry prompted=true\n"
            "| bin _time span=1w\n"
            "| stats count as completed, dc(prompt_id) as prompt_variety by _time\n"
            "| sort - _time",
            "Tracks how consistently you complete prompted journal entries instead of skipping reflective moments.",
            "Prompt completion is a simple measure of self-reflection consistency and can show when a journaling habit is quietly fading.",
            "Tag prompted entries in `index=personal`; summarize weekly completion counts and prompt variety.",
            "Weekly column chart of completed prompts with a secondary value for variety.",
            "how often you actually answer your journaling prompts, so a reflective habit does not quietly disappear.",
        ),
        S(
            "Gratitude Streak Break Detector",
            "low",
            "beginner",
            ["Availability"],
            "index=personal sourcetype=gratitude:log\n"
            "| stats latest(_time) as last_gratitude, count as total_entries\n"
            "| eval days_since=round((now()-last_gratitude)/86400,0), at_risk=if(days_since>=2,1,0)",
            "Shows when a gratitude habit has gone quiet for a couple of days and may need a nudge.",
            "Small, positive habits are easy to drop during stressful weeks; detecting the break early is better than restarting from scratch later.",
            "Send gratitude entries to `index=personal`; alert when the gap since the last entry passes your threshold.",
            "Single-value tile of days since last gratitude log.",
            "when your gratitude habit has gone quiet for a few days, so you can pick it back up quickly.",
        ),
        S(
            "Meditation Timing Drift Across the Week",
            "low",
            "beginner",
            ["Analytics"],
            "index=personal sourcetype=meditation:session\n"
            "| eval session_hour=tonumber(strftime(_time,\"%H\")), day=strftime(_time,\"%a\")\n"
            "| stats avg(session_hour) as avg_hour, avg(minutes) as avg_minutes, count as sessions by day\n"
            "| sort day",
            "Shows whether meditation is anchored to a stable time of day or keeps drifting later in the week.",
            "A habit tied to a reliable time usually survives busy weeks better than one that keeps sliding around.",
            "Ingest meditation sessions with durations; review average session time and duration by weekday.",
            "Table of weekdays with average meditation start hour and minutes.",
            "when your meditation time keeps drifting later in the week, which is often how a good habit starts to wobble.",
        ),
        S(
            "Morning vs Evening Mood Gap",
            "medium",
            "beginner",
            ["Analytics"],
            "index=personal sourcetype=mood:entry\n"
            "| eval daypart=if(tonumber(strftime(_time,\"%H\"))<12,\"morning\",\"evening\")\n"
            "| stats avg(mood_score) as avg_mood, count as entries by daypart\n"
            "| eventstats avg(avg_mood) as overall\n"
            "| eval delta_from_overall=round(avg_mood-overall,2)",
            "Compares whether you usually feel stronger in the morning or the evening.",
            "Knowing when your mood is naturally better helps you place demanding work, reflection, or social time in the right part of the day.",
            "Collect timestamped mood scores in `index=personal`; compare averages between morning and evening entries.",
            "Two-bar comparison of average morning and evening mood.",
            "whether mornings or evenings are usually better for you, which helps you plan harder tasks for the right time.",
        ),
        S(
            "Mood Recovery Time After Hard Days",
            "medium",
            "intermediate",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=mood:entry\n"
            "| sort 0 _time\n"
            "| streamstats current=f last(mood_score) as prev_score last(_time) as prev_time\n"
            "| eval recovery_days=round((_time-prev_time)/86400,1)\n"
            "| where prev_score<3 AND mood_score>=4\n"
            "| stats count as recoveries, avg(recovery_days) as avg_days_to_recover, perc90(recovery_days) as p90_days",
            "Measures how quickly your mood usually rebounds after a notably bad day.",
            "Recovery speed says more about resilience than any single rough day and can reveal whether support routines are helping.",
            "Log mood scores into `index=personal`; calculate the gap between low-score days and the next clearly recovered entry.",
            "Single-value recovery summary with average and p90 days to rebound.",
            "how long it usually takes you to bounce back after a rough day, which says a lot about recovery and support habits.",
        ),
        S(
            "Journal Topic Recurrence Tracker",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=journal:entry topic=*\n"
            "| top limit=10 topic\n"
            "| rename count as entries, percent as share_pct",
            "Surfaces the journal topics that keep coming back so repeated worries or priorities are easier to notice.",
            "Recurring themes often reveal the real story of a month better than reading one entry at a time.",
            "Tag journal entries with a topic or prompt category; review the most common themes over your chosen window.",
            "Top-10 table of journal topics by entry count and share.",
            "which journal themes keep coming back, so repeated worries or goals stand out clearly.",
        ),
        S(
            "Gratitude Log Cadence by Day of Week",
            "low",
            "beginner",
            ["Analytics"],
            "index=personal sourcetype=gratitude:log\n"
            "| eval day=strftime(_time,\"%A\")\n"
            "| stats count as entries, avg(item_count) as avg_items by day\n"
            "| sort day",
            "Shows which days of the week you are most and least likely to pause and note something positive.",
            "A cadence view often reveals that gratitude is easy on calm days and forgotten on overloaded ones.",
            "Send gratitude logs with item counts to `index=personal`; summarize entries and average list size by weekday.",
            "Weekday table of gratitude entry counts and average items listed.",
            "which days of the week you tend to remember gratitude and which busy days make it disappear.",
        ),
    ],
    "32": [
        S(
            "Shared Meal Frequency Trend",
            "low",
            "beginner",
            ["Analytics", "Availability"],
            "index=personal sourcetype=datenight:log activity=shared_meal\n"
            "| bin _time span=1w\n"
            "| stats count as meals, avg(duration_min) as avg_minutes by _time\n"
            "| sort - _time",
            "Tracks how often you sit down for a proper shared meal together instead of rushing past each other.",
            "Regular shared meals are one of the easiest signals that a relationship still has breathing room during busy seasons.",
            "Tag date-night entries by activity type; summarize shared-meal frequency and average duration each week.",
            "Weekly chart of shared meals with average time together.",
            "how often you actually sit down together for a real meal, which is an easy sign of connection during busy weeks.",
        ),
        S(
            "Conflict Repair Time Tracker",
            "medium",
            "intermediate",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=relationship:checkin issue_open=true resolution_hours=*\n"
            "| bin _time span=1mon\n"
            "| stats avg(resolution_hours) as avg_hours, perc90(resolution_hours) as p90_hours, count as issues by _time\n"
            "| sort - _time",
            "Measures how long it takes to repair after tension instead of just counting that tension happened.",
            "A relationship with fast repair can be healthier than one with fewer but unresolved conflicts.",
            "Log check-ins that include issue-open and resolution-hours fields; review monthly averages and tail latency.",
            "Monthly line chart of average repair time with p90 overlay.",
            "how long it takes to make things right after tension, because quick repair matters as much as avoiding conflict.",
        ),
        S(
            "Keep-in-Touch Rotation Gaps",
            "low",
            "beginner",
            ["Availability"],
            "index=personal sourcetype=keptintouch:contact person=*\n"
            "| stats latest(_time) as last_contact, values(channel) as channels by person\n"
            "| eval days_since=round((now()-last_contact)/86400,0)\n"
            "| where days_since>45\n"
            "| sort - days_since",
            "Lists loved ones who have quietly fallen out of your contact rotation.",
            "The people who matter most are often the easiest to delay contacting because there is no hard deadline.",
            "Collect contact reminders and completions in `index=personal`; alert when the contact gap exceeds your threshold.",
            "Table of people with days since last contact and last-used channel.",
            "which people you have not checked in on for too long, so important relationships do not drift by accident.",
        ),
        S(
            "Occasion Readiness Before Birthday Week",
            "low",
            "intermediate",
            ["Inventory", "Operations"],
            "index=personal sourcetype=giftidea:item occasion=*\n"
            "| eval days_to_event=round((occasion_date-now())/86400,0)\n"
            "| stats min(days_to_event) as days_to_event, count as ideas, sum(eval(if(status=\"bought\",1,0))) as bought by occasion\n"
            "| eval pct_ready=round(100*bought/ideas,0)\n"
            "| where days_to_event<=7\n"
            "| sort days_to_event",
            "Shows which upcoming birthdays or anniversaries are still all idea and no execution.",
            "A gift backlog feels productive until the event is a week away and nothing is actually ready.",
            "Log idea status and occasion dates in `index=personal`; review readiness in the final week before each event.",
            "Table of upcoming occasions with days left and percentage already bought.",
            "which upcoming occasions are getting close while your gift ideas are still only ideas.",
        ),
        S(
            "Weekend Quality-Time Protection",
            "low",
            "beginner",
            ["Analytics"],
            "index=personal sourcetype=datenight:log\n"
            "| eval day_type=if(match(strftime(_time,\"%w\"),\"0|6\"),\"weekend\",\"weekday\")\n"
            "| stats count as sessions, avg(duration_min) as avg_minutes by day_type",
            "Compares whether quality time is being protected on weekends or crowded out there too.",
            "If weekends stop holding any extra relationship time, busyness has probably taken over more than it feels like.",
            "Send date-night and quality-time logs to `index=personal`; compare session counts and average duration by day type.",
            "Two-bar comparison of weekday versus weekend quality-time sessions.",
            "whether weekends are still protecting time together or whether even those days are getting crowded out.",
        ),
        S(
            "Relationship Check-In Drift After Busy Weeks",
            "medium",
            "intermediate",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=relationship:checkin\n"
            "| bin _time span=1w\n"
            "| stats count as checkins, avg(score) as avg_score by _time\n"
            "| streamstats window=4 avg(checkins) as trailing_checkins\n"
            "| eval low_contact=if(checkins<trailing_checkins*0.5,1,0)\n"
            "| sort - _time",
            "Flags weeks where relationship check-ins dropped sharply compared with your recent norm.",
            "A sudden fall in check-ins is often the first sign that coordination and emotional maintenance are slipping.",
            "Track check-ins in `index=personal`; compare each week with the trailing four-week baseline.",
            "Weekly chart of check-in volume with anomaly highlighting.",
            "when the little check-ins that keep a relationship steady suddenly drop away during a busy stretch.",
        ),
        S(
            "Gift-Idea Conversion Before the Event",
            "low",
            "beginner",
            ["Quality", "Operations"],
            "index=personal sourcetype=giftidea:item occasion=*\n"
            "| stats count as ideas, sum(eval(if(status=\"bought\",1,0))) as bought, sum(eval(if(status=\"wrapped\",1,0))) as wrapped by occasion\n"
            "| eval conversion_pct=round(100*bought/ideas,0), wrap_pct=round(100*wrapped/ideas,0)\n"
            "| sort - conversion_pct",
            "Measures how many gift ideas ever turn into an actual bought or wrapped present.",
            "It is easy to mistake collecting ideas for making progress; conversion makes that gap visible.",
            "Record each idea with a lifecycle status in `index=personal`; summarize conversion and wrap rates by occasion.",
            "Table of occasions with idea count, bought count, and conversion percentage.",
            "how many gift ideas ever become a real present instead of staying in a list forever.",
        ),
        S(
            "One-Sided Chore Drift Alert",
            "medium",
            "intermediate",
            ["Analytics", "Risk"],
            "index=personal sourcetype=relationship:checkin chore_share_pct=*\n"
            "| bin _time span=1w\n"
            "| stats avg(my_share_pct) as my_share, avg(partner_share_pct) as partner_share by _time\n"
            "| eval imbalance=round(abs(my_share-partner_share),1)\n"
            "| where imbalance>20\n"
            "| sort - _time",
            "Flags weeks where household work starts tilting too heavily to one side.",
            "Chore imbalance builds resentment gradually; a simple percentage gap catches it before it becomes the whole conversation.",
            "Capture rough chore-share estimates during relationship check-ins; alert when weekly imbalance passes your chosen threshold.",
            "Weekly line chart of each person’s chore share with imbalance highlighting.",
            "when household work starts leaning too much onto one person, before that turns into quiet resentment.",
        ),
    ],
    "33": [
        S(
            "Dry-Week Completion Rate",
            "medium",
            "beginner",
            ["Analytics", "Compliance"],
            "index=personal sourcetype=vice:log habit=dry_week\n"
            "| bin _time span=1mon\n"
            "| stats count as attempts, sum(eval(if(completed=\"true\",1,0))) as completed by _time\n"
            "| eval completion_pct=round(100*completed/attempts,0)\n"
            "| sort - _time",
            "Tracks how often an intended dry week is completed rather than abandoned halfway through.",
            "Success rate is more honest than good intentions and shows whether the goal is actually sustainable.",
            "Log dry-week attempts and outcomes in `index=personal`; summarize monthly attempt and completion rates.",
            "Monthly column chart of dry-week attempts versus completions.",
            "how often your planned dry weeks actually make it to the finish line instead of fading halfway through.",
        ),
        S(
            "Late-Night Drink Clustering",
            "medium",
            "beginner",
            ["Analytics", "Risk"],
            "index=personal sourcetype=alcohol:drink\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| where hour>=21\n"
            "| bin _time span=1d\n"
            "| stats count as late_drinks, sum(units) as units by _time\n"
            "| sort - _time",
            "Shows how much drinking is concentrated late at night rather than spread across social meals or events.",
            "Late-night clustering often maps to lower-quality decisions, worse sleep, and habits that feel smaller than they are.",
            "Ingest alcohol events with unit counts; report daily drinks and units taken after 9 PM.",
            "Daily chart of late-night drinks and units.",
            "how much of your drinking happens late at night, when habits tend to be less deliberate and more costly.",
        ),
        S(
            "Nicotine-Free Morning Streak",
            "medium",
            "intermediate",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=vice:log habit=nicotine\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| bin _time span=1d\n"
            "| stats min(eval(if(hour<12,1,0))) as morning_use by _time\n"
            "| eval nicotine_free_morning=if(morning_use=1,0,1)\n"
            "| streamstats current=t sum(eval(if(nicotine_free_morning=1,1,0))) as streak reset_after=\"(nicotine_free_morning=0)\"\n"
            "| sort - _time",
            "Tracks the streak of mornings where nicotine was pushed back beyond midday or skipped entirely.",
            "Winning the first half of the day is often the strongest predictor that cutback plans are really taking hold.",
            "Log nicotine events to `index=personal`; calculate whether each morning stayed clear and maintain a rolling streak.",
            "Daily streak chart for nicotine-free mornings.",
            "how many mornings in a row you get through without nicotine, which is often the hardest and most important window.",
        ),
        S(
            "Midday Hydration Catch-Up Alert",
            "low",
            "beginner",
            ["Analytics", "Availability"],
            "index=personal sourcetype=hydration:intake\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| where hour<13\n"
            "| bin _time span=1d\n"
            "| stats sum(ml) as ml_by_midday by _time\n"
            "| eval catch_up_needed=if(ml_by_midday<1000,1,0)\n"
            "| sort - _time",
            "Flags days where hydration is already lagging by lunchtime.",
            "A midday catch-up alert is more useful than an end-of-day total because it still leaves time to fix the habit.",
            "Send water-intake logs to `index=personal`; alert when cumulative intake by midday misses your threshold.",
            "Daily column chart of hydration reached by midday.",
            "when you are already behind on water by lunchtime, so there is still time to catch up the easy way.",
        ),
        S(
            "Stress-Tagged Vice Trigger Map",
            "medium",
            "intermediate",
            ["Analytics", "Risk"],
            "index=personal sourcetype=vice:log trigger=*\n"
            "| stats count as events, avg(craving_score) as avg_craving by trigger\n"
            "| sort - events",
            "Ranks the triggers and contexts most often associated with smoking, vaping, drinking, or other vices.",
            "Knowing the trigger pattern turns a vague bad habit into something you can actually reroute.",
            "Tag vice events with trigger categories in `index=personal`; summarize event count and average craving by trigger.",
            "Bar chart of vice triggers ranked by frequency.",
            "which situations most often set off the habit, so you can plan around the trigger instead of only reacting later.",
        ),
        S(
            "Weekend Recovery Hydration Gap",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=hydration:intake\n"
            "| eval day_type=if(match(strftime(_time,\"%w\"),\"0|6\"),\"weekend\",\"weekday\")\n"
            "| stats avg(ml) as avg_ml, avg(goal_pct) as avg_goal_pct by day_type",
            "Compares whether hydration collapses on weekends, when routines and recovery needs often change most.",
            "Weekend habits often explain why Monday feels rough even when weekdays look disciplined.",
            "Track water intake and goal percentage in `index=personal`; compare average hydration by weekend versus weekday.",
            "Two-bar comparison of weekday and weekend hydration.",
            "whether weekends quietly wreck your hydration even when weekdays look under control.",
        ),
        S(
            "Swear-Jar Cost by Place and Time",
            "low",
            "beginner",
            ["Cost", "Analytics"],
            "index=personal sourcetype=swearjar:entry\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| stats count as swears, sum(amount) as cost by location hour\n"
            "| sort - cost",
            "Shows where and when the swear jar fills up fastest.",
            "A playful metric still reveals genuine stress pockets, commute frustrations, or environments that grind you down.",
            "Send each swear-jar event to `index=personal`; summarize counts and cost by location and hour.",
            "Heat map of swear-jar cost by location and hour.",
            "where and when your swear jar grows fastest, which often points to the most stressful pockets of the day.",
        ),
        S(
            "Sobriety Savings Run-Rate",
            "medium",
            "beginner",
            ["Cost", "Analytics"],
            "index=personal sourcetype=vice:log saved_amount=*\n"
            "| bin _time span=1w\n"
            "| stats sum(saved_amount) as saved by _time\n"
            "| eventstats avg(saved) as avg_weekly_saved\n"
            "| eval annualised=round(avg_weekly_saved*52,2)\n"
            "| sort - _time",
            "Turns each cut-back decision into a visible savings run-rate instead of a vague nice idea.",
            "Money saved is a powerful reinforcement loop for habits that otherwise feel like only deprivation.",
            "Record the estimated amount saved for skipped vice events; chart weekly totals and the annualised savings trend.",
            "Weekly savings chart with an annualised run-rate tile.",
            "how much money cutting back is really saving you, which makes progress feel concrete and worth keeping.",
        ),
    ],
    "34": [
        S(
            "Tiny Fee and Surcharge Leak",
            "low",
            "beginner",
            ["Cost", "Analytics"],
            "index=personal sourcetype=microspend:txn category=fees\n"
            "| bin _time span=1mon\n"
            "| stats sum(amount) as fee_spend, count as fees by _time\n"
            "| sort - _time",
            "Adds up all the tiny service fees, ATM charges, and surcharges that hide in the noise.",
            "Small fees feel harmless because each one is annoying rather than dramatic, but together they are pure leakage.",
            "Categorise micro-transactions in `index=personal`; total recurring small fees each month.",
            "Monthly chart of fee spend and count of fee events.",
            "all the little fees and surcharges that quietly leak money without buying you anything useful.",
        ),
        S(
            "Convenience-Store Premium Tracker",
            "low",
            "beginner",
            ["Cost", "Business"],
            "index=personal sourcetype=microspend:txn merchant_type=convenience\n"
            "| stats sum(amount) as spend, avg(unit_price) as avg_unit_price, count as buys by merchant\n"
            "| sort - spend",
            "Shows how much extra you pay for convenience-store habits compared with cheaper routine shopping.",
            "Convenience often means paying a premium for planning failure, and that pattern is worth seeing clearly.",
            "Tag merchant type and unit price for convenience buys in `index=personal`; summarize spend and average price by merchant.",
            "Merchant table of convenience spend and average unit price.",
            "how much extra convenience-store habits are really costing compared with better-planned shopping.",
        ),
        S(
            "Reward Breakage Before Expiry",
            "low",
            "beginner",
            ["Cost", "Risk"],
            "index=personal sourcetype=cashback:reward\n"
            "| eval days_to_expiry=round((expiry_date-now())/86400,0)\n"
            "| stats sum(balance) as balance, min(days_to_expiry) as soonest_expiry by program\n"
            "| where soonest_expiry<=30\n"
            "| sort soonest_expiry",
            "Flags rewards balances that are likely to expire unused.",
            "Cash-back and points feel like gains, but unused rewards are just deferred waste.",
            "Ingest reward-balance snapshots with expiry dates; alert when expiry is near and value is still unclaimed.",
            "Table of reward programs with balance and days to expiry.",
            "which rewards or points are about to expire unused, so free money does not vanish by neglect.",
        ),
        S(
            "Repeat Small Spend by Merchant",
            "low",
            "beginner",
            ["Analytics", "Business"],
            "index=personal sourcetype=microspend:txn\n"
            "| stats count as purchases, sum(amount) as spend, avg(amount) as avg_ticket by merchant\n"
            "| where purchases>=5\n"
            "| sort - spend",
            "Surfaces the merchants where tiny repeat purchases have become a pattern.",
            "The real leak is often not one expensive impulse but the place you visit a little too often without noticing.",
            "Track merchant names for micro-spend transactions; rank merchants by repeat-purchase count and total spend.",
            "Merchant leaderboard of repeat small spend.",
            "which places you keep making lots of little purchases from, even if each one feels harmless on its own.",
        ),
        S(
            "No-Spend Streak Recovery Time",
            "low",
            "intermediate",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=nospend:day\n"
            "| sort 0 _time\n"
            "| eval no_spend=if(status=\"success\",1,0)\n"
            "| streamstats current=t sum(eval(if(no_spend=1,1,0))) as streak reset_after=\"(no_spend=0)\"\n"
            "| stats max(streak) as best_streak, avg(streak) as avg_streak, latest(streak) as current_streak",
            "Shows how quickly you get back into a no-spend rhythm after a broken streak.",
            "Recovery after a miss is the difference between a useful habit and an all-or-nothing one.",
            "Log each no-spend day with success or failure status; track best, average, and current streaks.",
            "Streak summary tile with best, average, and current values.",
            "how quickly you get back into no-spend days after a wobble, which matters more than never slipping at all.",
        ),
        S(
            "Price-Per-Use Redemption Progress",
            "low",
            "beginner",
            ["Cost", "Quality"],
            "index=personal sourcetype=priceperuse:item\n"
            "| eval cost_per_use=round(price/uses,2)\n"
            "| stats latest(price) as price, latest(uses) as uses, latest(cost_per_use) as cost_per_use by item\n"
            "| sort cost_per_use",
            "Shows which purchases are earning their keep and which are still expensive clutter.",
            "Price-per-use turns guilt about a purchase into an objective signal of whether it is becoming valuable over time.",
            "Track item price and uses in `index=personal`; rank items by latest cost per use.",
            "Table of items with price, uses, and current cost per use.",
            "which purchases are finally earning their keep and which are still expensive things you barely touch.",
        ),
        S(
            "Delivery-App Spend vs Walkable Alternatives",
            "low",
            "beginner",
            ["Cost", "Analytics"],
            "index=personal sourcetype=microspend:txn category=delivery_food\n"
            "| bin _time span=1w\n"
            "| stats sum(amount) as delivery_spend, count as orders, avg(distance_km) as avg_distance by _time\n"
            "| sort - _time",
            "Highlights how much is being spent on convenience orders that may have an easy local alternative.",
            "Delivery spend often feels like a lifestyle choice until the weekly total makes the premium obvious.",
            "Categorise food-delivery transactions and track delivery distance when available; review weekly order count and spend.",
            "Weekly chart of delivery-app spend and order volume.",
            "how much money is going on convenience delivery that might have been a quick walk or cheaper local pickup.",
        ),
        S(
            "Impulse Spend Regret by Hour",
            "low",
            "intermediate",
            ["Analytics", "Risk"],
            "index=personal sourcetype=microspend:txn regretted=true\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| stats count as regretted_buys, sum(amount) as spend by hour\n"
            "| sort hour",
            "Shows the times of day when impulse spending is most likely to lead to regret.",
            "Patterns of regretted spending are usually linked to fatigue, stress, or boredom rather than real need.",
            "Tag regretted transactions in `index=personal`; summarize count and spend by purchase hour.",
            "Hour-by-hour chart of regretted impulse spend.",
            "what time of day you are most likely to buy something small and wish you had not later.",
        ),
    ],
    "35": [
        S(
            "Symptom Flare by Hour-of-Day",
            "medium",
            "beginner",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=symptom:log severity=*\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| stats avg(severity) as avg_severity, count as flares by hour\n"
            "| sort hour",
            "Shows when symptoms most often flare across the day.",
            "Timing patterns can reveal environmental triggers, meal timing effects, or workday stress that are easy to miss in notes.",
            "Collect timestamped symptom logs with severity in `index=personal`; summarize severity and count by hour.",
            "Hour-of-day heat map of symptom count and average severity.",
            "what time of day your symptoms usually flare, which can reveal patterns hidden inside a pile of notes.",
        ),
        S(
            "Overnight Bathroom Wake-Up Trend",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=bathroom:visit\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| where hour<6\n"
            "| bin _time span=1d\n"
            "| stats count as overnight_visits by _time\n"
            "| sort - _time",
            "Tracks nighttime bathroom interruptions that may be chipping away at sleep quality.",
            "A creeping overnight pattern is hard to notice from memory but easy to see in a daily count.",
            "Send bathroom-visit events to `index=personal`; review visits occurring before 6 AM as a sleep-disruption signal.",
            "Daily column chart of overnight bathroom visits.",
            "how often bathroom trips are breaking your sleep overnight, because even small interruptions add up.",
        ),
        S(
            "Sneezing Burst Detector",
            "low",
            "beginner",
            ["Anomaly"],
            "index=personal sourcetype=sneeze:event\n"
            "| bin _time span=30m\n"
            "| stats count as sneezes by _time\n"
            "| eventstats avg(sneezes) as base stdev(sneezes) as sd\n"
            "| eval burst=if(sneezes>base+(2*sd),1,0)\n"
            "| where burst=1\n"
            "| sort - _time",
            "Flags half-hour windows where sneezing suddenly spikes above your normal pattern.",
            "Burst detection helps you line symptoms up with pollen, dust, pets, rooms, or activities while the clue is still fresh.",
            "Ingest sneeze events into `index=personal`; compare each time bucket with your baseline and alert on spikes.",
            "Timeline of sneeze bursts above baseline.",
            "when your sneezing suddenly jumps well above normal, making it easier to connect it to the room or trigger.",
        ),
        S(
            "Posture Recovery After Break Reminders",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=posture:reading reminder_window=*\n"
            "| stats avg(posture_score) as avg_score, sum(duration_min) as minutes by reminder_window\n"
            "| sort reminder_window",
            "Measures whether break reminders actually improve posture afterwards or are simply dismissed.",
            "It is useful to know whether reminders help or just add notification guilt.",
            "Capture posture score and whether the reading is in a post-reminder window; compare average posture across windows.",
            "Table of posture score by reminder window.",
            "whether your break reminders are actually helping you sit better afterwards or just becoming background noise.",
        ),
        S(
            "Symptom-Free Streak Counter",
            "low",
            "beginner",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=symptom:log\n"
            "| bin _time span=1d\n"
            "| stats count as symptoms by _time\n"
            "| eval symptom_day=if(symptoms>0,1,0), symptom_free=if(symptom_day=0,1,0)\n"
            "| streamstats current=t sum(eval(if(symptom_free=1,1,0))) as clear_streak reset_after=\"(symptom_day=1)\"\n"
            "| sort - _time",
            "Tracks how many symptom-free days in a row you are managing.",
            "Seeing a clear streak can be motivating and can also reveal whether an intervention is quietly working.",
            "Aggregate symptom events into daily buckets; maintain a symptom-free streak counter in Splunk.",
            "Daily streak chart of symptom-free days.",
            "how many symptom-free days you manage in a row, which helps good periods feel real and measurable.",
        ),
        S(
            "Desk Pain Trigger Map",
            "medium",
            "intermediate",
            ["Analytics", "Risk"],
            "index=personal sourcetype=symptom:log trigger=desk_work\n"
            "| stats count as episodes, avg(severity) as avg_severity by body_area\n"
            "| sort - episodes",
            "Ranks the body areas most affected by desk-work-triggered pain or discomfort.",
            "If pain repeats in the same places, it is often pointing at setup problems rather than random bad luck.",
            "Tag symptom logs with trigger and body-area fields; summarize desk-related pain frequency and average severity.",
            "Bar chart of desk-related pain episodes by body area.",
            "which parts of your body desk work keeps irritating, so the pattern points you toward an ergonomic fix.",
        ),
        S(
            "Bathroom Visit Frequency Change Guard",
            "medium",
            "beginner",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=bathroom:visit\n"
            "| bin _time span=1d\n"
            "| stats count as visits by _time\n"
            "| eventstats avg(visits) as base stdev(visits) as sd\n"
            "| eval unusual=if(visits>base+(2*sd) OR visits<base-(2*sd),1,0)\n"
            "| sort - _time",
            "Flags days where bathroom frequency changes sharply from your normal baseline.",
            "A change in frequency is often more revealing than the absolute number because it reflects your usual pattern.",
            "Send bathroom visits to `index=personal`; compare daily totals with baseline and alert on sudden shifts.",
            "Daily chart of visit counts with anomaly markers.",
            "when bathroom visits change a lot from your normal pattern, which is usually more important than any one day alone.",
        ),
        S(
            "Slouching During Long Meetings",
            "low",
            "intermediate",
            ["Analytics", "Operations"],
            "index=personal sourcetype=posture:reading meeting=true\n"
            "| stats sum(eval(if(state=\"slouch\",duration_min,0))) as slouch_min, sum(duration_min) as total_min by meeting_name\n"
            "| eval slouch_pct=round(100*slouch_min/total_min,1)\n"
            "| sort - slouch_pct",
            "Shows which recurring meetings are posture traps.",
            "Some meetings are physically draining because they are long, passive, or badly timed, and that deserves visibility too.",
            "Tag posture readings that occur during meetings; compare slouch minutes and slouch percentage by meeting name.",
            "Meeting table ranked by slouch percentage.",
            "which meetings turn you into a slouching statue, so you can change how you sit or when you take breaks.",
        ),
    ],
    "36": [
        S(
            "Parcel Carrier Delay League Table",
            "low",
            "beginner",
            ["Quality", "Operations"],
            "index=personal sourcetype=delivery:parcel\n"
            "| stats avg(delay_hours) as avg_delay, perc90(delay_hours) as p90_delay, count as parcels by carrier\n"
            "| sort - avg_delay",
            "Ranks the carriers that are most likely to miss promised delivery windows for your household.",
            "A delay league table turns delivery frustration into evidence you can use when choosing shipping options.",
            "Track delivery events with carrier and delay-hours fields in `index=personal`; compare average and p90 delay by carrier.",
            "Carrier leaderboard of average and p90 parcel delays.",
            "which delivery carriers keep making your parcels late, instead of every delay feeling like random bad luck.",
        ),
        S(
            "Reorder Bundling Opportunity",
            "low",
            "intermediate",
            ["Inventory", "Cost"],
            "index=personal sourcetype=supply:level\n"
            "| eval days_left=round(level_pct/daily_use_pct,1)\n"
            "| where days_left<=14\n"
            "| stats values(item) as items min(days_left) as soonest by vendor\n"
            "| sort soonest",
            "Highlights low-stock items that can be reordered together instead of one emergency purchase at a time.",
            "Bundling planned reorders saves delivery fees, time, and the cognitive tax of constant replenishment.",
            "Track consumable levels and preferred vendor in `index=personal`; group items that will run low in the same window.",
            "Vendor table of low-stock items and soonest days-left value.",
            "which household items are due for reordering together, so you can batch them instead of making panic buys.",
        ),
        S(
            "Missed Bin Collection Recovery Watch",
            "low",
            "beginner",
            ["Operations", "Anomaly"],
            "index=personal sourcetype=bincollection:event status=missed\n"
            "| stats latest(_time) as last_missed, count as misses by collection_type\n"
            "| eval days_since=round((now()-last_missed)/86400,0)\n"
            "| sort - last_missed",
            "Tracks which collection types you are most likely to miss and how recently it happened.",
            "Missing the right bin on the wrong week creates outsized hassle, so it is worth making the weak point obvious.",
            "Send collection reminders and outcomes to `index=personal`; summarize missed pickups by waste type.",
            "Table of collection types with miss count and days since last miss.",
            "which bins you keep missing and how recently it happened, so the same annoying mistake does not repeat.",
        ),
        S(
            "Gift-Card Balance Fragmentation",
            "low",
            "beginner",
            ["Inventory", "Cost"],
            "index=personal sourcetype=giftcard:balance\n"
            "| stats count as cards, sum(balance) as total_balance, avg(balance) as avg_balance by merchant\n"
            "| sort - total_balance",
            "Shows where value is trapped in lots of half-used gift cards and vouchers.",
            "Fragmented balances are easy to forget and often expire before they ever become useful.",
            "Ingest gift-card balances in `index=personal`; summarize card count and value per merchant.",
            "Merchant table of cards held, total balance, and average remaining balance.",
            "how much value is scattered across partly used gift cards instead of being spent while it still matters.",
        ),
        S(
            "Pantry Overstock vs Use Rate",
            "low",
            "intermediate",
            ["Inventory", "Analytics"],
            "index=personal sourcetype=supply:level\n"
            "| eval days_left=round(level_pct/daily_use_pct,1)\n"
            "| stats latest(level_pct) as level_pct, latest(days_left) as days_left by item\n"
            "| where days_left>45\n"
            "| sort - days_left",
            "Flags pantry items where stock has outpaced real usage and may be turning into clutter or waste.",
            "Running out is annoying, but chronic overstock quietly ties up cash and shelf space.",
            "Track item levels and consumption rates in `index=personal`; review items with unusually long supply runways.",
            "Table of items with current level and estimated days of supply left.",
            "which pantry items you keep overbuying relative to how fast you actually use them.",
        ),
        S(
            "Delivery Failure and Redelivery Rate",
            "low",
            "beginner",
            ["Quality", "Operations"],
            "index=personal sourcetype=delivery:parcel\n"
            "| stats count as parcels, sum(eval(if(attempt_status=\"failed\",1,0))) as failed, sum(eval(if(redelivery_needed=\"true\",1,0))) as redeliveries by carrier\n"
            "| eval failure_pct=round(100*failed/parcels,1), redelivery_pct=round(100*redeliveries/parcels,1)\n"
            "| sort - failure_pct",
            "Shows which delivery workflows most often turn into failed attempts or redelivery hassle.",
            "The hidden cost of a parcel is often your time and coordination, not only the shipping price.",
            "Capture delivery attempt outcomes in `index=personal`; compare failure and redelivery rates by carrier.",
            "Carrier table of parcel count, failure percentage, and redelivery percentage.",
            "which deliveries keep failing on the first attempt and turning into avoidable extra hassle.",
        ),
        S(
            "Consumable Burn-Rate Spikes After Guests",
            "low",
            "intermediate",
            ["Analytics", "Capacity"],
            "index=personal sourcetype=supply:level guest_period=*\n"
            "| stats avg(daily_use_pct) as avg_daily_use, latest(level_pct) as current_level by item guest_period\n"
            "| sort - avg_daily_use",
            "Compares how quickly staples are consumed during guest periods versus normal household rhythm.",
            "Guests change consumption patterns fast, and learning those spikes helps you stock realistically for visits.",
            "Tag supply snapshots with guest-period context; compare average daily use across normal and guest periods.",
            "Grouped table of consumable burn rate by item and guest-period flag.",
            "how much faster household staples vanish when guests are around, so you can plan visits without running out.",
        ),
        S(
            "Bin-Day Prep Cutoff Reminder",
            "low",
            "beginner",
            ["Operations", "Availability"],
            "index=personal sourcetype=bincollection:event next_pickup=*\n"
            "| stats latest(next_pickup) as next_pickup, latest(collection_type) as collection_type by address\n"
            "| eval hours_left=round((next_pickup-now())/3600,1), prep_now=if(hours_left<12,1,0)\n"
            "| sort hours_left",
            "Shows when you are inside the last practical window to get the right bins or recycling out.",
            "A reminder the night before is useful; a reminder when there are two hours left is sometimes the one that saves you.",
            "Send calendar-style collection events into `index=personal`; compute hours remaining until the next pickup window.",
            "Single-value or table view of next collection type and hours remaining.",
            "when you are entering the last useful window to get the right bins out before collection morning.",
        ),
    ],
    "37": [
        S(
            "Overnight Humidity Recovery Failure",
            "medium",
            "intermediate",
            ["Anomaly", "Safety"],
            "index=personal sourcetype=mould:risk\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| where hour<6\n"
            "| stats avg(humidity_pct) as overnight_humidity, min(dewpoint_gap) as worst_gap by room\n"
            "| eval failed_recovery=if(overnight_humidity>65 OR worst_gap<3,1,0)\n"
            "| where failed_recovery=1",
            "Flags rooms that stay damp or condensation-prone all night instead of recovering by morning.",
            "If a room cannot recover overnight, the mould risk is no longer a short blip but a persistent condition.",
            "Ingest humidity and dew-point-gap readings into `index=personal`; alert on rooms that stay risky overnight.",
            "Room table of overnight humidity and worst dew-point gap.",
            "which rooms stay too damp all night instead of drying out by morning, giving mould a better chance to settle in.",
        ),
        S(
            "Crack Widening Acceleration Watch",
            "high",
            "intermediate",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=crackmeter:reading\n"
            "| sort 0 sensor _time\n"
            "| streamstats current=f last(width_mm) as prev_width by sensor\n"
            "| eval growth_mm=round(width_mm-prev_width,2)\n"
            "| stats max(growth_mm) as max_growth, latest(width_mm) as latest_width by sensor\n"
            "| where max_growth>0.5\n"
            "| sort - max_growth",
            "Flags structural cracks whose widening rate has accelerated beyond recent behaviour.",
            "Acceleration matters more than the absolute number because it hints that movement may be active rather than historical.",
            "Send crack-width readings to `index=personal`; compare each reading with the previous one and alert on sharp growth.",
            "Sensor table of latest width and maximum recent growth.",
            "which structural cracks are starting to widen faster than before, which matters more than a single static reading.",
        ),
        S(
            "Filter Life Burn-Down vs Runtime",
            "low",
            "beginner",
            ["Analytics", "Capacity"],
            "index=personal sourcetype=hvacfilter:life\n"
            "| stats latest(life_pct) as life_pct, avg(runtime_hours_per_day) as runtime_hours by filter_id\n"
            "| eval days_remaining=round((life_pct/100)*(90/runtime_hours),1)\n"
            "| sort days_remaining",
            "Estimates whether HVAC filters are burning down faster because the system is simply running harder.",
            "A filter can hit end-of-life quickly in heavy-use periods, and a percentage alone does not explain why.",
            "Capture filter-life percentage and runtime estimates in `index=personal`; estimate remaining days by filter.",
            "Table of filters with life percentage, runtime, and estimated days remaining.",
            "how quickly your HVAC filters are wearing out compared with how hard the system is running.",
        ),
        S(
            "Structural Tilt Drift After Storms",
            "high",
            "intermediate",
            ["Anomaly", "Safety"],
            "index=personal sourcetype=structural:tilt storm_window=true\n"
            "| bin _time span=1w\n"
            "| stats max(abs(tilt_deg)) as max_tilt, avg(abs(tilt_deg)) as avg_tilt by sensor _time\n"
            "| sort - _time",
            "Tracks whether tilt sensors show unusual movement during or just after storm-tagged windows.",
            "Storms often reveal weaknesses that calm-weather averages hide, so isolating those windows is useful.",
            "Tag structural tilt readings with a storm-window flag and summarize weekly peak tilt by sensor.",
            "Weekly sensor chart of average and maximum tilt during storm windows.",
            "whether storms seem to make certain parts of the building shift more than usual.",
        ),
        S(
            "Condensation-Prone Window Ranking",
            "medium",
            "beginner",
            ["Analytics", "Risk"],
            "index=personal sourcetype=mould:risk window_id=*\n"
            "| stats min(dewpoint_gap) as worst_gap, avg(humidity_pct) as avg_humidity by window_id\n"
            "| sort worst_gap",
            "Ranks the windows or cold surfaces most likely to attract condensation.",
            "Knowing the worst spots helps you prioritise insulation, ventilation, or simple daily wiping where it matters most.",
            "Attach window or surface identifiers to mould-risk readings; rank surfaces by worst dew-point gap.",
            "Table of windows ranked by condensation risk.",
            "which windows or cold surfaces are most likely to collect moisture and start trouble.",
        ),
        S(
            "Dehumidifier Impact on Mould Risk",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=mould:risk dehumidifier_state=*\n"
            "| stats avg(humidity_pct) as avg_humidity, avg(dewpoint_gap) as avg_gap by room dehumidifier_state\n"
            "| sort room dehumidifier_state",
            "Compares room humidity and condensation margin with the dehumidifier on versus off.",
            "This turns a dehumidifier from a vague comfort device into something you can verify is doing useful work.",
            "Send room readings with dehumidifier state to `index=personal`; compare averages for on and off periods.",
            "Grouped room table of humidity and dew-point gap by dehumidifier state.",
            "whether the dehumidifier is really making a measurable difference in the rooms you worry about.",
        ),
        S(
            "Filter Change Overdue Escalation",
            "medium",
            "beginner",
            ["Operations", "Risk"],
            "index=personal sourcetype=hvacfilter:life\n"
            "| stats latest(life_pct) as life_pct, latest(days_since_change) as days_since_change by filter_id\n"
            "| eval overdue=if(life_pct<20 OR days_since_change>120,1,0)\n"
            "| where overdue=1\n"
            "| sort - days_since_change",
            "Flags filters that are overdue by either condition-based life or elapsed time.",
            "Using both clocks catches the cases where the system is lightly used but the filter still sat there too long.",
            "Ingest filter-life and days-since-change metrics into `index=personal`; alert when either threshold is breached.",
            "Table of overdue filters with life percentage and days since change.",
            "which HVAC filters have been left too long either because they are worn out or simply too old.",
        ),
        S(
            "Room Stability Score Across Seasons",
            "low",
            "intermediate",
            ["Analytics", "Reliability"],
            "index=personal sourcetype=mould:risk\n"
            "| stats stdev(temp_c) as temp_sd, stdev(humidity_pct) as humidity_sd by room season\n"
            "| eval stability_score=round(100-(temp_sd*5)-(humidity_sd*1.5),1)\n"
            "| sort - stability_score",
            "Scores which rooms stay most stable across seasons and which ones swing wildly.",
            "Stability is a good shorthand for comfort, condensation control, and how predictable a room feels to live in.",
            "Log seasonal mould-risk readings with room and season tags; derive a simple stability score from temperature and humidity variance.",
            "Table of rooms and seasons ranked by stability score.",
            "which rooms stay nicely steady through the seasons and which ones swing around the most.",
        ),
    ],
    "38": [
        S(
            "Inbox Unread Debt Trend",
            "low",
            "beginner",
            ["Analytics", "Data Quality"],
            "index=personal sourcetype=inbox:stats\n"
            "| timechart span=1w avg(unread_count) as unread\n"
            "| eventstats avg(unread) as baseline\n"
            "| eval debt_rising=if(unread>baseline*1.2,1,0)",
            "Tracks whether inbox backlog is quietly turning into permanent unread debt.",
            "Unread debt is not just clutter; it is a personal attack surface for missed receipts, notices, and security mail.",
            "Send weekly inbox statistics to `index=personal`; chart unread counts and compare them with baseline.",
            "Weekly line chart of unread-count trend with rising-debt flag.",
            "whether unread email is quietly piling up into a backlog that never really gets cleared.",
        ),
        S(
            "Breach Exposure by Email Alias",
            "high",
            "beginner",
            ["Security", "Analytics"],
            "index=personal sourcetype=breach:alert alias=*\n"
            "| stats count as breach_hits, values(breach) as breaches by alias\n"
            "| sort - breach_hits",
            "Shows which email aliases or addresses attract the most breach exposure over time.",
            "Alias-level visibility helps you see which signup patterns or services are making your digital life noisier and riskier.",
            "Ingest breach alerts with alias or account labels; summarize hit counts and breach names per alias.",
            "Table of aliases ranked by breach exposure count.",
            "which email aliases get exposed in breaches most often, helping you spot the risky corners of your online life.",
        ),
        S(
            "Cloud-Drive Growth Runaway",
            "medium",
            "beginner",
            ["Capacity", "Cost"],
            "index=personal sourcetype=clouddrive:usage\n"
            "| timechart span=1w avg(used_gb) as used_gb\n"
            "| delta used_gb as weekly_growth_gb\n"
            "| eval runaway=if(weekly_growth_gb>5,1,0)",
            "Flags weeks where cloud storage growth speeds up sharply.",
            "Runaway storage growth usually means photo sync, backups, or large attachments are drifting without anyone noticing.",
            "Track storage usage snapshots in `index=personal`; chart weekly growth and alert when the slope jumps.",
            "Weekly line chart of used cloud storage with growth markers.",
            "when your cloud storage starts growing much faster than normal, before it turns into a cost or cleanup problem.",
        ),
        S(
            "Certificate Renewal Failure Queue",
            "high",
            "beginner",
            ["Security", "Operations"],
            "index=personal sourcetype=certexpiry:check\n"
            "| where status!=\"renewed\"\n"
            "| stats min(days_left) as days_left, latest(common_name) as common_name by endpoint\n"
            "| where days_left<14\n"
            "| sort days_left",
            "Lists personal endpoints or services whose certificates are nearing expiry without a successful renewal.",
            "Even for personal infrastructure, certificate expiry is a needless self-inflicted outage or trust warning.",
            "Ingest certificate checks into `index=personal`; alert on endpoints inside the final two weeks without renewal.",
            "Table of endpoints with common name and days remaining.",
            "which of your personal sites or services are heading toward an expired certificate warning because renewal has not happened.",
        ),
        S(
            "Newsletter Purge Progress",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=inbox:stats\n"
            "| bin _time span=1w\n"
            "| stats avg(newsletter_unread) as newsletter_unread, avg(unsubscribe_candidates) as unsubscribe_candidates by _time\n"
            "| sort - _time",
            "Shows whether inbox cleanup is actually reducing newsletter clutter over time.",
            "A purge feels satisfying in one session, but the trend tells you whether the system is healthier or just briefly tidier.",
            "Send inbox stats with newsletter counts to `index=personal`; review weekly clutter and unsubscribe-candidate trends.",
            "Weekly chart of newsletter unread count and candidate count.",
            "whether your inbox clean-up is really cutting newsletter clutter or only making it look better for a day or two.",
        ),
        S(
            "Secondary Inbox Neglect Risk",
            "medium",
            "beginner",
            ["Security", "Risk"],
            "index=personal sourcetype=inbox:stats account_role=backup\n"
            "| stats latest(_time) as last_seen, latest(unread_count) as unread_count by account\n"
            "| eval days_since=round((now()-last_seen)/86400,0), neglected=if(days_since>14,1,0)\n"
            "| sort - days_since",
            "Flags backup or secondary inboxes that have not been reviewed recently.",
            "Neglected secondary accounts are where password resets, billing notices, and breach warnings can quietly pile up.",
            "Label backup or secondary accounts in inbox stats and alert when they have gone unchecked beyond your threshold.",
            "Table of secondary inboxes with days since last check and unread count.",
            "which backup email accounts have been left unchecked long enough for important notices to pile up unnoticed.",
        ),
        S(
            "Large Attachment Bloat Watch",
            "low",
            "beginner",
            ["Capacity", "Analytics"],
            "index=personal sourcetype=inbox:stats\n"
            "| stats avg(large_attachment_mb) as avg_attachment_mb, sum(large_attachment_count) as large_attachments by account\n"
            "| sort - avg_attachment_mb",
            "Shows which accounts are accumulating the heaviest attachment burden.",
            "Large attachments are an easy source of inbox drag and often explain why storage usage grows faster than expected.",
            "Send attachment-size statistics with inbox snapshots; compare average large-attachment size and count by account.",
            "Account table of average large attachment size and total count.",
            "which email accounts are filling up with bulky attachments and quietly driving storage growth.",
        ),
        S(
            "Personal Attack-Surface Scorecard",
            "high",
            "intermediate",
            ["Security", "Risk"],
            "index=personal (sourcetype=breach:alert OR sourcetype=certexpiry:check OR sourcetype=inbox:stats OR sourcetype=clouddrive:usage)\n"
            "| eval risk_points=case(sourcetype=\"breach:alert\",5,sourcetype=\"certexpiry:check\" AND days_left<14,3,sourcetype=\"inbox:stats\" AND unread_count>1000,2,sourcetype=\"clouddrive:usage\" AND used_pct>90,2,true(),0)\n"
            "| stats sum(risk_points) as risk_score by sourcetype\n"
            "| sort - risk_score",
            "Rolls several personal-cyber weak signals into a simple scorecard.",
            "A single score does not replace details, but it helps you decide when your personal digital hygiene needs attention now rather than later.",
            "Use consistent fields across personal-cyber feeds in `index=personal`; derive a lightweight scorecard from breach, certificate, inbox, and storage signals.",
            "Table of personal-cyber sourcetypes with their current risk-point contribution.",
            "a simple score showing which parts of your personal digital world are creating the most risk right now.",
        ),
    ],
    "39": [
        S(
            "Decor Setup-to-Takedown Duration",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=festive:lights\n"
            "| stats earliest(_time) as setup_time latest(_time) as takedown_time by season\n"
            "| eval days_up=round((takedown_time-setup_time)/86400,1)\n"
            "| sort - days_up",
            "Measures how long seasonal decor actually stays up each year.",
            "Knowing the real setup-to-takedown duration helps put energy use, effort, and joy into the same frame.",
            "Use first and last festive-light events as rough setup and takedown boundaries; compute days active by season.",
            "Table of seasons with total days decor stayed up.",
            "how long your seasonal decorations really stay up each year from setup to takedown.",
        ),
        S(
            "Candy Refill Velocity by Hour",
            "low",
            "beginner",
            ["Analytics", "Capacity"],
            "index=personal sourcetype=candy:counter refill=true\n"
            "| eval hour=tonumber(strftime(_time,\"%H\"))\n"
            "| stats count as refills, avg(candies_added) as avg_added by hour\n"
            "| sort hour",
            "Shows the busiest times for candy-bowl refills during seasonal events.",
            "Refill timing reveals the real traffic rush much better than the total count at the end of the night.",
            "Track refill events and quantity added in `index=personal`; summarize refill timing by hour.",
            "Hour-by-hour chart of candy refills and average candies added.",
            "what time the candy bowl needs refilling fastest, which is the clearest clue about the real rush.",
        ),
        S(
            "Countdown Milestone Reminder Drift",
            "low",
            "beginner",
            ["Availability", "Analytics"],
            "index=personal sourcetype=countdown:event milestone=*\n"
            "| stats latest(days_remaining) as days_remaining, count as reminders by milestone\n"
            "| sort days_remaining",
            "Tracks whether milestone reminders are firing at the right points in a countdown.",
            "A countdown is more fun and useful when the little markers arrive on time instead of in a blur at the end.",
            "Send milestone countdown events into `index=personal`; review reminder frequency and current days remaining by milestone.",
            "Table of milestones with reminders fired and days remaining.",
            "whether the little milestones in a countdown are turning up when they should instead of bunching awkwardly at the end.",
        ),
        S(
            "Weekend vs Weekday Festive Energy",
            "low",
            "beginner",
            ["Cost", "Analytics"],
            "index=personal sourcetype=festive:lights\n"
            "| eval day_type=if(match(strftime(_time,\"%w\"),\"0|6\"),\"weekend\",\"weekday\")\n"
            "| stats sum(kwh) as kwh, avg(hours_on) as avg_hours_on by day_type\n"
            "| eval est_cost=round(kwh*0.30,2)",
            "Compares energy use for seasonal lights on weekends versus weekdays.",
            "This helps separate normal festive fun from the extra runtime that creeps in when everyone is home longer.",
            "Ingest festive-light power readings in `index=personal`; compare weekend and weekday consumption and runtime.",
            "Two-bar comparison of festive-light energy and runtime by day type.",
            "whether festive lighting uses much more energy on weekends when it tends to stay on for longer.",
        ),
        S(
            "Santa ETA vs Bedtime Risk",
            "low",
            "beginner",
            ["Risk", "Analytics"],
            "index=personal sourcetype=santa:tracker\n"
            "| stats latest(eta_hours) as eta_hours, latest(region) as region by tracker\n"
            "| eval bedtime_risk=if(eta_hours<2,1,0)\n"
            "| sort eta_hours",
            "Adds a deliberately silly view of whether Santa's ETA is getting too close to bedtime.",
            "Novelty metrics are still useful when they build anticipation and make the countdown feel alive.",
            "Send Santa-tracker snapshots to `index=personal`; compute a bedtime-risk flag based on the latest ETA.",
            "Single-value tile of Santa ETA with bedtime-risk flag.",
            "whether Santa seems uncomfortably close to bedtime, which is exactly the kind of festive detail a countdown needs.",
        ),
        S(
            "Holiday Lights Burnout Detection",
            "low",
            "intermediate",
            ["Anomaly", "Fault"],
            "index=personal sourcetype=festive:lights\n"
            "| stats latest(current_watts) as current_watts, latest(expected_watts) as expected_watts by circuit\n"
            "| eval drop_pct=round(100*(expected_watts-current_watts)/expected_watts,1)\n"
            "| where drop_pct>20\n"
            "| sort - drop_pct",
            "Flags lighting circuits whose power draw has dropped enough to suggest failed bulbs or sections.",
            "Power draw is a quick proxy for burnout when you do not want to inspect every strand manually.",
            "Ingest festive-light readings with expected and current wattage; alert when the measured draw falls too far below plan.",
            "Table of festive circuits with expected watts, current watts, and drop percentage.",
            "which light strands probably have burnt-out sections because the power draw has dropped more than expected.",
        ),
        S(
            "Candy Bowl Quiet Spell Alert",
            "low",
            "beginner",
            ["Anomaly", "Operations"],
            "index=personal sourcetype=candy:counter dispense=true\n"
            "| bin _time span=30m\n"
            "| stats count as dispenses by _time\n"
            "| eval quiet_spell=if(dispenses=0,1,0)\n"
            "| sort - _time",
            "Shows half-hour windows where expected candy traffic suddenly stopped.",
            "A quiet spell can mean the rush is over, the bowl is empty, or the sensor setup needs a check.",
            "Track candy dispenses in `index=personal`; review empty half-hour buckets to spot lulls or issues.",
            "Timeline of candy dispenses with quiet windows highlighted.",
            "when the candy bowl suddenly goes quiet, which can mean the rush ended or the bowl needs attention.",
        ),
        S(
            "Countdown Check-In Consistency",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=countdown:event\n"
            "| bin _time span=1d\n"
            "| stats count as checkins, latest(days_remaining) as days_remaining by _time\n"
            "| sort - _time",
            "Tracks whether a seasonal countdown stays part of the routine or gets forgotten until the last minute.",
            "Consistency is what makes a countdown feel playful instead of turning into a forgotten widget.",
            "Send daily countdown interactions to `index=personal`; chart check-in count and latest days remaining over time.",
            "Daily chart of countdown check-ins against days remaining.",
            "whether you keep checking in with a countdown steadily or forget about it until the very end.",
        ),
    ],
    "40": [
        S(
            "Missing-Signal Detector by Morning",
            "medium",
            "intermediate",
            ["Data Quality", "Operations"],
            "index=personal earliest=-24h\n"
            "| stats latest(_time) as last_seen by sourcetype\n"
            "| eval age_hours=round((now()-last_seen)/3600,1)\n"
            "| where age_hours>24\n"
            "| sort - age_hours",
            "Shows which feeds failed to report in the last day and may have fallen out of your personal data picture.",
            "A digital twin is only as useful as its freshest signals, so silence is a first-class problem.",
            "Review all `index=personal` feeds daily; alert when a sourcetype has gone stale beyond one day.",
            "Table of sourcetypes with hours since last event.",
            "which parts of your personal data picture have gone silent, so the whole dashboard does not quietly rot from missing pieces.",
        ),
        S(
            "Personal Golden Signals Rollup",
            "medium",
            "intermediate",
            ["Operations", "Reliability"],
            "index=personal sourcetype=personalslo:status\n"
            "| stats avg(latency_score) as latency, avg(error_budget_pct) as error_budget, avg(saturation_pct) as saturation, avg(availability_pct) as availability by service\n"
            "| sort service",
            "Rolls up a personal version of the golden signals across the services and habits you care about most.",
            "Treating life systems like services can sound silly, but it is a sharp way to see overload, fragility, and missed expectations.",
            "Publish personal-SLO status events into `index=personal`; summarize the key golden-signal metrics per service.",
            "Service table of latency, error-budget, saturation, and availability metrics.",
            "the basic health signals for the parts of life you track, so overload and drift stand out earlier.",
        ),
        S(
            "Feed Noise and Chattiness Score",
            "low",
            "beginner",
            ["Data Quality", "Analytics"],
            "index=personal earliest=-7d\n"
            "| stats count as events by sourcetype\n"
            "| eval daily_events=round(events/7,1)\n"
            "| sort - daily_events",
            "Ranks which personal feeds generate the most event noise each day.",
            "Noisy feeds can drown out the meaningful ones and make dashboards feel busier without becoming wiser.",
            "Count events by sourcetype over the last week in `index=personal`; rank them by average daily event volume.",
            "Leaderboard of sourcetypes by average daily events.",
            "which personal feeds are the chattiest and may be creating more noise than insight.",
        ),
        S(
            "Cross-Domain Recovery Lag Finder",
            "medium",
            "intermediate",
            ["Analytics", "Resilience"],
            "index=personal sourcetype=correlation:pair\n"
            "| stats avg(lag_days) as avg_lag, avg(correlation) as avg_correlation, count as observations by left_signal right_signal\n"
            "| sort - avg_lag",
            "Shows which improvements tend to take the longest to show up somewhere else in your life data.",
            "Not every good habit pays off immediately, and a lag view helps you stay patient with the right ones.",
            "Publish lag-aware correlation summaries to `index=personal`; review average lag and correlation by signal pair.",
            "Signal-pair table of average lag days and average correlation.",
            "which good signals take the longest to ripple into other parts of your life, helping you stay patient with the right habits.",
        ),
        S(
            "Life-Area Coverage Gap Audit",
            "medium",
            "beginner",
            ["Data Quality", "Governance"],
            "index=personal earliest=-30d\n"
            "| stats count as events by domain sourcetype\n"
            "| stats dc(sourcetype) as feeds, sum(events) as events by domain\n"
            "| sort domain",
            "Shows which life areas have broad instrumentation and which are mostly blind spots.",
            "Coverage gaps matter because over-instrumenting one area and ignoring another can distort the story you tell yourself.",
            "Tag feeds by domain such as health, home, money, and hobbies; summarize feed count and event volume by domain.",
            "Domain table of contributing feeds and event counts.",
            "which areas of life you are measuring well and which ones are still mostly a blind spot.",
        ),
        S(
            "Daily Data-Latency Hotspots",
            "medium",
            "intermediate",
            ["Data Quality", "Anomaly"],
            "index=personal sourcetype=personalslo:status\n"
            "| stats latest(freshness_min) as freshness_min by service\n"
            "| where freshness_min>180\n"
            "| sort - freshness_min",
            "Flags services in your personal stack whose data is arriving too slowly to stay useful.",
            "Late data is almost as bad as missing data when you rely on dashboards for a quick daily read.",
            "Emit freshness-minutes metrics for each personal service; alert when freshness exceeds your tolerated threshold.",
            "Table of services with current freshness in minutes.",
            "which parts of your personal dashboard are arriving too late to be very useful anymore.",
        ),
        S(
            "Best-Day Recipe Scorecard",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=lifescore:daily\n"
            "| where score>=8\n"
            "| stats avg(sleep_score) as sleep_score, avg(activity_score) as activity_score, avg(focus_score) as focus_score, count as great_days",
            "Summarises the ingredients that tend to show up on your best-scoring days.",
            "People often know their bad-day triggers better than their good-day recipe; this flips the focus.",
            "Log daily life scores with contributor dimensions; aggregate the companion scores for top-performing days.",
            "Single scorecard of the average contributor mix for great days.",
            "what your best days tend to have in common, so you can build more of them on purpose.",
        ),
        S(
            "Worst-Day Triage Stack Rank",
            "medium",
            "intermediate",
            ["Analytics", "Risk"],
            "index=personal sourcetype=lifescore:daily\n"
            "| where score<=4\n"
            "| stats avg(stress_score) as stress_score, avg(sleep_score) as sleep_score, avg(recovery_score) as recovery_score, count as rough_days",
            "Summarises the factors that most commonly accompany your worst-scoring days.",
            "A triage view of bad days helps you intervene on the strongest contributors instead of guessing.",
            "Publish daily life scores with stress, sleep, and recovery contributors; aggregate the mix for low-score days.",
            "Single scorecard of average stress, sleep, and recovery values on rough days.",
            "what your worst days usually have in common, so you know where to start fixing the pattern.",
        ),
    ],
    "41": [
        S(
            "Wind Penalty on Scooter Efficiency",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            "index=personal sourcetype=scooter:trip\n"
            "| eval km_per_pct=round(distance_km/battery_used_pct,2)\n"
            "| stats avg(km_per_pct) as avg_efficiency, avg(wind_kph) as avg_wind, count as trips by wind_bucket\n"
            "| sort wind_bucket",
            "Shows how much headwind is costing you in scooter efficiency.",
            "Knowing the wind penalty helps set realistic battery expectations and route choices.",
            "Capture trip distance, battery used, and wind bucket in `index=personal`; compare efficiency by wind condition.",
            "Bar chart of scooter efficiency by wind bucket.",
            "how much windy conditions cut into your scooter range, so battery anxiety gets replaced with real data.",
        ),
        S(
            "Commute Delay by Mode and Weather",
            "medium",
            "intermediate",
            ["Analytics", "Operations"],
            "index=personal (sourcetype=ebike:ride OR sourcetype=scooter:trip)\n"
            "| eval mode=if(sourcetype=\"ebike:ride\",\"e-bike\",\"e-scooter\")\n"
            "| stats avg(duration_min) as avg_duration, avg(delay_min) as avg_delay, count as trips by mode weather_bucket\n"
            "| sort mode weather_bucket",
            "Compares commute friction across micro-mobility modes under different weather conditions.",
            "Mode choice feels intuitive, but a delay matrix makes it easier to decide what really works in poor conditions.",
            "Track trip duration, delay, and weather bucket for e-bike and scooter commutes; summarize by mode and weather.",
            "Grouped table of average commute duration and delay by mode and weather.",
            "which ride mode handles different weather best when you are just trying to get somewhere on time.",
        ),
        S(
            "E-Bike Battery Health Drift",
            "medium",
            "beginner",
            ["Analytics", "Performance"],
            "index=personal sourcetype=ebike:ride\n"
            "| timechart span=1mon avg(battery_health_pct) as battery_health\n"
            "| delta battery_health as month_change",
            "Tracks the long-term drift in e-bike battery health rather than only day-to-day range swings.",
            "Battery health determines future anxiety more than any one ride, and monthly drift keeps the story honest.",
            "Ingest ride summaries with battery-health percentage; review monthly averages and month-over-month change.",
            "Monthly line chart of average battery health.",
            "how your e-bike battery health is drifting over time, not just how one ride happened to feel.",
        ),
        S(
            "Skate Session Consistency Before New Tricks",
            "low",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=skate:session\n"
            "| stats avg(landed_pct) as landed_pct, avg(attempts) as avg_attempts, count as sessions by trick_family\n"
            "| sort - landed_pct",
            "Shows which trick families have the consistency base to justify pushing for something harder.",
            "Progress usually stalls when new tricks are layered on top of foundations that are not stable yet.",
            "Track skate sessions with trick family, attempts, and landed percentage; compare consistency by trick family.",
            "Table of trick families with landed percentage and attempt volume.",
            "which skate fundamentals are consistent enough to build harder tricks on next.",
        ),
        S(
            "Surf Paddle-to-Wave Conversion",
            "low",
            "beginner",
            ["Analytics", "Performance"],
            "index=personal sourcetype=surf:session\n"
            "| stats avg(waves_caught) as avg_waves, avg(paddle_attempts) as avg_paddles, count as sessions by board\n"
            "| eval conversion_pct=round(100*avg_waves/avg_paddles,1)\n"
            "| sort - conversion_pct",
            "Measures how efficiently paddling attempts are turning into caught waves.",
            "Conversion is a better skill signal than raw wave count because conditions can inflate or deflate the total.",
            "Send surf-session summaries with board, wave count, and paddle attempts to `index=personal`; compare conversion by board.",
            "Board table of average waves, paddle attempts, and conversion percentage.",
            "how often your paddling efforts actually turn into caught waves instead of tired arms.",
        ),
        S(
            "Snow Speed vs Fall Rate",
            "medium",
            "beginner",
            ["Safety", "Analytics"],
            "index=personal sourcetype=snow:run\n"
            "| stats avg(max_speed_kph) as avg_speed, avg(falls) as avg_falls, count as runs by slope_type\n"
            "| sort - avg_speed",
            "Compares whether more speed is simply translating into more falls on certain terrain.",
            "This keeps progression honest by showing where chasing speed may be outrunning control.",
            "Track run summaries with max speed, falls, and slope type in `index=personal`; compare safety trade-offs by terrain.",
            "Slope-type table of average speed and average falls.",
            "whether going faster on the mountain is starting to come with a bigger falling cost than you want.",
        ),
        S(
            "Weekly Mixed-Mode Distance Stack",
            "low",
            "beginner",
            ["Analytics", "Capacity"],
            "index=personal (sourcetype=ebike:ride OR sourcetype=scooter:trip)\n"
            "| eval mode=if(sourcetype=\"ebike:ride\",\"e-bike\",\"e-scooter\")\n"
            "| bin _time span=1w\n"
            "| stats sum(distance_km) as distance_km by _time mode\n"
            "| sort - _time",
            "Stacks weekly distance across the micro-mobility modes you actually use.",
            "A weekly distance split makes mode share tangible and highlights what is replacing short car trips.",
            "Collect e-bike and scooter trip distances in `index=personal`; summarize weekly totals by mode.",
            "Stacked weekly column chart of micro-mobility distance by mode.",
            "how your weekly distance is split across bikes and scooters instead of guessing which one you use more.",
        ),
        S(
            "Helmet Usage Gap by Ride Type",
            "medium",
            "beginner",
            ["Safety", "Compliance"],
            "index=personal (sourcetype=ebike:ride OR sourcetype=scooter:trip)\n"
            "| eval ride_type=if(sourcetype=\"ebike:ride\",\"e-bike\",\"e-scooter\")\n"
            "| stats count as trips, sum(eval(if(helmet_used=\"true\",1,0))) as helmet_trips by ride_type\n"
            "| eval helmet_pct=round(100*helmet_trips/trips,1)\n"
            "| sort ride_type",
            "Shows whether helmet use is slipping for one ride type more than another.",
            "Safety habits often degrade first on the trips that feel shortest or most casual.",
            "Log helmet-use flags on ride events in `index=personal`; compare usage percentage across ride types.",
            "Two-bar comparison of helmet-use percentage by ride type.",
            "whether you are getting casual about helmets on one kind of ride more than another.",
        ),
    ],
    "42": [
        S(
            "Night-Currency Window Tracker",
            "medium",
            "beginner",
            ["Compliance", "Analytics"],
            "index=personal sourcetype=flightlog:entry\n"
            "| eval days_ago=round((now()-_time)/86400,0)\n"
            "| stats sum(eval(if(days_ago<=90,night_landings,0))) as recent_night_landings\n"
            "| eval current=if(recent_night_landings>=3,\"current\",\"NOT current\")",
            "Tracks whether you are staying inside the practical window for night-currency experience.",
            "Night flying confidence decays quietly if you are not watching the recency window.",
            "Ingest flight-log entries with night-landing counts; calculate rolling night-currency status.",
            "Single-value tile of recent night landings and current/not-current status.",
            "whether your recent night flying practice is still fresh enough to stay comfortable and current.",
        ),
        S(
            "Checklist Step Most Often Missed",
            "medium",
            "beginner",
            ["Audit", "Quality"],
            "index=personal sourcetype=preflight:check completed=false\n"
            "| stats count as misses by checklist_item\n"
            "| sort - misses",
            "Ranks the pre-flight checklist steps you skip or delay most often.",
            "A recurring miss on the same item is exactly the pattern checklists exist to expose.",
            "Send checklist outcomes to `index=personal`; review the most frequently incomplete items.",
            "Top table of missed checklist items.",
            "which pre-flight checklist steps you are most likely to skip or rush, so the weak spot becomes obvious.",
        ),
        S(
            "Landing Crosswind Practice Mix",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=flightlog:entry\n"
            "| stats avg(crosswind_kts) as avg_crosswind, count as landings by runway_type\n"
            "| sort - avg_crosswind",
            "Shows how much of your recent landing practice includes meaningful crosswind exposure.",
            "Practice mix matters because calm-day landings can create false confidence for more demanding conditions.",
            "Track crosswind estimates and runway type in `index=personal`; compare average crosswind exposure across recent landings.",
            "Runway-type table of landing count and average crosswind component.",
            "how much of your landing practice really includes crosswinds instead of only easy calm-day conditions.",
        ),
        S(
            "Hobbs vs Airborne Time Divergence",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=flightlog:entry\n"
            "| eval ground_overhead=round(hobbs_hours-airborne_hours,2)\n"
            "| stats avg(ground_overhead) as avg_ground_overhead, avg(airborne_hours) as avg_airborne by aircraft_type\n"
            "| sort - avg_ground_overhead",
            "Compares how much time is being spent on the ground relative to airborne time by aircraft type.",
            "Ground overhead is not bad, but it is useful to know when it starts to dominate training efficiency or rental cost.",
            "Log Hobbs and airborne time in `index=personal`; compare average ground-overhead gap by aircraft type.",
            "Aircraft table of average ground overhead and airborne hours.",
            "how much of your logged aircraft time is really ground time rather than time in the air.",
        ),
        S(
            "Approach Type Mix Over the Month",
            "low",
            "beginner",
            ["Analytics", "Inventory"],
            "index=personal sourcetype=flightlog:entry approach_type=*\n"
            "| bin _time span=1mon\n"
            "| stats count as approaches by _time approach_type\n"
            "| sort - _time",
            "Shows whether your recent instrument or proficiency work is varied or repetitive.",
            "A diverse approach mix often builds broader readiness than repeating only the familiar type.",
            "Tag logbook entries with approach type; summarize monthly counts by approach category.",
            "Stacked monthly chart of approaches by type.",
            "which kinds of approaches you have really been practicing lately instead of what you assume from memory.",
        ),
        S(
            "Flight-Sim Emergency Procedure Reps",
            "medium",
            "beginner",
            ["Analytics", "Safety"],
            "index=personal sourcetype=flightsim:session scenario=emergency\n"
            "| bin _time span=1w\n"
            "| stats count as reps, values(procedure) as procedures by _time\n"
            "| sort - _time",
            "Tracks whether emergency scenarios are being rehearsed consistently in the simulator.",
            "Emergency procedures are exactly what repetition is for because you do not want novelty in the real event.",
            "Label sim sessions by scenario and procedure; count weekly emergency repetitions in `index=personal`.",
            "Weekly chart of emergency-procedure practice reps.",
            "how often you are actually rehearsing emergency situations in the simulator instead of just ordinary flying.",
        ),
        S(
            "Taxi Time Creep by Airport",
            "low",
            "beginner",
            ["Analytics", "Operations"],
            "index=personal sourcetype=flightlog:entry departure_airport=*\n"
            "| stats avg(taxi_out_min) as avg_taxi_out, avg(taxi_in_min) as avg_taxi_in, count as flights by departure_airport\n"
            "| sort - avg_taxi_out",
            "Shows which airports or routines are adding the most ground-time creep before takeoff.",
            "Taxi-time creep matters for fuel planning, schedule realism, and total cost even if the flight itself is short.",
            "Capture taxi-in and taxi-out minutes in `index=personal`; compare averages by departure airport.",
            "Airport table of average taxi-out and taxi-in minutes.",
            "which airports are adding the most extra ground time before or after the part of flying you actually care about.",
        ),
        S(
            "Altitude Deviation Hotspots",
            "medium",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=avionics:telemetry altitude_error_ft=*\n"
            "| stats avg(abs(altitude_error_ft)) as avg_error, max(abs(altitude_error_ft)) as max_error by flight_phase\n"
            "| sort - avg_error",
            "Shows the flight phases where altitude control is least consistent.",
            "Phase-level hotspots are more useful than a single overall number because they point to where to focus practice.",
            "Ingest avionics telemetry with altitude-error values; summarize average and max deviation by flight phase.",
            "Flight-phase table of average and maximum altitude deviation.",
            "which parts of a flight are most likely to see altitude wandering, helping you target practice more precisely.",
        ),
    ],
    "43": [
        S(
            "Anchor Settle Time After Drop",
            "medium",
            "intermediate",
            ["Analytics", "Safety"],
            "index=personal sourcetype=mooring:status state=anchored\n"
            "| stats avg(settle_min) as avg_settle_min, perc90(settle_min) as p90_settle_min, count as drops by anchorage\n"
            "| sort - avg_settle_min",
            "Tracks how long anchor setups usually take to settle and look trustworthy.",
            "Long settle times can hint at poor bottoms, rushed technique, or weather that deserves more caution.",
            "Send anchor-watch status changes to `index=personal`; compare settle times by anchorage.",
            "Anchorage table of average and p90 anchor-settle minutes.",
            "how long it usually takes an anchor setup to settle properly after you drop it.",
        ),
        S(
            "Bilge Activity After Rainy Nights",
            "medium",
            "beginner",
            ["Anomaly", "Safety"],
            "index=personal sourcetype=bilge:event rain_window=true\n"
            "| bin _time span=1d\n"
            "| stats count as pump_cycles by _time\n"
            "| sort - _time",
            "Shows whether rainy nights correlate with more bilge-pump activity the next day.",
            "This is a simple way to spot weather-linked leaks before they become a much more expensive surprise.",
            "Tag bilge events that follow rainy windows; track daily pump-cycle counts in `index=personal`.",
            "Daily chart of bilge-pump cycles after rainy nights.",
            "whether rainy nights seem to lead to more bilge pumping, which can hint at leaks or water getting in where it should not.",
        ),
        S(
            "Heel Angle Spikes vs Wind Strength",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            "index=personal sourcetype=nmea:reading\n"
            "| stats avg(abs(heel_deg)) as avg_heel, max(abs(heel_deg)) as max_heel, avg(wind_kts) as avg_wind by sail_plan\n"
            "| sort - max_heel",
            "Compares heel behaviour against wind strength and sail configuration.",
            "Heel spikes are useful feedback for comfort, speed, reefing habits, and crew confidence.",
            "Ingest NMEA readings with heel angle, wind, and sail-plan tags; compare average and peak heel by sail plan.",
            "Sail-plan table of average wind, average heel, and maximum heel.",
            "how much your boat heels under different wind and sail setups, helping you see when comfort and control start to slip.",
        ),
        S(
            "Marina Power Dependence Trend",
            "low",
            "beginner",
            ["Analytics", "Operations"],
            "index=personal sourcetype=mooring:status shore_power=true\n"
            "| bin _time span=1w\n"
            "| stats count as shore_power_sessions, sum(hours_connected) as hours_connected by _time\n"
            "| sort - _time",
            "Tracks how much time is spent dependent on marina shore power rather than self-contained systems.",
            "This is useful for understanding battery habits, marina costs, and how robust the boat feels away from the dock.",
            "Log mooring status and shore-power connection hours in `index=personal`; summarize weekly dependence.",
            "Weekly chart of shore-power sessions and hours connected.",
            "how much you are relying on marina shore power instead of the boat carrying itself comfortably.",
        ),
        S(
            "Engine Temperature Excursion Watch",
            "high",
            "beginner",
            ["Safety", "Fault"],
            "index=personal sourcetype=nmea:reading engine_temp_c=*\n"
            "| stats max(engine_temp_c) as max_temp, avg(engine_temp_c) as avg_temp by voyage_id\n"
            "| where max_temp>95\n"
            "| sort - max_temp",
            "Flags voyages where engine temperature crossed a caution threshold.",
            "A simple excursion watch catches cooling issues early, which is much cheaper than diagnosing them after a failure.",
            "Ingest NMEA engine-temperature readings into `index=personal`; alert when maximum voyage temperature exceeds your threshold.",
            "Voyage table of average and maximum engine temperature.",
            "which trips saw the engine run hotter than it should, so you catch cooling trouble early.",
        ),
        S(
            "Battery Recovery After Shore Power",
            "medium",
            "intermediate",
            ["Analytics", "Reliability"],
            "index=personal sourcetype=nmea:reading shore_power_state=*\n"
            "| stats avg(battery_voltage) as avg_voltage, latest(battery_soc_pct) as latest_soc by shore_power_state\n"
            "| sort shore_power_state",
            "Compares battery recovery when shore power is on versus off.",
            "This turns battery confidence from a guess into a measurable before-and-after view.",
            "Send battery voltage and SOC readings with shore-power state tags to `index=personal`; compare recovery metrics.",
            "Grouped battery table for shore-power on and off states.",
            "whether the batteries really recover the way you expect when shore power is connected.",
        ),
        S(
            "Crosswind Docking Practice Log",
            "medium",
            "intermediate",
            ["Analytics", "Safety"],
            "index=personal sourcetype=nmea:reading maneuver=docking\n"
            "| stats avg(crosswind_kts) as avg_crosswind, avg(docking_score) as avg_score, count as attempts by marina\n"
            "| sort - avg_crosswind",
            "Shows how much crosswind docking practice you are getting and how it is going.",
            "Docking skill improves faster when you can see the conditions you have actually practiced in rather than remembering only the awkward ones.",
            "Tag docking maneuvers in NMEA-derived sessions; compare attempt count, crosswind, and score by marina.",
            "Marina table of docking attempts, average crosswind, and docking score.",
            "how much crosswind docking practice you are really getting, not just the handful of memorable hard approaches.",
        ),
        S(
            "Passage ETA Margin vs Forecast Change",
            "medium",
            "intermediate",
            ["Risk", "Analytics"],
            "index=personal sourcetype=marineweather:forecast route=passage\n"
            "| stats min(eta_margin_hours) as min_margin, avg(wind_shift_kts) as avg_shift, count as forecasts by route_name\n"
            "| sort min_margin",
            "Shows which planned passages have the least ETA buffer once forecast changes are factored in.",
            "Margin matters because a tight passage plan becomes stressful fast when the forecast moves against you.",
            "Ingest marine-forecast snapshots tagged to routes; compare ETA margin and forecast change by passage.",
            "Route table of minimum ETA margin and average forecast shift.",
            "which passages are starting to lose their comfort margin as the forecast changes.",
        ),
    ],
    "44": [
        S(
            "Skunked Trip Streak Alert",
            "low",
            "beginner",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=fishing:catch\n"
            "| bin _time span=1d\n"
            "| stats count as catches by _time trip_id\n"
            "| eval skunked=if(catches=0,1,0)\n"
            "| streamstats current=t sum(eval(if(skunked=1,1,0))) as skunk_streak reset_after=\"(skunked=0)\"\n"
            "| sort - _time",
            "Tracks consecutive outings with no catches so a frustrating run is visible rather than just felt.",
            "A skunk streak can mean conditions, technique, or spots need changing instead of more stubborn repetition.",
            "Summarize catches by trip in `index=personal`; maintain a streak count for catchless outings.",
            "Trip-by-trip streak chart for skunked outings.",
            "how many fishing trips in a row come up empty, which is a clear sign something may need changing.",
        ),
        S(
            "Catch Weight Trend by Tackle",
            "low",
            "beginner",
            ["Analytics", "Performance"],
            "index=personal sourcetype=fishing:catch\n"
            "| stats avg(weight_kg) as avg_weight, max(weight_kg) as best_weight, count as catches by tackle\n"
            "| sort - avg_weight",
            "Shows which tackle setups are producing heavier catches over time.",
            "This keeps tackle decisions grounded in results instead of stories about what should have worked.",
            "Log tackle used and catch weight in `index=personal`; compare average and best catch weight by setup.",
            "Tackle table of average weight, best weight, and catch count.",
            "which tackle setups really produce the heavier catches instead of only feeling lucky on a good day.",
        ),
        S(
            "Moon Phase vs Catch Success",
            "low",
            "intermediate",
            ["Analytics"],
            "index=personal sourcetype=fishing:catch moon_phase=*\n"
            "| stats count as catches, avg(weight_kg) as avg_weight by moon_phase\n"
            "| sort - catches",
            "Compares catch success across logged moon phases without pretending folklore is automatically true.",
            "If there is a pattern for your waters and species, this is how to earn it rather than assume it.",
            "Include moon-phase context on catch logs; summarize count and average weight by phase.",
            "Bar chart of catches by moon phase with average weight overlay.",
            "whether your catch results really seem to change with the moon phase or only feel that way.",
        ),
        S(
            "Sonar Depth Band with Best Hookups",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            "index=personal sourcetype=fishfinder:reading\n"
            "| stats avg(fish_density) as avg_density, count as pings by depth_band\n"
            "| sort - avg_density",
            "Shows which depth bands most consistently show promising sonar activity before hookups.",
            "A depth-band view helps turn sonar from a moving picture into something you can use on the next drift or cast.",
            "Bucket fishfinder readings into depth bands in `index=personal`; compare average density and ping volume by band.",
            "Depth-band table of average fish density and ping count.",
            "which depths most often show the sonar activity that leads to better chances of a hookup.",
        ),
        S(
            "Foraging Patch Revisit Cooldown",
            "low",
            "beginner",
            ["Analytics", "Governance"],
            "index=personal sourcetype=foraging:find patch_id=*\n"
            "| stats latest(_time) as last_visit, count as visits by patch_id species\n"
            "| eval days_since=round((now()-last_visit)/86400,0)\n"
            "| sort days_since",
            "Tracks how long it has been since each patch was last revisited.",
            "A revisit cooldown helps avoid over-harvesting the same spot just because it is familiar and easy.",
            "Log foraging finds with patch identifiers; review days since last visit by patch and species.",
            "Patch table of visit count and days since last revisit.",
            "how long each foraging patch has been left to recover before you go back again.",
        ),
        S(
            "Trail-Cam Dawn/Dusk Shift",
            "low",
            "beginner",
            ["Analytics", "Anomaly"],
            "index=personal sourcetype=gamecam:trigger\n"
            "| eval daypart=if(tonumber(strftime(_time,\"%H\"))<12,\"dawn\",\"dusk\")\n"
            "| stats count as triggers by species daypart\n"
            "| sort - triggers",
            "Shows whether game-camera activity is shifting between dawn and dusk windows.",
            "Small seasonal changes in timing can tell you as much as total activity when planning observation or trips.",
            "Send trail-camera triggers to `index=personal`; compare species activity counts by dawn and dusk buckets.",
            "Species-by-daypart table of trail-camera triggers.",
            "whether wildlife around your camera is becoming more active at dawn or dusk as the season shifts.",
        ),
        S(
            "Species Diversity per Outing",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=fishing:catch\n"
            "| stats dc(species) as species_count, count as total_catches by trip_id\n"
            "| sort - species_count",
            "Tracks which outings produce diversity rather than only volume.",
            "Some trips are valuable because they are rich and varied even if no personal best shows up.",
            "Group catch logs by trip in `index=personal`; calculate distinct species count and total catches.",
            "Trip table of total catches and distinct species count.",
            "which fishing trips are the most varied, not just the ones with the highest number of fish.",
        ),
        S(
            "Baitfish Presence Before the Bite Window",
            "low",
            "intermediate",
            ["Analytics", "Performance"],
            "index=personal sourcetype=fishfinder:reading baitfish_present=true\n"
            "| bin _time span=30m\n"
            "| stats count as baitfish_pings, avg(water_temp_c) as avg_temp by _time\n"
            "| sort - _time",
            "Shows when baitfish presence starts building before a better bite window.",
            "A lead indicator is often more actionable than only logging the catch after the fact.",
            "Track baitfish detections from sonar in `index=personal`; chart half-hour presence counts and water temperature.",
            "Half-hour timeline of baitfish detections and water temperature.",
            "when baitfish start showing up before the stronger bite window, giving you an earlier clue to stay put or start fishing harder.",
        ),
    ],
    "45": [
        S(
            "Warm-Up Time vs Practice Quality",
            "low",
            "beginner",
            ["Analytics", "Quality"],
            "index=personal sourcetype=practice:session\n"
            "| stats avg(quality_score) as avg_quality, avg(minutes) as avg_minutes, count as sessions by warmup_bucket\n"
            "| sort warmup_bucket",
            "Compares whether longer or more deliberate warm-ups correlate with better practice sessions.",
            "Warm-ups are easy to skip when rushed, but the data can show whether they actually improve the session quality.",
            "Track practice sessions with warmup buckets and quality scores; compare average quality by warmup profile.",
            "Warmup-bucket table of average practice quality and minutes.",
            "whether giving yourself a better warm-up really leads to better practice afterwards.",
        ),
        S(
            "Practice Start-Time Consistency",
            "low",
            "beginner",
            ["Analytics", "Reliability"],
            "index=personal sourcetype=practice:session\n"
            "| eval hour=tonumber(strftime(_time,\"%H\")), day=strftime(_time,\"%a\")\n"
            "| stats avg(hour) as avg_start_hour, count as sessions by day\n"
            "| sort day",
            "Shows whether practice starts at a dependable time or keeps drifting around.",
            "Consistent start times are often the hidden backbone of a durable creative routine.",
            "Send practice-session events to `index=personal`; compare average start hour and session count by weekday.",
            "Weekday table of average practice start hour.",
            "whether your practice habit has a dependable start time or keeps sliding around the week.",
        ),
        S(
            "Song Retirement Risk from Setlist Absence",
            "low",
            "intermediate",
            ["Inventory", "Risk"],
            "index=personal sourcetype=setlist:play song=*\n"
            "| stats latest(_time) as last_played, count as plays by song\n"
            "| eval days_since=round((now()-last_played)/86400,0)\n"
            "| where days_since>60\n"
            "| sort - days_since",
            "Flags songs that have quietly vanished from rotation long enough to risk getting rusty.",
            "Setlist absence is how pieces fade out of live readiness even when you still think you know them.",
            "Log setlist performances into `index=personal`; alert when a song has not appeared for your chosen interval.",
            "Song table of play count and days since last setlist appearance.",
            "which songs have been absent from the setlist long enough to start getting rusty.",
        ),
        S(
            "Demo Backlog and Unfinished Projects",
            "medium",
            "beginner",
            ["Inventory", "Operations"],
            "index=personal sourcetype=daw:session project_status!=finished\n"
            "| stats count as sessions, latest(last_touched_days) as last_touched_days by project_name project_status\n"
            "| sort - last_touched_days",
            "Lists unfinished DAW projects and how long they have been waiting for attention.",
            "A demo backlog is normal, but neglected projects pile up faster than most creators realise.",
            "Track DAW sessions with project name and status; review unfinished work by age since last touch.",
            "Project table of unfinished demos ranked by days since last touched.",
            "which music projects are still unfinished and how long they have been sitting there waiting.",
        ),
        S(
            "Stream-to-Save Conversion Trend",
            "medium",
            "beginner",
            ["Business", "Revenue Assurance"],
            "index=personal sourcetype=release:stats\n"
            "| bin _time span=1w\n"
            "| stats sum(streams) as streams, sum(saves) as saves by _time\n"
            "| eval save_rate=round(100*saves/streams,2)\n"
            "| sort - _time",
            "Tracks whether listeners are converting from casual streams into stronger save behaviour.",
            "Save rate is often a better retention signal than raw stream volume because it hints at real resonance.",
            "Ingest release statistics to `index=personal`; chart weekly streams, saves, and save-rate percentage.",
            "Weekly line chart of stream-to-save conversion.",
            "whether people are only sampling the music or actually saving it because it stuck with them.",
        ),
        S(
            "Rehearsal Gap Before Gig",
            "medium",
            "beginner",
            ["Risk", "Operations"],
            "index=personal sourcetype=setlist:play event_type=rehearsal\n"
            "| stats latest(_time) as last_rehearsal by upcoming_gig\n"
            "| eval days_since=round((now()-last_rehearsal)/86400,0)\n"
            "| sort - days_since",
            "Shows how long it has been since the last rehearsal for each upcoming gig.",
            "The rehearsal gap is a quick signal of whether performance confidence is being earned or assumed.",
            "Tag rehearsal setlists with the upcoming-gig identifier; compute days since the last rehearsal in Splunk.",
            "Table of upcoming gigs with days since last rehearsal.",
            "how long each upcoming gig has been going without a proper rehearsal refresh.",
        ),
        S(
            "Revision Churn Before Final Bounce",
            "medium",
            "intermediate",
            ["Analytics", "Quality"],
            "index=personal sourcetype=daw:session\n"
            "| stats avg(edit_count) as avg_edits, max(edit_count) as max_edits, count as sessions by project_name\n"
            "| sort - max_edits",
            "Shows which projects are bouncing around in revision churn instead of converging toward release.",
            "Too many edit cycles can be a sign of perfectionism, unclear direction, or a mix that keeps resisting closure.",
            "Ingest DAW session summaries with edit counts; compare average and maximum edit churn by project.",
            "Project table of average and maximum edit counts.",
            "which songs keep getting revised over and over instead of moving toward a finished bounce.",
        ),
        S(
            "Audience Return Cities from Repeated Setlists",
            "low",
            "intermediate",
            ["Business", "Analytics"],
            "index=personal sourcetype=setlist:play city=*\n"
            "| stats count as songs_played, dc(show_id) as shows by city\n"
            "| sort - shows",
            "Shows which cities see you repeatedly enough to suggest an audience worth nurturing.",
            "Repeated city appearance is a simple proxy for where live momentum may actually be building.",
            "Track show and setlist events with city fields in `index=personal`; summarize repeated appearance by city.",
            "City table of shows played and songs performed.",
            "which cities keep seeing your shows often enough that a real returning audience may be forming.",
        ),
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
