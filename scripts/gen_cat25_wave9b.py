#!/usr/bin/env python3
"""Generate cat-25 wave 9b use cases for subcategories 25.86-25.100."""
from __future__ import annotations

import json
from pathlib import Path

from gen_cat25_common import Cat25Writer, R
from gen_cat25_wave8a import G, S

EXPECTED_PER_SUB = 28
TARGET_SUBS = tuple(str(i) for i in range(86, 101))
METADATA_PATH = Path(__file__).resolve().with_name("wave9b_subcategories.json")

REF_OPENDENTAL = ("Open Dental API Specification", "https://www.opendental.com/site/apispecification.html")
REF_ZOCDOC = ("Zocdoc for Developers", "https://www.zocdoc.com/about/api/")
REF_WITHINGS = ("Withings Developer Portal", "https://developer.withings.com/")
REF_SIMPLEPRACTICE = ("SimplePractice", "https://www.simplepractice.com/")
REF_HEADWAY = ("Headway", "https://headway.co/")
REF_BETTERHELP = ("BetterHelp", "https://www.betterhelp.com/")
REF_DAYLIO = ("Daylio", "https://daylio.net/")
REF_MEDBRIDGE = ("MedBridge", "https://www.medbridgeeducation.com/")
REF_HINGEHEALTH = ("Hinge Health", "https://www.hingehealth.com/")
REF_BRIGHTWHEEL = ("brightwheel", "https://mybrightwheel.com/")
REF_PROCARE = ("Procare Solutions", "https://www.procaresoftware.com/")
REF_HUCKLEBERRY = ("Huckleberry", "https://huckleberrycare.com/")
REF_MEALIME = ("Mealime", "https://www.mealime.com/")
REF_ANYLIST = ("AnyList", "https://www.anylist.com/")
REF_INSTACART = ("Instacart Connect API", "https://docs.instacart.com/")
REF_PAPRIKA = ("Paprika Recipe Manager", "https://www.paprikaapp.com/")
REF_SLOPES = ("Slopes", "https://getslopes.com/")
REF_SKITRACKS = ("Ski Tracks", "https://www.corecoders.com/skitracks/")
REF_ONTHESNOW = ("OnTheSnow", "https://www.onthesnow.com/")
REF_IKON = ("Ikon Pass", "https://www.ikonpass.com/")
REF_DOWNDOG = ("Down Dog", "https://www.downdogapp.com/")
REF_PELOTON = ("Peloton Developer Portal", "https://developer.onepeloton.com/")
REF_GLO = ("Glo", "https://www.glo.com/")
REF_TRAININGPEAKS = ("TrainingPeaks API", "https://www.trainingpeaks.com/")
REF_GARMIN = ("Garmin Developer Program", "https://developer.garmin.com/")
REF_TRIDOT = ("TriDot", "https://www.tridot.com/")
REF_MONICA = ("Monica CRM", "https://www.monicahq.com/")
REF_CLAY = ("Clay", "https://clay.earth/")
REF_LINKEDIN = ("LinkedIn API Documentation", "https://learn.microsoft.com/en-us/linkedin/")
REF_AMAZON = ("Amazon Product Advertising API", "https://webservices.amazon.com/paapi5/documentation/")
REF_USPS = ("USPS Change of Address", "https://www.usps.com/manage/forward.htm")
REF_STOCKX = ("StockX Developer Portal", "https://stockx.com/about/api")
REF_GOAT = ("GOAT", "https://www.goat.com/")
REF_FASTF1 = ("FastF1 Python API", "https://docs.fastf1.dev/")
REF_ERGAST = ("Ergast F1 API", "http://ergast.com/mrd/")
REF_F1FANTASY = ("F1 Fantasy", "https://fantasy.formula1.com/")
REF_ANTENNAPOD = ("AntennaPod", "https://antennapod.org/")
REF_AUDIBLE = ("Audible", "https://www.audible.com/")
REF_GOODREADS = ("Goodreads API", "https://www.goodreads.com/api")

