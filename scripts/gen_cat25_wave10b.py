#!/usr/bin/env python3
"""Generate cat-25 wave 10b use cases for subcategories 25.101-25.115."""
from __future__ import annotations

import json
from pathlib import Path

from gen_cat25_common import Cat25Writer, R
from gen_cat25_wave8a import G, S

EXPECTED_PER_SUB = 28
TARGET_SUBS = tuple(str(i) for i in range(101, 116))
METADATA_PATH = Path(__file__).resolve().with_name("wave10b_subcategories.json")

REF_LEMONADE = ("Lemonade Insurance API", "https://www.lemonade.com/")
REF_TURBOTAX = ("TurboTax", "https://turbotax.intuit.com/")
REF_IRS = ("IRS Tax Transcript API", "https://www.irs.gov/individuals/get-transcript")
REF_SWIMCOM = ("Swim.com", "https://www.swim.com/")
REF_MYSWIMPRO = ("MySwimPro", "https://www.myswimpro.com/")
REF_CUROLOGY = ("Curology", "https://curology.com/")
REF_AIRBNB = ("Airbnb API", "https://developer.airbnb.com/")
REF_VRBO = ("Vrbo Partner API", "https://www.vrbo.com/partner/")
REF_CHRONO24 = ("Chrono24 API", "https://www.chrono24.com/info/api.htm")
REF_CELLARTRACKER = ("CellarTracker API", "https://www.cellartracker.com/")
REF_VIVINO = ("Vivino API", "https://developers.vivino.com/")
REF_ROBOROCK = ("Roborock Developer", "https://www.roborock.com/")
REF_GOODRX = ("GoodRx API", "https://www.goodrx.com/")
REF_CVS = ("CVS Pharmacy", "https://www.cvs.com/")
REF_GITHUB = ("GitHub REST API", "https://docs.github.com/en/rest")
REF_NEXTDOOR = ("Nextdoor API", "https://developer.nextdoor.com/")
REF_RING = ("Ring Neighbors API", "https://developer.ring.com/")
REF_HOTSPRING = ("Hot Spring Spas", "https://www.hotspringspas.com/")
REF_TRUPANION = ("Trupanion", "https://trupanion.com/")
REF_WARBY = ("Warby Parker", "https://www.warbyparker.com/")