SUBCATEGORIES: list[dict[str, object]] = [
    {
        "id": "86",
        "name": "Dental, Vision & Preventive Care",
        "app": "Open Dental appointment exports, Zocdoc booking webhooks, vision prescription sidecars, dental hygiene visit logs, and Withings Vision eye-health readings streamed into Splunk HEC under `index=personal`.",
        "ds": "Open Dental appointments (`opendental:appointment`), Zocdoc bookings (`zocdoc:booking`), vision prescriptions (`vision:prescription`), dental hygiene visits (`dental:hygiene`), and Withings eye-health checks (`withings:eye`).",
        "refs": R(REF_OPENDENTAL, REF_ZOCDOC, REF_WITHINGS),
        "sources": [
            {"label": "Open Dental Appointment", "friendly": "Open Dental appointment", "st": "opendental:appointment", "group_field": "provider_name", "group_desc": "provider name", "value_field": "copay_usd", "value_title": "Copay", "duration_field": "wait_minutes", "duration_title": "Wait Time", "status_field": "appt_status", "sync_hours": 168},
            {"label": "Zocdoc Booking", "friendly": "Zocdoc booking", "st": "zocdoc:booking", "group_field": "specialty", "group_desc": "specialty", "value_field": "provider_rating", "value_title": "Provider Rating", "duration_field": "lead_time_hours", "duration_title": "Lead Time", "status_field": "booking_status", "sync_hours": 168},
            {"label": "Vision Prescription", "friendly": "vision prescription", "st": "vision:prescription", "group_field": "optometrist", "group_desc": "optometrist", "value_field": "sphere_delta", "value_title": "Sphere Change", "duration_field": "exam_minutes", "duration_title": "Exam Time", "status_field": "rx_status", "sync_hours": 720},
            {"label": "Dental Hygiene Visit", "friendly": "dental hygiene visit", "st": "dental:hygiene", "group_field": "hygienist_name", "group_desc": "hygienist", "value_field": "plaque_score", "value_title": "Plaque Score", "duration_field": "cleaning_minutes", "duration_title": "Cleaning Time", "status_field": "visit_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": ["withings:eye"],
        "specials": [
            S("Withings Vision Score Trend", "medium", "intermediate", ["Analytics", "Patient Safety"],
              ("index=personal sourcetype=withings:eye eye_score=*", "| timechart span=1mon avg(eye_score) as avg_score, min(eye_score) as worst_score", "| fillnull value=0"),
              "Trends monthly average and worst Withings Vision eye-health scores from home screening exports.",
              "Gradual vision-score drift is easier to act on when you see it as a trend instead of one isolated reading.",
              "Export Withings Vision results with `eye_score` and schedule a monthly review against your optometrist baseline.",
              "Line chart of monthly average and worst eye score.", "whether your at-home eye scores are slowly getting better or worse over the months."),
            S("Preventive Cleaning Interval Breach", "medium", "intermediate", ["Operations", "Risk"],
              ("index=personal sourcetype=dental:hygiene patient_id=* visit_date=*", "| stats max(visit_date) as last_cleaning by patient_id", "| eval days_since=round((now()-strptime(last_cleaning,\"%Y-%m-%d\"))/86400,0)", "| where days_since>180", "| sort - days_since"),
              "Flags patients whose last recorded dental hygiene visit is more than six months ago.",
              "Preventive gaps are cheaper to close when the overdue interval is visible before discomfort forces an emergency visit.",
              "Emit one `dental:hygiene` event per visit with `patient_id` and ISO `visit_date`, then alert when the interval exceeds your target.",
              "Table of patients by days since last cleaning.", "who is overdue for a teeth cleaning based on your last recorded visit."),
            S("Vision Prescription Expiry Watch", "high", "beginner", ["Compliance", "Risk"],
              ("index=personal sourcetype=vision:prescription rx_expiry_date=*", "| eval days_to_expiry=round((strptime(rx_expiry_date,\"%Y-%m-%d\")-now())/86400,0)", "| where days_to_expiry<=60 AND days_to_expiry>=0", "| sort days_to_expiry", "| table patient_id optometrist rx_expiry_date days_to_expiry"),
              "Lists vision prescriptions expiring within the next sixty days so renewals can be scheduled early.",
              "Expired prescriptions delay new glasses orders and can leave you driving with outdated correction.",
              "Include `rx_expiry_date` on each prescription export and run weekly during open-enrollment or back-to-school windows.",
              "Table of prescriptions sorted by days until expiry.", "which eyeglass prescriptions are about to expire so you can renew them in time."),
            S("Dental vs Vision Appointment Balance", "low", "intermediate", ["Analytics", "Operations"],
              ("(index=personal sourcetype=opendental:appointment) OR (index=personal sourcetype=vision:prescription)", "| eval care_type=case(sourcetype=\"opendental:appointment\",\"dental\",sourcetype=\"vision:prescription\",\"vision\",1=1,\"other\")", "| bin _time span=1q", "| stats count as visits by _time care_type", "| chart sum(visits) over _time by care_type"),
              "Compares quarterly dental and vision preventive activity so one side of care does not get neglected.",
              "Preventive care often clusters on whichever appointment hurt last; a balance view keeps both on calendar.",
              "Forward Open Dental and vision prescription events into `index=personal` and review the quarterly split together.",
              "Stacked column chart of visits by quarter and care type.", "whether you are keeping up with both dental and eye checkups or letting one slip."),
        ],
    },
    {
        "id": "87",
        "name": "Therapy & Mental Health Care",
        "app": "SimplePractice session notes, Headway appointment confirmations, BetterHelp messaging sessions, CBT homework trackers, and Daylio mood exports ingested into Splunk HEC.",
        "ds": "SimplePractice therapy sessions (`simplepractice:session`), Headway appointments (`headway:appointment`), BetterHelp sessions (`betterhelp:session`), CBT homework logs (`cbt:homework`), and Daylio mood entries (`daylio:mood`).",
        "refs": R(REF_SIMPLEPRACTICE, REF_HEADWAY, REF_BETTERHELP, REF_DAYLIO),
        "sources": [
            {"label": "SimplePractice Session", "friendly": "SimplePractice therapy session", "st": "simplepractice:session", "group_field": "therapist_name", "group_desc": "therapist", "value_field": "session_fee_usd", "value_title": "Session Fee", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 168},
            {"label": "Headway Appointment", "friendly": "Headway appointment", "st": "headway:appointment", "group_field": "provider_name", "group_desc": "provider", "value_field": "copay_usd", "value_title": "Copay", "duration_field": "lead_days", "duration_title": "Booking Lead Time", "status_field": "appt_status", "sync_hours": 168},
            {"label": "BetterHelp Session", "friendly": "BetterHelp session", "st": "betterhelp:session", "group_field": "counselor_name", "group_desc": "counselor", "value_field": "message_count", "value_title": "Messages Exchanged", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 72},
            {"label": "CBT Homework Log", "friendly": "CBT homework log", "st": "cbt:homework", "group_field": "worksheet_name", "group_desc": "worksheet", "value_field": "completion_pct", "value_title": "Completion Percent", "duration_field": "time_minutes", "duration_title": "Time Spent", "status_field": "homework_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["daylio:mood"],
        "specials": [
            S("Daylio Mood Lift After Therapy Week", "low", "advanced", ["Analytics", "Patient Safety"],
              ("index=personal sourcetype=daylio:mood mood_rating=*", "| bin _time span=1w", "| stats avg(mood_rating) as avg_mood, count as entries by _time", "| join type=left _time [search index=personal sourcetype=simplepractice:session | bin _time span=1w | stats count as therapy_sessions by _time]", "| eval therapy_week=if(therapy_sessions>0,1,0)", "| stats avg(avg_mood) as avg_mood by therapy_week"),
              "Compares average Daylio mood ratings on weeks with at least one logged therapy session versus weeks without.",
              "Seeing whether therapy weeks correlate with better mood helps you judge consistency, not just attendance.",
              "Export Daylio entries with numeric `mood_rating` and align weekly bins with SimplePractice session counts.",
              "Side-by-side bar chart of average mood by therapy week flag.", "whether your mood scores tend to look better in weeks when you actually had therapy."),
            S("CBT Homework Completion Streak", "medium", "intermediate", ["Operations", "Quality"],
              ("index=personal sourcetype=cbt:homework completion_pct=*", "| eval completed=if(completion_pct>=80,1,0)", "| sort 0 _time", "| streamstats count as streak reset=eval(completed=0)", "| stats max(streak) as longest_streak, avg(completion_pct) as avg_completion"),
              "Finds the longest run of CBT homework assignments completed at or above eighty percent.",
              "Homework streaks turn abstract therapy goals into a concrete habit you can celebrate or troubleshoot.",
              "Log each worksheet with `completion_pct` and review streak length during weekly check-ins with your therapist.",
              "Single-value tile for longest streak with average completion percentage.", "your longest stretch of actually finishing CBT homework instead of skipping it."),
            S("Missed Therapy Session Rate", "high", "intermediate", ["Reliability", "Operations"],
              ("index=personal sourcetype=simplepractice:session session_status=*", "| eval missed=if(match(lower(session_status),\"no.?show|cancelled|missed\"),1,0)", "| stats sum(missed) as missed_sessions, count as total_sessions by therapist_name", "| eval missed_pct=round(100*missed_sessions/total_sessions,1)", "| sort - missed_pct"),
              "Measures how often scheduled therapy sessions end up cancelled or marked as no-shows by therapist.",
              "Missed-session patterns reveal scheduling friction, avoidance cycles, or providers that do not fit your rhythm.",
              "Normalize `session_status` across SimplePractice and Headway exports and review monthly missed rates.",
              "Bar chart of missed-session percentage by therapist.", "how often therapy appointments get cancelled or missed instead of happening."),
            S("Monthly Mental Health Copay Spend", "medium", "beginner", ["Cost", "Analytics"],
              ("(index=personal sourcetype=simplepractice:session) OR (index=personal sourcetype=headway:appointment)", "| eval copay=coalesce(session_fee_usd,copay_usd,0)", "| bin _time span=1mon", "| stats sum(copay) as monthly_copay_usd, count as sessions by _time", "| sort - _time"),
              "Totals monthly out-of-pocket copays across in-person and Headway therapy appointments.",
              "Copay visibility prevents surprise cash-flow hits and helps you compare telehealth versus in-office costs.",
              "Include fee or copay fields on every session event and chart monthly totals against your benefits budget.",
              "Column chart of monthly copay spend with session count overlay.", "how much you spent each month on therapy copays so the cost never sneaks up on you."),
        ],
    },
    {
        "id": "88",
        "name": "Physical Therapy & Rehab",
        "app": "MedBridge exercise completions, clinic PT session exports, Hinge Health digital sessions, ROM measurement logs, and pain diary entries forwarded to Splunk HEC.",
        "ds": "MedBridge exercises (`medbridge:exercise`), PT clinic sessions (`pt:session`), Hinge Health sessions (`hingehealth:session`), rehab range-of-motion logs (`rehab:rom`), and pain diary entries (`pain:diary`).",
        "refs": R(REF_MEDBRIDGE, REF_HINGEHEALTH),
        "sources": [
            {"label": "MedBridge Exercise", "friendly": "MedBridge exercise", "st": "medbridge:exercise", "group_field": "exercise_name", "group_desc": "exercise", "value_field": "reps_completed", "value_title": "Reps Completed", "duration_field": "exercise_minutes", "duration_title": "Exercise Time", "status_field": "completion_status", "sync_hours": 72},
            {"label": "PT Clinic Session", "friendly": "PT clinic session", "st": "pt:session", "group_field": "therapist_name", "group_desc": "therapist", "value_field": "pain_score", "value_title": "Pain Score", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 168},
            {"label": "Hinge Health Session", "friendly": "Hinge Health session", "st": "hingehealth:session", "group_field": "program_name", "group_desc": "program", "value_field": "completion_pct", "value_title": "Completion Percent", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 72},
            {"label": "Rehab ROM Measurement", "friendly": "rehab range-of-motion", "st": "rehab:rom", "group_field": "joint_name", "group_desc": "joint", "value_field": "rom_degrees", "value_title": "ROM Degrees", "duration_field": "measurement_seconds", "duration_title": "Measurement Time", "status_field": "measurement_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["pain:diary"],
        "specials": [
            S("Pain Score Trend vs Exercise Volume", "medium", "advanced", ["Analytics", "Patient Safety"],
              ("(index=personal sourcetype=pain:diary pain_level=*) OR (index=personal sourcetype=medbridge:exercise)", "| bin _time span=1w", "| eval pain_events=if(sourcetype=\"pain:diary\",pain_level,null()), exercise_events=if(sourcetype=\"medbridge:exercise\",1,0)", "| stats avg(pain_events) as avg_pain, sum(exercise_events) as exercises by _time", "| sort _time"),
              "Lines up weekly average pain-diary scores with MedBridge exercise completion counts.",
              "When pain rises while exercise volume drops, you catch a rehab backslide before it becomes a reinjury.",
              "Export Daylio-style pain levels to `pain:diary` and align weekly bins with MedBridge exercise events.",
              "Dual-axis chart of weekly average pain and exercise count.", "whether your pain scores and exercise homework are moving in the right direction together."),
            S("ROM Improvement Since Baseline", "medium", "intermediate", ["Performance", "Patient Safety"],
              ("index=personal sourcetype=rehab:rom joint_name=* rom_degrees=*", "| eventstats earliest(rom_degrees) as baseline_rom by joint_name", "| stats latest(rom_degrees) as current_rom, max(baseline_rom) as baseline_rom by joint_name", "| eval improvement_deg=round(current_rom-baseline_rom,1)", "| sort - improvement_deg"),
              "Compares latest range-of-motion readings against the first recorded baseline for each joint.",
              "ROM delta is the clearest proof that rehab homework is paying off, not just that sessions happened.",
              "Log `rom_degrees` and `joint_name` at intake and after each home measurement session.",
              "Table of joints with baseline, current ROM, and degree improvement.", "how much more you can move each joint compared with when rehab started."),
            S("Home Program Adherence Gap", "high", "intermediate", ["Operations", "Compliance"],
              ("index=personal sourcetype=hingehealth:session program_name=* completion_pct=*", "| stats avg(completion_pct) as avg_completion, count as sessions by program_name", "| eval adherence_gap=round(100-avg_completion,1)", "| where adherence_gap>25", "| sort - adherence_gap"),
              "Highlights Hinge Health programs whose average completion percentage falls materially below full adherence.",
              "Digital PT only works when sessions actually get finished; partial completions hide quiet dropout.",
              "Capture `completion_pct` on every Hinge Health session and review programs with large adherence gaps weekly.",
              "Bar chart of adherence gap percentage by program.", "which rehab programs you keep starting but not quite finishing."),
            S("PT Session Pain Spike Detection", "high", "advanced", ["Anomaly", "Patient Safety"],
              ("index=personal sourcetype=pt:session pain_score=* session_minutes=*", "| sort 0 _time", "| streamstats current=f last(pain_score) as prev_pain by body_region", "| eval pain_delta=pain_score-prev_pain", "| where pain_delta>=3", "| table _time body_region therapist_name pain_score prev_pain pain_delta"),
              "Flags in-clinic PT sessions where pain jumped three or more points versus the previous visit for the same body region.",
              "Sudden pain spikes after supervised sessions may signal flare-ups, poor load progression, or technique issues.",
              "Include `pain_score` and `body_region` on each `pt:session` event and alert when delta exceeds your threshold.",
              "Table of sessions with pain spike magnitude and body region.", "when a PT visit left you noticeably more sore than the last time for that body part."),
        ],
    },
    {
        "id": "89",
        "name": "Childcare & Early Years",
        "app": "brightwheel check-in exports, Procare attendance logs, Huckleberry sleep tracking, daycare incident reports, and nanny timesheet entries streamed into Splunk HEC.",
        "ds": "brightwheel check-ins (`brightwheel:checkin`), Procare attendance (`procare:attendance`), Huckleberry sleep logs (`huckleberry:sleep`), daycare incidents (`daycare:incident`), and nanny timesheets (`nanny:timesheet`).",
        "refs": R(REF_BRIGHTWHEEL, REF_PROCARE, REF_HUCKLEBERRY),
        "sources": [
            {"label": "brightwheel Check-In", "friendly": "brightwheel check-in", "st": "brightwheel:checkin", "group_field": "classroom", "group_desc": "classroom", "value_field": "checkin_count", "value_title": "Daily Check-Ins", "duration_field": "minutes_early", "duration_title": "Early Drop-Off", "status_field": "checkin_status", "sync_hours": 48},
            {"label": "Procare Attendance", "friendly": "Procare attendance", "st": "procare:attendance", "group_field": "child_name", "group_desc": "child", "value_field": "hours_present", "value_title": "Hours Present", "duration_field": "minutes_late", "duration_title": "Late Pickup", "status_field": "attendance_status", "sync_hours": 48},
            {"label": "Huckleberry Sleep Log", "friendly": "Huckleberry sleep log", "st": "huckleberry:sleep", "group_field": "child_name", "group_desc": "child", "value_field": "total_sleep_hours", "value_title": "Sleep Hours", "duration_field": "night_wakings", "duration_title": "Night Wakings", "status_field": "sleep_quality", "sync_hours": 72},
            {"label": "Daycare Incident Report", "friendly": "daycare incident report", "st": "daycare:incident", "group_field": "incident_type", "group_desc": "incident type", "value_field": "severity_score", "value_title": "Severity Score", "duration_field": "resolution_minutes", "duration_title": "Resolution Time", "status_field": "incident_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["nanny:timesheet"],
        "specials": [
            S("Nanny Hours vs Contracted Weekly Cap", "medium", "intermediate", ["Cost", "Operations"],
              ("index=personal sourcetype=nanny:timesheet hours_worked=*", "| bin _time span=1w", "| stats sum(hours_worked) as weekly_hours by _time caregiver_name", "| eval over_cap=if(weekly_hours>40,weekly_hours-40,0)", "| where over_cap>0", "| sort - over_cap"),
              "Detects weeks where logged nanny timesheet hours exceed a forty-hour contracted cap.",
              "Overtime in childcare billing adds up fast; a weekly cap view keeps invoices predictable.",
              "Export nanny timesheets with `hours_worked` and `caregiver_name`, then alert when weekly totals exceed your contract.",
              "Table of weeks and caregivers with overtime hours.", "when nanny hours went over the weekly limit you planned for."),
            S("Sleep Debt After Late Pickups", "low", "advanced", ["Analytics", "Patient Safety"],
              ("(index=personal sourcetype=procare:attendance minutes_late=*) OR (index=personal sourcetype=huckleberry:sleep total_sleep_hours=*)", "| bin _time span=1d", "| stats max(minutes_late) as max_late, avg(total_sleep_hours) as avg_sleep by _time child_name", "| where max_late>15", "| sort - max_late"),
              "Correlates days with late Procare pickups against that night's Huckleberry sleep totals.",
              "Late pickups can push bedtime routines; seeing the sleep hit helps you adjust schedules or backup care.",
              "Align daily attendance and sleep exports by `child_name` and review days where pickup ran more than fifteen minutes late.",
              "Scatter plot of late pickup minutes versus sleep hours.", "whether nights after late daycare pickups tend to come with less sleep."),
            S("Incident Severity Trend by Classroom", "high", "intermediate", ["Risk", "Analytics"],
              ("index=personal sourcetype=daycare:incident severity_score=* classroom=*", "| timechart span=1mon avg(severity_score) as avg_severity, count as incidents by classroom", "| fillnull value=0"),
              "Trends monthly average incident severity and count by daycare classroom.",
              "A rising severity trend in one room is worth a conversation even when total incident counts look flat.",
              "Include `severity_score` and `classroom` on every incident export and review monthly classroom trends.",
              "Multi-series line chart of average severity by classroom.", "whether any classroom is seeing rougher incidents over time."),
            S("Check-In Missing Day Alert", "high", "beginner", ["Availability", "Operations"],
              ("index=personal sourcetype=brightwheel:checkin child_name=*", "| bin _time span=1d", "| stats count as checkins by _time child_name", "| join type=left child_name [search index=personal sourcetype=procare:attendance | stats dc(_time) as expected_days by child_name]", "| where checkins=0 AND expected_days>0", "| sort child_name"),
              "Finds children with Procare attendance but zero brightwheel check-ins on the same calendar day.",
              "Mismatched feeds often mean a parent app stopped syncing even though the child was present.",
              "Compare daily brightwheel check-in counts with Procare attendance by child and alert on zero-check-in days.",
              "Table of child-day rows with missing check-ins.", "when a child was at care but the check-in app never recorded it."),
        ],
    },
    {
        "id": "90",
        "name": "Meal Planning & Grocery",
        "app": "Mealime weekly plans, AnyList grocery lists, Instacart order history, Paprika recipe exports, and pantry inventory scans ingested into Splunk HEC.",
        "ds": "Mealime meal plans (`mealime:plan`), AnyList grocery lists (`anylist:grocery`), Instacart orders (`instacart:order`), Paprika recipes (`paprika:recipe`), and pantry inventory counts (`pantry:inventory`).",
        "refs": R(REF_MEALIME, REF_ANYLIST, REF_INSTACART, REF_PAPRIKA),
        "sources": [
            {"label": "Mealime Plan", "friendly": "Mealime meal plan", "st": "mealime:plan", "group_field": "week_label", "group_desc": "week", "value_field": "meals_planned", "value_title": "Meals Planned", "duration_field": "planning_minutes", "duration_title": "Planning Time", "status_field": "plan_status", "sync_hours": 168},
            {"label": "AnyList Grocery List", "friendly": "AnyList grocery list", "st": "anylist:grocery", "group_field": "store_name", "group_desc": "store", "value_field": "items_checked", "value_title": "Items Checked", "duration_field": "shopping_minutes", "duration_title": "Shopping Time", "status_field": "list_status", "sync_hours": 72},
            {"label": "Instacart Order", "friendly": "Instacart order", "st": "instacart:order", "group_field": "store_name", "group_desc": "store", "value_field": "order_total_usd", "value_title": "Order Total", "duration_field": "delivery_minutes", "duration_title": "Delivery Time", "status_field": "order_status", "sync_hours": 72},
            {"label": "Paprika Recipe", "friendly": "Paprika recipe", "st": "paprika:recipe", "group_field": "recipe_name", "group_desc": "recipe", "value_field": "cook_count", "value_title": "Times Cooked", "duration_field": "prep_minutes", "duration_title": "Prep Time", "status_field": "recipe_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["pantry:inventory"],
        "specials": [
            S("Pantry Staple Below Par Level", "medium", "intermediate", ["Inventory", "Operations"],
              ("index=personal sourcetype=pantry:inventory item_name=* quantity_on_hand=* par_level=*", "| eval below_par=if(quantity_on_hand<par_level,1,0)", "| where below_par=1", "| sort quantity_on_hand", "| table item_name quantity_on_hand par_level category"),
              "Lists pantry items whose on-hand quantity has dropped below the configured par level.",
              "Running out of staples mid-week forces expensive emergency delivery orders you could have avoided.",
              "Scan pantry inventory into `pantry:inventory` with `quantity_on_hand` and `par_level`, then review before meal planning.",
              "Table of below-par items sorted by quantity.", "which pantry basics you are running low on before they disappear entirely."),
            S("Grocery Spend vs Meal Plan Coverage", "low", "intermediate", ["Cost", "Analytics"],
              ("(index=personal sourcetype=instacart:order order_total_usd=*) OR (index=personal sourcetype=mealime:plan meals_planned=*)", "| bin _time span=1w", "| stats sum(order_total_usd) as grocery_spend, max(meals_planned) as meals_planned by _time", "| eval spend_per_meal=round(grocery_spend/nullif(meals_planned,0),2)", "| sort - _time"),
              "Calculates weekly grocery spend divided by meals planned in Mealime for the same week.",
              "Cost-per-planned-meal shows whether shopping drift is outpacing what you actually intend to cook.",
              "Align Instacart order totals and Mealime plan exports by week and chart spend per planned meal.",
              "Line chart of weekly spend per planned meal.", "how much each planned meal is costing you at the grocery store each week."),
            S("Recipe Repeat vs Novelty Mix", "low", "beginner", ["Analytics", "Operations"],
              ("index=personal sourcetype=paprika:recipe recipe_name=* cook_count=*", "| eval cooked_recently=if(relative_time(_time,\"@w0\"),1,0)", "| stats sum(cooked_recently) as cooks_this_week, dc(recipe_name) as unique_recipes", "| eval repeat_ratio=round(100*cooks_this_week/unique_recipes,1)"),
              "Measures how often Paprika recipes cooked this week are repeats versus new additions.",
              "Too much repetition breeds meal fatigue; too much novelty wastes ingredients already in the pantry.",
              "Track `cook_count` and recipe name on each Paprika cook event and review the repeat ratio monthly.",
              "Donut chart of repeat versus new recipe cooks.", "whether you are mostly reheating the same recipes or actually trying new ones."),
            S("Unbought AnyList Items Carryover", "medium", "intermediate", ["Operations", "Quality"],
              ("index=personal sourcetype=anylist:grocery list_status=* items_unchecked=*", "| where items_unchecked>0", "| stats sum(items_unchecked) as total_unchecked, avg(shopping_minutes) as avg_trip_min by store_name", "| sort - total_unchecked"),
              "Surfaces grocery lists that ended shopping trips with unchecked items still on the list.",
              "Carryover items cause duplicate purchases or missing ingredients when the next recipe depends on them.",
              "Export AnyList completion stats with `items_unchecked` per trip and review stores with chronic carryover.",
              "Bar chart of unchecked items by store.", "which stores you keep leaving with items still unchecked on the list."),
        ],
    },
    {
        "id": "91",
        "name": "Snow Sports & Winter Recreation",
        "app": "Slopes ski sessions, Ski Tracks GPS runs, OnTheSnow resort reports, snow safety checklist logs, and Ikon Pass scan exports forwarded to Splunk HEC.",
        "ds": "Slopes ski sessions (`slopes:session`), Ski Tracks runs (`skitracks:run`), OnTheSnow resort reports (`onthesnow:report`), snow safety checks (`snow:safety`), and Ikon Pass lift scans (`ikon:pass`).",
        "refs": R(REF_SLOPES, REF_SKITRACKS, REF_ONTHESNOW, REF_IKON),
        "sources": [
            {"label": "Slopes Ski Session", "friendly": "Slopes ski session", "st": "slopes:session", "group_field": "resort_name", "group_desc": "resort", "value_field": "vertical_m", "value_title": "Vertical Meters", "duration_field": "active_minutes", "duration_title": "Active Time", "status_field": "session_status", "sync_hours": 72},
            {"label": "Ski Tracks Run", "friendly": "Ski Tracks run", "st": "skitracks:run", "group_field": "trail_name", "group_desc": "trail", "value_field": "max_speed_kph", "value_title": "Max Speed", "duration_field": "run_seconds", "duration_title": "Run Duration", "status_field": "run_status", "sync_hours": 72},
            {"label": "OnTheSnow Resort Report", "friendly": "OnTheSnow resort report", "st": "onthesnow:report", "group_field": "resort_name", "group_desc": "resort", "value_field": "base_depth_cm", "value_title": "Base Depth", "duration_field": "fresh_snow_cm", "duration_title": "Fresh Snow", "status_field": "report_status", "sync_hours": 24},
            {"label": "Snow Safety Check", "friendly": "snow safety check", "st": "snow:safety", "group_field": "checklist_name", "group_desc": "checklist", "value_field": "beacon_battery_pct", "value_title": "Beacon Battery", "duration_field": "check_minutes", "duration_title": "Check Time", "status_field": "check_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["ikon:pass"],
        "specials": [
            S("Ikon Pass Day Utilization", "low", "intermediate", ["Analytics", "Cost"],
              ("index=personal sourcetype=ikon:pass scan_type=* resort_name=*", "| bin _time span=1mon", "| stats dc(_time) as ski_days, dc(resort_name) as resorts_visited by _time pass_type", "| sort - _time"),
              "Counts distinct ski days and resorts visited per month from Ikon Pass lift scan exports.",
              "Pass utilization tells you whether the season ticket is paying for itself or sitting unused.",
              "Forward Ikon scan events with `pass_type` and `resort_name`, then compare ski days against pass blackout rules.",
              "Column chart of monthly ski days with resort count overlay.", "how many days you actually used your ski pass each month and at how many mountains."),
            S("Fresh Snow vs Planned Ski Days", "medium", "intermediate", ["Analytics", "Operations"],
              ("(index=personal sourcetype=onthesnow:report fresh_snow_cm=*) OR (index=personal sourcetype=slopes:session)", "| bin _time span=1d", "| stats max(fresh_snow_cm) as fresh_snow, count(eval(sourcetype=\"slopes:session\")) as ski_sessions by _time resort_name", "| where fresh_snow>=10", "| sort - fresh_snow"),
              "Highlights days with ten or more centimetres of fresh snow and whether a Slopes session was logged.",
              "Powder days are the payoff for season-pass math; this view shows whether you actually got out for them.",
              "Combine OnTheSnow daily reports with Slopes session counts by resort and date.",
              "Timeline of fresh-snow days with ski-session markers.", "which big snow days you skied versus the ones you missed."),
            S("Beacon Battery Pre-Trip Failures", "high", "intermediate", ["Safety", "Risk"],
              ("index=personal sourcetype=snow:safety checklist_name=* beacon_battery_pct=*", "| where beacon_battery_pct<40", "| stats min(beacon_battery_pct) as worst_battery, count as failed_checks by checklist_name", "| sort worst_battery"),
              "Flags snow-safety pre-trip checks where avalanche beacon battery fell below forty percent.",
              "A weak beacon battery is a backcountry trip-stopper that is easy to fix if caught before leaving the car.",
              "Log beacon battery percentage on every `snow:safety` checklist and block trip departure below your threshold.",
              "Table of failed checks ranked by worst battery reading.", "when your avalanche beacon was too low on battery before a trip."),
            S("Max Speed Outlier Runs", "low", "advanced", ["Anomaly", "Performance"],
              ("index=personal sourcetype=skitracks:run max_speed_kph=* trail_name=*", "| eventstats avg(max_speed_kph) as avg_speed, stdev(max_speed_kph) as speed_stdev by trail_name", "| eval z_score=round((max_speed_kph-avg_speed)/nullif(speed_stdev,0),2)", "| where z_score>=2", "| table _time trail_name max_speed_kph avg_speed z_score"),
              "Detects Ski Tracks runs whose max speed is two standard deviations above the trail average.",
              "Speed outliers can flag icy conditions, GPS glitches, or runs where control got away from you.",
              "Export Ski Tracks runs with `max_speed_kph` and review z-score outliers after each resort day.",
              "Scatter plot of max speed by trail with outlier markers.", "runs where you went unusually fast compared with your normal pace on that trail."),
        ],
    },
    {
        "id": "92",
        "name": "Yoga, Pilates & Mind-Body",
        "app": "Down Dog session logs, Peloton yoga classes, Glo streaming sessions, Pilates reformer notes, and home mat usage counters sent to Splunk HEC.",
        "ds": "Down Dog sessions (`downdog:session`), Peloton yoga classes (`peloton:yoga`), Glo classes (`glo:class`), Pilates sessions (`pilates:session`), and mat usage logs (`mat:usage`).",
        "refs": R(REF_DOWNDOG, REF_PELOTON, REF_GLO),
        "sources": [
            {"label": "Down Dog Session", "friendly": "Down Dog session", "st": "downdog:session", "group_field": "practice_type", "group_desc": "practice type", "value_field": "calories_burned", "value_title": "Calories Burned", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 72},
            {"label": "Peloton Yoga Class", "friendly": "Peloton yoga class", "st": "peloton:yoga", "group_field": "instructor_name", "group_desc": "instructor", "value_field": "output_kj", "value_title": "Output", "duration_field": "class_minutes", "duration_title": "Class Length", "status_field": "class_status", "sync_hours": 72},
            {"label": "Glo Class", "friendly": "Glo class", "st": "glo:class", "group_field": "style", "group_desc": "style", "value_field": "completion_pct", "value_title": "Completion Percent", "duration_field": "class_minutes", "duration_title": "Class Length", "status_field": "class_status", "sync_hours": 72},
            {"label": "Pilates Session", "friendly": "Pilates session", "st": "pilates:session", "group_field": "studio_name", "group_desc": "studio", "value_field": "reps_completed", "value_title": "Reps Completed", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["mat:usage"],
        "specials": [
            S("Home Mat Usage vs Studio Sessions", "low", "intermediate", ["Analytics", "Operations"],
              ("(index=personal sourcetype=mat:usage minutes_used=*) OR (index=personal sourcetype=pilates:session)", "| bin _time span=1w", "| eval home_min=if(sourcetype=\"mat:usage\",minutes_used,0), studio_min=if(sourcetype=\"pilates:session\",session_minutes,0)", "| stats sum(home_min) as home_minutes, sum(studio_min) as studio_minutes by _time", "| eval home_pct=round(100*home_minutes/(home_minutes+studio_minutes),1)", "| sort - _time"),
              "Compares weekly home mat minutes against in-studio Pilates session minutes.",
              "Knowing your home-versus-studio split helps you decide whether the gym membership is earning its keep.",
              "Log smart-mat or manual mat usage to `mat:usage` and align weekly totals with studio session exports.",
              "Stacked bar chart of home versus studio minutes by week.", "how much of your mind-body practice happens at home versus at the studio."),
            S("Instructor Loyalty Concentration", "low", "beginner", ["Analytics", "Operations"],
              ("index=personal sourcetype=peloton:yoga instructor_name=*", "| stats count as classes by instructor_name", "| eventstats sum(classes) as total", "| eval share_pct=round(100*classes/total,1)", "| sort - classes", "| head 10"),
              "Ranks Peloton yoga instructors by class count and share of total practice time.",
              "Favorite instructors are fine until one goes on leave; concentration shows whether you have backup teachers.",
              "Export Peloton yoga history with `instructor_name` and review top-instructor share quarterly.",
              "Pareto chart of classes by instructor.", "which yoga teachers you keep going back to most often."),
            S("Flexibility Style Mix Drift", "low", "intermediate", ["Analytics", "Quality"],
              ("index=personal sourcetype=glo:class style=*", "| bin _time span=1q", "| stats count as classes by _time style", "| chart sum(classes) over _time by style"),
              "Shows how your Glo class style mix shifts quarter over quarter across yoga, Pilates, and meditation.",
              "Style drift reveals whether you are balancing strength and recovery or over-indexing on one modality.",
              "Include `style` on each Glo export and review the quarterly mix during wellness check-ins.",
              "Stacked area chart of class count by style over quarters.", "whether your practice mix is changing toward more stretching, strength, or meditation."),
            S("Down Dog Streak Break Detection", "medium", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=downdog:session", "| bin _time span=1d", "| stats count as sessions by _time", "| sort _time", "| streamstats current=f last(_time) as prev_day", "| eval gap_days=round((_time-prev_day)/86400,0)", "| where gap_days>=4 AND sessions>0", "| stats max(gap_days) as longest_break_days"),
              "Finds the longest gap of four or more days between Down Dog practice days after activity was established.",
              "Streak breaks often precede full habit dropout; catching the gap early makes restarting easier.",
              "Run daily on Down Dog session counts and alert when the quiet gap exceeds your restart threshold.",
              "Single-value tile for longest practice break in days.", "the longest stretch you went without doing Down Dog after you had been practicing regularly."),
        ],
    },
    {
        "id": "93",
        "name": "Triathlon & Multisport",
        "app": "TrainingPeaks structured workouts, Garmin multisport FIT exports, TriDot training plans, brick workout logs, and transition timing notes ingested into Splunk HEC.",
        "ds": "TrainingPeaks workouts (`trainingpeaks:workout`), Garmin multisport activities (`garmin:multisport`), TriDot plans (`tridot:plan`), brick workouts (`brick:workout`), and transition logs (`transition:log`).",
        "refs": R(REF_TRAININGPEAKS, REF_GARMIN, REF_TRIDOT),
        "sources": [
            {"label": "TrainingPeaks Workout", "friendly": "TrainingPeaks workout", "st": "trainingpeaks:workout", "group_field": "sport", "group_desc": "sport", "value_field": "tss", "value_title": "Training Stress", "duration_field": "workout_minutes", "duration_title": "Workout Time", "status_field": "workout_status", "sync_hours": 72},
            {"label": "Garmin Multisport Activity", "friendly": "Garmin multisport activity", "st": "garmin:multisport", "group_field": "activity_type", "group_desc": "activity type", "value_field": "distance_km", "value_title": "Distance", "duration_field": "elapsed_minutes", "duration_title": "Elapsed Time", "status_field": "activity_status", "sync_hours": 48},
            {"label": "TriDot Training Plan", "friendly": "TriDot training plan", "st": "tridot:plan", "group_field": "phase", "group_desc": "training phase", "value_field": "compliance_pct", "value_title": "Compliance Percent", "duration_field": "planned_minutes", "duration_title": "Planned Duration", "status_field": "plan_status", "sync_hours": 72},
            {"label": "Brick Workout", "friendly": "brick workout", "st": "brick:workout", "group_field": "race_name", "group_desc": "target race", "value_field": "bike_run_combo_tss", "value_title": "Combined TSS", "duration_field": "brick_minutes", "duration_title": "Brick Duration", "status_field": "brick_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": ["transition:log"],
        "specials": [
            S("T2 Transition Time Regression", "medium", "advanced", ["Performance", "Analytics"],
              ("index=personal sourcetype=transition:log transition_type=\"T2\" transition_seconds=* race_name=*", "| stats avg(transition_seconds) as avg_t2, min(transition_seconds) as best_t2 by race_name", "| eval t2_gap=round(avg_t2-best_t2,1)", "| sort - t2_gap"),
              "Compares average T2 bike-to-run transition times against personal bests for each target race.",
              "Transition seconds are free speed on race day; tracking T2 drift shows where race-morning routines need tightening.",
              "Log `transition_seconds` and `transition_type` for every practice and race simulation into `transition:log`.",
              "Table of races with average, best, and gap T2 seconds.", "how much slower your average T2 transitions are compared with your best ones."),
            S("Weekly TSS by Discipline Balance", "medium", "intermediate", ["Analytics", "Performance"],
              ("index=personal sourcetype=trainingpeaks:workout sport=* tss=*", "| bin _time span=1w", "| stats sum(tss) as weekly_tss by _time sport", "| chart sum(weekly_tss) over _time by sport"),
              "Breaks down weekly Training Stress Score totals by swim, bike, and run discipline.",
              "Discipline imbalance is a common overuse-injury path; a weekly TSS split keeps load proportional.",
              "Ensure each TrainingPeaks workout carries `sport` and `tss`, then review the weekly stacked chart.",
              "Stacked column chart of weekly TSS by sport.", "whether your training load is balanced across swim, bike, and run each week."),
            S("TriDot Compliance Drop Alert", "high", "intermediate", ["Operations", "Compliance"],
              ("index=personal sourcetype=tridot:plan compliance_pct=* phase=*", "| timechart span=1w avg(compliance_pct) as avg_compliance by phase", "| where avg_compliance<75"),
              "Alerts when weekly average TriDot plan compliance falls below seventy-five percent for any training phase.",
              "Plan compliance drops often mean life stress or injury; catching them early prevents junk miles.",
              "Export TriDot compliance percentages weekly by `phase` and alert when averages slide under threshold.",
              "Line chart of weekly compliance by phase with threshold band.", "when you stopped following your TriDot plan closely enough to stay on track."),
            S("Garmin vs TrainingPeaks Duration Mismatch", "low", "advanced", ["Data Quality", "Analytics"],
              ("index=personal sourcetype=garmin:multisport activity_id=* elapsed_minutes=*", "| join type=inner activity_id [search index=personal sourcetype=trainingpeaks:workout activity_id=* | rename workout_minutes as tp_minutes]", "| eval duration_delta=round(elapsed_minutes-tp_minutes,1)", "| where abs(duration_delta)>10", "| table _time activity_type elapsed_minutes tp_minutes duration_delta"),
              "Finds multisport activities where Garmin elapsed time differs from TrainingPeaks by more than ten minutes.",
              "Duration mismatches usually mean a failed sync, paused watch, or duplicate activity that skews load metrics.",
              "Share a common `activity_id` between Garmin and TrainingPeaks exports and review large deltas after each upload.",
              "Table of activities with duration delta in minutes.", "workouts where your watch time and TrainingPeaks time do not match up."),
        ],
    },
    {
        "id": "94",
        "name": "Personal CRM & Networking",
        "app": "Monica contact relationship logs, Clay network exports, LinkedIn connection events, follow-up reminder tasks, and warm-intro request trackers streamed into Splunk HEC.",
        "ds": "Monica contacts (`monica:contact`), Clay relationships (`clay:relationship`), LinkedIn connections (`linkedin:connection`), follow-up reminders (`followup:reminder`), and intro requests (`intro:request`).",
        "refs": R(REF_MONICA, REF_CLAY, REF_LINKEDIN),
        "sources": [
            {"label": "Monica Contact", "friendly": "Monica contact", "st": "monica:contact", "group_field": "relationship_type", "group_desc": "relationship type", "value_field": "interaction_count", "value_title": "Interaction Count", "duration_field": "days_since_contact", "duration_title": "Days Since Contact", "status_field": "contact_status", "sync_hours": 168},
            {"label": "Clay Relationship", "friendly": "Clay relationship", "st": "clay:relationship", "group_field": "network_segment", "group_desc": "network segment", "value_field": "strength_score", "value_title": "Strength Score", "duration_field": "days_since_touch", "duration_title": "Days Since Touch", "status_field": "relationship_status", "sync_hours": 168},
            {"label": "LinkedIn Connection", "friendly": "LinkedIn connection", "st": "linkedin:connection", "group_field": "industry", "group_desc": "industry", "value_field": "mutual_connections", "value_title": "Mutual Connections", "duration_field": "days_since_accept", "duration_title": "Days Since Accept", "status_field": "connection_status", "sync_hours": 168},
            {"label": "Follow-Up Reminder", "friendly": "follow-up reminder", "st": "followup:reminder", "group_field": "contact_name", "group_desc": "contact", "value_field": "priority_score", "value_title": "Priority Score", "duration_field": "days_overdue", "duration_title": "Days Overdue", "status_field": "reminder_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": ["intro:request"],
        "specials": [
            S("Overdue Follow-Up Backlog", "medium", "intermediate", ["Operations", "Business"],
              ("index=personal sourcetype=followup:reminder days_overdue=*", "| where days_overdue>0", "| stats count as overdue_reminders, max(days_overdue) as worst_overdue by contact_name", "| sort - worst_overdue", "| head 20"),
              "Lists contacts with open follow-up reminders sorted by how many days overdue they are.",
              "Networking debt compounds quietly; an overdue backlog turns good intentions into missed opportunities.",
              "Export follow-up tasks with `days_overdue` and review the top twenty contacts each Monday morning.",
              "Table of contacts with overdue reminder count and worst overdue days.", "which people you meant to follow up with but keep putting off."),
            S("LinkedIn Connection Acceptance Lag", "low", "intermediate", ["Analytics", "Business"],
              ("index=personal sourcetype=linkedin:connection connection_status=* days_since_accept=*", "| where connection_status=\"pending\"", "| stats avg(days_since_accept) as avg_pending_days, count as pending_requests by industry", "| sort - pending_requests"),
              "Measures how long LinkedIn connection requests have remained pending by industry segment.",
              "Stale pending requests clutter your network hygiene and may mean your outreach message needs tuning.",
              "Track `connection_status` and `days_since_accept` on LinkedIn exports and review pending queues monthly.",
              "Bar chart of pending request count with average pending days.", "how long your LinkedIn connection requests have been sitting unanswered."),
            S("Warm Intro Request Conversion", "medium", "intermediate", ["Analytics", "Business"],
              ("index=personal sourcetype=intro:request intro_status=*", "| stats count as requests, sum(eval(if(intro_status=\"accepted\",1,0))) as accepted by network_segment", "| eval conversion_pct=round(100*accepted/requests,1)", "| sort - conversion_pct"),
              "Calculates warm-intro request acceptance rate by network segment.",
              "Intro conversion rates show which circles actually move the needle versus ones that look busy but go nowhere.",
              "Log each intro request with `intro_status` and `network_segment`, then review conversion quarterly.",
              "Bar chart of conversion percentage by segment.", "which parts of your network actually say yes when you ask for an introduction."),
            S("Relationship Strength Decay Watch", "high", "intermediate", ["Risk", "Business"],
              ("index=personal sourcetype=clay:relationship strength_score=* days_since_touch=*", "| where days_since_touch>90 AND strength_score>=7", "| sort - strength_score - days_since_touch", "| table contact_name network_segment strength_score days_since_touch"),
              "Flags high-strength Clay relationships that have gone more than ninety days without a logged touch.",
              "Strong ties go cold fastest when you assume they will always be there; decay alerts prompt a quick check-in.",
              "Sync Clay with `strength_score` and `days_since_touch`, then alert on high-value contacts past your touch window.",
              "Table of at-risk high-strength contacts.", "important relationships that have gone quiet for too long even though they used to be close."),
        ],
    },
    {
        "id": "95",
        "name": "Gifts, Holidays & Celebrations",
        "app": "Gift registry exports, Amazon wishlist snapshots, holiday card mail logs, birthday budget trackers, and thank-you note reminders ingested into Splunk HEC.",
        "ds": "Gift registries (`gift:registry`), Amazon wishlists (`amazon:wishlist`), holiday card sends (`holiday:card`), birthday budgets (`birthday:budget`), and thank-you notes (`thankyou:note`).",
        "refs": R(REF_AMAZON),
        "sources": [
            {"label": "Gift Registry Entry", "friendly": "gift registry entry", "st": "gift:registry", "group_field": "event_name", "group_desc": "event", "value_field": "item_price_usd", "value_title": "Item Price", "duration_field": "days_until_event", "duration_title": "Days Until Event", "status_field": "purchase_status", "sync_hours": 168},
            {"label": "Amazon Wishlist Item", "friendly": "Amazon wishlist item", "st": "amazon:wishlist", "group_field": "recipient_name", "group_desc": "recipient", "value_field": "item_price_usd", "value_title": "Item Price", "duration_field": "days_on_list", "duration_title": "Days on List", "status_field": "item_status", "sync_hours": 168},
            {"label": "Holiday Card Send", "friendly": "holiday card send", "st": "holiday:card", "group_field": "card_type", "group_desc": "card type", "value_field": "cards_sent", "value_title": "Cards Sent", "duration_field": "mailing_minutes", "duration_title": "Mailing Time", "status_field": "mail_status", "sync_hours": 720},
            {"label": "Birthday Budget Entry", "friendly": "birthday budget entry", "st": "birthday:budget", "group_field": "recipient_name", "group_desc": "recipient", "value_field": "budget_usd", "value_title": "Budget Amount", "duration_field": "days_until_birthday", "duration_title": "Days Until Birthday", "status_field": "budget_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["thankyou:note"],
        "specials": [
            S("Thank-You Note Overdue Queue", "medium", "intermediate", ["Operations", "Quality"],
              ("index=personal sourcetype=thankyou:note note_status=* days_overdue=*", "| where note_status!=\"sent\" AND days_overdue>7", "| sort - days_overdue", "| table recipient_name gift_event days_overdue note_status"),
              "Lists thank-you notes that remain unsent more than seven days after the related gift event.",
              "Late thank-you notes feel worse the longer they wait; a visible queue keeps social obligations manageable.",
              "Track `note_status` and `days_overdue` for each gift and review the queue every Sunday.",
              "Table of overdue thank-you notes sorted by days overdue.", "thank-you notes you still owe people more than a week after the gift."),
            S("Holiday Card Mailing Progress", "low", "beginner", ["Operations", "Analytics"],
              ("index=personal sourcetype=holiday:card season_year=* cards_sent=* cards_planned=*", "| stats sum(cards_sent) as sent, max(cards_planned) as planned by season_year card_type", "| eval pct_complete=round(100*sent/planned,1)", "| sort season_year"),
              "Tracks holiday card mailing progress as sent versus planned counts by season and card type.",
              "Card season stress drops when you can see exactly how far behind or ahead the mailing list is.",
              "Include `cards_sent` and `cards_planned` on each mailing session export and update through December.",
              "Progress bar or gauge of percent complete by card type.", "how far along you are sending holiday cards compared with your plan."),
            S("Birthday Budget Overrun Risk", "medium", "intermediate", ["Cost", "Risk"],
              ("index=personal sourcetype=birthday:budget budget_usd=* spent_usd=* days_until_birthday=*", "| eval remaining_usd=budget_usd-spent_usd, overrun_risk=if(spent_usd>budget_usd,1,0)", "| where days_until_birthday<=30 AND (overrun_risk=1 OR remaining_usd<20)", "| sort days_until_birthday", "| table recipient_name budget_usd spent_usd remaining_usd days_until_birthday"),
              "Flags upcoming birthdays where spending has exceeded budget or remaining funds are under twenty dollars.",
              "Birthday budget overruns are small individually but add up across a busy family calendar.",
              "Log `budget_usd` and `spent_usd` per recipient and review thirty days before each birthday.",
              "Table of at-risk birthdays with budget and spend columns.", "upcoming birthdays where you are about to overspend your gift budget."),
            S("Registry Fulfillment Gap Before Event", "high", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=gift:registry event_name=* purchase_status=* days_until_event=*", "| where days_until_event<=14 AND purchase_status!=\"purchased\"", "| stats count as unpurchased_items, sum(item_price_usd) as open_value by event_name", "| sort - open_value"),
              "Surfaces registry items still unpurchased within fourteen days of the event date.",
              "Last-minute registry gaps force rushed shipping or duplicate gifts nobody needed.",
              "Sync registry exports with `purchase_status` and `days_until_event`, then alert two weeks before each event.",
              "Table of events with unpurchased item count and open dollar value.", "registry gifts still not bought when the event is only two weeks away."),
        ],
    },
    {
        "id": "96",
        "name": "Moving & Relocation",
        "app": "Move checklist task exports, USPS change-of-address confirmations, mover quote comparisons, utility transfer logs, and box inventory scans forwarded to Splunk HEC.",
        "ds": "Move checklists (`move:checklist`), USPS change-of-address (`usps:change`), mover quotes (`mover:quote`), utility transfers (`utility:transfer`), and box inventories (`box:inventory`).",
        "refs": R(REF_USPS),
        "sources": [
            {"label": "Move Checklist Task", "friendly": "move checklist task", "st": "move:checklist", "group_field": "phase", "group_desc": "move phase", "value_field": "tasks_completed", "value_title": "Tasks Completed", "duration_field": "days_before_move", "duration_title": "Days Before Move", "status_field": "task_status", "sync_hours": 72},
            {"label": "USPS Change of Address", "friendly": "USPS change of address", "st": "usps:change", "group_field": "move_type", "group_desc": "move type", "value_field": "forward_days", "value_title": "Forward Days", "duration_field": "processing_days", "duration_title": "Processing Time", "status_field": "coa_status", "sync_hours": 168},
            {"label": "Mover Quote", "friendly": "mover quote", "st": "mover:quote", "group_field": "vendor_name", "group_desc": "mover", "value_field": "quote_usd", "value_title": "Quote Amount", "duration_field": "estimate_minutes", "duration_title": "Estimate Time", "status_field": "quote_status", "sync_hours": 168},
            {"label": "Utility Transfer", "friendly": "utility transfer", "st": "utility:transfer", "group_field": "utility_type", "group_desc": "utility type", "value_field": "deposit_usd", "value_title": "Deposit Amount", "duration_field": "transfer_days", "duration_title": "Transfer Lead Time", "status_field": "transfer_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": ["box:inventory"],
        "specials": [
            S("Box Inventory Unlabeled Rate", "medium", "intermediate", ["Operations", "Quality"],
              ("index=personal sourcetype=box:inventory box_id=* room_label=*", "| eval unlabeled=if(isnull(room_label) OR room_label=\"\",1,0)", "| stats sum(unlabeled) as unlabeled_boxes, count as total_boxes", "| eval unlabeled_pct=round(100*unlabeled_boxes/total_boxes,1)"),
              "Measures what percentage of packed moving boxes lack a room label in the inventory scan.",
              "Unlabeled boxes turn unpacking into a guessing game that adds hours on move-in day.",
              "Scan each box into `box:inventory` with `box_id` and `room_label` before the truck loads.",
              "Gauge of percent unlabeled boxes with total count.", "how many moving boxes still do not say which room they belong in."),
            S("Move Checklist Critical Path Slip", "high", "intermediate", ["Operations", "Risk"],
              ("index=personal sourcetype=move:checklist phase=* task_status=* days_before_move=*", "| where task_status!=\"done\" AND days_before_move<=7", "| stats count as open_critical_tasks, min(days_before_move) as nearest_deadline by phase", "| sort nearest_deadline"),
              "Lists move checklist tasks still open within seven days of move date grouped by phase.",
              "Critical-path slips on utilities, COA, and mover confirmations cascade into expensive move-day chaos.",
              "Tag each checklist task with `days_before_move` and review open critical items daily the final week.",
              "Table of phases with open task count and nearest deadline.", "important move tasks still not done when moving day is only a week away."),
            S("Mover Quote Spread Analysis", "low", "intermediate", ["Cost", "Analytics"],
              ("index=personal sourcetype=mover:quote quote_usd=* vendor_name=*", "| stats min(quote_usd) as low_quote, max(quote_usd) as high_quote, avg(quote_usd) as avg_quote", "| eval spread_usd=round(high_quote-low_quote,2), spread_pct=round(100*(high_quote-low_quote)/nullif(low_quote,0),1)"),
              "Calculates the dollar and percentage spread between lowest and highest mover quotes received.",
              "Quote spread shows whether you are comparing like-for-like estimates or talking to outliers.",
              "Collect at least three `mover:quote` events with `quote_usd` before signing a contract.",
              "Single-value tiles for spread dollars and percent.", "how far apart your highest and lowest mover quotes were."),
            S("Utility Transfer Gap on Move Day", "high", "advanced", ["Operations", "Risk"],
              ("index=personal sourcetype=utility:transfer utility_type=* transfer_status=* move_date=*", "| eval gap=if(transfer_status!=\"active\" AND transfer_date<=move_date,1,0)", "| where gap=1", "| table utility_type transfer_status move_date transfer_date"),
              "Flags utilities that were not active by the recorded move-in date.",
              "Arriving without power, water, or internet turns the first night into an unnecessary crisis.",
              "Include `move_date`, `transfer_date`, and `transfer_status` on each utility event and verify one week ahead.",
              "Table of utilities not active by move date.", "utilities that were not turned on by the day you actually moved in."),
        ],
    },
    {
        "id": "97",
        "name": "Emergency Preparedness",
        "app": "Go-bag inventory audits, household prep drill logs, water rotation schedules, battery expiration trackers, and emergency radio test results streamed into Splunk HEC.",
        "ds": "Go-bag inventories (`gobag:inventory`), prep drills (`prep:drill`), water rotation logs (`water:rotation`), battery expiration checks (`battery:expiration`), and radio tests (`radio:test`).",
        "refs": R(REF_USPS),
        "sources": [
            {"label": "Go-Bag Inventory", "friendly": "go-bag inventory", "st": "gobag:inventory", "group_field": "bag_name", "group_desc": "go bag", "value_field": "items_present", "value_title": "Items Present", "duration_field": "audit_minutes", "duration_title": "Audit Time", "status_field": "audit_status", "sync_hours": 720},
            {"label": "Prep Drill Log", "friendly": "prep drill log", "st": "prep:drill", "group_field": "drill_type", "group_desc": "drill type", "value_field": "completion_pct", "value_title": "Completion Percent", "duration_field": "drill_minutes", "duration_title": "Drill Time", "status_field": "drill_status", "sync_hours": 720},
            {"label": "Water Rotation Log", "friendly": "water rotation log", "st": "water:rotation", "group_field": "storage_location", "group_desc": "storage location", "value_field": "gallons_rotated", "value_title": "Gallons Rotated", "duration_field": "days_since_rotation", "duration_title": "Days Since Rotation", "status_field": "rotation_status", "sync_hours": 720},
            {"label": "Battery Expiration Check", "friendly": "battery expiration check", "st": "battery:expiration", "group_field": "device_name", "group_desc": "device", "value_field": "batteries_expired", "value_title": "Expired Batteries", "duration_field": "days_until_expiry", "duration_title": "Days Until Expiry", "status_field": "check_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": ["radio:test"],
        "specials": [
            S("Emergency Radio Test Failures", "high", "intermediate", ["Safety", "Reliability"],
              ("index=personal sourcetype=radio:test test_result=* signal_strength_dbm=*", "| where test_result!=\"pass\"", "| stats count as failed_tests, min(signal_strength_dbm) as worst_signal by radio_model", "| sort - failed_tests"),
              "Counts failed emergency radio tests and worst signal strength by radio model.",
              "A radio that fails the monthly test is decoration, not preparedness, when the grid goes down.",
              "Log `test_result` and `signal_strength_dbm` after each NOAA radio check into `radio:test`.",
              "Table of radio models with failed test count.", "emergency radios that failed their last check and might not work in a crisis."),
            S("Water Rotation Overdue Locations", "high", "intermediate", ["Operations", "Risk"],
              ("index=personal sourcetype=water:rotation days_since_rotation=* storage_location=*", "| where days_since_rotation>180", "| sort - days_since_rotation", "| table storage_location gallons_stored days_since_rotation last_rotation_date"),
              "Lists water storage locations whose rotation interval exceeds six months.",
              "Stale stored water is a false sense of security; rotation schedules keep supplies actually drinkable.",
              "Track `days_since_rotation` and `storage_location` on each rotation event and alert past one hundred eighty days.",
              "Table of overdue storage locations by days since rotation.", "water supplies that have not been rotated in more than six months."),
            S("Go-Bag Item Missing Rate", "medium", "intermediate", ["Inventory", "Risk"],
              ("index=personal sourcetype=gobag:inventory bag_name=* items_required=* items_present=*", "| eval missing_items=items_required-items_present", "| eval missing_pct=round(100*missing_items/items_required,1)", "| where missing_pct>0", "| sort - missing_pct", "| table bag_name missing_items missing_pct"),
              "Calculates the percentage of required go-bag items missing during each inventory audit.",
              "Go bags erode over time as you borrow gear; missing-item rate catches drift before storm season.",
              "Include `items_required` and `items_present` on quarterly go-bag audits and review any bag above zero missing.",
              "Bar chart of missing-item percentage by bag.", "how incomplete each emergency go bag is after your last check."),
            S("Household Drill Completion Trend", "low", "intermediate", ["Operations", "Resilience"],
              ("index=personal sourcetype=prep:drill drill_type=* completion_pct=*", "| timechart span=1q avg(completion_pct) as avg_completion, count as drills by drill_type", "| fillnull value=0"),
              "Trends quarterly average completion percentage for household emergency prep drills by type.",
              "Drill completion trends reveal whether preparedness is a living habit or a one-time shopping spree.",
              "Log fire, earthquake, and evacuation drills with `completion_pct` and review quarterly averages.",
              "Multi-series line chart of average drill completion by type.", "whether your family is actually practicing emergency drills or just planning to."),
        ],
    },
    {
        "id": "98",
        "name": "Sneakers & Resale Collecting",
        "app": "StockX price alerts, GOAT listing exports, Alias seller settlement logs, sneaker rotation wear trackers, and deadstock age audits ingested into Splunk HEC.",
        "ds": "StockX market prices (`stockx:price`), GOAT listings (`goat:listing`), Alias sales (`alias:sale`), sneaker rotation logs (`sneaker:rotation`), and deadstock age checks (`deadstock:age`).",
        "refs": R(REF_STOCKX, REF_GOAT),
        "sources": [
            {"label": "StockX Price Snapshot", "friendly": "StockX price snapshot", "st": "stockx:price", "group_field": "sku", "group_desc": "SKU", "value_field": "lowest_ask_usd", "value_title": "Lowest Ask", "duration_field": "spread_usd", "duration_title": "Bid-Ask Spread", "status_field": "market_status", "sync_hours": 24},
            {"label": "GOAT Listing", "friendly": "GOAT listing", "st": "goat:listing", "group_field": "sku", "group_desc": "SKU", "value_field": "list_price_usd", "value_title": "List Price", "duration_field": "days_listed", "duration_title": "Days Listed", "status_field": "listing_status", "sync_hours": 24},
            {"label": "Alias Sale", "friendly": "Alias sale", "st": "alias:sale", "group_field": "sku", "group_desc": "SKU", "value_field": "net_payout_usd", "value_title": "Net Payout", "duration_field": "days_to_sell", "duration_title": "Days to Sell", "status_field": "sale_status", "sync_hours": 72},
            {"label": "Sneaker Rotation Log", "friendly": "sneaker rotation log", "st": "sneaker:rotation", "group_field": "silhouette", "group_desc": "silhouette", "value_field": "wear_count", "value_title": "Wear Count", "duration_field": "days_since_wear", "duration_title": "Days Since Wear", "status_field": "rotation_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": ["deadstock:age"],
        "specials": [
            S("Deadstock Age Yellowing Risk", "medium", "intermediate", ["Risk", "Inventory"],
              ("index=personal sourcetype=deadstock:age sku=* age_days=* storage_type=*", "| where age_days>365 AND storage_type=\"open_air\"", "| sort - age_days", "| table sku age_days storage_type box_condition"),
              "Lists deadstock pairs stored in open air for more than one year where midsole yellowing risk rises.",
              "Heat and light damage is irreversible; age plus storage type tells you which pairs need rotation or sale.",
              "Audit unworn inventory into `deadstock:age` with `age_days` and `storage_type` quarterly.",
              "Table of at-risk SKUs sorted by age.", "sneakers sitting unworn too long in storage where yellowing becomes likely."),
            S("StockX Ask Below Purchase Price", "high", "intermediate", ["Cost", "Analytics"],
              ("index=personal sourcetype=stockx:price sku=* lowest_ask_usd=*", "| join type=inner sku [search index=personal sourcetype=alias:sale OR sourcetype=goat:listing | stats latest(purchase_price_usd) as cost by sku]", "| eval loss_usd=round(cost-lowest_ask_usd,2)", "| where loss_usd>0", "| sort - loss_usd", "| table sku cost lowest_ask_usd loss_usd"),
              "Finds SKUs where the current StockX lowest ask is below recorded purchase cost.",
              "Holding losers ties up capital; knowing market-versus-cost helps decide hold, drop, or wear.",
              "Maintain `purchase_price_usd` per SKU and compare nightly against StockX `lowest_ask_usd`.",
              "Table of underwater SKUs with loss amount.", "shoes worth less on StockX right now than you paid for them."),
            S("Rotation Neglect for Daily Beaters", "low", "intermediate", ["Operations", "Inventory"],
              ("index=personal sourcetype=sneaker:rotation silhouette=* days_since_wear=* wear_count=*", "| where wear_count>=10 AND days_since_wear>30", "| sort - days_since_wear", "| table sku silhouette wear_count days_since_wear"),
              "Flags heavily worn daily beaters that have not been rotated in more than thirty days.",
              "Even beaters need rest and cleaning cycles; neglect accelerates midsole collapse and odor buildup.",
              "Log each wear with `days_since_wear` and review beaters with high `wear_count` monthly.",
              "Table of neglected beaters by days since last wear.", "everyday sneakers you have not rotated out in over a month."),
            S("GOAT Listing Stale Inventory", "medium", "intermediate", ["Operations", "Cost"],
              ("index=personal sourcetype=goat:listing listing_status=\"active\" days_listed=*", "| where days_listed>45", "| stats count as stale_listings, avg(list_price_usd) as avg_price by sku", "| sort - stale_listings", "| head 15"),
              "Surfaces GOAT listings active for more than forty-five days without selling.",
              "Stale listings usually mean price is too high or photos need refresh; visibility prevents forgotten inventory tax.",
              "Export GOAT active listings with `days_listed` and review stale SKUs biweekly for repricing.",
              "Table of stale listings by SKU with average list price.", "sneakers listed on GOAT so long they probably need a price cut."),
        ],
    },
    {
        "id": "99",
        "name": "Formula 1 & Motorsport Fandom",
        "app": "FastF1 session exports, Ergast race results, F1 Fantasy team snapshots, race watch-party logs, and F1 telemetry lap dumps forwarded to Splunk HEC.",
        "ds": "FastF1 session data (`fastf1:session`), Ergast race results (`ergast:result`), F1 Fantasy teams (`f1fantasy:team`), race watch parties (`race:watchparty`), and F1 telemetry laps (`f1telemetry:lap`).",
        "refs": R(REF_FASTF1, REF_ERGAST, REF_F1FANTASY),
        "sources": [
            {"label": "FastF1 Session", "friendly": "FastF1 session", "st": "fastf1:session", "group_field": "session_type", "group_desc": "session type", "value_field": "lap_count", "value_title": "Lap Count", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 168},
            {"label": "Ergast Race Result", "friendly": "Ergast race result", "st": "ergast:result", "group_field": "constructor", "group_desc": "constructor", "value_field": "points", "value_title": "Points Scored", "duration_field": "gap_to_leader_seconds", "duration_title": "Gap to Leader", "status_field": "result_status", "sync_hours": 168},
            {"label": "F1 Fantasy Team", "friendly": "F1 Fantasy team", "st": "f1fantasy:team", "group_field": "round_name", "group_desc": "race round", "value_field": "team_points", "value_title": "Fantasy Points", "duration_field": "budget_remaining_m", "duration_title": "Budget Remaining", "status_field": "team_status", "sync_hours": 168},
            {"label": "Race Watch Party", "friendly": "race watch party", "st": "race:watchparty", "group_field": "venue", "group_desc": "venue", "value_field": "guest_count", "value_title": "Guest Count", "duration_field": "watch_minutes", "duration_title": "Watch Time", "status_field": "party_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": ["f1telemetry:lap"],
        "specials": [
            S("Telemetry Lap Personal Best Delta", "low", "advanced", ["Performance", "Analytics"],
              ("index=personal sourcetype=f1telemetry:lap driver_code=* lap_time_seconds=* circuit=*", "| stats min(lap_time_seconds) as best_lap, avg(lap_time_seconds) as avg_lap by driver_code circuit", "| eval delta=round(avg_lap-best_lap,3)", "| sort - delta", "| table driver_code circuit best_lap avg_lap delta"),
              "Compares average F1 telemetry lap times against personal best per driver and circuit.",
              "Lap deltas show whether your sim or tracker laps are tightening or still inconsistent corner to corner.",
              "Import F1 game or tracker laps into `f1telemetry:lap` with `lap_time_seconds` and `circuit`.",
              "Table of driver-circuit pairs with best, average, and delta.", "how much slower your average lap is compared with your best at each track."),
            S("Constructor Points Momentum", "low", "intermediate", ["Analytics", "Operations"],
              ("index=personal sourcetype=ergast:result constructor=* points=* round_number=*", "| sort constructor round_number", "| streamstats current=f last(points) as prev_points by constructor", "| eval points_delta=points-prev_points", "| timechart span=1mon sum(points_delta) as momentum by constructor"),
              "Tracks month-over-month constructor points momentum from Ergast race result exports.",
              "Momentum charts make championship fights easier to follow than raw standings alone.",
              "Ingest Ergast results with `constructor`, `points`, and `round_number` after each race weekend.",
              "Multi-series line chart of monthly points momentum.", "which F1 teams are gaining or losing ground in the championship fight."),
            S("Fantasy Team Budget Efficiency", "medium", "intermediate", ["Analytics", "Cost"],
              ("index=personal sourcetype=f1fantasy:team round_name=* team_points=* budget_spent_m=*", "| eval points_per_million=round(team_points/budget_spent_m,2)", "| sort - points_per_million", "| table round_name team_points budget_spent_m points_per_million"),
              "Calculates F1 Fantasy points scored per million of budget spent for each race round.",
              "Budget efficiency exposes whether you are overpaying for marquee drivers who under-deliver.",
              "Export fantasy team snapshots with `team_points` and `budget_spent_m` after each lock deadline.",
              "Bar chart of points per million by race round.", "how efficiently you spent your F1 Fantasy budget each race."),
            S("Watch Party Attendance vs Race Quality", "low", "beginner", ["Analytics", "Operations"],
              ("(index=personal sourcetype=race:watchparty guest_count=*) OR (index=personal sourcetype=ergast:result)", "| bin _time span=1w", "| stats max(guest_count) as guests, sum(eval(if(sourcetype=\"ergast:result\",1,0))) as races by _time", "| where races>0", "| sort - guests"),
              "Correlates race-weekend watch-party guest counts with Ergast result events on the same calendar week.",
              "Guest spikes on boring weekends may mean social draw beats on-track action for your crew.",
              "Log watch parties with `guest_count` and align weekly bins with Ergast race result timestamps.",
              "Scatter plot of guest count by race week.", "whether your watch parties get bigger on the most exciting race weekends."),
        ],
    },
    {
        "id": "100",
        "name": "Podcasts & Audiobooks",
        "app": "AntennaPod listening exports, Audible progress logs, Goodreads audiobook shelves, podcast queue snapshots, and listening streak counters ingested into Splunk HEC.",
        "ds": "AntennaPod episodes (`antennapod:episode`), Audible listening sessions (`audible:listen`), Goodreads audiobooks (`goodreads:audiobook`), podcast queues (`podcast:queue`), and listening streaks (`listen:streak`).",
        "refs": R(REF_ANTENNAPOD, REF_AUDIBLE, REF_GOODREADS),
        "sources": [
            {"label": "AntennaPod Episode", "friendly": "AntennaPod episode", "st": "antennapod:episode", "group_field": "podcast_name", "group_desc": "podcast", "value_field": "playback_seconds", "value_title": "Playback Seconds", "duration_field": "episode_minutes", "duration_title": "Episode Length", "status_field": "playback_status", "sync_hours": 72},
            {"label": "Audible Listen Session", "friendly": "Audible listen session", "st": "audible:listen", "group_field": "book_title", "group_desc": "book title", "value_field": "minutes_listened", "value_title": "Minutes Listened", "duration_field": "progress_pct", "duration_title": "Progress Percent", "status_field": "listen_status", "sync_hours": 72},
            {"label": "Goodreads Audiobook", "friendly": "Goodreads audiobook", "st": "goodreads:audiobook", "group_field": "shelf", "group_desc": "shelf", "value_field": "rating", "value_title": "Rating", "duration_field": "hours_length", "duration_title": "Book Length", "status_field": "read_status", "sync_hours": 168},
            {"label": "Podcast Queue Snapshot", "friendly": "podcast queue snapshot", "st": "podcast:queue", "group_field": "queue_name", "group_desc": "queue", "value_field": "episodes_queued", "value_title": "Episodes Queued", "duration_field": "queue_hours", "duration_title": "Queue Hours", "status_field": "queue_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": ["listen:streak"],
        "specials": [
            S("Listening Streak Break Alert", "low", "intermediate", ["Analytics", "Operations"],
              ("index=personal sourcetype=listen:streak streak_days=*", "| sort - _time", "| head 1", "| eval broken=if(streak_days=0,1,0)", "| where broken=1", "| table _time streak_days previous_best_days"),
              "Alerts when the current listening streak drops to zero after a previously active run.",
              "Streak breaks are the top dropout signal for audiobook and podcast habits worth restarting quickly.",
              "Publish daily `listen:streak` events with `streak_days` and alert when the count resets to zero.",
              "Single-value tile showing current streak with previous best.", "when your listening streak just broke so you can restart before the habit fades."),
            S("Audiobook Finish Rate by Genre", "low", "intermediate", ["Analytics", "Operations"],
              ("index=personal sourcetype=audible:listen book_title=* progress_pct=* genre=*", "| stats max(progress_pct) as max_progress by genre", "| eval finished=if(max_progress>=95,1,0)", "| stats sum(finished) as finished_books, count as started_books by genre", "| eval finish_rate=round(100*finished_books/started_books,1)", "| sort - finish_rate"),
              "Calculates audiobook completion rate by genre from Audible listening progress exports.",
              "Genre finish rates reveal whether you abandon nonfiction faster than fiction before buying the next title.",
              "Include `genre` and `progress_pct` on Audible exports and review finish rates before annual credits renew.",
              "Bar chart of finish rate percentage by genre.", "which kinds of audiobooks you actually finish versus abandon halfway."),
            S("Podcast Queue Overflow Hours", "medium", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=podcast:queue queue_hours=* episodes_queued=*", "| where queue_hours>20", "| sort - queue_hours", "| table queue_name episodes_queued queue_hours"),
              "Lists podcast queues whose total queued hours exceed twenty hours of listening backlog.",
              "Queue overflow means discovery outran listening; pruning prevents guilt-driven unsubscribes.",
              "Snapshot AntennaPod or app queues nightly with `queue_hours` and review overflow queues weekly.",
              "Table of queues sorted by backlog hours.", "podcast queues so long you would need a whole day just to catch up."),
            S("AntennaPod In-Progress Abandon Rate", "low", "intermediate", ["Analytics", "Quality"],
              ("index=personal sourcetype=antennapod:episode playback_status=* playback_seconds=* episode_minutes=*", "| eval completion_pct=round(100*playback_seconds/(episode_minutes*60),1)", "| eval abandoned=if(playback_status=\"started\" AND completion_pct<20,1,0)", "| stats sum(abandoned) as abandoned_episodes, count as started_episodes by podcast_name", "| eval abandon_pct=round(100*abandoned_episodes/started_episodes,1)", "| sort - abandon_pct", "| head 15"),
              "Measures how often episodes are started but abandoned below twenty percent completion by podcast.",
              "High abandon rates flag shows that looked good in the feed but did not earn your attention.",
              "Export AntennaPod playback with `playback_seconds` and `episode_minutes`, then rank podcasts by abandon rate.",
              "Bar chart of abandon percentage by podcast.", "which podcasts you keep starting but rarely stick with past the opening."),
        ],
    },
]


def write_metadata_file() -> Path:
    payload = [
        {
            "id": f"25.{sub['id']}",
            "name": sub["name"],
            "useCaseCount": EXPECTED_PER_SUB,
            "primaryAppTa": sub["app"],
            "dataSources": sub["ds"],
        }
        for sub in SUBCATEGORIES
    ]
    METADATA_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return METADATA_PATH


def collect_sourcetypes(sub: dict[str, object]) -> set[str]:
    sourcetypes = {str(src["st"]) for src in sub["sources"]}  # type: ignore[index]
    sourcetypes.update(str(st) for st in sub.get("extra_sourcetypes", []))
    return sourcetypes


def build_specs(sub: dict[str, object]) -> list[dict[str, object]]:
    specs = list(sub["specials"])  # type: ignore[arg-type]
    for source in sub["sources"]:  # type: ignore[index]
        specs.extend(G(source))
    assert len(specs) == EXPECTED_PER_SUB, f"25.{sub['id']} expected {EXPECTED_PER_SUB}, found {len(specs)}"
    return specs


def main() -> int:
    assert tuple(str(sub["id"]) for sub in SUBCATEGORIES) == TARGET_SUBS
    writer = Cat25Writer(append=True)
    for sub in TARGET_SUBS:
        assert writer.max_z.get(sub, 0) == 0, f"25.{sub} already has generated UCs; refusing to append"

    metadata_path = write_metadata_file()
    created: list[str] = []
    new_sourcetypes: set[str] = set()

    for sub in SUBCATEGORIES:
        specs = build_specs(sub)
        meta_refs = sub["refs"]  # type: ignore[assignment]
        for spec in specs:
            created.append(
                writer.U(
                    sub=str(sub["id"]),
                    title=str(spec["title"]),
                    crit=str(spec["crit"]),
                    diff=str(spec["diff"]),
                    mtypes=list(spec["mtypes"]),  # type: ignore[arg-type]
                    spl=str(spec["spl"]),
                    desc=str(spec["desc"]),
                    val=str(spec["val"]),
                    impl=str(spec["impl"]),
                    viz=str(spec["viz"]),
                    grandma_body=str(spec["grandma_body"]),
                    refs=meta_refs,
                    app=str(sub["app"]),
                    ds=str(sub["ds"]),
                )
            )
        new_sourcetypes.update(collect_sourcetypes(sub))

    total_added, by_sub = writer.summary()
    assert total_added == EXPECTED_PER_SUB * len(SUBCATEGORIES), f"expected 420 new UCs, found {total_added}"
    print(f"script_path={__file__}")
    print(f"metadata_path={metadata_path}")
    print(f"new_use_cases={total_added}")
    for sub in TARGET_SUBS:
        print(f"25.{sub}=+{by_sub.get(sub, 0)}")
    print(f"first_id={created[0]}")
    print(f"last_id={created[-1]}")
    print(f"new_sourcetypes={json.dumps(sorted(new_sourcetypes))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