SUBCATEGORIES: list[dict[str, object]] = [
    {
        "id": "101",
        "name": "Home Insurance & Claims",
        "app": "Lemonade policy exports, home claim filings, premium billing snapshots, renewal offer logs, and coverage review notes streamed into Splunk HEC under `index=personal`.",
        "ds": "Lemonade policies (`lemonade:policy`), home claims (`claim:home`), premium bills (`homeinsurance:premium`), and renewal offers (`homeinsurance:renewal`).",
        "refs": R(REF_LEMONADE),
        "sources": [
            {"label": "Lemonade Policy", "friendly": "Lemonade policy", "st": "lemonade:policy", "group_field": "policy_type", "group_desc": "policy type", "value_field": "coverage_usd", "value_title": "Coverage Amount", "duration_field": "term_months", "duration_title": "Term Length", "status_field": "policy_status", "sync_hours": 720},
            {"label": "Home Claim", "friendly": "home insurance claim", "st": "claim:home", "group_field": "claim_type", "group_desc": "claim type", "value_field": "payout_usd", "value_title": "Payout Amount", "duration_field": "days_open", "duration_title": "Days Open", "status_field": "claim_status", "sync_hours": 168},
            {"label": "Home Insurance Premium", "friendly": "home insurance premium", "st": "homeinsurance:premium", "group_field": "carrier_name", "group_desc": "carrier", "value_field": "premium_usd", "value_title": "Premium Amount", "duration_field": "billing_cycle_days", "duration_title": "Billing Cycle", "status_field": "payment_status", "sync_hours": 720},
            {"label": "Home Insurance Renewal", "friendly": "home insurance renewal", "st": "homeinsurance:renewal", "group_field": "policy_id", "group_desc": "policy", "value_field": "renewal_premium_usd", "value_title": "Renewal Premium", "duration_field": "days_until_renewal", "duration_title": "Days Until Renewal", "status_field": "renewal_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Renewal Premium Increase Alert", "high", "intermediate", ["Cost", "Risk"],
              ("index=personal sourcetype=homeinsurance:renewal renewal_premium_usd=* prior_premium_usd=*", "| eval increase_pct=round(100*(renewal_premium_usd-prior_premium_usd)/nullif(prior_premium_usd,0),1)", "| where increase_pct>=10", "| sort - increase_pct", "| table policy_id renewal_premium_usd prior_premium_usd increase_pct days_until_renewal"),
              "Flags home insurance renewals where the quoted premium rose ten percent or more versus the prior term.",
              "Renewal shock is easier to negotiate when you see the percentage jump before the auto-pay date hits.",
              "Include `prior_premium_usd` and `renewal_premium_usd` on each renewal export and review increases sixty days ahead.",
              "Table of policies sorted by renewal premium increase percent.", "when your home insurance renewal quote jumped noticeably compared with last year."),
            S("Open Claim Aging Watch", "high", "intermediate", ["Operations", "Risk"],
              ("index=personal sourcetype=claim:home claim_status=* days_open=*", "| where claim_status!=\"closed\" AND days_open>30", "| sort - days_open", "| table claim_type claim_status days_open payout_usd"),
              "Lists open home insurance claims that have remained unresolved for more than thirty days.",
              "Stale claims often mean missing documentation or adjuster follow-up that you can nudge proactively.",
              "Log `days_open` and `claim_status` on every claim event and review the aging queue weekly during repairs.",
              "Table of open claims ranked by days open.", "home insurance claims that have dragged on more than a month without closing."),
            S("Premium vs Coverage Value Ratio", "medium", "intermediate", ["Analytics", "Cost"],
              ("index=personal sourcetype=lemonade:policy coverage_usd=* premium_annual_usd=*", "| eval cost_per_1k=round(1000*premium_annual_usd/coverage_usd,2)", "| sort - cost_per_1k", "| table policy_type coverage_usd premium_annual_usd cost_per_1k"),
              "Calculates annual premium dollars per thousand dollars of dwelling coverage for each policy type.",
              "Cost-per-coverage helps compare Lemonade quotes against broker alternatives on equal footing.",
              "Export policies with `coverage_usd` and annualized premium, then rank by cost per thousand covered.",
              "Bar chart of cost per thousand coverage by policy type.", "how expensive each home policy is relative to the amount of coverage you actually have."),
            S("Claim Frequency by Peril Type", "medium", "intermediate", ["Analytics", "Risk"],
              ("index=personal sourcetype=claim:home claim_type=*", "| bin _time span=1y", "| stats count as claims, sum(payout_usd) as total_payout by _time claim_type", "| chart sum(claims) over _time by claim_type"),
              "Trends annual home claim counts and payout totals grouped by peril or claim type.",
              "Peril-frequency patterns reveal whether deductibles or riders should shift before the next renewal cycle.",
              "Ensure each claim export includes `claim_type` and `payout_usd`, then review the yearly mix before renewal.",
              "Stacked column chart of claims by year and peril type.", "which kinds of home damage you claim for most often over the years."),
        ],
    },
    {
        "id": "102",
        "name": "Tax Prep & Filing",
        "app": "TurboTax return exports, IRS transcript pulls, tax estimate calculators, payment confirmations, and W-2 import logs ingested into Splunk HEC.",
        "ds": "TurboTax returns (`turbotax:return`), IRS transcripts (`irs:transcript`), tax estimates (`tax:estimate`), tax payments (`tax:payment`), and W-2 imports (`w2:import`).",
        "refs": R(REF_TURBOTAX, REF_IRS),
        "sources": [
            {"label": "TurboTax Return", "friendly": "TurboTax return", "st": "turbotax:return", "group_field": "filing_status", "group_desc": "filing status", "value_field": "refund_usd", "value_title": "Refund Amount", "duration_field": "prep_minutes", "duration_title": "Prep Time", "status_field": "return_status", "sync_hours": 720},
            {"label": "IRS Transcript", "friendly": "IRS transcript", "st": "irs:transcript", "group_field": "transcript_type", "group_desc": "transcript type", "value_field": "reported_income_usd", "value_title": "Reported Income", "duration_field": "processing_days", "duration_title": "Processing Days", "status_field": "transcript_status", "sync_hours": 720},
            {"label": "Tax Estimate", "friendly": "tax estimate", "st": "tax:estimate", "group_field": "tax_year", "group_desc": "tax year", "value_field": "estimated_liability_usd", "value_title": "Estimated Liability", "duration_field": "quarter_number", "duration_title": "Quarter", "status_field": "estimate_status", "sync_hours": 720},
            {"label": "Tax Payment", "friendly": "tax payment", "st": "tax:payment", "group_field": "payment_method", "group_desc": "payment method", "value_field": "payment_usd", "value_title": "Payment Amount", "duration_field": "days_before_deadline", "duration_title": "Days Before Deadline", "status_field": "payment_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": ["w2:import"],
        "specials": [
            S("W-2 Import Mismatch vs Transcript", "high", "advanced", ["Data Quality", "Compliance"],
              ("index=personal sourcetype=w2:import wages_usd=* employer_ein=* tax_year=*", "| join type=inner employer_ein tax_year [search index=personal sourcetype=irs:transcript transcript_type=\"wage\" reported_income_usd=* | rename reported_income_usd as transcript_wages]", "| eval wage_delta=round(wages_usd-transcript_wages,2)", "| where abs(wage_delta)>100", "| table employer_ein tax_year wages_usd transcript_wages wage_delta"),
              "Compares imported W-2 wage totals against IRS wage transcript amounts for the same employer and tax year.",
              "W-2 versus transcript gaps catch typos before e-file acceptance or an IRS mismatch letter arrives.",
              "Share `employer_ein`, `tax_year`, and wage fields across W-2 imports and IRS transcript pulls.",
              "Table of employers with wage delta in dollars.", "when your W-2 wages do not match what the IRS transcript says your employer reported."),
            S("Estimated Tax Underpayment Risk", "high", "intermediate", ["Compliance", "Risk"],
              ("index=personal sourcetype=tax:estimate estimated_liability_usd=* payments_made_usd=* quarter_number=*", "| eval shortfall_usd=estimated_liability_usd-payments_made_usd", "| where shortfall_usd>500", "| sort - shortfall_usd", "| table tax_year quarter_number estimated_liability_usd payments_made_usd shortfall_usd"),
              "Flags quarterly tax estimates where recorded payments fall more than five hundred dollars short of liability.",
              "Underpayment penalties are avoidable when quarterly gaps show up before the deadline, not after.",
              "Track `estimated_liability_usd` and cumulative `payments_made_usd` each quarter and alert on large shortfalls.",
              "Table of quarters with estimated tax shortfall.", "quarters where you probably have not paid enough estimated tax yet."),
            S("Return Prep Time Trend", "low", "intermediate", ["Analytics", "Operations"],
              ("index=personal sourcetype=turbotax:return prep_minutes=* tax_year=*", "| timechart span=1y avg(prep_minutes) as avg_prep, max(prep_minutes) as worst_prep by filing_status", "| fillnull value=0"),
              "Trends average and maximum TurboTax return preparation minutes by filing status across tax years.",
              "Prep-time drift shows when life complexity outgrew DIY and a CPA might save hours and mistakes.",
              "Log `prep_minutes` and `filing_status` on each return session and compare year-over-year averages.",
              "Multi-series line chart of prep minutes by filing status.", "whether doing your taxes yourself is taking longer each year."),
            S("Payment Before Deadline Compliance", "medium", "beginner", ["Compliance", "Operations"],
              ("index=personal sourcetype=tax:payment days_before_deadline=* payment_status=*", "| eval late=if(days_before_deadline<0 OR match(lower(payment_status),\"late|failed\"),1,0)", "| stats sum(late) as late_payments, count as total_payments by tax_year", "| eval late_pct=round(100*late_payments/total_payments,1)", "| sort tax_year"),
              "Measures what percentage of tax payments were late or submitted after the deadline each year.",
              "Late payment history triggers penalties and audit attention that a simple compliance view prevents.",
              "Include `days_before_deadline` and `payment_status` on every payment confirmation export.",
              "Column chart of late payment percentage by tax year.", "how often your tax payments missed the deadline or went in late."),
        ],
    },
    {
        "id": "103",
        "name": "Swimming & Lap Training",
        "app": "Swim.com workout exports, MySwimPro session logs, pool lap counters, swim meet results, and interval pace trackers forwarded to Splunk HEC.",
        "ds": "Swim.com workouts (`swimcom:workout`), MySwimPro sessions (`myswimpro:session`), pool lap logs (`pool:lap`), and swim meet results (`swim:meet`).",
        "refs": R(REF_SWIMCOM, REF_MYSWIMPRO),
        "sources": [
            {"label": "Swim.com Workout", "friendly": "Swim.com workout", "st": "swimcom:workout", "group_field": "stroke_type", "group_desc": "stroke", "value_field": "distance_m", "value_title": "Distance", "duration_field": "workout_minutes", "duration_title": "Workout Time", "status_field": "workout_status", "sync_hours": 72},
            {"label": "MySwimPro Session", "friendly": "MySwimPro session", "st": "myswimpro:session", "group_field": "drill_name", "group_desc": "drill", "value_field": "swolf_score", "value_title": "SWOLF Score", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 72},
            {"label": "Pool Lap Log", "friendly": "pool lap log", "st": "pool:lap", "group_field": "pool_name", "group_desc": "pool", "value_field": "lap_count", "value_title": "Lap Count", "duration_field": "pace_per_100m", "duration_title": "Pace per 100m", "status_field": "session_status", "sync_hours": 72},
            {"label": "Swim Meet Result", "friendly": "swim meet result", "st": "swim:meet", "group_field": "event_name", "group_desc": "event", "value_field": "finish_time_seconds", "value_title": "Finish Time", "duration_field": "reaction_time_ms", "duration_title": "Reaction Time", "status_field": "result_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("SWOLF Improvement Trend", "low", "intermediate", ["Performance", "Analytics"],
              ("index=personal sourcetype=myswimpro:session swolf_score=* stroke_type=*", "| timechart span=1w avg(swolf_score) as avg_swolf, min(swolf_score) as best_swolf by stroke_type", "| fillnull value=0"),
              "Trends weekly average and best MySwimPro SWOLF scores by stroke type.",
              "SWOLF combines stroke count and time; trending it shows efficiency gains better than distance alone.",
              "Export MySwimPro sessions with `swolf_score` and `stroke_type`, then review weekly averages after each block.",
              "Multi-series line chart of SWOLF by stroke and week.", "whether your swim efficiency is getting better week by week."),
            S("Weekly Pool Distance Total", "medium", "beginner", ["Analytics", "Performance"],
              ("(index=personal sourcetype=swimcom:workout distance_m=*) OR (index=personal sourcetype=pool:lap lap_count=* pool_length_m=*)", "| eval distance=coalesce(distance_m, lap_count*pool_length_m)", "| bin _time span=1w", "| stats sum(distance) as weekly_meters by _time", "| eval weekly_km=round(weekly_meters/1000,2)", "| sort - _time"),
              "Totals weekly swim distance in kilometers from Swim.com workouts and pool lap logs.",
              "Weekly volume is the foundation metric for endurance progress and overuse-injury prevention in masters swimming.",
              "Normalize distance from both feeds into meters and chart weekly totals against your training plan target.",
              "Column chart of weekly kilometers swum.", "how many kilometers you swam each week across pool and open-water logs."),
            S("Meet Time Personal Best Delta", "medium", "intermediate", ["Performance", "Analytics"],
              ("index=personal sourcetype=swim:meet event_name=* finish_time_seconds=*", "| stats min(finish_time_seconds) as best_time, latest(finish_time_seconds) as latest_time by event_name", "| eval delta_seconds=round(latest_time-best_time,2)", "| sort delta_seconds", "| table event_name best_time latest_time delta_seconds"),
              "Compares latest swim meet finish times against personal bests for each event.",
              "Race-day deltas show whether training cycles are converting to faster times when it counts.",
              "Log `event_name` and `finish_time_seconds` for every meet and review deltas after each competition.",
              "Table of events with best, latest, and delta seconds.", "how your most recent race times compare with your personal bests."),
            S("Missed Workout Streak Break", "low", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=swimcom:workout", "| bin _time span=1d", "| stats count as sessions by _time", "| sort _time", "| streamstats current=f last(_time) as prev_day", "| eval gap_days=round((_time-prev_day)/86400,0)", "| where gap_days>=7 AND sessions>0", "| stats max(gap_days) as longest_break_days"),
              "Finds the longest gap of seven or more days between logged Swim.com workout days.",
              "Long pool absences erode feel for the water; catching the break early makes returning less painful.",
              "Run daily on Swim.com session counts and alert when the quiet gap exceeds your restart threshold.",
              "Single-value tile for longest workout break in days.", "the longest stretch you went without a logged swim workout."),
        ],
    },
    {
        "id": "104",
        "name": "Skincare & Dermatology",
        "app": "Curology prescription shipments, daily skin diary entries, dermatology appointment exports, and UV exposure tracker logs ingested into Splunk HEC.",
        "ds": "Curology prescriptions (`curology:prescription`), skin diaries (`skin:diary`), dermatology appointments (`derm:appointment`), and UV exposure logs (`uv:exposure`).",
        "refs": R(REF_CUROLOGY),
        "sources": [
            {"label": "Curology Prescription", "friendly": "Curology prescription", "st": "curology:prescription", "group_field": "formula_name", "group_desc": "formula", "value_field": "bottle_days_supply", "value_title": "Days Supply", "duration_field": "days_since_ship", "duration_title": "Days Since Ship", "status_field": "rx_status", "sync_hours": 720},
            {"label": "Skin Diary Entry", "friendly": "skin diary entry", "st": "skin:diary", "group_field": "concern_type", "group_desc": "concern", "value_field": "severity_score", "value_title": "Severity Score", "duration_field": "sleep_hours", "duration_title": "Sleep Hours", "status_field": "diary_status", "sync_hours": 72},
            {"label": "Dermatology Appointment", "friendly": "dermatology appointment", "st": "derm:appointment", "group_field": "provider_name", "group_desc": "provider", "value_field": "copay_usd", "value_title": "Copay", "duration_field": "wait_minutes", "duration_title": "Wait Time", "status_field": "appt_status", "sync_hours": 720},
            {"label": "UV Exposure Log", "friendly": "UV exposure log", "st": "uv:exposure", "group_field": "location", "group_desc": "location", "value_field": "uv_index", "value_title": "UV Index", "duration_field": "exposure_minutes", "duration_title": "Exposure Minutes", "status_field": "exposure_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Severity Trend vs Prescription Refill", "medium", "advanced", ["Analytics", "Patient Safety"],
              ("(index=personal sourcetype=skin:diary severity_score=*) OR (index=personal sourcetype=curology:prescription rx_status=\"shipped\")", "| bin _time span=1w", "| stats avg(severity_score) as avg_severity, count(eval(sourcetype=\"curology:prescription\")) as refills by _time concern_type", "| sort _time"),
              "Lines up weekly average skin concern severity with Curology refill shipment counts.",
              "When severity rises despite regular refills, it is time to message your derm or adjust the formula.",
              "Export diary `severity_score` by `concern_type` and align weekly bins with prescription ship events.",
              "Dual-axis chart of severity and refill count by week.", "whether your skin scores are improving after each new prescription shipment."),
            S("UV Overexposure Day Alert", "high", "intermediate", ["Safety", "Risk"],
              ("index=personal sourcetype=uv:exposure uv_index=* exposure_minutes=*", "| eval high_uv=if(uv_index>=8 AND exposure_minutes>=30,1,0)", "| where high_uv=1", "| stats count as overexposure_days, max(uv_index) as peak_uv by location", "| sort - overexposure_days"),
              "Counts days with UV index eight or above and at least thirty minutes of logged exposure by location.",
              "High-UV overexposure days drive photoaging and flare-ups that sunscreen reminders alone miss.",
              "Log `uv_index` and `exposure_minutes` from your wearable or weather app and review weekly peaks.",
              "Table of locations with overexposure day counts.", "days you spent too long in strong sun without enough protection."),
            S("Derm Appointment Interval Breach", "medium", "intermediate", ["Operations", "Compliance"],
              ("index=personal sourcetype=derm:appointment patient_id=* appt_date=*", "| stats max(appt_date) as last_visit by patient_id concern_type", "| eval days_since=round((now()-strptime(last_visit,\"%Y-%m-%d\"))/86400,0)", "| where days_since>365", "| sort - days_since"),
              "Flags skin concerns whose last dermatology visit was more than twelve months ago.",
              "Annual derm checks catch changes early; overdue intervals let mole checks and prescription renewals slip.",
              "Emit one `derm:appointment` event per visit with ISO `appt_date` and review overdue concerns quarterly.",
              "Table of concerns by days since last derm visit.", "skin issues you have not had a dermatologist look at in over a year."),
            S("Prescription Supply Gap Before Refill", "high", "beginner", ["Operations", "Risk"],
              ("index=personal sourcetype=curology:prescription bottle_days_supply=* days_since_ship=*", "| eval days_remaining=bottle_days_supply-days_since_ship", "| where days_remaining<=5 AND rx_status!=\"shipped\"", "| sort days_remaining", "| table formula_name days_remaining rx_status"),
              "Lists Curology prescriptions with five or fewer days of supply remaining before the next shipment.",
              "Running out of active ingredients mid-routine can trigger breakouts that take weeks to calm down.",
              "Track `bottle_days_supply` and `days_since_ship` on each bottle and alert before the supply gap.",
              "Table of formulas sorted by days remaining.", "when your skincare prescription is about to run out before the next bottle arrives."),
        ],
    },
    {
        "id": "105",
        "name": "Estate Planning & Legal",
        "app": "Trust document vault exports, will status trackers, power-of-attorney records, and estate review checklists forwarded to Splunk HEC.",
        "ds": "Trust documents (`trust:document`), will status logs (`will:status`), power-of-attorney records (`poa:record`), and estate review sessions (`estate:review`).",
        "refs": R(REF_LEMONADE),
        "sources": [
            {"label": "Trust Document", "friendly": "trust document", "st": "trust:document", "group_field": "document_type", "group_desc": "document type", "value_field": "asset_value_usd", "value_title": "Asset Value", "duration_field": "days_since_update", "duration_title": "Days Since Update", "status_field": "document_status", "sync_hours": 720},
            {"label": "Will Status", "friendly": "will status", "st": "will:status", "group_field": "jurisdiction", "group_desc": "jurisdiction", "value_field": "beneficiary_count", "value_title": "Beneficiary Count", "duration_field": "years_since_signed", "duration_title": "Years Since Signed", "status_field": "will_status", "sync_hours": 720},
            {"label": "Power of Attorney Record", "friendly": "power of attorney record", "st": "poa:record", "group_field": "poa_type", "group_desc": "POA type", "value_field": "agent_count", "value_title": "Agent Count", "duration_field": "days_until_expiry", "duration_title": "Days Until Expiry", "status_field": "poa_status", "sync_hours": 720},
            {"label": "Estate Review Session", "friendly": "estate review session", "st": "estate:review", "group_field": "review_type", "group_desc": "review type", "value_field": "action_items_open", "value_title": "Open Action Items", "duration_field": "review_minutes", "duration_title": "Review Time", "status_field": "review_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("POA Expiry Within Ninety Days", "high", "intermediate", ["Compliance", "Risk"],
              ("index=personal sourcetype=poa:record days_until_expiry=* poa_status=*", "| where days_until_expiry<=90 AND days_until_expiry>=0 AND poa_status=\"active\"", "| sort days_until_expiry", "| table poa_type agent_name days_until_expiry jurisdiction"),
              "Lists active powers of attorney expiring within the next ninety days.",
              "Expired POA documents fail exactly when a family crisis needs them; early renewal avoids court delays.",
              "Include `days_until_expiry` and `poa_status` on each POA record and review quarterly with your attorney.",
              "Table of POAs sorted by days until expiry.", "power-of-attorney documents that expire soon and need renewal."),
            S("Will Stale Signature Alert", "high", "intermediate", ["Compliance", "Governance"],
              ("index=personal sourcetype=will:status years_since_signed=* will_status=*", "| where years_since_signed>=5 OR will_status=\"needs_update\"", "| sort - years_since_signed", "| table jurisdiction years_since_signed beneficiary_count will_status"),
              "Flags wills signed five or more years ago or marked as needing update.",
              "Life changes make old wills dangerous; stale-signature alerts prompt reviews after births, moves, or divorces.",
              "Track `years_since_signed` and `will_status` on each will export and schedule reviews after major life events.",
              "Table of wills ranked by years since signed.", "wills that are old enough they probably do not match your life anymore."),
            S("Trust Document Update Backlog", "medium", "intermediate", ["Operations", "Governance"],
              ("index=personal sourcetype=trust:document days_since_update=* document_status=*", "| where days_since_update>730 AND document_status!=\"current\"", "| sort - days_since_update", "| table document_type asset_value_usd days_since_update document_status"),
              "Surfaces trust documents not marked current and unchanged for more than two years.",
              "Outdated trust schedules miss new accounts and property, creating probate gaps you thought you closed.",
              "Log `days_since_update` and `document_status` for each trust document and review the backlog annually.",
              "Table of stale trust documents by days since update.", "trust paperwork that has not been updated in more than two years."),
            S("Estate Review Action Item Closure Rate", "low", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=estate:review action_items_open=* action_items_total=*", "| eval closure_pct=round(100*(action_items_total-action_items_open)/nullif(action_items_total,0),1)", "| stats avg(closure_pct) as avg_closure, max(action_items_open) as max_open by review_type", "| sort - max_open"),
              "Calculates average action-item closure percentage from estate review sessions by review type.",
              "Open action items after attorney meetings mean recommendations never reached your binder or beneficiaries.",
              "Capture `action_items_open` and `action_items_total` per review and track closure before the next session.",
              "Bar chart of closure percentage by review type.", "how much of your estate planning homework actually got done after each review."),
        ],
    },
    {
        "id": "106",
        "name": "Short-term Rental Hosting",
        "app": "Airbnb booking exports, Vrbo reservation webhooks, Airbnb payout statements, guest review logs, and turnover checklists streamed into Splunk HEC.",
        "ds": "Airbnb bookings (`airbnb:booking`), Vrbo reservations (`vrbo:reservation`), Airbnb payouts (`airbnb:payout`), and guest reviews (`guest:review`).",
        "refs": R(REF_AIRBNB, REF_VRBO),
        "sources": [
            {"label": "Airbnb Booking", "friendly": "Airbnb booking", "st": "airbnb:booking", "group_field": "listing_name", "group_desc": "listing", "value_field": "nightly_rate_usd", "value_title": "Nightly Rate", "duration_field": "stay_nights", "duration_title": "Stay Nights", "status_field": "booking_status", "sync_hours": 48},
            {"label": "Vrbo Reservation", "friendly": "Vrbo reservation", "st": "vrbo:reservation", "group_field": "property_name", "group_desc": "property", "value_field": "total_usd", "value_title": "Total Amount", "duration_field": "lead_days", "duration_title": "Booking Lead Time", "status_field": "reservation_status", "sync_hours": 48},
            {"label": "Airbnb Payout", "friendly": "Airbnb payout", "st": "airbnb:payout", "group_field": "listing_name", "group_desc": "listing", "value_field": "payout_usd", "value_title": "Payout Amount", "duration_field": "days_to_payout", "duration_title": "Days to Payout", "status_field": "payout_status", "sync_hours": 168},
            {"label": "Guest Review", "friendly": "guest review", "st": "guest:review", "group_field": "listing_name", "group_desc": "listing", "value_field": "rating", "value_title": "Rating", "duration_field": "response_hours", "duration_title": "Response Time", "status_field": "review_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Guest Rating Below Superhost Threshold", "high", "intermediate", ["Quality", "Risk"],
              ("index=personal sourcetype=guest:review rating=* listing_name=*", "| bin _time span=1q", "| stats avg(rating) as avg_rating, count as reviews by _time listing_name", "| where avg_rating<4.8 AND reviews>=3", "| sort avg_rating"),
              "Flags listings whose quarterly average guest rating falls below the typical Superhost threshold.",
              "Rating slippage is easier to fix mid-quarter than after Airbnb removes your Superhost badge.",
              "Export guest reviews with numeric `rating` and review at least three reviews per listing each quarter.",
              "Table of listings with quarterly average rating.", "rental listings whose guest ratings are slipping below Superhost levels."),
            S("Occupancy Gap Between Bookings", "medium", "intermediate", ["Revenue Assurance", "Analytics"],
              ("index=personal sourcetype=airbnb:booking listing_name=* checkout_date=* checkin_date=*", "| sort listing_name checkout_date", "| streamstats current=f last(checkout_date) as prev_checkout by listing_name", "| eval gap_nights=round((strptime(checkin_date,\"%Y-%m-%d\")-strptime(prev_checkout,\"%Y-%m-%d\"))/86400,0)", "| where gap_nights>3", "| sort - gap_nights"),
              "Finds gaps of more than three nights between consecutive bookings on the same listing.",
              "Vacancy gaps are lost revenue; seeing them on a calendar helps you adjust minimum stays or pricing.",
              "Include ISO `checkin_date` and `checkout_date` on each booking and compute inter-booking gaps nightly.",
              "Table of listings with gap nights between stays.", "nights your rental sat empty between back-to-back guest bookings."),
            S("Payout Delay Beyond Expected Window", "high", "intermediate", ["Operations", "Revenue Assurance"],
              ("index=personal sourcetype=airbnb:payout days_to_payout=* payout_status=*", "| where days_to_payout>7 AND payout_status!=\"completed\"", "| sort - days_to_payout", "| table listing_name payout_usd days_to_payout payout_status"),
              "Lists Airbnb payouts that took more than seven days to complete.",
              "Delayed payouts often signal dispute holds or tax documentation issues worth resolving before cash-flow crunch.",
              "Track `days_to_payout` from checkout to bank deposit and alert when payouts exceed your normal window.",
              "Table of delayed payouts sorted by days to payout.", "Airbnb payouts that took unusually long to hit your bank account."),
            S("Airbnb vs Vrbo Revenue Mix", "low", "intermediate", ["Analytics", "Business"],
              ("(index=personal sourcetype=airbnb:booking nightly_rate_usd=* stay_nights=*) OR (index=personal sourcetype=vrbo:reservation total_usd=*)", "| eval revenue=coalesce(nightly_rate_usd*stay_nights,total_usd)", "| bin _time span=1q", "| stats sum(revenue) as quarterly_revenue by _time platform=case(sourcetype=\"airbnb:booking\",\"Airbnb\",sourcetype=\"vrbo:reservation\",\"Vrbo\",1=1,\"Other\")", "| chart sum(quarterly_revenue) over _time by platform"),
              "Compares quarterly rental revenue between Airbnb and Vrbo channels.",
              "Channel mix shows whether diversification is real or whether one platform carries all your income risk.",
              "Normalize revenue from both booking feeds and review the quarterly split before renewing channel subscriptions.",
              "Stacked column chart of revenue by platform and quarter.", "how much rental income came from Airbnb versus Vrbo each quarter."),
        ],
    },
    {
        "id": "107",
        "name": "Watch Collecting & Horology",
        "app": "Chrono24 listing snapshots, WatchBox service records, wrist-time wear logs, and in-house service history exports ingested into Splunk HEC.",
        "ds": "Chrono24 listings (`chrono24:listing`), WatchBox service records (`watchbox:service`), wrist-time logs (`watch:wristtime`), and watch service history (`watch:service`).",
        "refs": R(REF_CHRONO24),
        "sources": [
            {"label": "Chrono24 Listing", "friendly": "Chrono24 listing", "st": "chrono24:listing", "group_field": "brand", "group_desc": "brand", "value_field": "ask_price_usd", "value_title": "Ask Price", "duration_field": "days_listed", "duration_title": "Days Listed", "status_field": "listing_status", "sync_hours": 24},
            {"label": "WatchBox Service Record", "friendly": "WatchBox service record", "st": "watchbox:service", "group_field": "service_type", "group_desc": "service type", "value_field": "service_cost_usd", "value_title": "Service Cost", "duration_field": "turnaround_days", "duration_title": "Turnaround Days", "status_field": "service_status", "sync_hours": 720},
            {"label": "Watch Wrist Time Log", "friendly": "watch wrist-time log", "st": "watch:wristtime", "group_field": "reference_number", "group_desc": "reference", "value_field": "wear_hours", "value_title": "Wear Hours", "duration_field": "days_since_wear", "duration_title": "Days Since Wear", "status_field": "wear_status", "sync_hours": 168},
            {"label": "Watch Service History", "friendly": "watch service history", "st": "watch:service", "group_field": "reference_number", "group_desc": "reference", "value_field": "service_interval_years", "value_title": "Service Interval", "duration_field": "days_since_service", "duration_title": "Days Since Service", "status_field": "service_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Market Ask Below Purchase Cost", "high", "intermediate", ["Cost", "Analytics"],
              ("index=personal sourcetype=chrono24:listing reference_number=* ask_price_usd=*", "| join type=inner reference_number [search index=personal sourcetype=watch:wristtime | stats latest(purchase_price_usd) as cost by reference_number]", "| eval loss_usd=round(cost-ask_price_usd,2)", "| where loss_usd>0", "| sort - loss_usd", "| table reference_number brand cost ask_price_usd loss_usd"),
              "Finds watches whose current Chrono24 ask is below recorded purchase cost.",
              "Underwater references help decide whether to hold, sell, or rotate pieces before the market moves further.",
              "Maintain `purchase_price_usd` per reference and compare nightly against Chrono24 `ask_price_usd`.",
              "Table of references with market loss amount.", "watches worth less on the market right now than you paid for them."),
            S("Service Interval Overdue by Reference", "high", "intermediate", ["Operations", "Risk"],
              ("index=personal sourcetype=watch:service days_since_service=* service_interval_years=* reference_number=*", "| eval interval_days=service_interval_years*365", "| where days_since_service>interval_days", "| sort - days_since_service", "| table reference_number brand days_since_service interval_days"),
              "Flags watches whose days since last service exceed the manufacturer-recommended interval.",
              "Overdue service on automatic movements risks magnetization damage and resale value loss at sale time.",
              "Log `days_since_service` and recommended `service_interval_years` per reference and review quarterly.",
              "Table of overdue references ranked by days past interval.", "watches that are past due for a service based on the recommended interval."),
            S("Rotation Neglect for In-Rotation Pieces", "low", "intermediate", ["Inventory", "Operations"],
              ("index=personal sourcetype=watch:wristtime reference_number=* days_since_wear=*", "| where days_since_wear>21", "| sort - days_since_wear", "| table reference_number brand days_since_wear wear_hours"),
              "Lists watches in the active rotation not worn for more than twenty-one days.",
              "Unworn rotation pieces still need winding and wear to keep oils distributed and straps from dry rotting.",
              "Log each wear session with `days_since_wear` and review neglected references monthly.",
              "Table of references sorted by days since last wear.", "watches in your rotation you have not worn in three weeks or more."),
            S("Chrono24 Listing Stale Inventory", "medium", "intermediate", ["Operations", "Business"],
              ("index=personal sourcetype=chrono24:listing listing_status=\"active\" days_listed=*", "| where days_listed>60", "| stats count as stale_listings, avg(ask_price_usd) as avg_ask by brand reference_number", "| sort - stale_listings", "| head 15"),
              "Surfaces Chrono24 listings active for more than sixty days without selling.",
              "Stale listings usually mean ask price is optimistic or photos need refresh before capital stays locked up.",
              "Export active listings with `days_listed` and review stale references biweekly for repricing.",
              "Table of stale listings by reference with average ask.", "watches listed so long on Chrono24 they probably need a price adjustment."),
        ],
    },
    {
        "id": "108",
        "name": "Wine & Spirits Cellar",
        "app": "CellarTracker bottle exports, Vivino wine scans, spirits inventory logs, and tasting note journals forwarded to Splunk HEC.",
        "ds": "CellarTracker bottles (`cellartracker:bottle`), Vivino wines (`vivino:wine`), spirits bottles (`spirit:bottle`), and wine tasting notes (`wine:tasting`).",
        "refs": R(REF_CELLARTRACKER, REF_VIVINO),
        "sources": [
            {"label": "CellarTracker Bottle", "friendly": "CellarTracker bottle", "st": "cellartracker:bottle", "group_field": "region", "group_desc": "region", "value_field": "bottle_value_usd", "value_title": "Bottle Value", "duration_field": "vintage_year", "duration_title": "Vintage Year", "status_field": "bottle_status", "sync_hours": 720},
            {"label": "Vivino Wine Scan", "friendly": "Vivino wine scan", "st": "vivino:wine", "group_field": "wine_name", "group_desc": "wine", "value_field": "vivino_rating", "value_title": "Vivino Rating", "duration_field": "scan_count", "duration_title": "Scan Count", "status_field": "scan_status", "sync_hours": 168},
            {"label": "Spirits Bottle", "friendly": "spirits bottle", "st": "spirit:bottle", "group_field": "spirit_type", "group_desc": "spirit type", "value_field": "abv_pct", "value_title": "ABV Percent", "duration_field": "fill_level_pct", "duration_title": "Fill Level", "status_field": "bottle_status", "sync_hours": 720},
            {"label": "Wine Tasting Note", "friendly": "wine tasting note", "st": "wine:tasting", "group_field": "tasting_type", "group_desc": "tasting type", "value_field": "score", "value_title": "Score", "duration_field": "tasting_minutes", "duration_title": "Tasting Time", "status_field": "tasting_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Bottle Past Drinking Window", "medium", "intermediate", ["Risk", "Inventory"],
              ("index=personal sourcetype=cellartracker:bottle vintage_year=* drink_by_year=* bottle_status=\"cellared\"", "| eval years_past=2026-drink_by_year", "| where years_past>0", "| sort - years_past", "| table wine_name region vintage_year drink_by_year years_past"),
              "Lists cellared bottles whose recommended drink-by year has passed.",
              "Overholding past peak risks cork failure and wasted investment on wines past their best window.",
              "Include `drink_by_year` on CellarTracker exports and review overdue bottles each quarter.",
              "Table of past-window bottles sorted by years overdue.", "wines in your cellar that probably should have been opened already."),
            S("Spirit Fill Level Depletion Rate", "low", "intermediate", ["Analytics", "Inventory"],
              ("index=personal sourcetype=spirit:bottle spirit_type=* fill_level_pct=*", "| sort 0 _time", "| streamstats current=f last(fill_level_pct) as prev_fill by bottle_id", "| eval depletion_pct=round(prev_fill-fill_level_pct,1)", "| where depletion_pct>5", "| stats avg(depletion_pct) as avg_depletion, count as pours by spirit_type bottle_id", "| sort - avg_depletion"),
              "Tracks how quickly spirits bottle fill levels drop between inventory scans.",
              "Depletion rate shows which bottles get enjoyed versus collect dust, guiding repurchase and gift decisions.",
              "Log `fill_level_pct` on periodic spirit inventory scans and compare pour frequency by bottle.",
              "Bar chart of average depletion percent by spirit type.", "which bottles you are actually drinking down versus letting sit full."),
            S("Tasting Score vs Cellar Value Correlation", "low", "advanced", ["Analytics", "Quality"],
              ("index=personal sourcetype=wine:tasting wine_id=* score=*", "| join type=inner wine_id [search index=personal sourcetype=cellartracker:bottle | rename bottle_value_usd as value_usd | fields wine_id value_usd region]", "| stats avg(score) as avg_score, avg(value_usd) as avg_value by region", "| sort - avg_score"),
              "Compares average tasting scores against average cellar value by wine region.",
              "Expensive regions that score lower on your palate suggest reallocating budget toward producers you prefer.",
              "Share a common `wine_id` between tasting notes and CellarTracker inventory for joined analysis.",
              "Scatter plot of average score versus average value by region.", "whether the expensive regions in your cellar actually taste better to you."),
            S("Vivino Rating Drift on Owned Bottles", "low", "intermediate", ["Analytics", "Data Quality"],
              ("index=personal sourcetype=vivino:wine wine_id=* vivino_rating=*", "| sort wine_id _time", "| streamstats current=f last(vivino_rating) as prior_rating by wine_id", "| eval rating_delta=round(vivino_rating-prior_rating,2)", "| where abs(rating_delta)>=0.5", "| table wine_name vivino_rating prior_rating rating_delta"),
              "Detects Vivino community rating shifts of half a point or more on wines you own.",
              "Community rating drift can signal vintage variation or emerging quality issues before you open a case.",
              "Rescan owned wines periodically and compare `vivino_rating` against prior snapshots by `wine_id`.",
              "Table of wines with rating delta.", "wines in your collection whose Vivino scores moved noticeably since you last checked."),
        ],
    },
    {
        "id": "109",
        "name": "Home Cleaning & Housekeeping",
        "app": "Roborock vacuum session exports, Tidy scheduling logs, cleaning checklists, and runtime telemetry from robot vacuums ingested into Splunk HEC.",
        "ds": "Roborock sessions (`roborock:session`), Tidy schedules (`tidy:schedule`), cleaning checklists (`cleaning:checklist`), and vacuum runtime logs (`vacuum:runtime`).",
        "refs": R(REF_ROBOROCK),
        "sources": [
            {"label": "Roborock Session", "friendly": "Roborock session", "st": "roborock:session", "group_field": "room_name", "group_desc": "room", "value_field": "area_sqm", "value_title": "Area Cleaned", "duration_field": "runtime_minutes", "duration_title": "Runtime", "status_field": "session_status", "sync_hours": 72},
            {"label": "Tidy Schedule", "friendly": "Tidy schedule", "st": "tidy:schedule", "group_field": "task_name", "group_desc": "task", "value_field": "estimated_minutes", "value_title": "Estimated Minutes", "duration_field": "days_overdue", "duration_title": "Days Overdue", "status_field": "task_status", "sync_hours": 168},
            {"label": "Cleaning Checklist", "friendly": "cleaning checklist", "st": "cleaning:checklist", "group_field": "checklist_name", "group_desc": "checklist", "value_field": "items_completed", "value_title": "Items Completed", "duration_field": "checklist_minutes", "duration_title": "Checklist Time", "status_field": "checklist_status", "sync_hours": 168},
            {"label": "Vacuum Runtime Log", "friendly": "vacuum runtime log", "st": "vacuum:runtime", "group_field": "device_name", "group_desc": "device", "value_field": "runtime_minutes", "value_title": "Runtime Minutes", "duration_field": "battery_pct_end", "duration_title": "Battery at End", "status_field": "runtime_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Overdue Deep-Clean Tasks", "medium", "intermediate", ["Operations", "Quality"],
              ("index=personal sourcetype=tidy:schedule days_overdue=* task_status=*", "| where days_overdue>0 AND task_status!=\"done\"", "| sort - days_overdue", "| table task_name days_overdue estimated_minutes task_status"),
              "Lists Tidy scheduled cleaning tasks that are past due and not marked complete.",
              "Overdue deep cleans pile into weekend marathons; a backlog view spreads work across the month.",
              "Export Tidy tasks with `days_overdue` and review the open queue every Sunday planning session.",
              "Table of overdue tasks sorted by days overdue.", "cleaning chores on your schedule that you keep putting off."),
            S("Robot Vacuum Coverage Gap by Room", "low", "intermediate", ["Analytics", "Operations"],
              ("index=personal sourcetype=roborock:session room_name=* area_sqm=*", "| bin _time span=1w", "| stats sum(area_sqm) as weekly_sqm, count as sessions by _time room_name", "| eventstats avg(weekly_sqm) as avg_sqm by room_name", "| eval below_avg=if(weekly_sqm<avg_sqm*0.5,1,0)", "| where below_avg=1", "| table _time room_name weekly_sqm avg_sqm"),
              "Flags weeks where Roborock cleaned less than half the usual area for a given room.",
              "Coverage gaps often mean blocked doors, moved furniture, or a map that needs remapping after layout changes.",
              "Include `area_sqm` and `room_name` on each session and compare weekly totals to room baselines.",
              "Heat map or table of under-cleaned rooms by week.", "rooms your robot vacuum barely touched compared with its usual coverage."),
            S("Checklist Completion Rate Trend", "low", "beginner", ["Analytics", "Operations"],
              ("index=personal sourcetype=cleaning:checklist items_completed=* items_total=*", "| eval completion_pct=round(100*items_completed/nullif(items_total,0),1)", "| timechart span=1w avg(completion_pct) as avg_completion by checklist_name", "| fillnull value=0"),
              "Trends weekly average completion percentage for each household cleaning checklist.",
              "Completion drift shows when routines collapse after travel or busy seasons and need a reset.",
              "Log `items_completed` and `items_total` per checklist run and chart weekly averages.",
              "Multi-series line chart of completion percent by checklist.", "whether you are finishing your cleaning checklists or letting items slide."),
            S("Vacuum Battery Depletion Anomaly", "medium", "intermediate", ["Anomaly", "Reliability"],
              ("index=personal sourcetype=vacuum:runtime device_name=* battery_pct_end=* runtime_minutes=*", "| eventstats avg(battery_pct_end) as avg_battery, stdev(battery_pct_end) as battery_stdev by device_name", "| eval z_score=round((battery_pct_end-avg_battery)/nullif(battery_stdev,0),2)", "| where z_score<=-2", "| table _time device_name runtime_minutes battery_pct_end avg_battery z_score"),
              "Detects vacuum sessions where end-of-run battery fell two standard deviations below the device average.",
              "Sudden battery drops often precede failing cells or brushes binding, causing incomplete cleans.",
              "Capture `battery_pct_end` and `runtime_minutes` on every run and alert on low-battery outliers.",
              "Table of anomalous sessions with battery z-score.", "vacuum runs that ended with unusually low battery compared with normal."),
        ],
    },
    {
        "id": "110",
        "name": "Pharmacy & Prescriptions",
        "app": "GoodRx price lookups, CVS refill confirmations, pharmacy pickup logs, and prescription adherence trackers streamed into Splunk HEC.",
        "ds": "GoodRx prices (`goodrx:price`), CVS refills (`cvs:refill`), pharmacy pickups (`pharmacy:pickup`), and prescription adherence logs (`prescription:adherence`).",
        "refs": R(REF_GOODRX, REF_CVS),
        "sources": [
            {"label": "GoodRx Price Lookup", "friendly": "GoodRx price lookup", "st": "goodrx:price", "group_field": "drug_name", "group_desc": "drug", "value_field": "lowest_price_usd", "value_title": "Lowest Price", "duration_field": "pharmacy_count", "duration_title": "Pharmacies Compared", "status_field": "lookup_status", "sync_hours": 168},
            {"label": "CVS Refill", "friendly": "CVS refill", "st": "cvs:refill", "group_field": "drug_name", "group_desc": "drug", "value_field": "copay_usd", "value_title": "Copay", "duration_field": "days_supply", "duration_title": "Days Supply", "status_field": "refill_status", "sync_hours": 168},
            {"label": "Pharmacy Pickup", "friendly": "pharmacy pickup", "st": "pharmacy:pickup", "group_field": "pharmacy_name", "group_desc": "pharmacy", "value_field": "pickup_wait_minutes", "value_title": "Pickup Wait", "duration_field": "days_since_fill", "duration_title": "Days Since Fill", "status_field": "pickup_status", "sync_hours": 168},
            {"label": "Prescription Adherence Log", "friendly": "prescription adherence log", "st": "prescription:adherence", "group_field": "drug_name", "group_desc": "drug", "value_field": "doses_taken", "value_title": "Doses Taken", "duration_field": "doses_scheduled", "duration_title": "Doses Scheduled", "status_field": "adherence_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Adherence Below Eighty Percent", "high", "intermediate", ["Patient Safety", "Compliance"],
              ("index=personal sourcetype=prescription:adherence doses_taken=* doses_scheduled=* drug_name=*", "| eval adherence_pct=round(100*doses_taken/nullif(doses_scheduled,0),1)", "| where adherence_pct<80", "| stats avg(adherence_pct) as avg_adherence, count as reporting_days by drug_name", "| sort avg_adherence"),
              "Flags medications whose dose adherence fell below eighty percent over the reporting window.",
              "Missed doses on maintenance meds are invisible day to day but show up as flare-ups weeks later.",
              "Log daily `doses_taken` and `doses_scheduled` per drug and review sub-eighty-percent streaks weekly.",
              "Bar chart of adherence percentage by drug.", "medications you are not taking often enough according to your schedule."),
            S("Refill Gap Before Supply Runs Out", "high", "beginner", ["Operations", "Patient Safety"],
              ("index=personal sourcetype=cvs:refill days_supply=* days_since_fill=* refill_status=*", "| eval days_remaining=days_supply-days_since_fill", "| where days_remaining<=3 AND refill_status!=\"filled\"", "| sort days_remaining", "| table drug_name days_remaining days_supply refill_status"),
              "Lists prescriptions with three or fewer days of supply remaining and no completed refill.",
              "Running out of chronic meds triggers gaps that pharmacies cannot always same-day fill on weekends.",
              "Track `days_supply` and `days_since_fill` on each refill event and alert before the three-day window.",
              "Table of drugs sorted by days remaining.", "prescriptions about to run out before your next refill is ready."),
            S("GoodRx Savings vs Copay Paid", "low", "intermediate", ["Cost", "Analytics"],
              ("index=personal sourcetype=goodrx:price drug_name=* lowest_price_usd=*", "| join type=inner drug_name [search index=personal sourcetype=cvs:refill | stats latest(copay_usd) as copay by drug_name]", "| eval savings_usd=round(copay-lowest_price_usd,2)", "| where savings_usd>5", "| sort - savings_usd", "| table drug_name copay lowest_price_usd savings_usd"),
              "Compares CVS copays against GoodRx lowest prices for the same drug names.",
              "Copay-versus-coupon gaps show where cash price beats insurance and saves real money monthly.",
              "Match `drug_name` across GoodRx lookups and CVS refill receipts, then review positive savings monthly.",
              "Table of drugs with potential savings in dollars.", "prescriptions where GoodRx could have been cheaper than your copay."),
            S("Pharmacy Pickup Wait Outlier", "low", "intermediate", ["Anomaly", "Operations"],
              ("index=personal sourcetype=pharmacy:pickup pharmacy_name=* pickup_wait_minutes=*", "| eventstats avg(pickup_wait_minutes) as avg_wait, stdev(pickup_wait_minutes) as wait_stdev by pharmacy_name", "| eval z_score=round((pickup_wait_minutes-avg_wait)/nullif(wait_stdev,0),2)", "| where z_score>=2", "| table _time pharmacy_name pickup_wait_minutes avg_wait z_score"),
              "Detects pharmacy pickups whose wait time exceeded two standard deviations above the store average.",
              "Wait outliers flag understaffed locations or fill backlog worth switching pharmacies for recurring scripts.",
              "Log `pickup_wait_minutes` per visit and review z-score outliers when choosing a default pharmacy.",
              "Table of outlier pickup waits by pharmacy.", "pharmacy visits where you waited much longer than usual to pick up."),
        ],
    },
    {
        "id": "111",
        "name": "Personal GitHub & Side Projects",
        "app": "GitHub repository metadata, commit activity feeds, issue trackers, and release publish logs forwarded to Splunk HEC.",
        "ds": "GitHub repositories (`github:repo`), commits (`github:commit`), issues (`github:issue`), and releases (`github:release`).",
        "refs": R(REF_GITHUB),
        "sources": [
            {"label": "GitHub Repository", "friendly": "GitHub repository", "st": "github:repo", "group_field": "repo_name", "group_desc": "repository", "value_field": "star_count", "value_title": "Star Count", "duration_field": "open_issues", "duration_title": "Open Issues", "status_field": "repo_status", "sync_hours": 168},
            {"label": "GitHub Commit", "friendly": "GitHub commit", "st": "github:commit", "group_field": "repo_name", "group_desc": "repository", "value_field": "lines_changed", "value_title": "Lines Changed", "duration_field": "commit_minutes", "duration_title": "Commit Window", "status_field": "commit_status", "sync_hours": 72},
            {"label": "GitHub Issue", "friendly": "GitHub issue", "st": "github:issue", "group_field": "label", "group_desc": "label", "value_field": "comment_count", "value_title": "Comment Count", "duration_field": "days_open", "duration_title": "Days Open", "status_field": "issue_status", "sync_hours": 72},
            {"label": "GitHub Release", "friendly": "GitHub release", "st": "github:release", "group_field": "repo_name", "group_desc": "repository", "value_field": "download_count", "value_title": "Download Count", "duration_field": "days_since_release", "duration_title": "Days Since Release", "status_field": "release_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Side Project Commit Drought", "medium", "intermediate", ["Operations", "Analytics"],
              ("index=personal sourcetype=github:commit repo_name=*", "| stats max(_time) as last_commit by repo_name", "| eval days_since=round((now()-last_commit)/86400,0)", "| where days_since>14", "| sort - days_since", "| table repo_name days_since"),
              "Flags personal repositories with no commits for more than fourteen days.",
              "Commit droughts are the early signal that a side project stalled before the repo goes fully dormant.",
              "Ingest GitHub commit webhooks per repo and alert when `days_since` exceeds your active-project threshold.",
              "Table of repos ranked by days since last commit.", "side projects you have not touched in two weeks or more."),
            S("Stale Open Issue Backlog", "high", "intermediate", ["Operations", "DevSecOps"],
              ("index=personal sourcetype=github:issue issue_status=\"open\" days_open=*", "| where days_open>30", "| stats count as stale_issues, max(days_open) as oldest_days by repo_name label", "| sort - stale_issues", "| head 20"),
              "Counts open GitHub issues older than thirty days grouped by repository and label.",
              "Stale issues become silent debt that makes repos feel abandoned to future contributors or employers.",
              "Export issues with `days_open` and `label`, then triage the top twenty stale items each sprint.",
              "Bar chart of stale issue count by repo.", "GitHub issues that have been open so long they probably need closing or fixing."),
            S("Release Cadence Gap Alert", "low", "intermediate", ["Reliability", "Operations"],
              ("index=personal sourcetype=github:release repo_name=* tag_name=*", "| sort repo_name - _time", "| streamstats current=f last(_time) as prev_release by repo_name", "| eval gap_days=round((_time-prev_release)/86400,0)", "| where gap_days>90", "| table repo_name tag_name gap_days"),
              "Detects repositories whose latest release is more than ninety days after the previous one.",
              "Release cadence gaps on public side projects signal bitrot for dependents waiting on fixes.",
              "Log each GitHub release with `repo_name` and compare inter-release gaps against your target schedule.",
              "Table of repos with days between releases.", "projects where you have not shipped a release in three months or more."),
            S("Weekly Commit Velocity by Repo", "low", "beginner", ["Analytics", "Performance"],
              ("index=personal sourcetype=github:commit repo_name=* lines_changed=*", "| bin _time span=1w", "| stats count as commits, sum(lines_changed) as lines_changed by _time repo_name", "| sort - _time - commits"),
              "Tracks weekly commit counts and lines changed across personal GitHub repositories.",
              "Velocity by repo shows which side projects get real attention versus repo-create-and-forget experiments.",
              "Forward commit events with `lines_changed` and chart weekly totals during monthly project reviews.",
              "Stacked column chart of commits by repo and week.", "which personal GitHub repos you actually worked on each week."),
        ],
    },
    {
        "id": "112",
        "name": "Neighborhood & Hyperlocal",
        "app": "Nextdoor post exports, Ring Neighbors alerts, neighborhood watch logs, and local emergency alert feeds ingested into Splunk HEC.",
        "ds": "Nextdoor posts (`nextdoor:post`), Ring Neighbors alerts (`ring:neighbor`), neighborhood watch logs (`neighborhood:watch`), and local alerts (`local:alert`).",
        "refs": R(REF_NEXTDOOR, REF_RING),
        "sources": [
            {"label": "Nextdoor Post", "friendly": "Nextdoor post", "st": "nextdoor:post", "group_field": "category", "group_desc": "category", "value_field": "reaction_count", "value_title": "Reaction Count", "duration_field": "comment_count", "duration_title": "Comment Count", "status_field": "post_status", "sync_hours": 48},
            {"label": "Ring Neighbors Alert", "friendly": "Ring Neighbors alert", "st": "ring:neighbor", "group_field": "alert_type", "group_desc": "alert type", "value_field": "distance_m", "value_title": "Distance", "duration_field": "video_seconds", "duration_title": "Video Length", "status_field": "alert_status", "sync_hours": 24},
            {"label": "Neighborhood Watch Log", "friendly": "neighborhood watch log", "st": "neighborhood:watch", "group_field": "patrol_zone", "group_desc": "patrol zone", "value_field": "incidents_reported", "value_title": "Incidents Reported", "duration_field": "patrol_minutes", "duration_title": "Patrol Time", "status_field": "patrol_status", "sync_hours": 168},
            {"label": "Local Alert", "friendly": "local alert", "st": "local:alert", "group_field": "alert_source", "group_desc": "alert source", "value_field": "severity_score", "value_title": "Severity Score", "duration_field": "affected_radius_m", "duration_title": "Affected Radius", "status_field": "alert_status", "sync_hours": 24},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("High-Severity Local Alert Cluster", "high", "intermediate", ["Safety", "Risk"],
              ("index=personal sourcetype=local:alert severity_score=* alert_source=*", "| bin _time span=1d", "| stats count as alerts, max(severity_score) as peak_severity by _time alert_source", "| where alerts>=3 OR peak_severity>=8", "| sort - peak_severity"),
              "Detects days with three or more local alerts or a peak severity score of eight or above.",
              "Alert clusters often precede weather, fire, or civil events worth adjusting commute and home plans for.",
              "Ingest local emergency feeds with `severity_score` and review daily clusters each morning.",
              "Timeline of alert count and peak severity by source.", "days when your neighborhood had an unusual burst of serious local alerts."),
            S("Ring Alert Volume by Type Trend", "medium", "intermediate", ["Analytics", "Physical Security"],
              ("index=personal sourcetype=ring:neighbor alert_type=* distance_m=*", "| timechart span=1w count as alerts, avg(distance_m) as avg_distance by alert_type", "| fillnull value=0"),
              "Trends weekly Ring Neighbors alert counts and average distance by alert type.",
              "Alert-type trends reveal whether package thefts, strangers, or animals dominate your block's noise.",
              "Export Ring Neighbors alerts with `alert_type` and `distance_m` and review weekly type mix.",
              "Multi-series line chart of alerts by type.", "what kinds of Ring Neighbors alerts happen most around your home each week."),
            S("Nextdoor Complaint Category Spike", "low", "intermediate", ["Analytics", "Governance"],
              ("index=personal sourcetype=nextdoor:post category=* reaction_count=*", "| bin _time span=1w", "| stats count as posts, avg(reaction_count) as avg_reactions by _time category", "| eventstats avg(posts) as baseline_posts by category", "| where posts>baseline_posts*1.5", "| sort - posts"),
              "Flags Nextdoor categories whose weekly post volume exceeds one and a half times the category baseline.",
              "Category spikes surface emerging block issues like noise, parking, or contractor scams before they escalate.",
              "Include `category` on each post export and compare weekly counts to trailing baselines.",
              "Bar chart of categories exceeding baseline post volume.", "Nextdoor topics that suddenly got much more chatter than usual."),
            S("Watch Patrol Coverage Gap", "medium", "intermediate", ["Operations", "Physical Security"],
              ("index=personal sourcetype=neighborhood:watch patrol_zone=* patrol_minutes=*", "| bin _time span=1w", "| stats sum(patrol_minutes) as weekly_minutes by _time patrol_zone", "| where weekly_minutes<30", "| sort _time patrol_zone"),
              "Lists patrol zones with fewer than thirty logged neighborhood watch minutes in a week.",
              "Coverage gaps leave blind spots on blocks that rely on volunteer patrol visibility for deterrence.",
              "Log patrol sessions with `patrol_zone` and `patrol_minutes` and review under-covered zones weekly.",
              "Heat map of weekly patrol minutes by zone.", "parts of the neighborhood that did not get enough watch patrol time."),
        ],
    },
    {
        "id": "113",
        "name": "Hot Tub & Spa",
        "app": "Hot Spring session logs, spa chemistry test results, filter maintenance records, and energy consumption telemetry streamed into Splunk HEC.",
        "ds": "Hot Spring sessions (`hotspring:session`), spa chemistry logs (`spa:chemistry`), filter maintenance records (`spa:filter`), and spa energy usage (`spa:energy`).",
        "refs": R(REF_HOTSPRING),
        "sources": [
            {"label": "Hot Spring Session", "friendly": "Hot Spring session", "st": "hotspring:session", "group_field": "spa_name", "group_desc": "spa", "value_field": "water_temp_f", "value_title": "Water Temperature", "duration_field": "session_minutes", "duration_title": "Session Length", "status_field": "session_status", "sync_hours": 72},
            {"label": "Spa Chemistry Test", "friendly": "spa chemistry test", "st": "spa:chemistry", "group_field": "spa_name", "group_desc": "spa", "value_field": "ph_level", "value_title": "pH Level", "duration_field": "chlorine_ppm", "duration_title": "Chlorine PPM", "status_field": "test_status", "sync_hours": 168},
            {"label": "Spa Filter Maintenance", "friendly": "spa filter maintenance", "st": "spa:filter", "group_field": "filter_id", "group_desc": "filter", "value_field": "pressure_psi", "value_title": "Filter Pressure", "duration_field": "days_since_clean", "duration_title": "Days Since Clean", "status_field": "filter_status", "sync_hours": 168},
            {"label": "Spa Energy Usage", "friendly": "spa energy usage", "st": "spa:energy", "group_field": "spa_name", "group_desc": "spa", "value_field": "kwh_used", "value_title": "kWh Used", "duration_field": "heater_runtime_min", "duration_title": "Heater Runtime", "status_field": "energy_status", "sync_hours": 72},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("pH Out of Safe Range Alert", "high", "intermediate", ["Safety", "Quality"],
              ("index=personal sourcetype=spa:chemistry ph_level=* spa_name=*", "| where ph_level<7.2 OR ph_level>7.8", "| sort - _time", "| table spa_name ph_level chlorine_ppm test_status _time"),
              "Lists spa chemistry tests where pH fell outside the safe 7.2 to 7.8 range.",
              "pH drift causes skin irritation and equipment corrosion long before the water looks visibly wrong.",
              "Log `ph_level` on every chemistry test and alert immediately when readings leave the target band.",
              "Table of out-of-range tests sorted by time.", "hot tub water tests where the pH was too high or too low to soak safely."),
            S("Filter Pressure Rise Before Clean", "medium", "intermediate", ["Operations", "Performance"],
              ("index=personal sourcetype=spa:filter filter_id=* pressure_psi=* days_since_clean=*", "| where pressure_psi>=25 OR days_since_clean>30", "| sort - pressure_psi", "| table filter_id pressure_psi days_since_clean filter_status"),
              "Flags spa filters with pressure at or above twenty-five PSI or not cleaned in thirty days.",
              "High filter pressure reduces circulation and makes the heater work harder, raising energy bills.",
              "Track `pressure_psi` and `days_since_clean` on each filter reading and clean when pressure rises.",
              "Gauge of filter pressure with days-since-clean overlay.", "spa filters that are clogged enough they probably need cleaning now."),
            S("Monthly Spa Energy Cost Trend", "low", "intermediate", ["Cost", "Analytics"],
              ("index=personal sourcetype=spa:energy kwh_used=* rate_usd_per_kwh=*", "| eval session_cost_usd=round(kwh_used*rate_usd_per_kwh,2)", "| bin _time span=1mon", "| stats sum(kwh_used) as monthly_kwh, sum(session_cost_usd) as monthly_cost by _time spa_name", "| sort - _time"),
              "Totals monthly spa energy consumption and estimated cost from heater telemetry.",
              "Energy trends reveal cover-leak heat loss or scheduler mistakes that inflate the hydro bill quietly.",
              "Include `kwh_used` and local `rate_usd_per_kwh` on energy events and chart monthly totals.",
              "Column chart of monthly kWh and cost by spa.", "how much electricity your hot tub used and cost each month."),
            S("Session Frequency vs Chemistry Test Gap", "medium", "intermediate", ["Operations", "Compliance"],
              ("(index=personal sourcetype=hotspring:session) OR (index=personal sourcetype=spa:chemistry)", "| bin _time span=1w", "| stats count(eval(sourcetype=\"hotspring:session\")) as sessions, count(eval(sourcetype=\"spa:chemistry\")) as tests by _time", "| eval test_gap=sessions-tests", "| where sessions>=3 AND tests=0", "| sort - test_gap"),
              "Finds weeks with three or more spa sessions but zero logged chemistry tests.",
              "Heavy use without testing lets sanitizer drift until the water turns cloudy or irritates skin.",
              "Align weekly session counts with chemistry test events and alert when sessions outrun tests.",
              "Table of weeks with session-test gap.", "weeks you used the hot tub a lot but never logged a water chemistry test."),
        ],
    },
    {
        "id": "114",
        "name": "Eyewear & Vision Care",
        "app": "Contact lens order exports, glasses prescription records, vision exam logs, and lens replacement reminders ingested into Splunk HEC.",
        "ds": "Contact lens orders (`contacts:order`), glasses prescriptions (`glasses:prescription`), vision exams (`vision:exam`), and lens replacement logs (`lens:replacement`).",
        "refs": R(REF_WARBY),
        "sources": [
            {"label": "Contact Lens Order", "friendly": "contact lens order", "st": "contacts:order", "group_field": "lens_brand", "group_desc": "lens brand", "value_field": "boxes_ordered", "value_title": "Boxes Ordered", "duration_field": "supply_days", "duration_title": "Supply Days", "status_field": "order_status", "sync_hours": 720},
            {"label": "Glasses Prescription", "friendly": "glasses prescription", "st": "glasses:prescription", "group_field": "optometrist", "group_desc": "optometrist", "value_field": "sphere_od", "value_title": "Sphere OD", "duration_field": "days_until_expiry", "duration_title": "Days Until Expiry", "status_field": "rx_status", "sync_hours": 720},
            {"label": "Vision Exam", "friendly": "vision exam", "st": "vision:exam", "group_field": "provider_name", "group_desc": "provider", "value_field": "copay_usd", "value_title": "Copay", "duration_field": "exam_minutes", "duration_title": "Exam Time", "status_field": "exam_status", "sync_hours": 720},
            {"label": "Lens Replacement Log", "friendly": "lens replacement log", "st": "lens:replacement", "group_field": "replacement_type", "group_desc": "replacement type", "value_field": "days_worn", "value_title": "Days Worn", "duration_field": "days_overdue", "duration_title": "Days Overdue", "status_field": "replacement_status", "sync_hours": 168},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Contact Supply Running Low", "high", "beginner", ["Operations", "Patient Safety"],
              ("index=personal sourcetype=contacts:order supply_days=* days_since_order=* boxes_on_hand=*", "| eval days_remaining=supply_days-days_since_order", "| where days_remaining<=7 AND boxes_on_hand<=1", "| sort days_remaining", "| table lens_brand days_remaining boxes_on_hand order_status"),
              "Lists contact lens orders with seven or fewer supply days remaining and one or fewer boxes on hand.",
              "Running out of contacts forces expensive emergency orders or wearing lenses past safe replacement dates.",
              "Track `supply_days`, `days_since_order`, and `boxes_on_hand` and alert before the one-week window.",
              "Table of lens brands sorted by days remaining.", "contact lens orders that are about to run out before you reorder."),
            S("Glasses Prescription Expiry Watch", "high", "beginner", ["Compliance", "Risk"],
              ("index=personal sourcetype=glasses:prescription days_until_expiry=* rx_status=*", "| where days_until_expiry<=60 AND days_until_expiry>=0", "| sort days_until_expiry", "| table optometrist days_until_expiry sphere_od rx_status"),
              "Lists glasses prescriptions expiring within the next sixty days.",
              "Expired prescriptions delay new frame orders and can leave you driving with outdated correction.",
              "Include `days_until_expiry` on each prescription export and run weekly during back-to-school windows.",
              "Table of prescriptions sorted by days until expiry.", "eyeglass prescriptions about to expire so you can renew them in time."),
            S("Lens Replacement Overdue Alert", "medium", "intermediate", ["Patient Safety", "Compliance"],
              ("index=personal sourcetype=lens:replacement days_overdue=* replacement_type=*", "| where days_overdue>0", "| sort - days_overdue", "| table replacement_type days_worn days_overdue replacement_status"),
              "Flags contact lens replacements worn past their scheduled change date.",
              "Overworn lenses increase infection risk and discomfort that a simple overdue view prevents.",
              "Log `days_worn` and scheduled replacement dates on each lens change and alert on positive overdue days.",
              "Table of overdue replacements by type.", "contact lenses you have been wearing longer than you should have."),
            S("Vision Exam Interval Compliance", "low", "intermediate", ["Compliance", "Operations"],
              ("index=personal sourcetype=vision:exam patient_id=* exam_date=*", "| stats max(exam_date) as last_exam by patient_id", "| eval days_since=round((now()-strptime(last_exam,\"%Y-%m-%d\"))/86400,0)", "| where days_since>730", "| sort - days_since"),
              "Flags patients whose last vision exam was more than two years ago.",
              "Biennial exams catch prescription drift and eye-health changes that daily lens wear masks.",
              "Emit one `vision:exam` event per visit with ISO `exam_date` and review overdue patients annually.",
              "Table of patients by days since last exam.", "people who have not had an eye exam in more than two years."),
        ],
    },
    {
        "id": "115",
        "name": "Pet Insurance & Vet Care",
        "app": "Trupanion claim exports, veterinary invoice logs, pet insurance premium bills, and vet visit records streamed into Splunk HEC.",
        "ds": "Trupanion claims (`trupanion:claim`), vet invoices (`vet:invoice`), pet insurance premiums (`petinsurance:premium`), and vet visits (`vet:visit`).",
        "refs": R(REF_TRUPANION),
        "sources": [
            {"label": "Trupanion Claim", "friendly": "Trupanion claim", "st": "trupanion:claim", "group_field": "pet_name", "group_desc": "pet", "value_field": "reimbursement_usd", "value_title": "Reimbursement", "duration_field": "days_to_pay", "duration_title": "Days to Pay", "status_field": "claim_status", "sync_hours": 168},
            {"label": "Vet Invoice", "friendly": "vet invoice", "st": "vet:invoice", "group_field": "clinic_name", "group_desc": "clinic", "value_field": "invoice_usd", "value_title": "Invoice Amount", "duration_field": "visit_minutes", "duration_title": "Visit Time", "status_field": "invoice_status", "sync_hours": 168},
            {"label": "Pet Insurance Premium", "friendly": "pet insurance premium", "st": "petinsurance:premium", "group_field": "pet_name", "group_desc": "pet", "value_field": "premium_usd", "value_title": "Premium Amount", "duration_field": "billing_cycle_days", "duration_title": "Billing Cycle", "status_field": "payment_status", "sync_hours": 720},
            {"label": "Vet Visit", "friendly": "vet visit", "st": "vet:visit", "group_field": "visit_type", "group_desc": "visit type", "value_field": "weight_kg", "value_title": "Weight", "duration_field": "days_since_last_visit", "duration_title": "Days Since Last Visit", "status_field": "visit_status", "sync_hours": 720},
        ],
        "extra_sourcetypes": [],
        "specials": [
            S("Claim Reimbursement Lag Alert", "high", "intermediate", ["Operations", "Revenue Assurance"],
              ("index=personal sourcetype=trupanion:claim days_to_pay=* claim_status=*", "| where days_to_pay>14 AND claim_status!=\"paid\"", "| sort - days_to_pay", "| table pet_name reimbursement_usd days_to_pay claim_status"),
              "Lists Trupanion claims unpaid more than fourteen days after submission.",
              "Reimbursement lag ties up cash flow for vet bills you expected insurance to cover quickly.",
              "Track `days_to_pay` from submission to deposit and follow up on claims past your normal window.",
              "Table of claims sorted by days to pay.", "pet insurance claims that have taken more than two weeks to pay out."),
            S("Annual Vet Spend vs Premium Paid", "medium", "intermediate", ["Cost", "Analytics"],
              ("(index=personal sourcetype=vet:invoice invoice_usd=*) OR (index=personal sourcetype=petinsurance:premium premium_usd=*)", "| bin _time span=1y", "| stats sum(invoice_usd) as vet_spend, sum(premium_usd) as premiums by _time pet_name", "| eval net_cost=round(vet_spend-premiums,2), value_ratio=round(vet_spend/nullif(premiums,0),2)", "| sort - value_ratio"),
              "Compares annual veterinary invoice totals against pet insurance premiums paid for each pet.",
              "Premium-versus-spend ratio shows whether coverage is paying for itself or mostly funding peace of mind.",
              "Align yearly vet invoices and premium payments by `pet_name` and review before renewal.",
              "Bar chart of vet spend, premiums, and net cost by pet.", "whether your pet insurance premiums are worth it compared with what you spent at the vet."),
            S("Wellness Visit Overdue by Pet", "medium", "intermediate", ["Patient Safety", "Operations"],
              ("index=personal sourcetype=vet:visit pet_name=* visit_type=\"wellness\" visit_date=*", "| stats max(visit_date) as last_wellness by pet_name", "| eval days_since=round((now()-strptime(last_wellness,\"%Y-%m-%d\"))/86400,0)", "| where days_since>365", "| sort - days_since", "| table pet_name days_since last_wellness"),
              "Flags pets whose last wellness visit was more than twelve months ago.",
              "Annual wellness visits catch chronic conditions early when treatment is cheaper and less stressful.",
              "Log wellness visits with ISO `visit_date` and `pet_name`, then alert when the interval exceeds one year.",
              "Table of pets by days since last wellness visit.", "pets that are overdue for their yearly checkup at the vet."),
            S("Invoice vs Claim Filing Gap", "high", "advanced", ["Compliance", "Revenue Assurance"],
              ("index=personal sourcetype=vet:invoice invoice_id=* invoice_usd=* claim_filed=*", "| where invoice_usd>=250 AND claim_filed=0", "| sort - invoice_usd", "| table pet_name clinic_name invoice_usd invoice_date claim_filed"),
              "Surfaces vet invoices of two hundred fifty dollars or more where no insurance claim was filed.",
              "Unfiled claims on large bills leave reimbursement money on the table after you already paid the premium.",
              "Include `claim_filed` flag on invoice exports and review unclaimed invoices over your deductible weekly.",
              "Table of large invoices without claims.", "big vet bills where you never submitted a pet insurance claim."),
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
