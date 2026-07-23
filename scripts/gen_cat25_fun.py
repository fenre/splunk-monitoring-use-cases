#!/usr/bin/env python3
"""Authoring generator for cat-25 — Personal & Hobbyist Monitoring (the fun category).

Produces genuinely runnable, plain-language use cases across 13 subcategories
covering fitness, health/wearables, connected cars, smart home, energy/solar,
media/gaming, home lab, home network, weather/garden, pets, personal finance,
and digital life.  Every UC ships all 13 required fields, valid SPL (no join /
makeresults / random / search-after-stats / earliest=0), and jargon-free
grandmaExplanation text.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict

ROOT = "/workspace/content/cat-25-personal-hobbyist-monitoring"
HEC = {
    "title": "Splunk HTTP Event Collector",
    "url": "https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector",
}

_counts: dict[str, int] = defaultdict(int)
_titles: set[str] = set()


def R(*pairs):
    return [{"title": t, "url": u} for t, u in pairs] + [HEC]


def U(sub, title, crit, diff, mtypes, spl, desc, val, impl, viz, grandma, refs, app, ds,
      pillar="Platform"):
    """Write one UC sidecar, auto-numbering within the subcategory."""
    assert title not in _titles, f"duplicate title: {title}"
    assert desc.strip() != val.strip(), f"desc==value for {title}"
    _titles.add(title)
    _counts[sub] += 1
    uc_id = f"25.{sub}.{_counts[sub]}"
    doc = {
        "$schema": "../../schemas/uc.schema.json",
        "id": uc_id,
        "title": title,
        "criticality": crit,
        "difficulty": diff,
        "monitoringType": mtypes,
        "splunkPillar": pillar,
        "dataSources": ds,
        "app": app,
        "spl": spl,
        "description": desc,
        "value": val,
        "implementation": impl,
        "visualization": viz,
        "cimModels": [],
        "references": refs,
        "grandmaExplanation": grandma,
    }
    with open(os.path.join(ROOT, f"UC-{uc_id}.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ===========================================================================
# 25.1  Fitness & Activity Tracking
# ===========================================================================
F_APP = ("Strava / Garmin Connect / Fitbit / Peloton / Zwift APIs and webhooks via "
         "Splunk HEC scripted inputs; GPX/FIT/CSV activity exports ingested as file inputs.")
F_DS = ("Strava API activities (`strava:activity`), Garmin Connect (`garmin:activity`), "
        "Fitbit Web API (`fitbit:activity`), Peloton workout history (`peloton:workout`).")
STRAVA = ("Strava — API reference", "https://developers.strava.com/docs/reference/")
GARMIN = ("Garmin — Connect Developer Program", "https://developer.garmin.com/gc-developer-program/overview/")
FITBIT = ("Fitbit — Web API reference", "https://dev.fitbit.com/build/reference/web-api/")

U("1", "Strava Weekly Distance vs Goal", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=strava:activity type=Run\n"
  "| bin _time span=1w\n"
  "| stats sum(distance_km) as km, sum(moving_time_s) as secs by _time\n"
  "| eval goal_km=40, pct_of_goal=round(100*km/goal_km,1)\n"
  "| eval status=if(km>=goal_km,\"goal met\",\"behind\")\n"
  "| sort - _time",
  "Sums your Strava running distance per calendar week and compares it to a personal weekly goal so you can see, at a glance, whether you are on track.",
  "Turns a vague sense of 'am I running enough?' into a concrete weekly number against a target, which is far more motivating than staring at individual activities.",
  "Pull activities from the Strava API into `index=personal` on a schedule (or via Strava webhooks); adjust `goal_km` to your target and alert yourself on a Sunday if you are behind.",
  "Column chart of weekly kilometres with a goal reference line and percent-of-goal label.",
  "It adds up how far you ran each week and tells you if you have hit your target, so you know whether to squeeze in one more run.",
  R(STRAVA), F_APP, F_DS)

U("1", "Running Pace Improvement Trend", "low", "intermediate", ["Analytics", "Anomaly"],
  "index=personal sourcetype=strava:activity type=Run distance_km>3\n"
  "| eval pace_min_km=round((moving_time_s/60)/distance_km,2)\n"
  "| timechart span=1w avg(pace_min_km) as avg_pace\n"
  "| eventstats avg(avg_pace) as season_avg\n"
  "| eval faster_than_season=if(avg_pace<season_avg,1,0)",
  "Calculates your average minutes-per-kilometre pace each week and trends it so you can see whether your training is actually making you faster.",
  "Weekly pace trending separates real fitness progress from a single good or bad run, showing whether a training block is paying off before a race.",
  "Ingest Strava runs with distance and moving time; schedule weekly and review the pace line against your season average before planning the next block.",
  "Line chart of weekly average pace (lower is better) with a season-average band.",
  "It works out how fast you have been running each week and shows whether you are getting quicker over time.",
  R(STRAVA), F_APP, F_DS)

U("1", "Missed Workout Streak Alert", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=strava:activity\n"
  "| stats max(_time) as last_activity\n"
  "| eval days_since=round((now()-last_activity)/86400,1)\n"
  "| where days_since>3\n"
  "| eval nudge=\"time to get moving\"",
  "Checks how many days have passed since your last recorded activity and nudges you when the gap grows beyond your rest tolerance.",
  "A gentle streak-protection alert catches motivation slumps early, when one skipped session is about to become a skipped week.",
  "Ingest any activity source into `index=personal`; schedule daily and send yourself a push or email when `days_since` exceeds your threshold.",
  "Single-value panel of days since last activity with a red threshold.",
  "It notices when you have not exercised for a few days and gives you a friendly reminder to get back to it.",
  R(STRAVA), F_APP, F_DS)

U("1", "Heart-Rate Zone Distribution per Workout", "low", "intermediate", ["Analytics", "Performance"],
  "index=personal sourcetype=garmin:activity\n"
  "| eval zone=case(avg_hr<114,\"Z1 easy\",avg_hr<133,\"Z2 aerobic\",avg_hr<152,\"Z3 tempo\",avg_hr<171,\"Z4 threshold\",1=1,\"Z5 max\")\n"
  "| stats sum(moving_time_s) as secs by zone\n"
  "| eval minutes=round(secs/60)\n"
  "| sort zone",
  "Buckets your Garmin workout time into heart-rate training zones so you can see whether you are spending enough time easy and not living in the grey zone.",
  "Most amateur athletes train too hard on easy days; a zone-distribution view makes polarised training visible and keeps effort honest.",
  "Ingest Garmin activities with average heart rate; adjust the zone breakpoints to your own maximum heart rate and review the split weekly.",
  "Bar chart of minutes per heart-rate zone.",
  "It shows how much of your exercise time was easy versus hard, so you can avoid always pushing too much.",
  R(GARMIN), F_APP, F_DS)

U("1", "Personal Records Detection", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=strava:activity type=Run\n"
  "| eval pace_min_km=(moving_time_s/60)/distance_km\n"
  "| streamstats min(pace_min_km) as best_pace_so_far\n"
  "| eval is_pr=if(pace_min_km<=best_pace_so_far,1,0)\n"
  "| where is_pr=1\n"
  "| table _time distance_km pace_min_km",
  "Scans your run history in time order and flags each activity that set a new best pace, giving you an automatic personal-records log.",
  "Celebrating personal records is a proven motivator; detecting them automatically means you never miss a milestone buried in the activity feed.",
  "Ingest Strava runs; schedule after each sync and notify yourself when a new best is detected. Split by distance band for distance-specific records.",
  "Table of record-setting activities with a marker on the pace timeline.",
  "It spots when you have just run your fastest ever and lets you celebrate the new record.",
  R(STRAVA), F_APP, F_DS)

U("1", "Fitbit Daily Step Goal Adherence", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=fitbit:activity\n"
  "| bin _time span=1d\n"
  "| stats sum(steps) as steps by _time\n"
  "| eval goal=10000, met_goal=if(steps>=goal,1,0)\n"
  "| timechart span=1w sum(met_goal) as days_goal_met",
  "Counts how many days each week you hit your daily step goal, turning a single day's number into a habit-strength signal.",
  "Consistency beats intensity for everyday health; counting goal-met days rewards the habit rather than a one-off big walk.",
  "Ingest Fitbit daily activity summaries; schedule weekly and review the count of goal-met days as your habit score.",
  "Column chart of goal-met days per week out of seven.",
  "It counts how many days you reached your step goal, so you can see if walking is becoming a steady habit.",
  R(FITBIT), F_APP, F_DS)

U("1", "Peloton Output Trend by Class Type", "low", "intermediate", ["Analytics", "Performance"],
  "index=personal sourcetype=peloton:workout\n"
  "| timechart span=1w avg(total_output_kj) as avg_output by discipline\n"
  "| fillnull value=0",
  "Trends your average Peloton output in kilojoules per week, split by class discipline, so you can see which kinds of workouts you are improving on.",
  "Output is Peloton's honest effort metric; trending it by discipline reveals whether your cycling power or strength volume is genuinely climbing.",
  "Ingest Peloton workout history into `index=personal`; schedule weekly and compare disciplines to guide your next block.",
  "Multi-series line chart of weekly average output by discipline.",
  "It tracks how hard your Peloton workouts have been each week and which types you are getting stronger at.",
  R(("Peloton — Member support", "https://support.onepeloton.com/")), F_APP, F_DS)

U("1", "Training Load Ramp-Rate (Injury Risk) Warning", "medium", "advanced", ["Anomaly", "Risk"],
  "index=personal sourcetype=strava:activity\n"
  "| bin _time span=1w\n"
  "| stats sum(distance_km) as weekly_km by _time\n"
  "| streamstats window=4 current=f avg(weekly_km) as chronic_load\n"
  "| eval acute_chronic_ratio=round(weekly_km/chronic_load,2)\n"
  "| where acute_chronic_ratio>1.5\n"
  "| sort - _time",
  "Compares this week's training volume to your rolling four-week average and flags weeks where you ramped up too fast, a well-known injury-risk signal.",
  "The acute-to-chronic workload ratio is a research-backed injury predictor; catching a spike lets you back off before a niggle becomes a lay-off.",
  "Ingest weekly distance; schedule weekly and alert when the ratio exceeds 1.5 so you can plan a recovery week.",
  "Line chart of the acute-to-chronic ratio with a danger threshold at 1.5.",
  "It warns you when you suddenly do a lot more exercise than usual, which is when injuries often happen.",
  R(STRAVA), F_APP, F_DS)

U("1", "Cycling Elevation and Distance Rollup", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=strava:activity type=Ride\n"
  "| bin _time span=1mon\n"
  "| stats sum(distance_km) as km, sum(elevation_m) as climb_m, count as rides by _time\n"
  "| sort - _time",
  "Rolls up your monthly cycling distance, total climbing, and ride count so you can track your season at a glance.",
  "A monthly rollup is the perfect scrapbook metric — it captures the shape of your riding season without you logging anything by hand.",
  "Ingest Strava rides; schedule monthly and keep the rollup as a personal season log.",
  "Table and column chart of monthly distance and elevation.",
  "It adds up how far and how much you climbed on your bike each month, like a scrapbook of your cycling year.",
  R(STRAVA), F_APP, F_DS)

U("1", "Activity Upload Gap Detection", "low", "intermediate", ["Availability", "Data Quality"],
  "index=personal sourcetype=garmin:activity\n"
  "| stats max(_time) as last_sync by device\n"
  "| eval hours_since=round((now()-last_sync)/3600,1)\n"
  "| where hours_since>36\n"
  "| sort - hours_since",
  "Detects when a fitness device has stopped syncing activities, which usually means a broken connection, a dead battery, or a forgotten watch.",
  "A silent sync gap means lost data and a broken streak; catching it early lets you re-pair the device before a big activity goes unrecorded.",
  "Ingest per-device activity events; schedule twice daily and alert when a device has not synced within its expected window.",
  "Table of devices by hours since last sync.",
  "It tells you when your watch or fitness gadget has stopped sending data, so you do not lose a workout.",
  R(GARMIN), F_APP, F_DS)

U("1", "Weekly Active Minutes vs Recommendation", "low", "beginner", ["Analytics", "Compliance"],
  "index=personal sourcetype=fitbit:activity\n"
  "| bin _time span=1w\n"
  "| stats sum(active_minutes) as active_min by _time\n"
  "| eval recommended=150, pct=round(100*active_min/recommended)\n"
  "| sort - _time",
  "Sums your weekly moderate-to-vigorous active minutes and compares them to the widely recommended 150-minute guideline.",
  "Framing your week against the official activity guideline turns exercise into a simple pass/fail health target anyone can understand.",
  "Ingest Fitbit or Apple active-minutes data; schedule weekly and alert when you fall short of the guideline.",
  "Gauge or column chart of active minutes against the 150-minute line.",
  "It checks whether you got the amount of exercise health experts recommend each week.",
  R(FITBIT), F_APP, F_DS)

U("1", "Zwift Virtual Ride FTP Progress", "low", "intermediate", ["Analytics", "Performance"],
  "index=personal sourcetype=zwift:activity\n"
  "| timechart span=1mon max(estimated_ftp_w) as ftp\n"
  "| eventstats avg(ftp) as avg_ftp",
  "Trends the highest estimated functional threshold power from your Zwift rides each month so you can watch your cycling fitness ceiling rise.",
  "Functional threshold power is the single most useful cycling fitness number; tracking its monthly best shows long-term progress that day-to-day rides hide.",
  "Ingest Zwift ride summaries; schedule monthly and review the power trend before setting new training targets.",
  "Line chart of monthly best estimated power.",
  "It follows how your cycling power is improving month by month on your indoor trainer.",
  R(("Zwift — Support", "https://support.zwift.com/")), F_APP, F_DS)


# ===========================================================================
# 25.2  Health, Sleep & Wearables
# ===========================================================================
H_APP = ("Apple Health / Apple Watch exports (Health Auto Export or Shortcuts) via HEC; "
         "Oura, Whoop, Withings, and Dexcom APIs via scripted REST inputs.")
H_DS = ("Apple Health metrics (`apple:health`), Oura Ring readiness/sleep (`oura:daily`), "
        "Whoop recovery/strain (`whoop:cycle`), Withings measurements (`withings:measure`).")
OURA = ("Oura — API v2 documentation", "https://cloud.ouraring.com/v2/docs")
WHOOP = ("WHOOP — Developer platform", "https://developer.whoop.com/docs/")
WITHINGS = ("Withings — Developer API", "https://developer.withings.com/api-reference/")
APPLEHK = ("Apple — HealthKit documentation", "https://developer.apple.com/documentation/healthkit")

U("2", "Resting Heart Rate Anomaly Detection", "medium", "advanced", ["Anomaly", "Safety"],
  "index=personal sourcetype=apple:health metric=resting_heart_rate\n"
  "| timechart span=1d avg(value) as rhr\n"
  "| eventstats avg(rhr) as base, stdev(rhr) as sd\n"
  "| eval elevated=if(rhr>base+2*sd,1,0)\n"
  "| where elevated=1",
  "Baselines your daily resting heart rate and flags days when it jumps well above normal, an early sign of illness, poor recovery, or overtraining.",
  "A sudden resting-heart-rate rise often precedes a cold or burnout by a day or two; catching it lets you rest before you get sick.",
  "Export Apple Watch resting heart rate into `index=personal`; schedule daily and alert when today's value exceeds your personal baseline.",
  "Line chart of daily resting heart rate with an anomaly band.",
  "It learns your normal resting heartbeat and warns you on days it is unusually high, which can mean you are getting run down.",
  R(APPLEHK), H_APP, H_DS)

U("2", "Sleep Duration vs Target Trend", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=oura:daily\n"
  "| eval sleep_h=round(total_sleep_s/3600,1)\n"
  "| timechart span=1d avg(sleep_h) as hours\n"
  "| eval target=7.5, deficit=round(target-hours,1)",
  "Trends how many hours you actually sleep each night against a personal target so chronic sleep debt becomes visible instead of vague.",
  "Sleep debt accumulates invisibly; a daily target comparison turns 'I feel tired' into a number you can act on.",
  "Ingest Oura or Apple sleep data; schedule daily and review the running deficit against your target.",
  "Line chart of nightly sleep hours with a target line.",
  "It shows how much you slept each night compared to your goal, so you can see if you are short on rest.",
  R(OURA), H_APP, H_DS)

U("2", "Oura Readiness Score Drop Alert", "medium", "intermediate", ["Anomaly", "Safety"],
  "index=personal sourcetype=oura:daily\n"
  "| timechart span=1d avg(readiness_score) as readiness\n"
  "| streamstats window=7 current=f avg(readiness) as week_avg\n"
  "| eval drop=round(week_avg-readiness,1)\n"
  "| where drop>10",
  "Compares today's Oura readiness score to your recent seven-day average and flags a sharp drop, signalling your body needs an easier day.",
  "A readiness crash is a data-driven reason to skip a hard workout; acting on it prevents the deeper fatigue that leads to illness or injury.",
  "Ingest Oura daily readiness; schedule each morning and send yourself a 'take it easy' nudge when readiness drops sharply.",
  "Line chart of readiness with drop markers.",
  "It notices when your body's recovery score falls a lot overnight and suggests taking it easy that day.",
  R(OURA), H_APP, H_DS)

U("2", "Heart-Rate Variability Weekly Trend", "low", "advanced", ["Analytics", "Anomaly"],
  "index=personal sourcetype=whoop:cycle\n"
  "| timechart span=1w avg(hrv_ms) as hrv\n"
  "| eventstats avg(hrv) as base\n"
  "| eval below_baseline=if(hrv<base,1,0)",
  "Trends your weekly average heart-rate variability, a sensitive marker of stress and recovery, so you can see how life is affecting your body over time.",
  "Heart-rate variability responds to sleep, alcohol, stress, and training; a weekly trend connects lifestyle choices to how recovered you actually are.",
  "Ingest Whoop or Apple heart-rate-variability data; schedule weekly and correlate dips with travel, alcohol, or heavy training.",
  "Line chart of weekly heart-rate variability with a baseline band.",
  "It follows a body signal that shows how well you are recovering, so you can see what habits help or hurt you.",
  R(WHOOP), H_APP, H_DS)

U("2", "Weight and Body Composition Trend", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=withings:measure\n"
  "| timechart span=1w avg(weight_kg) as weight, avg(fat_pct) as body_fat\n"
  "| eventstats avg(weight) as avg_weight",
  "Smooths your smart-scale readings into a weekly trend so day-to-day water-weight noise stops hiding the real direction of travel.",
  "Daily weigh-ins are noisy and demoralising; a weekly average shows the genuine trend and keeps you focused on progress, not fluctuations.",
  "Ingest Withings or other smart-scale data; schedule weekly and review the smoothed weight line rather than single readings.",
  "Line chart of weekly average weight and body-fat percentage.",
  "It averages your scale readings each week so the normal ups and downs do not distract you from the real trend.",
  R(WITHINGS), H_APP, H_DS)

U("2", "Blood Pressure Out-of-Range Log", "medium", "beginner", ["Safety", "Compliance"],
  "index=personal sourcetype=withings:measure metric=blood_pressure\n"
  "| eval flag=case(systolic>=140 OR diastolic>=90,\"high\",systolic<90 OR diastolic<60,\"low\",1=1,\"normal\")\n"
  "| where flag!=\"normal\"\n"
  "| table _time systolic diastolic flag\n"
  "| sort - _time",
  "Keeps a running log of every blood-pressure reading that falls outside the normal range, ready to show a doctor.",
  "An automatically curated out-of-range log is far more useful at a check-up than a memory of 'it was high sometimes'.",
  "Ingest home blood-pressure readings; schedule daily and export the out-of-range log ahead of medical appointments.",
  "Table of out-of-range readings over time with high/low flags.",
  "It keeps a tidy list of the times your blood pressure was too high or low, which is handy to show your doctor.",
  R(WITHINGS), H_APP, H_DS)

U("2", "Continuous Glucose Time-in-Range", "medium", "advanced", ["Analytics", "Safety"],
  "index=personal sourcetype=dexcom:egv\n"
  "| eval band=case(glucose_mgdl<70,\"low\",glucose_mgdl<=180,\"in range\",1=1,\"high\")\n"
  "| stats count by band\n"
  "| eventstats sum(count) as total\n"
  "| eval pct=round(100*count/total,1)",
  "Calculates what fraction of the day your glucose stays within the healthy target band, the headline metric clinicians use for glucose management.",
  "Time-in-range is a more meaningful goal than a single reading; quantifying it helps anyone managing glucose see progress clearly.",
  "Ingest continuous-glucose-monitor values into `index=personal`; schedule daily and track the in-range percentage over time.",
  "Pie or bar chart of time spent low, in range, and high.",
  "It works out how much of the day your blood sugar stayed in the healthy zone.",
  R(("Dexcom — Developer portal", "https://developer.dexcom.com/")), H_APP, H_DS)

U("2", "Daily Hydration and Nutrition Rollup", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=apple:health (metric=water OR metric=dietary_energy)\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(metric=\"water\",value,0))) as water_ml, sum(eval(if(metric=\"dietary_energy\",value,0))) as kcal by _time\n"
  "| sort - _time",
  "Rolls up your logged water intake and calories per day so you can spot the days you forgot to drink or drastically under-ate.",
  "Seeing hydration and calories side by side each day catches the patterns that single meal logs miss, like chronic under-eating on busy days.",
  "Ingest Apple Health nutrition and water metrics; schedule daily and review the rollup weekly.",
  "Dual-axis chart of daily water and calories.",
  "It adds up how much you drank and ate each day so you can spot the days you forgot to look after yourself.",
  R(APPLEHK), H_APP, H_DS)

U("2", "Mindfulness and Stress-Minute Tracking", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=apple:health metric=mindful_minutes\n"
  "| timechart span=1w sum(value) as mindful_min\n"
  "| eval goal=70, met=if(mindful_min>=goal,1,0)",
  "Sums the minutes you spend on logged mindfulness or breathing sessions each week and compares them to a personal goal.",
  "Mental-health habits are easy to drop; a simple weekly minutes target keeps mindfulness as visible and trackable as steps.",
  "Ingest Apple Health mindful-minutes; schedule weekly and nudge yourself when you fall short of the goal.",
  "Column chart of weekly mindful minutes against a goal line.",
  "It tracks how much calm-down or breathing time you got each week, so looking after your mind stays a habit.",
  R(APPLEHK), H_APP, H_DS)

U("2", "Wearable Battery and Sync Health", "low", "intermediate", ["Availability", "Data Quality"],
  "index=personal sourcetype=oura:daily\n"
  "| stats max(_time) as last_seen, latest(battery_pct) as battery by device\n"
  "| eval hours_since=round((now()-last_seen)/3600,1)\n"
  "| where hours_since>30 OR battery<15\n"
  "| sort - hours_since",
  "Watches your health wearables for a low battery or a stalled sync so you do not wake up to a night of missing sleep and recovery data.",
  "Health trends only work with continuous data; catching a dead ring or a sync stall protects the very metrics you rely on.",
  "Ingest device battery and last-sync fields; schedule twice daily and alert on low battery or a sync gap before bedtime.",
  "Table of devices by battery level and hours since last sync.",
  "It reminds you to charge your health ring or watch before the battery dies and you miss a night of data.",
  R(OURA), H_APP, H_DS)

U("2", "Sleep Consistency (Bed and Wake Time) Score", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=oura:daily\n"
  "| eval bedtime_min=strftime(bedtime_start,\"%H\")*60+strftime(bedtime_start,\"%M\")\n"
  "| timechart span=1w stdev(bedtime_min) as bedtime_variability_min",
  "Measures how much your bedtime drifts from night to night, because a regular sleep schedule matters as much as total sleep for how you feel.",
  "Sleep consistency is an underrated lever; quantifying bedtime variability shows whether an irregular schedule is quietly wrecking your rest.",
  "Ingest Oura bedtime data; schedule weekly and aim to shrink the variability number over time.",
  "Line chart of weekly bedtime variability in minutes (lower is better).",
  "It shows how much your bedtime jumps around, because going to bed at similar times helps you feel better.",
  R(OURA), H_APP, H_DS)


# ===========================================================================
# 25.3  Connected Cars & EVs
# ===========================================================================
C_APP = ("Tesla Fleet API / TeslaMate, Teslafi, and generic OBD-II / Smartcar / "
         "manufacturer APIs via HEC scripted inputs and MQTT bridges.")
C_DS = ("Tesla vehicle/charge state (`tesla:vehicle`, `tesla:charge`), TeslaMate MQTT, "
        "OBD-II PIDs (`obd:pid`), Smartcar API (`smartcar:vehicle`), charger sessions (`evcharger:session`).")
TESLA = ("Tesla — Fleet API documentation", "https://developer.tesla.com/docs/fleet-api")
TESLAMATE = ("TeslaMate — Documentation", "https://docs.teslamate.org/")
SMARTCAR = ("Smartcar — API reference", "https://smartcar.com/docs/api-reference/")

U("3", "Tesla Battery Health Degradation Trend", "medium", "advanced", ["Analytics", "Reliability"],
  "index=personal sourcetype=tesla:charge charge_pct>=95\n"
  "| eval range_at_full=rated_range_km/(charge_pct/100)\n"
  "| timechart span=1mon avg(range_at_full) as full_range_km\n"
  "| eventstats first(full_range_km) as new_range\n"
  "| eval degradation_pct=round(100*(new_range-full_range_km)/new_range,1)",
  "Estimates your Tesla's full-charge range each month from near-full charges and trends how much battery capacity has faded since new.",
  "Battery degradation affects resale value and daily range; a monthly trend gives you an honest number instead of range-anxiety guesswork.",
  "Ingest Tesla charge state (via TeslaMate or the Fleet API) into `index=personal`; schedule monthly and watch the degradation percentage.",
  "Line chart of estimated full-charge range per month with a degradation percentage.",
  "It works out how much your electric car's battery has worn down over time, so you know the true range you can count on.",
  R(TESLA, TESLAMATE), C_APP, C_DS, pillar="Observability")

U("3", "EV Charging Cost by Session", "low", "intermediate", ["Cost", "Analytics"],
  "index=personal sourcetype=tesla:charge\n"
  "| eval kwh=energy_added_kwh, cost=round(kwh*tariff_per_kwh,2)\n"
  "| stats sum(kwh) as total_kwh, sum(cost) as total_cost, count as sessions by location\n"
  "| eval avg_cost_per_session=round(total_cost/sessions,2)\n"
  "| sort - total_cost",
  "Adds up the energy and money spent charging at each location so you can see whether home, work, or public charging is costing you the most.",
  "Charging cost is invisible when it is spread across a power bill; attributing it per location reveals where to shift charging to save real money.",
  "Ingest charge sessions with energy added and your tariff; schedule weekly and compare cost per location.",
  "Table and bar chart of charging cost by location.",
  "It adds up what it costs to charge your car in different places, so you can charge where it is cheapest.",
  R(TESLA), C_APP, C_DS)

U("3", "Phantom Battery Drain While Parked", "low", "advanced", ["Anomaly", "Cost"],
  "index=personal sourcetype=tesla:vehicle shift_state=\"P\"\n"
  "| sort 0 _time\n"
  "| delta battery_pct as drop p=1\n"
  "| eval drain=abs(drop)\n"
  "| bin _time span=1d\n"
  "| stats sum(drain) as pct_lost_parked by _time\n"
  "| where pct_lost_parked>3",
  "Measures how much charge your car loses overnight while parked and flags days with unusually high standby drain.",
  "Excessive phantom drain points at settings like sentry mode or cabin overheat protection quietly eating your range and money.",
  "Ingest parked vehicle state; schedule daily and investigate settings when overnight drain exceeds your tolerance.",
  "Column chart of daily charge lost while parked.",
  "It shows how much battery your car quietly loses while parked, so you can turn off settings that waste it.",
  R(TESLAMATE), C_APP, C_DS, pillar="Observability")

U("3", "Tire Pressure Low Warning", "medium", "beginner", ["Safety", "Fault"],
  "index=personal sourcetype=tesla:vehicle\n"
  "| eval low=if(tpms_fl<2.5 OR tpms_fr<2.5 OR tpms_rl<2.5 OR tpms_rr<2.5,1,0)\n"
  "| where low=1\n"
  "| table _time tpms_fl tpms_fr tpms_rl tpms_rr\n"
  "| sort - _time",
  "Checks the tyre-pressure readings reported by the car and alerts when any wheel drops below a safe threshold.",
  "Low tyre pressure hurts range, wears tyres unevenly, and is a safety risk; an early alert lets you top up before a slow leak becomes a flat.",
  "Ingest per-wheel pressure fields; schedule hourly and alert when any wheel falls below your safe pressure.",
  "Table of low-pressure events with per-wheel values.",
  "It watches your car tyres and tells you when one is getting soft, before it becomes a flat.",
  R(SMARTCAR), C_APP, C_DS, pillar="Observability")

U("3", "Monthly Driving Distance and Efficiency", "low", "beginner", ["Analytics", "Cost"],
  "index=personal sourcetype=tesla:vehicle\n"
  "| bin _time span=1mon\n"
  "| stats max(odometer_km) as end_odo, min(odometer_km) as start_odo, avg(wh_per_km) as efficiency by _time\n"
  "| eval km_driven=end_odo-start_odo\n"
  "| sort - _time",
  "Summarises how far you drove each month and your average energy use per kilometre so you can track both mileage and efficiency.",
  "Monthly mileage and efficiency together explain your charging bill and reveal seasonal swings, like winter range loss.",
  "Ingest odometer and consumption fields; schedule monthly and review distance and efficiency together.",
  "Dual-axis chart of monthly distance and efficiency.",
  "It sums up how far you drove each month and how efficiently, so you understand your charging costs.",
  R(TESLAMATE), C_APP, C_DS)

U("3", "OBD-II Check-Engine and Fault-Code Capture", "medium", "advanced", ["Fault", "Availability"],
  "index=personal sourcetype=obd:pid dtc_count>0\n"
  "| stats latest(dtc_codes) as codes, latest(dtc_count) as count, max(_time) as last_seen by vin\n"
  "| eval last=strftime(last_seen,\"%F %T\")\n"
  "| sort - last_seen",
  "Captures diagnostic trouble codes from an OBD-II dongle so a check-engine light comes with the actual fault codes instead of a mystery symbol.",
  "Knowing the fault code before visiting a mechanic saves money and avoids being upsold; logging them also reveals intermittent faults.",
  "Read OBD-II PIDs via a Bluetooth/Wi-Fi dongle bridged to HEC; schedule frequently and alert whenever a new trouble code appears.",
  "Table of vehicles by current trouble codes and last-seen time.",
  "It reads the fault codes behind your car's check-engine light so you know what is actually wrong before the garage.",
  R(("OBD-II — PIDs reference (SAE J1979)", "https://en.wikipedia.org/wiki/OBD-II_PIDs")), C_APP, C_DS,
  pillar="Observability")

U("3", "Charging Session Failure Detection", "medium", "intermediate", ["Availability", "Fault"],
  "index=personal sourcetype=evcharger:session\n"
  "| stats count as sessions, sum(eval(status=\"faulted\" OR status=\"interrupted\")) as failed by charger_id\n"
  "| eval fail_rate=round(100*failed/sessions,1)\n"
  "| where failed>0\n"
  "| sort - fail_rate",
  "Counts charging sessions that faulted or stopped early per charger so you catch a flaky home charger or a bad cable before a morning with an empty battery.",
  "A charge that silently fails overnight ruins your day; tracking failure rate per charger surfaces hardware problems while they are still cheap to fix.",
  "Ingest charger session records; schedule daily and alert when a charger's failure rate climbs.",
  "Table of chargers by failure rate with a trend.",
  "It spots when your car charger keeps stopping early, so you are not left with an empty battery in the morning.",
  R(("Open Charge Point Protocol (OCPP)", "https://openchargealliance.org/protocols/open-charge-point-protocol/")),
  C_APP, C_DS, pillar="Observability")

U("3", "Optimal Charge-Window Adherence", "low", "intermediate", ["Cost", "Analytics"],
  "index=personal sourcetype=tesla:charge\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| eval off_peak=if(hour>=1 AND hour<6,1,0)\n"
  "| stats sum(eval(off_peak*energy_added_kwh)) as offpeak_kwh, sum(energy_added_kwh) as total_kwh\n"
  "| eval pct_offpeak=round(100*offpeak_kwh/total_kwh,1)",
  "Measures what share of your charging happened during cheap off-peak hours so you can see whether your scheduled charging is actually working.",
  "Off-peak charging can halve your fuelling cost; verifying adherence catches a mis-set schedule that is quietly charging at peak rates.",
  "Ingest charge sessions with timestamps; adjust the off-peak window to your tariff and schedule weekly.",
  "Gauge of off-peak charging percentage over time.",
  "It checks that your car charges mostly during the cheap night-time hours, so you are not paying peak prices.",
  R(TESLA), C_APP, C_DS)

U("3", "Cabin Overheat and Climate Event Log", "low", "beginner", ["Analytics", "Safety"],
  "index=personal sourcetype=tesla:vehicle inside_temp_c>45\n"
  "| stats max(inside_temp_c) as peak_temp, count as readings by date_mday\n"
  "| sort - peak_temp",
  "Logs the days your parked car's cabin got dangerously hot, useful if you carry pets, children, or heat-sensitive items.",
  "A hot cabin is a real safety issue; a log of peak temperatures shows whether cabin-overheat protection is doing its job.",
  "Ingest inside-temperature readings; schedule daily and review peak cabin temperatures during summer.",
  "Column chart of daily peak cabin temperature.",
  "It records the days your car got very hot inside while parked, which matters if you carry pets or children.",
  R(TESLAMATE), C_APP, C_DS)

U("3", "Software Update and Version Tracking", "low", "beginner", ["Change", "Inventory"],
  "index=personal sourcetype=tesla:vehicle\n"
  "| stats earliest(car_version) as from_version, latest(car_version) as to_version, count as readings by date_month\n"
  "| where from_version!=to_version\n"
  "| sort - date_month",
  "Tracks when your car's software version changes so you have a dated record of every over-the-air update it received.",
  "A version history helps you correlate a new quirk or feature with the update that introduced it, and confirms updates are actually installing.",
  "Ingest the reported software version; schedule daily and log every version change.",
  "Timeline of software versions with change markers.",
  "It keeps a dated list of when your car got new software, so you can link any new behaviour to an update.",
  R(TESLA), C_APP, C_DS)


# ===========================================================================
# 25.4  Smart Home Platforms & Automation
# ===========================================================================
SH_APP = ("Home Assistant / Homey / SmartThings / Hubitat / openHAB event streams via "
          "MQTT, webhooks, and REST — forwarded to Splunk HEC.")
SH_DS = ("Home Assistant state/logbook events (`homeassistant:event`), Homey flow/insights "
         "(`homey:flow`), SmartThings events (`smartthings:event`), Node-RED flow events (`nodered:event`).")
HASS = ("Home Assistant — Documentation", "https://www.home-assistant.io/docs/")
HOMEY = ("Homey — Developer documentation", "https://apps.developer.homey.app/")
SMARTTHINGS = ("SmartThings — Developer documentation", "https://developer.smartthings.com/docs/getting-started/welcome")

U("4", "Home Assistant Automation Failures", "medium", "intermediate", ["Availability", "Fault"],
  "index=personal sourcetype=homeassistant:event event_type=automation_triggered\n"
  "| stats count as runs, sum(eval(result=\"failed\" OR level=\"ERROR\")) as failures by automation\n"
  "| eval fail_rate=round(100*failures/runs,1)\n"
  "| where failures>0\n"
  "| sort - fail_rate",
  "Counts how often each Home Assistant automation runs and how often it errors, so a broken automation surfaces instead of just silently not happening.",
  "A failed automation is invisible by design — the lights just do not turn on; tracking failure rate makes these silent failures actionable.",
  "Forward Home Assistant logbook/automation events to HEC; schedule hourly and alert when a key automation starts failing.",
  "Table of automations by failure rate with a trend line.",
  "It notices when your home's automatic routines stop working, like lights that should have come on but did not.",
  R(HASS), SH_APP, SH_DS, pillar="Observability")

U("4", "Smart Home Device Offline Detection", "medium", "beginner", ["Availability", "Fault"],
  "index=personal sourcetype=homeassistant:event\n"
  "| stats max(_time) as last_seen by entity_id\n"
  "| eval mins_since=round((now()-last_seen)/60)\n"
  "| where mins_since>60\n"
  "| sort - mins_since",
  "Finds smart-home devices that have stopped reporting to your hub, catching dead batteries, dropped Wi-Fi, and crashed integrations.",
  "An offline sensor breaks every automation that depends on it; a single offline-device view replaces hunting through the app room by room.",
  "Forward device state events to HEC; schedule every 15 minutes and alert when a critical device goes quiet.",
  "Table of entities by minutes since last report.",
  "It tells you which smart-home gadgets have gone quiet, so you can fix the dead batteries or lost connections.",
  R(HASS), SH_APP, SH_DS, pillar="Observability")

U("4", "Automation Trigger Frequency Heatmap", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=homeassistant:event event_type=automation_triggered\n"
  "| eval hour=strftime(_time,\"%H\"), day=strftime(_time,\"%A\")\n"
  "| stats count as triggers by day hour\n"
  "| sort day hour",
  "Maps when your home automations fire across the hours and days of the week, revealing the rhythm of your household.",
  "A trigger heatmap surfaces automations firing at odd hours (a sign of a bad trigger) and helps you understand and tune your setup.",
  "Forward automation events; schedule weekly and render the heatmap to spot unexpected firing patterns.",
  "Heatmap of automation triggers by day and hour.",
  "It draws a picture of when your home's routines happen through the week, which helps spot anything odd.",
  R(HASS), SH_APP, SH_DS)

U("4", "Homey Flow Error Tracking", "medium", "intermediate", ["Availability", "Fault"],
  "index=personal sourcetype=homey:flow\n"
  "| stats count as runs, sum(eval(status=\"error\")) as errors by flow_name\n"
  "| eval error_rate=round(100*errors/runs,1)\n"
  "| where errors>0\n"
  "| sort - error_rate",
  "Tracks how often each Homey flow errors so a misbehaving automation is caught before it disrupts your daily routine.",
  "Homey flows chain many devices; one broken step breaks the whole flow, so per-flow error tracking pinpoints exactly what to fix.",
  "Forward Homey flow results to HEC; schedule hourly and alert on rising flow error rates.",
  "Table of Homey flows by error rate.",
  "It watches your Homey routines and flags the ones that keep failing, so your home keeps behaving as expected.",
  R(HOMEY), SH_APP, SH_DS, pillar="Observability")

U("4", "Presence Detection Accuracy", "low", "advanced", ["Anomaly", "Quality"],
  "index=personal sourcetype=homeassistant:event entity_id=\"person.*\"\n"
  "| transaction entity_id startswith=\"state=home\" endswith=\"state=not_home\" maxspan=1d\n"
  "| stats count as transitions, avg(duration) as avg_home_s by entity_id\n"
  "| eval flaps_flag=if(transitions>20,\"flapping\",\"ok\")",
  "Measures how often your home/away presence state flips, catching the flapping that makes presence-based automations unreliable.",
  "Flapping presence turns the heating and lights on and off all day; detecting it lets you tune the device trackers behind it.",
  "Forward person-entity state changes; schedule daily and investigate entities that flap excessively.",
  "Table of people by presence transitions per day.",
  "It checks whether your home reliably knows when you are in or out, so the lights and heating behave correctly.",
  R(HASS), SH_APP, SH_DS, pillar="Observability")

U("4", "Voice Assistant Command Log", "low", "beginner", ["Analytics", "Audit"],
  "index=personal sourcetype=homeassistant:event event_type=voice_command\n"
  "| stats count as commands by intent\n"
  "| sort - commands\n"
  "| head 20",
  "Ranks the voice commands your household actually uses so you can design better automations around real behaviour.",
  "Knowing your most-used voice intents reveals which routines to streamline and which fancy automations nobody ever triggers.",
  "Forward voice-assistant intents to HEC; schedule weekly and review the top commands.",
  "Bar chart of top voice intents by count.",
  "It lists the voice commands your family uses most, so you can make the popular ones work even better.",
  R(HASS), SH_APP, SH_DS)

U("4", "Node-RED Flow Exception Monitoring", "medium", "advanced", ["Fault", "Availability"],
  "index=personal sourcetype=nodered:event level=error\n"
  "| stats count as errors, latest(message) as last_message by node_id\n"
  "| where errors>0\n"
  "| sort - errors",
  "Surfaces exceptions thrown by your Node-RED flows so a crashed node stops silently breaking the automations built on top of it.",
  "Node-RED underpins many advanced smart homes; catching node exceptions prevents a single failing function from cascading through your flows.",
  "Forward Node-RED debug/error output to HEC; schedule hourly and alert on new exception sources.",
  "Table of Node-RED nodes by error count with last message.",
  "It catches errors in the wiring behind your smart home, so one broken piece does not quietly stop everything.",
  R(("Node-RED — Documentation", "https://nodered.org/docs/")), SH_APP, SH_DS, pillar="Observability")

U("4", "Scene Activation Trends", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=homeassistant:event event_type=scene_activated\n"
  "| timechart span=1d count by scene_name",
  "Trends how often each lighting or mood scene is activated so you can see which scenes earn their keep and which are clutter.",
  "Unused scenes make the app harder to use; usage trends tell you what to keep, tweak, or delete.",
  "Forward scene-activation events; schedule weekly and prune scenes that are never used.",
  "Stacked area chart of scene activations over time.",
  "It shows which of your saved lighting moods you actually use, so you can tidy up the ones you never touch.",
  R(HASS), SH_APP, SH_DS)

U("4", "Integration Restart and Reload Counter", "low", "intermediate", ["Reliability", "Availability"],
  "index=personal sourcetype=homeassistant:event (event_type=integration_reloaded OR message=\"*setup failed*\")\n"
  "| stats count as reloads, sum(eval(match(message,\"failed\"))) as failed_setups by integration\n"
  "| where reloads>0\n"
  "| sort - reloads",
  "Counts how often each Home Assistant integration reloads or fails to start, exposing the flaky ones that need attention or replacement.",
  "A frequently reloading integration is a slow-motion outage; counting reloads points you at the unstable add-ons dragging the whole hub down.",
  "Forward integration setup/reload events; schedule daily and review the least stable integrations.",
  "Table of integrations by reload and failed-setup count.",
  "It counts how often each smart-home add-on has to restart, so you can spot the unreliable ones.",
  R(HASS), SH_APP, SH_DS, pillar="Observability")

U("4", "Automation Latency (Trigger to Action)", "low", "advanced", ["Performance"],
  "index=personal sourcetype=homeassistant:event event_type=automation_triggered\n"
  "| eval latency_ms=action_time*1000-trigger_time*1000\n"
  "| stats avg(latency_ms) as avg_ms, p95(latency_ms) as p95_ms by automation\n"
  "| where p95_ms>2000\n"
  "| sort - p95_ms",
  "Measures the delay between an automation being triggered and its action completing, flagging the sluggish ones that make your home feel laggy.",
  "A light that takes two seconds to react feels broken; measuring automation latency finds the slow flows worth optimising.",
  "Forward automations with trigger and action timestamps; schedule daily and tune the slowest automations.",
  "Table of automations by 95th-percentile latency.",
  "It measures how long your home takes to react after something triggers it, so you can fix the slow, laggy routines.",
  R(HASS), SH_APP, SH_DS, pillar="Observability")


# ===========================================================================
# 25.5  Smart Home Devices & Sensors
# ===========================================================================
D_APP = ("Philips Hue, smart plugs (Tasmota/Shelly/TP-Link Kasa), thermostats (Nest/Ecobee), "
         "locks, and Zigbee/Z-Wave sensors via MQTT / Zigbee2MQTT bridged to HEC.")
D_DS = ("Zigbee2MQTT device reports (`zigbee2mqtt:device`), Shelly/Tasmota telemetry "
        "(`shelly:status`, `tasmota:sensor`), Hue events (`hue:event`), thermostats (`ecobee:thermostat`).")
Z2M = ("Zigbee2MQTT — Documentation", "https://www.zigbee2mqtt.io/")
SHELLY = ("Shelly — API documentation", "https://shelly-api-docs.shelly.cloud/")
ECOBEE = ("ecobee — Developer API", "https://www.ecobee.com/home/developer/api/introduction/index.shtml")

U("5", "Zigbee Sensor Low-Battery Roundup", "medium", "beginner", ["Availability", "Inventory"],
  "index=personal sourcetype=zigbee2mqtt:device\n"
  "| stats latest(battery) as battery, max(_time) as last_seen by friendly_name\n"
  "| where battery<20\n"
  "| eval battery=battery.\"%\"\n"
  "| sort battery",
  "Rounds up every Zigbee sensor whose battery is running low so you can replace them all in one trip instead of one dead sensor at a time.",
  "Scattered battery warnings are easy to ignore until a critical door or leak sensor dies; a single roundup makes battery care a five-minute chore.",
  "Bridge Zigbee2MQTT device reports to HEC; schedule daily and alert when any battery drops below 20 percent.",
  "Table of sensors by battery percentage, sorted lowest first.",
  "It lists every wireless sensor with a low battery, so you can change them all at once before any stop working.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Zigbee Mesh Link-Quality Weak Spots", "low", "advanced", ["Performance", "Reliability"],
  "index=personal sourcetype=zigbee2mqtt:device\n"
  "| stats avg(linkquality) as avg_lqi, min(linkquality) as min_lqi by friendly_name\n"
  "| where avg_lqi<40\n"
  "| sort avg_lqi",
  "Finds smart-home devices with a weak wireless link so you can add a repeater or move a router device before they start dropping off the mesh.",
  "Weak mesh links cause the maddening intermittent failures that are impossible to reproduce; surfacing them turns guesswork into a fix.",
  "Bridge Zigbee link-quality reports; schedule daily and review the weakest devices to plan repeater placement.",
  "Table of devices by average link quality.",
  "It finds the smart-home gadgets with a poor wireless signal, so you can fix them before they act up.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Smart Plug Energy Hogs", "low", "beginner", ["Cost", "Analytics"],
  "index=personal sourcetype=shelly:status\n"
  "| bin _time span=1d\n"
  "| stats sum(energy_wh) as wh by device_name _time\n"
  "| stats avg(wh) as avg_daily_wh by device_name\n"
  "| eval avg_daily_kwh=round(avg_daily_wh/1000,2)\n"
  "| sort - avg_daily_kwh",
  "Ranks your smart-plug-monitored appliances by average daily energy use so you can find the quiet money-drainers around the house.",
  "The biggest energy savings usually come from one or two surprising devices; ranking them shows exactly where to focus.",
  "Bridge Shelly/Tasmota energy telemetry to HEC; schedule daily and review the top consumers each week.",
  "Bar chart of average daily energy by device.",
  "It ranks which plugged-in gadgets use the most electricity, so you can find what is quietly running up the bill.",
  R(SHELLY), D_APP, D_DS, pillar="Observability")

U("5", "Standby Power (Vampire Load) Detection", "low", "advanced", ["Cost", "Anomaly"],
  "index=personal sourcetype=shelly:status power_w>0\n"
  "| stats min(power_w) as standby_w, max(power_w) as peak_w by device_name\n"
  "| where standby_w>2 AND standby_w<peak_w*0.1\n"
  "| eval annual_kwh=round(standby_w*24*365/1000,1)\n"
  "| sort - annual_kwh",
  "Detects devices that keep drawing power even when idle and estimates the yearly cost of that standby draw.",
  "Vampire loads can add up to a noticeable chunk of a power bill; quantifying them per device justifies a smart plug or a switched socket.",
  "Bridge per-device power readings; schedule weekly and target the biggest standby loads for switching off.",
  "Table of devices by estimated annual standby energy.",
  "It finds gadgets that keep sipping electricity even when switched off, and shows how much that wastes each year.",
  R(SHELLY), D_APP, D_DS, pillar="Observability")

U("5", "Indoor Temperature and Humidity Comfort Band", "low", "beginner", ["Analytics", "Quality"],
  "index=personal sourcetype=zigbee2mqtt:device\n"
  "| stats avg(temperature) as temp_c, avg(humidity) as humidity_pct by friendly_name\n"
  "| eval comfort=case(temp_c<18,\"cold\",temp_c>25,\"warm\",humidity_pct>60,\"humid\",humidity_pct<30,\"dry\",1=1,\"comfortable\")\n"
  "| where comfort!=\"comfortable\"",
  "Checks each room's temperature and humidity against a comfort band and flags rooms that are too cold, warm, damp, or dry.",
  "Comfort and mould risk both hide in humidity; a per-room comfort view catches the damp spare room before it becomes a problem.",
  "Bridge climate-sensor readings; schedule hourly and alert on rooms outside the comfort band.",
  "Table of rooms by temperature, humidity, and comfort flag.",
  "It checks each room is a comfortable temperature and not too damp or dry, which also helps prevent mould.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Water Leak Sensor Instant Alert", "high", "beginner", ["Safety", "Fault"],
  "index=personal sourcetype=zigbee2mqtt:device water_leak=true\n"
  "| stats max(_time) as detected, latest(friendly_name) as sensor by friendly_name\n"
  "| eval detected=strftime(detected,\"%F %T\")\n"
  "| sort - detected",
  "Fires the instant any leak sensor reports water, because minutes matter when a washing machine hose or boiler starts leaking.",
  "Water damage is among the costliest home disasters; a real-time leak alert can be the difference between a mopped floor and a ruined ceiling.",
  "Bridge leak-sensor state to HEC; schedule at the shortest interval and send a high-priority push the moment water is detected.",
  "Single-value alert panel with the triggering sensor and time.",
  "It shouts the moment a leak sensor gets wet, so you can stop a small leak before it wrecks the floor.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Door and Window Left-Open Reminder", "medium", "beginner", ["Safety", "Availability"],
  "index=personal sourcetype=zigbee2mqtt:device contact=false\n"
  "| stats max(_time) as opened by friendly_name\n"
  "| eval mins_open=round((now()-opened)/60)\n"
  "| where mins_open>30\n"
  "| sort - mins_open",
  "Flags doors and windows that have been open longer than expected, catching the garage door left up or a window forgotten before a storm.",
  "A door left open wastes heating and invites both intruders and weather; a simple duration check turns forgetfulness into a timely nudge.",
  "Bridge contact-sensor state; schedule every 10 minutes and alert on doors or windows open beyond your threshold.",
  "Table of open contacts by minutes open.",
  "It reminds you when a door or window has been left open too long, like the garage before you go to bed.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Thermostat Runtime and Efficiency", "low", "intermediate", ["Cost", "Analytics"],
  "index=personal sourcetype=ecobee:thermostat\n"
  "| bin _time span=1d\n"
  "| stats sum(heat_runtime_s) as heat_s, sum(cool_runtime_s) as cool_s, avg(outdoor_temp_c) as outdoor by _time\n"
  "| eval heat_hours=round(heat_s/3600,1), cool_hours=round(cool_s/3600,1)\n"
  "| sort - _time",
  "Trends how many hours your heating and cooling actually ran each day alongside the outdoor temperature so you can judge efficiency.",
  "Runtime versus outdoor temperature is the honest measure of your home's efficiency; a rising trend at the same weather hints at a failing system or lost insulation.",
  "Ingest Ecobee/Nest runtime and weather fields; schedule daily and watch runtime against outdoor temperature.",
  "Chart of daily heating/cooling hours overlaid with outdoor temperature.",
  "It shows how long your heating and cooling ran each day versus the weather, so you can tell if your home is getting less efficient.",
  R(ECOBEE), D_APP, D_DS, pillar="Observability")

U("5", "Smart Lock Access Audit", "medium", "beginner", ["Audit", "Physical Security"],
  "index=personal sourcetype=zigbee2mqtt:device event=lock_operation\n"
  "| stats count as operations, values(user_name) as users by action\n"
  "| sort - operations",
  "Keeps an audit trail of every smart-lock lock and unlock with who did it, so you know exactly who came and went.",
  "A lock history is reassuring and useful — it confirms the kids got home and flags an unlock you did not expect.",
  "Bridge lock-operation events; schedule daily and alert on unlocks outside expected hours or by unknown users.",
  "Table of lock operations by action with user names.",
  "It keeps a record of who locked and unlocked the door and when, so you know the family got home safely.",
  R(Z2M), D_APP, D_DS, pillar="Observability")

U("5", "Motion Sensor Activity Baseline", "low", "advanced", ["Anomaly", "Physical Security"],
  "index=personal sourcetype=zigbee2mqtt:device occupancy=true\n"
  "| bin _time span=1h\n"
  "| stats count as motion by _time friendly_name\n"
  "| eventstats avg(motion) as avg_motion, stdev(motion) as sd_motion by friendly_name\n"
  "| where motion>avg_motion+3*sd_motion\n"
  "| sort - _time",
  "Learns the normal motion pattern for each room and flags unusual activity, such as movement while you are away or at odd hours.",
  "Motion anomalies are a lightweight home-security signal; baselining per room suppresses the pet-and-routine noise that plagues naive alerts.",
  "Bridge motion events; schedule hourly and alert on motion that far exceeds the room's baseline, especially in away mode.",
  "Timeline of motion per room with anomaly markers.",
  "It learns the usual movement in each room and warns you about unusual activity, like motion while you are out.",
  R(Z2M), D_APP, D_DS, pillar="Observability")


# ===========================================================================
# 25.6  Home Energy & Solar
# ===========================================================================
E_APP = ("Solar inverters (SolarEdge/Enphase/Fronius/Growatt), Tesla Powerwall, and smart "
         "meters (P1/DSMR, Emporia Vue, Sense) via vendor APIs and MQTT to HEC.")
E_DS = ("SolarEdge/Enphase production (`solaredge:power`, `enphase:production`), Powerwall "
        "(`powerwall:aggregate`), smart-meter P1/DSMR (`dsmr:telegram`), Emporia Vue (`emporia:circuit`).")
SOLAREDGE = ("SolarEdge — Monitoring API", "https://knowledge-center.solaredge.com/sites/kc/files/se_monitoring_api.pdf")
ENPHASE = ("Enphase — Enlighten API", "https://developer.enphase.com/docs")
DSMR = ("DSMR / P1 smart-meter specification", "https://www.netbeheernederland.nl/dossiers/slimme-meter-15")

U("6", "Solar Production vs Home Consumption", "low", "beginner", ["Analytics", "Cost"],
  "index=personal sourcetype=solaredge:power\n"
  "| bin _time span=1d\n"
  "| stats sum(production_wh) as produced, sum(consumption_wh) as consumed by _time\n"
  "| eval self_sufficiency_pct=round(100*min(produced,consumed)/consumed,1)\n"
  "| sort - _time",
  "Compares how much energy your solar panels produced with how much your home used each day and calculates your self-sufficiency percentage.",
  "Self-sufficiency is the number that makes solar feel worthwhile; tracking it daily shows the payback and reveals your best and worst days.",
  "Ingest inverter production and meter consumption; schedule daily and trend your self-sufficiency percentage.",
  "Chart of daily production versus consumption with a self-sufficiency line.",
  "It compares how much power your solar panels made with how much your home used, so you can see how self-sufficient you are.",
  R(SOLAREDGE), E_APP, E_DS, pillar="Observability")

U("6", "Solar Panel Underperformance Detection", "medium", "advanced", ["Anomaly", "Fault"],
  "index=personal sourcetype=enphase:production\n"
  "| stats avg(power_w) as avg_power by inverter_serial\n"
  "| eventstats avg(avg_power) as fleet_avg\n"
  "| eval pct_of_fleet=round(100*avg_power/fleet_avg,1)\n"
  "| where pct_of_fleet<80\n"
  "| sort pct_of_fleet",
  "Compares each micro-inverter or panel against the average of the array and flags any that consistently underperform, pointing at shading, dirt, or a fault.",
  "A single failing panel can go unnoticed for months; peer comparison surfaces it so you can clean, unshade, or warranty-claim it.",
  "Ingest per-panel production; schedule daily over daylight hours and alert when a panel lags its peers.",
  "Bar chart of panels by percentage of array average.",
  "It compares each solar panel to the others and flags any that are lazy, which usually means dirt, shade, or a fault.",
  R(ENPHASE), E_APP, E_DS, pillar="Observability")

U("6", "Powerwall Battery Cycle and Reserve Tracking", "low", "intermediate", ["Analytics", "Reliability"],
  "index=personal sourcetype=powerwall:aggregate\n"
  "| bin _time span=1d\n"
  "| stats sum(battery_discharge_wh) as discharged, min(soc_pct) as min_soc, max(soc_pct) as max_soc by _time\n"
  "| eval cycles=round(discharged/13500,2)\n"
  "| sort - _time",
  "Estimates how many full battery cycles your home battery does each day and how low it drains, which drives both savings and long-term battery health.",
  "Cycle count is the main wear factor for a home battery; tracking it helps you balance bill savings against battery longevity.",
  "Ingest Powerwall aggregate data; schedule daily and review cycles and minimum state of charge.",
  "Chart of daily battery cycles and state-of-charge range.",
  "It tracks how hard your home battery works each day, which affects both your savings and how long the battery lasts.",
  R(("Tesla — Powerwall owner resources", "https://www.tesla.com/support/energy/powerwall")), E_APP, E_DS,
  pillar="Observability")

U("6", "Grid Import and Export Cost Balance", "low", "intermediate", ["Cost", "Analytics"],
  "index=personal sourcetype=dsmr:telegram\n"
  "| bin _time span=1d\n"
  "| stats sum(import_kwh) as import_kwh, sum(export_kwh) as export_kwh by _time\n"
  "| eval net_cost=round(import_kwh*0.30 - export_kwh*0.10,2)\n"
  "| sort - _time",
  "Balances the energy you bought from the grid against what you sold back and turns it into a daily net cost using your tariff.",
  "The net grid balance is what actually lands on your bill; seeing it daily connects your habits and the weather to real money.",
  "Ingest smart-meter import/export registers; set your tariffs and schedule daily to track net cost.",
  "Chart of daily grid import, export, and net cost.",
  "It works out each day whether you bought more electricity than you sold back, and what that costs.",
  R(DSMR), E_APP, E_DS, pillar="Observability")

U("6", "Peak Demand and Load-Shifting Opportunities", "low", "advanced", ["Cost", "Capacity"],
  "index=personal sourcetype=emporia:circuit\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats avg(power_w) as avg_w by hour circuit\n"
  "| where hour>=17 AND hour<=21 AND avg_w>500\n"
  "| sort - avg_w",
  "Identifies which circuits draw the most power during expensive peak hours so you can shift dishwashers, dryers, and charging to cheaper times.",
  "Load shifting is free money on a time-of-use tariff; pinpointing peak-hour loads shows exactly what to reschedule.",
  "Ingest per-circuit power; schedule weekly and target the biggest peak-hour loads for shifting.",
  "Heatmap of circuit power by hour with peak hours highlighted.",
  "It finds what uses the most electricity during the expensive evening hours, so you can run it later when power is cheaper.",
  R(("Emporia — Vue energy monitor", "https://www.emporiaenergy.com/how-the-vue-energy-monitor-works/")),
  E_APP, E_DS, pillar="Observability")

U("6", "Inverter Fault and Downtime Alert", "medium", "intermediate", ["Availability", "Fault"],
  "index=personal sourcetype=solaredge:power\n"
  "| eval daylight=if(strftime(_time,\"%H\")>=9 AND strftime(_time,\"%H\")<=16,1,0)\n"
  "| where daylight=1\n"
  "| stats sum(eval(production_wh=0)) as zero_intervals, count as intervals by _time\n"
  "| bin _time span=1d\n"
  "| stats sum(zero_intervals) as dead_intervals by _time\n"
  "| where dead_intervals>4",
  "Detects daylight hours when your inverter produced nothing, catching a tripped or failed inverter on the day it happens rather than at the next bill.",
  "An inverter that trips out on a sunny morning can cost a day's generation unnoticed; a same-day alert protects your production.",
  "Ingest inverter production; schedule mid-afternoon and alert on unexpected zero-production during daylight.",
  "Timeline of production with dead-interval markers.",
  "It notices when your solar system stops making power on a sunny day, so you can restart it and not lose a day's generation.",
  R(SOLAREDGE), E_APP, E_DS, pillar="Observability")

U("6", "Monthly Energy Bill Estimate", "low", "beginner", ["Cost", "Business"],
  "index=personal sourcetype=dsmr:telegram\n"
  "| bin _time span=1mon\n"
  "| stats sum(import_kwh) as import_kwh, sum(export_kwh) as export_kwh by _time\n"
  "| eval estimated_bill=round(import_kwh*0.30 - export_kwh*0.10 + 15,2)\n"
  "| sort - _time",
  "Projects your monthly electricity bill from real meter data plus your standing charge, so the bill is never a surprise.",
  "A running bill estimate lets you course-correct mid-month rather than opening a shock invoice at the end.",
  "Ingest meter data and set your tariff and standing charge; schedule daily to keep a live monthly estimate.",
  "Column chart of estimated monthly bill with a running current-month total.",
  "It estimates your electricity bill as the month goes, so it is never a nasty surprise.",
  R(DSMR), E_APP, E_DS)

U("6", "Weather-Normalised Solar Yield", "low", "advanced", ["Analytics", "Quality"],
  "index=personal sourcetype=solaredge:power\n"
  "| bin _time span=1d\n"
  "| stats sum(production_wh) as produced, avg(irradiance_wm2) as irradiance by _time\n"
  "| eval yield_per_sun=round(produced/irradiance,1)\n"
  "| timechart span=1w avg(yield_per_sun) as normalised_yield",
  "Divides your solar production by the available sunshine to produce a weather-normalised yield, revealing gradual efficiency loss that raw output hides.",
  "Raw output falls in winter for obvious reasons; normalising by sunshine exposes real degradation, soiling, or shading trends worth acting on.",
  "Ingest production and an irradiance estimate; schedule weekly and watch the normalised yield trend.",
  "Line chart of weather-normalised weekly yield.",
  "It adjusts your solar output for how sunny it actually was, so you can spot if the panels are slowly getting less effective.",
  R(SOLAREDGE), E_APP, E_DS, pillar="Observability")


# ===========================================================================
# 25.7  Media, Gaming & Entertainment
# ===========================================================================
M_APP = ("Plex / Jellyfin (Tautulli), Sonos, Spotify, Steam, Xbox/PSN, and the *arr stack "
         "(Sonarr/Radarr) APIs and webhooks via HEC scripted inputs.")
M_DS = ("Tautulli/Plex playback (`tautulli:play`), Jellyfin activity (`jellyfin:activity`), "
        "Spotify recently-played (`spotify:play`), Steam player/achievements (`steam:player`).")
TAUTULLI = ("Tautulli — Documentation", "https://github.com/Tautulli/Tautulli/wiki")
SPOTIFY = ("Spotify — Web API", "https://developer.spotify.com/documentation/web-api")
STEAM = ("Steam — Web API documentation", "https://steamcommunity.com/dev")

U("7", "Plex Watch-Time Leaderboard", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=tautulli:play\n"
  "| bin _time span=1mon\n"
  "| stats sum(duration_s) as secs by user _time\n"
  "| eval hours=round(secs/3600,1)\n"
  "| sort - hours",
  "Ranks who watched the most on your Plex server each month, the friendly leaderboard every home media server deserves.",
  "A watch-time leaderboard is pure fun and also tells you who your server is really for when you plan upgrades.",
  "Forward Tautulli playback events to HEC; schedule monthly and share the leaderboard with your household.",
  "Bar chart of monthly watch hours by user.",
  "It shows who watched the most on your home movie server each month, like a family leaderboard.",
  R(TAUTULLI), M_APP, M_DS)

U("7", "Plex Transcode Overload Warning", "medium", "advanced", ["Performance", "Capacity"],
  "index=personal sourcetype=tautulli:play transcode_decision=transcode\n"
  "| bin _time span=5m\n"
  "| stats dc(session_id) as concurrent_transcodes by _time\n"
  "| where concurrent_transcodes>2\n"
  "| sort - _time",
  "Watches for too many simultaneous video transcodes on your Plex server, the main cause of buffering and an overloaded home server.",
  "Transcoding is CPU-hungry; catching concurrent transcode spikes explains buffering complaints and tells you when to nudge clients to direct play.",
  "Forward Tautulli sessions; schedule frequently and alert when concurrent transcodes exceed your server's comfortable limit.",
  "Timeline of concurrent transcodes with a threshold line.",
  "It warns when too many people are streaming in a way that overloads your home server and causes buffering.",
  R(TAUTULLI), M_APP, M_DS, pillar="Observability")

U("7", "Spotify Listening Habits and Top Artists", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=spotify:play\n"
  "| bin _time span=1mon\n"
  "| stats sum(duration_ms) as ms, dc(track_id) as unique_tracks by artist _time\n"
  "| eval minutes=round(ms/60000)\n"
  "| sort - minutes\n"
  "| head 20",
  "Builds your own monthly listening wrap-up ranking your top artists and how much you explored, without waiting for a year-end summary.",
  "A personal, always-on listening summary is more fun and honest than a once-a-year recap and helps you notice music ruts.",
  "Ingest Spotify recently-played into `index=personal`; schedule monthly and enjoy your own listening wrap-up.",
  "Bar chart of monthly listening minutes by artist.",
  "It builds your own music summary each month, showing your favourite artists and how much you listened.",
  R(SPOTIFY), M_APP, M_DS)

U("7", "Steam Gaming Time and Backlog Tracker", "low", "beginner", ["Analytics", "Inventory"],
  "index=personal sourcetype=steam:player\n"
  "| stats latest(playtime_forever_min) as total_min, latest(playtime_2weeks_min) as recent_min by game_name\n"
  "| eval total_hours=round(total_min/60,1), never_played=if(total_min=0,\"backlog\",\"played\")\n"
  "| sort - total_hours",
  "Tracks how long you have spent in each game and flags the ever-growing backlog of titles you own but have never launched.",
  "The gaming backlog is a beloved running joke; quantifying it (and your actual playtime) helps you buy less and play more.",
  "Ingest Steam owned-games and playtime; schedule weekly and review your playtime and backlog.",
  "Table of games by total hours with a backlog flag.",
  "It shows how long you have played each game and how many you bought but never actually started.",
  R(STEAM), M_APP, M_DS)

U("7", "Gaming Achievement Progress", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=steam:player\n"
  "| where total_achievements>0\n"
  "| eval completion_pct=round(100*unlocked_achievements/total_achievements,1)\n"
  "| stats latest(completion_pct) as completion by game_name\n"
  "| where completion>0 AND completion<100\n"
  "| sort - completion",
  "Shows how close you are to completing the achievements in each game so you can chase the ones within reach.",
  "Achievement completion is a satisfying goal; surfacing the near-complete games turns idle backlog into achievable wins.",
  "Ingest per-game achievement counts; schedule weekly and celebrate games as they hit full completion.",
  "Bar chart of achievement completion percentage per game.",
  "It shows how close you are to finishing all the challenges in each game, so you can chase the easy wins.",
  R(STEAM), M_APP, M_DS)

U("7", "Media Server Library Growth", "low", "beginner", ["Capacity", "Analytics"],
  "index=personal sourcetype=jellyfin:activity event=item_added\n"
  "| bin _time span=1mon\n"
  "| stats count as items_added, sum(file_size_gb) as gb_added by _time library\n"
  "| sort - _time",
  "Trends how fast your media library is growing in both item count and disk space so storage upgrades never catch you off guard.",
  "Library growth quietly fills disks; trending it lets you plan storage before the server stops accepting new downloads.",
  "Forward library-add events; schedule monthly and project storage needs from the growth trend.",
  "Stacked column chart of monthly items and gigabytes added by library.",
  "It tracks how fast your movie and music collection is growing, so you can add storage before you run out.",
  R(("Jellyfin — Documentation", "https://jellyfin.org/docs/")), M_APP, M_DS, pillar="Observability")

U("7", "Download Queue Stall Detection (arr Stack)", "medium", "intermediate", ["Availability", "Fault"],
  "index=personal sourcetype=sonarr:event\n"
  "| stats count as events, sum(eval(status=\"warning\" OR status=\"failed\")) as problems, max(_time) as last_grab by indexer\n"
  "| eval hours_since_grab=round((now()-last_grab)/3600,1)\n"
  "| where problems>0 OR hours_since_grab>48\n"
  "| sort - problems",
  "Catches when your automated download manager stalls, whether from a failing indexer or a queue that has gone quiet for too long.",
  "A silently stalled download stack means your shows just stop appearing; monitoring indexers and grab recency keeps the pipeline flowing.",
  "Forward Sonarr/Radarr events; schedule every few hours and alert on failing indexers or a stalled queue.",
  "Table of indexers by problem count and time since last grab.",
  "It notices when your automatic TV and movie downloader gets stuck, so new episodes keep showing up.",
  R(("Sonarr — Wiki", "https://wiki.servarr.com/sonarr")), M_APP, M_DS, pillar="Observability")

U("7", "Late-Night Screen-Time Watchdog", "low", "beginner", ["Analytics", "Safety"],
  "index=personal sourcetype=tautulli:play\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| where hour>=0 AND hour<5\n"
  "| bin _time span=1w\n"
  "| stats sum(duration_s) as secs by _time\n"
  "| eval late_hours=round(secs/3600,1)",
  "Sums how much you stream in the small hours each week, gently surfacing the late-night binges that wreck the next day.",
  "Late viewing is a common sleep-wrecker; quantifying it connects a rough morning to last night's episode-after-episode habit.",
  "Forward playback events; schedule weekly and review late-night streaming as a sleep-hygiene signal.",
  "Column chart of weekly late-night streaming hours.",
  "It adds up how much you watch very late at night, which is often why the next morning feels rough.",
  R(TAUTULLI), M_APP, M_DS)


# ===========================================================================
# 25.8  Home Lab & Self-Hosting
# ===========================================================================
L_APP = ("Proxmox / Docker / Portainer, Synology/TrueNAS, Raspberry Pi, and UPS (NUT) metrics "
         "via the Splunk Universal Forwarder, collectd/telegraf, and HEC.")
L_DS = ("Proxmox node/VM metrics (`proxmox:metric`), Docker container stats (`docker:stats`), "
        "Synology/TrueNAS (`synology:disk`, `truenas:pool`), UPS status via NUT (`nut:ups`).")
PROXMOX = ("Proxmox VE — Documentation", "https://pve.proxmox.com/pve-docs/")
DOCKER = ("Docker — Engine API", "https://docs.docker.com/engine/api/")
NUT = ("Network UPS Tools (NUT) — Documentation", "https://networkupstools.org/documentation.html")

U("8", "Home Lab Disk Space Runway", "high", "intermediate", ["Capacity", "Availability"],
  "index=personal sourcetype=truenas:pool\n"
  "| stats latest(used_pct) as used_pct, latest(free_gb) as free_gb by pool\n"
  "| where used_pct>80\n"
  "| sort - used_pct",
  "Watches your NAS pools for filling disks and flags any above a safe threshold before a full pool corrupts downloads or stops backups.",
  "A full storage pool is one of the fastest ways to break a home lab; an early warning gives you time to prune or expand.",
  "Forward TrueNAS/Synology pool stats; schedule hourly and alert when a pool crosses your capacity threshold.",
  "Table of pools by used percentage with a runway estimate.",
  "It warns you when the storage in your home server is filling up, before it gets full and things break.",
  R(("TrueNAS — Documentation Hub", "https://www.truenas.com/docs/")), L_APP, L_DS, pillar="Observability")

U("8", "Docker Container Restart-Loop Detection", "high", "advanced", ["Availability", "Fault"],
  "index=personal sourcetype=docker:stats\n"
  "| stats max(restart_count) as restarts, latest(status) as status by container_name\n"
  "| streamstats current=f last(restarts) as prev by container_name\n"
  "| eval delta=restarts-coalesce(prev,restarts)\n"
  "| where delta>3\n"
  "| sort - delta",
  "Detects containers that are crash-looping by watching their restart counter climb, catching a broken self-hosted app before you notice it is down.",
  "A crash-looping container quietly burns resources and stays offline; catching the restart pattern points you straight at the failing service.",
  "Forward Docker stats/events to HEC; schedule every few minutes and alert on rapidly rising restart counts.",
  "Table of containers by recent restart count.",
  "It spots when one of your self-hosted apps keeps crashing and restarting, so you can fix it.",
  R(DOCKER), L_APP, L_DS, pillar="Observability")

U("8", "Proxmox Node Resource Saturation", "high", "advanced", ["Capacity", "Performance"],
  "index=personal sourcetype=proxmox:metric\n"
  "| stats max(cpu_pct) as max_cpu, avg(cpu_pct) as avg_cpu, max(mem_pct) as max_mem by node\n"
  "| where max_cpu>90 OR max_mem>90\n"
  "| sort - max_cpu",
  "Tracks CPU and memory pressure on your Proxmox hosts and flags nodes running hot, which slows every virtual machine on them.",
  "One saturated host degrades all its guests at once; catching it early lets you rebalance virtual machines before everything crawls.",
  "Forward Proxmox node metrics; schedule every 10 minutes and alert on sustained high CPU or memory.",
  "Heatmap of nodes by peak CPU and memory.",
  "It watches how hard your home server hosts are working, so you can rebalance before everything slows down.",
  R(PROXMOX), L_APP, L_DS, pillar="Observability")

U("8", "UPS Battery and Runtime Health", "high", "beginner", ["Availability", "Reliability"],
  "index=personal sourcetype=nut:ups\n"
  "| stats latest(battery_charge_pct) as charge, latest(runtime_s) as runtime_s, latest(status) as status by ups_name\n"
  "| eval runtime_min=round(runtime_s/60,1)\n"
  "| where status!=\"OL\" OR charge<50 OR runtime_min<10\n"
  "| sort runtime_min",
  "Monitors your battery backup for mains-power loss, a weak battery, or a shrinking runtime so it can actually protect your gear when it matters.",
  "A UPS with a worn battery gives a false sense of safety; checking charge and runtime ensures it survives the next power cut.",
  "Forward NUT UPS status; schedule every few minutes and alert on power loss, low charge, or degraded runtime.",
  "Table of UPS units by charge, runtime, and status.",
  "It checks the backup battery for your home server so it can actually keep things running during a power cut.",
  R(NUT), L_APP, L_DS, pillar="Observability")

U("8", "Self-Hosted Service Uptime (Blackbox)", "medium", "intermediate", ["Availability"],
  "index=personal sourcetype=uptime:probe\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(status=\"up\")) as up_checks, count as total by service _time\n"
  "| eval uptime_pct=round(100*up_checks/total,2)\n"
  "| where uptime_pct<99\n"
  "| sort uptime_pct",
  "Calculates the daily uptime of each self-hosted service from health-check probes so you have real numbers instead of a vague sense of flakiness.",
  "Your own status page is deeply satisfying and genuinely useful; per-service uptime shows which app to harden next.",
  "Run HTTP/TCP health probes and forward results; schedule daily and alert when a service drops below its uptime target.",
  "Table of services by daily uptime percentage.",
  "It measures how reliably each of your home-run apps stays online, giving you your own little status page.",
  R(("Blackbox exporter / uptime monitoring", "https://github.com/prometheus/blackbox_exporter")), L_APP, L_DS,
  pillar="Observability")

U("8", "Backup Job Success and Freshness", "high", "intermediate", ["Data Quality", "Availability"],
  "index=personal sourcetype=proxmox:metric event=backup\n"
  "| stats latest(status) as last_status, max(_time) as last_backup by vm_name\n"
  "| eval hours_since=round((now()-last_backup)/3600,1)\n"
  "| where last_status!=\"ok\" OR hours_since>36\n"
  "| sort - hours_since",
  "Confirms that every virtual machine and dataset actually backed up recently and successfully, closing the gap between assuming and knowing.",
  "The worst time to discover a broken backup is during a restore; freshness and success checks make your safety net trustworthy.",
  "Forward backup job results; schedule daily and alert on any failed or overdue backup.",
  "Table of protected items by last backup status and age.",
  "It makes sure your important files and servers really did back up recently, so you are safe if something breaks.",
  R(PROXMOX), L_APP, L_DS, pillar="Observability")

U("8", "Raspberry Pi Temperature and Throttling", "medium", "beginner", ["Performance", "Fault"],
  "index=personal sourcetype=rpi:metric\n"
  "| stats max(cpu_temp_c) as peak_temp, sum(eval(throttled=1)) as throttle_events by host\n"
  "| where peak_temp>80 OR throttle_events>0\n"
  "| sort - peak_temp",
  "Watches your Raspberry Pis for overheating and CPU throttling, the usual culprit behind a sluggish or crashing Pi project.",
  "A throttling Pi is slow for a reason you cannot see in the app; surfacing temperature and throttling points at a fan or heatsink fix.",
  "Forward Pi temperature and throttle flags; schedule every few minutes and alert on overheating.",
  "Table of Pis by peak temperature and throttle-event count.",
  "It watches your little home-project computers for overheating, which is usually why they get slow or crash.",
  R(("Raspberry Pi — vcgencmd and throttling", "https://www.raspberrypi.com/documentation/computers/os.html")),
  L_APP, L_DS, pillar="Observability")

U("8", "SMART Disk Failure Early Warning", "high", "advanced", ["Reliability", "Fault"],
  "index=personal sourcetype=synology:disk\n"
  "| stats latest(reallocated_sectors) as realloc, latest(pending_sectors) as pending, latest(smart_status) as smart by disk\n"
  "| where realloc>0 OR pending>0 OR smart!=\"normal\"\n"
  "| sort - realloc",
  "Reads the self-diagnostic attributes of your NAS disks and flags the early warning signs of a drive about to fail.",
  "Disks rarely die without warning in their diagnostics; catching reallocated or pending sectors early lets you swap the drive before data loss.",
  "Forward disk self-diagnostic attributes; schedule daily and alert on any degrading drive.",
  "Table of disks by reallocated and pending sector counts.",
  "It reads the health warnings built into your storage drives so you can replace one before it fails and loses data.",
  R(("Synology — DSM Storage Manager", "https://kb.synology.com/en-global/DSM/help/DSM/StorageManager/storage_pool")),
  L_APP, L_DS, pillar="Observability")

U("8", "Container Image Update Backlog", "low", "intermediate", ["Vulnerability", "Change"],
  "index=personal sourcetype=docker:stats\n"
  "| stats latest(image_age_days) as age_days, latest(update_available) as update_available by container_name\n"
  "| where update_available=\"true\" AND age_days>30\n"
  "| sort - age_days",
  "Lists self-hosted containers running old images with an update available, so security patches do not pile up unnoticed.",
  "Self-hosted apps miss the auto-updates cloud services get; a staleness list keeps your exposure low without a full patch-management tool.",
  "Forward image age and update-availability data; schedule weekly and review the update backlog.",
  "Table of containers by image age with an update flag.",
  "It lists your self-hosted apps that are overdue for updates, so security fixes do not pile up.",
  R(DOCKER), L_APP, L_DS, pillar="Observability")


# ===========================================================================
# 25.9  Home Network & Connectivity
# ===========================================================================
N_APP = ("UniFi / router syslog, Pi-hole/AdGuard, and scheduled speedtests via HEC scripted "
         "inputs and the Universal Forwarder.")
N_DS = ("UniFi controller events (`unifi:event`), Pi-hole query log (`pihole:query`), AdGuard "
        "Home (`adguard:query`), speedtest-cli results (`speedtest:result`), router/firewall syslog.")
UNIFI = ("Ubiquiti — UniFi Network documentation", "https://help.ui.com/hc/en-us/categories/6583256751383")
PIHOLE = ("Pi-hole — Documentation", "https://docs.pi-hole.net/")
SPEEDTEST = ("Ookla Speedtest CLI", "https://www.speedtest.net/apps/cli")

U("9", "Internet Speed vs Paid Plan", "medium", "beginner", ["Performance", "Business"],
  "index=personal sourcetype=speedtest:result\n"
  "| timechart span=1d avg(download_mbps) as download, avg(upload_mbps) as upload\n"
  "| eval paid_download=500, shortfall=round(paid_download-download,1)",
  "Runs scheduled speed tests and trends your actual internet speed against the plan you pay for, giving you evidence when it falls short.",
  "Internet providers rarely deliver the headline speed; a long-run record is exactly what you need to demand a fix or a refund.",
  "Schedule speedtest-cli and forward results to HEC; run several times a day and alert when speed drops well below your plan.",
  "Line chart of daily download/upload against the paid-plan line.",
  "It regularly checks your internet speed against what you pay for, giving you proof when it is too slow.",
  R(SPEEDTEST), N_APP, N_DS, pillar="Observability")

U("9", "Internet Outage Detection and Log", "high", "intermediate", ["Availability"],
  "index=personal sourcetype=uptime:probe target=internet\n"
  "| sort 0 _time\n"
  "| streamstats current=f last(status) as prev_status\n"
  "| where status=\"down\" AND prev_status=\"up\"\n"
  "| table _time status\n"
  "| sort - _time",
  "Records every moment your internet connection drops so you have a dated outage log to raise with your provider.",
  "Providers ask 'when exactly?' — an automatic outage log answers with timestamps and turns anecdotes into a credible complaint.",
  "Probe an external target continuously and forward results; schedule frequently and alert on transitions to down.",
  "Timeline of outages with start times and durations.",
  "It keeps a dated list of every time your internet went down, which is exactly what your provider asks for.",
  R(("Internet uptime monitoring", "https://github.com/prometheus/blackbox_exporter")), N_APP, N_DS,
  pillar="Observability")

U("9", "Pi-hole Ad-Block Effectiveness", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=pihole:query\n"
  "| stats count as total, sum(eval(blocked=\"true\")) as blocked\n"
  "| eval block_rate=round(100*blocked/total,1)",
  "Calculates what percentage of your household's DNS requests Pi-hole blocked, the satisfying number that shows your ad-blocker earning its keep.",
  "A visible block rate proves the value of network-wide ad blocking and helps you tune blocklists for the right balance.",
  "Forward the Pi-hole query log to HEC; schedule daily and trend the block rate over time.",
  "Gauge of block rate with a trend line.",
  "It shows what share of ads and trackers your network blocker stopped, which is very satisfying to watch.",
  R(PIHOLE), N_APP, N_DS, pillar="Observability")

U("9", "Top DNS Talkers and Chatty Devices", "low", "intermediate", ["Analytics", "Anomaly"],
  "index=personal sourcetype=pihole:query\n"
  "| stats count as queries, dc(domain) as unique_domains by client\n"
  "| sort - queries\n"
  "| head 15",
  "Ranks which devices make the most DNS requests, revealing the chatty smart gadget or the phone phoning home far more than expected.",
  "An unusually chatty device can indicate misbehaving firmware or unwanted tracking; ranking talkers makes the oddball obvious.",
  "Forward the query log; schedule daily and investigate any device whose query volume looks out of place.",
  "Bar chart of DNS queries by client device.",
  "It shows which of your devices chatter the most on the network, which can reveal a gadget behaving oddly.",
  R(PIHOLE), N_APP, N_DS, pillar="Observability")

U("9", "New Device Joined Network Alert", "medium", "beginner", ["Physical Security", "Inventory"],
  "index=personal sourcetype=unifi:event event_key=\"EVT_LU_Connected\"\n"
  "| stats earliest(_time) as first_seen by mac hostname\n"
  "| eval age_hours=round((now()-first_seen)/3600,1)\n"
  "| where age_hours<24\n"
  "| sort - first_seen",
  "Alerts when a device never seen before joins your Wi-Fi, catching both a neighbour on your password and a new gadget you forgot you set up.",
  "A rogue device on your network is a real privacy and security concern; first-seen detection is a simple, effective tripwire.",
  "Forward UniFi client-connect events; schedule hourly and alert on any newly seen MAC address.",
  "Table of newly seen devices with first-seen time.",
  "It tells you when a device you have never seen before joins your Wi-Fi, like a neighbour guessing your password.",
  R(UNIFI), N_APP, N_DS, pillar="Observability")

U("9", "Wi-Fi Signal and Roaming Quality", "low", "advanced", ["Performance", "Quality"],
  "index=personal sourcetype=unifi:event\n"
  "| stats avg(signal_dbm) as avg_signal, min(signal_dbm) as worst_signal, dc(ap_mac) as aps_used by hostname\n"
  "| where avg_signal<-70\n"
  "| sort avg_signal",
  "Finds devices stuck on a weak Wi-Fi signal or bouncing between access points, the hidden cause of drops and slow speeds in far rooms.",
  "Weak signal and bad roaming explain most 'the Wi-Fi is bad in the bedroom' complaints; the data points at where to add an access point.",
  "Forward UniFi client statistics; schedule daily and review devices with consistently weak signal.",
  "Table of devices by average and worst signal strength.",
  "It finds devices with a weak Wi-Fi signal, explaining why the connection is bad in certain rooms.",
  R(UNIFI), N_APP, N_DS, pillar="Observability")

U("9", "Firewall Blocked-Connection Trends", "medium", "intermediate", ["Security", "Anomaly"],
  "index=personal sourcetype=unifi:event event_key=\"EVT_GW_Blocked\"\n"
  "| timechart span=1h count as blocked_connections\n"
  "| eventstats avg(blocked_connections) as avg_blocked, stdev(blocked_connections) as sd_blocked\n"
  "| eval spike=if(blocked_connections>avg_blocked+3*sd_blocked,1,0)",
  "Trends the connections your home firewall blocked and flags unusual spikes that can signal scanning or a compromised device reaching out.",
  "A blocked-connection spike is a lightweight intrusion signal; baselining it separates routine internet background noise from something worth a look.",
  "Forward firewall/gateway block events; schedule hourly and alert on statistically unusual spikes.",
  "Timeline of blocked connections with anomaly markers.",
  "It watches what your home firewall is blocking and warns you about unusual spikes that could mean trouble.",
  R(UNIFI), N_APP, N_DS, pillar="Security", )

U("9", "Bandwidth Hog Identification", "low", "intermediate", ["Capacity", "Analytics"],
  "index=personal sourcetype=unifi:event\n"
  "| bin _time span=1d\n"
  "| stats sum(tx_bytes) as up_bytes, sum(rx_bytes) as down_bytes by hostname _time\n"
  "| eval total_gb=round((up_bytes+down_bytes)/1073741824,2)\n"
  "| stats avg(total_gb) as avg_daily_gb by hostname\n"
  "| sort - avg_daily_gb",
  "Ranks which devices use the most data each day, explaining a slow connection or a data-capped plan creeping toward its limit.",
  "When the internet feels slow, the culprit is usually one device; ranking daily usage names it without guesswork.",
  "Forward per-client traffic counters; schedule daily and review the heaviest users.",
  "Bar chart of average daily data use by device.",
  "It shows which devices use the most internet data, explaining why things feel slow or your data cap is close.",
  R(UNIFI), N_APP, N_DS, pillar="Observability")


# ===========================================================================
# 25.10  Weather, Environment & Garden
# ===========================================================================
W_APP = ("Personal weather stations (Ecowitt/Ambient/Davis/WeatherFlow), air-quality sensors "
         "(PurpleAir/AirGradient), and aquarium/greenhouse/soil sensors via HEC and MQTT.")
W_DS = ("Weather-station observations (`ecowitt:obs`, `weatherflow:obs`), air-quality readings "
        "(`purpleair:aqi`, `airgradient:sensor`), soil/greenhouse sensors, aquarium controllers.")
ECOWITT = ("Ecowitt — API documentation", "https://doc.ecowitt.net/web/#/apiv3en")
PURPLEAIR = ("PurpleAir — API documentation", "https://api.purpleair.com/")
WEATHERFLOW = ("WeatherFlow Tempest — API", "https://weatherflow.github.io/Tempest/api/")

U("10", "Indoor Air Quality Alert", "medium", "beginner", ["Safety", "Anomaly"],
  "index=personal sourcetype=airgradient:sensor\n"
  "| stats latest(pm25) as pm25, latest(co2_ppm) as co2, latest(voc_index) as voc by location\n"
  "| eval concern=case(pm25>35,\"high particulates\",co2>1000,\"stuffy air\",voc>250,\"high VOCs\",1=1,\"good\")\n"
  "| where concern!=\"good\"",
  "Watches indoor air-quality sensors for high particulates, stale carbon dioxide, or volatile chemicals and tells you which room needs a window open.",
  "Poor indoor air harms sleep and focus in ways you cannot feel; a per-room alert turns invisible air quality into a simple action.",
  "Forward air-quality sensor readings to HEC; schedule every 15 minutes and alert when a room crosses a health threshold.",
  "Table of rooms by particulates, carbon dioxide, and chemical levels.",
  "It watches the air inside your home and tells you when a room is stuffy or unhealthy and needs a window opened.",
  R(("AirGradient — Documentation", "https://www.airgradient.com/documentation/")), W_APP, W_DS,
  pillar="Observability")

U("10", "Outdoor Air-Quality (Wildfire Smoke) Watch", "high", "beginner", ["Safety", "Anomaly"],
  "index=personal sourcetype=purpleair:aqi\n"
  "| timechart span=1h avg(aqi) as aqi\n"
  "| eval category=case(aqi<=50,\"good\",aqi<=100,\"moderate\",aqi<=150,\"unhealthy for sensitive\",1=1,\"unhealthy\")\n"
  "| where aqi>100",
  "Trends the outdoor air-quality index from a nearby sensor and alerts when smoke or pollution makes it unsafe to open windows or exercise outside.",
  "During wildfire season a local sensor beats a distant official station; a timely alert protects your lungs and tells you when to close up.",
  "Ingest a local outdoor air-quality feed; schedule hourly and alert when the index becomes unhealthy.",
  "Line chart of hourly outdoor air-quality index with category bands.",
  "It watches the outdoor air near your home and warns you when smoke or pollution makes it unhealthy to go outside.",
  R(PURPLEAIR), W_APP, W_DS, pillar="Observability")

U("10", "Frost and Freeze Warning", "medium", "beginner", ["Anomaly", "Safety"],
  "index=personal sourcetype=ecowitt:obs\n"
  "| where outdoor_temp_c<3\n"
  "| stats min(outdoor_temp_c) as low_temp, latest(_time) as when by date_mday\n"
  "| eval when=strftime(when,\"%F %T\")\n"
  "| sort - when",
  "Warns when your weather station reports temperatures approaching freezing so you can protect plants, pipes, and the car windscreen.",
  "A local frost warning is more accurate than a regional forecast; acting the night before saves tender plants and burst pipes.",
  "Ingest weather-station temperature; schedule each evening and alert when a frost is likely overnight.",
  "Table of frost nights with the low temperature reached.",
  "It warns you when it is about to freeze so you can cover plants and protect pipes before the cold hits.",
  R(ECOWITT), W_APP, W_DS, pillar="Observability")

U("10", "Rainfall Accumulation and Dry-Spell Tracker", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=ecowitt:obs\n"
  "| bin _time span=1d\n"
  "| stats sum(rain_mm) as rain_mm by _time\n"
  "| streamstats current=t sum(eval(if(rain_mm=0,1,0))) as dry_streak reset_after=\"(rain_mm>0)\"\n"
  "| sort - _time",
  "Tracks daily rainfall and counts consecutive dry days so gardeners know exactly when to water and when nature has done it for them.",
  "A running dry-spell counter saves both water and plants by turning 'has it rained lately?' into a definite number.",
  "Ingest weather-station rainfall; schedule daily and use the dry-streak counter to guide watering.",
  "Column chart of daily rainfall with a dry-streak overlay.",
  "It tracks how much rain fell and how many dry days in a row, so you know exactly when the garden needs watering.",
  R(ECOWITT), W_APP, W_DS, pillar="Observability")

U("10", "Wind Gust and Storm Alert", "medium", "beginner", ["Safety", "Anomaly"],
  "index=personal sourcetype=weatherflow:obs\n"
  "| stats max(wind_gust_ms) as peak_gust, avg(wind_avg_ms) as avg_wind by date_hour\n"
  "| where peak_gust>15\n"
  "| sort - peak_gust",
  "Flags high wind gusts recorded at your own location so you can secure garden furniture, trampolines, and bins before they take off.",
  "Hyper-local wind data beats a town-wide forecast; a timely gust alert prevents the classic storm-day chase down the street.",
  "Ingest weather-station wind data; schedule hourly and alert when gusts exceed your threshold.",
  "Chart of peak wind gusts by hour with a warning threshold.",
  "It warns you about strong winds at your home so you can tie down garden furniture before a storm.",
  R(WEATHERFLOW), W_APP, W_DS, pillar="Observability")

U("10", "Greenhouse and Soil-Moisture Guardian", "medium", "intermediate", ["Safety", "Quality"],
  "index=personal sourcetype=plant:sensor\n"
  "| stats latest(soil_moisture_pct) as moisture, latest(temp_c) as temp by plant\n"
  "| eval status=case(moisture<20,\"needs water\",temp>35,\"too hot\",temp<5,\"too cold\",1=1,\"happy\")\n"
  "| where status!=\"happy\"\n"
  "| sort moisture",
  "Watches soil moisture and temperature for your plants or greenhouse and tells you exactly which ones need water or shelter.",
  "Plant sensors turn a green thumb into a data feed; per-plant alerts save a prized tomato crop from a hot weekend away.",
  "Forward soil and greenhouse sensor readings; schedule twice daily and alert on plants that are dry or stressed.",
  "Table of plants by soil moisture and temperature with a status flag.",
  "It watches your plants and tells you which ones are thirsty or too hot, so nothing wilts while you are busy.",
  R(("Home Assistant — Plant integration", "https://www.home-assistant.io/integrations/plant/")), W_APP, W_DS,
  pillar="Observability")

U("10", "Aquarium Water-Parameter Stability", "medium", "advanced", ["Safety", "Anomaly"],
  "index=personal sourcetype=aquarium:sensor\n"
  "| stats latest(temp_c) as temp, latest(ph) as ph, avg(temp_c) as avg_temp, stdev(temp_c) as sd_temp by tank\n"
  "| eval unstable=if(abs(temp-avg_temp)>2*sd_temp OR ph<6.5 OR ph>8.5,1,0)\n"
  "| where unstable=1",
  "Monitors aquarium temperature and pH for sudden swings that stress or kill fish, catching a failing heater or chiller before it is too late.",
  "Fish are unforgiving of parameter swings; continuous monitoring with anomaly detection is the difference between a healthy tank and a disaster.",
  "Forward aquarium controller readings; schedule frequently and alert on temperature swings or pH outside the safe band.",
  "Chart of tank temperature and pH with stability bands.",
  "It keeps an eye on your fish tank's temperature and water balance, warning you before a broken heater harms the fish.",
  R(("Home Assistant — MQTT sensor", "https://www.home-assistant.io/integrations/sensor.mqtt/")), W_APP, W_DS,
  pillar="Observability")

U("10", "UV Index and Sun-Safety Advisory", "low", "beginner", ["Safety", "Analytics"],
  "index=personal sourcetype=ecowitt:obs\n"
  "| stats max(uv_index) as peak_uv, latest(_time) as when by date_mday\n"
  "| eval advice=case(peak_uv>=8,\"extreme - cover up\",peak_uv>=6,\"high - sunscreen\",peak_uv>=3,\"moderate\",1=1,\"low\")\n"
  "| sort - when",
  "Records the peak ultraviolet index each day from your weather station and turns it into simple sun-safety advice for the family.",
  "Local ultraviolet readings help you plan outdoor time and remember sunscreen, especially for children and fair skin.",
  "Ingest weather-station ultraviolet readings; schedule daily and surface the peak with plain-language advice.",
  "Column chart of daily peak ultraviolet index with advisory bands.",
  "It records how strong the sun was each day and reminds you when to wear sunscreen or stay in the shade.",
  R(ECOWITT), W_APP, W_DS, pillar="Observability")


# ===========================================================================
# 25.11  Pets & Home Life
# ===========================================================================
P_APP = ("Pet GPS/activity trackers (Tractive/Fi/Whistle), smart feeders and litter boxes, "
         "bird feeders/cams, and plant sensors via vendor APIs and MQTT to HEC.")
P_DS = ("Pet tracker location/activity (`tractive:position`, `whistle:activity`), smart feeder "
        "events (`petfeeder:event`), litter-box usage (`litterrobot:cycle`), bird-feeder detections.")
TRACTIVE = ("Tractive — GPS pet tracker", "https://tractive.com/en/pd/gps-tracker-dog")
WHISTLE = ("Whistle — Pet health and GPS", "https://www.whistle.com/")

U("11", "Pet Daily Activity vs Goal", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=whistle:activity\n"
  "| bin _time span=1d\n"
  "| stats sum(active_minutes) as active_min by pet_name _time\n"
  "| eval goal=60, met=if(active_min>=goal,\"active enough\",\"needs a walk\")\n"
  "| sort - _time",
  "Tracks how much daily activity your pet gets against a vet-style goal so an under-exercised dog gets the walks it needs.",
  "Pet obesity is common and harmful; a simple daily activity target keeps your dog healthy and gives you a nudge to get out.",
  "Ingest pet-tracker activity into `index=personal`; schedule daily and nudge yourself when your pet is short on activity.",
  "Column chart of pet active minutes against a daily goal.",
  "It checks your pet got enough exercise each day, and reminds you when it is time for another walk.",
  R(WHISTLE), P_APP, P_DS)

U("11", "Pet Left the Safe Zone Alert", "high", "beginner", ["Safety", "Physical"],
  "index=personal sourcetype=tractive:position\n"
  "| eval outside=if(in_safe_zone=\"false\",1,0)\n"
  "| where outside=1\n"
  "| stats min(_time) as left_at, latest(latitude) as lat, latest(longitude) as lon by pet_name\n"
  "| eval left_at=strftime(left_at,\"%F %T\")",
  "Fires the moment a pet's GPS tracker reports it has left your defined safe zone, so an escaped dog or wandering cat is caught early.",
  "The first minutes of an escape matter most; an instant geofence alert with a location can turn a frantic search into a quick recovery.",
  "Ingest pet GPS positions and geofence state; schedule at the shortest interval and send a high-priority alert on any breach.",
  "Map and alert panel showing the pet's location when it left the safe zone.",
  "It alerts you the instant your pet wanders out of the safe area, with a map so you can go straight to them.",
  R(TRACTIVE), P_APP, P_DS, pillar="Observability")

U("11", "Smart Feeder Missed-Meal Detection", "medium", "beginner", ["Availability", "Fault"],
  "index=personal sourcetype=petfeeder:event\n"
  "| stats latest(status) as last_status, max(_time) as last_feed by feeder\n"
  "| eval hours_since=round((now()-last_feed)/3600,1)\n"
  "| where last_status=\"failed\" OR hours_since>14\n"
  "| sort - hours_since",
  "Confirms your automatic pet feeder actually dispensed each scheduled meal and alerts on a jam or a missed feeding.",
  "A stuck feeder means a hungry pet while you are out; verifying each meal turns 'I hope it fed them' into certainty.",
  "Forward feeder dispense events; schedule after each meal window and alert on failures or overdue feeds.",
  "Table of feeders by last feed status and time.",
  "It makes sure the automatic feeder really fed your pet, and warns you if it jammed or missed a meal.",
  R(("PetLibro / smart feeder integrations", "https://www.home-assistant.io/integrations/")), P_APP, P_DS,
  pillar="Observability")

U("11", "Litter Box Usage Health Signal", "medium", "intermediate", ["Analytics", "Safety"],
  "index=personal sourcetype=litterrobot:cycle\n"
  "| bin _time span=1d\n"
  "| stats count as visits by _time\n"
  "| eventstats avg(visits) as avg_visits, stdev(visits) as sd_visits\n"
  "| eval anomaly=if(abs(visits-avg_visits)>2*sd_visits,1,0)\n"
  "| where anomaly=1",
  "Trends how often the litter box is used and flags sudden changes, which for cats can be an early sign of a urinary or kidney problem.",
  "Cats hide illness well, but litter-box frequency does not; an anomaly alert can prompt a vet visit before a problem becomes serious.",
  "Forward litter-box cycle events; schedule daily and alert on a significant change in usage frequency.",
  "Chart of daily litter-box visits with anomaly markers.",
  "It watches how often the cat uses the litter box, because a sudden change can be an early sign of illness.",
  R(("Litter-Robot — smart litter box", "https://www.litter-robot.com/")), P_APP, P_DS, pillar="Observability")

U("11", "Bird Feeder Visitor Species Log", "low", "intermediate", ["Analytics", "Inventory"],
  "index=personal sourcetype=birdfeeder:detection confidence>0.7\n"
  "| bin _time span=1d\n"
  "| stats count as visits, dc(species) as species_seen by _time\n"
  "| stats sum(visits) as total_visits, max(species_seen) as daily_species by species\n"
  "| sort - total_visits",
  "Turns your smart bird feeder's camera detections into a running log of which species visited and how often, a delightful backyard biodiversity record.",
  "A species log makes a hobby measurable and rewarding, and over time reveals seasonal migration and the effect of different seed.",
  "Forward bird-camera detections with species and confidence; schedule daily and build a species leaderboard.",
  "Bar chart of visits by species over time.",
  "It keeps a fun log of which birds visited your feeder and how often, like a backyard nature diary.",
  R(("Bird feeder AI cameras", "https://www.home-assistant.io/integrations/")), P_APP, P_DS)

U("11", "Pet Sleep and Rest Pattern", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=whistle:activity\n"
  "| timechart span=1d avg(rest_minutes) as rest, avg(active_minutes) as active by pet_name",
  "Trends your pet's rest and activity balance day to day, giving you a baseline that makes a lethargic or restless spell obvious.",
  "Changes in a pet's rest pattern are a subtle health signal; a baseline turns 'seems a bit off' into something you can actually see.",
  "Ingest pet rest/activity data; schedule daily and review the balance for sudden shifts.",
  "Line chart of pet rest versus active minutes per day.",
  "It shows how much your pet rested and played each day, so you notice if they suddenly seem off.",
  R(WHISTLE), P_APP, P_DS)

U("11", "Doorbell and Package-Delivery Tracker", "low", "beginner", ["Analytics", "Physical Security"],
  "index=personal sourcetype=doorbell:event event=motion OR event=ring OR event=package\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(event=\"package\")) as deliveries, sum(eval(event=\"ring\")) as rings by _time\n"
  "| sort - _time",
  "Counts doorbell rings and detected package deliveries per day so you have a tidy record of who came by and what arrived.",
  "A delivery log settles the 'did it actually arrive?' question and, with rings, shows patterns like a regular caller or missed visitors.",
  "Forward doorbell events; schedule daily and review the delivery and visitor log.",
  "Column chart of daily deliveries and rings.",
  "It keeps a daily tally of doorbell rings and deliveries, so you know what arrived and who stopped by.",
  R(("Home Assistant — Doorbell integrations", "https://www.home-assistant.io/integrations/")), P_APP, P_DS)


# ===========================================================================
# 25.12  Personal Finance & Crypto
# ===========================================================================
FIN_APP = ("Crypto exchange/wallet APIs (Coinbase, on-chain), budgeting exports (YNAB/Firefly III), "
           "and subscription trackers via HEC scripted inputs.")
FIN_DS = ("Crypto prices/holdings (`crypto:price`, `wallet:balance`), exchange transactions "
          "(`coinbase:txn`), budget/transaction exports (`firefly:txn`, `ynab:txn`), bill feeds.")
COINGECKO = ("CoinGecko — API documentation", "https://www.coingecko.com/en/api/documentation")
COINBASE = ("Coinbase — API documentation", "https://docs.cloud.coinbase.com/")
FIREFLY = ("Firefly III — Documentation", "https://docs.firefly-iii.org/")

U("12", "Crypto Portfolio Value Trend", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=crypto:price\n"
  "| stats latest(price_usd) as price by symbol\n"
  "| lookup holdings symbol OUTPUT amount\n"
  "| eval value=round(price*amount,2)\n"
  "| stats sum(value) as portfolio_value\n"
  "| eval portfolio_value=\"$\".tostring(portfolio_value,\"commas\")",
  "Combines live prices with your holdings to show your total crypto portfolio value in one number, without handing your keys to a third-party app.",
  "A self-hosted portfolio view keeps your holdings private and puts the number you care about front and centre, updated as often as you like.",
  "Ingest prices to `index=personal` and keep holdings in a lookup; schedule frequently and trend total value over time.",
  "Single-value portfolio total with a value-over-time trend.",
  "It adds up what your crypto is worth right now, all in one place and without sharing your details with an app.",
  R(COINGECKO), FIN_APP, FIN_DS)

U("12", "Crypto Price Alert (Threshold and Swing)", "low", "intermediate", ["Anomaly", "Business"],
  "index=personal sourcetype=crypto:price\n"
  "| timechart span=1h latest(price_usd) as price by symbol\n"
  "| untable _time symbol price\n"
  "| streamstats current=f last(price) as prev by symbol\n"
  "| eval pct_change=round(100*(price-prev)/prev,2)\n"
  "| where abs(pct_change)>5",
  "Alerts when a coin you follow moves sharply within an hour or crosses a price you set, so you never miss a big swing.",
  "Timely price alerts on your own terms beat doom-scrolling an exchange app all day and help you avoid emotional decisions.",
  "Ingest prices for your watched symbols; schedule hourly and alert on large swings or threshold crossings.",
  "Table of symbols by hourly percentage change with alert markers.",
  "It tells you when a coin you follow jumps or drops a lot, so you do not have to keep checking all day.",
  R(COINGECKO), FIN_APP, FIN_DS)

U("12", "Monthly Spending by Category", "low", "beginner", ["Analytics", "Cost"],
  "index=personal sourcetype=firefly:txn amount<0\n"
  "| eval spend=abs(amount)\n"
  "| bin _time span=1mon\n"
  "| stats sum(spend) as total by category _time\n"
  "| sort _time - total",
  "Summarises where your money went each month by category, turning a wall of transactions into a clear picture of your spending.",
  "Category spending is the foundation of any budget; seeing it monthly reveals the creeping costs that individual purchases hide.",
  "Export budgeting transactions to HEC; schedule monthly and review spending by category.",
  "Stacked column chart of monthly spending by category.",
  "It sorts your spending into groups each month, so you can finally see where the money actually goes.",
  R(FIREFLY), FIN_APP, FIN_DS)

U("12", "Budget Overspend Warning", "medium", "intermediate", ["Cost", "Anomaly"],
  "index=personal sourcetype=firefly:txn amount<0\n"
  "| eval spend=abs(amount), month=strftime(_time,\"%Y-%m\")\n"
  "| stats sum(spend) as spent by category month\n"
  "| lookup budgets category OUTPUT monthly_budget\n"
  "| eval pct_used=round(100*spent/monthly_budget)\n"
  "| where pct_used>90\n"
  "| sort - pct_used",
  "Warns when spending in any category approaches its monthly budget, giving you time to ease off before you blow past it.",
  "A mid-month overspend warning is the whole point of a budget; catching it early is what actually changes behaviour.",
  "Keep budgets in a lookup and export transactions; schedule daily and alert as categories near their limit.",
  "Table of categories by percentage of budget used.",
  "It warns you when you are about to overspend in a budget category, while there is still time to slow down.",
  R(FIREFLY), FIN_APP, FIN_DS)

U("12", "Subscription Creep Detection", "medium", "intermediate", ["Cost", "Inventory"],
  "index=personal sourcetype=firefly:txn\n"
  "| where match(description,\"(?i)subscription|monthly|netflix|spotify|prime|icloud|patreon\")\n"
  "| stats count as charges, avg(abs(amount)) as avg_amount, latest(_time) as last_charge by merchant\n"
  "| where charges>=2\n"
  "| eval annual_cost=round(avg_amount*12,2)\n"
  "| sort - annual_cost",
  "Finds recurring subscription charges and adds up their yearly cost, surfacing the forgotten free trials and creeping renewals draining your account.",
  "Subscription creep is a silent budget killer; listing every recurring charge with its annual cost makes cancellation decisions easy.",
  "Export transactions; schedule monthly and review the recurring-charge list to prune what you no longer use.",
  "Table of subscriptions by estimated annual cost.",
  "It finds all your monthly subscriptions and shows what they cost per year, so you can cancel the ones you forgot about.",
  R(FIREFLY), FIN_APP, FIN_DS)

U("12", "Large or Unusual Transaction Watch", "medium", "advanced", ["Anomaly", "Fraud"],
  "index=personal sourcetype=coinbase:txn\n"
  "| eventstats avg(abs(amount)) as avg_amt, stdev(abs(amount)) as sd_amt by account\n"
  "| eval unusual=if(abs(amount)>avg_amt+3*sd_amt,1,0)\n"
  "| where unusual=1\n"
  "| table _time account merchant amount\n"
  "| sort - _time",
  "Flags transactions far larger than your normal pattern, an early, private tripwire for fraud or a mistaken double-charge.",
  "Banks miss small-scale fraud and are slow to alert; your own anomaly watch catches the odd charge on your terms and timeline.",
  "Export transactions to HEC; schedule daily and alert on statistically unusual amounts for review.",
  "Table of unusual transactions with amounts and merchants.",
  "It spots payments that are much bigger than your usual ones, giving you an early warning of a mistake or fraud.",
  R(COINBASE), FIN_APP, FIN_DS)

U("12", "Net Worth and Savings-Rate Trend", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=firefly:txn\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(amount>0,amount,0))) as income, sum(eval(if(amount<0,abs(amount),0))) as spending by _time\n"
  "| eval saved=income-spending, savings_rate=round(100*saved/income,1)\n"
  "| sort - _time",
  "Calculates your monthly savings rate from income minus spending, the single most powerful number for long-term financial health.",
  "Savings rate, not income, determines financial freedom; trending it monthly keeps the goal that matters most in constant view.",
  "Export income and spending; schedule monthly and trend the savings rate over time.",
  "Line chart of monthly savings rate with an income/spending overlay.",
  "It works out how much of your income you actually saved each month, which is the key to long-term financial health.",
  R(FIREFLY), FIN_APP, FIN_DS)

U("12", "Crypto Gas-Fee and Transaction-Cost Tracker", "low", "advanced", ["Cost", "Analytics"],
  "index=personal sourcetype=wallet:balance event=transaction\n"
  "| stats sum(gas_fee_usd) as total_fees, count as txns, avg(gas_fee_usd) as avg_fee by chain\n"
  "| eval avg_fee=round(avg_fee,2), total_fees=round(total_fees,2)\n"
  "| sort - total_fees",
  "Adds up the network fees you have paid on each blockchain so the real, often surprising, cost of your on-chain activity is clear.",
  "Gas fees quietly erode returns; totalling them per chain reveals whether your trading or minting habit is worth the transaction cost.",
  "Ingest on-chain transaction records with fees; schedule weekly and review total fees per chain.",
  "Bar chart of total network fees paid by chain.",
  "It adds up the little fees you pay for every crypto transaction, which often cost far more than people realise.",
  R(("Etherscan — API documentation", "https://docs.etherscan.io/")), FIN_APP, FIN_DS)


# ===========================================================================
# 25.13  Digital Life & Productivity
# ===========================================================================
DL_APP = ("Screen-time / RescueTime exports, GitHub personal activity, habit/journal trackers, "
          "and calendar feeds via HEC scripted inputs.")
DL_DS = ("RescueTime activity (`rescuetime:activity`), screen-time exports (`screentime:usage`), "
         "GitHub events (`github:personal`), habit-tracker logs (`habit:entry`), calendar exports.")
RESCUETIME = ("RescueTime — API documentation", "https://www.rescuetime.com/apidoc")
GITHUB = ("GitHub — REST API documentation", "https://docs.github.com/en/rest")

U("13", "Focus vs Distraction Time", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=rescuetime:activity\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(productivity>=1,duration_s,0))) as focus_s, sum(eval(if(productivity<0,duration_s,0))) as distract_s by _time\n"
  "| eval focus_h=round(focus_s/3600,1), distract_h=round(distract_s/3600,1)\n"
  "| sort - _time",
  "Splits your computer time into focused and distracting hours each day so you can see your real productivity, not how busy you felt.",
  "Perceived productivity is unreliable; an honest daily focus-versus-distraction split shows what your time actually went to.",
  "Export RescueTime activity to HEC; schedule daily and review the focus/distraction balance.",
  "Stacked column chart of daily focus versus distraction hours.",
  "It shows how much of your day was real focused work versus distractions, which is often eye-opening.",
  R(RESCUETIME), DL_APP, DL_DS)

U("13", "Phone Screen-Time Trend and Goal", "low", "beginner", ["Analytics", "Safety"],
  "index=personal sourcetype=screentime:usage\n"
  "| timechart span=1d sum(minutes) as screen_min\n"
  "| eval hours=round(screen_min/60,1), goal_h=3, over_goal=if(hours>goal_h,1,0)",
  "Trends your daily phone screen time against a personal goal, making a creeping habit visible before it eats your evenings.",
  "Screen-time awareness is the first step to changing it; a trend against a goal is far more motivating than a weekly guilt notification.",
  "Export screen-time data to HEC; schedule daily and nudge yourself on days you exceed your goal.",
  "Line chart of daily phone hours against a goal line.",
  "It tracks how long you spend on your phone each day compared to your goal, so the habit does not creep up on you.",
  R(("Apple — Screen Time", "https://support.apple.com/en-us/HT208982")), DL_APP, DL_DS)

U("13", "App Usage Breakdown", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=screentime:usage\n"
  "| bin _time span=1w\n"
  "| stats sum(minutes) as minutes by app _time\n"
  "| stats avg(minutes) as avg_weekly_min by app\n"
  "| eval avg_weekly_h=round(avg_weekly_min/60,1)\n"
  "| sort - avg_weekly_h\n"
  "| head 15",
  "Ranks which apps eat the most of your time each week, naming the specific culprits behind your screen-time total.",
  "A total is abstract; naming the exact apps stealing your hours is what actually prompts you to delete or limit one.",
  "Export per-app usage; schedule weekly and review the biggest time sinks.",
  "Bar chart of average weekly hours by app.",
  "It shows exactly which apps take up most of your time, so you know which one to cut back on.",
  R(("Android — Digital Wellbeing", "https://wellbeing.google/")), DL_APP, DL_DS)

U("13", "GitHub Contribution Streak", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=github:personal\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(type=\"PushEvent\",1,0))) as commits_days by _time\n"
  "| streamstats current=t sum(eval(if(commits_days>0,1,0))) as streak reset_after=\"(commits_days=0)\"\n"
  "| sort - _time",
  "Recreates your coding contribution streak from GitHub events so you can protect the green squares that keep side projects alive.",
  "A visible streak is a proven motivator for hobby coding; recreating it in your own dashboard keeps momentum without opening the site.",
  "Ingest your GitHub events to HEC; schedule daily and surface your current streak.",
  "Calendar heatmap of daily contributions with the current streak.",
  "It tracks how many days in a row you have worked on your coding projects, which helps keep the habit going.",
  R(GITHUB), DL_APP, DL_DS)

U("13", "Habit Tracker Completion Rate", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=habit:entry\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(completed=\"true\",1,0))) as done, count as scheduled by habit _time\n"
  "| eval completion_pct=round(100*done/scheduled)\n"
  "| stats avg(completion_pct) as avg_completion by habit\n"
  "| sort avg_completion",
  "Calculates how consistently you keep each habit and ranks them so you can double down on what is working and rethink what is not.",
  "Habits succeed or fail on consistency, not intensity; a completion rate per habit shows exactly where to focus your willpower.",
  "Export habit-tracker logs to HEC; schedule weekly and review completion rates across habits.",
  "Bar chart of completion rate by habit.",
  "It shows how well you are sticking to each of your habits, so you can see which ones need more attention.",
  R(("Home Assistant — long-term statistics", "https://www.home-assistant.io/more-info/statistics/")), DL_APP, DL_DS)

U("13", "Calendar Meeting Load and Deep-Work Time", "low", "intermediate", ["Analytics", "Capacity"],
  "index=personal sourcetype=calendar:event\n"
  "| bin _time span=1d\n"
  "| stats sum(duration_min) as meeting_min, count as meetings by _time\n"
  "| eval meeting_h=round(meeting_min/60,1), deep_work_h=round((8-meeting_h),1)\n"
  "| sort - _time",
  "Adds up how many hours of your day meetings consume and what is left for focused work, revealing the days with no room to think.",
  "Meeting overload is the enemy of deep work; quantifying the split makes the case to protect focus blocks on your calendar.",
  "Export calendar events to HEC; schedule daily and review meeting load versus available focus time.",
  "Stacked column chart of daily meeting hours versus deep-work hours.",
  "It adds up how much of your day is meetings versus time to actually get work done, exposing the overloaded days.",
  R(("Google Calendar — API", "https://developers.google.com/calendar/api")), DL_APP, DL_DS)

U("13", "Password Manager Weak and Reused Credentials", "medium", "intermediate", ["Security", "Risk"],
  "index=personal sourcetype=passwordmanager:audit\n"
  "| stats sum(eval(strength=\"weak\")) as weak, sum(eval(reused=\"true\")) as reused, sum(eval(breached=\"true\")) as breached\n"
  "| eval total_issues=weak+reused+breached",
  "Summarises the weak, reused, and breached passwords flagged by your password manager so you can tackle your worst security debt first.",
  "Reused and breached passwords are the top cause of account takeovers; a running count turns a scary audit into a tidy to-do list.",
  "Export your password manager's security-audit report to HEC; schedule weekly and drive the issue count toward zero.",
  "Single-value panels for weak, reused, and breached credential counts.",
  "It counts how many of your passwords are weak, reused, or leaked, so you can fix the most dangerous ones first.",
  R(("Have I Been Pwned — API", "https://haveibeenpwned.com/API/v3")), DL_APP, DL_DS, pillar="Security")

U("13", "Personal Email Newsletter and Inbox Load", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=email:metadata\n"
  "| bin _time span=1w\n"
  "| stats count as received, sum(eval(if(category=\"newsletter\" OR list_unsubscribe=\"true\",1,0))) as newsletters by _time\n"
  "| eval newsletter_pct=round(100*newsletters/received)\n"
  "| sort - _time",
  "Trends how much email you receive each week and what share is newsletters, giving you the ammunition for a satisfying unsubscribe session.",
  "Inbox overload is mostly newsletters you forgot you signed up for; quantifying the share motivates a cleanup that actually sticks.",
  "Ingest email metadata (not content) to HEC; schedule weekly and target the newsletter share for pruning.",
  "Column chart of weekly email received with the newsletter share.",
  "It shows how much email you get each week and how much is newsletters, so you know it is time to unsubscribe.",
  R(("RFC 8058 — One-Click Unsubscribe", "https://www.rfc-editor.org/rfc/rfc8058")), DL_APP, DL_DS)


# ===========================================================================
# 25.14  Travel, Commute & Flight-Spotting
# ===========================================================================
TR_APP = ("Home ADS-B receiver (dump1090 / readsb / tar1090 JSON feed), personal flight "
          "logbook exports, commute/transit APIs, and phone geofence webhooks via Splunk HEC.")
TR_DS = ("ADS-B aircraft snapshots (`adsb:aircraft`), personal flight logbook (`flight:log`), "
         "commute trips (`commute:trip`), transit arrivals (`transit:arrival`), geofence "
         "events (`geofence:event`), travel documents (`travel:document`), fare quotes (`airprice:quote`).")
ADSB = ("ADS-B — readsb / tar1090 JSON output", "https://github.com/wiedehopf/readsb")
OSKY = ("OpenSky Network — REST API", "https://opensky-network.org/apidoc/rest.html")
GTFS = ("GTFS Realtime — reference", "https://gtfs.org/realtime/reference/")

U("14", "Overhead Aircraft Log and Rare-Type Spotting", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=adsb:aircraft\n"
  "| stats count as pings, min(altitude_ft) as low_alt, values(type) as types by hex callsign\n"
  "| eventstats count as fleet_seen by type\n"
  "| eval rarity=if(fleet_seen<=3,\"rare\",\"common\")\n"
  "| sort - pings",
  "Rolls up every aircraft your home ADS-B receiver has heard, tagging the types you rarely see so an unusual visitor stands out.",
  "Turns a raw firehose of ADS-B pings into a browsable log where a once-a-year aircraft type is flagged instead of lost in the noise.",
  "Point Splunk at your dump1090/readsb JSON feed into `index=personal`; schedule daily and alert when a `rare` type appears overhead.",
  "Table of aircraft by callsign with a rarity tag and lowest altitude.",
  "It keeps a list of every plane your little radio receiver hears and points out the unusual ones you almost never see.",
  R(ADSB, OSKY), TR_APP, TR_DS)

U("14", "Military and Emergency Squawk Alert", "medium", "intermediate", ["Safety", "Anomaly"],
  "index=personal sourcetype=adsb:aircraft (squawk=7500 OR squawk=7600 OR squawk=7700 OR is_military=\"true\")\n"
  "| eval condition=case(squawk=\"7500\",\"hijack\",squawk=\"7600\",\"radio failure\",squawk=\"7700\",\"general emergency\",is_military=\"true\",\"military\",1=1,\"other\")\n"
  "| stats count by condition callsign\n"
  "| sort - count",
  "Watches the ADS-B stream for emergency transponder codes and military aircraft, surfacing the handful of flights that are genuinely notable.",
  "Emergency squawks and military traffic are needles in a huge haystack; a standing alert catches them the moment they appear in your sky.",
  "Ingest ADS-B with squawk and category fields; schedule every few minutes and push a notification when an emergency code is seen.",
  "Table of flagged flights grouped by emergency or military condition.",
  "It listens for the special codes planes use in emergencies and highlights military flights, so the rare interesting ones do not slip past.",
  R(ADSB, OSKY), TR_APP, TR_DS)

U("14", "Closest-Approach Aircraft of the Day", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=adsb:aircraft\n"
  "| stats min(distance_km) as closest_km, min(altitude_ft) as low_alt by callsign type\n"
  "| sort closest_km\n"
  "| head 10",
  "Finds which aircraft passed nearest to your receiver each day, ranked by distance, for the plane-spotters among us.",
  "A daily closest-approach leaderboard makes casual plane-spotting a game and helps you time a look outside for a low pass.",
  "Ingest ADS-B position data with a computed distance field; schedule daily and review the ten nearest passes.",
  "Ranked table of the ten closest aircraft with distance and altitude.",
  "It shows which planes flew closest to your house today, so you know when to look up for a good view.",
  R(ADSB), TR_APP, TR_DS)

U("14", "ADS-B Receiver Coverage and Range", "low", "intermediate", ["Performance"],
  "index=personal sourcetype=adsb:aircraft\n"
  "| bin _time span=1d\n"
  "| stats max(distance_km) as max_range, dc(hex) as aircraft, count as pings by _time\n"
  "| sort - _time",
  "Trends the maximum range and aircraft count your ADS-B setup achieves each day so you can tell whether an antenna tweak actually helped.",
  "Coverage is the key quality metric for a receiver; trending daily max range turns antenna experiments into measurable before-and-after results.",
  "Ingest ADS-B pings with distance; schedule daily and compare max range across antenna or placement changes.",
  "Line chart of daily maximum range with an aircraft-count overlay.",
  "It measures how far away your radio can pick up planes each day, so you can see if moving the antenna made it better.",
  R(ADSB), TR_APP, TR_DS)

U("14", "Personal Flight Logbook Miles and Countries", "low", "beginner", ["Business", "Analytics"],
  "index=personal sourcetype=flight:log\n"
  "| stats sum(distance_km) as total_km, count as flights, dc(arr_country) as countries\n"
  "| eval total_miles=round(total_km*0.621,0)",
  "Adds up every flight you have taken into total miles, flights, and distinct countries visited for a personal travel map.",
  "A lifetime flight tally turns scattered boarding passes into a satisfying record of where you have been and how far you have flown.",
  "Load your flight history (from email or a logbook export) into `index=personal`; schedule monthly and watch the totals climb.",
  "Single-value tiles for total miles, flights, and countries visited.",
  "It adds up all the flights you have ever taken to show how far you have flown and how many countries you have visited.",
  R(OSKY), TR_APP, TR_DS)

U("14", "Airline On-Time Record for My Flights", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=flight:log\n"
  "| eval delay_min=round((actual_dep_epoch-sched_dep_epoch)/60,0)\n"
  "| stats avg(delay_min) as avg_delay, sum(eval(if(delay_min>15,1,0))) as late, count as flights by airline\n"
  "| eval on_time_pct=round(100*(flights-late)/flights,1)\n"
  "| sort on_time_pct",
  "Calculates the on-time percentage of the airlines you actually fly, not the industry averages that never match your luck.",
  "Your personal on-time record beats any published statistic when choosing who to book next, especially for tight connections.",
  "Record scheduled versus actual departure per flight; schedule monthly and rank the airlines you use by on-time rate.",
  "Bar chart of on-time percentage by airline with average delay.",
  "It works out how often the airlines you use actually leave on time, based on your own flights rather than general figures.",
  R(OSKY), TR_APP, TR_DS)

U("14", "Commute Time vs Baseline Anomaly", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=commute:trip\n"
  "| eval dow=strftime(_time,\"%A\")\n"
  "| eventstats avg(duration_min) as usual, stdev(duration_min) as sd by dow route\n"
  "| eval worse_than_usual=if(duration_min>usual+2*sd,1,0)\n"
  "| where worse_than_usual=1\n"
  "| table _time route duration_min usual",
  "Learns your normal commute time for each route and day of week, then flags the trips that were unusually slow.",
  "A same-day-of-week baseline separates a genuinely bad traffic day from the ordinary Monday crawl, so alerts mean something.",
  "Log each commute's duration and route to `index=personal`; schedule after your typical commute window and notify on anomalies.",
  "Table of anomalous commutes with actual versus usual duration.",
  "It learns how long your commute normally takes and tells you when a trip was much slower than usual.",
  R(GTFS), TR_APP, TR_DS)

U("14", "Public Transit Delay Tracker", "low", "beginner", ["Availability"],
  "index=personal sourcetype=transit:arrival\n"
  "| eval delay_min=round((actual_epoch-sched_epoch)/60,0)\n"
  "| stats avg(delay_min) as avg_delay, max(delay_min) as worst, count as trips by line\n"
  "| sort - avg_delay",
  "Measures how late your bus or train lines run on average so you can plan around the chronically unreliable ones.",
  "Knowing which line is habitually late lets you leave earlier for the one that matters and stop trusting the timetable blindly.",
  "Ingest realtime transit arrivals against schedule; schedule daily and review average and worst-case delay per line.",
  "Bar chart of average delay by transit line with worst-case markers.",
  "It tracks how late your buses and trains usually are, so you know which ones to give extra time.",
  R(GTFS), TR_APP, TR_DS)

U("14", "Geofence Arrival and Departure Log", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=geofence:event\n"
  "| stats earliest(_time) as first_seen, latest(_time) as last_seen, count as crossings by place event_type\n"
  "| eval first_seen=strftime(first_seen,\"%F %T\"), last_seen=strftime(last_seen,\"%F %T\")\n"
  "| sort - crossings",
  "Keeps a tidy log of when you arrive at and leave your regular places, the raw material for smarter home automations.",
  "An arrival and departure history reveals your real routine and powers automations that trigger on leaving work or reaching home.",
  "Send phone geofence webhooks to `index=personal`; schedule daily and use the log to tune presence-based automations.",
  "Table of places with arrival and departure counts and timestamps.",
  "It notes when you come and go from the places you visit often, which is handy for making your home react automatically.",
  R(("Home Assistant — Geofencing / zones", "https://www.home-assistant.io/integrations/zone/")), TR_APP, TR_DS)

U("14", "Passport and Visa Expiry Countdown", "medium", "beginner", ["Risk"],
  "index=personal sourcetype=travel:document\n"
  "| stats latest(expiry_epoch) as expiry by holder doc_type\n"
  "| eval days_left=round((expiry_epoch-now())/86400,0)\n"
  "| where days_left<270\n"
  "| sort days_left",
  "Counts down the days until each passport, visa, or travel-authorisation expires and warns you while there is still time to renew.",
  "Many countries refuse entry within six months of passport expiry; an early countdown avoids a cancelled trip and a panic renewal.",
  "Store document expiry dates in `index=personal`; schedule weekly and alert when any document drops below your renewal threshold.",
  "Table of documents sorted by days remaining with a red warning band.",
  "It counts down to when your passport or visa runs out and warns you early, so a trip is never ruined by an expired document.",
  R(("ICAO — Machine Readable Travel Documents", "https://www.icao.int/publications/pages/publication.aspx?docnum=9303")), TR_APP, TR_DS)

U("14", "Airfare Price-Drop Watch", "low", "intermediate", ["Cost"],
  "index=personal sourcetype=airprice:quote\n"
  "| stats latest(price) as current, min(price) as lowest, avg(price) as typical by route\n"
  "| eval drop_pct=round(100*(typical-current)/typical,1)\n"
  "| where current<=lowest OR drop_pct>=15\n"
  "| sort - drop_pct",
  "Tracks fare quotes for routes you care about and flags a genuine price drop against the recent typical fare.",
  "Fares swing constantly; comparing the current quote to your own recent history catches a real deal instead of marketing hype.",
  "Poll a fare source into `index=personal` on a schedule; alert when the current price hits a new low or falls well below typical.",
  "Table of watched routes with current, lowest, and percent-below-typical.",
  "It keeps an eye on flight prices for the trips you want and tells you when they drop enough to be worth booking.",
  R(OSKY), TR_APP, TR_DS)

U("14", "Monthly Travel Spend and Distance Rollup", "low", "beginner", ["Cost", "Business"],
  "index=personal (sourcetype=commute:trip OR sourcetype=flight:log)\n"
  "| bin _time span=1mon\n"
  "| stats sum(cost) as spend, sum(distance_km) as km, count as trips by _time\n"
  "| eval cost_per_km=round(spend/km,2)\n"
  "| sort - _time",
  "Combines your commutes and flights into a monthly view of what travel costs you and how far it takes you.",
  "Seeing travel spend and distance together each month exposes an expensive habit and makes the cost-per-kilometre trade-off concrete.",
  "Ingest trips and flights with cost and distance; schedule monthly and review spend, distance, and cost per kilometre.",
  "Column chart of monthly travel spend with a distance overlay.",
  "It adds up what you spend getting around each month and how far you travel, so the real cost of moving about is clear.",
  R(GTFS), TR_APP, TR_DS)


# ===========================================================================
# 25.15  Kitchen, Cooking & Fermentation
# ===========================================================================
KI_APP = ("ESP32/ESPHome kitchen sensors (sourdough rise, BBQ/sous-vide probes, fridge/freezer "
          "temperature), espresso-shot logs, and pantry inventory via MQTT and Splunk HEC.")
KI_DS = ("Sourdough monitor (`sourdough:reading`), BBQ/sous-vide probes (`bbq:probe`), fridge/"
         "freezer/oven temperature (`kitchen:appliance`), espresso shots (`espresso:shot`), "
         "pantry inventory (`pantry:item`), kombucha brew (`kombucha:reading`).")
ESPHOME = ("ESPHome — sensor components", "https://esphome.io/index.html")
GRAF_SD = ("Grafana Labs — monitor a sourdough starter", "https://grafana.com/blog/how-to-monitor-a-sourdough-starter-with-grafana/")

U("15", "Sourdough Starter Peak-Rise Bake-Now Alert", "low", "intermediate", ["Analytics", "Anomaly"],
  "index=personal sourcetype=sourdough:reading\n"
  "| streamstats current=t max(rise_pct) as peak_so_far\n"
  "| eval at_peak=if(rise_pct>=peak_so_far AND rise_pct>=80,1,0)\n"
  "| where at_peak=1\n"
  "| table _time rise_pct temp_c",
  "Watches your starter climb after feeding and pings you when it hits its peak rise, the perfect moment to bake.",
  "A starter at peak makes the best loaf; catching that window automatically beats guessing and staring at the jar.",
  "Feed sourdough-monitor readings (a distance sensor over the jar) into `index=personal`; alert the moment rise reaches its peak.",
  "Line chart of rise percentage over time with the peak marked.",
  "It watches your sourdough grow after you feed it and tells you the exact best moment to start baking.",
  R(GRAF_SD, ESPHOME), KI_APP, KI_DS)

U("15", "Sourdough Fermentation Environment Trend", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=sourdough:reading\n"
  "| timechart span=30m avg(temp_c) as temp, avg(humidity_pct) as humidity\n"
  "| eval warm_enough=if(temp>=24,1,0)",
  "Trends the temperature and humidity around your starter so you can explain why it rose fast one day and sluggishly the next.",
  "Fermentation speed is driven by warmth; trending the jar's environment turns an inconsistent starter into a predictable one.",
  "Ingest temperature and humidity from the sourdough sensor; review the environment trend alongside rise behaviour.",
  "Dual-axis line chart of jar temperature and humidity over time.",
  "It records how warm and humid it is around your starter, which explains why it grows quickly some days and slowly on others.",
  R(GRAF_SD, ESPHOME), KI_APP, KI_DS)

U("15", "BBQ Smoker Temperature Stall Detection", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=bbq:probe probe=meat\n"
  "| timechart span=10m avg(temp_c) as meat_temp\n"
  "| streamstats current=f last(meat_temp) as prev\n"
  "| eval climb=meat_temp-prev, stalled=if(climb<0.3 AND meat_temp>63 AND meat_temp<74,1,0)",
  "Detects the notorious brisket stall, when the meat temperature plateaus for hours, so you know whether to wait it out or wrap.",
  "The stall panics first-time smokers into ruining dinner; spotting it for what it is turns a scary plateau into a planned step.",
  "Feed a meat-probe into `index=personal`; run during a cook and flag when the temperature climb flattens in the stall zone.",
  "Line chart of meat temperature with the stall zone shaded.",
  "It spots when the meat's temperature stops rising for a while during a long cook, which is normal and just means keep going or wrap it.",
  R(ESPHOME, ("Inkbird — cooking thermometers", "https://www.inkbird.com/")), KI_APP, KI_DS)

U("15", "Sous-Vide Core-Temperature and Doneness Timer", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=bbq:probe probe=water\n"
  "| stats latest(temp_c) as bath_temp, earliest(_time) as start\n"
  "| eval at_temp_since=if(bath_temp>=target_c,round((now()-start)/60,0),0)\n"
  "| eval status=if(bath_temp>=target_c,\"holding at temp\",\"heating\")",
  "Confirms your sous-vide bath has reached and held its target temperature, and for how long, so food is both safe and perfect.",
  "Sous-vide safety depends on time at temperature; tracking how long the bath has held target removes the guesswork from doneness.",
  "Ingest the water-bath probe; run during a cook and surface bath temperature and time-at-target.",
  "Single-value panels for bath temperature, status, and minutes at target.",
  "It checks that your sous-vide water has reached the right temperature and how long it has stayed there, so the food is safe and cooked just right.",
  R(ESPHOME), KI_APP, KI_DS)

U("15", "Fridge and Freezer Food-Safety Excursion Alert", "medium", "beginner", ["Safety"],
  "index=personal sourcetype=kitchen:appliance (appliance=fridge OR appliance=freezer)\n"
  "| eval limit=if(appliance=\"freezer\",-15,5)\n"
  "| eval breach=if(temp_c>limit,1,0)\n"
  "| stats sum(breach) as breach_readings, max(temp_c) as warmest by appliance\n"
  "| where breach_readings>0",
  "Alerts when your fridge or freezer drifts above a safe temperature, the classic sign of a left-open door or failing seal.",
  "A warm fridge spoils food and risks illness; an instant excursion alert saves a freezer of food when a door is left ajar.",
  "Put a temperature sensor in each appliance feeding `index=personal`; alert whenever a reading crosses the safe limit.",
  "Time chart of appliance temperature with a safe-limit threshold line.",
  "It warns you if your fridge or freezer gets too warm, which usually means a door was left open or something is breaking.",
  R(ESPHOME), KI_APP, KI_DS)

U("15", "Oven Preheat Readiness Confirmation", "low", "beginner", ["Availability"],
  "index=personal sourcetype=kitchen:appliance appliance=oven\n"
  "| stats latest(temp_c) as oven_temp, latest(target_c) as target\n"
  "| eval ready=if(oven_temp>=target,\"ready\",\"still heating\"), gap=round(target-oven_temp,0)",
  "Tells you when the oven has genuinely reached the set temperature, which is often several minutes after the beep.",
  "Ovens beep early and bake unevenly before they are truly hot; confirming real readiness improves everything you cook.",
  "Ingest an oven temperature sensor; surface a simple ready or still-heating state against the target.",
  "Single-value readiness indicator with the temperature gap to target.",
  "It tells you when the oven is actually hot enough, which is usually a bit after it beeps, so your food cooks properly.",
  R(ESPHOME), KI_APP, KI_DS)

U("15", "Espresso Shot Extraction Consistency", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=espresso:shot\n"
  "| eval ratio=round(yield_g/dose_g,2)\n"
  "| stats avg(shot_time_s) as avg_time, stdev(shot_time_s) as time_sd, avg(ratio) as avg_ratio by bean\n"
  "| eval consistency=if(time_sd<3,\"dialed in\",\"variable\")\n"
  "| sort - avg_ratio",
  "Tracks your espresso shot time and brew ratio per bean so you can tell when a coffee is dialed in versus all over the place.",
  "Great espresso is repeatable espresso; measuring shot-time variation shows whether your grind is dialed in or still guesswork.",
  "Log each shot's dose, yield, and time to `index=personal`; review consistency per bean to fine-tune the grinder.",
  "Table of beans with average shot time, ratio, and a consistency label.",
  "It records how your espresso shots turn out so you can see when a coffee is perfectly tuned and when it needs adjusting.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), KI_APP, KI_DS)

U("15", "Daily Caffeine Intake vs Limit", "low", "beginner", ["Safety", "Analytics"],
  "index=personal sourcetype=espresso:shot\n"
  "| bin _time span=1d\n"
  "| stats sum(caffeine_mg) as caffeine, count as cups by _time\n"
  "| eval limit=400, over_limit=if(caffeine>limit,1,0)\n"
  "| sort - _time",
  "Adds up the caffeine in your day's coffees and compares it to a sensible daily limit before the jitters set in.",
  "Caffeine creeps up across a day of small cups; a running daily total keeps you under the limit that protects your sleep.",
  "Log each drink's caffeine estimate; schedule through the day and warn when the running total nears the limit.",
  "Column chart of daily caffeine against a limit line with cup count.",
  "It adds up how much caffeine you have had today compared to a healthy limit, so you know when to switch to decaf.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), KI_APP, KI_DS)

U("15", "Pantry Low-Stock and Reorder Forecast", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=pantry:item\n"
  "| stats latest(quantity) as on_hand, avg(weekly_use) as usage by item\n"
  "| eval weeks_left=round(on_hand/usage,1)\n"
  "| where weeks_left<2\n"
  "| sort weeks_left",
  "Estimates how many weeks of each staple you have left from your usage rate so you reorder before running out.",
  "Running out of a staple mid-recipe is a small daily annoyance a usage-based forecast quietly eliminates.",
  "Track pantry quantities and typical usage in `index=personal`; schedule weekly and flag items about to run out.",
  "Table of pantry items sorted by weeks of stock remaining.",
  "It works out how long your kitchen staples will last and reminds you to buy more before you run out.",
  R(("Home Assistant — shopping list", "https://www.home-assistant.io/integrations/shopping_list/")), KI_APP, KI_DS)

U("15", "Pantry Expiry and Food-Waste Reduction", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=pantry:item\n"
  "| eval days_to_expiry=round((expiry_epoch-now())/86400,0)\n"
  "| where days_to_expiry<7 AND quantity>0\n"
  "| sort days_to_expiry\n"
  "| table item days_to_expiry quantity",
  "Lists the food nearing its use-by date so you can cook it first and throw less away.",
  "Most household food waste is stuff forgotten at the back of a shelf; an eat-me-first list turns waste into dinner.",
  "Record expiry dates with pantry items; schedule daily and surface everything due to expire this week.",
  "Table of soon-to-expire items sorted by days remaining.",
  "It shows which food is about to go off so you can use it up instead of binning it.",
  R(("Home Assistant — shopping list", "https://www.home-assistant.io/integrations/shopping_list/")), KI_APP, KI_DS)

U("15", "Kombucha Brew Batch Progress", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=kombucha:reading\n"
  "| stats earliest(_time) as start, latest(ph) as ph, avg(temp_c) as temp by batch\n"
  "| eval days_fermenting=round((now()-start)/86400,1)\n"
  "| eval stage=case(ph>3.5,\"early\",ph>2.8,\"ready soon\",1=1,\"ready\")\n"
  "| sort - days_fermenting",
  "Follows each kombucha batch by pH and temperature so you know when a brew has fermented to the tartness you like.",
  "Kombucha readiness is a pH question, not a calendar one; tracking it per batch means every brew tastes the way you want.",
  "Ingest pH and temperature per batch; schedule daily and watch each batch progress toward ready.",
  "Table of batches with days fermenting, pH, and a stage label.",
  "It follows each batch of kombucha as it brews and tells you when it is ready to drink.",
  R(ESPHOME), KI_APP, KI_DS)

U("15", "Coffee-Bean Freshness Countdown", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=pantry:item category=coffee\n"
  "| eval days_since_roast=round((now()-roast_epoch)/86400,0)\n"
  "| eval freshness=case(days_since_roast<7,\"resting\",days_since_roast<21,\"peak\",days_since_roast<35,\"fading\",1=1,\"stale\")\n"
  "| table item days_since_roast freshness quantity",
  "Counts the days since each bag of coffee was roasted and rates its freshness so you brew beans at their best.",
  "Coffee peaks a couple of weeks after roasting and fades fast after a month; a freshness clock makes sure good beans are not wasted.",
  "Record roast dates with your coffee inventory; schedule daily and rate each bag from resting through stale.",
  "Table of coffee bags with days since roast and a freshness rating.",
  "It counts how long ago your coffee was roasted and tells you when the beans are at their tastiest.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), KI_APP, KI_DS)


# ===========================================================================
# 25.16  Homebrewing, Beer & Wine
# ===========================================================================
BR_APP = ("Fermentation sensors (Tilt/iSpindel hydrometer, temperature), kegerator flow meters "
          "and scales, and wine-cellar climate sensors via MQTT and Splunk HEC.")
BR_DS = ("Fermentation gravity/temperature (`brew:fermentation`), kegerator pours (`kegerator:pour`), "
         "wine-cellar climate (`winecellar:reading`).")
ISPINDEL = ("iSpindel — DIY digital hydrometer", "https://www.ispindel.de/docs/README_en.html")

U("16", "Fermentation Gravity and Attenuation Curve", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=brew:fermentation\n"
  "| timechart span=6h avg(gravity) as sg\n"
  "| eventstats first(sg) as og\n"
  "| eval attenuation_pct=round(100*(og-sg)/(og-1),1)",
  "Charts the specific gravity of a fermenting batch and derives how far it has attenuated toward finished beer.",
  "The gravity curve is the heartbeat of a fermentation; watching attenuation tells you how the yeast is really doing, day by day.",
  "Feed a floating hydrometer (Tilt/iSpindel) into `index=personal`; review the gravity drop and attenuation across the ferment.",
  "Line chart of specific gravity over time with attenuation percentage.",
  "It follows how your beer is fermenting by tracking its density, showing how far along the yeast has turned sugar into alcohol.",
  R(ISPINDEL, ESPHOME), BR_APP, BR_DS)

U("16", "Fermentation Temperature Stability Alert", "medium", "beginner", ["Anomaly"],
  "index=personal sourcetype=brew:fermentation\n"
  "| eval in_band=if(temp_c>=target_c-1 AND temp_c<=target_c+1,1,0)\n"
  "| stats latest(temp_c) as temp, latest(target_c) as target, sum(eval(in_band=0)) as out_of_band\n"
  "| eval drift=round(temp-target,1)",
  "Warns when a fermenting batch drifts outside its target temperature band, where off-flavours are born.",
  "Yeast produces off-flavours when it gets too warm or cold; a tight temperature alert protects the taste of the whole batch.",
  "Ingest fermentation-chamber temperature; alert whenever the reading leaves the target band around the set point.",
  "Time chart of fermentation temperature with a target band overlay.",
  "It warns you if your fermenting beer gets too warm or too cold, which can spoil the flavour.",
  R(ISPINDEL, ESPHOME), BR_APP, BR_DS)

U("16", "Fermentation Complete Detection", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=brew:fermentation\n"
  "| timechart span=1d avg(gravity) as sg\n"
  "| streamstats current=f last(sg) as prev_sg\n"
  "| eval change=abs(sg-prev_sg), done=if(change<0.001,1,0)",
  "Detects when specific gravity stops falling for consecutive days, the signal that fermentation has finished and the beer is ready to package.",
  "A stable gravity for several days is the only reliable sign fermentation is done; automating it prevents bottling too early and making bombs.",
  "Ingest daily gravity; flag when the day-over-day change stays near zero, indicating a finished ferment.",
  "Line chart of daily gravity flattening to a stable finish.",
  "It notices when your beer has stopped fermenting so you know it is safe to bottle without risk of exploding bottles.",
  R(ISPINDEL), BR_APP, BR_DS)

U("16", "Kegerator Pour Count and Keg-Level Forecast", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=kegerator:pour\n"
  "| stats sum(volume_ml) as poured_ml, count as pours by keg\n"
  "| eval keg_ml=19000, remaining_ml=keg_ml-poured_ml, pints_left=round(remaining_ml/473,1)\n"
  "| sort remaining_ml",
  "Counts pours from each keg and estimates the pints remaining so a keg never runs dry mid-party.",
  "Nothing kills a gathering like a keg blowing unexpectedly; a running pints-left estimate tells you when to chill the next one.",
  "Feed a flow meter on the beer line into `index=personal`; track cumulative pours and estimate remaining volume per keg.",
  "Gauge of estimated pints remaining per keg.",
  "It counts how much beer has been poured and estimates how many pints are left in the keg.",
  R(ESPHOME), BR_APP, BR_DS)

U("16", "Kegerator Temperature and CO2 Health", "low", "beginner", ["Availability"],
  "index=personal sourcetype=kegerator:pour\n"
  "| stats latest(fridge_temp_c) as temp, latest(co2_psi) as co2\n"
  "| eval temp_ok=if(temp>=2 AND temp<=5,\"good\",\"check\"), co2_ok=if(co2>=8 AND co2<=14,\"good\",\"check\")",
  "Checks that your kegerator is holding serving temperature and carbonation pressure, the two things that ruin a pint when they drift.",
  "Warm beer and flat or over-carbonated pours both come from a neglected kegerator; monitoring temperature and pressure keeps every pour right.",
  "Ingest fridge temperature and regulator pressure; surface simple good-or-check states for each.",
  "Single-value panels for serving temperature and CO2 pressure.",
  "It checks that your beer fridge is cold enough and the gas pressure is right, so every pint tastes good.",
  R(ESPHOME), BR_APP, BR_DS)

U("16", "Beer Cost-Per-Pint vs Store-Bought", "low", "beginner", ["Cost"],
  "index=personal sourcetype=kegerator:pour\n"
  "| stats sum(volume_ml) as poured_ml, sum(batch_cost) as cost by batch\n"
  "| eval pints=poured_ml/473, cost_per_pint=round(cost/pints,2)\n"
  "| sort cost_per_pint",
  "Works out what each homebrewed pint actually costs once ingredients are spread across the batch, versus buying it.",
  "Homebrew feels cheap until you count the ingredients; a real cost-per-pint tells you whether the hobby also saves money.",
  "Record batch costs and pour volumes; schedule per batch and compare cost per pint to shop prices.",
  "Bar chart of cost per pint by batch with a store-price reference.",
  "It works out how much each homemade pint really costs compared to buying beer from the shop.",
  R(ESPHOME), BR_APP, BR_DS)

U("16", "Wine Cellar Temperature and Humidity Stability", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=winecellar:reading\n"
  "| timechart span=1h avg(temp_c) as temp, avg(humidity_pct) as humidity\n"
  "| eval temp_ok=if(temp>=11 AND temp<=15,1,0)",
  "Trends your wine storage temperature and humidity to prove your bottles are ageing in stable, cellar-like conditions.",
  "Wine is ruined slowly by temperature swings; a steady-conditions record protects a collection you cannot taste-test until it is too late.",
  "Ingest cellar climate sensors; review temperature and humidity stability over time.",
  "Dual-axis line chart of cellar temperature and humidity.",
  "It keeps track of how steady the temperature and humidity are where you store your wine, protecting the bottles as they age.",
  R(ESPHOME), BR_APP, BR_DS)

U("16", "Wine Cellar Inventory and Drink-By Window", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=winecellar:reading event=inventory\n"
  "| stats latest(bottles) as bottles, latest(drink_by_year) as drink_by by wine\n"
  "| eval years_left=drink_by-strftime(now(),\"%Y\")\n"
  "| sort years_left\n"
  "| head 20",
  "Lists your cellared wines by how many years remain in their ideal drinking window so none is forgotten past its prime.",
  "A collection is wasted if bottles slip past their peak unnoticed; a drink-by ranking makes sure the right bottle is opened in time.",
  "Record bottle counts and drinking windows; schedule monthly and surface wines nearing the end of their window.",
  "Table of wines sorted by years left in the drinking window.",
  "It lists your wine and how long each bottle should be kept, so you drink them at their best instead of too late.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), BR_APP, BR_DS)

U("16", "Batch Pipeline and Brew-Day Cadence", "low", "beginner", ["Business"],
  "index=personal sourcetype=brew:fermentation\n"
  "| bin _time span=1mon\n"
  "| stats dc(batch) as batches by _time\n"
  "| sort - _time",
  "Counts how many batches you start each month, revealing the rhythm of your brewing hobby over the year.",
  "Seeing your brew-day cadence shows whether the hobby is thriving or stalled, and helps plan ingredient buying ahead.",
  "Ingest fermentation records tagged by batch; schedule monthly and count distinct batches started.",
  "Column chart of batches started per month.",
  "It counts how often you brew each month, showing whether your hobby is busy or has gone quiet.",
  R(ISPINDEL), BR_APP, BR_DS)

U("16", "Peak-Fermentation Activity Ranking", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=brew:fermentation\n"
  "| streamstats current=f last(gravity) as prev by batch\n"
  "| eval drop=prev-gravity\n"
  "| stats max(drop) as peak_drop, avg(temp_c) as temp by batch\n"
  "| sort - peak_drop",
  "Ranks your batches by their most vigorous fermentation day, a fun way to compare how lively different yeasts and recipes were.",
  "Comparing peak activity across batches teaches you which yeast and temperature combinations ferment hardest for next time.",
  "Ingest gravity per batch; compute the biggest daily drop and rank batches by peak activity.",
  "Bar chart of peak daily gravity drop by batch.",
  "It shows which of your beer batches fermented most vigorously, which is a fun way to compare recipes.",
  R(ISPINDEL), BR_APP, BR_DS)


# ===========================================================================
# 25.17  Making, 3D Printing & Workshop
# ===========================================================================
MK_APP = ("OctoPrint / Klipper (Moonraker) print servers, printer firmware telemetry, filament "
          "spool tracking, CNC/laser job logs, and workshop air/tool sensors via HEC and MQTT.")
MK_DS = ("Print jobs (`octoprint:job`), printer firmware telemetry (`printer:telemetry`), filament "
         "spools (`filament:spool`), CNC/laser jobs (`cnc:job`), workshop air (`workshop:air`), "
         "cordless tool batteries (`tool:battery`).")
OCTO = ("OctoPrint — REST API", "https://docs.octoprint.org/en/master/api/index.html")
MOON = ("Klipper — Moonraker API", "https://moonraker.readthedocs.io/en/latest/web_api/")

U("17", "3D Print Job Success Rate by Printer", "low", "beginner", ["Reliability"],
  "index=personal sourcetype=octoprint:job\n"
  "| stats sum(eval(if(result=\"success\",1,0))) as ok, count as jobs by printer\n"
  "| eval success_pct=round(100*ok/jobs,1)\n"
  "| sort success_pct",
  "Calculates the success rate of each 3D printer so you can tell which machine is reliable and which needs attention.",
  "A printer's success rate is the truest measure of its health; comparing machines shows where a tune-up or upgrade pays off.",
  "Ingest print-job outcomes from OctoPrint/Moonraker; schedule weekly and rank printers by success rate.",
  "Bar chart of print success rate by printer.",
  "It works out how often each 3D printer finishes a print successfully, so you know which one to trust.",
  R(OCTO, MOON), MK_APP, MK_DS)

U("17", "Print Failure and Reason Breakdown", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=octoprint:job result=failed\n"
  "| stats count as failures by reason printer\n"
  "| sort - failures",
  "Groups your failed prints by cause so you can fix the one problem behind most of your wasted filament.",
  "Failures cluster around a few root causes; naming them turns random frustration into a short, actionable fix list.",
  "Tag failed jobs with a reason; schedule weekly and review the leading failure causes per printer.",
  "Pie chart of print failures by reason.",
  "It sorts your failed prints by what went wrong, so you can fix the most common problem first.",
  R(OCTO), MK_APP, MK_DS)

U("17", "Long Print Progress and ETA", "low", "beginner", ["Availability"],
  "index=personal sourcetype=octoprint:job state=printing\n"
  "| stats latest(progress_pct) as progress, latest(eta_epoch) as eta by printer file\n"
  "| eval finishes=strftime(eta,\"%F %T\"), remaining_min=round((eta-now())/60,0)",
  "Shows the live progress and estimated finish time of running prints so you know when to check on a multi-hour job.",
  "Long prints are nerve-wracking; a clear progress and finish time lets you step away without wondering how it is going.",
  "Ingest live job progress; surface percent complete and estimated finish per active print.",
  "Progress bars per active print with estimated finish time.",
  "It shows how far along each long 3D print is and when it will finish, so you know when to come back.",
  R(OCTO, MOON), MK_APP, MK_DS)

U("17", "Hotend and Bed Temperature Stability", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=printer:telemetry\n"
  "| eval hot_dev=abs(hotend_c-hotend_target), bed_dev=abs(bed_c-bed_target)\n"
  "| stats max(hot_dev) as worst_hotend, max(bed_dev) as worst_bed by printer\n"
  "| eval unstable=if(worst_hotend>5 OR worst_bed>5,1,0)",
  "Tracks how tightly each printer holds its hotend and bed temperatures, since drift here causes layer defects and failed prints.",
  "Temperature wobble is an early sign of a failing heater or thermistor; catching it prevents mid-print failures and bad layers.",
  "Ingest firmware temperature telemetry; alert when the deviation from target exceeds a few degrees.",
  "Time chart of temperature deviation from target per printer.",
  "It checks that the printer holds its heat steady, because temperature wobble causes bad prints.",
  R(MOON), MK_APP, MK_DS)

U("17", "Enclosure Air Quality During Printing", "medium", "intermediate", ["Safety"],
  "index=personal sourcetype=workshop:air location=printer_enclosure\n"
  "| timechart span=5m max(voc_index) as voc, max(pm25) as pm25\n"
  "| eval ventilate=if(voc>250 OR pm25>25,1,0)",
  "Monitors fumes and fine particles inside your printer enclosure so you can ventilate when printing materials that off-gas.",
  "Some filaments release irritating fumes and ultrafine particles; watching enclosure air quality keeps your workshop safe to breathe.",
  "Place an air-quality sensor in the enclosure feeding `index=personal`; alert when VOC or particulate levels climb.",
  "Time chart of enclosure VOC and particulate levels with thresholds.",
  "It watches the air inside your 3D printer's box for fumes and dust, so you know when to open a window.",
  R(ESPHOME), MK_APP, MK_DS)

U("17", "Filament Spool Remaining and Runout Warning", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=filament:spool\n"
  "| stats latest(remaining_g) as grams by spool material color\n"
  "| eval runs_low=if(grams<100,1,0)\n"
  "| sort grams",
  "Estimates the grams of filament left on each spool and warns before one runs out mid-print.",
  "A spool running out during a long print wastes hours of work; a low-filament warning lets you swap or reorder in time.",
  "Track remaining filament weight per spool; schedule daily and flag spools running low.",
  "Table of spools sorted by grams remaining with a low warning.",
  "It estimates how much printing plastic is left on each reel and warns you before it runs out during a print.",
  R(OCTO), MK_APP, MK_DS)

U("17", "Filament Usage and Cost Per Print", "low", "intermediate", ["Cost"],
  "index=personal sourcetype=octoprint:job result=success\n"
  "| stats sum(filament_g) as grams, sum(eval(filament_g/1000*spool_price_per_kg)) as cost, count as prints by material\n"
  "| eval cost_per_print=round(cost/prints,2)\n"
  "| sort - cost",
  "Adds up the filament each print consumes and turns it into a per-print cost, so the true price of the hobby is visible.",
  "Filament cost hides in grams here and there; totalling it per material shows where the money actually goes.",
  "Record filament used and spool price per job; schedule monthly and review cost per print by material.",
  "Bar chart of filament cost by material with cost per print.",
  "It adds up how much plastic each print uses and what it costs, so you can see the real price of 3D printing.",
  R(OCTO), MK_APP, MK_DS)

U("17", "Print Farm Utilization Dashboard", "low", "intermediate", ["Capacity"],
  "index=personal sourcetype=octoprint:job\n"
  "| bin _time span=1d\n"
  "| stats sum(print_time_s) as busy_s by printer _time\n"
  "| eval utilization_pct=round(100*busy_s/86400,1)\n"
  "| stats avg(utilization_pct) as avg_util by printer\n"
  "| sort - avg_util",
  "Measures how much of each day your printers are actually printing so you can balance load or justify another machine.",
  "Utilization reveals whether a printer is a bottleneck or idle capacity, guiding both scheduling and buying decisions.",
  "Ingest print durations; schedule daily and compute per-printer utilization over time.",
  "Bar chart of average daily utilization by printer.",
  "It shows how busy each of your 3D printers is, so you can share the work or decide if you need another.",
  R(OCTO), MK_APP, MK_DS)

U("17", "CNC and Laser Job Runtime and Queue", "low", "intermediate", ["Operations"],
  "index=personal sourcetype=cnc:job\n"
  "| stats sum(runtime_s) as run_s, count as jobs, sum(eval(if(state=\"queued\",1,0))) as queued by machine\n"
  "| eval run_hours=round(run_s/3600,1)\n"
  "| sort - run_hours",
  "Tracks runtime and the pending queue for your CNC or laser so you can plan the shop's workload and material.",
  "Knowing machine hours and backlog helps schedule cuts, order stock, and time consumable replacement before a big job.",
  "Ingest CNC/laser job records; schedule daily and review runtime and queue per machine.",
  "Table of machines with total runtime, job count, and queue depth.",
  "It tracks how long your cutting machines run and how many jobs are waiting, so you can plan your projects.",
  R(("LinuxCNC — documentation", "https://linuxcnc.org/docs/")), MK_APP, MK_DS)

U("17", "Workshop Dust and Noise Exposure", "medium", "intermediate", ["Safety"],
  "index=personal sourcetype=workshop:air location=workshop\n"
  "| timechart span=5m max(pm25) as dust, max(noise_db) as noise\n"
  "| eval hearing_risk=if(noise>85,1,0), dust_risk=if(dust>35,1,0)",
  "Logs fine dust and noise levels in the workshop, the two exposures that quietly damage lungs and hearing over years.",
  "Dust and noise harm accumulates invisibly; a running exposure record prompts a mask or ear defenders before it matters.",
  "Place air-quality and sound sensors in the workshop; alert when dust or noise crosses safe exposure levels.",
  "Time chart of workshop dust and noise with safety thresholds.",
  "It measures the dust and noise in your workshop, which can harm your lungs and hearing if you are not careful.",
  R(ESPHOME), MK_APP, MK_DS)

U("17", "Cordless Tool Battery Charge Status", "low", "beginner", ["Availability"],
  "index=personal sourcetype=tool:battery\n"
  "| stats latest(charge_pct) as charge, latest(state) as state by battery\n"
  "| eval ready=if(charge>=80,\"ready\",\"charging\")\n"
  "| sort charge",
  "Shows the charge level of your cordless tool batteries so you never start a job with a dead pack.",
  "A flat battery mid-task is a familiar workshop frustration; a charge overview lets you grab a ready pack instead.",
  "Ingest smart-charger status for your tool batteries; surface charge level and readiness for each.",
  "Table of tool batteries with charge level and ready state.",
  "It shows how charged your power-tool batteries are, so you always grab one that is ready to go.",
  R(ESPHOME), MK_APP, MK_DS)

U("17", "Machine Maintenance Interval Tracker", "low", "intermediate", ["Reliability"],
  "index=personal sourcetype=printer:telemetry\n"
  "| stats sum(print_time_s) as run_s by printer\n"
  "| eval run_hours=round(run_s/3600,0), since_service=run_hours%250, due_in=250-since_service\n"
  "| where due_in<40\n"
  "| sort due_in",
  "Counts machine hours since the last service and reminds you when lubrication or belt checks are due.",
  "Preventive maintenance on printed hours avoids the mid-print failures that neglected machines eventually suffer.",
  "Accumulate machine hours; schedule weekly and flag printers approaching a service interval.",
  "Table of printers with hours until the next service due.",
  "It counts how many hours your machines have run and reminds you when they need a bit of maintenance.",
  R(MOON), MK_APP, MK_DS)


# ===========================================================================
# 25.18  Home Security & Surveillance
# ===========================================================================
SE_APP = ("Frigate / Blue Iris NVR object-detection events, camera health, alarm and smart-lock "
          "logs, and licence-plate recognition via MQTT and Splunk HEC.")
SE_DS = ("NVR object-detection (`frigate:event`), camera health (`camera:health`), alarm arm/"
         "disarm and life-safety (`alarm:event`), lock access (`lock:access`), plate recognition "
         "(`plate:detection`), doorbell (`doorbell:event`).")
FRIGATE = ("Frigate NVR — documentation", "https://docs.frigate.video/")
BLUEIRIS = ("Blue Iris — MQTT / alerts", "https://blueirissoftware.com/")

U("18", "Camera Object-Detection Counts by Type", "low", "beginner", ["Security"],
  "index=personal sourcetype=frigate:event\n"
  "| bin _time span=1d\n"
  "| stats count as detections by label camera _time\n"
  "| stats sum(detections) as total by label camera\n"
  "| sort - total",
  "Summarises how many people, cars, and animals each camera detected so you understand the normal traffic around your home.",
  "A baseline of detections per camera turns object detection from a stream of clips into a picture of your property's routine.",
  "Send NVR detection events to `index=personal`; schedule daily and review counts by object type and camera.",
  "Bar chart of detections by object type per camera.",
  "It counts how many people, cars, and animals each camera sees, so you learn what is normal around your home.",
  R(FRIGATE, BLUEIRIS), SE_APP, SE_DS, pillar="Security")

U("18", "Package Delivery and Porch-Pirate Watch", "medium", "intermediate", ["Security"],
  "index=personal sourcetype=frigate:event camera=front_door label=package\n"
  "| stats earliest(_time) as appeared, latest(_time) as last_seen by event_id\n"
  "| eval dwell_min=round((last_seen-appeared)/60,0)\n"
  "| where dwell_min>0",
  "Detects when a package appears at the door and how long it sits there, so a parcel taken quickly by a stranger stands out.",
  "Porch theft happens in the gap between delivery and pickup; tracking a package's dwell time turns a camera into a theft alert.",
  "Detect the package object class at the door; alert on delivery and on unusually fast removal.",
  "Timeline of package appearances with dwell time at the door.",
  "It notices when a parcel arrives at your door and how long it stays, so you can spot if someone grabs it.",
  R(FRIGATE), SE_APP, SE_DS, pillar="Security")

U("18", "Detection False-Positive Rate by Camera", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=frigate:event\n"
  "| stats sum(eval(if(false_positive=\"true\",1,0))) as fps, count as events by camera\n"
  "| eval fp_rate=round(100*fps/events,1)\n"
  "| sort - fp_rate",
  "Measures how often each camera raises a false detection so you can tune the noisy ones instead of ignoring all alerts.",
  "A camera that cries wolf trains you to ignore it; a false-positive rate shows exactly which needs zone or threshold tuning.",
  "Label reviewed detections as true or false; schedule weekly and rank cameras by false-positive rate.",
  "Bar chart of false-positive rate by camera.",
  "It measures how often each camera raises a false alarm, so you can fix the annoying ones and trust the rest.",
  R(FRIGATE), SE_APP, SE_DS, pillar="Security")

U("18", "Camera Offline and Health Monitor", "medium", "beginner", ["Availability"],
  "index=personal sourcetype=camera:health\n"
  "| stats latest(_time) as last_seen, latest(status) as status by camera\n"
  "| eval mins_silent=round((now()-last_seen)/60,0), offline=if(mins_silent>10,1,0)\n"
  "| where offline=1",
  "Alerts when a security camera stops reporting, because a camera that is quietly offline is worse than no camera at all.",
  "Cameras fail silently and you only notice when you need the footage; a heartbeat check catches an outage the day it happens.",
  "Ingest camera heartbeats or status; alert when a camera has not reported for several minutes.",
  "Table of cameras with minutes since last seen and offline flag.",
  "It warns you if a security camera goes offline, so you are not relying on one that has quietly stopped working.",
  R(FRIGATE, BLUEIRIS), SE_APP, SE_DS, pillar="Security")

U("18", "Alarm Arm and Disarm Audit", "medium", "beginner", ["Audit"],
  "index=personal sourcetype=alarm:event (action=arm OR action=disarm)\n"
  "| stats count as events, values(action) as actions by user _time\n"
  "| sort - _time\n"
  "| head 50",
  "Keeps a log of who armed or disarmed the alarm and when, a simple audit trail for a busy household.",
  "An arm and disarm history answers the everyday question of whether the house was actually set, and by whom, without guesswork.",
  "Ingest alarm-panel events to `index=personal`; review the recent arm and disarm history by user.",
  "Table of recent arm and disarm actions by user and time.",
  "It keeps a record of who turned the burglar alarm on or off and when, so you can always check.",
  R(("Home Assistant — alarm control panel", "https://www.home-assistant.io/integrations/alarm_control_panel/")), SE_APP, SE_DS, pillar="Security")

U("18", "Smoke and CO Alarm Event Log", "high", "beginner", ["Safety"],
  "index=personal sourcetype=alarm:event (device=smoke OR device=co)\n"
  "| stats count as alerts, values(state) as states, latest(battery_pct) as battery by device room\n"
  "| eval low_battery=if(battery<20,1,0)\n"
  "| sort - alerts",
  "Logs every smoke and carbon-monoxide alarm event and low-battery warning, the life-safety signals that must never be missed.",
  "Smoke and CO alerts are the highest-stakes events in a home; capturing them and battery health ensures the alarms work when needed.",
  "Ingest connected smoke and CO detector events; alert immediately on any activation or low battery.",
  "Table of smoke and CO devices with alert counts and battery level.",
  "It records every smoke and carbon-monoxide alarm and warns of low batteries, keeping the most important home alarms working.",
  R(("Home Assistant — binary sensor (smoke/CO)", "https://www.home-assistant.io/integrations/binary_sensor/")), SE_APP, SE_DS, pillar="Security")

U("18", "Keypad Lock Access History", "medium", "intermediate", ["Security"],
  "index=personal sourcetype=lock:access\n"
  "| stats count as unlocks, values(method) as methods by user door\n"
  "| sort - unlocks",
  "Summarises who unlocked each door and how, from codes to app to key, giving a clear picture of household and guest access.",
  "A per-user unlock history spots an unexpected code use and confirms a guest or contractor came and went as planned.",
  "Ingest smart-lock access logs; schedule daily and review unlocks by user, door, and method.",
  "Table of unlock counts by user and door with methods used.",
  "It shows who unlocked each door and how, so you can keep an eye on who is coming and going.",
  R(("Home Assistant — lock", "https://www.home-assistant.io/integrations/lock/")), SE_APP, SE_DS, pillar="Security")

U("18", "Repeat-Vehicle and Stranger-Car Alert", "medium", "advanced", ["Security", "Anomaly"],
  "index=personal sourcetype=plate:detection\n"
  "| stats count as sightings, earliest(_time) as first_seen by plate\n"
  "| eval known=if(sightings>=5,\"regular\",\"infrequent\"), brand_new=if(first_seen>relative_time(now(),\"-1d\"),1,0)\n"
  "| where known=\"infrequent\" AND brand_new=1",
  "Flags vehicles seen on your street for the first time against the regulars, useful context for a quiet neighbourhood watch.",
  "Distinguishing a new car from the daily regulars turns plate recognition into a gentle heads-up rather than constant noise.",
  "Feed plate-recognition results into `index=personal`; alert on brand-new plates that are not among the regulars.",
  "Table of newly seen plates with sighting counts.",
  "It learns which cars are regulars on your street and points out ones it has never seen before.",
  R(("CodeProject.AI / ALPR — overview", "https://www.codeproject.com/AI/docs/")), SE_APP, SE_DS, pillar="Security")

U("18", "Night-Time Motion Anomaly Baseline", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=frigate:event label=person\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| where hour>=1 AND hour<=4\n"
  "| bin _time span=1d\n"
  "| stats count as night_person_events by _time camera\n"
  "| eventstats avg(night_person_events) as usual by camera\n"
  "| where night_person_events>usual+3",
  "Learns how much person-motion is normal in the small hours and flags a night with far more than usual.",
  "Most late-night motion is harmless, but a sharp spike above your own baseline is exactly the kind of thing worth a look.",
  "Ingest person detections; schedule each morning and alert when overnight activity exceeds the camera's baseline.",
  "Time chart of overnight person events per camera with baseline band.",
  "It learns how much movement is normal at night and warns you if there is a lot more than usual.",
  R(FRIGATE), SE_APP, SE_DS, pillar="Security")

U("18", "Doorbell Ring and Visitor Classification", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=doorbell:event\n"
  "| stats count as rings by classification\n"
  "| sort - rings",
  "Breaks down doorbell activity into deliveries, visitors, and solicitors so you can see who actually comes to the door.",
  "Classifying rings turns a noisy doorbell into useful insight, like how many deliveries you really get versus cold callers.",
  "Ingest doorbell press and detection events; schedule weekly and review the mix of visitor types.",
  "Pie chart of doorbell rings by visitor classification.",
  "It sorts your doorbell rings into deliveries, visitors, and salespeople, so you can see who keeps coming to the door.",
  R(("Home Assistant — doorbell events", "https://www.home-assistant.io/integrations/doorbell/")), SE_APP, SE_DS)

U("18", "Alarm False-Alarm Rate", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=alarm:event action=trigger\n"
  "| stats sum(eval(if(outcome=\"false\",1,0))) as false_alarms, count as triggers by zone\n"
  "| eval false_pct=round(100*false_alarms/triggers,1)\n"
  "| sort - false_pct",
  "Measures how often each alarm zone triggers falsely so you can fix the sensor that keeps crying wolf.",
  "False alarms erode trust and risk fines; pinpointing the worst zone lets you reposition or adjust a single problem sensor.",
  "Tag alarm triggers with their outcome; schedule monthly and rank zones by false-alarm rate.",
  "Bar chart of false-alarm rate by zone.",
  "It measures which alarm sensors keep going off for no reason, so you can fix the troublesome one.",
  R(("Home Assistant — alarm control panel", "https://www.home-assistant.io/integrations/alarm_control_panel/")), SE_APP, SE_DS, pillar="Security")

U("18", "Recording Storage Retention and Capacity", "low", "intermediate", ["Capacity"],
  "index=personal sourcetype=camera:health event=storage\n"
  "| stats latest(used_gb) as used, latest(total_gb) as total, latest(oldest_clip_epoch) as oldest by nvr\n"
  "| eval used_pct=round(100*used/total,1), retention_days=round((now()-oldest)/86400,1)",
  "Tracks how full your NVR storage is and how many days of footage you are actually keeping.",
  "Security footage is worthless if it rolled off before you needed it; watching capacity and real retention keeps the evidence window honest.",
  "Ingest NVR storage stats; schedule daily and surface used capacity and actual retention days.",
  "Gauge of storage used with retention-days indicator.",
  "It shows how full your camera storage is and how many days of video you are keeping, so recordings are there when you need them.",
  R(FRIGATE, BLUEIRIS), SE_APP, SE_DS, pillar="Security")


# ===========================================================================
# 25.19  Water, Plumbing & Utilities
# ===========================================================================
WA_APP = ("Smart water meters (Flume / Flo / HomeWizard), sump- and well-pump sensors, pool/spa "
          "controllers, water-softener and irrigation controllers via vendor APIs, MQTT, and HEC.")
WA_DS = ("Whole-home water flow (`watermeter:flow`), sump pump (`sumppump:event`), well pump "
         "(`wellpump:event`), pool/spa chemistry (`pool:chemistry`), water softener "
         "(`watersoftener:status`), irrigation zones (`irrigation:zone`).")
FLUME = ("Flume — personal API", "https://help.flumewater.com/en/articles/3457857-flume-personal-api")

U("19", "Continuous-Flow Water Leak Detection", "high", "intermediate", ["Anomaly"],
  "index=personal sourcetype=watermeter:flow\n"
  "| timechart span=15m max(flow_lpm) as flow\n"
  "| streamstats current=t count(eval(flow>0)) as consecutive reset_after=\"(flow=0)\"\n"
  "| eval leak_suspected=if(consecutive>=8,1,0)",
  "Detects water flowing continuously for hours with no pause, the tell-tale signature of a running toilet or a burst pipe.",
  "A silent leak can waste thousands of litres and cause real damage; catching non-stop flow early turns a disaster into a quick fix.",
  "Feed a smart water meter into `index=personal`; alert when flow never returns to zero over a sustained window.",
  "Time chart of water flow with continuous-flow periods highlighted.",
  "It spots water running non-stop for a long time, which usually means a running toilet or a leak, so you can act fast.",
  R(FLUME), WA_APP, WA_DS)

U("19", "Daily Water Usage and Fixture Breakdown", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=watermeter:flow\n"
  "| bin _time span=1d\n"
  "| stats sum(volume_l) as litres by fixture _time\n"
  "| stats avg(litres) as avg_daily by fixture\n"
  "| sort - avg_daily",
  "Breaks your daily water use down by fixture so you can see whether the shower, garden, or laundry drives the bill.",
  "Knowing which fixture uses the most water is the first step to cutting the bill, and it is usually a surprise.",
  "Ingest per-fixture or disaggregated flow; schedule daily and rank fixtures by average usage.",
  "Bar chart of average daily water use by fixture.",
  "It shows which taps and appliances use the most water at home, which is usually surprising.",
  R(FLUME), WA_APP, WA_DS)

U("19", "Monthly Water Bill Estimate", "low", "beginner", ["Cost"],
  "index=personal sourcetype=watermeter:flow\n"
  "| bin _time span=1mon\n"
  "| stats sum(volume_l) as litres by _time\n"
  "| eval kilolitres=round(litres/1000,2), est_bill=round(kilolitres*rate_per_kl,2)\n"
  "| sort - _time",
  "Turns your metered water use into a running monthly cost estimate so the bill never comes as a shock.",
  "Water bills arrive quarterly and vaguely; a monthly running estimate keeps usage and cost connected while you can still change habits.",
  "Ingest metered volume and your tariff; schedule monthly and trend the estimated cost.",
  "Column chart of estimated monthly water cost.",
  "It turns how much water you use into an estimated monthly cost, so the bill is never a surprise.",
  R(FLUME), WA_APP, WA_DS)

U("19", "Sump Pump Activation and Failure Alert", "high", "intermediate", ["Availability"],
  "index=personal sourcetype=sumppump:event\n"
  "| stats latest(_time) as last_run, sum(eval(if(event=\"run\",1,0))) as runs, latest(water_level_cm) as level\n"
  "| eval high_water=if(level>40,1,0), silent=if((now()-last_run)>604800,1,0)",
  "Watches your sump pump for both high water and a pump that has gone suspiciously quiet, either of which means a wet basement soon.",
  "A failed sump pump is discovered too late, after the flood; monitoring level and activity gives warning while the basement is still dry.",
  "Ingest a sump-pump sensor and float switch; alert on high water level or an unexpectedly idle pump during wet weather.",
  "Single-value water-level gauge with pump activity history.",
  "It keeps an eye on the pump that keeps your basement dry, warning you if the water rises or the pump seems to have stopped.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Sump Pump Cycle-Frequency Flood Warning", "medium", "intermediate", ["Risk"],
  "index=personal sourcetype=sumppump:event event=run\n"
  "| bin _time span=1h\n"
  "| stats count as cycles by _time\n"
  "| eventstats avg(cycles) as usual\n"
  "| eval overwhelmed=if(cycles>usual*3,1,0)",
  "Alerts when the sump pump is cycling far more often than normal, a sign the water table is rising faster than usual.",
  "A pump cycling constantly is racing a rising water table; an early frequency alert buys time to act before it loses.",
  "Ingest pump run events; schedule hourly during storms and alert when cycle frequency spikes above baseline.",
  "Time chart of pump cycles per hour with a baseline band.",
  "It warns you when the basement pump is running much more than usual, which can mean flooding is on the way.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Well Pump Short-Cycle Health", "medium", "advanced", ["Reliability"],
  "index=personal sourcetype=wellpump:event event=run\n"
  "| streamstats current=f last(_time) as prev_run\n"
  "| eval gap_s=_time-prev_run\n"
  "| stats count(eval(gap_s<60)) as short_cycles, count as runs\n"
  "| eval short_cycle_pct=round(100*short_cycles/runs,1)",
  "Detects a well pump switching on and off too rapidly, the short-cycling that burns out pumps and points to a failing pressure tank.",
  "Short-cycling is the classic early symptom of a waterlogged pressure tank; catching it saves an expensive pump before it fails.",
  "Ingest well-pump run events; schedule daily and flag a high proportion of rapid on-off cycles.",
  "Single-value short-cycle percentage with run history.",
  "It spots when a well pump keeps switching on and off too quickly, which wears it out and needs fixing.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Pool and Spa Chemistry Balance", "medium", "beginner", ["Safety"],
  "index=personal sourcetype=pool:chemistry\n"
  "| stats latest(ph) as ph, latest(orp_mv) as orp, latest(temp_c) as temp\n"
  "| eval ph_ok=if(ph>=7.2 AND ph<=7.8,\"good\",\"adjust\"), sanitiser_ok=if(orp>=650,\"good\",\"low\")",
  "Tracks pool or spa pH and sanitiser level so the water stays safe and comfortable without constant test strips.",
  "Unbalanced pool water irritates skin and eyes and lets algae bloom; continuous chemistry keeps it safe with far less fuss.",
  "Ingest a pool controller's pH and ORP readings; alert when either drifts out of the safe range.",
  "Single-value panels for pH and sanitiser level with safe bands.",
  "It checks that your pool or hot tub water is balanced and safe to swim in, without endless testing.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Pool Pump Runtime and Energy Cost", "low", "intermediate", ["Cost"],
  "index=personal sourcetype=pool:chemistry event=pump\n"
  "| bin _time span=1d\n"
  "| stats sum(pump_watt_hours) as wh by _time\n"
  "| eval kwh=round(wh/1000,2), cost=round(kwh*rate_per_kwh,2)\n"
  "| sort - _time",
  "Adds up how long the pool pump runs and what that costs, since the pump is often the single biggest energy user at home.",
  "Pool pumps quietly dominate summer electricity bills; seeing their daily cost reveals how much shorter run-times could save.",
  "Ingest pump energy readings; schedule daily and trend runtime cost.",
  "Column chart of daily pool-pump energy cost.",
  "It adds up how much running the pool pump costs, which is often one of the biggest parts of the electricity bill.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Water Softener Salt-Level Reminder", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=watersoftener:status\n"
  "| stats latest(salt_pct) as salt, latest(days_to_empty) as days_left\n"
  "| eval refill=if(salt<25,\"refill soon\",\"ok\")",
  "Watches the salt level in your water softener and reminds you to top it up before hard water returns.",
  "A softener that runs out of salt silently reverts to hard water, scaling appliances; a refill reminder prevents the creep.",
  "Ingest softener salt-level readings; schedule weekly and alert when salt runs low.",
  "Single-value salt-level gauge with a refill reminder.",
  "It watches the salt in your water softener and reminds you to refill it before the water gets hard again.",
  R(ESPHOME), WA_APP, WA_DS)

U("19", "Irrigation Zone Runtime and Rain-Skip", "low", "intermediate", ["Operations"],
  "index=personal sourcetype=irrigation:zone\n"
  "| stats sum(runtime_min) as minutes, sum(eval(if(skipped=\"rain\",1,0))) as rain_skips, count as cycles by zone\n"
  "| sort - minutes",
  "Summarises how long each irrigation zone ran and how often it sensibly skipped watering after rain.",
  "Seeing runtime and rain-skips per zone confirms the controller is watering smartly rather than soaking the garden after a downpour.",
  "Ingest irrigation controller events; schedule weekly and review runtime and rain-skips by zone.",
  "Bar chart of watering minutes by zone with rain-skip counts.",
  "It shows how long each part of the garden was watered and when it wisely skipped because of rain.",
  R(("OpenSprinkler — API", "https://openthings.freshdesk.com/support/solutions/articles/5000716363")), WA_APP, WA_DS)

U("19", "Irrigation Water Budget vs Rainfall", "low", "advanced", ["Cost"],
  "index=personal sourcetype=irrigation:zone\n"
  "| bin _time span=1w\n"
  "| stats sum(water_l) as irrigated_l by _time\n"
  "| eval budget_l=6000, over_budget=if(irrigated_l>budget_l,1,0)\n"
  "| sort - _time",
  "Compares how much water your garden irrigation used each week against a target budget so watering stays generous but not wasteful.",
  "Irrigation is easy to over-do; a weekly water budget keeps the garden healthy while curbing the biggest avoidable water expense.",
  "Ingest irrigation volumes; schedule weekly and compare usage to your water budget.",
  "Column chart of weekly irrigation volume against a budget line.",
  "It compares how much water the garden sprinklers use each week to a sensible target, so you do not overwater.",
  R(("OpenSprinkler — API", "https://openthings.freshdesk.com/support/solutions/articles/5000716363")), WA_APP, WA_DS)


# ===========================================================================
# 25.20  Citizen Science & Backyard Sensing
# ===========================================================================
CS_APP = ("DIY citizen-science sensors — Raspberry Shake seismograph, DIY Geiger counter, "
          "AS3935/Blitzortung lightning detector, radon monitor, all-sky meteor camera, river-"
          "level gauge, and magnetometer — streamed to Splunk HEC via MQTT and scripted inputs.")
CS_DS = ("Seismograph (`seismo:reading`), Geiger counter (`geiger:cpm`), lightning strikes "
         "(`lightning:strike`), radon (`radon:reading`), all-sky meteor camera (`allsky:capture`), "
         "river-level gauge (`riverlevel:reading`), magnetometer (`magnetometer:reading`).")
RSHAKE = ("Raspberry Shake — citizen seismograph", "https://raspberryshake.org/")
BLITZ = ("Blitzortung — lightning detection network", "https://www.blitzortung.org/")

U("20", "Backyard Seismograph Quake Detection", "low", "advanced", ["Anomaly"],
  "index=personal sourcetype=seismo:reading\n"
  "| eventstats avg(amplitude) as base, stdev(amplitude) as sd\n"
  "| eval quake=if(amplitude>base+6*sd,1,0)\n"
  "| where quake=1\n"
  "| table _time amplitude base",
  "Flags ground-motion spikes far above your sensor's quiet baseline, catching real earthquakes among the everyday rumble of traffic.",
  "A personal seismograph is only useful if it separates a genuine quake from a passing truck; a statistical baseline does exactly that.",
  "Stream Raspberry Shake amplitude into `index=personal`; alert when motion jumps well above the rolling background level.",
  "Time chart of ground-motion amplitude with detected quakes marked.",
  "It watches the ground shaking sensor in your home and picks out real earthquakes from ordinary rumbles like passing lorries.",
  R(RSHAKE), CS_APP, CS_DS)

U("20", "Seismograph Daily Noise Floor", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=seismo:reading\n"
  "| timechart span=1h avg(amplitude) as noise\n"
  "| eval hour=strftime(_time,\"%H\")",
  "Trends the background vibration level through the day, revealing the human rhythm of rush hour, quiet nights, and weekends.",
  "The daily noise floor is a fascinating fingerprint of your neighbourhood and the reference every quake detection is measured against.",
  "Ingest seismograph amplitude; review the hourly noise pattern to understand your sensor's environment.",
  "Line chart of hourly background vibration over a day.",
  "It shows how much the ground quietly buzzes at different times of day, which is busiest during rush hour.",
  R(RSHAKE), CS_APP, CS_DS)

U("20", "Radiation Level Anomaly Watch", "medium", "advanced", ["Safety", "Anomaly"],
  "index=personal sourcetype=geiger:cpm\n"
  "| eventstats avg(cpm) as base, stdev(cpm) as sd\n"
  "| eval usv_h=round(cpm*0.0057,3), elevated=if(cpm>base+5*sd,1,0)\n"
  "| where elevated=1\n"
  "| table _time cpm usv_h",
  "Watches your Geiger counter for readings well above the normal background and converts counts to an approximate dose rate.",
  "Background radiation is steady; a sustained jump is worth knowing about, and a personal monitor turns curiosity into reassurance.",
  "Feed counts-per-minute into `index=personal`; alert on readings that rise clearly above your local background.",
  "Time chart of radiation with an elevated-reading threshold.",
  "It keeps an eye on the natural background radiation and tells you if it ever rises noticeably above normal.",
  R(("Safecast — open radiation data", "https://safecast.org/")), CS_APP, CS_DS)

U("20", "Lightning Proximity and Storm Approach", "medium", "intermediate", ["Safety", "Anomaly"],
  "index=personal sourcetype=lightning:strike\n"
  "| bin _time span=5m\n"
  "| stats count as strikes, min(distance_km) as nearest by _time\n"
  "| eval close=if(nearest<10,1,0)\n"
  "| sort - _time",
  "Counts nearby lightning strikes and tracks the closest one so you get a heads-up when a storm is bearing down.",
  "A falling nearest-strike distance is the clearest early warning that a storm is closing in, time to bring in the washing or the kids.",
  "Ingest AS3935 or Blitzortung strike data; alert when the nearest strike falls inside your safety radius.",
  "Time chart of strike count with nearest-distance overlay.",
  "It counts nearby lightning and shows how close the storm is getting, so you know when to head indoors.",
  R(BLITZ), CS_APP, CS_DS)

U("20", "Home Radon Level Trend and Alert", "high", "beginner", ["Safety"],
  "index=personal sourcetype=radon:reading\n"
  "| timechart span=1d avg(radon_bq_m3) as radon\n"
  "| eval over_action=if(radon>100,1,0)",
  "Trends indoor radon against health-guideline levels so a slow, invisible build-up in the basement never goes unnoticed.",
  "Radon is an odourless long-term health risk; a daily trend against the action level tells you whether ventilation is actually needed.",
  "Ingest a continuous radon monitor into `index=personal`; alert when the daily average crosses the action threshold.",
  "Line chart of daily radon with an action-level reference line.",
  "It tracks the invisible radon gas in your home and warns you if it gets high enough to need better ventilation.",
  R(("WHO — Radon and health", "https://www.who.int/news-room/fact-sheets/detail/radon-and-health")), CS_APP, CS_DS)

U("20", "All-Sky Camera Meteor and Fireball Log", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=allsky:capture event=detection\n"
  "| bin _time span=1d\n"
  "| stats count as meteors, max(brightness) as brightest by _time\n"
  "| sort - _time",
  "Counts meteor and fireball detections from your all-sky camera each night, building your own record of the sky's activity.",
  "An all-sky camera turns clear nights into data; a nightly meteor count reveals shower peaks and the occasional bright fireball.",
  "Feed all-sky detection events into `index=personal`; schedule nightly and review meteor counts and peak brightness.",
  "Column chart of nightly meteor detections with brightness peaks.",
  "It counts the shooting stars your night-sky camera spots each night, so you can see when meteor showers are at their best.",
  R(("UKMON — meteor observation network", "https://ukmeteornetwork.co.uk/")), CS_APP, CS_DS)

U("20", "River or Creek Level Flood Watch", "high", "intermediate", ["Risk", "Anomaly"],
  "index=personal sourcetype=riverlevel:reading\n"
  "| streamstats current=f last(level_cm) as prev\n"
  "| eval rise_rate=level_cm-prev\n"
  "| stats latest(level_cm) as level, max(rise_rate) as fastest_rise\n"
  "| eval flood_risk=if(level>200 OR fastest_rise>15,1,0)",
  "Tracks the level of a nearby river or creek and how fast it is rising, an early flood warning for properties near water.",
  "Flooding is about rate as much as height; watching both the level and the rise speed gives precious minutes to act.",
  "Ingest an ultrasonic level sensor over the water into `index=personal`; alert on a high level or a rapid rise.",
  "Time chart of water level with rise-rate and flood threshold.",
  "It watches a nearby stream's level and how quickly it is rising, giving early warning of possible flooding.",
  R(("USGS — water data for the nation", "https://waterdata.usgs.gov/nwis")), CS_APP, CS_DS)

U("20", "Geomagnetic Activity and Aurora Chance", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=magnetometer:reading\n"
  "| timechart span=1h max(field_nt) as field\n"
  "| streamstats current=f last(field) as prev\n"
  "| eval disturbance=abs(field-prev), aurora_watch=if(disturbance>50,1,0)",
  "Watches your magnetometer for the field disturbances that accompany geomagnetic storms and hint at aurora visible from your latitude.",
  "A backyard magnetometer gives a personal, local aurora heads-up that official indices miss, letting you step outside at the right moment.",
  "Ingest magnetometer readings; flag hours with large field swings as an aurora watch.",
  "Time chart of magnetic field with disturbance spikes highlighted.",
  "It notices the magnetic disturbances that come with space-weather storms, hinting when the northern lights might be visible.",
  R(("NOAA SWPC — space weather", "https://www.swpc.noaa.gov/")), CS_APP, CS_DS)

U("20", "International Space Station Pass Reminder", "low", "beginner", ["Availability"],
  "index=personal sourcetype=satpass:prediction satellite=ISS\n"
  "| eval mins_away=round((pass_epoch-now())/60,0)\n"
  "| where mins_away>0 AND mins_away<60 AND max_elevation>30\n"
  "| sort mins_away\n"
  "| table pass_epoch mins_away max_elevation direction",
  "Reminds you when the Space Station will make a bright, high pass over your location so you can catch it with the naked eye.",
  "The ISS is easy to see but easy to miss; a timely reminder for the good high passes turns a rare glimpse into a regular treat.",
  "Ingest ISS pass predictions into `index=personal`; alert shortly before a high-elevation evening pass.",
  "Table of upcoming ISS passes with time, elevation, and direction.",
  "It reminds you just before the Space Station flies over so you can go outside and watch it cross the sky.",
  R(("NASA — Spot the Station", "https://spotthestation.nasa.gov/")), CS_APP, CS_DS)

U("20", "Backyard Sensor Fleet Uptime", "low", "intermediate", ["Availability"],
  "index=personal (sourcetype=seismo:reading OR sourcetype=geiger:cpm OR sourcetype=radon:reading OR sourcetype=magnetometer:reading)\n"
  "| stats latest(_time) as last_seen by sourcetype\n"
  "| eval mins_silent=round((now()-last_seen)/60,0), offline=if(mins_silent>30,1,0)\n"
  "| sort - mins_silent",
  "Checks that each of your citizen-science sensors is still reporting so a dead feed does not leave a silent gap in your data.",
  "Long-running science needs unbroken data; a simple heartbeat across the sensor fleet catches a crashed feed before the record has holes.",
  "Track the last-seen time per sensor sourcetype; alert when any has been quiet too long.",
  "Table of sensors with minutes since last reading and offline flag.",
  "It makes sure all your little science sensors are still sending data, so none quietly stops without you noticing.",
  R(RSHAKE), CS_APP, CS_DS)

U("20", "Meteor Shower Peak-Night Ranking", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=allsky:capture event=detection\n"
  "| bin _time span=1d\n"
  "| stats count as meteors by _time\n"
  "| eventstats avg(meteors) as typical\n"
  "| eval peak=if(meteors>typical*3,1,0)\n"
  "| sort - meteors\n"
  "| head 10",
  "Ranks your busiest meteor nights against a typical night, letting your own camera confirm when a shower actually peaked overhead.",
  "Predicted shower peaks often miss local conditions; your own detection count is the honest record of what your sky really delivered.",
  "Ingest all-sky detections; schedule after each night and rank nights by how far above typical the count rose.",
  "Ranked table of the busiest meteor nights versus typical.",
  "It ranks your best shooting-star nights so you can see which meteor showers really put on a show over your house.",
  R(("IMO — International Meteor Organization", "https://www.imo.net/")), CS_APP, CS_DS)


# ===========================================================================
# 25.21  Radio, SDR & Space
# ===========================================================================
RD_APP = ("Software-defined radio and ham-radio stations — APRS igate, WSPR beacon, NOAA weather-"
          "satellite (APT) receiver, meteor-scatter monitor, and SSTV decoder — logging to Splunk "
          "HEC via scripted inputs.")
RD_DS = ("APRS packets (`aprs:packet`), WSPR spots (`wspr:spot`), satellite passes "
         "(`satpass:prediction`), NOAA APT captures (`noaa:apt`), meteor-scatter pings "
         "(`meteorscatter:ping`), SSTV images (`sstv:image`).")
WSPR = ("WSPRnet — weak-signal propagation reporter", "https://www.wsprnet.org/")
APRS = ("APRS-IS — automatic packet reporting", "http://www.aprs-is.net/")

U("21", "WSPR Propagation Reach and DX Records", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=wspr:spot\n"
  "| stats max(distance_km) as best_dx, dc(reporter_grid) as stations, count as spots by band\n"
  "| sort - best_dx",
  "Summarises how far your low-power WSPR beacon reached on each band, capturing your best long-distance contacts.",
  "WSPR turns a tiny signal into a global propagation experiment; a per-band reach record shows which band is open and how far it carries.",
  "Ingest your WSPR spots into `index=personal`; schedule daily and review best distance and reporting stations per band.",
  "Bar chart of best distance reached by band.",
  "It shows how far your tiny radio beacon was heard on each band, which is a fun way to study how radio waves travel.",
  R(WSPR), RD_APP, RD_DS)

U("21", "WSPR Band-Opening Time-of-Day Map", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=wspr:spot\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats avg(distance_km) as reach by band hour\n"
  "| sort band hour",
  "Maps when each radio band tends to open for long distance by hour, guiding when to listen for far-away signals.",
  "Band openings follow the sun; charting reach by hour and band turns propagation folklore into your own measured schedule.",
  "Ingest WSPR spots with timestamps; review average reach by band and hour to learn your local openings.",
  "Heatmap of average reach by band and hour of day.",
  "It shows what times of day each radio band carries signals furthest, so you know when to listen.",
  R(WSPR), RD_APP, RD_DS)

U("21", "APRS Station Heard and Range", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=aprs:packet\n"
  "| bin _time span=1d\n"
  "| stats dc(callsign) as stations, max(distance_km) as farthest, count as packets by _time\n"
  "| sort - _time",
  "Counts how many APRS stations your igate heard each day and the farthest one, a daily measure of your station's reach.",
  "An igate's daily station count and range is the simplest health-and-reach metric, showing when conditions or antennas change.",
  "Ingest APRS-IS packets from your igate; schedule daily and review stations heard and maximum range.",
  "Column chart of daily stations heard with farthest-station overlay.",
  "It counts how many other radio stations your receiver picked up each day and the most distant one.",
  R(APRS), RD_APP, RD_DS)

U("21", "NOAA Weather-Satellite Pass Capture Log", "low", "advanced", ["Availability"],
  "index=personal sourcetype=noaa:apt\n"
  "| stats count as captures, avg(max_elevation) as avg_elev, sum(eval(if(quality=\"good\",1,0))) as good by satellite\n"
  "| eval success_pct=round(100*good/captures,1)\n"
  "| sort - captures",
  "Logs each weather-satellite image capture and how many came out clean, so you can tune your antenna and timing.",
  "APT reception is finicky; tracking capture success per satellite tells you whether an antenna change actually improved your images.",
  "Ingest capture metadata from your NOAA APT receiver; schedule daily and review success rate per satellite.",
  "Bar chart of capture success rate by satellite.",
  "It records each time you catch a picture from a weather satellite and how many turned out clear.",
  R(("NOAA — APT weather satellites", "https://www.noaa.gov/")), RD_APP, RD_DS)

U("21", "Satellite Pass Schedule for Today", "low", "beginner", ["Availability"],
  "index=personal sourcetype=satpass:prediction\n"
  "| eval mins_away=round((pass_epoch-now())/60,0)\n"
  "| where mins_away>0 AND mins_away<720\n"
  "| sort mins_away\n"
  "| table satellite pass_epoch mins_away max_elevation",
  "Lists the upcoming satellite passes over your station today so you never miss a good reception or spotting window.",
  "Passes are brief and infrequent; a clear same-day schedule means you are set up and recording before the satellite rises.",
  "Ingest pass predictions for your satellites of interest; schedule daily and surface today's passes by time.",
  "Table of today's passes with time-away and maximum elevation.",
  "It lists when satellites will pass overhead today, so you are ready to catch their signals.",
  R(("Celestrak — orbital data", "https://celestrak.org/")), RD_APP, RD_DS)

U("21", "Meteor-Scatter Ping Activity", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=meteorscatter:ping\n"
  "| bin _time span=1h\n"
  "| stats count as pings, avg(duration_ms) as avg_len by _time\n"
  "| sort - _time",
  "Counts the brief radio reflections off meteor trails each hour, an indirect but reliable measure of meteor activity day and night.",
  "Meteor scatter detects meteors even in daylight and cloud; hourly ping counts reveal shower peaks the eye can never see.",
  "Ingest meteor-scatter detections into `index=personal`; review hourly ping counts and echo durations.",
  "Time chart of hourly meteor pings with average echo length.",
  "It counts the tiny radio echoes bouncing off meteor trails, letting you detect meteors even in daylight or clouds.",
  R(("RMOB — radio meteor observation", "https://www.rmob.org/")), RD_APP, RD_DS)

U("21", "SSTV Image Reception Log", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=sstv:image\n"
  "| stats count as images, values(mode) as modes by callsign\n"
  "| sort - images",
  "Keeps a log of slow-scan television images you have received and from whom, including special ISS SSTV events.",
  "SSTV events like ISS transmissions are time-limited; a reception log is a satisfying record of the pictures you pulled from the air.",
  "Ingest decoded SSTV metadata into `index=personal`; review received images by sending station and mode.",
  "Table of received SSTV images by callsign and mode.",
  "It keeps a record of the pictures you receive by radio, including the special ones broadcast from the Space Station.",
  R(("ARISS — amateur radio on the ISS", "https://www.ariss.org/")), RD_APP, RD_DS)

U("21", "SDR Receiver Uptime and Feed Health", "low", "intermediate", ["Availability"],
  "index=personal (sourcetype=aprs:packet OR sourcetype=wspr:spot)\n"
  "| stats latest(_time) as last_pkt by sourcetype\n"
  "| eval mins_silent=round((now()-last_pkt)/60,0), stalled=if(mins_silent>20,1,0)",
  "Confirms your always-on SDR feeds are still decoding, since a crashed dongle or software lock is easy to miss for days.",
  "Unattended receivers fail silently; a heartbeat across your feeds catches a stalled decoder before you lose a week of spots.",
  "Track the last packet time per SDR feed; alert when a feed goes quiet longer than expected.",
  "Table of SDR feeds with minutes since last decode.",
  "It checks your always-on radio receivers are still working, so a crash does not go unnoticed for days.",
  R(WSPR), RD_APP, RD_DS)

U("21", "WSPR Signal-to-Noise Distribution", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=wspr:spot\n"
  "| eval snr_bucket=case(snr<-25,\"very weak\",snr<-15,\"weak\",snr<-5,\"fair\",1=1,\"strong\")\n"
  "| stats count by band snr_bucket\n"
  "| sort band",
  "Breaks your received WSPR reports into signal-strength bands so you can judge how well your antenna hears faint signals.",
  "The share of very-weak decodes you catch is a real measure of receiver sensitivity, useful for comparing antennas objectively.",
  "Ingest WSPR spots with signal-to-noise values; review the strength distribution per band.",
  "Stacked bar chart of signal strength buckets by band.",
  "It sorts the radio signals you receive by how faint they are, showing how good your antenna is at hearing weak ones.",
  R(WSPR), RD_APP, RD_DS)

U("21", "Ham Contact Log and Grid Coverage", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=aprs:packet\n"
  "| bin _time span=1mon\n"
  "| stats dc(grid) as grids, dc(callsign) as stations, count as contacts by _time\n"
  "| sort - _time",
  "Counts the distinct map grid squares and stations your station worked each month, gamifying your on-air activity.",
  "Grid-square chasing is a favourite ham pastime; a monthly coverage count keeps the collection growing and the hobby fun.",
  "Ingest station contacts into `index=personal`; schedule monthly and count distinct grids and stations.",
  "Column chart of grids and stations worked per month.",
  "It counts how many different map areas and stations you contacted by radio each month, like collecting them.",
  R(APRS), RD_APP, RD_DS)

U("21", "Best-DX-of-the-Month Highlight", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=wspr:spot\n"
  "| bin _time span=1mon\n"
  "| stats max(distance_km) as best_dx, values(eval(if(distance_km>18000,reporter_grid,null()))) as antipodal by _time\n"
  "| sort - _time",
  "Highlights your farthest contact each month and flags any near-antipodal reception, the trophies of weak-signal radio.",
  "A monthly best-distance highlight gives the hobby a satisfying scoreboard and preserves the memorable record-breaking days.",
  "Ingest WSPR spots; schedule monthly and surface the best distance and any extraordinary long-haul receptions.",
  "Single-value best-DX tile per month with record markers.",
  "It picks out your most distant radio contact each month, like keeping the trophies of the hobby.",
  R(WSPR), RD_APP, RD_DS)


# ===========================================================================
# 25.22  Backyard Astronomy & Observatory
# ===========================================================================
AS_APP = ("Backyard observatory automation — roll-off-roof/dome controller, sky-quality meter, "
          "cloud sensor, telescope mount, and astrophotography capture software (N.I.N.A./"
          "Ekos) — logging to Splunk HEC via MQTT and scripted inputs.")
AS_DS = ("Observatory environment (`observatory:env`), sky-quality meter (`skyquality:reading`), "
         "imaging sessions (`imaging:session`), telescope mount (`mount:status`), cloud sensor "
         "(`allsky:cloud`).")
NINA = ("N.I.N.A. — astrophotography imager", "https://nighttime-imaging.eu/")
EKOS = ("KStars/Ekos — observatory control", "https://kstars.kde.org/")

U("22", "Astrophotography Sub-Frame Yield per Session", "low", "advanced", ["Quality"],
  "index=personal sourcetype=imaging:session\n"
  "| stats sum(eval(if(rejected=\"false\",1,0))) as kept, count as total, avg(hfr) as focus by target\n"
  "| eval keep_pct=round(100*kept/total,1)\n"
  "| sort keep_pct",
  "Measures how many exposures you kept versus threw away per target, the real productivity of a night under the stars.",
  "Astrophotography is a numbers game; a keep rate per target reveals guiding, focus, or wind problems eating your imaging time.",
  "Ingest per-sub metadata from your capture software; schedule after each session and review keep rate by target.",
  "Bar chart of kept-frame percentage by target.",
  "It counts how many of your long night-sky photos were good enough to keep, showing how productive the night was.",
  R(NINA), AS_APP, AS_DS)

U("22", "Sky Quality and Light-Pollution Trend", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=skyquality:reading\n"
  "| timechart span=1h avg(mpsas) as darkness\n"
  "| eval bortle_hint=case(mpsas>21.5,\"excellent\",mpsas>20.5,\"good\",mpsas>19,\"suburban\",1=1,\"bright\")",
  "Trends how dark your sky actually is through the night, quantifying light pollution and picking the truly dark hours.",
  "Sky darkness drives what you can image; a measured trend beats guesswork for timing faint targets and comparing sites.",
  "Ingest sky-quality-meter readings into `index=personal`; review darkness through the night and across seasons.",
  "Line chart of sky darkness with a light-pollution scale.",
  "It measures how dark your night sky is, so you know the best hours for stargazing away from light pollution.",
  R(("Unihedron — Sky Quality Meter", "http://unihedron.com/projects/darksky/")), AS_APP, AS_DS)

U("22", "Cloud Sensor Imaging-Window Alert", "medium", "intermediate", ["Availability"],
  "index=personal sourcetype=allsky:cloud\n"
  "| stats latest(sky_temp_c) as sky, latest(ambient_c) as amb\n"
  "| eval spread=amb-sky, clear=if(spread>25,\"clear\",\"clouds\")",
  "Uses the sky-minus-ambient temperature spread to tell you when it is genuinely clear enough to open the observatory.",
  "A cloud sensor protects both your gear and your sleep, opening only for real clear spells and closing before the clouds return.",
  "Ingest an infrared cloud sensor into `index=personal`; alert when the sky clears enough for imaging.",
  "Single-value clear-or-cloudy indicator with the temperature spread.",
  "It tells you when the sky is genuinely clear enough to set up the telescope, using a clever temperature trick.",
  R(EKOS), AS_APP, AS_DS)

U("22", "Telescope Mount Guiding Error Trend", "low", "advanced", ["Performance"],
  "index=personal sourcetype=mount:status\n"
  "| timechart span=5m avg(guide_rms_arcsec) as rms\n"
  "| eval poor=if(rms>1.5,1,0)",
  "Trends your mount's guiding error so you can see when wind, balance, or a cable snag is blurring your exposures.",
  "Guiding error directly sets your sharpness limit; watching it live lets you abort and fix a bad run instead of wasting the night.",
  "Ingest guiding RMS from your imaging software; review the trend and flag periods of poor tracking.",
  "Time chart of guiding error with a quality threshold.",
  "It tracks how steadily your telescope tracks the stars, so you can spot when something is making your photos blurry.",
  R(NINA), AS_APP, AS_DS)

U("22", "Observatory Roof and Power State Audit", "medium", "intermediate", ["Audit"],
  "index=personal sourcetype=observatory:env\n"
  "| stats latest(roof_state) as roof, latest(mains_ok) as power, latest(_time) as last_seen\n"
  "| eval stale=if((now()-last_seen)>900,1,0), risk=if(roof=\"open\" AND power=\"false\",1,0)",
  "Confirms the observatory roof and power are in a safe state, catching the nightmare of an open roof on lost power.",
  "An open roof with a failed closer during rain is a gear-destroying event; a safe-state check is cheap insurance for expensive optics.",
  "Ingest roof and power state into `index=personal`; alert on an open roof combined with a power problem or stale telemetry.",
  "Status panel of roof state, power, and a combined risk flag.",
  "It checks the observatory roof and power are safe, so your telescope is never left exposed to the rain.",
  R(EKOS), AS_APP, AS_DS)

U("22", "Imaging Integration-Time Tracker", "low", "intermediate", ["Business"],
  "index=personal sourcetype=imaging:session rejected=false\n"
  "| stats sum(exposure_s) as total_s by target\n"
  "| eval hours=round(total_s/3600,1)\n"
  "| sort - hours",
  "Adds up the total good exposure time you have accumulated on each deep-sky target across all your nights.",
  "Faint objects need many hours stacked over many nights; a running total tells you when a target has enough data to finish.",
  "Ingest kept-sub exposure times; schedule after sessions and total integration hours per target.",
  "Bar chart of total integration hours by target.",
  "It adds up all the hours you have spent photographing each object in space, so you know when you have enough.",
  R(NINA), AS_APP, AS_DS)

U("22", "Best-Seeing Nights Ranking", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=mount:status\n"
  "| bin _time span=1d\n"
  "| stats avg(guide_rms_arcsec) as rms, min(guide_rms_arcsec) as best by _time\n"
  "| sort rms\n"
  "| head 10",
  "Ranks your calmest, steadiest nights by guiding performance so you can plan demanding targets for similar conditions.",
  "Atmospheric steadiness makes or breaks planetary and fine detail; knowing your best nights helps you recognise and use them.",
  "Ingest nightly guiding statistics; rank nights by average steadiness.",
  "Ranked table of nights by guiding steadiness.",
  "It ranks your steadiest, calmest nights for stargazing, so you can plan tricky targets for the best conditions.",
  R(EKOS), AS_APP, AS_DS)

U("22", "Dew and Frost Risk on Optics", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=observatory:env\n"
  "| eval dew_gap=ambient_c-dewpoint_c\n"
  "| stats latest(dew_gap) as gap, latest(ambient_c) as temp\n"
  "| eval dewing=if(gap<2,1,0), frost=if(temp<0 AND gap<2,1,0)",
  "Warns when conditions are about to fog or frost your optics so the dew heaters come on before the night is lost.",
  "Dew on a lens ends imaging instantly; a dew-point margin warning triggers heaters in time to keep the glass clear.",
  "Ingest temperature and dew point into `index=personal`; alert when the margin closes toward dewing or frost.",
  "Single-value dew-margin gauge with a warning band.",
  "It warns when your telescope lens is about to fog up or frost over, so you can turn on the heaters in time.",
  R(EKOS), AS_APP, AS_DS)

U("22", "Clear-Night Utilisation Rate", "low", "intermediate", ["Capacity"],
  "index=personal sourcetype=allsky:cloud\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(sky_temp_c<-20,1,0))) as clear_readings, count as readings by _time\n"
  "| eval clear_pct=round(100*clear_readings/readings,1)\n"
  "| stats avg(clear_pct) as avg_clear",
  "Measures what fraction of night hours were actually clear over time, a sobering but useful reality check for the hobby.",
  "Knowing your true clear-sky percentage sets realistic expectations and helps justify remote or travel imaging plans.",
  "Ingest cloud-sensor readings; schedule monthly and compute the share of clear night hours.",
  "Single-value clear-sky percentage with a monthly trend.",
  "It works out how often your nights are actually clear enough for stargazing, which is often fewer than you would hope.",
  R(EKOS), AS_APP, AS_DS)

U("22", "Meridian-Flip and Session Failure Log", "low", "advanced", ["Reliability"],
  "index=personal sourcetype=imaging:session event=error\n"
  "| stats count as failures by reason\n"
  "| sort - failures",
  "Groups the errors that ended imaging sessions, from failed meridian flips to lost guide stars, so you can fix the top cause.",
  "Automated imaging fails in a handful of predictable ways; naming them turns a ruined night into a concrete reliability fix.",
  "Ingest session error events into `index=personal`; schedule weekly and rank failure causes.",
  "Pie chart of session failures by cause.",
  "It sorts the problems that end your automatic night-sky imaging by cause, so you can fix the most common one.",
  R(NINA), AS_APP, AS_DS)


# ===========================================================================
# 25.23  Family, Baby & Household Chaos
# ===========================================================================
FM_APP = ("Baby-tracking apps (Huckleberry/Baby Daybook exports), chore and allowance boards, "
          "shared family calendars, and growth logs — sent to Splunk HEC via scripted inputs.")
FM_DS = ("Baby feeds (`baby:feed`), baby sleep (`baby:sleep`), diaper changes (`diaper:change`), "
         "chore completions (`chore:completion`), allowance ledger (`allowance:ledger`), family "
         "calendar (`family:calendar`), growth measurements (`growth:measurement`).")
HUCK = ("Huckleberry — baby tracking", "https://huckleberrycare.com/")
WHO_GROWTH = ("WHO — child growth standards", "https://www.who.int/tools/child-growth-standards")

U("23", "Baby Feeding Interval and Daily Total", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=baby:feed\n"
  "| bin _time span=1d\n"
  "| stats count as feeds, sum(amount_ml) as ml by _time\n"
  "| sort - _time",
  "Adds up daily feeds and volume for a new baby so bleary-eyed parents can answer the paediatrician's questions with real numbers.",
  "In the newborn fog, counting feeds and totals by memory is impossible; a clear daily record brings calm and confidence.",
  "Log each feed to `index=personal` from your tracking app; schedule daily and review counts and totals.",
  "Column chart of daily feeds with volume overlay.",
  "It counts how often and how much the baby fed each day, so tired parents have real numbers for the doctor.",
  R(HUCK), FM_APP, FM_DS)

U("23", "Baby Sleep Pattern and Longest Stretch", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=baby:sleep\n"
  "| bin _time span=1d\n"
  "| stats sum(duration_min) as total_min, max(duration_min) as longest by _time\n"
  "| eval total_h=round(total_min/60,1), longest_h=round(longest/60,1)\n"
  "| sort - _time",
  "Trends how much a baby slept each day and the longest unbroken stretch, the number every exhausted parent watches most.",
  "The longest sleep stretch is the truest sign of progress toward sleeping through; trending it turns hope into visible improvement.",
  "Log sleep sessions to `index=personal`; schedule daily and review total sleep and the longest stretch.",
  "Line chart of daily total sleep with the longest stretch.",
  "It tracks how much the baby slept and the longest they went without waking, which every tired parent watches closely.",
  R(HUCK), FM_APP, FM_DS)

U("23", "Diaper-Change Log and Health Signal", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=diaper:change\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(type=\"wet\",1,0))) as wet, sum(eval(if(type=\"dirty\",1,0))) as dirty by _time\n"
  "| eval low_wet=if(wet<6,1,0)\n"
  "| sort - _time",
  "Counts daily wet and dirty nappies, a simple but genuine indicator of a newborn's hydration and feeding.",
  "Too few wet nappies is an early dehydration warning parents are told to watch; a running count makes it hard to miss.",
  "Log diaper changes to `index=personal`; schedule daily and flag days with unusually few wet nappies.",
  "Column chart of daily wet versus dirty nappies.",
  "It counts the baby's nappies each day, which is a simple way to check they are feeding and hydrated well.",
  R(HUCK), FM_APP, FM_DS)

U("23", "Child Growth Percentile Tracking", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=growth:measurement\n"
  "| stats latest(weight_kg) as weight, latest(height_cm) as height, latest(percentile) as pct by child metric\n"
  "| sort child metric",
  "Tracks a child's weight and height against standard growth percentiles so you can see steady progress along their own curve.",
  "Healthy growth follows a consistent percentile; plotting it yourself brings reassurance between paediatric visits.",
  "Record measurements against WHO percentiles into `index=personal`; review each child's growth curve over time.",
  "Line chart of growth percentile over time per child.",
  "It tracks your child's height and weight against normal ranges, so you can see they are growing steadily.",
  R(WHO_GROWTH), FM_APP, FM_DS)

U("23", "Chore Completion Leaderboard", "low", "beginner", ["Business"],
  "index=personal sourcetype=chore:completion\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as done, count as assigned by person _time\n"
  "| eval rate=round(100*done/assigned)\n"
  "| stats avg(rate) as completion by person\n"
  "| sort - completion",
  "Ranks who in the household actually finished their chores each week, a friendly (or fierce) family leaderboard.",
  "A visible chore scoreboard motivates kids far better than nagging and settles the eternal who-does-more debate with data.",
  "Log chore completions to `index=personal`; schedule weekly and rank family members by completion rate.",
  "Bar chart of chore completion rate by person.",
  "It shows who in the family actually did their chores each week, which is a fun and motivating scoreboard.",
  R(("Home Assistant — to-do list", "https://www.home-assistant.io/integrations/todo/")), FM_APP, FM_DS)

U("23", "Kids' Allowance and Savings Ledger", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=allowance:ledger\n"
  "| stats sum(eval(if(amount>0,amount,0))) as earned, sum(eval(if(amount<0,abs(amount),0))) as spent by child\n"
  "| eval balance=earned-spent\n"
  "| sort - balance",
  "Keeps a running balance of each child's pocket money, earnings, and spending to teach saving with a real ledger.",
  "A visible balance turns allowance into a lesson; kids grasp saving and spending far faster when they can watch it add up.",
  "Log allowance and purchases to `index=personal`; review each child's earned, spent, and balance.",
  "Bar chart of balance by child with earned and spent.",
  "It keeps track of each child's pocket money, what they earned and spent, to help them learn about saving.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), FM_APP, FM_DS)

U("23", "Family Calendar Load and Clash Detection", "low", "intermediate", ["Capacity"],
  "index=personal sourcetype=family:calendar\n"
  "| bin _time span=1d\n"
  "| stats count as events, dc(person) as people by _time\n"
  "| eval busy=if(events>6,1,0)\n"
  "| sort - events",
  "Counts everyone's events per day to spot the over-scheduled days before the family logistics collapse.",
  "Modern family calendars overflow silently; a daily load view flags the impossible days early enough to reschedule something.",
  "Ingest shared calendar events into `index=personal`; schedule daily and flag over-full days.",
  "Column chart of daily family events with a busy threshold.",
  "It counts everyone's activities each day to spot the over-busy days before the family runs itself ragged.",
  R(("Google Calendar — API", "https://developers.google.com/calendar/api")), FM_APP, FM_DS)

U("23", "Screen-Time Fairness Across Kids", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=screentime:usage\n"
  "| search person=*\n"
  "| bin _time span=1w\n"
  "| stats sum(minutes) as minutes by person _time\n"
  "| stats avg(minutes) as avg_weekly by person\n"
  "| eval hours=round(avg_weekly/60,1)\n"
  "| sort - hours",
  "Compares each child's weekly screen time so the family screen-time rules are applied evenly and arguments are settled with facts.",
  "Perceived unfairness drives sibling screen-time battles; an even comparison turns a shouting match into a calm agreement.",
  "Ingest per-child screen-time into `index=personal`; schedule weekly and compare hours across kids.",
  "Bar chart of average weekly screen hours by child.",
  "It compares how much screen time each child gets, so the rules feel fair and there are fewer arguments.",
  R(("Android — Family Link", "https://families.google/familylink/")), FM_APP, FM_DS)

U("23", "Bedtime Routine Adherence", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=baby:sleep event=bedtime\n"
  "| eval target=1230, actual=strftime(_time,\"%H%M\"), late=if(actual>2100,1,0)\n"
  "| bin _time span=1w\n"
  "| stats sum(late) as late_nights, count as nights by _time\n"
  "| eval on_time_pct=round(100*(nights-late_nights)/nights)",
  "Tracks how consistently the kids actually got to bed on time each week, the quiet foundation of a calmer household.",
  "Consistent bedtimes improve everyone's mood and sleep; measuring adherence keeps the routine honest when life gets busy.",
  "Log bedtimes to `index=personal`; schedule weekly and review on-time nights.",
  "Column chart of on-time bedtime percentage per week.",
  "It tracks how often the children actually got to bed on time, which makes for a calmer home.",
  R(HUCK), FM_APP, FM_DS)

U("23", "Household Task Backlog Burn-Down", "low", "intermediate", ["Operations"],
  "index=personal sourcetype=chore:completion\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(status=\"added\",1,0))) as added, sum(eval(if(status=\"done\",1,0))) as done by _time\n"
  "| streamstats sum(added) as total_added, sum(done) as total_done\n"
  "| eval backlog=total_added-total_done\n"
  "| sort - _time",
  "Tracks the household to-do backlog rising and falling over time, treating home chores like a project sprint.",
  "A growing backlog is the early sign the household is falling behind; a burn-down makes it visible before the clutter wins.",
  "Log task additions and completions into `index=personal`; schedule daily and trend the open backlog.",
  "Area chart of household task backlog over time.",
  "It shows whether the household to-do list is growing or shrinking, so chores never quietly pile up.",
  R(("Home Assistant — to-do list", "https://www.home-assistant.io/integrations/todo/")), FM_APP, FM_DS)

U("23", "New-Parent Sleep Debt Estimate", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=baby:sleep event=parent_sleep\n"
  "| bin _time span=1d\n"
  "| stats sum(duration_min) as slept_min by _time\n"
  "| eval slept_h=round(slept_min/60,1), deficit_h=round(8-slept_h,1)\n"
  "| sort - _time",
  "Estimates how far below a full night's rest the parents fell each day, quantifying the newborn sleep-debt everyone jokes about.",
  "Sleep debt affects mood and safety; seeing it plainly helps parents plan naps and share night duties more fairly.",
  "Log parents' sleep to `index=personal`; schedule daily and estimate the deficit against a target.",
  "Column chart of daily parent sleep with the deficit to target.",
  "It estimates how much sleep the parents are missing each day, putting real numbers on newborn exhaustion.",
  R(HUCK), FM_APP, FM_DS)


# ===========================================================================
# 25.24  Homestead, Bees & Livestock
# ===========================================================================
HS_APP = ("Homestead sensors — connected beehive scale/temperature/sound, automatic chicken-coop "
          "door, egg counter, livestock GPS/health tags, feed-silo level, and pasture soil "
          "sensors — streamed to Splunk HEC via MQTT and LoRaWAN gateways.")
HS_DS = ("Beehive telemetry (`beehive:reading`), coop door (`chickencoop:door`), egg counts "
         "(`egg:count`), livestock tags (`livestock:tag`), feed level (`feed:level`), pasture "
         "sensors (`pasture:sensor`).")
BEEP = ("BEEP — open beehive monitoring", "https://beep.nl/")
LORAWAN = ("The Things Network — LoRaWAN", "https://www.thethingsnetwork.org/")

U("24", "Beehive Weight Nectar-Flow and Swarm Alert", "low", "advanced", ["Analytics", "Anomaly"],
  "index=personal sourcetype=beehive:reading\n"
  "| timechart span=1h avg(weight_kg) as weight\n"
  "| streamstats current=f last(weight) as prev\n"
  "| eval change=weight-prev, sudden_drop=if(change<-1.5,1,0)",
  "Watches hive weight to see nectar coming in day by day and flags a sudden drop that can signal a swarm leaving.",
  "Hive weight is the beekeeper's vital sign; it reveals nectar flow, stores for winter, and the abrupt loss that means a swarm.",
  "Feed a hive scale into `index=personal`; review the weight trend and alert on a sudden large drop.",
  "Time chart of hive weight with sudden-drop markers.",
  "It watches how heavy the beehive is to see honey building up and warns if the bees suddenly swarm away.",
  R(BEEP), HS_APP, HS_DS)

U("24", "Beehive Temperature and Colony Health", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=beehive:reading\n"
  "| timechart span=30m avg(brood_temp_c) as brood\n"
  "| eval unhealthy=if(brood<33 OR brood>36,1,0)",
  "Trends the brood-nest temperature bees work hard to keep steady, where a drift signals a struggling or queenless colony.",
  "A healthy colony holds brood temperature in a tight band; a persistent drift is an early, non-invasive sign something is wrong.",
  "Ingest brood-nest temperature into `index=personal`; alert when it drifts outside the healthy band.",
  "Time chart of brood temperature with a healthy band.",
  "It watches the temperature inside the hive, which healthy bees keep very steady, warning if something is wrong.",
  R(BEEP), HS_APP, HS_DS)

U("24", "Beehive Acoustic Activity Pattern", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=beehive:reading\n"
  "| timechart span=1h avg(sound_db) as buzz\n"
  "| eval hour=strftime(_time,\"%H\")",
  "Trends the hum of the hive through the day, a window into foraging activity and the colony's changing mood.",
  "Hive sound reflects activity and stress; watching its daily rhythm adds a non-invasive dimension no scale or thermometer captures.",
  "Ingest a hive microphone level into `index=personal`; review the daily buzz pattern.",
  "Line chart of hive sound level over the day.",
  "It listens to how loudly the hive is buzzing through the day, which hints at how busy and happy the bees are.",
  R(BEEP), HS_APP, HS_DS)

U("24", "Chicken Coop Auto-Door Audit", "medium", "beginner", ["Availability"],
  "index=personal sourcetype=chickencoop:door\n"
  "| stats latest(state) as state, latest(_time) as last_action, latest(sunset_epoch) as sunset\n"
  "| eval closed_after_dark=if(state=\"closed\" AND last_action>sunset,1,0), risk=if(state=\"open\" AND now()>sunset+1800,1,0)",
  "Confirms the automatic coop door actually closed after dusk, the difference between safe hens and a fox's easy dinner.",
  "A coop door that fails to close is discovered only after a predator gets in; a nightly confirmation prevents heartbreak.",
  "Ingest coop-door events into `index=personal`; alert if the door is still open well after sunset.",
  "Status panel of door state with a post-sunset risk flag.",
  "It checks the automatic chicken-coop door really closed at dusk, keeping the hens safe from foxes.",
  R(("Home Assistant — cover", "https://www.home-assistant.io/integrations/cover/")), HS_APP, HS_DS)

U("24", "Daily Egg Count and Laying-Rate Trend", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=egg:count\n"
  "| timechart span=1d sum(eggs) as eggs\n"
  "| eventstats avg(eggs) as flock_avg\n"
  "| eval below_normal=if(eggs<flock_avg*0.6,1,0)",
  "Trends how many eggs the flock lays each day and flags a sudden drop that can mean stress, illness, or a hidden nest.",
  "A laying-rate dip is often the first sign of a flock problem; trending it catches trouble long before you would notice by eye.",
  "Log daily egg counts into `index=personal`; alert when the count falls well below the flock's normal.",
  "Column chart of daily egg count with the flock average.",
  "It tracks how many eggs your hens lay each day and warns of a sudden drop, which can mean they are unwell.",
  R(("Home Assistant — counter", "https://www.home-assistant.io/integrations/counter/")), HS_APP, HS_DS)

U("24", "Livestock GPS Fence and Straying Alert", "medium", "intermediate", ["Safety", "Anomaly"],
  "index=personal sourcetype=livestock:tag\n"
  "| stats latest(distance_from_center_m) as dist, latest(_time) as seen by animal\n"
  "| eval strayed=if(dist>pasture_radius_m,1,0), silent=if((now()-seen)>7200,1,0)\n"
  "| where strayed=1 OR silent=1",
  "Alerts when a tagged animal wanders beyond the pasture or a tag goes silent, so a break in the fence is caught quickly.",
  "A single strayed animal can mean a downed fence and a lost flock; a location and heartbeat check turns hours of searching into minutes.",
  "Ingest livestock GPS tags into `index=personal`; alert when an animal leaves the pasture or stops reporting.",
  "Table of animals outside the fence or gone quiet.",
  "It warns you if an animal wanders out of the field or its tracker goes quiet, so you find a broken fence fast.",
  R(LORAWAN), HS_APP, HS_DS)

U("24", "Feed and Water Supply Runway", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=feed:level\n"
  "| stats latest(level_pct) as level, avg(daily_use_pct) as usage by silo\n"
  "| eval days_left=round(level/usage,1)\n"
  "| where days_left<7\n"
  "| sort days_left",
  "Estimates how many days of feed remain in each silo or bin so a delivery is ordered before the animals go hungry.",
  "Running out of feed is not an option on a homestead; a usage-based runway makes reordering timely instead of frantic.",
  "Ingest feed-level sensors into `index=personal`; schedule daily and flag supplies running low.",
  "Table of feed silos by days of supply remaining.",
  "It works out how many days of animal feed you have left, so you reorder before running out.",
  R(LORAWAN), HS_APP, HS_DS)

U("24", "Pasture Soil-Moisture and Grazing Readiness", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=pasture:sensor\n"
  "| stats avg(soil_moisture_pct) as moisture, avg(soil_temp_c) as temp by paddock\n"
  "| eval growing=if(moisture>25 AND temp>8,\"growing\",\"resting\")\n"
  "| sort - moisture",
  "Tracks soil moisture and temperature across paddocks to judge which are growing grass and ready to graze.",
  "Rotational grazing depends on grass recovery; measuring paddock conditions helps move stock at the right time for healthy pasture.",
  "Ingest pasture soil sensors into `index=personal`; review moisture and temperature by paddock.",
  "Bar chart of soil moisture by paddock with a growing indicator.",
  "It checks how moist and warm the soil is in each field, so you know which are ready for animals to graze.",
  R(LORAWAN), HS_APP, HS_DS)

U("24", "Honey Harvest Yield by Hive and Season", "low", "beginner", ["Business"],
  "index=personal sourcetype=beehive:reading event=harvest\n"
  "| bin _time span=1mon\n"
  "| stats sum(harvest_kg) as honey by hive _time\n"
  "| stats sum(honey) as total by hive\n"
  "| sort - total",
  "Totals the honey harvested from each hive across the season, revealing your strongest colonies and best-producing sites.",
  "Comparing yield per hive guides which colonies to split and where to place hives, turning beekeeping into informed husbandry.",
  "Log harvest weights into `index=personal`; schedule seasonally and total honey per hive.",
  "Bar chart of honey harvested by hive.",
  "It adds up how much honey each hive produced, showing which of your colonies are the strongest.",
  R(BEEP), HS_APP, HS_DS)

U("24", "Predator Activity Near Coop and Pasture", "medium", "intermediate", ["Security"],
  "index=personal sourcetype=trailcam:detection (label=fox OR label=coyote OR label=raccoon OR label=hawk)\n"
  "| bin _time span=1d\n"
  "| stats count as sightings by label _time\n"
  "| sort - _time",
  "Counts predator sightings from trail cameras around the coop and pasture, revealing when and what is casing your animals.",
  "Predators scout before they strike; knowing which species appear and when lets you reinforce defences before you lose stock.",
  "Feed trail-camera detections into `index=personal`; schedule daily and review predator activity by species.",
  "Column chart of predator sightings by species over time.",
  "It counts foxes and other predators your cameras spot near the animals, so you can protect them before an attack.",
  R(LORAWAN), HS_APP, HS_DS, pillar="Security")


# ===========================================================================
# 25.25  Advanced Health & Biohacking
# ===========================================================================
BH_APP = ("Biohacking and advanced-health data — HRV chest straps, pulse oximeters, blood-pressure "
          "cuffs, continuous glucose monitors, body-composition scales, lab-result exports, and "
          "supplement logs — ingested to Splunk HEC via APIs and scripted inputs.")
BH_DS = ("HRV (`hrv:reading`), blood oxygen (`spo2:reading`), lab panels (`bloodpanel:result`), "
         "supplements (`supplement:intake`), continuous glucose (`cgm:glucose`), sleep-apnea "
         "events (`apnea:event`), body composition (`bodycomp:measure`).")
QS = ("Quantified Self — self-tracking community", "https://quantifiedself.com/")

U("25", "Heart-Rate Variability Recovery Baseline", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=hrv:reading\n"
  "| timechart span=1d avg(rmssd_ms) as hrv\n"
  "| eventstats avg(hrv) as base, stdev(hrv) as sd\n"
  "| eval suppressed=if(hrv<base-sd,1,0)",
  "Tracks morning heart-rate variability against your personal baseline to flag the low-recovery days worth taking easy.",
  "A suppressed HRV is an early, objective sign of fatigue, stress, or oncoming illness, letting you adjust training before you crash.",
  "Ingest morning HRV readings into `index=personal`; alert on readings well below your rolling baseline.",
  "Line chart of daily HRV with a personal baseline band.",
  "It measures a heart signal each morning that shows how recovered you are, flagging days you should take it easy.",
  R(QS), BH_APP, BH_DS)

U("25", "Overnight Blood-Oxygen Dip Detection", "high", "advanced", ["Safety", "Anomaly"],
  "index=personal sourcetype=spo2:reading\n"
  "| bin _time span=1d\n"
  "| stats min(spo2) as lowest, sum(eval(if(spo2<90,1,0))) as dips by _time\n"
  "| where dips>5\n"
  "| sort - _time",
  "Counts overnight drops in blood oxygen that can point to disrupted breathing during sleep, a signal worth discussing with a doctor.",
  "Frequent nightly oxygen dips are a hallmark of sleep-disordered breathing; surfacing them can prompt a proper medical evaluation.",
  "Ingest overnight pulse-oximeter data into `index=personal`; schedule each morning and flag nights with many dips.",
  "Time chart of overnight oxygen with dip counts per night.",
  "It counts the times your blood oxygen dips at night, which can be a sign of breathing trouble worth checking with a doctor.",
  R(QS), BH_APP, BH_DS)

U("25", "Continuous-Glucose Meal Response", "medium", "advanced", ["Analytics"],
  "index=personal sourcetype=cgm:glucose\n"
  "| eventstats avg(glucose_mg_dl) as day_avg\n"
  "| eval spike=if(glucose_mg_dl>day_avg+40,1,0)\n"
  "| timechart span=15m avg(glucose_mg_dl) as glucose, max(spike) as spiked",
  "Charts how your glucose responds through the day so you can learn which meals send it spiking and which keep it steady.",
  "Even without diabetes, glucose spikes affect energy and hunger; seeing your own responses guides genuinely personal food choices.",
  "Ingest continuous-glucose data into `index=personal`; review the daily curve and flag post-meal spikes.",
  "Time chart of glucose with meal-spike markers.",
  "It shows how your blood sugar rises and falls through the day, revealing which foods spike it and which keep it steady.",
  R(QS), BH_APP, BH_DS)

U("25", "Resting Blood-Pressure Trend and Alert", "high", "beginner", ["Anomaly"],
  "index=personal sourcetype=bloodpressure:reading\n"
  "| timechart span=1d avg(systolic) as sys, avg(diastolic) as dia\n"
  "| eval elevated=if(sys>135 OR dia>85,1,0)",
  "Trends your resting blood pressure over time and flags a sustained rise into the range that warrants attention.",
  "A single reading is noisy; a trend reveals genuine change and gives your doctor far more to work with than an occasional check.",
  "Ingest cuff readings into `index=personal`; schedule daily and alert on a sustained elevation.",
  "Line chart of daily blood pressure with a threshold band.",
  "It tracks your blood pressure over time and flags if it stays higher than it should, so you can see a doctor early.",
  R(("WHO — hypertension", "https://www.who.int/news-room/fact-sheets/detail/hypertension")), BH_APP, BH_DS)

U("25", "Body-Composition Change Over Time", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=bodycomp:measure\n"
  "| timechart span=1w avg(weight_kg) as weight, avg(body_fat_pct) as fat, avg(muscle_kg) as muscle",
  "Trends weight, body-fat percentage, and muscle mass together so progress shows up as body change, not just a scale number.",
  "The scale alone misleads; trending fat and muscle separately shows whether a plan is actually recomposing your body.",
  "Ingest smart-scale body-composition data into `index=personal`; review weekly trends of weight, fat, and muscle.",
  "Multi-line chart of weight, body fat, and muscle over time.",
  "It tracks not just your weight but your muscle and fat, so you see real body changes rather than one number.",
  R(QS), BH_APP, BH_DS)

U("25", "Lab-Panel Biomarker Trend", "medium", "intermediate", ["Analytics"],
  "index=personal sourcetype=bloodpanel:result\n"
  "| stats latest(value) as latest, earliest(value) as first, latest(ref_high) as high, latest(ref_low) as low by marker\n"
  "| eval out_of_range=if(latest>high OR latest<low,1,0)\n"
  "| sort - out_of_range",
  "Trends your blood-test biomarkers across panels and flags any outside the reference range, building a personal health history.",
  "Single lab reports are snapshots; trending markers over years reveals slow drifts and gives context no one-off result can.",
  "Ingest lab results into `index=personal`; review each biomarker's trend and flag out-of-range values.",
  "Table of biomarkers with latest value, trend, and range flag.",
  "It keeps a history of your blood-test results over time, so slow changes and out-of-range values are easy to see.",
  R(QS), BH_APP, BH_DS)

U("25", "Supplement and Medication Adherence", "medium", "beginner", ["Compliance"],
  "index=personal sourcetype=supplement:intake\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(taken=\"true\",1,0))) as taken, count as scheduled by item _time\n"
  "| eval adherence=round(100*taken/scheduled)\n"
  "| stats avg(adherence) as avg_adherence by item\n"
  "| sort avg_adherence",
  "Measures how reliably you actually take each supplement or medication, so a forgotten dose does not undermine the whole regimen.",
  "Adherence, not the plan, determines results and safety; a per-item rate shows exactly which one you keep forgetting.",
  "Log intake to `index=personal`; schedule weekly and rank items by adherence.",
  "Bar chart of adherence rate by supplement or medication.",
  "It tracks how reliably you take each supplement or medicine, so you can see which one you keep forgetting.",
  R(QS), BH_APP, BH_DS)

U("25", "Sleep-Apnea Event Frequency", "high", "advanced", ["Anomaly"],
  "index=personal sourcetype=apnea:event\n"
  "| bin _time span=1d\n"
  "| stats count as events, sum(sleep_hours) as hours by _time\n"
  "| eval ahi=round(events/hours,1), severe=if(ahi>15,1,0)\n"
  "| sort - _time",
  "Estimates a nightly apnea-events-per-hour index from your monitor so disrupted breathing is quantified over time.",
  "A rising events-per-hour index is exactly what sleep clinics measure; tracking it at home can motivate and inform proper diagnosis.",
  "Ingest apnea-event data into `index=personal`; schedule each morning and trend the events-per-hour index.",
  "Line chart of nightly apnea index with a severity threshold.",
  "It estimates how often your breathing was interrupted per hour of sleep, a number sleep doctors care about.",
  R(QS), BH_APP, BH_DS)

U("25", "Illness Early-Warning Composite", "medium", "advanced", ["Anomaly"],
  "index=personal (sourcetype=hrv:reading OR sourcetype=whoop:cycle OR sourcetype=oura:daily)\n"
  "| bin _time span=1d\n"
  "| stats avg(rmssd_ms) as hrv, avg(resting_hr) as rhr, avg(skin_temp_dev_c) as temp_dev by _time\n"
  "| eventstats avg(hrv) as hrv_base, avg(rhr) as rhr_base\n"
  "| eval warning=if(hrv<hrv_base*0.8 AND rhr>rhr_base+3 AND temp_dev>0.3,1,0)",
  "Combines a dropping HRV, rising resting heart rate, and raised skin temperature into a single you-might-be-getting-sick signal.",
  "These three signs shift a day or two before symptoms; combining them catches an oncoming illness while rest can still help.",
  "Ingest recovery metrics into `index=personal`; schedule daily and alert when all three point the wrong way at once.",
  "Multi-metric panel with a combined illness-warning flag.",
  "It combines several body signals that change before you feel ill, giving you a heads-up to rest before a cold takes hold.",
  R(QS), BH_APP, BH_DS)

U("25", "Caffeine-Timing vs Sleep-Quality Correlation", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=espresso:shot OR sourcetype=oura:daily)\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(strftime(_time,\"%H\")>=14,caffeine_mg,0))) as late_caffeine, avg(sleep_score) as sleep by _time\n"
  "| eval high_late=if(late_caffeine>100,1,0)\n"
  "| stats avg(sleep) as avg_sleep by high_late",
  "Compares your sleep quality on days with and without late-afternoon caffeine, testing the advice on your own body.",
  "Generic caffeine advice may not fit you; comparing your own late-caffeine days to the rest gives a personal, convincing answer.",
  "Ingest caffeine timing and sleep scores into `index=personal`; compare average sleep by whether you had late caffeine.",
  "Bar chart of average sleep score with versus without late caffeine.",
  "It compares how well you sleep on days you had afternoon coffee versus days you did not, testing the advice on you.",
  R(QS), BH_APP, BH_DS)


# ===========================================================================
# 25.26  Wildlife & Biodiversity
# ===========================================================================
WL_APP = ("Backyard wildlife monitoring — BirdNET acoustic bird ID, trail cameras with object "
          "detection, camera moth traps, ultrasonic bat detectors, and pollinator counts — "
          "streamed to Splunk HEC via MQTT and scripted inputs.")
WL_DS = ("BirdNET detections (`birdnet:detection`), trail-cam detections (`trailcam:detection`), "
         "moth-trap captures (`mothtrap:capture`), bat-detector passes (`batdetector:pass`), "
         "pollinator counts (`pollinator:count`), wildlife-cam visits (`wildlifecam:visit`).")
BIRDNET = ("BirdNET — acoustic bird identification", "https://birdnet.cornell.edu/")
INAT = ("iNaturalist — biodiversity observations", "https://www.inaturalist.org/")

U("26", "Backyard Bird Species Diversity", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=birdnet:detection confidence>0.7\n"
  "| bin _time span=1d\n"
  "| stats dc(species) as species, count as calls by _time\n"
  "| sort - _time",
  "Counts how many distinct bird species your acoustic monitor hears each day, tracking the biodiversity of your own garden.",
  "A daily species count turns a bird-call recorder into a living biodiversity log, revealing seasonal arrivals and departures.",
  "Feed BirdNET detections into `index=personal`; schedule daily and count distinct species heard.",
  "Column chart of daily species diversity with call counts.",
  "It counts how many different kinds of birds your microphone hears each day, tracking the wildlife in your garden.",
  R(BIRDNET), WL_APP, WL_DS)

U("26", "First-of-Season and Rare Bird Alert", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=birdnet:detection confidence>0.85\n"
  "| stats earliest(_time) as first_heard, count as detections by species\n"
  "| eval brand_new=if(first_heard>relative_time(now(),\"-2d\"),1,0), rare=if(detections<=2,1,0)\n"
  "| where brand_new=1 OR rare=1\n"
  "| sort - first_heard",
  "Flags the first appearance of a migratory species and the rarely heard visitors, the highlights every garden birder waits for.",
  "First-of-season and rare detections are the exciting moments; surfacing them automatically means you never miss a notable visitor.",
  "Ingest high-confidence BirdNET detections; alert on newly heard or seldom-heard species.",
  "Table of new-of-season and rare species with first-heard time.",
  "It tells you when a new migrating bird arrives for the season or a rare one visits, the highlights for bird lovers.",
  R(BIRDNET), WL_APP, WL_DS)

U("26", "Dawn-Chorus Activity Peak", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=birdnet:detection\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats count as calls by hour\n"
  "| sort hour",
  "Maps bird-call activity by hour to reveal the dawn chorus peak and the quieter middle of the day.",
  "The dawn chorus is a delight; charting call activity by hour shows exactly when your garden is most alive with birdsong.",
  "Ingest BirdNET detections; review call counts by hour of day.",
  "Column chart of bird-call activity by hour of day.",
  "It shows what time of day the birds sing most, capturing the lovely dawn chorus in your garden.",
  R(BIRDNET), WL_APP, WL_DS)

U("26", "Trail-Camera Wildlife Visitor Log", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=trailcam:detection\n"
  "| bin _time span=1d\n"
  "| stats count as visits by label _time\n"
  "| stats sum(visits) as total by label\n"
  "| sort - total",
  "Tallies which wild animals your trail cameras record and how often, building a picture of who shares your land.",
  "A visitor log turns scattered clips into an ecology of your property, revealing the deer, foxes, and badgers passing through.",
  "Feed trail-cam detections into `index=personal`; schedule daily and rank species by visits.",
  "Bar chart of wildlife visits by species.",
  "It counts which wild animals your outdoor cameras record, showing who visits your garden at night.",
  R(INAT), WL_APP, WL_DS)

U("26", "Nocturnal Wildlife Activity Clock", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=trailcam:detection\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats count as detections by label hour\n"
  "| sort label hour",
  "Maps when each species is active through the night, revealing the hidden schedule of your local nocturnal wildlife.",
  "Different animals own different hours; an activity clock per species is a fascinating, genuinely scientific view of your patch.",
  "Ingest trail-cam detections; review activity by species and hour.",
  "Heatmap of wildlife activity by species and hour.",
  "It shows what time of night each animal is active, revealing the secret schedule of your local wildlife.",
  R(INAT), WL_APP, WL_DS)

U("26", "Moth-Trap Capture Diversity", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=mothtrap:capture\n"
  "| bin _time span=1d\n"
  "| stats dc(species) as species, sum(count) as moths by _time\n"
  "| sort - _time",
  "Counts the species and numbers a camera moth-trap records each night, a rich window into insect biodiversity.",
  "Moths are hugely diverse and easy to overlook; a nightly diversity count makes garden entomology approachable and data-rich.",
  "Feed camera moth-trap identifications into `index=personal`; schedule nightly and count species and totals.",
  "Column chart of nightly moth species and counts.",
  "It counts how many kinds of moths your special camera trap catches each night, a peek into the insect world.",
  R(INAT), WL_APP, WL_DS)

U("26", "Bat Detector Pass Activity", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=batdetector:pass\n"
  "| bin _time span=1h\n"
  "| stats count as passes, dc(species) as species by _time\n"
  "| sort - _time",
  "Counts bat passes and species from an ultrasonic detector through the evening, revealing your garden's after-dark aviators.",
  "Bats are near-invisible but vital; a pass count by hour makes their emergence and foraging a tangible part of your wildlife record.",
  "Ingest bat-detector passes into `index=personal`; review activity by hour and species through the night.",
  "Time chart of bat passes with species diversity.",
  "It counts the bats flying past a special microphone each evening, revealing the creatures active after dark.",
  R(("Bat Conservation Trust — monitoring", "https://www.bats.org.uk/")), WL_APP, WL_DS)

U("26", "Pollinator Visit Count by Plant", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=pollinator:count\n"
  "| stats sum(visits) as visits by plant pollinator\n"
  "| sort - visits",
  "Counts bee and butterfly visits to different flowers so you learn which plants best support pollinators in your garden.",
  "Choosing pollinator-friendly plants is guesswork without data; visit counts show which flowers actually earn their place.",
  "Log pollinator observations into `index=personal`; review visits by plant and pollinator type.",
  "Bar chart of pollinator visits by plant.",
  "It counts how many bees and butterflies visit each type of flower, so you plant the ones they love most.",
  R(INAT), WL_APP, WL_DS)

U("26", "Bird-Feeder Squirrel-Raid Detection", "low", "beginner", ["Anomaly"],
  "index=personal sourcetype=wildlifecam:visit location=feeder\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(label=\"squirrel\",1,0))) as raids, sum(eval(if(label=\"bird\",1,0))) as birds by _time\n"
  "| sort - _time",
  "Counts squirrel raids on the bird feeder versus genuine bird visits, quantifying the eternal backyard battle.",
  "Squirrels empty feeders fast; a daily raid count tells you whether a baffle is working and how much seed the squirrels steal.",
  "Feed feeder-cam detections into `index=personal`; schedule daily and compare squirrel raids to bird visits.",
  "Column chart of daily squirrel raids versus bird visits.",
  "It counts how often squirrels raid the bird feeder versus real bird visits, tracking that classic garden battle.",
  R(INAT), WL_APP, WL_DS)

U("26", "Seasonal Biodiversity Index", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=birdnet:detection OR sourcetype=trailcam:detection OR sourcetype=mothtrap:capture)\n"
  "| bin _time span=1mon\n"
  "| stats dc(species) as species by _time\n"
  "| sort - _time",
  "Combines birds, mammals, and moths into a monthly count of distinct species, a single index of your patch's biodiversity.",
  "A combined species index across taxa is a powerful, motivating measure of whether your rewilding or planting is working.",
  "Ingest detections across sensors into `index=personal`; schedule monthly and count total distinct species.",
  "Line chart of monthly distinct species across all sensors.",
  "It combines birds, animals, and insects into one monthly count of how many species share your garden.",
  R(INAT), WL_APP, WL_DS)


# ===========================================================================
# 25.27  Aquariums, Reptiles & Vivariums
# ===========================================================================
AQ_APP = ("Aquarium and vivarium controllers — reef-tank parameter monitors, auto-dosers, "
          "auto-top-off, reptile terrarium climate/UVB, and pond sensors — streamed to Splunk "
          "HEC via MQTT and controller APIs (e.g. Apex, GHL, ESPHome).")
AQ_DS = ("Reef-tank parameters (`reeftank:param`), vivarium climate (`vivarium:climate`), fish "
         "feeder (`fishfeeder:event`), auto-doser (`doser:event`), auto-top-off (`ato:event`), "
         "pond sensors (`pondsensor:reading`).")
APEX = ("Neptune Apex — aquarium controller", "https://www.neptunesystems.com/")
ARDUINO = ("Arduino — project hub", "https://projecthub.arduino.cc/")

U("27", "Reef-Tank Parameter Stability", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=reeftank:param\n"
  "| stats latest(temp_c) as temp, latest(ph) as ph, latest(salinity_ppt) as salinity\n"
  "| eval temp_ok=if(temp>=25 AND temp<=27,\"good\",\"check\"), ph_ok=if(ph>=7.9 AND ph<=8.4,\"good\",\"check\"), sal_ok=if(salinity>=34 AND salinity<=36,\"good\",\"check\")",
  "Checks the core reef parameters, temperature, pH, and salinity, stay inside the narrow bands corals need to thrive.",
  "Reef inhabitants are unforgiving of swings; a continuous stability check protects a living system that took months to build.",
  "Ingest controller parameters into `index=personal`; alert when temperature, pH, or salinity leaves its safe band.",
  "Status panel of temperature, pH, and salinity with safe bands.",
  "It checks the water in a reef tank stays just right for the corals, watching temperature, acidity, and saltiness.",
  R(APEX), AQ_APP, AQ_DS)

U("27", "Aquarium Temperature Heater-Failure Alert", "high", "beginner", ["Availability", "Anomaly"],
  "index=personal sourcetype=reeftank:param\n"
  "| timechart span=10m avg(temp_c) as temp\n"
  "| eval danger=if(temp<24 OR temp>28,1,0)",
  "Alerts fast when tank temperature drifts toward danger, the classic sign of a stuck-on or failed heater.",
  "A failed heater can cook or chill a tank within hours; an immediate temperature alert is the difference between a scare and a wipeout.",
  "Ingest tank temperature into `index=personal`; alert the moment it crosses a danger threshold.",
  "Time chart of tank temperature with danger thresholds.",
  "It quickly warns you if the fish-tank water gets too hot or cold, which usually means a broken heater.",
  R(APEX), AQ_APP, AQ_DS)

U("27", "Auto-Doser Reagent Runway", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=doser:event\n"
  "| stats latest(container_ml) as remaining, avg(daily_ml) as usage by reagent\n"
  "| eval days_left=round(remaining/usage,1)\n"
  "| where days_left<7\n"
  "| sort days_left",
  "Estimates how many days of each dosing reagent remain so a reef's chemistry never lapses because a bottle ran dry.",
  "Coral growth depends on steady dosing; a reagent runway means you refill before a gap stalls or harms the reef.",
  "Ingest doser events into `index=personal`; schedule daily and flag reagents running low.",
  "Table of dosing reagents by days of supply remaining.",
  "It works out how many days of the special reef chemicals are left, so you refill before the tank goes without.",
  R(APEX), AQ_APP, AQ_DS)

U("27", "Auto-Top-Off Water and Leak Watch", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=ato:event\n"
  "| bin _time span=1d\n"
  "| stats sum(topup_ml) as topped, count as cycles by _time\n"
  "| eventstats avg(topped) as usual\n"
  "| eval abnormal=if(topped>usual*2,1,0)",
  "Watches how much water the auto-top-off adds each day, flagging a spike that can mean a leak or runaway evaporation.",
  "A sudden jump in top-off volume is often the first sign of a leak or a stuck valve, caught here before the floor gets wet.",
  "Ingest top-off events into `index=personal`; schedule daily and alert on abnormal top-off volume.",
  "Column chart of daily top-off volume with a normal band.",
  "It watches how much water is automatically added to the tank, warning of a leak if it suddenly needs much more.",
  R(APEX), AQ_APP, AQ_DS)

U("27", "Fish-Feeder Confirmation and Overfeeding Guard", "low", "beginner", ["Availability"],
  "index=personal sourcetype=fishfeeder:event\n"
  "| bin _time span=1d\n"
  "| stats count as feeds by _time\n"
  "| eval status=case(feeds=0,\"missed\",feeds>3,\"overfed\",1=1,\"ok\")\n"
  "| sort - _time",
  "Confirms the automatic feeder ran the right number of times, catching both a missed meal and accidental overfeeding.",
  "A jammed feeder starves fish while a double-trigger fouls the water; a simple daily count keeps feeding just right.",
  "Ingest feeder events into `index=personal`; schedule daily and flag missed or excessive feeds.",
  "Column chart of daily feeds with a normal range.",
  "It checks the automatic fish feeder ran the right number of times, so the fish are neither missed nor overfed.",
  R(ARDUINO), AQ_APP, AQ_DS)

U("27", "Reptile Terrarium Climate and UVB", "medium", "intermediate", ["Safety"],
  "index=personal sourcetype=vivarium:climate\n"
  "| stats latest(basking_c) as basking, latest(cool_c) as cool, latest(humidity_pct) as humidity, latest(uvi) as uvi by enclosure\n"
  "| eval gradient_ok=if(basking>=32 AND cool<=26,\"good\",\"check\"), uvb_ok=if(uvi>=2,\"good\",\"low\")",
  "Checks a reptile's enclosure keeps a proper warm-to-cool gradient, humidity, and UVB, the essentials of reptile health.",
  "Reptiles depend entirely on their environment; monitoring the gradient and UVB prevents the slow health decline of poor husbandry.",
  "Ingest terrarium climate and UV index into `index=personal`; alert when the gradient, humidity, or UVB is off.",
  "Status panel of basking and cool temperatures, humidity, and UVB.",
  "It checks a reptile's tank has the right warm and cool areas, humidity, and special light it needs to stay healthy.",
  R(ARDUINO), AQ_APP, AQ_DS)

U("27", "Vivarium Misting and Humidity Cycle", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vivarium:climate\n"
  "| timechart span=30m avg(humidity_pct) as humidity, max(eval(if(misting=\"true\",1,0))) as misted by enclosure",
  "Trends humidity around each misting cycle so you can tune a tropical enclosure to hold the right damp without staying soggy.",
  "Correct humidity cycling prevents both dehydration and mould; seeing the misting effect lets you dial the schedule in precisely.",
  "Ingest humidity and misting events into `index=personal`; review how humidity responds to each cycle.",
  "Time chart of humidity with misting events marked.",
  "It shows how the humidity rises and falls with each misting, so you keep a tropical tank damp but not soggy.",
  R(ARDUINO), AQ_APP, AQ_DS)

U("27", "Garden Pond Oxygen and Temperature", "medium", "intermediate", ["Safety"],
  "index=personal sourcetype=pondsensor:reading\n"
  "| timechart span=1h avg(do_mg_l) as oxygen, avg(temp_c) as temp\n"
  "| eval low_oxygen=if(oxygen<5,1,0)",
  "Watches dissolved oxygen and temperature in a garden pond, flagging the hot, still nights when fish can suffocate.",
  "Warm water holds less oxygen; a low-oxygen alert on summer nights can save a pond full of fish from a silent die-off.",
  "Ingest pond sensors into `index=personal`; alert when dissolved oxygen falls too low.",
  "Time chart of pond oxygen and temperature with a low-oxygen line.",
  "It watches the oxygen and warmth in a garden pond, warning on hot nights when fish might struggle to breathe.",
  R(ARDUINO), AQ_APP, AQ_DS)

U("27", "Tank Equipment Uptime and Pump Health", "medium", "intermediate", ["Availability"],
  "index=personal sourcetype=reeftank:param\n"
  "| stats latest(return_pump_w) as return_pump, latest(skimmer_w) as skimmer, latest(_time) as seen\n"
  "| eval pump_off=if(return_pump<5,1,0), stale=if((now()-seen)>600,1,0)",
  "Confirms the return pump and skimmer are drawing power and the controller is reporting, catching a stopped pump fast.",
  "A stopped return pump crashes oxygen and flow within an hour; power monitoring catches the failure the controller state might hide.",
  "Ingest equipment power draw into `index=personal`; alert when the return pump stops or telemetry goes stale.",
  "Status panel of pump and skimmer power with a health flag.",
  "It checks the tank's pumps are actually running, so a stopped pump is caught before the fish are harmed.",
  R(APEX), AQ_APP, AQ_DS)

U("27", "Water-Change and Maintenance Cadence", "low", "beginner", ["Operations"],
  "index=personal sourcetype=reeftank:param event=maintenance\n"
  "| stats latest(_time) as last_change by task tank\n"
  "| eval days_since=round((now()-last_change)/86400,1), overdue=if(days_since>14,1,0)\n"
  "| sort - days_since",
  "Tracks when each tank last had a water change or filter clean so routine maintenance does not quietly slip.",
  "Skipped water changes are the top cause of tank trouble; a cadence tracker keeps the boring-but-essential jobs on schedule.",
  "Log maintenance events into `index=personal`; schedule weekly and flag overdue tasks per tank.",
  "Table of maintenance tasks by days since last done.",
  "It tracks when you last cleaned or changed the tank water, so the important routine jobs do not get forgotten.",
  R(APEX), AQ_APP, AQ_DS)


# ===========================================================================
# 25.28  Sports, Skills & Training Telemetry
# ===========================================================================
SP_APP = ("Sports and skill sensors — velocity-based-training bar trackers, running-form IMUs, "
          "climbing hangboard load cells, golf launch monitors, cycling power meters, and "
          "computer-vision shot trackers — logged to Splunk HEC via APIs and scripted inputs.")
SP_DS = ("Bar-velocity reps (`vbt:rep`), running gait (`gait:metric`), hangboard sessions "
         "(`hangboard:session`), golf-swing metrics (`golfswing:metric`), power-meter intervals "
         "(`powermeter:interval`), basketball shot arcs (`shotarc:make`).")
TP = ("TrainingPeaks — training analytics", "https://www.trainingpeaks.com/")
GC = ("GoldenCheetah — open cycling analytics", "https://www.goldencheetah.org/")

U("28", "Velocity-Based-Training Bar-Speed Autoregulation", "low", "advanced", ["Performance"],
  "index=personal sourcetype=vbt:rep\n"
  "| stats avg(mean_velocity) as avg_v, max(mean_velocity) as best_v, count as reps by exercise load_kg\n"
  "| eval velocity_loss=round(100*(best_v-avg_v)/best_v,1)\n"
  "| sort exercise load_kg",
  "Tracks bar speed across a lifting set so you can stop when velocity drops, training hard without grinding into junk fatigue.",
  "Velocity loss is a live fatigue gauge; autoregulating by bar speed builds strength while avoiding the reps that only add risk.",
  "Ingest bar-velocity reps into `index=personal`; review velocity loss per exercise and load to set stopping points.",
  "Bar chart of velocity loss by exercise and load.",
  "It measures how fast you lift the bar and when it slows down, so you stop a set at the right time.",
  R(TP), SP_APP, SP_DS)

U("28", "Estimated One-Rep-Max Trend", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vbt:rep\n"
  "| eval est_1rm=round(load_kg*(1+reps/30),1)\n"
  "| timechart span=1w max(est_1rm) as best_1rm by exercise",
  "Trends your estimated one-rep max for each lift so strength progress is visible without risky max-out attempts.",
  "Testing a true max is stressful and rare; an estimate from every set trends your real strength continuously and safely.",
  "Ingest reps and loads into `index=personal`; review the estimated one-rep-max trend per lift.",
  "Multi-line chart of estimated one-rep max by exercise.",
  "It estimates your top strength for each lift from normal sets, so you see progress without risky maximum attempts.",
  R(TP), SP_APP, SP_DS)

U("28", "Running Gait Symmetry and Cadence", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=gait:metric\n"
  "| stats avg(cadence_spm) as cadence, avg(left_contact_ms) as left, avg(right_contact_ms) as right by run\n"
  "| eval imbalance=round(100*abs(left-right)/((left+right)/2),1)\n"
  "| sort - imbalance",
  "Measures your running cadence and left-right ground-contact symmetry to spot the imbalance behind recurring injuries.",
  "Persistent left-right asymmetry is a common injury driver; quantifying it guides drills before a niggle becomes a layoff.",
  "Ingest running-form IMU data into `index=personal`; review cadence and left-right symmetry per run.",
  "Bar chart of gait imbalance per run with cadence overlay.",
  "It measures your running rhythm and whether your two legs work evenly, which helps avoid injuries.",
  R(TP), SP_APP, SP_DS)

U("28", "Cycling Power Interval Compliance", "low", "advanced", ["Performance"],
  "index=personal sourcetype=powermeter:interval\n"
  "| eval in_zone=if(avg_watts>=target_watts*0.95 AND avg_watts<=target_watts*1.05,1,0)\n"
  "| stats sum(in_zone) as hit, count as intervals by workout\n"
  "| eval compliance=round(100*hit/intervals,1)\n"
  "| sort compliance",
  "Measures how many training intervals you actually held in the target power band, grading how well you executed the workout.",
  "A structured session only works if the intervals hit target; a compliance score separates a great workout from a sloppy one.",
  "Ingest power-meter interval data into `index=personal`; review target-band compliance per workout.",
  "Bar chart of interval compliance by workout.",
  "It checks how many of your cycling efforts hit the target power, showing how well you followed the training plan.",
  R(GC), SP_APP, SP_DS)

U("28", "Cycling Fitness and Fatigue Balance", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=powermeter:interval\n"
  "| bin _time span=1d\n"
  "| stats sum(training_load) as daily_load by _time\n"
  "| streamstats window=42 avg(daily_load) as fitness\n"
  "| streamstats window=7 avg(daily_load) as fatigue\n"
  "| eval form=round(fitness-fatigue,1)",
  "Trends long-term fitness against short-term fatigue to estimate your form, guiding when to push and when to taper.",
  "The fitness-minus-fatigue balance predicts readiness; watching it helps you peak for events and avoid overtraining.",
  "Ingest daily training load into `index=personal`; compute rolling fitness and fatigue and trend the difference.",
  "Line chart of fitness, fatigue, and resulting form.",
  "It balances your long-term fitness against recent tiredness to show your form, so you know when to push or rest.",
  R(GC), SP_APP, SP_DS)

U("28", "Climbing Hangboard Load Progression", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=hangboard:session\n"
  "| timechart span=1w max(added_kg) as max_load, avg(hang_time_s) as avg_hang by grip",
  "Trends the added weight and hang time you sustain on each grip type, charting finger-strength gains for climbing.",
  "Finger strength is climbing's foundation and slow to build; trending hangboard load makes tiny weekly gains visible and motivating.",
  "Ingest hangboard load-cell sessions into `index=personal`; review load and hang time by grip.",
  "Multi-line chart of hangboard load by grip type.",
  "It tracks how much weight your fingers can hold on the training board, showing your climbing strength grow.",
  R(TP), SP_APP, SP_DS)

U("28", "Golf-Swing Consistency by Club", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=golfswing:metric\n"
  "| stats avg(carry_m) as carry, stdev(carry_m) as carry_sd, avg(club_speed_kmh) as speed by club\n"
  "| eval consistency=round(carry_sd,1)\n"
  "| sort - consistency",
  "Measures how consistent your carry distance is with each club so you know which yardages you can actually trust on the course.",
  "Golf is a game of dispersion; knowing the spread per club turns club selection from hope into a confident, data-backed decision.",
  "Ingest launch-monitor data into `index=personal`; review carry consistency per club.",
  "Bar chart of carry-distance variation by club.",
  "It measures how consistent your distance is with each golf club, so you know which ones you can rely on.",
  R(("USGA — handicap and stats", "https://www.usga.org/")), SP_APP, SP_DS)

U("28", "Basketball Shooting Percentage by Spot", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=shotarc:make\n"
  "| stats sum(eval(if(result=\"make\",1,0))) as makes, count as attempts by spot\n"
  "| eval pct=round(100*makes/attempts,1)\n"
  "| sort - pct",
  "Tracks your make percentage from each spot on the floor so practice targets your genuine cold zones, not your favourites.",
  "Shooters over-practise their strengths; a spot-by-spot percentage exposes the weak areas that actually need the reps.",
  "Feed shot-tracker results into `index=personal`; review shooting percentage by location.",
  "Shot chart of make percentage by spot.",
  "It tracks how often you score from each spot on the court, so you practise the places you actually miss.",
  R(("NBA — stats glossary", "https://www.nba.com/stats/help/glossary")), SP_APP, SP_DS)

U("28", "Training Streak and Weekly Volume", "low", "beginner", ["Business"],
  "index=personal (sourcetype=vbt:rep OR sourcetype=powermeter:interval OR sourcetype=hangboard:session)\n"
  "| bin _time span=1d\n"
  "| stats count as sessions by _time\n"
  "| streamstats current=t sum(eval(if(sessions>0,1,0))) as streak reset_after=\"(sessions=0)\"\n"
  "| sort - _time",
  "Recreates your training streak and daily activity across all your sports so consistency stays visible and motivating.",
  "Consistency beats intensity for long-term progress; a visible streak across every sport keeps the habit alive on tired days.",
  "Ingest sessions across your sports into `index=personal`; schedule daily and surface the current streak.",
  "Calendar heatmap of training days with the current streak.",
  "It tracks how many days in a row you have trained across all your sports, which keeps you motivated.",
  R(TP), SP_APP, SP_DS)

U("28", "Personal-Best Achievement Log", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vbt:rep\n"
  "| eval est_1rm=round(load_kg*(1+reps/30),1)\n"
  "| streamstats current=t max(est_1rm) as best_so_far by exercise\n"
  "| eval new_pb=if(est_1rm>=best_so_far AND est_1rm>0,1,0)\n"
  "| where new_pb=1\n"
  "| table _time exercise est_1rm",
  "Flags the moment you set a new personal best on any lift, capturing the milestones that make training rewarding.",
  "Personal bests are the reward that keeps training fun; surfacing them automatically turns raw logs into a highlight reel.",
  "Ingest reps and loads into `index=personal`; detect and log new personal bests per exercise.",
  "Table of personal-best moments by exercise and date.",
  "It spots when you set a new personal record on a lift, capturing the milestones that make training satisfying.",
  R(TP), SP_APP, SP_DS)


# ===========================================================================
# 25.29  Games & Tabletop
# ===========================================================================
GM_APP = ("Gaming and tabletop telemetry — Steam / PSN / Xbox playtime and achievement APIs, "
          "BoardGameGeek plays export, Lichess / Chess.com game archives, and tabletop dice-roller "
          "logs — streamed to Splunk HEC via scripted inputs.")
GM_DS = ("Video-game sessions (`game:session`), achievement unlocks (`achievement:unlock`), "
         "board-game plays (`boardgame:play`), chess games (`chess:game`), dice rolls (`dice:roll`).")
STEAM = ("Steam — Web API", "https://steamcommunity.com/dev")
BGG = ("BoardGameGeek — XML API2", "https://boardgamegeek.com/wiki/page/BGG_XML_API2")
LICHESS = ("Lichess — API", "https://lichess.org/api")

U("29", "Weekly Gaming Time vs Self-Set Limit", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=game:session\n"
  "| bin _time span=1w\n"
  "| stats sum(minutes) as played by _time\n"
  "| eval hours=round(played/60,1), limit_h=10, over=if(hours>limit_h,1,0)\n"
  "| sort - _time",
  "Adds up how many hours you spent gaming each week and compares it to a limit you set for yourself.",
  "A visible weekly total against a personal cap keeps a hobby from quietly eating whole evenings without you noticing.",
  "Pull playtime from Steam/PSN/Xbox APIs into `index=personal`; alert when the weekly total crosses your limit.",
  "Column chart of weekly gaming hours with a limit line.",
  "It adds up your gaming hours each week and tells you if you have gone over the limit you set yourself.",
  R(STEAM), GM_APP, GM_DS)

U("29", "Backlog Burn-Down of Unfinished Games", "low", "intermediate", ["Business"],
  "index=personal sourcetype=game:session\n"
  "| stats sum(minutes) as played, latest(status) as status by title\n"
  "| where status!=\"completed\" AND played>0\n"
  "| eval hours=round(played/60,1)\n"
  "| sort - hours",
  "Lists the games you have started but never finished, ranked by how much time you have already sunk into each.",
  "The pile of half-played games is real; seeing the sunk hours nudges you to finish one before buying the next.",
  "Ingest per-title playtime and completion status; schedule weekly and surface the unfinished pile.",
  "Bar chart of hours invested in unfinished games.",
  "It shows the games you started but never finished, so you can go back and complete one before buying more.",
  R(STEAM), GM_APP, GM_DS)

U("29", "Achievement Completion Rate by Game", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=achievement:unlock\n"
  "| stats dc(achievement) as earned, max(total_achievements) as total by title\n"
  "| eval pct=round(100*earned/total,1)\n"
  "| sort - pct",
  "Tracks what share of each game's achievements you have unlocked, gamifying your own completionism.",
  "A per-game completion percentage turns a scattered trophy list into a satisfying progress bar you can chase.",
  "Ingest achievement unlocks into `index=personal`; review completion percentage per title.",
  "Bar chart of achievement completion percentage by game.",
  "It shows how many of each game's rewards you have unlocked, which is fun if you like completing everything.",
  R(STEAM), GM_APP, GM_DS)

U("29", "Board-Game Play Frequency and Shelf of Shame", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=boardgame:play\n"
  "| stats count as plays, latest(_time) as last_played by game\n"
  "| eval days_since=round((now()-last_played)/86400,0), unplayed=if(plays=0,1,0)\n"
  "| sort plays",
  "Counts how often each board game hits the table and flags the ones gathering dust, the dreaded shelf of shame.",
  "Board-game collections skew toward the unplayed; a play-count view earns each game its place or prompts a cull.",
  "Log plays from BoardGameGeek into `index=personal`; schedule monthly and rank games by plays and days since last played.",
  "Table of board games by play count and days since last played.",
  "It counts how often you actually play each board game, showing which ones just gather dust on the shelf.",
  R(BGG), GM_APP, GM_DS)

U("29", "Board-Game Cost-Per-Play Value", "low", "intermediate", ["Business"],
  "index=personal sourcetype=boardgame:play\n"
  "| stats count as plays, latest(price) as price by game\n"
  "| eval cost_per_play=round(price/plays,2)\n"
  "| sort - cost_per_play",
  "Divides what each board game cost by how many times you have played it to reveal its true value per session.",
  "Cost-per-play reframes an expensive game that gets played often as a bargain and a cheap one that never does as waste.",
  "Ingest plays and purchase price; schedule monthly and compute cost-per-play per game.",
  "Bar chart of cost-per-play by board game.",
  "It works out how much each board game costs per time you play it, so you see which were really worth buying.",
  R(BGG), GM_APP, GM_DS)

U("29", "Chess Rating Trend and Slumps", "low", "intermediate", ["Analytics", "Anomaly"],
  "index=personal sourcetype=chess:game\n"
  "| timechart span=1w latest(rating) as rating by variant\n"
  "| eventstats avg(rating) as season_avg\n"
  "| eval slump=if(rating<season_avg-50,1,0)",
  "Trends your online chess rating over time per variant and flags the slumps worth stepping away from.",
  "A rating trend separates real improvement from tilt; spotting a slump early is the cue to take a break, not to keep losing.",
  "Ingest game results from Lichess/Chess.com; schedule weekly and trend rating per variant.",
  "Line chart of chess rating over time by variant.",
  "It tracks your online chess rating over time and warns of a losing slump, when it is best to take a break.",
  R(LICHESS), GM_APP, GM_DS)

U("29", "Chess Opening Win-Rate Breakdown", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=chess:game\n"
  "| stats sum(eval(if(result=\"win\",1,0))) as wins, count as games by opening\n"
  "| where games>=5\n"
  "| eval win_pct=round(100*wins/games,1)\n"
  "| sort - win_pct",
  "Breaks your chess results down by opening so you learn which lines actually win for you and which to drop.",
  "Win-rate by opening is the fastest route to practical improvement, pointing your study where it pays off most.",
  "Ingest game archives with opening tags; review win rate per opening with a minimum sample size.",
  "Bar chart of win rate by chess opening.",
  "It shows which chess openings you win with most, so you know which to keep playing and which to drop.",
  R(LICHESS), GM_APP, GM_DS)

U("29", "Tabletop RPG Dice Luck Tracker", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=dice:roll die=d20\n"
  "| stats count as rolls, avg(value) as avg_roll, sum(eval(if(value=20,1,0))) as crits, sum(eval(if(value=1,1,0))) as fumbles by player\n"
  "| eval expected=10.5, luck=round(avg_roll-expected,2)\n"
  "| sort - luck",
  "Tracks each player's average d20 roll against the expected 10.5, settling once and for all who the table's lucky roller is.",
  "Perceived dice luck is a favourite table argument; the long-run average turns folklore into a friendly, data-backed verdict.",
  "Log dice rolls from an electronic roller into `index=personal`; review average roll, crits, and fumbles per player.",
  "Bar chart of average d20 roll per player versus expected.",
  "It tracks everyone's dice rolls in a tabletop game to settle who is really the lucky one at the table.",
  R(("Roll20 — virtual tabletop", "https://roll20.net/")), GM_APP, GM_DS)

U("29", "Late-Night Gaming vs Next-Day Tiredness", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=game:session OR sourcetype=oura:daily)\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(strftime(_time,\"%H\")>=23,minutes,0))) as late_gaming, avg(sleep_score) as sleep by _time\n"
  "| eval late=if(late_gaming>30,1,0)\n"
  "| stats avg(sleep) as avg_sleep by late",
  "Compares your sleep quality on nights you gamed late against nights you did not, testing whether the late sessions cost you.",
  "Linking late gaming to next-day recovery makes an abstract trade-off concrete enough to actually change the habit.",
  "Join gaming sessions with sleep scores in `index=personal`; compare average sleep by whether you gamed late.",
  "Bar chart of average sleep score with versus without late gaming.",
  "It compares how well you sleep after late-night gaming versus early nights, showing whether the late sessions are worth it.",
  R(STEAM), GM_APP, GM_DS)

U("29", "Game Library Value and Never-Played Spend", "low", "intermediate", ["Business"],
  "index=personal sourcetype=game:session\n"
  "| stats sum(minutes) as played, latest(price) as price by title\n"
  "| eval wasted=if(played=0,price,0)\n"
  "| stats sum(price) as library_value, sum(wasted) as never_played_spend",
  "Totals what your game library cost and how much of it went on games you have never even launched.",
  "The never-played spend is a sobering number that curbs impulse sales-buying far better than good intentions.",
  "Ingest per-title price and playtime; schedule monthly and total library value and never-played spend.",
  "Single-value tiles of library value and never-played spend.",
  "It adds up what your game collection cost and how much you spent on games you never even opened.",
  R(STEAM), GM_APP, GM_DS)


# ===========================================================================
# 25.30  Collections & Hobbies
# ===========================================================================
CO_APP = ("Collection catalogues and price APIs — Discogs (vinyl), BrickLink (LEGO), trading-card "
          "and coin/stamp price feeds, and personal inventory databases with NFC-tagged scans — "
          "streamed to Splunk HEC via scripted inputs.")
CO_DS = ("Collection items (`collection:item`), vinyl plays (`vinyl:play`), LEGO sets "
         "(`lego:set`), trading-card prices (`tradingcard:price`).")
DISCOGS = ("Discogs — API", "https://www.discogs.com/developers")
BRICKLINK = ("BrickLink — API", "https://www.bricklink.com/v3/api.page")

U("30", "Collection Value Trend Over Time", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=collection:item\n"
  "| timechart span=1mon sum(market_value) as value by category",
  "Trends the estimated market value of your collections month by month, so you watch your hobby appreciate (or not).",
  "A value trend turns a shelf of stuff into a tracked asset, revealing which parts of a collection are actually gaining.",
  "Ingest catalogue values from Discogs/BrickLink into `index=personal`; schedule monthly and trend value by category.",
  "Line chart of collection value over time by category.",
  "It tracks how much your collections are worth over time, so you can see them grow in value.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Most-Valuable Items and Insurance List", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=collection:item\n"
  "| stats latest(market_value) as value, latest(condition) as condition by item category\n"
  "| where value>100\n"
  "| sort - value",
  "Lists your most valuable collectibles with their condition, ready-made for an insurance schedule.",
  "A current high-value list is exactly what an insurer wants and what you would need after a fire or theft.",
  "Ingest item values into `index=personal`; schedule and surface items above a value threshold for insurance.",
  "Table of highest-value items with condition and category.",
  "It lists your most valuable collectibles, which is exactly what you need for insurance or after a burglary.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Vinyl Play-Count and Turntable Wear", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vinyl:play\n"
  "| stats count as plays by album\n"
  "| eventstats sum(plays) as total_plays\n"
  "| eval stylus_hours=round(total_plays*0.35,1)\n"
  "| sort - plays",
  "Counts how often each record is played and estimates total stylus hours, hinting when the needle needs replacing.",
  "Tracking plays both surfaces your true favourites and protects your records by timing stylus changes before they wear grooves.",
  "Log plays (NFC tap or app) into `index=personal`; review play counts and cumulative stylus hours.",
  "Bar chart of play count by album with a stylus-hours total.",
  "It counts how often you play each record and hints when the turntable needle needs replacing to protect them.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "LEGO Set Completeness and Missing Parts", "low", "intermediate", ["Data Quality"],
  "index=personal sourcetype=lego:set\n"
  "| stats latest(owned_parts) as owned, latest(total_parts) as total by set\n"
  "| eval complete_pct=round(100*owned/total,1), missing=total-owned\n"
  "| where missing>0\n"
  "| sort - missing",
  "Tracks how complete each LEGO set is and how many parts are missing, guiding your BrickLink replacement orders.",
  "A completeness view turns a bin of mixed bricks into a clear list of exactly which parts to reorder to finish a set.",
  "Ingest owned-versus-total part counts into `index=personal`; surface sets with missing parts.",
  "Table of LEGO sets by completeness and missing-part count.",
  "It tracks how complete each LEGO set is and which pieces are missing, so you know what to order to finish it.",
  R(BRICKLINK), CO_APP, CO_DS)

U("30", "Trading-Card Portfolio Movers", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=tradingcard:price\n"
  "| streamstats current=f last(price) as prev by card\n"
  "| eval change_pct=round(100*(price-prev)/prev,1)\n"
  "| stats latest(change_pct) as move, latest(price) as price by card\n"
  "| where abs(move)>10\n"
  "| sort - move",
  "Flags the trading cards in your collection whose price moved sharply, so you catch a spike worth selling into.",
  "Card prices swing on reprints and hype; a movers view lets you act on a spike instead of learning about it too late.",
  "Ingest card price feeds into `index=personal`; alert on large price moves in cards you own.",
  "Table of biggest price movers among owned cards.",
  "It flags trading cards whose value jumped or dropped a lot, so you can sell at a good time.",
  R(("TCGplayer — pricing", "https://www.tcgplayer.com/")), CO_APP, CO_DS)

U("30", "Collection Gaps and Want-List Progress", "low", "beginner", ["Business"],
  "index=personal sourcetype=collection:item\n"
  "| stats sum(eval(if(status=\"owned\",1,0))) as owned, count as total by series\n"
  "| eval pct=round(100*owned/total,1), remaining=total-owned\n"
  "| sort pct",
  "Tracks how close each series or set in your collection is to complete and how many items remain on the want list.",
  "A per-series completion bar makes the chase visible and keeps you focused on finishing sets rather than scattering purchases.",
  "Ingest owned-versus-target counts into `index=personal`; review completion per series.",
  "Bar chart of completion percentage by collection series.",
  "It shows how close each of your collections is to complete and what is still on your wish list.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Duplicate and Overlap Detector", "low", "intermediate", ["Data Quality"],
  "index=personal sourcetype=collection:item\n"
  "| stats count as copies, values(location) as where by item\n"
  "| where copies>1\n"
  "| sort - copies",
  "Finds items you own more than one of, catching accidental double-buys across a large collection.",
  "In a big collection it is easy to rebuy something you forgot you had; a duplicate check saves money and shelf space.",
  "Ingest item catalogue into `index=personal`; surface items with more than one copy.",
  "Table of duplicated items with copy count and locations.",
  "It finds things you accidentally bought twice, which is easy to do in a big collection.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Acquisition Pace and Spend Rate", "low", "beginner", ["Business"],
  "index=personal sourcetype=collection:item event=acquired\n"
  "| bin _time span=1mon\n"
  "| stats count as items, sum(price) as spend by _time\n"
  "| sort - _time",
  "Tracks how many items you add to your collections each month and what you spend, keeping an expensive hobby honest.",
  "Seeing the monthly acquisition pace and spend curbs the slow, unnoticed creep that collections are famous for.",
  "Ingest acquisition events into `index=personal`; schedule monthly and trend items added and spend.",
  "Column chart of monthly acquisitions with spend overlay.",
  "It tracks how many new items you add to your collections each month and what you spend, keeping the hobby in check.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Rarest-Items Spotlight", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=collection:item\n"
  "| stats latest(rarity_score) as rarity, latest(market_value) as value by item\n"
  "| sort - rarity\n"
  "| head 15",
  "Spotlights the rarest pieces in your collection by a rarity score, the crown jewels worth showing off.",
  "A rarity ranking celebrates the highlights of a collection and reminds you which pieces deserve the best care.",
  "Ingest rarity scores into `index=personal`; surface the rarest items.",
  "Ranked table of the rarest items with value.",
  "It highlights the rarest pieces in your collection, the special ones worth showing off and protecting.",
  R(DISCOGS), CO_APP, CO_DS)

U("30", "Storage-Condition Watch for Collectibles", "low", "intermediate", ["Safety"],
  "index=personal sourcetype=collection:item\n"
  "| eval risk=case(humidity>60,\"too damp\",humidity<30,\"too dry\",temp>25,\"too warm\",1=1,\"ok\")\n"
  "| stats latest(risk) as risk, latest(humidity) as humidity, latest(temp) as temp by location\n"
  "| where risk!=\"ok\"",
  "Watches the temperature and humidity where sensitive collectibles are stored and warns when conditions risk damage.",
  "Paper, vinyl, and cards degrade in damp or heat; an environment check protects a collection that took years to build.",
  "Ingest storage-area sensors tagged to collections; alert when conditions leave the safe range.",
  "Table of storage locations with out-of-range conditions.",
  "It watches the temperature and damp where you keep collectibles and warns before conditions can damage them.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), CO_APP, CO_DS)


# ===========================================================================
# 25.31  Mind, Mood & Journaling
# ===========================================================================
MD_APP = ("Mood, mindfulness and journaling apps — Daylio / How We Feel mood exports, Headspace / "
          "Insight Timer meditation logs, journaling and gratitude entries — sent to Splunk HEC via "
          "scripted inputs.")
MD_DS = ("Mood entries (`mood:entry`), meditation sessions (`meditation:session`), journal entries "
         "(`journal:entry`), gratitude logs (`gratitude:log`).")
DAYLIO = ("Daylio — mood diary", "https://daylio.net/")
INSIGHT = ("Insight Timer — meditation", "https://insighttimer.com/")

U("31", "Mood Trend and Low-Streak Alert", "medium", "beginner", ["Analytics", "Anomaly"],
  "index=personal sourcetype=mood:entry\n"
  "| timechart span=1d avg(mood_score) as mood\n"
  "| streamstats current=t sum(eval(if(mood<3,1,0))) as low_streak reset_after=\"(mood>=3)\"\n"
  "| eval concern=if(low_streak>=5,1,0)",
  "Trends your daily mood and gently flags a run of consecutive low days worth paying attention to.",
  "A sustained low streak is easy to miss day to day; surfacing it can be the nudge to reach out or seek support.",
  "Ingest mood ratings into `index=personal`; alert on an extended run of low days.",
  "Line chart of daily mood with low-streak highlighting.",
  "It tracks your daily mood and gently flags a run of low days, which can be a sign to reach out for support.",
  R(DAYLIO), MD_APP, MD_DS)

U("31", "What Lifts My Mood — Activity Correlation", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=mood:entry\n"
  "| eval activity=mvindex(split(tags,\",\"),0)\n"
  "| stats avg(mood_score) as avg_mood, count as days by activity\n"
  "| where days>=5\n"
  "| sort - avg_mood",
  "Compares your average mood across the activities you tag, revealing which things reliably lift you up.",
  "Learning that, say, exercise or seeing friends consistently raises your mood turns vague advice into personal evidence.",
  "Ingest mood entries with activity tags; review average mood by tagged activity.",
  "Bar chart of average mood by tagged activity.",
  "It shows which activities tend to lift your mood most, based on your own diary entries.",
  R(DAYLIO), MD_APP, MD_DS)

U("31", "Meditation Streak and Consistency", "low", "beginner", ["Business"],
  "index=personal sourcetype=meditation:session\n"
  "| bin _time span=1d\n"
  "| stats sum(minutes) as minutes by _time\n"
  "| streamstats current=t sum(eval(if(minutes>0,1,0))) as streak reset_after=\"(minutes=0)\"\n"
  "| sort - _time",
  "Tracks your meditation streak and daily minutes so a mindfulness habit stays visible and rewarding.",
  "A visible streak is one of the strongest motivators for a daily practice that is otherwise easy to skip.",
  "Ingest meditation sessions into `index=personal`; schedule daily and surface the current streak.",
  "Calendar heatmap of meditation days with the current streak.",
  "It tracks how many days in a row you have meditated, which keeps the calming habit going.",
  R(INSIGHT), MD_APP, MD_DS)

U("31", "Journaling Frequency and Word Count", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=journal:entry\n"
  "| timechart span=1w count as entries, sum(word_count) as words",
  "Trends how often you journal and how much you write, keeping a reflective habit from quietly lapsing.",
  "Writing frequency is the habit that matters; trending it reveals the busy weeks when reflection slipped away.",
  "Ingest journal metadata into `index=personal`; schedule weekly and trend entries and words.",
  "Column chart of weekly journal entries with word-count overlay.",
  "It tracks how often and how much you write in your journal, so the reflective habit does not fade.",
  R(("Day One — journaling", "https://dayoneapp.com/")), MD_APP, MD_DS)

U("31", "Gratitude Themes Word Cloud", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=gratitude:log\n"
  "| eval theme=lower(theme)\n"
  "| stats count as mentions by theme\n"
  "| sort - mentions\n"
  "| head 20",
  "Counts the recurring themes in your gratitude entries, reflecting back what you most often appreciate.",
  "Seeing your gratitude themes ranked is a quietly powerful reminder of what truly matters to you.",
  "Ingest gratitude entries with themes into `index=personal`; rank the most common themes.",
  "Word-cloud or bar chart of gratitude themes.",
  "It gathers the things you are most often grateful for, gently reflecting back what matters to you.",
  R(("Presently — gratitude journal", "https://play.google.com/store/apps/details?id=com.imangi.gratitude")), MD_APP, MD_DS)

U("31", "Sleep vs Mood Correlation", "medium", "advanced", ["Analytics"],
  "index=personal (sourcetype=mood:entry OR sourcetype=oura:daily)\n"
  "| bin _time span=1d\n"
  "| stats avg(mood_score) as mood, avg(sleep_score) as sleep by _time\n"
  "| eval good_sleep=if(sleep>=80,\"slept well\",\"slept poorly\")\n"
  "| stats avg(mood) as avg_mood by good_sleep",
  "Compares your mood on well-slept days versus poorly-slept ones, quantifying how much sleep shapes how you feel.",
  "Proving to yourself that sleep drives mood is often the most persuasive reason to protect your bedtime.",
  "Join mood and sleep scores in `index=personal`; compare average mood by sleep quality.",
  "Bar chart of average mood after good versus poor sleep.",
  "It compares your mood on nights you slept well versus badly, showing how much rest affects how you feel.",
  R(DAYLIO), MD_APP, MD_DS)

U("31", "Mood by Day-of-Week Pattern", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=mood:entry\n"
  "| eval dow=strftime(_time,\"%A\")\n"
  "| stats avg(mood_score) as avg_mood by dow\n"
  "| sort - avg_mood",
  "Averages your mood by day of the week, exposing the Monday dip or the Friday lift in your own rhythm.",
  "A weekly mood pattern helps you plan demanding tasks for your naturally better days and protect the harder ones.",
  "Ingest mood entries into `index=personal`; review average mood by weekday.",
  "Bar chart of average mood by day of week.",
  "It shows which days of the week you tend to feel best and worst, revealing your own rhythm.",
  R(DAYLIO), MD_APP, MD_DS)

U("31", "Meditation Impact on Resting Heart Rate", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=meditation:session OR sourcetype=hrv:reading)\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(sourcetype==\"meditation:session\",minutes,0))) as med_min, avg(rmssd_ms) as hrv by _time\n"
  "| eval meditated=if(med_min>0,\"meditated\",\"did not\")\n"
  "| stats avg(hrv) as avg_hrv by meditated",
  "Compares your heart-rate variability on days you meditated versus days you did not, testing the calm you feel.",
  "Linking meditation to a measurable recovery signal gives the practice objective backing beyond how it feels.",
  "Join meditation minutes with HRV in `index=personal`; compare average HRV by whether you meditated.",
  "Bar chart of average HRV on meditation versus non-meditation days.",
  "It compares a calmness heart-signal on days you meditated versus days you did not, testing whether it helps.",
  R(INSIGHT), MD_APP, MD_DS)

U("31", "Journaling Sentiment Drift", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=journal:entry\n"
  "| timechart span=1w avg(sentiment_score) as sentiment\n"
  "| eventstats avg(sentiment) as base, stdev(sentiment) as sd\n"
  "| eval dip=if(sentiment<base-sd,1,0)",
  "Trends the overall sentiment of your journal entries and flags a sustained dip in tone worth noticing.",
  "A gradual darkening in your own writing is hard to see up close; a sentiment trend surfaces it kindly and early.",
  "Ingest per-entry sentiment scores into `index=personal`; alert on a sustained downward drift.",
  "Line chart of journal sentiment over time with a dip band.",
  "It notices when the overall tone of your journal drifts sad over time, which is worth gently paying attention to.",
  R(("Day One — journaling", "https://dayoneapp.com/")), MD_APP, MD_DS)

U("31", "Screen-Time vs Mood Trade-off", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=mood:entry OR sourcetype=screentime:usage)\n"
  "| bin _time span=1d\n"
  "| stats avg(mood_score) as mood, sum(minutes) as screen by _time\n"
  "| eval heavy=if(screen>240,\"heavy screen\",\"lighter\")\n"
  "| stats avg(mood) as avg_mood by heavy",
  "Compares your mood on heavy-screen days versus lighter ones, testing whether more scrolling really means feeling worse.",
  "Seeing your own mood dip on high-screen days is far more motivating than generic warnings about screen time.",
  "Join mood with screen-time in `index=personal`; compare average mood by screen load.",
  "Bar chart of average mood on heavy versus light screen days.",
  "It compares your mood on days of heavy phone use versus lighter days, testing whether scrolling brings you down.",
  R(DAYLIO), MD_APP, MD_DS)


# ===========================================================================
# 25.32  Relationships & Togetherness
# ===========================================================================
RL_APP = ("Relationship and togetherness logs — shared check-in apps, date-night and gift-idea "
          "lists, and stay-in-touch reminders — sent to Splunk HEC via scripted inputs.")
RL_DS = ("Relationship check-ins (`relationship:checkin`), date nights (`datenight:log`), gift "
         "ideas (`giftidea:item`), keep-in-touch contacts (`keptintouch:contact`).")
HA_REST = ("Home Assistant — REST integration", "https://www.home-assistant.io/integrations/rest/")

U("32", "Date-Night Cadence Tracker", "low", "beginner", ["Availability"],
  "index=personal sourcetype=datenight:log\n"
  "| stats latest(_time) as last_date, count as total\n"
  "| eval days_since=round((now()-last_date)/86400,0), overdue=if(days_since>21,1,0)",
  "Tracks how long it has been since your last proper date night and nudges you when life has crowded it out.",
  "Regular quality time slips first when life gets busy; a gentle cadence nudge helps keep a relationship a priority.",
  "Log date nights into `index=personal`; alert when it has been too long since the last one.",
  "Single-value tile of days since last date night.",
  "It tracks how long since your last date night and reminds you when it is time to plan another.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Stay-in-Touch Reminder for Loved Ones", "low", "beginner", ["Availability"],
  "index=personal sourcetype=keptintouch:contact\n"
  "| stats latest(_time) as last_contact, latest(target_days) as cadence by person\n"
  "| eval days_since=round((now()-last_contact)/86400,0), overdue=if(days_since>cadence,1,0)\n"
  "| where overdue=1\n"
  "| sort - days_since",
  "Reminds you which friends and family you have not spoken to within the cadence you set for each of them.",
  "Meaningful relationships fade through simple neglect; a per-person reminder keeps the important ones warm.",
  "Log calls and messages into `index=personal`; alert when a loved one is overdue for contact.",
  "Table of people overdue for a catch-up.",
  "It reminds you which friends and family you have not been in touch with for a while, so no one slips away.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Relationship Check-In Mood Trend", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=relationship:checkin\n"
  "| timechart span=1w avg(satisfaction) as satisfaction by partner",
  "Trends how each of you rates the relationship over time in shared check-ins, catching drift before it grows.",
  "A gentle, shared satisfaction trend opens honest conversations while issues are still small and easy to address.",
  "Ingest mutual check-in ratings into `index=personal`; schedule weekly and trend satisfaction.",
  "Line chart of relationship satisfaction over time.",
  "It tracks how happy you both feel in your relationship over time, so you can talk things through early.",
  R(("Paired — relationship app", "https://www.paired.com/")), RL_APP, RL_DS)

U("32", "Gift-Idea Backlog and Occasion Countdown", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=giftidea:item\n"
  "| eval days_to=round((occasion_epoch-now())/86400,0)\n"
  "| where status=\"idea\" AND days_to>0 AND days_to<45\n"
  "| sort days_to",
  "Surfaces the gift ideas you saved for upcoming birthdays and occasions in time to actually buy them.",
  "Good gift ideas struck at random moments are worthless if forgotten; a countdown makes sure they get used.",
  "Log gift ideas with target occasions into `index=personal`; surface ideas for occasions coming up soon.",
  "Table of gift ideas by days until the occasion.",
  "It reminds you of the gift ideas you jotted down, in time to buy them before the birthday or occasion.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Chore Balance Between Partners", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=chore:completion\n"
  "| search person=*\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(status=\"done\",effort_points,0))) as effort by person _time\n"
  "| stats avg(effort) as avg_effort by person\n"
  "| sort - avg_effort",
  "Compares the household workload each partner actually carries by effort points, settling the fairness debate with data.",
  "Perceived chore imbalance is a common friction; an effort-weighted comparison replaces resentment with a clear picture.",
  "Ingest chore completions with effort weights into `index=personal`; compare weekly effort by partner.",
  "Bar chart of average weekly chore effort by partner.",
  "It compares how much housework each partner really does, settling the fairness question with facts.",
  R(("Home Assistant — to-do list", "https://www.home-assistant.io/integrations/todo/")), RL_APP, RL_DS)

U("32", "Quality-Time vs Screen-Time Split", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=datenight:log OR sourcetype=screentime:usage)\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(sourcetype==\"datenight:log\",duration_min,0))) as together, sum(eval(if(sourcetype==\"screentime:usage\",minutes,0))) as screen by _time\n"
  "| eval ratio=round(together/(screen+1),3)",
  "Contrasts the time spent together against time on screens each week, a gentle mirror on where attention goes.",
  "Putting togetherness and screen minutes side by side can prompt small, deliberate changes toward presence.",
  "Join together-time with screen-time in `index=personal`; trend the ratio weekly.",
  "Dual-axis chart of together-time versus screen-time per week.",
  "It compares time spent together with time on screens each week, a gentle nudge toward being more present.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Anniversary and Important-Date Countdown", "low", "beginner", ["Availability"],
  "index=personal sourcetype=keptintouch:contact event=important_date\n"
  "| eval days_to=round((date_epoch-now())/86400,0)\n"
  "| where days_to>=0 AND days_to<=30\n"
  "| sort days_to",
  "Counts down to anniversaries, birthdays, and other important dates so none catches you unprepared.",
  "Forgetting an important date is a needless own-goal; an early countdown gives time to plan something thoughtful.",
  "Log important dates into `index=personal`; surface those coming up within a month.",
  "Table of upcoming important dates by days remaining.",
  "It counts down to anniversaries and birthdays so you never forget an important date again.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Acts-of-Kindness Ledger", "low", "beginner", ["Business"],
  "index=personal sourcetype=relationship:checkin event=kindness\n"
  "| bin _time span=1w\n"
  "| stats count as acts by person _time\n"
  "| stats avg(acts) as weekly_acts by person",
  "Counts the small thoughtful acts logged for each other each week, celebrating the little things that add up.",
  "Noticing and recording kindness reinforces the habit and reminds a couple of the good they do for each other.",
  "Log small acts of kindness into `index=personal`; review the weekly count per person.",
  "Bar chart of weekly acts of kindness per person.",
  "It counts the little kind things you do for each other, celebrating the small gestures that matter.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Long-Distance Call Frequency", "low", "beginner", ["Availability"],
  "index=personal sourcetype=keptintouch:contact event=call\n"
  "| bin _time span=1w\n"
  "| stats count as calls, sum(duration_min) as minutes by person _time\n"
  "| sort - _time",
  "Tracks how often and how long you talk with long-distance loved ones each week, keeping far-away bonds strong.",
  "Distance erodes contact by default; a call-frequency view helps you keep important relationships alive on purpose.",
  "Log calls into `index=personal`; schedule weekly and review call frequency and duration per person.",
  "Column chart of weekly calls and minutes per person.",
  "It tracks how often you call faraway family and friends, helping you keep in touch across the distance.",
  R(HA_REST), RL_APP, RL_DS)

U("32", "Shared Bucket-List Progress", "low", "beginner", ["Business"],
  "index=personal sourcetype=giftidea:item category=bucketlist\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as done, count as total\n"
  "| eval pct=round(100*done/total,1)",
  "Tracks how many items on your shared bucket list you have actually done together, keeping big dreams moving.",
  "A visible bucket-list bar turns someday plans into things you actively work toward as a couple or family.",
  "Log bucket-list items and completions into `index=personal`; review overall progress.",
  "Progress bar of shared bucket-list completion.",
  "It tracks how many things on your shared bucket list you have done together, keeping your dreams alive.",
  R(HA_REST), RL_APP, RL_DS)


# ===========================================================================
# 25.33  Everyday Habits & Vices
# ===========================================================================
HB_APP = ("Habit and sobriety trackers, alcohol-unit and hydration logs, vaping/smoking cessation "
          "apps, and a smart swear jar — sent to Splunk HEC via scripted inputs and MQTT.")
HB_DS = ("Alcohol drinks (`alcohol:drink`), vice logs (`vice:log`), hydration intake "
         "(`hydration:intake`), swear-jar entries (`swearjar:entry`).")
NHS_UNITS = ("NHS — alcohol units", "https://www.nhs.uk/live-well/alcohol-advice/calculating-alcohol-units/")

U("33", "Weekly Alcohol Units vs Guideline", "medium", "beginner", ["Analytics", "Compliance"],
  "index=personal sourcetype=alcohol:drink\n"
  "| bin _time span=1w\n"
  "| stats sum(units) as units by _time\n"
  "| eval guideline=14, over=if(units>guideline,1,0)\n"
  "| sort - _time",
  "Adds up your weekly alcohol units and compares them to the recommended guideline so a slow creep is visible.",
  "Counting units against a clear guideline is far more honest than a vague sense of how much you drink.",
  "Log drinks with units into `index=personal`; alert when the weekly total exceeds the guideline.",
  "Column chart of weekly alcohol units with a guideline line.",
  "It adds up how much alcohol you drink each week against the recommended limit, keeping it honest.",
  R(NHS_UNITS), HB_APP, HB_DS)

U("33", "Alcohol-Free Day Streak", "low", "beginner", ["Business"],
  "index=personal sourcetype=alcohol:drink\n"
  "| bin _time span=1d\n"
  "| stats sum(units) as units by _time\n"
  "| streamstats current=t sum(eval(if(units=0,1,0))) as dry_streak reset_after=\"(units>0)\"\n"
  "| sort - _time",
  "Counts your current run of alcohol-free days, turning cutting back into a streak you want to protect.",
  "A dry-day streak gamifies moderation, making an alcohol-free evening a small win rather than a sacrifice.",
  "Log drinks into `index=personal`; schedule daily and surface the current alcohol-free streak.",
  "Single-value tile of the current alcohol-free-day streak.",
  "It counts how many days in a row you have gone without alcohol, making cutting back feel like a winning streak.",
  R(NHS_UNITS), HB_APP, HB_DS)

U("33", "Smoking / Vaping Cessation Progress", "medium", "beginner", ["Business"],
  "index=personal sourcetype=vice:log type=nicotine\n"
  "| bin _time span=1d\n"
  "| stats sum(count) as uses by _time\n"
  "| eventstats avg(uses) as baseline\n"
  "| eval reduction_pct=round(100*(baseline-uses)/baseline,1)\n"
  "| sort - _time",
  "Tracks your daily cigarette or vape count and how far it has fallen from your starting baseline.",
  "Seeing the daily count drop is powerful motivation, and the money and health saved becomes tangible progress.",
  "Log each use into `index=personal`; trend daily count and the reduction from baseline.",
  "Line chart of daily nicotine use with a reduction percentage.",
  "It tracks how much you smoke or vape each day and how far you have cut down, cheering on your progress.",
  R(("NHS — quit smoking", "https://www.nhs.uk/better-health/quit-smoking/")), HB_APP, HB_DS)

U("33", "Daily Hydration vs Target", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=hydration:intake\n"
  "| bin _time span=1d\n"
  "| stats sum(ml) as ml by _time\n"
  "| eval target=2000, pct=round(100*ml/target), short=if(ml<target,1,0)\n"
  "| sort - _time",
  "Adds up how much water you drank each day against your target, so you catch the days you forget to hydrate.",
  "Staying hydrated is a simple win most people miss; a daily total against a target makes it easy to stay on track.",
  "Log intake (smart bottle or app) into `index=personal`; alert on days well below target.",
  "Column chart of daily water intake with a target line.",
  "It adds up how much water you drink each day against your goal, so you remember to stay hydrated.",
  R(("Home Assistant — utility meter", "https://www.home-assistant.io/integrations/utility_meter/")), HB_APP, HB_DS)

U("33", "Swear-Jar Ledger and Worst Days", "low", "beginner", ["Business"],
  "index=personal sourcetype=swearjar:entry\n"
  "| bin _time span=1d\n"
  "| stats count as swears, sum(fine) as owed by _time\n"
  "| sort - swears",
  "Counts the swear-jar entries each day and totals what you owe, a light-hearted nudge to clean up your language.",
  "A running swear-jar tally is a fun accountability game that turns a bad habit into a charity donation.",
  "Log swear-jar taps (a button by the jar) into `index=personal`; review daily counts and fines owed.",
  "Column chart of daily swear count with fines owed.",
  "It counts your swear-jar slip-ups and adds up what you owe, a fun way to watch your language.",
  R(("ESPHome — button", "https://esphome.io/components/binary_sensor/")), HB_APP, HB_DS)

U("33", "Bad-Habit Trigger Time-of-Day", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vice:log\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats count as uses by hour\n"
  "| sort - uses",
  "Maps when your slip-ups cluster through the day, revealing the trigger times to plan around.",
  "Habits are cued by moments; knowing that mid-afternoon is your weak spot lets you prepare a healthier alternative.",
  "Ingest vice logs into `index=personal`; review counts by hour to find trigger windows.",
  "Column chart of habit slips by hour of day.",
  "It shows what times of day you tend to slip up, so you can plan around your weak moments.",
  R(("NHS — quit smoking", "https://www.nhs.uk/better-health/quit-smoking/")), HB_APP, HB_DS)

U("33", "Money Saved by Cutting Back", "low", "beginner", ["Business"],
  "index=personal sourcetype=vice:log type=nicotine\n"
  "| bin _time span=1mon\n"
  "| stats sum(count) as uses by _time\n"
  "| eventstats max(uses) as baseline\n"
  "| eval avoided=baseline-uses, saved=round(avoided*0.60,2)\n"
  "| sort - _time",
  "Estimates the money you have saved each month by using less than your peak, turning willpower into cash.",
  "A pounds-saved figure is often the most motivating number of all, making the benefit of cutting back concrete.",
  "Ingest usage counts into `index=personal`; estimate monthly savings against your peak usage.",
  "Column chart of estimated monthly savings.",
  "It estimates how much money you have saved by cutting back on a habit, turning willpower into real cash.",
  R(("NHS — quit smoking", "https://www.nhs.uk/better-health/quit-smoking/")), HB_APP, HB_DS)

U("33", "Weekday vs Weekend Drinking Split", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=alcohol:drink\n"
  "| eval part=if(strftime(_time,\"%w\")>=1 AND strftime(_time,\"%w\")<=5,\"weekday\",\"weekend\")\n"
  "| stats sum(units) as units, dc(_time) as days by part\n"
  "| eval per_day=round(units/days,2)",
  "Compares your alcohol intake on weekdays versus weekends, showing whether a weekday habit has crept in.",
  "Many assume they only drink at weekends; the split reveals whether that is actually true for you.",
  "Ingest drinks into `index=personal`; compare units per day on weekdays versus weekends.",
  "Bar chart of alcohol units per day, weekday versus weekend.",
  "It compares your drinking on weekdays versus weekends, revealing whether a midweek habit has slipped in.",
  R(NHS_UNITS), HB_APP, HB_DS)

U("33", "Caffeine After Noon Sleep Guard", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=espresso:shot\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(strftime(_time,\"%H\")>=12,caffeine_mg,0))) as afternoon_mg by _time\n"
  "| eval risky=if(afternoon_mg>150,1,0)\n"
  "| sort - _time",
  "Totals the caffeine you take after midday and flags the days likely to disturb your sleep.",
  "Afternoon caffeine is a common hidden cause of poor sleep; flagging it links the habit to the consequence.",
  "Ingest coffee logs into `index=personal`; alert on high afternoon caffeine.",
  "Column chart of afternoon caffeine with a risk threshold.",
  "It adds up the coffee you drink after midday and warns when it is enough to spoil your sleep.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), HB_APP, HB_DS)

U("33", "Habit Substitution Success Rate", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vice:log\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(action=\"resisted\",1,0))) as resisted, sum(eval(if(action=\"gave_in\",1,0))) as gave_in by _time\n"
  "| eval success=round(100*resisted/(resisted+gave_in),1)\n"
  "| sort - _time",
  "Tracks how often you resisted an urge versus gave in each day, measuring the willpower behind breaking a habit.",
  "A daily success rate turns the fuzzy struggle of quitting into a metric you can watch improve.",
  "Log resisted and gave-in moments into `index=personal`; trend the daily resist rate.",
  "Line chart of daily urge-resisting success rate.",
  "It tracks how often you resisted a craving versus gave in, showing your willpower getting stronger over time.",
  R(("NHS — quit smoking", "https://www.nhs.uk/better-health/quit-smoking/")), HB_APP, HB_DS)


# ===========================================================================
# 25.34  Money Pettiness & Microspending
# ===========================================================================
MS_APP = ("Bank-transaction exports categorised for micro-spending, no-spend-day trackers, "
          "price-per-use logs, and cash-back / rewards feeds — sent to Splunk HEC via scripted inputs.")
MS_DS = ("Micro-spend transactions (`microspend:txn`), no-spend days (`nospend:day`), price-per-use "
         "items (`priceperuse:item`), cash-back rewards (`cashback:reward`).")
FIREFLY = ("Firefly III — personal finance", "https://www.firefly-iii.org/")

U("34", "Daily Coffee & Snack Spend Creep", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=microspend:txn category=coffee_snacks\n"
  "| bin _time span=1w\n"
  "| stats sum(amount) as spend, count as buys by _time\n"
  "| sort - _time",
  "Adds up the small coffee and snack purchases that quietly total a fortune over a month.",
  "The daily latte factor is invisible transaction by transaction; a weekly total makes the real cost impossible to ignore.",
  "Categorise transactions in `index=personal`; schedule weekly and total the small everyday buys.",
  "Column chart of weekly coffee and snack spend.",
  "It adds up all your little coffee and snack buys, which quietly cost a surprising amount each month.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "No-Spend Day Streak", "low", "beginner", ["Business"],
  "index=personal sourcetype=nospend:day\n"
  "| bin _time span=1d\n"
  "| stats max(spent) as spent by _time\n"
  "| streamstats current=t sum(eval(if(spent=0,1,0))) as streak reset_after=\"(spent>0)\"\n"
  "| sort - _time",
  "Counts your current run of days with zero discretionary spending, gamifying mindful saving.",
  "A no-spend streak makes frugality a game you want to win rather than a restriction you resent.",
  "Flag zero-spend days in `index=personal`; schedule daily and surface the current streak.",
  "Single-value tile of the current no-spend-day streak.",
  "It counts how many days in a row you spent nothing extra, making saving feel like a game.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Impulse-Buy Detector", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=microspend:txn\n"
  "| eventstats avg(amount) as avg_amt, stdev(amount) as sd by category\n"
  "| eval impulse=if(amount>avg_amt+2*sd AND flagged=\"unplanned\",1,0)\n"
  "| where impulse=1\n"
  "| table _time merchant amount category",
  "Flags unusually large, unplanned purchases that stand out from your normal spending in each category.",
  "Catching impulse buys as they happen builds awareness and, over time, a pause before the next one.",
  "Ingest categorised transactions into `index=personal`; alert on large unplanned outliers.",
  "Table of flagged impulse purchases.",
  "It spots unusually big, unplanned purchases, helping you notice impulse buys and think twice next time.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Price-Per-Use of Big Purchases", "low", "intermediate", ["Business"],
  "index=personal sourcetype=priceperuse:item\n"
  "| stats latest(price) as price, sum(uses) as uses by item\n"
  "| eval cost_per_use=round(price/uses,2)\n"
  "| sort - cost_per_use",
  "Divides the cost of your bigger purchases by how many times you have used them, exposing the real value of each.",
  "Cost-per-use vindicates a well-used splurge and shames the gadget in the cupboard, guiding smarter future buys.",
  "Log uses of tracked items into `index=personal`; compute cost-per-use per item.",
  "Bar chart of cost-per-use by purchase.",
  "It works out how much each big purchase costs per time you use it, showing which were worth the money.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Cash-Back and Rewards Harvest", "low", "beginner", ["Business"],
  "index=personal sourcetype=cashback:reward\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as earned by _time program\n"
  "| stats sum(earned) as total by program\n"
  "| sort - total",
  "Totals the cash-back and rewards you actually earned by program, so you use the cards and schemes that pay.",
  "Rewards only matter if collected; a per-program total shows which schemes are worth the effort and which to drop.",
  "Ingest rewards feeds into `index=personal`; schedule monthly and total earnings per program.",
  "Bar chart of rewards earned by program.",
  "It adds up the cash-back and points you actually earn, so you know which reward schemes are worth using.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Eating-Out vs Cooking Cost Split", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=microspend:txn\n"
  "| eval kind=case(category=\"restaurants\",\"eating out\",category=\"groceries\",\"cooking\",1=1,\"other\")\n"
  "| where kind!=\"other\"\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as spend by kind _time\n"
  "| sort - _time",
  "Compares what you spend eating out versus buying groceries each month, revealing the true cost of convenience.",
  "The eating-out-versus-cooking split is one of the biggest controllable levers in a food budget.",
  "Categorise food spending in `index=personal`; schedule monthly and compare eating out to groceries.",
  "Stacked column chart of eating-out versus grocery spend.",
  "It compares what you spend eating out versus cooking at home, showing the real cost of takeaways.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Round-Up Micro-Savings Total", "low", "beginner", ["Business"],
  "index=personal sourcetype=microspend:txn\n"
  "| eval roundup=ceiling(amount)-amount\n"
  "| bin _time span=1mon\n"
  "| stats sum(roundup) as saved by _time\n"
  "| sort - _time",
  "Adds up the spare change from rounding each purchase up, showing how painless micro-saving accumulates.",
  "Round-up saving is invisible yet surprisingly effective; totalling it proves small change becomes real money.",
  "Compute per-transaction round-ups in `index=personal`; schedule monthly and total the savings.",
  "Column chart of monthly round-up savings.",
  "It adds up the small change from rounding purchases up, showing how painlessly little savings grow.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Merchant Frequency and Loyalty Leaks", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=microspend:txn\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as spend, count as visits by merchant\n"
  "| where visits>=4\n"
  "| sort - spend",
  "Ranks the merchants you spend with most often, revealing where your money quietly concentrates.",
  "Knowing your top merchants highlights where a loyalty scheme, subscription swap, or habit change would save the most.",
  "Ingest transactions into `index=personal`; schedule monthly and rank merchants by spend and visits.",
  "Bar chart of spend by most-frequent merchant.",
  "It shows which shops you spend the most at, revealing where your money quietly goes.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Budget Category Overrun Alert", "medium", "beginner", ["Anomaly"],
  "index=personal sourcetype=microspend:txn\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as spend by category _time\n"
  "| eval budget=case(category=\"groceries\",400,category=\"eating_out\",150,category=\"coffee_snacks\",60,1=1,200)\n"
  "| eval over=if(spend>budget,1,0), over_by=round(spend-budget,2)\n"
  "| where over=1",
  "Alerts when spending in any category blows past its monthly budget, before the month-end surprise.",
  "Catching an overrun mid-month leaves time to rein it in, unlike discovering it on the statement.",
  "Set per-category budgets in `index=personal`; alert when a category exceeds its budget.",
  "Table of over-budget categories with the overshoot.",
  "It warns when you have overspent in any budget area, so there is no nasty surprise at month end.",
  R(FIREFLY), MS_APP, MS_DS)

U("34", "Fun-Money vs Essentials Ratio", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=microspend:txn\n"
  "| eval bucket=if(category IN (\"rent\",\"utilities\",\"groceries\",\"transport\"),\"essential\",\"discretionary\")\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as spend by bucket _time\n"
  "| sort - _time",
  "Splits your monthly spending into essentials versus discretionary fun money, a quick check on balance.",
  "The essentials-to-fun ratio is a fast health check on a budget without needing to itemise every line.",
  "Bucket transactions in `index=personal`; schedule monthly and compare essential versus discretionary spend.",
  "Stacked column chart of essential versus discretionary spend.",
  "It splits your spending into needs versus fun, a quick check that your budget is in balance.",
  R(FIREFLY), MS_APP, MS_DS)


# ===========================================================================
# 25.35  Body Signals & Personal Oddities
# ===========================================================================
BS_APP = ("Everyday body-signal logs — posture sensors, symptom and allergy journals, hydration-"
          "linked bathroom logs, and quirky personal counters — sent to Splunk HEC via wearables, "
          "MQTT, and scripted inputs.")
BS_DS = ("Posture readings (`posture:reading`), symptom logs (`symptom:log`), bathroom visits "
         "(`bathroom:visit`), sneeze events (`sneeze:event`).")
POSTURE = ("Upright — posture training", "https://www.uprightpose.com/")

U("35", "Posture Slouch-Time per Work Day", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=posture:reading\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(state=\"slouch\",duration_min,0))) as slouch_min, sum(duration_min) as total by _time\n"
  "| eval slouch_pct=round(100*slouch_min/total,1)\n"
  "| sort - _time",
  "Measures how much of each work day you spent slouching versus sitting upright, a nudge for your back.",
  "Posture is hard to self-assess; a daily slouch percentage turns a vague ache into a habit you can improve.",
  "Ingest a posture sensor into `index=personal`; review daily slouch time and percentage.",
  "Column chart of daily slouch time as a percentage.",
  "It measures how much of your day you spent slouching, gently reminding you to sit up straight.",
  R(POSTURE), BS_APP, BS_DS)

U("35", "Allergy Symptom vs Pollen Correlation", "medium", "advanced", ["Analytics"],
  "index=personal (sourcetype=symptom:log OR sourcetype=purpleair:aqi)\n"
  "| bin _time span=1d\n"
  "| stats avg(eval(if(sourcetype==\"symptom:log\",severity,null()))) as symptoms, avg(pollen_index) as pollen by _time\n"
  "| sort - _time",
  "Lines up your allergy symptom severity against pollen and air-quality readings to find your real triggers.",
  "Matching symptoms to environmental data pinpoints which days and triggers to prepare for with medication.",
  "Join symptom logs with air-quality/pollen data in `index=personal`; trend both together.",
  "Dual-axis chart of symptom severity and pollen index.",
  "It lines up your allergy symptoms with pollen levels to work out what actually sets them off.",
  R(("Home Assistant — pollen", "https://www.home-assistant.io/integrations/")), BS_APP, BS_DS)

U("35", "Headache Frequency and Trigger Log", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=symptom:log type=headache\n"
  "| bin _time span=1w\n"
  "| stats count as headaches, values(trigger) as triggers by _time\n"
  "| sort - _time",
  "Counts your headaches each week and gathers the triggers you logged, building a record for you and your doctor.",
  "A headache diary reveals patterns, such as poor sleep or dehydration, that a single appointment never could.",
  "Log headaches with triggers into `index=personal`; schedule weekly and review frequency and common triggers.",
  "Column chart of weekly headaches with common triggers.",
  "It counts your headaches and notes what set them off, building a helpful record for you and your doctor.",
  R(("NHS — headaches", "https://www.nhs.uk/conditions/headaches/")), BS_APP, BS_DS)

U("35", "Hydration vs Bathroom-Visit Balance", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=hydration:intake OR sourcetype=bathroom:visit)\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(sourcetype==\"hydration:intake\",ml,0))) as ml_in, sum(eval(if(sourcetype==\"bathroom:visit\",1,0))) as visits by _time\n"
  "| sort - _time",
  "Compares how much you drank with how often you visited the bathroom, a light-hearted balance check.",
  "Beyond the humour, an unusual mismatch over time can be a genuinely useful health signal to mention to a doctor.",
  "Join hydration and bathroom logs in `index=personal`; trend intake against visits.",
  "Dual-axis chart of water intake versus bathroom visits.",
  "It compares how much you drink with how often you visit the loo, a light-hearted balance check.",
  R(("NHS — water and hydration", "https://www.nhs.uk/live-well/eat-well/food-guidelines-and-food-labels/water-drinks-nutrition/")), BS_APP, BS_DS)

U("35", "Sneeze Count and Seasonal Peaks", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=sneeze:event\n"
  "| bin _time span=1d\n"
  "| stats sum(count) as sneezes by _time\n"
  "| eventstats avg(sneezes) as typical\n"
  "| eval peak=if(sneezes>typical*2,1,0)\n"
  "| sort - _time",
  "Counts your daily sneezes and flags the peak days, a quirky but real window into allergy season.",
  "A sneeze count is playful, yet its seasonal peaks map neatly onto pollen spikes and help time antihistamines.",
  "Log sneezes (a counter button) into `index=personal`; flag unusually sneezy days.",
  "Column chart of daily sneezes with peak days marked.",
  "It counts your sneezes each day and flags the worst ones, a fun peek at your allergy season.",
  R(("NHS — hay fever", "https://www.nhs.uk/conditions/hay-fever/")), BS_APP, BS_DS)

U("35", "Standing vs Sitting Time Balance", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=posture:reading\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(state=\"standing\",duration_min,0))) as standing, sum(eval(if(state=\"sitting\",duration_min,0))) as sitting by _time\n"
  "| eval standing_pct=round(100*standing/(standing+sitting),1)\n"
  "| sort - _time",
  "Tracks how much of your day you spent standing versus sitting, encouraging you to break up long sits.",
  "Long unbroken sitting is a well-known health risk; a daily standing percentage keeps a sit-stand desk honest.",
  "Ingest desk/posture state into `index=personal`; review standing versus sitting balance.",
  "Column chart of daily standing percentage.",
  "It tracks how much you stand versus sit each day, nudging you to get up and move more often.",
  R(POSTURE), BS_APP, BS_DS)

U("35", "Symptom Onset Early-Warning", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=symptom:log\n"
  "| bin _time span=1d\n"
  "| stats dc(symptom) as distinct_symptoms, sum(severity) as load by _time\n"
  "| eventstats avg(load) as base, stdev(load) as sd\n"
  "| eval flare=if(load>base+2*sd,1,0)\n"
  "| where flare=1",
  "Flags days when your overall symptom load jumps well above normal, an early sign of an illness or flare.",
  "A combined symptom-load spike catches something brewing before any single symptom feels alarming.",
  "Aggregate symptom severity in `index=personal`; alert when the daily load spikes.",
  "Time chart of daily symptom load with flare markers.",
  "It warns when your overall symptoms jump above normal, an early sign you might be coming down with something.",
  R(("NHS — health A to Z", "https://www.nhs.uk/conditions/")), BS_APP, BS_DS)

U("35", "Desk-Break Adherence", "low", "beginner", ["Compliance"],
  "index=personal sourcetype=posture:reading\n"
  "| eval hour=strftime(_time,\"%H\"), day=strftime(_time,\"%F\")\n"
  "| where hour>=9 AND hour<=17\n"
  "| bin _time span=1h\n"
  "| stats max(eval(if(state=\"break\",1,0))) as took_break by _time day\n"
  "| stats sum(took_break) as breaks, count as work_hours by day\n"
  "| eval adherence=round(100*breaks/work_hours,1)",
  "Measures how many working hours included a proper movement break, keeping the pomodoro promise honest.",
  "Regular breaks protect eyes, back, and focus; measuring adherence turns good intentions into a tracked habit.",
  "Ingest break events into `index=personal`; review the share of work hours with a break.",
  "Column chart of daily desk-break adherence.",
  "It checks how many work hours you took a proper break in, keeping you moving through the day.",
  R(POSTURE), BS_APP, BS_DS)

U("35", "Cold & Flu Recovery Curve", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=symptom:log episode=*\n"
  "| stats min(_time) as onset, max(_time) as recovered, max(severity) as peak by episode\n"
  "| eval duration_days=round((recovered-onset)/86400,1)\n"
  "| sort - onset",
  "Records how long each cold or illness lasted and how bad it got, building your personal recovery history.",
  "Knowing your typical recovery time sets expectations and flags when an illness is dragging on unusually long.",
  "Group symptom episodes in `index=personal`; review duration and peak severity per illness.",
  "Table of illness episodes with duration and peak severity.",
  "It records how long each cold lasts and how bad it got, so you know what is normal for you.",
  R(("NHS — common cold", "https://www.nhs.uk/conditions/common-cold/")), BS_APP, BS_DS)

U("35", "Eye-Strain and Screen-Break Reminder", "low", "intermediate", ["Anomaly"],
  "index=personal sourcetype=symptom:log type=eyestrain\n"
  "| bin _time span=1d\n"
  "| stats count as episodes by _time\n"
  "| eval high=if(episodes>3,1,0)\n"
  "| sort - _time",
  "Counts eye-strain episodes each day so a screen-heavy stretch prompts you to follow the twenty-twenty rule.",
  "Frequent eye strain is a signal to change habits; tracking it links the discomfort to your screen days.",
  "Log eye-strain moments into `index=personal`; alert on high-strain days.",
  "Column chart of daily eye-strain episodes.",
  "It counts how often your eyes feel strained, reminding you to rest them during screen-heavy days.",
  R(("NHS — eye health", "https://www.nhs.uk/live-well/healthy-body/look-after-your-eyes/")), BS_APP, BS_DS)


# ===========================================================================
# 25.36  Household Supplies & Logistics
# ===========================================================================
SL_APP = ("Household logistics feeds — smart-scale consumable trackers, parcel/delivery tracking "
          "APIs, council bin-collection calendars, and gift-card balance logs — sent to Splunk HEC "
          "via scripted inputs and MQTT.")
SL_DS = ("Consumable levels (`supply:level`), parcels (`delivery:parcel`), bin collections "
         "(`bincollection:event`), gift-card balances (`giftcard:balance`).")
SEVENTEENTRACK = ("17TRACK — parcel tracking API", "https://api.17track.net/")

U("36", "Household Consumables Reorder Forecast", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=supply:level\n"
  "| stats latest(level_pct) as level, avg(daily_use_pct) as usage by item\n"
  "| eval days_left=round(level/usage,1)\n"
  "| where days_left<10\n"
  "| sort days_left",
  "Estimates how many days of everyday consumables (detergent, coffee, pet food) remain and flags what to reorder.",
  "A usage-based runway ends the run-out-and-dash routine for the boring but essential household staples.",
  "Ingest smart-scale or manual consumable levels into `index=personal`; flag items running low.",
  "Table of consumables by days of supply left.",
  "It works out how many days of everyday supplies like detergent are left, so you reorder before running out.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), SL_APP, SL_DS)

U("36", "Parcel Delivery Tracker and Delays", "low", "beginner", ["Availability"],
  "index=personal sourcetype=delivery:parcel status!=delivered\n"
  "| eval days_in_transit=round((now()-shipped_epoch)/86400,1), stuck=if(days_in_transit>7,1,0)\n"
  "| sort - days_in_transit\n"
  "| table carrier item days_in_transit status stuck",
  "Tracks your in-flight parcels in one place and flags the ones stuck in transit far too long.",
  "A single view of every incoming parcel replaces a dozen carrier apps and catches a lost package early.",
  "Ingest tracking updates into `index=personal`; alert on parcels stuck in transit.",
  "Table of in-transit parcels with days elapsed and stuck flag.",
  "It tracks all your incoming parcels in one place and flags any stuck in the post too long.",
  R(SEVENTEENTRACK), SL_APP, SL_DS)

U("36", "Bin & Recycling Collection Reminder", "low", "beginner", ["Availability"],
  "index=personal sourcetype=bincollection:event\n"
  "| eval hours_to=round((collection_epoch-now())/3600,1)\n"
  "| where hours_to>0 AND hours_to<24\n"
  "| sort hours_to\n"
  "| table bin_type collection_epoch hours_to",
  "Reminds you which bins go out tomorrow so you never miss a collection and wait another fortnight.",
  "A missed bin day means overflowing rubbish for two weeks; a timely reminder is a small but real quality-of-life win.",
  "Ingest the council collection calendar into `index=personal`; alert the evening before a collection.",
  "Table of upcoming bin collections by type and time.",
  "It reminds you which bins to put out the night before, so you never miss a collection again.",
  R(("Home Assistant — waste collection", "https://www.home-assistant.io/integrations/waste_collection_schedule/")), SL_APP, SL_DS)

U("36", "Gift-Card and Voucher Expiry Watch", "low", "beginner", ["Anomaly"],
  "index=personal sourcetype=giftcard:balance balance>0\n"
  "| eval days_to_expiry=round((expiry_epoch-now())/86400,0)\n"
  "| where days_to_expiry>0 AND days_to_expiry<60\n"
  "| sort days_to_expiry",
  "Surfaces gift cards and vouchers with money left that are about to expire, so none goes to waste.",
  "Unspent gift-card balances are money thrown away; an expiry watch makes sure you use them in time.",
  "Ingest gift-card balances into `index=personal`; alert on cards nearing expiry with a balance.",
  "Table of gift cards by days to expiry with balance.",
  "It reminds you to use gift cards and vouchers before they expire, so you never waste the money.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), SL_APP, SL_DS)

U("36", "Grocery Restock Prediction", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=supply:level category=groceries\n"
  "| stats latest(level_pct) as level, avg(daily_use_pct) as usage by item\n"
  "| eval days_left=round(level/usage,1), add_to_list=if(days_left<4,1,0)\n"
  "| where add_to_list=1\n"
  "| sort days_left",
  "Predicts which fridge and pantry staples will run out within days and builds your next shopping list automatically.",
  "An auto-built restock list means fewer forgotten items and fewer midweek shop dashes.",
  "Ingest grocery levels into `index=personal`; surface items to add to the shopping list.",
  "Table of groceries to restock by days remaining.",
  "It predicts which food staples are about to run out and adds them to your shopping list for you.",
  R(("Home Assistant — shopping list", "https://www.home-assistant.io/integrations/shopping_list/")), SL_APP, SL_DS)

U("36", "Delivery Spend and Frequency", "low", "intermediate", ["Business"],
  "index=personal sourcetype=delivery:parcel status=delivered\n"
  "| bin _time span=1mon\n"
  "| stats count as parcels, sum(order_value) as spend by _time retailer\n"
  "| stats sum(parcels) as parcels, sum(spend) as spend by _time\n"
  "| sort - _time",
  "Counts how many parcels you receive and what you spend online each month, a check on the one-click habit.",
  "The true scale of online shopping is easy to underestimate; a monthly count and total makes it real.",
  "Ingest delivered-parcel data into `index=personal`; schedule monthly and total parcels and spend.",
  "Column chart of monthly parcels with online-spend overlay.",
  "It counts how many parcels arrive and what you spend online each month, revealing the online-shopping habit.",
  R(SEVENTEENTRACK), SL_APP, SL_DS)

U("36", "Expiry-Date Food-Waste Reducer", "medium", "intermediate", ["Anomaly"],
  "index=personal sourcetype=supply:level category=fridge\n"
  "| eval days_to_expiry=round((expiry_epoch-now())/86400,1)\n"
  "| where days_to_expiry>=0 AND days_to_expiry<=3\n"
  "| sort days_to_expiry",
  "Flags fridge items about to expire so you eat them in time and cut food waste and its cost.",
  "Use-it-up prompts turn forgotten leftovers into meals, saving money and reducing waste.",
  "Ingest fridge inventory with expiry dates into `index=personal`; alert on items expiring soon.",
  "Table of fridge items expiring within days.",
  "It flags food about to go off so you eat it in time, cutting waste and saving money.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), SL_APP, SL_DS)

U("36", "Battery Stock and Device Drain", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=supply:level category=batteries\n"
  "| stats latest(level_pct) as stock, avg(monthly_use) as usage by battery_type\n"
  "| eval months_left=round(stock/usage,1)\n"
  "| sort months_left",
  "Tracks your household battery stock against how fast devices drain them, so you are never caught without.",
  "A battery drawer runs dry at the worst moment; a stock-versus-usage view keeps the common sizes topped up.",
  "Log battery stock and usage into `index=personal`; flag types running low.",
  "Table of battery types by months of stock left.",
  "It tracks your spare batteries against how fast you use them, so the drawer is never empty when you need one.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), SL_APP, SL_DS)

U("36", "Subscription-Box Value Check", "low", "intermediate", ["Business"],
  "index=personal sourcetype=delivery:parcel type=subscription_box\n"
  "| stats avg(order_value) as paid, avg(contents_value) as received, count as boxes by service\n"
  "| eval value_ratio=round(received/paid,2)\n"
  "| sort value_ratio",
  "Compares what each subscription box costs against the value of what it contains, exposing the poor-value ones.",
  "Subscription boxes drift from delightful to wasteful; a value ratio tells you which to keep and which to cancel.",
  "Log box cost and estimated contents value into `index=personal`; review the value ratio per service.",
  "Bar chart of value ratio by subscription box.",
  "It compares what each subscription box costs with what is inside, showing which are worth keeping.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), SL_APP, SL_DS)

U("36", "Household Restock Shopping-Day Optimiser", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=supply:level\n"
  "| stats latest(level_pct) as level, avg(daily_use_pct) as usage by item\n"
  "| eval days_left=round(level/usage,1)\n"
  "| eval week=floor(days_left/7)\n"
  "| stats count as items by week\n"
  "| sort week",
  "Groups upcoming restocks by the week they are needed, helping you batch shopping trips efficiently.",
  "Clustering reorders into fewer, fuller shops saves time, delivery fees, and the constant top-up runs.",
  "Ingest consumable runways into `index=personal`; group items by the week they will run out.",
  "Histogram of items needing restock by week.",
  "It groups what you will run out of by week, so you can do fewer, fuller shopping trips.",
  R(("Home Assistant — shopping list", "https://www.home-assistant.io/integrations/shopping_list/")), SL_APP, SL_DS)


# ===========================================================================
# 25.37  Building Health & Structural
# ===========================================================================
BD_APP = ("Building-health sensors — indoor humidity / mould-risk monitors, crack and tilt meters, "
          "HVAC filter-life trackers, and damp sensors — streamed to Splunk HEC via MQTT and "
          "ESPHome.")
BD_DS = ("Mould risk (`mould:risk`), crack meters (`crackmeter:reading`), HVAC filter life "
         "(`hvacfilter:life`), structural tilt (`structural:tilt`).")
ESPHOME = ("ESPHome — DIY sensors", "https://esphome.io/")

U("37", "Mould-Risk Humidity Watch", "high", "intermediate", ["Safety", "Anomaly"],
  "index=personal sourcetype=mould:risk\n"
  "| eval dewpoint_gap=surface_temp_c-dewpoint_c\n"
  "| stats latest(humidity_pct) as humidity, latest(dewpoint_gap) as gap by room\n"
  "| eval risk=if(humidity>70 OR gap<3,1,0)\n"
  "| where risk=1",
  "Watches each room for the sustained high humidity and cold surfaces that let mould take hold.",
  "Mould damages health and homes and is far cheaper to prevent than remove; an early humidity warning triggers ventilation in time.",
  "Ingest room humidity and surface temperature into `index=personal`; alert on mould-risk conditions.",
  "Table of rooms at mould risk with humidity and margin.",
  "It watches for the damp, cold conditions that grow mould, warning you to ventilate before it takes hold.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Structural Crack Movement Trend", "high", "advanced", ["Anomaly"],
  "index=personal sourcetype=crackmeter:reading\n"
  "| timechart span=1w avg(width_mm) as width by crack_id\n"
  "| streamstats current=f last(width) as prev by crack_id\n"
  "| eval widening=if(width-prev>0.2,1,0)",
  "Trends the width of monitored cracks over time and flags any that are steadily widening.",
  "Most cracks are cosmetic, but a steadily widening one can signal subsidence; trending catches real movement early.",
  "Ingest crack-gauge readings into `index=personal`; alert on sustained widening.",
  "Line chart of crack width over time with widening flags.",
  "It measures monitored cracks in the walls over time and warns if any is slowly getting wider.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "HVAC Filter Life and Replacement", "low", "beginner", ["Availability"],
  "index=personal sourcetype=hvacfilter:life\n"
  "| stats latest(runtime_hours) as hours, latest(rated_hours) as rated by unit\n"
  "| eval life_pct=round(100*(1-hours/rated),1), replace=if(life_pct<10,1,0)\n"
  "| sort life_pct",
  "Tracks HVAC filter life by runtime hours and reminds you to change filters before airflow and efficiency suffer.",
  "A clogged filter wastes energy and strains the system; a runtime-based reminder beats guessing or forgetting.",
  "Ingest system runtime into `index=personal`; alert when a filter is near end of life.",
  "Gauge of remaining filter life per unit.",
  "It tracks how used your air filters are and reminds you to change them before they clog up.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Foundation Tilt and Settlement Monitor", "high", "advanced", ["Anomaly"],
  "index=personal sourcetype=structural:tilt\n"
  "| timechart span=1d avg(tilt_deg) as tilt by point\n"
  "| streamstats current=f last(tilt) as prev by point\n"
  "| eval drift=abs(tilt-prev), alert=if(drift>0.05,1,0)",
  "Monitors tilt sensors on the structure for slow changes that can indicate settlement or movement.",
  "Structural movement is gradual and easy to miss; a tilt trend gives early, quantified warning worth a surveyor's visit.",
  "Ingest tilt-sensor data into `index=personal`; alert on sustained tilt drift.",
  "Line chart of structural tilt over time by point.",
  "It watches sensors on the house for slow tilting that could mean the ground is shifting underneath.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Room-by-Room Damp Comparison", "medium", "intermediate", ["Analytics"],
  "index=personal sourcetype=mould:risk\n"
  "| stats avg(humidity_pct) as humidity, max(humidity_pct) as peak by room\n"
  "| eval concern=if(humidity>65,1,0)\n"
  "| sort - humidity",
  "Compares average humidity across rooms to pinpoint the dampest spots that need attention.",
  "Knowing which room is consistently dampest guides where to add ventilation or a dehumidifier for best effect.",
  "Ingest per-room humidity into `index=personal`; rank rooms by average dampness.",
  "Bar chart of average humidity by room.",
  "It compares how damp each room is, pointing to where you most need better airflow or a dehumidifier.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Window & Door Open-Duration Heat Loss", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=structural:tilt event=opening OR sourcetype=alarm:event event=opening\n"
  "| bin _time span=1d\n"
  "| stats sum(open_min) as open_min by opening _time\n"
  "| where open_min>60\n"
  "| sort - open_min",
  "Totals how long windows and external doors were left open in cold weather, quantifying heat lost.",
  "A door left ajar bleeds heat and money; totalling open-time makes an invisible waste visible.",
  "Ingest contact-sensor open durations into `index=personal`; flag openings left open a long time.",
  "Column chart of daily open-duration by window or door.",
  "It adds up how long windows and doors were left open in the cold, showing where heat is escaping.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Indoor Temperature Stability by Room", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=mould:risk\n"
  "| bin _time span=1d\n"
  "| stats max(surface_temp_c) as high, min(surface_temp_c) as low by room _time\n"
  "| eval swing=round(high-low,1)\n"
  "| stats avg(swing) as avg_swing by room\n"
  "| sort - avg_swing",
  "Measures how much each room's temperature swings through the day, revealing poor insulation or draughts.",
  "Big daily temperature swings point to insulation gaps; ranking rooms shows where improvements pay off most.",
  "Ingest room temperatures into `index=personal`; compare daily swing per room.",
  "Bar chart of average daily temperature swing by room.",
  "It measures how much each room's temperature changes through the day, hinting where insulation is poor.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Roof & Gutter Rain-Response Check", "medium", "advanced", ["Anomaly"],
  "index=personal (sourcetype=mould:risk OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1h\n"
  "| stats sum(rain_mm) as rain, max(eval(if(location=\"loft\",humidity_pct,0))) as loft_humidity by _time\n"
  "| eval leak_suspect=if(rain>5 AND loft_humidity>75,1,0)\n"
  "| where leak_suspect=1",
  "Correlates heavy rain with loft humidity spikes to catch a possible roof or gutter leak early.",
  "A roof leak often shows first as raised loft humidity after rain; catching it early prevents costly damage.",
  "Join rainfall with loft humidity in `index=personal`; alert when both spike together.",
  "Time chart of rainfall against loft humidity.",
  "It links heavy rain with damp in the loft to catch a roof or gutter leak before it causes real damage.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Heating Efficiency vs Outdoor Temperature", "low", "advanced", ["Performance"],
  "index=personal (sourcetype=mould:risk OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1d\n"
  "| stats avg(eval(if(location=\"living\",surface_temp_c,null()))) as indoor, avg(outdoor_temp_c) as outdoor by _time\n"
  "| eval delta=round(indoor-outdoor,1)\n"
  "| sort - _time",
  "Trends how well your home holds warmth against the outside temperature, a proxy for heating efficiency.",
  "A shrinking indoor-outdoor gap for the same heating hints at efficiency loss worth investigating.",
  "Join indoor and outdoor temperatures in `index=personal`; trend the difference over time.",
  "Line chart of indoor-outdoor temperature gap.",
  "It tracks how well your home stays warm compared to outside, a simple sign of heating efficiency.",
  R(ESPHOME), BD_APP, BD_DS)

U("37", "Appliance Vibration Fault Early-Warning", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=structural:tilt event=vibration\n"
  "| timechart span=1h avg(vibration_rms) as vib by appliance\n"
  "| eventstats avg(vib) as base, stdev(vib) as sd by appliance\n"
  "| eval fault=if(vib>base+3*sd,1,0)",
  "Watches vibration on big appliances like the washing machine for a jump that can precede a bearing failure.",
  "Rising vibration is an early mechanical warning; catching it can turn a catastrophic failure into a cheap repair.",
  "Ingest appliance vibration into `index=personal`; alert on abnormal vibration.",
  "Time chart of appliance vibration with fault threshold.",
  "It listens to big appliances shaking and warns of a jump that can mean a part is about to fail.",
  R(ESPHOME), BD_APP, BD_DS)


# ===========================================================================
# 25.38  Personal Cyber & Digital Exhaust
# ===========================================================================
CY_APP = ("Personal cybersecurity feeds — Have-I-Been-Pwned breach alerts, personal email/inbox "
          "stats, cloud-storage usage APIs, and personal TLS-certificate expiry checks — sent to "
          "Splunk HEC via scripted inputs.")
CY_DS = ("Breach alerts (`breach:alert`), inbox stats (`inbox:stats`), cloud-drive usage "
         "(`clouddrive:usage`), certificate expiry (`certexpiry:check`).")
HIBP = ("Have I Been Pwned — API", "https://haveibeenpwned.com/API/v3")

U("38", "Credential-Breach Exposure Alert", "high", "beginner", ["Security", "Anomaly"],
  "index=personal sourcetype=breach:alert\n"
  "| where notified=\"false\"\n"
  "| stats values(breach) as breaches, latest(_time) as seen by account\n"
  "| sort - seen",
  "Alerts when one of your email addresses shows up in a new data breach so you can change passwords fast.",
  "Knowing you are in a breach within hours, not months, is the difference between a password change and account takeover.",
  "Poll a breach-notification API into `index=personal`; alert on new exposures per account.",
  "Table of accounts newly appearing in breaches.",
  "It warns you the moment your email turns up in a data breach, so you can change your password quickly.",
  R(HIBP), CY_APP, CY_DS, pillar="Security")

U("38", "Two-Factor Coverage Gap Audit", "high", "beginner", ["Security", "Compliance"],
  "index=personal sourcetype=breach:alert event=account_inventory\n"
  "| stats latest(mfa_enabled) as mfa, latest(importance) as importance by account\n"
  "| where mfa=\"false\" AND importance IN (\"high\",\"critical\")\n"
  "| sort importance",
  "Lists your important accounts that still lack two-factor authentication, the biggest easy security win.",
  "Enabling two-factor on your critical accounts blocks the vast majority of account takeovers; this shows exactly where it is missing.",
  "Maintain an account inventory in `index=personal`; flag important accounts without two-factor.",
  "Table of important accounts missing two-factor.",
  "It lists your important accounts that still lack a second login step, the easiest way to stay safe online.",
  R(("NCSC — 2-step verification", "https://www.ncsc.gov.uk/guidance/setting-two-factor-authentication-2fa")), CY_APP, CY_DS, pillar="Security")

U("38", "Personal Certificate Expiry Watch", "medium", "intermediate", ["Availability"],
  "index=personal sourcetype=certexpiry:check\n"
  "| eval days_left=round((expiry_epoch-now())/86400,0)\n"
  "| where days_left<21\n"
  "| sort days_left\n"
  "| table host days_left issuer",
  "Watches the TLS certificates on your home-lab services and domains and warns before any expires.",
  "An expired certificate breaks your self-hosted services and looks alarming; an early warning avoids the scramble.",
  "Probe your certificates into `index=personal`; alert on those expiring soon.",
  "Table of certificates by days until expiry.",
  "It warns you before the security certificates on your home services expire, so nothing suddenly breaks.",
  R(("Let's Encrypt — documentation", "https://letsencrypt.org/docs/")), CY_APP, CY_DS, pillar="Security")

U("38", "Inbox Volume and Newsletter Bloat", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=inbox:stats\n"
  "| bin _time span=1w\n"
  "| stats sum(received) as received, sum(eval(if(category=\"newsletter\",received,0))) as newsletters by _time\n"
  "| eval newsletter_pct=round(100*newsletters/received,1)\n"
  "| sort - _time",
  "Trends how much email you receive and what share is newsletters, guiding a good unsubscribe purge.",
  "Seeing newsletters dominate your inbox is the motivation to unsubscribe and reclaim your attention.",
  "Ingest inbox stats into `index=personal`; schedule weekly and trend volume and newsletter share.",
  "Column chart of weekly email with newsletter percentage.",
  "It shows how much email you get and how much is newsletters, so you know what to unsubscribe from.",
  R(("Home Assistant — IMAP", "https://www.home-assistant.io/integrations/imap/")), CY_APP, CY_DS)

U("38", "Cloud-Storage Usage and Cost Runway", "low", "intermediate", ["Capacity"],
  "index=personal sourcetype=clouddrive:usage\n"
  "| stats latest(used_gb) as used, latest(quota_gb) as quota, avg(daily_growth_gb) as growth by provider\n"
  "| eval pct=round(100*used/quota,1), days_to_full=round((quota-used)/growth,0)\n"
  "| sort - pct",
  "Tracks how full each cloud drive is and predicts when you will hit the limit and face an upgrade.",
  "A storage runway lets you clean up or plan an upgrade calmly instead of hitting a full-drive wall mid-backup.",
  "Ingest cloud-storage usage into `index=personal`; predict days to full per provider.",
  "Gauge of cloud-storage usage with days-to-full.",
  "It tracks how full your cloud storage is and predicts when you will run out and need to pay for more.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), CY_APP, CY_DS)

U("38", "Suspicious Login Location Watch", "high", "advanced", ["Security", "Anomaly"],
  "index=personal sourcetype=breach:alert event=login\n"
  "| iplocation src_ip\n"
  "| stats values(Country) as countries, count as logins by account\n"
  "| eval foreign=if(mvcount(countries)>1,1,0)\n"
  "| where foreign=1",
  "Flags logins to your accounts from unexpected countries, an early sign of account compromise.",
  "A login from a country you have never visited is a classic takeover signal worth acting on immediately.",
  "Ingest account login events into `index=personal`; alert on logins from unexpected locations.",
  "Map of account login locations with foreign-login flags.",
  "It flags logins to your accounts from unexpected countries, an early sign someone else may be in.",
  R(("NCSC — protect your accounts", "https://www.ncsc.gov.uk/collection/top-tips-for-staying-secure-online")), CY_APP, CY_DS, pillar="Security")

U("38", "Password Age and Reuse Audit", "medium", "intermediate", ["Security", "Compliance"],
  "index=personal sourcetype=breach:alert event=account_inventory\n"
  "| eval age_days=round((now()-last_changed)/86400,0)\n"
  "| stats latest(age_days) as age, latest(reused) as reused by account\n"
  "| where age>365 OR reused=\"true\"\n"
  "| sort - age",
  "Surfaces accounts with old or reused passwords, the ones most worth updating in your manager.",
  "Old and reused passwords are the weakest links; a targeted list makes a password refresh quick and high-impact.",
  "Ingest password-manager metadata into `index=personal`; flag stale or reused passwords.",
  "Table of accounts with old or reused passwords.",
  "It finds accounts with old or repeated passwords, the ones most worth updating to stay safe.",
  R(("NCSC — password guidance", "https://www.ncsc.gov.uk/collection/passwords")), CY_APP, CY_DS, pillar="Security")

U("38", "Data-Broker Opt-Out Tracker", "low", "intermediate", ["Compliance"],
  "index=personal sourcetype=breach:alert event=optout\n"
  "| stats latest(status) as status, latest(_time) as updated by broker\n"
  "| eval stale=if(status=\"listed\" OR (now()-updated)>15552000,1,0)\n"
  "| where stale=1\n"
  "| sort broker",
  "Tracks your data-broker opt-out requests and flags those that lapsed or where you have reappeared.",
  "Data brokers re-list you over time; tracking opt-outs keeps your personal data off people-search sites.",
  "Log opt-out requests and re-checks into `index=personal`; flag brokers to re-submit.",
  "Table of data brokers needing an opt-out refresh.",
  "It tracks your requests to remove your details from data brokers and flags when you reappear on them.",
  R(("Privacy Rights Clearinghouse", "https://privacyrights.org/")), CY_APP, CY_DS)

U("38", "Digital Subscription & Account Sprawl", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=breach:alert event=account_inventory\n"
  "| stats count as accounts, sum(eval(if(last_used_days>365,1,0))) as dormant by category\n"
  "| sort - dormant",
  "Counts your online accounts and how many are dormant, prompting you to close the ones you no longer use.",
  "Every unused account is attack surface; pruning them shrinks your exposure and your digital clutter.",
  "Maintain an account inventory in `index=personal`; count dormant accounts by category.",
  "Bar chart of dormant accounts by category.",
  "It counts your online accounts and how many you no longer use, so you can close the old ones.",
  R(("NCSC — top tips online", "https://www.ncsc.gov.uk/collection/top-tips-for-staying-secure-online")), CY_APP, CY_DS, pillar="Security")

U("38", "Backup Freshness and 3-2-1 Check", "high", "intermediate", ["Availability", "Compliance"],
  "index=personal sourcetype=clouddrive:usage event=backup\n"
  "| stats latest(_time) as last_backup, dc(location) as copies by dataset\n"
  "| eval hours_since=round((now()-last_backup)/3600,1), at_risk=if(hours_since>48 OR copies<2,1,0)\n"
  "| where at_risk=1",
  "Checks each important dataset was backed up recently and to enough places, upholding the 3-2-1 rule.",
  "Backups fail silently; verifying freshness and copy count is the only way to trust them before you need them.",
  "Ingest backup-job results into `index=personal`; alert on stale or under-replicated backups.",
  "Table of datasets with stale or too-few backups.",
  "It checks your important files were backed up recently and in enough places, so nothing is lost.",
  R(("Backblaze — 3-2-1 backup", "https://www.backblaze.com/blog/the-3-2-1-backup-strategy/")), CY_APP, CY_DS)


# ===========================================================================
# 25.39  Seasonal & Silly
# ===========================================================================
SS_APP = ("Seasonal novelty feeds — smart Christmas-light power meters, a Halloween candy counter, "
          "advent/holiday countdowns, and festive trackers — streamed to Splunk HEC via MQTT and "
          "smart plugs.")
SS_DS = ("Festive lights (`festive:lights`), candy counter (`candy:counter`), countdown events "
         "(`countdown:event`), Santa tracker (`santa:tracker`).")
SMARTPLUG = ("Home Assistant — smart plug energy", "https://www.home-assistant.io/integrations/switch/")

U("39", "Christmas-Lights Power and Cost", "low", "beginner", ["Cost"],
  "index=personal sourcetype=festive:lights\n"
  "| bin _time span=1d\n"
  "| stats sum(kwh) as kwh by _time\n"
  "| eval cost=round(kwh*0.30,2)\n"
  "| sort - _time",
  "Adds up the electricity your festive lights use each day and what it costs, settling the annual debate.",
  "Putting a real daily cost on the Christmas display turns the yearly grumble into a fun, factual number.",
  "Meter the lights on a smart plug into `index=personal`; total daily energy and cost.",
  "Column chart of daily festive-light energy and cost.",
  "It adds up what your Christmas lights cost to run each day, settling the yearly family debate.",
  R(SMARTPLUG), SS_APP, SS_DS)

U("39", "Halloween Candy Dispensing Counter", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=candy:counter\n"
  "| bin _time span=15m\n"
  "| stats sum(pieces) as candy, dc(visitor) as trick_or_treaters by _time\n"
  "| sort _time",
  "Counts trick-or-treaters and candy handed out through the evening, capturing the Halloween rush hour.",
  "A candy-per-quarter-hour chart is pure fun and genuinely helps you buy the right amount next year.",
  "Log dispenses (a button or sensor) into `index=personal`; chart candy and visitors over the evening.",
  "Time chart of candy given out and visitors on Halloween.",
  "It counts the trick-or-treaters and sweets you hand out, capturing the busy Halloween rush.",
  R(("ESPHome — binary sensor", "https://esphome.io/components/binary_sensor/")), SS_APP, SS_DS)

U("39", "Advent & Holiday Countdown", "low", "beginner", ["Availability"],
  "index=personal sourcetype=countdown:event\n"
  "| eval days_to=round((event_epoch-now())/86400,0)\n"
  "| where days_to>=0\n"
  "| sort days_to\n"
  "| head 10",
  "Counts down the days to the holidays and other big events you are looking forward to.",
  "A countdown builds anticipation and, more practically, keeps holiday preparation on schedule.",
  "Log key dates into `index=personal`; surface the nearest upcoming events with days remaining.",
  "Table of upcoming events with a days-to-go countdown.",
  "It counts down the days to Christmas, holidays, and other big events you are excited about.",
  R(("Home Assistant — calendar", "https://www.home-assistant.io/integrations/calendar/")), SS_APP, SS_DS)

U("39", "Festive Energy vs Rest-of-Year Baseline", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=festive:lights OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(sourcetype==\"festive:lights\",kwh,0))) as festive_kwh by _time\n"
  "| eventstats avg(festive_kwh) as yearly_avg\n"
  "| eval spike=round(festive_kwh-yearly_avg,1)\n"
  "| sort - festive_kwh",
  "Compares your festive-season electricity use against the rest of the year, quantifying the holiday spike.",
  "Seeing December light up on the energy chart is amusing and a gentle reminder of seasonal costs.",
  "Ingest festive energy into `index=personal`; compare the holiday months to your baseline.",
  "Column chart of festive energy versus yearly average.",
  "It compares how much extra electricity the festive season uses versus the rest of the year.",
  R(SMARTPLUG), SS_APP, SS_DS)

U("39", "Pumpkin-Carving to Rot Timer", "low", "beginner", ["Anomaly"],
  "index=personal sourcetype=candy:counter event=pumpkin\n"
  "| stats latest(freshness) as freshness, min(_time) as carved by pumpkin\n"
  "| eval age_days=round((now()-carved)/86400,1), rotting=if(freshness<30,1,0)\n"
  "| sort - age_days",
  "Tracks how many days your carved pumpkins have lasted and flags when they are turning, a silly seasonal classic.",
  "It is pure novelty, but it does tell you when to compost the pumpkin before it collapses on the doorstep.",
  "Log a pumpkin freshness estimate into `index=personal`; flag pumpkins past their prime.",
  "Table of pumpkins by age and freshness.",
  "It tracks how long your carved pumpkins last before they go mushy, a bit of seasonal fun.",
  R(("Home Assistant — template sensor", "https://www.home-assistant.io/integrations/template/")), SS_APP, SS_DS)

U("39", "New-Year Resolution Progress Board", "low", "beginner", ["Business"],
  "index=personal sourcetype=countdown:event category=resolution\n"
  "| stats latest(progress_pct) as progress, latest(target_date) as target by resolution\n"
  "| eval days_left=round((target-now())/86400,0)\n"
  "| sort progress",
  "Tracks progress on your New Year resolutions against their deadlines, keeping January's promises alive in June.",
  "Most resolutions fade by February; a visible progress board is exactly the accountability that keeps them going.",
  "Log resolution progress into `index=personal`; review percentage complete and days remaining.",
  "Bar chart of resolution progress with deadlines.",
  "It tracks how your New Year resolutions are going, keeping January's promises alive all year.",
  R(("Home Assistant — counter", "https://www.home-assistant.io/integrations/counter/")), SS_APP, SS_DS)

U("39", "Seasonal Daylight and Mood Tie-In", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=mood:entry OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1w\n"
  "| stats avg(eval(if(sourcetype==\"mood:entry\",mood_score,null()))) as mood, avg(daylight_hours) as daylight by _time\n"
  "| sort _time",
  "Lines up your mood with the changing daylight hours across the year, revealing any winter dip.",
  "Seeing mood track daylight can validate seasonal low mood and prompt helpful steps like a daylight lamp.",
  "Join mood with daylight hours in `index=personal`; trend both across the seasons.",
  "Dual-axis chart of mood and daylight hours over the year.",
  "It lines up your mood with the changing daylight through the year, showing any winter dip.",
  R(DAYLIO), SS_APP, SS_DS)

U("39", "Holiday Gift Budget Burn-Down", "low", "beginner", ["Cost"],
  "index=personal sourcetype=countdown:event category=gift_budget\n"
  "| stats sum(spent) as spent, latest(budget) as budget\n"
  "| eval remaining=budget-spent, pct=round(100*spent/budget,1)",
  "Tracks holiday gift spending against your budget so the festive season does not blow a hole in January.",
  "Gift budgets vanish quietly; a running burn-down keeps generosity and finances in balance.",
  "Log gift purchases into `index=personal`; track spend against the holiday budget.",
  "Progress bar of holiday gift budget used.",
  "It tracks your holiday gift spending against a budget, so the festive season does not break the bank.",
  R(FIREFLY), SS_APP, SS_DS)

U("39", "Garden-Gnome / Mascot Presence Cam", "low", "intermediate", ["Availability"],
  "index=personal sourcetype=candy:counter event=mascot_check\n"
  "| stats latest(present) as present, latest(_time) as last_seen\n"
  "| eval hours_missing=round((now()-last_seen)/3600,1), missing=if(present=\"false\",1,0)",
  "Keeps a light-hearted watch on a garden gnome or mascot and alerts if it goes missing, a playful use of a camera.",
  "It is deliberately silly, yet it doubles as a real presence check for any small outdoor object you care about.",
  "Run object detection on a garden cam into `index=personal`; alert if the mascot disappears.",
  "Single-value tile of mascot presence with time missing.",
  "It playfully keeps an eye on a garden gnome and tells you if it goes missing.",
  R(("Frigate — object detection", "https://frigate.video/")), SS_APP, SS_DS)

U("39", "Festive Playlist and Mood Boost", "low", "beginner", ["Analytics"],
  "index=personal (sourcetype=mood:entry OR sourcetype=festive:lights)\n"
  "| bin _time span=1d\n"
  "| stats avg(eval(if(sourcetype==\"mood:entry\",mood_score,null()))) as mood, max(eval(if(lights_on=\"true\",1,0))) as festive_on by _time\n"
  "| eval festive=if(festive_on=1,\"lights on\",\"lights off\")\n"
  "| stats avg(mood) as avg_mood by festive",
  "Compares your mood on days the festive lights were on versus off, testing whether the decorations really cheer you up.",
  "It is a bit of fun, but a genuine mood lift from decorations is a lovely reason to put them up early.",
  "Join mood with festive-light state in `index=personal`; compare average mood by whether the lights were on.",
  "Bar chart of average mood with festive lights on versus off.",
  "It checks whether your mood is better on days the festive lights are on, a cheerful bit of fun.",
  R(DAYLIO), SS_APP, SS_DS)


# ===========================================================================
# 25.40  Cross-Stream ML & the Personal Digital Twin
# ===========================================================================
DT_APP = ("The meta layer — correlating every `index=personal` feed (sleep, activity, mood, "
          "weather, spend, productivity, home telemetry) into daily life scores, personal SLOs, "
          "and cross-signal anomaly detection, all computed in Splunk.")
DT_DS = ("Daily life scores (`lifescore:daily`), personal SLO status (`personalslo:status`), "
         "cross-signal correlations (`correlation:pair`), plus every other `index=personal` "
         "sourcetype as input.")
SRE = ("Google — SRE book (SLOs)", "https://sre.google/sre-book/service-level-objectives/")

U("40", "Daily Life Score Composite", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=lifescore:daily\n"
  "| timechart span=1d avg(score) as life_score\n"
  "| eventstats avg(life_score) as base\n"
  "| eval good_day=if(life_score>base,1,0)",
  "Blends sleep, activity, mood, and productivity into a single daily life score you can watch trend.",
  "One honest composite is easier to act on than a dozen scattered metrics, turning self-tracking into a clear signal.",
  "Compute a weighted daily score from your feeds into `index=personal`; trend it over time.",
  "Line chart of the daily life score with a personal baseline.",
  "It blends your sleep, activity, mood, and focus into one daily score, a simple read on how life is going.",
  R(SRE), DT_APP, DT_DS)

U("40", "Personal SLO Error-Budget Dashboard", "low", "advanced", ["Reliability"],
  "index=personal sourcetype=personalslo:status\n"
  "| stats latest(attained_pct) as attained, latest(target_pct) as target by objective\n"
  "| eval error_budget=round(attained-target,1), breached=if(attained<target,1,0)\n"
  "| sort error_budget",
  "Treats your habits like service objectives — floss daily, sleep 7 hours, gym thrice weekly — with error budgets.",
  "Framing habits as SLOs with a little slack is forgiving yet accountable, exactly why the technique works at work.",
  "Define personal objectives in `index=personal`; track attainment against target and the remaining error budget.",
  "Table of personal SLOs with attainment and error budget.",
  "It treats your goals like promises with a little wiggle room, showing which you are keeping and which are slipping.",
  R(SRE), DT_APP, DT_DS)

U("40", "Cross-Signal Anomaly of the Day", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=correlation:pair\n"
  "| stats latest(zscore) as z, latest(detail) as detail by signal\n"
  "| where abs(z)>2.5\n"
  "| sort - z",
  "Scans every personal metric at once and surfaces the one behaving most abnormally today.",
  "A single anomaly-of-the-day cuts through dashboards to tell you the one thing actually worth a look.",
  "Compute per-signal z-scores across `index=personal`; surface the day's biggest outliers.",
  "Table of the most anomalous personal signals today.",
  "It scans all your personal data at once and points out the one thing that is most unusual today.",
  R(SRE), DT_APP, DT_DS)

U("40", "What Predicts My Best Days", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=correlation:pair target=life_score\n"
  "| stats latest(correlation) as r by driver\n"
  "| eval strength=abs(r)\n"
  "| sort - strength\n"
  "| head 10",
  "Ranks which inputs most strongly correlate with your best days, revealing your personal levers of wellbeing.",
  "Knowing that, say, morning exercise and early nights drive your good days makes self-improvement concrete.",
  "Compute correlations between drivers and your life score in `index=personal`; rank the strongest.",
  "Bar chart of drivers most correlated with good days.",
  "It works out what most often leads to your best days, revealing the habits that truly help you.",
  R(SRE), DT_APP, DT_DS)

U("40", "Weekly Personal Ops Review", "low", "intermediate", ["Business"],
  "index=personal sourcetype=lifescore:daily\n"
  "| bin _time span=1w\n"
  "| stats avg(score) as avg_score, min(score) as worst, max(score) as best by _time\n"
  "| sort - _time",
  "Produces a weekly summary of your life score, mirroring the ops review teams run on their systems.",
  "A regular personal review builds the habit of reflecting and adjusting, the real value behind all the tracking.",
  "Aggregate your life score weekly in `index=personal`; review average, best, and worst.",
  "Column chart of weekly life-score summary.",
  "It gives you a weekly summary of how things went, like a team's regular review but for your own life.",
  R(SRE), DT_APP, DT_DS)

U("40", "Habit Domino-Effect Map", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=correlation:pair\n"
  "| where abs(correlation)>0.4\n"
  "| stats values(driver) as drivers by outcome\n"
  "| sort outcome",
  "Maps how your habits cascade — good sleep to more exercise to better mood — showing the keystone ones.",
  "Finding the keystone habit that pulls the others along tells you where a single change has the biggest ripple.",
  "Compute pairwise habit correlations in `index=personal`; group strong links by outcome.",
  "Network view of linked habits and outcomes.",
  "It maps how your habits knock into each other, showing the one keystone change that improves everything.",
  R(SRE), DT_APP, DT_DS)

U("40", "Personal NOC House-Health Wall", "medium", "intermediate", ["Availability"],
  "index=personal sourcetype=personalslo:status category=house\n"
  "| stats latest(status) as status by system\n"
  "| eval down=if(status!=\"ok\",1,0)\n"
  "| sort - down",
  "Rolls up every home system — network, energy, security, climate — into one green-or-red status wall.",
  "A single house-health wall is the home version of a network operations centre, surfacing any problem at a glance.",
  "Summarise home-system health into `index=personal`; show a single status board.",
  "Status wall of home systems, green or red.",
  "It shows all your home systems on one board, green when fine and red when something needs attention.",
  R(SRE), DT_APP, DT_DS)

U("40", "Anomaly-Free Streak Across All Feeds", "low", "intermediate", ["Reliability"],
  "index=personal sourcetype=correlation:pair\n"
  "| bin _time span=1d\n"
  "| stats max(eval(if(abs(zscore)>3,1,0))) as had_anomaly by _time\n"
  "| streamstats current=t sum(eval(if(had_anomaly=0,1,0))) as clean_streak reset_after=\"(had_anomaly=1)\"\n"
  "| sort - _time",
  "Counts how many days in a row every personal signal stayed within normal range, a calm-life streak.",
  "A clean streak across all feeds is a satisfying, holistic sign that life is running smoothly.",
  "Detect daily anomalies across `index=personal`; track the anomaly-free streak.",
  "Single-value tile of the anomaly-free-day streak.",
  "It counts how many days in a row everything in your life stayed normal, a nice sign all is well.",
  R(SRE), DT_APP, DT_DS)

U("40", "Personal Digital-Twin Data Freshness", "medium", "intermediate", ["Data Quality"],
  "index=personal\n"
  "| stats latest(_time) as last_seen by sourcetype\n"
  "| eval hours_silent=round((now()-last_seen)/3600,1), stale=if(hours_silent>48,1,0)\n"
  "| where stale=1\n"
  "| sort - hours_silent",
  "Checks every feed powering your personal digital twin is still reporting, catching a broken integration.",
  "A digital twin is only as good as its data; a freshness sweep across all sourcetypes keeps the whole picture trustworthy.",
  "Track last-seen per sourcetype across `index=personal`; alert on any feed that has gone quiet.",
  "Table of personal feeds with time since last data.",
  "It checks every source of your life data is still updating, so nothing quietly stops feeding in.",
  R(SRE), DT_APP, DT_DS)

U("40", "Life-Score Forecast and Trend Alert", "low", "advanced", ["Anomaly"],
  "index=personal sourcetype=lifescore:daily\n"
  "| timechart span=1d avg(score) as score\n"
  "| trendline sma7(score) as trend\n"
  "| eval declining=if(score<trend AND trend<50,1,0)",
  "Smooths your life score into a trend and warns when it is drifting downward over a sustained stretch.",
  "A gentle downward-trend alert catches a slow slump early, when small corrections still turn things around.",
  "Compute a moving average of your life score in `index=personal`; alert on a sustained decline.",
  "Line chart of life score with a smoothed trend and alert band.",
  "It smooths your daily life score into a trend and warns if things are gradually sliding, so you can course-correct.",
  R(SRE), DT_APP, DT_DS)


# ===========================================================================
# 25.41  Micro-Mobility & Action Sports
# ===========================================================================
MM_APP = ("Micro-mobility and action-sport trackers — e-bike / e-scooter apps (VanMoof, Bosch "
          "eBike Flow), and skate / surf / snow session trackers (Trace, Slopes, Xensr) with IMU "
          "sensors — streamed to Splunk HEC via APIs and scripted inputs.")
MM_DS = ("E-bike rides (`ebike:ride`), scooter trips (`scooter:trip`), skate sessions "
         "(`skate:session`), surf sessions (`surf:session`), snow runs (`snow:run`).")
SLOPES = ("Slopes — ski/snowboard tracking", "https://getslopes.com/")
BOSCH = ("Bosch eBike Flow — app", "https://www.bosch-ebike.com/en/products/ebike-flow-app")

U("41", "E-Bike Range vs Battery Anxiety", "low", "beginner", ["Capacity", "Analytics"],
  "index=personal sourcetype=ebike:ride\n"
  "| eval km_per_pct=round(distance_km/battery_used_pct,2)\n"
  "| timechart span=1w avg(km_per_pct) as efficiency\n"
  "| eventstats avg(efficiency) as base\n"
  "| eval declining=if(efficiency<base*0.85,1,0)",
  "Trends how far your e-bike travels per percent of battery, so you can trust its real range on longer rides.",
  "A falling range-per-percent is the first sign of battery ageing and helps you plan trips without getting stranded.",
  "Ingest e-bike rides into `index=personal`; trend kilometres per battery percent and flag a decline.",
  "Line chart of e-bike efficiency (km per battery %) over time.",
  "It tracks how far your e-bike goes on each bit of battery, so you know you will make it home.",
  R(BOSCH), MM_APP, MM_DS)

U("41", "E-Scooter Commute Cost vs Public Transport", "low", "beginner", ["Cost"],
  "index=personal sourcetype=scooter:trip\n"
  "| bin _time span=1mon\n"
  "| stats sum(distance_km) as km, count as trips by _time\n"
  "| eval scooter_cost=round(km*0.05,2), transit_cost=round(trips*2.5,2), saved=round(transit_cost-scooter_cost,2)\n"
  "| sort - _time",
  "Compares the running cost of your e-scooter commute against what the same trips would cost on public transport.",
  "Seeing the monthly saving (or loss) tells you whether the scooter is really cheaper than the bus or train.",
  "Ingest scooter trips into `index=personal`; estimate cost against a transit fare baseline.",
  "Column chart of monthly scooter cost versus transit cost.",
  "It compares what your scooter commute costs against taking the bus, showing which is cheaper.",
  R(("Home Assistant — REST sensor", "https://www.home-assistant.io/integrations/rest/")), MM_APP, MM_DS)

U("41", "Skate Session Airtime and Trick Count", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=skate:session\n"
  "| stats sum(tricks_landed) as tricks, max(max_airtime_ms) as best_air, sum(duration_min) as minutes by session\n"
  "| eventstats avg(tricks) as avg_tricks\n"
  "| sort - _time",
  "Tracks tricks landed and best airtime per skate session from a board-mounted motion sensor.",
  "Objective session stats turn practice into visible progress and help you chase a new personal airtime record.",
  "Ingest skate IMU sessions into `index=personal`; review tricks and airtime per session.",
  "Table of skate sessions with tricks and best airtime.",
  "It counts your tricks and measures your biggest jumps each skate session, so you can see yourself improve.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), MM_APP, MM_DS)

U("41", "Surf Session Wave Count and Conditions", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=surf:session\n"
  "| stats sum(waves_caught) as waves, avg(swell_m) as swell, sum(paddle_km) as paddle by session\n"
  "| eval waves_per_hr=round(waves/(duration_min/60),1)\n"
  "| sort - _time",
  "Logs waves caught, paddle distance, and swell size each surf session, mapping your sessions to the conditions.",
  "Linking wave counts to conditions helps you learn which swells suit you and get the most from each session.",
  "Ingest surf-watch sessions into `index=personal`; review waves and conditions per session.",
  "Table of surf sessions with waves caught and swell.",
  "It logs how many waves you caught and the conditions each surf, helping you pick the best days.",
  R(("Surfline — forecasts", "https://www.surfline.com/")), MM_APP, MM_DS)

U("41", "Ski Day Vertical Metres and Runs", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=snow:run\n"
  "| bin _time span=1d\n"
  "| stats sum(vertical_m) as vertical, count as runs, max(top_speed_kmh) as top_speed by _time\n"
  "| sort - _time",
  "Totals the vertical metres, runs, and top speed of each ski or snowboard day, capturing the numbers behind the fun.",
  "Vertical-metre totals are the classic ski bragging right, and tracking them across a season shows how much you rode.",
  "Ingest ski-tracker runs into `index=personal`; total vertical, runs, and top speed per day.",
  "Column chart of daily vertical metres with run count.",
  "It adds up how far you descended, how many runs, and your top speed each ski day.",
  R(SLOPES), MM_APP, MM_DS)

U("41", "Action-Sport Crash and Big-Impact Log", "medium", "intermediate", ["Safety", "Anomaly"],
  "index=personal (sourcetype=skate:session OR sourcetype=snow:run OR sourcetype=surf:session)\n"
  "| where impact_g>6\n"
  "| stats count as hard_impacts, max(impact_g) as worst by sport\n"
  "| sort - worst",
  "Flags the hardest impacts across your action-sport sessions, a light-touch safety log for a rough day out.",
  "A record of big impacts is useful context after a fall and a gentle prompt to check gear or rest when they pile up.",
  "Ingest impact data from IMU sensors into `index=personal`; count and rank hard impacts per sport.",
  "Bar chart of hard impacts by sport with the worst reading.",
  "It flags your hardest falls across board and snow sports, a simple safety log for a rough day.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), MM_APP, MM_DS)

U("41", "E-Bike Maintenance Interval by Distance", "low", "beginner", ["Availability"],
  "index=personal sourcetype=ebike:ride\n"
  "| stats sum(distance_km) as total_km, latest(km_at_last_service) as serviced\n"
  "| eval since_service=total_km-serviced, due=if(since_service>500,1,0)",
  "Tracks kilometres ridden since your last e-bike service and reminds you when a chain or brake check is due.",
  "Distance-based servicing keeps an e-bike safe and efficient, catching worn brakes or a stretched chain in time.",
  "Ingest ride distances into `index=personal`; alert when distance since service passes an interval.",
  "Single-value tile of kilometres since last e-bike service.",
  "It tracks how far you have ridden since the last service and reminds you when the e-bike needs a check.",
  R(BOSCH), MM_APP, MM_DS)

U("41", "Micro-Mobility Modal Share of Commutes", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=ebike:ride OR sourcetype=scooter:trip)\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(purpose=\"commute\",distance_km,0))) as micro_km by _time\n"
  "| sort - _time",
  "Measures how many of your commuting kilometres are on an e-bike or scooter rather than a car.",
  "A rising micro-mobility share is a satisfying, measurable sign of a greener, cheaper, healthier commute.",
  "Ingest commute trips into `index=personal`; trend micro-mobility commute distance monthly.",
  "Column chart of monthly micro-mobility commute kilometres.",
  "It measures how much of your commute is by e-bike or scooter instead of the car.",
  R(("Home Assistant — utility meter", "https://www.home-assistant.io/integrations/utility_meter/")), MM_APP, MM_DS)

U("41", "Season Progression — Skill Trend", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=surf:session OR sourcetype=snow:run OR sourcetype=skate:session)\n"
  "| timechart span=1mon avg(skill_score) as skill by sport",
  "Trends a per-session skill score across a season so you can see steady improvement in your chosen sport.",
  "A season-long skill curve rewards consistency and shows whether coaching or practice is actually paying off.",
  "Ingest per-session skill scores into `index=personal`; trend by sport over the season.",
  "Line chart of skill score over the season by sport.",
  "It tracks your skill through the season across board and snow sports, showing steady improvement.",
  R(SLOPES), MM_APP, MM_DS)

U("41", "Weather Window Finder for Action Sports", "low", "advanced", ["Availability"],
  "index=personal (sourcetype=surf:session OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1d\n"
  "| stats avg(eval(if(sourcetype==\"ecowitt:obs\",wind_kmh,null()))) as wind, avg(swell_m) as swell by _time\n"
  "| eval good=if(wind<20 AND swell>1,1,0)\n"
  "| where good=1\n"
  "| sort - _time",
  "Highlights the upcoming days whose forecast conditions suit your sport, so you never miss a perfect window.",
  "Matching your logged good sessions to forecast conditions turns spare hours into well-timed sessions.",
  "Join session conditions with forecasts in `index=personal`; surface upcoming favourable days.",
  "Table of favourable upcoming days for your sport.",
  "It highlights the days coming up with the right weather for your sport, so you catch the good conditions.",
  R(("Surfline — forecasts", "https://www.surfline.com/")), MM_APP, MM_DS)


# ===========================================================================
# 25.42  Aviation & Flight Simulation
# ===========================================================================
AV_APP = ("Pilot and flight-sim telemetry — electronic logbooks (ForeFlight, LogTen Pro), Stratux / "
          "GDL90 avionics receivers, and Microsoft Flight Simulator / X-Plane SimConnect sessions — "
          "streamed to Splunk HEC via scripted inputs.")
AV_DS = ("Pilot logbook (`flightlog:entry`), avionics telemetry (`avionics:telemetry`), flight-sim "
         "sessions (`flightsim:session`), pre-flight checklists (`preflight:check`).")
FOREFLIGHT = ("ForeFlight — pilot app", "https://foreflight.com/")
FAA = ("FAA — currency & recency requirements", "https://www.faa.gov/")

U("42", "Pilot Currency and Recency Watch", "high", "intermediate", ["Compliance", "Availability"],
  "index=personal sourcetype=flightlog:entry\n"
  "| eval days_ago=round((now()-_time)/86400,0)\n"
  "| stats sum(eval(if(days_ago<=90 AND takeoffs>0,takeoffs,0))) as recent_to, sum(eval(if(days_ago<=90,landings,0))) as recent_ldg\n"
  "| eval current=if(recent_to>=3 AND recent_ldg>=3,\"current\",\"NOT current\")",
  "Checks your recent take-offs and landings against the 90-day passenger-currency rule so you know if you are legal to fly.",
  "Losing currency without noticing is a real risk for private pilots; an automatic check keeps you legal and safe.",
  "Ingest logbook entries into `index=personal`; compute rolling take-off and landing recency.",
  "Single-value tile of currency status with recent counts.",
  "It checks whether you have flown enough recently to legally carry passengers, a real rule for private pilots.",
  R(FAA), AV_APP, AV_DS)

U("42", "Flight Hours by Aircraft Type and Rating", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=flightlog:entry\n"
  "| stats sum(hours) as hours, count as flights by aircraft_type\n"
  "| sort - hours",
  "Totals your logged flight hours by aircraft type, the record you need for ratings, insurance, and hire.",
  "Accurate per-type totals matter for checkrides and renting aircraft, and are tedious to tally by hand.",
  "Ingest logbook entries into `index=personal`; total hours and flights per aircraft type.",
  "Bar chart of flight hours by aircraft type.",
  "It adds up your flying hours by aircraft type, the record you need for licences and hiring planes.",
  R(FOREFLIGHT), AV_DS and AV_APP, AV_DS)

U("42", "Own-Aircraft ADS-B Track and Altitude", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=avionics:telemetry\n"
  "| bin _time span=1min\n"
  "| stats max(altitude_ft) as alt, avg(groundspeed_kt) as gs by _time flight_id\n"
  "| stats max(alt) as peak_alt, avg(gs) as avg_gs by flight_id\n"
  "| sort - _time",
  "Reconstructs each flight's altitude and ground-speed profile from your own aircraft's ADS-B/GDL90 feed.",
  "A recorded track is great for post-flight review, sharing, and spotting habits in your climbs and descents.",
  "Ingest Stratux/GDL90 telemetry into `index=personal`; summarise altitude and speed per flight.",
  "Table of flights with peak altitude and average ground speed.",
  "It records the height and speed of each flight from your plane's own signal, for reviewing afterwards.",
  R(("Stratux — ADS-B receiver", "https://stratux.me/")), AV_APP, AV_DS)

U("42", "Pre-Flight Checklist Completion Audit", "high", "beginner", ["Safety", "Compliance"],
  "index=personal sourcetype=preflight:check\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as done, count as total by flight_id\n"
  "| eval pct=round(100*done/total,1), incomplete=if(done<total,1,0)\n"
  "| where incomplete=1",
  "Flags any flight where the pre-flight checklist was not fully completed, reinforcing a safety-critical habit.",
  "Checklist discipline saves lives in aviation; an audit that catches skipped items strengthens the habit.",
  "Log checklist completions into `index=personal`; flag flights with incomplete checklists.",
  "Table of flights with incomplete pre-flight checklists.",
  "It flags any flight where you did not finish the pre-flight checklist, reinforcing a life-saving habit.",
  R(FOREFLIGHT), AV_APP, AV_DS)

U("42", "Flight-Sim Landing Smoothness Score", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=flightsim:session event=landing\n"
  "| eval grade=case(touchdown_fpm>-100,\"butter\",touchdown_fpm>-300,\"good\",touchdown_fpm>-600,\"firm\",1=1,\"hard\")\n"
  "| stats count as landings by grade\n"
  "| sort grade",
  "Grades your flight-sim landings by touchdown rate, turning greaser hunting into a tracked skill.",
  "A landing-quality breakdown makes sim practice measurable and genuinely transfers to smoother real approaches.",
  "Ingest SimConnect landing events into `index=personal`; grade landings by descent rate.",
  "Bar chart of flight-sim landings by smoothness grade.",
  "It grades how smoothly you land in the flight simulator, turning practice into a fun skill to improve.",
  R(("MSFS — SimConnect SDK", "https://docs.flightsimulator.com/")), AV_APP, AV_DS)

U("42", "Cross-Country Flight Distance Log", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=flightlog:entry\n"
  "| where distance_nm>50\n"
  "| bin _time span=1y\n"
  "| stats sum(distance_nm) as nm, count as xc_flights by _time\n"
  "| sort - _time",
  "Totals your cross-country flying distance each year, tracking the long trips that build real experience.",
  "Cross-country hours are milestones for pilots; totalling them shows how your range and confidence grow.",
  "Ingest logbook entries into `index=personal`; total cross-country distance annually.",
  "Column chart of yearly cross-country distance.",
  "It adds up the long flights you make each year, tracking the trips that build real flying experience.",
  R(FOREFLIGHT), AV_APP, AV_DS)

U("42", "Sim vs Real Approach Consistency", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=flightsim:session OR sourcetype=avionics:telemetry) event=approach\n"
  "| eval src=if(sourcetype==\"flightsim:session\",\"sim\",\"real\")\n"
  "| stats avg(glideslope_dev) as avg_dev, stdev(glideslope_dev) as consistency by src\n"
  "| sort src",
  "Compares how consistently you fly the approach glideslope in the simulator versus real flights.",
  "Seeing sim and real approach precision side by side shows whether sim practice is sharpening the real thing.",
  "Ingest approach data from both sources into `index=personal`; compare glideslope deviation.",
  "Bar chart of approach consistency, sim versus real.",
  "It compares how steadily you fly the approach in the sim versus real flights, testing whether practice helps.",
  R(("MSFS — SimConnect SDK", "https://docs.flightsimulator.com/")), AV_APP, AV_DS)

U("42", "Medical & Rating Expiry Countdown", "high", "beginner", ["Compliance", "Availability"],
  "index=personal sourcetype=flightlog:entry event=certificate\n"
  "| eval days_to=round((expiry_epoch-now())/86400,0)\n"
  "| where days_to<120\n"
  "| sort days_to\n"
  "| table certificate days_to",
  "Counts down to the expiry of your medical, ratings, and flight review so none lapses unnoticed.",
  "A lapsed medical or review grounds you; an early countdown gives time to book renewals without a gap.",
  "Log certificate expiry dates into `index=personal`; alert as each approaches expiry.",
  "Table of pilot certificates by days to expiry.",
  "It counts down to when your pilot medical and ratings expire, so none lapses and grounds you.",
  R(FAA), AV_APP, AV_DS)

U("42", "Fuel Burn vs Book Figures", "medium", "advanced", ["Analytics"],
  "index=personal sourcetype=flightlog:entry\n"
  "| eval gph=round(fuel_gal/hours,1)\n"
  "| stats avg(gph) as actual_gph by aircraft_type\n"
  "| eval book_gph=8.5, delta=round(actual_gph-book_gph,1)\n"
  "| sort - delta",
  "Compares your actual fuel burn against the aircraft's published figures, a check on both technique and engine health.",
  "A creeping fuel burn can indicate a leaning technique to fix or an engine issue worth a mechanic's look.",
  "Ingest fuel and hours into `index=personal`; compare actual burn to book figures per type.",
  "Bar chart of actual versus book fuel burn by type.",
  "It compares how much fuel you actually use against the plane's official figures, a check on technique and engine.",
  R(FOREFLIGHT), AV_APP, AV_DS)

U("42", "Flight-Sim Hours Toward a Goal", "low", "beginner", ["Business"],
  "index=personal sourcetype=flightsim:session\n"
  "| bin _time span=1w\n"
  "| stats sum(duration_min) as minutes by _time\n"
  "| eval hours=round(minutes/60,1)\n"
  "| sort - _time",
  "Tracks your weekly flight-sim hours toward a training or currency-practice goal.",
  "Regular sim practice builds procedural skill cheaply; a weekly total keeps the habit going between real flights.",
  "Ingest sim sessions into `index=personal`; total hours per week.",
  "Column chart of weekly flight-sim hours.",
  "It tracks how many hours you spend in the flight simulator each week toward your goal.",
  R(("X-Plane — developer docs", "https://developer.x-plane.com/")), AV_APP, AV_DS)


# ===========================================================================
# 25.43  Boating & Marine
# ===========================================================================
BT_APP = ("Marine electronics — NMEA 2000 / SignalK boat networks, bilge, battery and shore-power "
          "sensors, anchor-watch GPS, and marine weather feeds — streamed to Splunk HEC via SignalK "
          "and scripted inputs.")
BT_DS = ("NMEA/SignalK data (`nmea:reading`), bilge pump (`bilge:event`), mooring/anchor watch "
         "(`mooring:status`), marine weather (`marineweather:forecast`).")
SIGNALK = ("SignalK — open marine data", "https://signalk.org/")

U("43", "Bilge-Pump Run Frequency Leak Watch", "high", "intermediate", ["Safety", "Anomaly"],
  "index=personal sourcetype=bilge:event event=pump_on\n"
  "| bin _time span=1h\n"
  "| stats count as cycles by _time\n"
  "| eventstats avg(cycles) as base, stdev(cycles) as sd\n"
  "| eval leak_suspect=if(cycles>base+3*sd,1,0)\n"
  "| where leak_suspect=1",
  "Watches how often the bilge pump runs and alerts when the rate spikes, an early sign the boat is taking on water.",
  "A bilge pump cycling far more than usual is the classic early warning of a leak that could sink a boat.",
  "Ingest bilge-pump events into `index=personal`; alert on an abnormal run rate.",
  "Time chart of bilge-pump cycles with a leak-alert band.",
  "It watches how often the bilge pump runs and warns if it spikes, an early sign the boat is leaking.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Anchor-Watch Drag Alarm", "high", "advanced", ["Safety", "Anomaly"],
  "index=personal sourcetype=mooring:status event=anchor\n"
  "| eval drift_m=round(sqrt(pow(lat_m-set_lat_m,2)+pow(lon_m-set_lon_m,2)),1)\n"
  "| where drift_m>swing_radius_m\n"
  "| sort - _time\n"
  "| table _time drift_m swing_radius_m",
  "Raises an alarm when the boat drifts beyond its anchor swing circle, warning that the anchor is dragging.",
  "A dragging anchor overnight can put a boat on the rocks; a drift alarm buys crucial time to react.",
  "Ingest GPS anchor-watch data into `index=personal`; alert when drift exceeds the swing radius.",
  "Map of anchor position versus swing circle with drift alerts.",
  "It sounds the alarm if the boat drifts too far from where you anchored, warning the anchor is slipping.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "House-Battery State-of-Charge Watch", "medium", "intermediate", ["Capacity", "Availability"],
  "index=personal sourcetype=nmea:reading measurement=battery\n"
  "| timechart span=15m min(soc_pct) as soc by bank\n"
  "| eval low=if(soc<50,1,0)",
  "Trends the house-battery charge on board and warns before it falls too low to run the fridge, lights, and pumps.",
  "Flat house batteries at anchor mean warm food and dead instruments; an early warning lets you run the engine in time.",
  "Ingest battery telemetry into `index=personal`; alert on low state of charge per bank.",
  "Line chart of battery state of charge by bank.",
  "It tracks the boat's batteries and warns before they run too low to power the fridge and lights.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Engine-Hours and Service Interval", "low", "beginner", ["Availability"],
  "index=personal sourcetype=nmea:reading measurement=engine\n"
  "| stats max(engine_hours) as hours, latest(hours_at_service) as serviced by engine\n"
  "| eval since=hours-serviced, due=if(since>100,1,0)",
  "Tracks engine hours since the last service and reminds you when an oil change or impeller check is due.",
  "Marine engines are serviced by the hour; missing an interval risks an expensive failure far from a mechanic.",
  "Ingest engine-hour telemetry into `index=personal`; alert when hours since service pass the interval.",
  "Single-value tile of engine hours since service.",
  "It tracks the boat engine's running hours and reminds you when it needs its next service.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Sailing Performance vs Polars", "low", "advanced", ["Performance"],
  "index=personal sourcetype=nmea:reading measurement=sailing\n"
  "| eval polar_pct=round(100*boatspeed_kt/target_speed_kt,1)\n"
  "| bin _time span=10min\n"
  "| stats avg(polar_pct) as performance by _time\n"
  "| sort - _time",
  "Compares your boat speed against its theoretical polar targets for the wind, measuring how well you are trimmed.",
  "Sailing to polars is how racers extract speed; a live performance percentage guides trim and course choices.",
  "Ingest speed and wind data into `index=personal`; compute performance against polar targets.",
  "Line chart of sailing performance versus polar targets.",
  "It compares your boat's speed to its ideal for the wind, showing how well the sails are trimmed.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Shore-Power and Galvanic Watch", "medium", "intermediate", ["Safety"],
  "index=personal sourcetype=nmea:reading measurement=shorepower\n"
  "| stats latest(connected) as connected, latest(leakage_ma) as leakage by _time\n"
  "| eval fault=if(leakage>30,1,0)\n"
  "| where fault=1",
  "Monitors shore-power connection and leakage current, flagging the faults behind galvanic corrosion and shock risk.",
  "Stray current at the dock corrodes fittings and endangers swimmers; catching leakage protects boat and people.",
  "Ingest shore-power telemetry into `index=personal`; alert on excessive leakage current.",
  "Table of shore-power sessions with leakage faults.",
  "It watches the boat's dock power for electrical leaks that cause corrosion and shock danger.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Marine Weather Window for Passage", "medium", "advanced", ["Availability"],
  "index=personal sourcetype=marineweather:forecast\n"
  "| eval good=if(wind_kt<20 AND wave_m<1.5 AND gust_kt<25,1,0)\n"
  "| where good=1 AND forecast_epoch>now()\n"
  "| sort forecast_epoch\n"
  "| table forecast_epoch wind_kt wave_m",
  "Finds the upcoming windows of calm-enough wind and sea state for a safe passage or day out.",
  "Choosing the right weather window is the core of safe boating; an automated finder removes guesswork from planning.",
  "Ingest marine forecasts into `index=personal`; surface upcoming safe windows.",
  "Table of upcoming safe weather windows.",
  "It finds the upcoming calm windows in the marine forecast that are safe for a trip out.",
  R(("NOAA — marine forecasts", "https://www.weather.gov/marine/")), BT_APP, BT_DS)

U("43", "Fresh-Water and Holding-Tank Levels", "low", "beginner", ["Capacity"],
  "index=personal sourcetype=nmea:reading measurement=tank\n"
  "| stats latest(level_pct) as level by tank\n"
  "| eval alert=case(tank=\"freshwater\" AND level<20,\"refill water\",tank=\"holding\" AND level>80,\"pump out soon\",1=1,\"ok\")\n"
  "| where alert!=\"ok\"",
  "Tracks fresh-water and waste holding-tank levels so you refill or pump out before either becomes a problem.",
  "Running out of water or overfilling the holding tank ruins a trip; level alerts keep the essentials sorted.",
  "Ingest tank sensors into `index=personal`; alert on low water or high holding-tank levels.",
  "Gauges of fresh-water and holding-tank levels.",
  "It tracks the boat's water and waste tanks so you top up or empty them before they cause trouble.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Trip Log — Nautical Miles and Time Underway", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=nmea:reading measurement=navigation\n"
  "| bin _time span=1d\n"
  "| stats sum(distance_nm) as nm, sum(eval(if(underway=\"true\",duration_min,0)))/60 as hours by _time\n"
  "| sort - _time",
  "Logs nautical miles covered and hours underway each day, building the cruising record every skipper keeps.",
  "A digital trip log captures the miles and hours automatically, feeding logbooks, insurance, and sea-time claims.",
  "Ingest navigation data into `index=personal`; total distance and time underway daily.",
  "Column chart of daily nautical miles with hours underway.",
  "It logs how far you sailed and how long you were out each day, the record every skipper keeps.",
  R(SIGNALK), BT_APP, BT_DS)

U("43", "Depth-Alarm Grounding Guard", "high", "beginner", ["Safety", "Anomaly"],
  "index=personal sourcetype=nmea:reading measurement=depth\n"
  "| where depth_m<safety_depth_m\n"
  "| stats min(depth_m) as shallowest, count as alerts by _time\n"
  "| sort - _time",
  "Alerts whenever the water depth falls below your safety margin, guarding against running aground.",
  "Shallow water appears fast; a depth alarm gives the seconds needed to turn away before grounding.",
  "Ingest depth-sounder data into `index=personal`; alert when depth drops below a safety threshold.",
  "Time chart of depth with grounding-alarm markers.",
  "It warns the moment the water gets too shallow, helping you avoid running the boat aground.",
  R(SIGNALK), BT_APP, BT_DS)


# ===========================================================================
# 25.44  Fishing, Hunting & Foraging
# ===========================================================================
FH_APP = ("Outdoor logs — fishing apps (Fishbrain), sonar / fishfinder exports, game/trail cameras, "
          "and foraging journals — streamed to Splunk HEC via APIs and scripted inputs.")
FH_DS = ("Fishing catches (`fishing:catch`), fishfinder sonar (`fishfinder:reading`), foraging "
         "finds (`foraging:find`), game-cam triggers (`gamecam:trigger`).")
FISHBRAIN = ("Fishbrain — fishing app", "https://fishbrain.com/")

U("44", "Catch Log — Species, Size, and Spot", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=fishing:catch\n"
  "| stats count as catches, max(length_cm) as biggest, values(spot) as spots by species\n"
  "| sort - catches",
  "Logs every catch by species, size, and location, building the fishing diary that reveals your best patterns.",
  "A structured catch log turns fishing luck into learnable patterns of species, spot, and personal-best size.",
  "Ingest catches into `index=personal`; summarise by species with biggest and spots.",
  "Table of catches by species with biggest fish and spots.",
  "It logs every fish you catch with its size and where, building a diary of your best spots.",
  R(FISHBRAIN), FH_APP, FH_DS)

U("44", "Bite-Time vs Conditions Correlation", "low", "advanced", ["Analytics"],
  "index=personal (sourcetype=fishing:catch OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1h\n"
  "| stats sum(eval(if(sourcetype==\"fishing:catch\",1,0))) as catches, avg(pressure_hpa) as pressure by _time\n"
  "| eval falling=if(pressure<1010,\"low/falling\",\"high\")\n"
  "| stats avg(catches) as avg_catches by falling",
  "Correlates your catch rate with barometric pressure and time of day to learn when the fish really bite.",
  "The old wisdom that fish bite on a falling barometer becomes testable against your own logged results.",
  "Join catches with weather in `index=personal`; compare catch rate by pressure trend.",
  "Bar chart of catch rate by barometric condition.",
  "It works out when the fish actually bite for you, based on weather and time of day.",
  R(FISHBRAIN), FH_APP, FH_DS)

U("44", "Personal-Best Leaderboard by Species", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=fishing:catch\n"
  "| stats max(weight_kg) as pb_weight, max(length_cm) as pb_length, latest(_time) as last by species\n"
  "| sort - pb_weight",
  "Keeps a personal-best leaderboard of your biggest fish per species, the record every angler wants.",
  "A living personal-best table celebrates milestones and gives you a clear target to beat next time out.",
  "Ingest catches into `index=personal`; track the biggest per species.",
  "Ranked table of personal-best fish by species.",
  "It keeps a record of your biggest fish of each kind, the personal bests every angler is proud of.",
  R(FISHBRAIN), FH_APP, FH_DS)

U("44", "Fishfinder Sonar — Bait-Ball Detection", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=fishfinder:reading\n"
  "| where target_strength_db>-45\n"
  "| bin _time span=1min\n"
  "| stats count as marks, avg(depth_m) as depth by _time\n"
  "| where marks>10\n"
  "| sort - _time",
  "Flags the moments your sonar shows dense fish marks, mapping where and how deep the bait balls hold.",
  "Turning raw sonar into logged hotspots helps you return to productive depths and structure another day.",
  "Ingest fishfinder readings into `index=personal`; flag dense fish-mark periods and depth.",
  "Time chart of sonar marks with depth of dense schools.",
  "It flags when your sonar shows lots of fish and how deep, so you can find them again.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), FH_APP, FH_DS)

U("44", "Foraging Finds Map and Seasonality", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=foraging:find\n"
  "| eval month=strftime(_time,\"%B\")\n"
  "| stats count as finds, values(location) as spots by species month\n"
  "| sort species",
  "Logs your foraging finds by species, spot, and month, learning the seasonal calendar of your patch.",
  "Foraging rewards memory of where and when things grow; a logged calendar makes your patch pay off year after year.",
  "Ingest foraging finds into `index=personal`; summarise by species and month.",
  "Table of foraging finds by species and season.",
  "It logs where and when you find wild mushrooms and plants, learning your patch's seasons.",
  R(("iNaturalist — species observations", "https://www.inaturalist.org/")), FH_APP, FH_DS)

U("44", "Game-Camera Wildlife Activity Clock", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=gamecam:trigger\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats count as sightings by species hour\n"
  "| sort species hour",
  "Maps when different animals pass your game camera through the day, revealing their movement patterns.",
  "Knowing an animal's active hours is invaluable for wildlife watching and ethical, well-timed hunting.",
  "Ingest game-cam triggers into `index=personal`; chart sightings by species and hour.",
  "Heatmap of wildlife sightings by species and hour.",
  "It maps what time of day different animals pass your camera, revealing their daily patterns.",
  R(("Home Assistant — image processing", "https://www.home-assistant.io/integrations/image_processing/")), FH_APP, FH_DS)

U("44", "Licence, Tag, and Season Compliance", "medium", "beginner", ["Compliance"],
  "index=personal sourcetype=fishing:catch event=regulation\n"
  "| eval days_to_expiry=round((licence_expiry-now())/86400,0)\n"
  "| where days_to_expiry<30 OR season_status=\"closed\"\n"
  "| table item days_to_expiry season_status",
  "Tracks your fishing and hunting licences, tags, and open seasons so you always stay within the rules.",
  "Fines and bans for an expired licence or closed season are avoidable; a compliance check keeps you legal.",
  "Log licences and season dates into `index=personal`; alert on expiries and closed seasons.",
  "Table of licences and seasons needing attention.",
  "It tracks your fishing and hunting licences and open seasons, keeping you within the law.",
  R(("Home Assistant — calendar", "https://www.home-assistant.io/integrations/calendar/")), FH_APP, FH_DS)

U("44", "Tackle and Gear Inventory", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=fishing:catch event=gear\n"
  "| stats latest(quantity) as qty, latest(condition) as condition by item\n"
  "| where qty<min_stock OR condition=\"worn\"\n"
  "| sort item",
  "Tracks your lures, lines, and gear, flagging what is worn or running low before the next trip.",
  "Discovering you are out of the right lure at the water is a wasted trip; an inventory check prevents it.",
  "Log gear stock into `index=personal`; flag low or worn items.",
  "Table of tackle needing restock or replacement.",
  "It tracks your fishing gear and flags what is worn or running low before your next trip.",
  R(FISHBRAIN), FH_APP, FH_DS)

U("44", "Catch-and-Release Survival Care Log", "low", "intermediate", ["Quality"],
  "index=personal sourcetype=fishing:catch event=release\n"
  "| stats avg(handling_time_s) as avg_handling, count as released by species\n"
  "| eval good_practice=if(avg_handling<30,1,0)\n"
  "| sort - released",
  "Tracks how quickly you handle and release fish, encouraging the gentle practice that helps them survive.",
  "Fast, careful handling dramatically improves catch-and-release survival; logging it keeps your practice honest.",
  "Log release handling times into `index=personal`; review average handling per species.",
  "Bar chart of average handling time by released species.",
  "It tracks how gently and quickly you release fish, helping them survive to be caught again.",
  R(("iNaturalist — species observations", "https://www.inaturalist.org/")), FH_APP, FH_DS)

U("44", "Best-Spot Ranking by Catch Rate", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=fishing:catch\n"
  "| stats count as catches, sum(hours_fished) as hours by spot\n"
  "| eval catch_rate=round(catches/hours,2)\n"
  "| where hours>=2\n"
  "| sort - catch_rate",
  "Ranks your fishing spots by catches per hour, cutting through nostalgia to show where you truly do best.",
  "Catch-per-hour reveals which spots are genuinely productive versus merely familiar, focusing limited time well.",
  "Ingest catches and hours by spot into `index=personal`; rank by catch rate.",
  "Bar chart of catch rate by fishing spot.",
  "It ranks your fishing spots by how many fish you catch per hour, showing where you really do best.",
  R(FISHBRAIN), FH_APP, FH_DS)


# ===========================================================================
# 25.45  Music-Making & Creator Analytics
# ===========================================================================
MU_APP = ("Music and creator telemetry — practice-tracker apps (Modacity), DAW project logs, and "
          "streaming/creator analytics (Spotify for Artists, YouTube Studio) — streamed to Splunk "
          "HEC via APIs and scripted inputs.")
MU_DS = ("Practice sessions (`practice:session`), DAW sessions (`daw:session`), release/streaming "
         "stats (`release:stats`), gig setlists (`setlist:play`).")
SPOTA = ("Spotify for Artists — API", "https://developer.spotify.com/")

U("45", "Instrument Practice Streak and Minutes", "low", "beginner", ["Business"],
  "index=personal sourcetype=practice:session\n"
  "| bin _time span=1d\n"
  "| stats sum(minutes) as minutes by _time\n"
  "| streamstats current=t sum(eval(if(minutes>0,1,0))) as streak reset_after=\"(minutes=0)\"\n"
  "| sort - _time",
  "Tracks daily practice minutes and your current streak, the single best predictor of musical progress.",
  "Consistent daily practice beats occasional marathons; a visible streak is exactly what keeps you at the instrument.",
  "Ingest practice sessions into `index=personal`; surface daily minutes and the streak.",
  "Calendar heatmap of practice days with the current streak.",
  "It tracks how many days in a row you practise your instrument, which keeps the habit going.",
  R(("Modacity — practice app", "https://www.modacity.co/")), MU_APP, MU_DS)

U("45", "Practice Time by Piece and Weak Spots", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=practice:session\n"
  "| stats sum(minutes) as minutes, avg(self_rating) as rating by piece\n"
  "| where minutes>0\n"
  "| sort rating",
  "Shows how much you have practised each piece against how well you rate it, exposing the ones needing work.",
  "Time-versus-mastery guides practice to where it pays, stopping you from over-drilling what you already know.",
  "Ingest practice sessions with self-ratings into `index=personal`; review minutes and rating per piece.",
  "Scatter of practice minutes versus self-rating per piece.",
  "It shows which pieces you have practised most and least mastered, so you know what to work on.",
  R(("Modacity — practice app", "https://www.modacity.co/")), MU_APP, MU_DS)

U("45", "Streaming Growth and Milestone Watch", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=release:stats\n"
  "| timechart span=1w sum(streams) as streams by track\n"
  "| untable _time track streams\n"
  "| streamstats sum(streams) as cumulative by track",
  "Trends the streams your released music earns each week and tracks cumulative milestones per track.",
  "For an independent musician, a clear growth trend shows which tracks resonate and where promotion works.",
  "Ingest streaming stats into `index=personal`; trend weekly streams and cumulative totals per track.",
  "Line chart of weekly streams with cumulative milestones.",
  "It tracks how many times your released songs are streamed each week, showing which ones are catching on.",
  R(SPOTA), MU_APP, MU_DS)

U("45", "DAW Project Time-to-Finish", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=daw:session\n"
  "| stats sum(duration_min) as minutes, min(_time) as started, max(_time) as touched, latest(status) as status by project\n"
  "| eval days_active=round((touched-started)/86400,1), hours=round(minutes/60,1)\n"
  "| where status!=\"released\"\n"
  "| sort - hours",
  "Tracks hours spent and elapsed days per music project, surfacing the unfinished tracks stuck in limbo.",
  "Most home producers have a graveyard of half-finished projects; this nudges you to finish one before starting three.",
  "Ingest DAW session logs into `index=personal`; review time invested in unfinished projects.",
  "Table of unfinished projects by hours invested.",
  "It tracks how long you spend on each music project and which ones are stuck unfinished.",
  R(("Ableton — Live", "https://www.ableton.com/")), MU_APP, MU_DS)

U("45", "Setlist Performance and Song Rotation", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=setlist:play\n"
  "| stats count as times_played, latest(_time) as last_played by song\n"
  "| eval days_since=round((now()-last_played)/86400,0)\n"
  "| sort - times_played",
  "Tracks which songs you play live most and which have dropped out of rotation, balancing your set.",
  "A rotation view keeps sets fresh, retires tired songs, and makes sure crowd favourites still get played.",
  "Ingest gig setlists into `index=personal`; review play counts and time since last performed.",
  "Table of songs by times played and days since last.",
  "It tracks which songs you play live most and which you have not played in a while, keeping sets fresh.",
  R(("setlist.fm — setlists", "https://www.setlist.fm/")), MU_APP, MU_DS)

U("45", "Listener Geography and Reach", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=release:stats event=geography\n"
  "| stats sum(listeners) as listeners by country\n"
  "| sort - listeners\n"
  "| head 15",
  "Maps where in the world your music is being heard, revealing the cities and countries to target for gigs.",
  "Knowing your listener geography turns a vague online presence into concrete decisions about touring and promotion.",
  "Ingest listener geography into `index=personal`; rank countries by listeners.",
  "Map of listeners by country.",
  "It maps where in the world people are listening to your music, showing where your fans are.",
  R(SPOTA), MU_APP, MU_DS)

U("45", "Practice Tempo Progress (BPM Ramp)", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=practice:session event=tempo\n"
  "| timechart span=1w max(clean_bpm) as bpm by piece",
  "Trends the fastest clean tempo you can play a piece at each week, proving your metronome work is paying off.",
  "A rising clean-BPM curve is objective evidence of technical progress that daily practice can otherwise hide.",
  "Ingest per-piece clean tempos into `index=personal`; trend maximum clean BPM weekly.",
  "Line chart of clean tempo (BPM) over time per piece.",
  "It tracks the fastest speed you can cleanly play a piece each week, proving your practice is working.",
  R(("Modacity — practice app", "https://www.modacity.co/")), MU_APP, MU_DS)

U("45", "Revenue Mix — Streams, Sales, and Gigs", "low", "intermediate", ["Cost", "Business"],
  "index=personal sourcetype=release:stats event=revenue\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as revenue by source _time\n"
  "| stats sum(revenue) as total by source\n"
  "| sort - total",
  "Breaks your music income down by source — streaming, sales, gigs, merch — so you know what actually pays.",
  "Understanding the revenue mix helps a musician invest effort where the money is rather than where it feels good.",
  "Ingest revenue events into `index=personal`; total income by source.",
  "Bar chart of music revenue by source.",
  "It breaks your music income down by streaming, sales, and gigs, showing what really pays.",
  R(SPOTA), MU_APP, MU_DS)

U("45", "Skipped-Track Retention Signal", "low", "advanced", ["Quality"],
  "index=personal sourcetype=release:stats event=engagement\n"
  "| stats avg(completion_pct) as retention, sum(streams) as streams by track\n"
  "| where streams>50\n"
  "| sort retention",
  "Surfaces which released tracks listeners skip early, a candid signal of where a song loses people.",
  "Low completion is honest feedback that no play count reveals, guiding what to fix in your next release.",
  "Ingest completion-rate data into `index=personal`; rank tracks by retention.",
  "Bar chart of listener retention by track.",
  "It shows which of your songs listeners skip early, honest feedback on what to improve.",
  R(SPOTA), MU_APP, MU_DS)

U("45", "Gear Acquisition vs Actual Use", "low", "intermediate", ["Inventory", "Cost"],
  "index=personal sourcetype=daw:session event=gear_use\n"
  "| stats sum(use_count) as uses, latest(price) as price by gear\n"
  "| eval cost_per_use=round(price/(uses+1),2)\n"
  "| sort - cost_per_use",
  "Compares what your instruments and plugins cost against how often you actually use them in projects.",
  "Gear acquisition syndrome is real; cost-per-use exposes the pedal or plugin that never earns its keep.",
  "Ingest gear-use events into `index=personal`; compute cost-per-use per item.",
  "Bar chart of cost-per-use by music gear.",
  "It compares what your music gear cost with how often you use it, revealing the impulse buys.",
  R(("Ableton — Live", "https://www.ableton.com/")), MU_APP, MU_DS)


# ===========================================================================
# 25.46  Tabletop RPG Campaigns
# ===========================================================================
RP_APP = ("Tabletop RPG telemetry — virtual-tabletop session logs (Roll20, Foundry VTT), campaign "
          "trackers (World Anvil), and XP / loot / NPC ledgers — streamed to Splunk HEC via scripted "
          "inputs.")
RP_DS = ("Campaign sessions (`campaign:session`), NPC ledger (`npc:ledger`), loot drops "
         "(`loot:drop`), XP awards (`xp:award`).")
FOUNDRY = ("Foundry VTT — virtual tabletop", "https://foundryvtt.com/")

U("46", "Campaign Session Cadence and Attendance", "low", "beginner", ["Availability"],
  "index=personal sourcetype=campaign:session\n"
  "| bin _time span=1mon\n"
  "| stats count as sessions, avg(players_present) as avg_attendance by _time campaign\n"
  "| sort - _time",
  "Tracks how often your campaign meets and how many players show up, the pulse of a healthy game group.",
  "Campaigns die from irregular sessions and dropping attendance; a cadence view helps a group stay committed.",
  "Ingest session logs into `index=personal`; trend session frequency and attendance.",
  "Column chart of monthly sessions with average attendance.",
  "It tracks how often your role-playing group meets and who shows up, keeping the campaign alive.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Party XP and Level-Up Forecast", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=xp:award\n"
  "| stats sum(xp) as total_xp, latest(next_level_xp) as needed by character\n"
  "| eval to_go=needed-total_xp, pct=round(100*total_xp/needed,1)\n"
  "| sort pct",
  "Tracks each character's experience toward the next level and forecasts who is closest to levelling up.",
  "A shared XP tracker keeps the table motivated and helps the game master pace encounters toward level milestones.",
  "Ingest XP awards into `index=personal`; track progress to the next level per character.",
  "Bar chart of XP progress to next level by character.",
  "It tracks each character's experience points and who is closest to levelling up.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Loot Ledger and Treasure Balance", "low", "beginner", ["Business"],
  "index=personal sourcetype=loot:drop\n"
  "| stats sum(gold_value) as loot_value, count as items by character\n"
  "| eventstats avg(loot_value) as party_avg\n"
  "| eval imbalance=round(loot_value-party_avg,0)\n"
  "| sort - imbalance",
  "Totals the treasure each character has gained and flags an unfair split before it causes table friction.",
  "Loot disputes sour campaigns; a transparent ledger keeps distribution fair and the party happy.",
  "Ingest loot drops into `index=personal`; total value per character and flag imbalance.",
  "Bar chart of loot value by character versus party average.",
  "It totals the treasure each character has and flags an unfair split before it causes arguments.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "NPC Roster and Recurring Characters", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=npc:ledger\n"
  "| stats count as appearances, latest(status) as status, latest(_time) as last_seen by npc\n"
  "| where status=\"alive\"\n"
  "| sort - appearances",
  "Keeps a roster of the non-player characters the party has met, tracking who recurs and who is still alive.",
  "A living NPC ledger helps a game master keep continuity and bring back characters the players remember.",
  "Ingest NPC ledger entries into `index=personal`; track appearances and status per NPC.",
  "Table of NPCs by appearances and status.",
  "It keeps a list of the characters the group has met, tracking who keeps coming back into the story.",
  R(("World Anvil — worldbuilding", "https://www.worldanvil.com/")), RP_APP, RP_DS)

U("46", "Session Pacing — Combat vs Roleplay", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=campaign:session\n"
  "| stats sum(combat_min) as combat, sum(roleplay_min) as roleplay, sum(exploration_min) as explore by campaign\n"
  "| eval combat_pct=round(100*combat/(combat+roleplay+explore),1)",
  "Breaks each session into combat, roleplay, and exploration time, revealing the true balance of your game.",
  "Knowing the real pacing helps a game master match the group's taste rather than accidentally over-doing combat.",
  "Log per-phase minutes into `index=personal`; compare combat, roleplay, and exploration share.",
  "Stacked bar of session time by activity type.",
  "It shows how much of each game session is fighting versus talking and exploring, revealing your group's style.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Dice-Fairness Audit for the Table", "low", "intermediate", ["Data Quality"],
  "index=personal sourcetype=xp:award event=roll\n"
  "| stats count as rolls, avg(d20) as avg_roll by player\n"
  "| eval expected=10.5, deviation=round(avg_roll-expected,2)\n"
  "| where rolls>=30\n"
  "| sort - deviation",
  "Audits each player's long-run d20 average to check whether a lucky-feeling set of dice is actually skewed.",
  "Over enough rolls, a genuinely biased die shows up; this settles good-natured accusations at the table with data.",
  "Ingest roll data into `index=personal`; compare each player's average to the expected value.",
  "Bar chart of average roll deviation by player.",
  "It checks whether anyone's dice are genuinely lucky or unlucky over many rolls, settling table debates.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Character Survival and Death Log", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=campaign:session event=downed\n"
  "| stats count as times_downed, sum(eval(if(outcome=\"died\",1,0))) as deaths by character\n"
  "| sort - times_downed",
  "Logs how often each character has been knocked out or killed, the war stories a long campaign accumulates.",
  "A downed-and-died tally is both a fun record and a signal of encounters that may be too deadly.",
  "Ingest downed events into `index=personal`; count knockouts and deaths per character.",
  "Bar chart of times downed and deaths by character.",
  "It logs how often each hero has been knocked out or killed, the war stories of a long campaign.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Plot-Thread Tracker and Loose Ends", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=campaign:session event=plot_thread\n"
  "| stats latest(status) as status, latest(_time) as updated by thread\n"
  "| eval stale_days=round((now()-updated)/86400,0)\n"
  "| where status=\"open\" AND stale_days>60\n"
  "| sort - stale_days",
  "Tracks open story threads and flags the ones the party has not touched in a while, so none is forgotten.",
  "Dangling plot threads frustrate players; a loose-ends tracker helps the game master weave them back in.",
  "Log plot threads into `index=personal`; flag long-dormant open threads.",
  "Table of open plot threads by days since last touched.",
  "It tracks the open story threads and flags ones the group has forgotten, so the plot stays tight.",
  R(("World Anvil — worldbuilding", "https://www.worldanvil.com/")), RP_APP, RP_DS)

U("46", "Spotlight Balance Across Players", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=campaign:session event=spotlight\n"
  "| stats sum(spotlight_min) as spotlight by player\n"
  "| eventstats avg(spotlight) as fair_share\n"
  "| eval delta=round(spotlight-fair_share,0)\n"
  "| sort delta",
  "Measures how much spotlight time each player gets, helping the game master share the limelight fairly.",
  "Quiet players drift away when overshadowed; a spotlight balance nudges a fairer, more engaging table.",
  "Log spotlight minutes into `index=personal`; compare each player to the fair share.",
  "Bar chart of spotlight time by player versus fair share.",
  "It measures how much attention each player gets in the story, helping share the spotlight fairly.",
  R(FOUNDRY), RP_APP, RP_DS)

U("46", "Campaign Length and Milestone Timeline", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=campaign:session\n"
  "| stats min(_time) as start, max(_time) as latest, count as sessions, sum(duration_min) as minutes by campaign\n"
  "| eval months=round((latest-start)/2629800,1), hours=round(minutes/60,0)\n"
  "| sort - hours",
  "Summarises how long each campaign has run in sessions, months, and total hours played.",
  "Seeing a campaign's total investment is a satisfying record and helps set expectations for finishing the story.",
  "Ingest session logs into `index=personal`; summarise length and total hours per campaign.",
  "Table of campaigns by sessions, months, and total hours.",
  "It sums up how long each campaign has run in sessions and total hours, a record of the adventure.",
  R(FOUNDRY), RP_APP, RP_DS)


# ===========================================================================
# 25.47  Reading & Second Brain
# ===========================================================================
RB_APP = ("Reading and knowledge-management telemetry — Goodreads / StoryGraph libraries, Kindle "
          "highlights (Readwise), and note-graph exports (Obsidian, Notion) — streamed to Splunk "
          "HEC via APIs and scripted inputs.")
RB_DS = ("Reading progress (`reading:progress`), highlights (`highlight:capture`), note links "
         "(`note:link`), books finished (`book:finished`).")
READWISE = ("Readwise — highlights", "https://readwise.io/")
STORYGRAPH = ("The StoryGraph — reading tracker", "https://thestorygraph.com/")

U("47", "Books Finished vs Yearly Goal", "low", "beginner", ["Business"],
  "index=personal sourcetype=book:finished\n"
  "| bin _time span=1y\n"
  "| stats count as books by _time\n"
  "| eval goal=24, pct=round(100*books/goal,1)\n"
  "| sort - _time",
  "Counts the books you finish each year against your reading challenge, keeping the goal in sight.",
  "A visible progress bar against a reading goal is a proven nudge to pick the book over the phone.",
  "Ingest finished-book events into `index=personal`; track against a yearly goal.",
  "Progress bar of books finished versus goal.",
  "It counts the books you finish each year against your goal, nudging you to keep reading.",
  R(STORYGRAPH), RB_APP, RB_DS)

U("47", "Reading Pace and Time-to-Finish", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=reading:progress\n"
  "| stats max(pct_complete) as progress, avg(pages_per_day) as pace, latest(pages_left) as left by book\n"
  "| eval days_to_finish=round(left/pace,1)\n"
  "| where progress<100\n"
  "| sort days_to_finish",
  "Estimates how long you will take to finish each book you are reading, based on your recent pace.",
  "A finish forecast helps you decide whether to push on, and gently exposes the books you have quietly abandoned.",
  "Ingest reading progress into `index=personal`; estimate days to finish per book.",
  "Table of in-progress books by estimated days to finish.",
  "It estimates how long you will take to finish each book you are reading, at your current pace.",
  R(STORYGRAPH), RB_APP, RB_DS)

U("47", "Genre and Author Diversity", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=book:finished\n"
  "| stats count as books, dc(author) as authors by genre\n"
  "| sort - books",
  "Breaks your finished reading down by genre and author diversity, revealing your ruts and blind spots.",
  "Seeing that you read one genre almost exclusively is the nudge to broaden your horizons on purpose.",
  "Ingest finished books into `index=personal`; summarise by genre and distinct authors.",
  "Bar chart of books finished by genre.",
  "It breaks your reading down by genre and author, revealing whether you should branch out more.",
  R(STORYGRAPH), RB_APP, RB_DS)

U("47", "Highlights Captured per Book", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=highlight:capture\n"
  "| stats count as highlights by book\n"
  "| eventstats avg(highlights) as avg_h\n"
  "| sort - highlights",
  "Counts the passages you highlighted in each book, a proxy for which ones truly resonated with you.",
  "A highlight count surfaces the books worth revisiting and feeds a spaced-review habit that makes reading stick.",
  "Ingest highlights into `index=personal`; count per book.",
  "Bar chart of highlights captured per book.",
  "It counts the passages you highlighted in each book, showing which ones really spoke to you.",
  R(READWISE), RB_APP, RB_DS)

U("47", "Second-Brain Note Graph Growth", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=note:link\n"
  "| timechart span=1w dc(note) as notes, count as links\n"
  "| eval link_density=round(links/notes,2)",
  "Trends how your personal knowledge base grows in notes and the links between them over time.",
  "Link density, not note count, is what makes a second brain useful; trending it shows whether ideas are connecting.",
  "Ingest note-graph exports into `index=personal`; trend notes, links, and density weekly.",
  "Line chart of notes and links over time.",
  "It tracks how your personal notes and the links between them grow, building a useful second brain.",
  R(("Obsidian — knowledge base", "https://obsidian.md/")), RB_APP, RB_DS)

U("47", "Orphan-Note Cleanup Finder", "low", "intermediate", ["Data Quality"],
  "index=personal sourcetype=note:link\n"
  "| stats sum(inbound) as inbound, sum(outbound) as outbound by note\n"
  "| where inbound=0 AND outbound=0\n"
  "| sort note",
  "Finds notes with no links in or out — the orphans that make a knowledge base messy and hard to navigate.",
  "Orphan notes are dead weight; surfacing them prompts you to connect or prune them and keep the vault tidy.",
  "Ingest link data into `index=personal`; surface notes with zero links.",
  "Table of orphan notes to connect or archive.",
  "It finds notes with no links to anything, the loose ends that clutter your knowledge base.",
  R(("Obsidian — knowledge base", "https://obsidian.md/")), RB_APP, RB_DS)

U("47", "Reading Time-of-Day Habits", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=reading:progress\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats sum(minutes) as minutes by hour\n"
  "| sort - minutes",
  "Maps when in the day you actually read, revealing whether your reading habit lives at breakfast or bedtime.",
  "Knowing your natural reading windows helps you protect them and build a more reliable habit.",
  "Ingest reading sessions into `index=personal`; total minutes by hour of day.",
  "Column chart of reading minutes by hour.",
  "It shows what time of day you actually read, so you can protect your best reading moments.",
  R(STORYGRAPH), RB_APP, RB_DS)

U("47", "To-Be-Read Pile and Book Cost-Per-Read", "low", "intermediate", ["Inventory", "Cost"],
  "index=personal sourcetype=reading:progress event=inventory\n"
  "| stats sum(eval(if(status=\"unread\",1,0))) as unread, sum(eval(if(status=\"unread\",price,0))) as unread_value\n"
  "| eval note=\"the pile of shame\"",
  "Totals your unread books and what they cost — the affectionately named pile of shame.",
  "Quantifying the unread pile curbs buying more before finishing what you own, saving money and shelf space.",
  "Ingest book inventory into `index=personal`; total unread count and value.",
  "Single-value tiles of unread books and their value.",
  "It totals the books you own but have not read and what they cost, the famous pile of shame.",
  R(STORYGRAPH), RB_APP, RB_DS)

U("47", "Spaced-Review Resurfacing Queue", "low", "advanced", ["Availability"],
  "index=personal sourcetype=highlight:capture\n"
  "| eval days_since=round((now()-last_reviewed)/86400,0)\n"
  "| where days_since>review_interval_days\n"
  "| sort - days_since\n"
  "| head 20",
  "Surfaces highlights due for review on a spaced schedule, turning saved passages into knowledge you keep.",
  "Highlights you never revisit are wasted; a resurfacing queue is what turns reading into lasting learning.",
  "Ingest highlights with review intervals into `index=personal`; surface those due for review.",
  "Table of highlights due for spaced review.",
  "It resurfaces old highlights for you to review, so the best bits of your reading actually stick.",
  R(READWISE), RB_APP, RB_DS)

U("47", "DNF Rate and Book-Abandon Patterns", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=reading:progress\n"
  "| stats sum(eval(if(status=\"abandoned\",1,0))) as dnf, count as started by genre\n"
  "| eval dnf_rate=round(100*dnf/started,1)\n"
  "| where started>=3\n"
  "| sort - dnf_rate",
  "Tracks which genres you most often abandon partway, revealing where your taste and the hype diverge.",
  "A did-not-finish pattern helps you stop buying books you predictably will not finish, saving money and guilt.",
  "Ingest reading outcomes into `index=personal`; compute abandon rate by genre.",
  "Bar chart of did-not-finish rate by genre.",
  "It shows which kinds of books you tend to give up on, so you buy fewer you will not finish.",
  R(STORYGRAPH), RB_APP, RB_DS)


# ===========================================================================
# 25.48  Language Learning
# ===========================================================================
LL_APP = ("Language-learning telemetry — Duolingo / Babbel lesson exports, Anki spaced-repetition "
          "review logs, immersion trackers, and speaking-practice logs — streamed to Splunk HEC via "
          "APIs and scripted inputs.")
LL_DS = ("Lessons (`lesson:complete`), vocab reviews (`vocab:review`), immersion (`immersion:log`), "
         "speaking practice (`speaking:session`).")
ANKI = ("Anki — spaced repetition", "https://apps.ankiweb.net/")
DUO = ("Duolingo — language app", "https://www.duolingo.com/")

U("48", "Daily Lesson Streak and XP", "low", "beginner", ["Business"],
  "index=personal sourcetype=lesson:complete\n"
  "| bin _time span=1d\n"
  "| stats sum(xp) as xp, count as lessons by _time\n"
  "| streamstats current=t sum(eval(if(lessons>0,1,0))) as streak reset_after=\"(lessons=0)\"\n"
  "| sort - _time",
  "Tracks your daily language-lesson streak and XP, the habit engine behind long-term fluency.",
  "Language learning rewards daily consistency above all; a visible streak is exactly what sustains it.",
  "Ingest lesson completions into `index=personal`; surface daily XP and the streak.",
  "Calendar heatmap of study days with the current streak.",
  "It tracks your daily language-study streak, the steady habit that builds fluency over time.",
  R(DUO), LL_APP, LL_DS)

U("48", "Vocabulary Retention and Mature Cards", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=vocab:review\n"
  "| stats sum(eval(if(interval_days>=21,1,0))) as mature, count as total, avg(recall_pct) as retention by deck\n"
  "| eval mature_pct=round(100*mature/total,1)\n"
  "| sort - mature_pct",
  "Tracks how many vocabulary cards have matured into long-term memory and your overall recall rate.",
  "Mature-card counts and recall show whether words are truly sticking, not just being crammed and forgotten.",
  "Ingest Anki review logs into `index=personal`; track mature cards and retention per deck.",
  "Bar chart of mature-card percentage by deck.",
  "It tracks how many words have moved into long-term memory and how well you remember them.",
  R(ANKI), LL_APP, LL_DS)

U("48", "Review Backlog and Due-Card Load", "low", "beginner", ["Capacity", "Anomaly"],
  "index=personal sourcetype=vocab:review event=due\n"
  "| stats sum(due_count) as due by deck\n"
  "| eval overload=if(due>200,1,0)\n"
  "| sort - due",
  "Warns when your spaced-repetition review backlog balloons, before it becomes discouraging to catch up.",
  "A runaway due pile is the number-one reason people quit flashcards; an early warning keeps it manageable.",
  "Ingest due-card counts into `index=personal`; alert on a large review backlog.",
  "Bar chart of due-card backlog by deck.",
  "It warns when your flashcard reviews pile up too high, before it feels impossible to catch up.",
  R(ANKI), LL_APP, LL_DS)

U("48", "Immersion Hours Toward Fluency", "low", "intermediate", ["Business"],
  "index=personal sourcetype=immersion:log\n"
  "| bin _time span=1w\n"
  "| stats sum(minutes) as minutes by _time activity\n"
  "| stats sum(minutes) as weekly by _time\n"
  "| eval hours=round(weekly/60,1)\n"
  "| sort - _time",
  "Totals your weekly immersion hours — listening, watching, reading in the target language — toward a fluency estimate.",
  "Comprehensible-input hours are the truest predictor of fluency; totalling them makes an abstract journey concrete.",
  "Ingest immersion logs into `index=personal`; total weekly immersion hours.",
  "Column chart of weekly immersion hours.",
  "It adds up your hours of listening and reading in the language, the real path to fluency.",
  R(("Refold — immersion method", "https://refold.la/")), LL_APP, LL_DS)

U("48", "Speaking-Practice Frequency", "low", "beginner", ["Availability"],
  "index=personal sourcetype=speaking:session\n"
  "| bin _time span=1w\n"
  "| stats sum(minutes) as minutes, count as sessions by _time\n"
  "| eval enough=if(minutes>=60,1,0)\n"
  "| sort - _time",
  "Tracks how much you actually speak the language each week, the skill most learners neglect.",
  "Output practice lags input for most learners; a weekly speaking total nudges you to actually use the language.",
  "Ingest speaking sessions into `index=personal`; total weekly speaking minutes.",
  "Column chart of weekly speaking-practice minutes.",
  "It tracks how much you actually speak the language each week, the part most learners skip.",
  R(("italki — language tutors", "https://www.italki.com/")), LL_APP, LL_DS)

U("48", "Skill Balance — Reading vs Listening vs Speaking", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=immersion:log OR sourcetype=speaking:session)\n"
  "| eval skill=case(activity=\"reading\",\"reading\",activity IN (\"listening\",\"watching\"),\"listening\",sourcetype==\"speaking:session\",\"speaking\",1=1,\"other\")\n"
  "| bin _time span=1mon\n"
  "| stats sum(minutes) as minutes by skill _time\n"
  "| sort - _time",
  "Breaks your study time across reading, listening, and speaking, exposing the skill you are neglecting.",
  "Balanced practice avoids the lopsided learner who reads well but freezes in conversation; this keeps skills even.",
  "Ingest activity minutes into `index=personal`; compare time across the core skills.",
  "Stacked column chart of monthly minutes by skill.",
  "It shows how your study splits across reading, listening, and speaking, revealing what you neglect.",
  R(("Refold — immersion method", "https://refold.la/")), LL_APP, LL_DS)

U("48", "New Words Learned per Week", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=vocab:review event=learned\n"
  "| bin _time span=1w\n"
  "| stats sum(new_cards) as new_words by _time\n"
  "| eventstats avg(new_words) as avg_new\n"
  "| sort - _time",
  "Counts the new words you add to your vocabulary each week, a satisfying measure of steady growth.",
  "Watching your active vocabulary grow week by week is motivating and helps you pace new learning sustainably.",
  "Ingest new-card events into `index=personal`; total new words weekly.",
  "Column chart of new words learned per week.",
  "It counts the new words you learn each week, a satisfying sign your vocabulary is growing.",
  R(ANKI), LL_APP, LL_DS)

U("48", "Best Study-Time-of-Day for Recall", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=vocab:review\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats avg(recall_pct) as recall, count as reviews by hour\n"
  "| where reviews>=20\n"
  "| sort - recall",
  "Compares your recall accuracy by the hour you study, revealing when your brain retains vocabulary best.",
  "Studying when your recall is naturally highest makes every review more efficient, a small but real edge.",
  "Ingest reviews with timestamps into `index=personal`; compare recall by hour.",
  "Bar chart of recall accuracy by study hour.",
  "It shows what time of day you remember words best, so you can study when it works.",
  R(ANKI), LL_APP, LL_DS)

U("48", "Plateau Detector — Progress Stall", "medium", "advanced", ["Anomaly"],
  "index=personal sourcetype=lesson:complete\n"
  "| timechart span=1w sum(xp) as xp\n"
  "| trendline sma4(xp) as trend\n"
  "| eval stalled=if(xp<trend*0.6,1,0)",
  "Flags when your study output stalls well below its recent trend, the plateau that precedes quitting.",
  "Catching a motivation dip early lets you change methods or take a planned break before you drop the habit entirely.",
  "Ingest lesson XP into `index=personal`; alert when weekly output falls below trend.",
  "Line chart of weekly XP with a stall band.",
  "It notices when your language study slows down, the plateau that often comes before giving up.",
  R(DUO), LL_APP, LL_DS)

U("48", "Multi-Language Portfolio Balance", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=lesson:complete OR sourcetype=immersion:log)\n"
  "| bin _time span=1mon\n"
  "| stats sum(minutes) as minutes by language _time\n"
  "| stats sum(minutes) as total by language\n"
  "| sort - total",
  "Tracks how you split study time across the languages you are learning, guarding against neglecting one.",
  "Polyglots easily let one language slide; a portfolio view keeps a chosen balance intentional rather than accidental.",
  "Ingest study time by language into `index=personal`; compare totals across languages.",
  "Bar chart of study time by language.",
  "It shows how you split your time across the languages you are learning, so none gets neglected.",
  R(("Refold — immersion method", "https://refold.la/")), LL_APP, LL_DS)


# ===========================================================================
# 25.49  Wardrobe, Fashion & Beauty
# ===========================================================================
WD_APP = ("Wardrobe and grooming logs — closet apps (Whering, Stylebook), cost-per-wear trackers, "
          "skincare-routine logs, and smart-laundry cycles — streamed to Splunk HEC via APIs and "
          "scripted inputs.")
WD_DS = ("Wardrobe items (`wardrobe:item`), outfit wears (`outfit:wear`), skincare routines "
         "(`skincare:routine`), laundry cycles (`laundry:cycle`).")
WHERING = ("Whering — digital wardrobe", "https://whering.co.uk/")

U("49", "Cost-Per-Wear of Every Garment", "low", "intermediate", ["Cost", "Business"],
  "index=personal sourcetype=outfit:wear\n"
  "| stats count as wears, latest(price) as price by item\n"
  "| eval cost_per_wear=round(price/wears,2)\n"
  "| sort - cost_per_wear",
  "Divides each garment's price by how many times you have worn it, exposing your best and worst buys.",
  "Cost-per-wear is the single most useful clothing metric, rewarding versatile staples and shaming impulse buys.",
  "Ingest outfit wears into `index=personal`; compute cost-per-wear per item.",
  "Bar chart of cost-per-wear by garment.",
  "It works out how much each item of clothing costs per time you wear it, showing your best buys.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Closet Cost-Per-Wear Wardrobe Value", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=wardrobe:item\n"
  "| stats sum(price) as value, count as items by category\n"
  "| sort - value",
  "Totals what your wardrobe is worth by category, a revealing (sometimes alarming) inventory.",
  "Seeing the total value tied up in clothes informs insurance, decluttering, and future buying decisions.",
  "Ingest wardrobe inventory into `index=personal`; total value by category.",
  "Bar chart of wardrobe value by category.",
  "It totals what all your clothes are worth by type, a revealing look at your wardrobe.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Never-Worn and Declutter Candidates", "low", "beginner", ["Inventory"],
  "index=personal sourcetype=wardrobe:item\n"
  "| eval days_owned=round((now()-acquired_epoch)/86400,0)\n"
  "| where wears=0 AND days_owned>180\n"
  "| sort - days_owned",
  "Surfaces clothes you have owned for months but never worn, the prime candidates to donate or sell.",
  "The never-worn pile is where wardrobe money goes to die; surfacing it makes decluttering easy and guilt-free.",
  "Ingest wardrobe data into `index=personal`; flag long-owned unworn items.",
  "Table of never-worn items by days owned.",
  "It finds clothes you have owned for ages but never worn, perfect to donate or sell.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Outfit Rotation and Favourites", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=outfit:wear\n"
  "| stats count as wears, latest(_time) as last by item\n"
  "| eventstats avg(wears) as avg_wears\n"
  "| eval overworn=if(wears>avg_wears*2,1,0)\n"
  "| sort - wears",
  "Shows which items you wear far more than the rest, revealing your true favourites and rotation ruts.",
  "Knowing you cycle through the same few pieces helps you either embrace a capsule wardrobe or shop your own closet.",
  "Ingest wears into `index=personal`; rank items by wear count.",
  "Bar chart of wear count by item.",
  "It shows which clothes you wear far more than others, revealing your real favourites.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Skincare Routine Adherence", "low", "beginner", ["Compliance"],
  "index=personal sourcetype=skincare:routine\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(step=\"done\",1,0))) as done, dc(step_name) as planned by _time routine\n"
  "| eval adherence=round(100*done/planned,1)\n"
  "| stats avg(adherence) as avg_adherence by routine",
  "Tracks how consistently you complete your morning and evening skincare routines.",
  "Skincare results come from consistency, not products; an adherence view keeps the routine on track.",
  "Ingest routine steps into `index=personal`; track completion of each routine.",
  "Bar chart of routine adherence, morning versus evening.",
  "It tracks how consistently you do your skincare routine, which is what actually gets results.",
  R(("Home Assistant — to-do list", "https://www.home-assistant.io/integrations/todo/")), WD_APP, WD_DS)

U("49", "Product Finish-Date and Repurchase", "low", "intermediate", ["Inventory"],
  "index=personal sourcetype=skincare:routine event=product\n"
  "| eval daily_use=amount_per_use*uses_per_day, days_left=round(remaining_ml/daily_use,0)\n"
  "| where days_left<14\n"
  "| sort days_left",
  "Predicts when your skincare and beauty products will run out so you repurchase before hitting empty.",
  "Running out of a daily product mid-routine is annoying; a finish-date forecast keeps essentials stocked.",
  "Ingest product usage into `index=personal`; predict finish dates.",
  "Table of products by days until empty.",
  "It predicts when your skincare products will run out, so you can restock before they do.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), WD_APP, WD_DS)

U("49", "Laundry Load Efficiency and Cost", "low", "beginner", ["Cost"],
  "index=personal sourcetype=laundry:cycle\n"
  "| bin _time span=1mon\n"
  "| stats count as loads, avg(load_pct) as fullness, sum(kwh) as energy by _time\n"
  "| eval cost=round(energy*0.30,2)\n"
  "| sort - _time",
  "Tracks how full your laundry loads are and what they cost in energy, nudging you toward fuller, cheaper washes.",
  "Half-empty washes waste water, energy, and money; a fullness view encourages efficient full loads.",
  "Ingest smart-washer cycles into `index=personal`; track load fullness and energy cost.",
  "Column chart of monthly laundry loads with average fullness.",
  "It tracks how full your washing loads are and what they cost, nudging you to run fuller washes.",
  R(("Home Assistant — appliance", "https://www.home-assistant.io/integrations/")), WD_APP, WD_DS)

U("49", "Seasonal Wardrobe Readiness", "low", "intermediate", ["Availability"],
  "index=personal (sourcetype=wardrobe:item OR sourcetype=ecowitt:obs)\n"
  "| bin _time span=1d\n"
  "| stats avg(outdoor_temp_c) as temp, sum(eval(if(season=\"winter\" AND status=\"stored\",1,0))) as stored_winter by _time\n"
  "| where temp<8 AND stored_winter>0\n"
  "| sort - _time",
  "Reminds you to swap seasonal clothes out of storage when the weather turns, so you are never caught cold.",
  "Matching your wardrobe to the forecast means the warm coat is out before the first frost, not after.",
  "Join wardrobe status with weather in `index=personal`; alert when stored seasonal wear is needed.",
  "Table flagging seasonal wardrobe swaps due.",
  "It reminds you to get seasonal clothes out of storage when the weather turns, so you are ready.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Colour and Style Palette Analysis", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=wardrobe:item\n"
  "| stats count as items by colour\n"
  "| sort - items\n"
  "| head 12",
  "Breaks your wardrobe down by colour, revealing the palette you actually own versus what you think you wear.",
  "A colour breakdown highlights gaps and over-buying, helping you build a wardrobe that mixes and matches.",
  "Ingest wardrobe items into `index=personal`; count by colour.",
  "Bar chart of wardrobe items by colour.",
  "It breaks your clothes down by colour, showing the palette you really own.",
  R(WHERING), WD_APP, WD_DS)

U("49", "Spend-Per-Season Fashion Budget", "low", "beginner", ["Cost"],
  "index=personal sourcetype=wardrobe:item event=purchase\n"
  "| bin _time span=3mon\n"
  "| stats sum(price) as spend, count as items by _time\n"
  "| eval budget=300, over=if(spend>budget,1,0)\n"
  "| sort - _time",
  "Tracks clothing spend each season against a budget, keeping fashion enthusiasm within your means.",
  "Seasonal clothing spend creeps up unnoticed; a budget check keeps a wardrobe habit affordable.",
  "Ingest purchases into `index=personal`; total spend per season against a budget.",
  "Column chart of seasonal clothing spend with a budget line.",
  "It tracks what you spend on clothes each season against a budget, keeping fashion affordable.",
  R(WHERING), WD_APP, WD_DS)


# ===========================================================================
# 25.50  Sustainability & Zero-Waste
# ===========================================================================
SU_APP = ("Sustainability telemetry — carbon-footprint apps, home recycling scales, food-waste "
          "logs, and repair / reuse journals — streamed to Splunk HEC via APIs, MQTT, and scripted "
          "inputs.")
SU_DS = ("Carbon estimates (`carbon:estimate`), recycling weight (`recycling:weight`), food waste "
         "(`foodwaste:log`), repairs (`repair:event`).")
WATTTIME = ("WattTime — grid carbon intensity", "https://www.watttime.org/")

U("50", "Personal Carbon Footprint Trend", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=carbon:estimate\n"
  "| timechart span=1mon sum(kg_co2e) as footprint by category",
  "Trends your estimated carbon footprint month by month, broken down by transport, food, energy, and goods.",
  "A trended footprint turns good intentions into measurable progress and shows which changes actually move the needle.",
  "Ingest carbon estimates into `index=personal`; trend footprint by category.",
  "Stacked area chart of monthly carbon footprint by category.",
  "It tracks your carbon footprint month by month, showing where your impact comes from.",
  R(("UK Gov — greenhouse gas conversion factors", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting")), SU_APP, SU_DS)

U("50", "Recycling vs Landfill Diversion Rate", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=recycling:weight\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(stream=\"recycle\",kg,0))) as recycled, sum(kg) as total by _time\n"
  "| eval diversion_pct=round(100*recycled/total,1)\n"
  "| sort - _time",
  "Measures what share of your household waste is diverted from landfill into recycling and compost.",
  "A diversion rate turns a vague green intention into a number you can improve, load by load.",
  "Ingest weighed waste streams into `index=personal`; compute the diversion rate.",
  "Column chart of monthly landfill-diversion rate.",
  "It measures how much of your rubbish you recycle instead of sending to landfill.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), SU_APP, SU_DS)

U("50", "Food-Waste Reduction Tracker", "medium", "beginner", ["Analytics", "Cost"],
  "index=personal sourcetype=foodwaste:log\n"
  "| bin _time span=1w\n"
  "| stats sum(kg) as wasted, sum(est_value) as value by _time\n"
  "| eventstats avg(wasted) as base\n"
  "| eval improving=if(wasted<base,1,0)\n"
  "| sort - _time",
  "Tracks how much food you throw away each week and what it cost, turning waste into a number you can cut.",
  "Households bin a shocking amount of food; measuring it in weight and money is the strongest motivator to reduce it.",
  "Ingest food-waste logs into `index=personal`; trend weekly waste and its value.",
  "Column chart of weekly food waste with cost overlay.",
  "It tracks how much food you throw away each week and what it cost, helping you waste less.",
  R(("WRAP — Love Food Hate Waste", "https://www.lovefoodhatewaste.com/")), SU_APP, SU_DS)

U("50", "Repair-vs-Replace Savings Log", "low", "intermediate", ["Cost"],
  "index=personal sourcetype=repair:event\n"
  "| stats sum(eval(replace_cost-repair_cost)) as saved, count as repairs by category\n"
  "| sort - saved",
  "Totals the money and waste saved by repairing things instead of replacing them.",
  "Quantifying repair savings rewards the fix-it habit and pushes back on the throwaway default.",
  "Ingest repair events into `index=personal`; total savings versus replacement cost.",
  "Bar chart of repair savings by category.",
  "It totals the money you save by fixing things instead of buying new, rewarding the repair habit.",
  R(("iFixit — repair guides", "https://www.ifixit.com/")), SU_APP, SU_DS)

U("50", "Grid-Carbon-Aware Appliance Timing", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=carbon:estimate event=grid\n"
  "| timechart span=1h avg(grid_intensity_gco2) as intensity\n"
  "| eventstats min(intensity) as cleanest\n"
  "| eval clean_window=if(intensity<cleanest*1.2,1,0)",
  "Highlights the hours when your electricity grid is cleanest, so you time the dishwasher and car charging to match.",
  "Shifting flexible loads to low-carbon hours cuts emissions for free — this shows exactly when to run them.",
  "Ingest grid carbon intensity into `index=personal`; surface the cleanest hours to run appliances.",
  "Time chart of grid carbon intensity with clean windows.",
  "It shows when the electricity grid is cleanest, so you run appliances at the greenest times.",
  R(WATTTIME), SU_APP, SU_DS)

U("50", "Single-Use Plastic Count", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=foodwaste:log event=packaging\n"
  "| bin _time span=1w\n"
  "| stats sum(single_use_items) as plastics by _time\n"
  "| eventstats avg(plastics) as base\n"
  "| eval improving=if(plastics<base,1,0)\n"
  "| sort - _time",
  "Counts the single-use plastic items entering your home each week, making an invisible habit visible.",
  "You cannot cut what you cannot see; a weekly plastic count is the first step to meaningful reduction.",
  "Log single-use items into `index=personal`; trend the weekly count.",
  "Column chart of weekly single-use plastic count.",
  "It counts the single-use plastics coming into your home each week, so you can cut them down.",
  R(("WRAP — Love Food Hate Waste", "https://www.lovefoodhatewaste.com/")), SU_APP, SU_DS)

U("50", "Water Footprint by Activity", "low", "intermediate", ["Analytics"],
  "index=personal (sourcetype=watermeter:flow OR sourcetype=carbon:estimate)\n"
  "| bin _time span=1mon\n"
  "| stats sum(litres) as litres by activity _time\n"
  "| stats sum(litres) as total by activity\n"
  "| sort - total",
  "Breaks your household water use down by activity — showers, laundry, garden — to target the biggest savings.",
  "Knowing where your water actually goes focuses effort on the habits that save the most, not the most visible ones.",
  "Ingest water use by activity into `index=personal`; compare totals.",
  "Bar chart of water use by activity.",
  "It breaks your water use down by activity, showing where you can save the most.",
  R(("Home Assistant — utility meter", "https://www.home-assistant.io/integrations/utility_meter/")), SU_APP, SU_DS)

U("50", "Second-Hand vs New Purchase Ratio", "low", "beginner", ["Analytics"],
  "index=personal sourcetype=repair:event event=acquisition\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(source=\"secondhand\",1,0))) as used, count as total by _time\n"
  "| eval secondhand_pct=round(100*used/total,1)\n"
  "| sort - _time",
  "Tracks how much of what you buy is second-hand rather than new, a core zero-waste habit.",
  "A rising second-hand share cuts waste and cost at once, and seeing it grow reinforces the choice.",
  "Ingest acquisitions into `index=personal`; compute the second-hand share monthly.",
  "Column chart of second-hand purchase percentage.",
  "It tracks how much you buy second-hand instead of new, a key part of living with less waste.",
  R(("iFixit — repair guides", "https://www.ifixit.com/")), SU_APP, SU_DS)

U("50", "Compost Yield and Kitchen Diversion", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=recycling:weight stream=compost\n"
  "| bin _time span=1mon\n"
  "| stats sum(kg) as composted by _time\n"
  "| eventstats sum(composted) as total_diverted\n"
  "| sort - _time",
  "Tracks how much kitchen and garden waste you compost, diverting it from the bin into the garden.",
  "Composting closes a loop most households ignore; a running total makes the environmental win tangible.",
  "Ingest composted weight into `index=personal`; trend monthly and total diverted.",
  "Column chart of monthly composted weight.",
  "It tracks how much kitchen waste you compost instead of binning, feeding your garden.",
  R(("Home Assistant — sensors", "https://www.home-assistant.io/integrations/sensor/")), SU_APP, SU_DS)

U("50", "Sustainability Goal Scorecard", "low", "advanced", ["Business"],
  "index=personal (sourcetype=carbon:estimate OR sourcetype=recycling:weight OR sourcetype=foodwaste:log)\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(sourcetype==\"carbon:estimate\",kg_co2e,0))) as carbon, sum(eval(if(sourcetype==\"recycling:weight\" AND stream==\"recycle\",kg,0))) as recycled, sum(eval(if(sourcetype==\"foodwaste:log\",kg,0))) as waste by _time\n"
  "| eval score=round(recycled*2 - carbon*0.1 - waste*3,0)\n"
  "| sort - _time",
  "Combines carbon, recycling, and food-waste metrics into one monthly sustainability score to track overall progress.",
  "A single scorecard makes competing green efforts comparable and turns sustainability into a goal you can steadily improve.",
  "Combine sustainability feeds in `index=personal`; compute a composite monthly score.",
  "Line chart of the monthly sustainability score.",
  "It combines your recycling, waste, and carbon into one monthly green score to track overall progress.",
  R(("UK Gov — greenhouse gas conversion factors", "https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting")), SU_APP, SU_DS)


# ===========================================================================
# 25.51  Chronic-Condition Management
# ===========================================================================
CC_APP = ("Chronic-condition self-management — symptom and medication trackers (Bearable, "
          "MyTherapy), connected blood-pressure cuffs and glucometers, and lab-result portals — "
          "streamed to Splunk HEC via APIs and scripted inputs.")
CC_DS = ("Symptom logs (`condition:symptom`), medication doses (`medication:dose`), vitals "
         "readings (`vitals:reading`), flare-up events (`flareup:event`), lab results "
         "(`labresult:value`).")
CC_REF = ("CDC — Chronic Disease self-management", "https://www.cdc.gov/chronicdisease/index.htm")

U("51", "Medication Adherence Rate", "medium", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=medication:dose\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(status=\"taken\",1,0))) as taken, sum(eval(if(status=\"scheduled\",1,0))) as scheduled by _time\n"
  "| eval adherence_pct=round(100*taken/scheduled,1)\n"
  "| sort - _time",
  "Compares medication doses actually taken against those scheduled each week so you can see how consistently you are following your plan.",
  "Adherence is the single biggest factor in managing most chronic conditions; a weekly number makes slippage visible before it affects your health.",
  "Ingest scheduled and taken doses into `index=personal`; compute weekly adherence and alert below your target.",
  "Column chart of weekly adherence percentage with a target line.",
  "It checks how many of your pills you actually took each week compared with what you were meant to, so nothing slips.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Symptom Severity Trend", "medium", "beginner", ["Analytics", "Anomaly"],
  "index=personal sourcetype=condition:symptom\n"
  "| timechart span=1d avg(severity) as avg_severity by symptom\n"
  "| untable _time symptom avg_severity",
  "Trends how severe each of your tracked symptoms is over time so you and your doctor can spot whether things are improving or worsening.",
  "A clear severity trend turns a vague sense of 'feeling worse' into evidence you can bring to an appointment and act on.",
  "Ingest daily symptom scores into `index=personal`; trend each symptom and review before appointments.",
  "Line chart of symptom severity over time, one line per symptom.",
  "It shows whether your symptoms are getting better or worse over the weeks, giving your doctor something real to look at.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Flare-Up Trigger Correlation", "medium", "advanced", ["Analytics", "Anomaly"],
  "index=personal (sourcetype=flareup:event OR sourcetype=condition:symptom)\n"
  "| bin _time span=1d\n"
  "| stats max(eval(if(sourcetype=\"flareup:event\",1,0))) as flare, values(trigger) as triggers by _time\n"
  "| stats count as days, sum(flare) as flare_days by triggers\n"
  "| eval flare_rate=round(100*flare_days/days,1)\n"
  "| sort - flare_rate",
  "Looks at what you logged around each flare-up — foods, stress, weather, sleep — to surface the triggers most often present before symptoms spike.",
  "Identifying personal triggers is the heart of chronic-condition control, and patterns are far easier to see in data than from memory.",
  "Ingest flare events and candidate triggers into `index=personal`; rank triggers by how often they precede a flare.",
  "Bar chart of flare rate by candidate trigger.",
  "It works out what tends to set off your bad days, so you can avoid the things that make you flare up.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Blood-Pressure Control Zone", "medium", "beginner", ["Analytics", "Availability"],
  "index=personal sourcetype=vitals:reading metric=blood_pressure\n"
  "| eval zone=case(systolic<120 AND diastolic<80,\"normal\",systolic<130 AND diastolic<80,\"elevated\",systolic<140 OR diastolic<90,\"stage 1\",1=1,\"stage 2\")\n"
  "| timechart span=1w count by zone",
  "Classifies each blood-pressure reading into standard control zones and shows how the mix shifts week to week.",
  "Seeing more readings drift into higher zones is an early warning to adjust lifestyle or medication before a crisis.",
  "Ingest cuff readings into `index=personal`; classify by zone and trend the weekly distribution.",
  "Stacked column chart of readings per control zone each week.",
  "It sorts your blood-pressure readings into safe and worrying bands, so you can see if things are creeping up.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Lab-Result Trend vs Target Range", "medium", "intermediate", ["Analytics"],
  "index=personal sourcetype=labresult:value\n"
  "| timechart span=1mon avg(value) as value by test\n"
  "| untable _time test value",
  "Trends your recurring lab results — cholesterol, HbA1c, kidney markers — against the healthy target range for each test.",
  "Tracking labs over time reveals slow drifts a single result would hide, giving you time to change course.",
  "Ingest lab-portal results into `index=personal`; trend each test and overlay its target band.",
  "Line chart of each lab value over time with target-range shading.",
  "It follows your blood-test numbers over time so you can tell whether they are moving into or out of the healthy range.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Missed-Dose Same-Day Alert", "medium", "beginner", ["Availability"],
  "index=personal sourcetype=medication:dose status=scheduled\n"
  "| eval due_hour=strftime(scheduled_time,\"%H\")\n"
  "| search NOT [ search index=personal sourcetype=medication:dose status=taken | fields dose_id ]\n"
  "| where now()-scheduled_time>7200\n"
  "| table medication scheduled_time",
  "Flags scheduled doses that have not been marked taken two hours after they were due, so you can catch a missed dose the same day.",
  "A same-day nudge prevents a single forgotten dose from becoming a gap that undermines treatment.",
  "Ingest scheduled and taken doses into `index=personal`; alert on scheduled doses with no matching taken record.",
  "Single-value panel of overdue doses today.",
  "It notices when you have not taken a pill a couple of hours after it was due and reminds you before the day is out.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Symptom-Free Day Streak", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=condition:symptom\n"
  "| bin _time span=1d\n"
  "| stats max(severity) as worst by _time\n"
  "| eval symptom_free=if(worst=0,1,0)\n"
  "| streamstats reset_after=\"(symptom_free=0)\" sum(symptom_free) as streak\n"
  "| sort - _time",
  "Counts your current run of consecutive days with no symptoms so progress is visible and encouraging.",
  "A visible good-day streak is powerful motivation and a simple summary of how well the condition is being controlled.",
  "Ingest daily symptom scores into `index=personal`; compute the current symptom-free streak.",
  "Single-value panel of the current symptom-free-day streak.",
  "It counts how many days in a row you have felt well, turning good spells into a streak worth protecting.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Medication Refill Countdown", "medium", "beginner", ["Availability"],
  "index=personal sourcetype=medication:dose status=taken\n"
  "| stats count as taken_since_fill, max(pills_remaining) as remaining by medication\n"
  "| eval days_left=round(remaining/1,0)\n"
  "| where days_left<10\n"
  "| sort days_left",
  "Estimates how many days of each medication you have left and warns you before you run out and need a refill.",
  "Running out of a maintenance medication can be genuinely dangerous; an early countdown keeps the pharmacy trip ahead of the gap.",
  "Ingest doses and remaining counts into `index=personal`; project days remaining and alert under your buffer.",
  "Table of medications with days of supply remaining.",
  "It works out when you are about to run out of each medicine, so you order a refill in good time.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Pain Diary Time-of-Day Pattern", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=condition:symptom symptom=pain\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats avg(severity) as avg_pain by hour\n"
  "| sort hour",
  "Averages your pain scores by hour of day to reveal when you typically hurt most and when relief tends to arrive.",
  "Knowing your daily pain rhythm helps time medication, rest, and activity for the best effect.",
  "Ingest timestamped pain scores into `index=personal`; average by hour of day.",
  "Column chart of average pain by hour of day.",
  "It shows what times of day you usually hurt the most, so you can plan rest and medicine around them.",
  R(CC_REF), CC_APP, CC_DS)

U("51", "Care-Plan Vitals Dashboard", "medium", "intermediate", ["Analytics", "Availability"],
  "index=personal (sourcetype=vitals:reading OR sourcetype=medication:dose OR sourcetype=condition:symptom)\n"
  "| stats latest(value) as last_vital, avg(severity) as avg_symptom, sum(eval(if(status=\"taken\",1,0))) as doses_taken by metric\n"
  "| sort metric",
  "Brings your latest vitals, symptom averages, and medication adherence into one care-plan view to share with family or clinicians.",
  "A single consolidated picture makes appointments faster and keeps carers informed without chasing separate apps.",
  "Combine vitals, symptoms, and doses in `index=personal`; summarise into one care-plan panel.",
  "Summary dashboard of key vitals, symptoms, and adherence.",
  "It gathers your latest readings, symptoms, and medicines into one simple page you can show your doctor or family.",
  R(CC_REF), CC_APP, CC_DS)

# ===========================================================================
# 25.52  Elder Care & Accessibility
# ===========================================================================
EC_APP = ("Elder-care and accessibility telemetry — activity and fall sensors (Apple Watch fall "
          "detection, motion mats), medication dispensers, and check-in / video-call logs — "
          "streamed to Splunk HEC via APIs and smart-home hubs.")
EC_DS = ("Daily activity (`eldercare:activity`), fall alerts (`fall:alert`), medication reminders "
         "(`medreminder:event`), check-in calls (`checkin:call`), wandering alerts "
         "(`wandering:alert`).")
EC_REF = ("Home Assistant — presence detection", "https://www.home-assistant.io/integrations/person/")

U("52", "Daily Activity Baseline and Deviation", "high", "advanced", ["Anomaly", "Availability"],
  "index=personal sourcetype=eldercare:activity\n"
  "| bin _time span=1d\n"
  "| stats sum(motion_events) as motion by _time\n"
  "| eventstats avg(motion) as baseline, stdev(motion) as sd\n"
  "| eval low=if(motion<baseline-2*sd,1,0)\n"
  "| where low=1",
  "Learns a loved one's normal daily movement around the home and flags days that fall well below it, which can signal illness or a problem.",
  "A quiet house is often the first sign something is wrong for someone living alone; catching it early can prevent harm.",
  "Ingest motion-sensor counts into `index=personal`; compare each day to a rolling baseline and alert on big drops.",
  "Line chart of daily motion with a baseline band and flagged low days.",
  "It learns how much your relative normally moves about at home and warns you on days they are unusually still.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Fall-Alert Response Log", "high", "beginner", ["Availability"],
  "index=personal sourcetype=fall:alert\n"
  "| eval responded=if(isnotnull(response_time),1,0), response_min=round((response_time-_time)/60,1)\n"
  "| stats count as falls, sum(responded) as answered, avg(response_min) as avg_response\n"
  "| eval unanswered=falls-answered",
  "Records every fall-detection alert, whether someone responded, and how quickly, so care gaps are visible.",
  "Knowing that alerts are actually reaching and being answered by a carer is the whole point of a fall detector.",
  "Ingest fall-detector alerts and acknowledgements into `index=personal`; summarise response coverage.",
  "Table of fall alerts with response status and time.",
  "It keeps a record of every fall alarm and whether someone answered it quickly, so no alert is ever missed.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Medication-Dispenser Compliance", "high", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=medreminder:event\n"
  "| bin _time span=1d\n"
  "| stats sum(eval(if(action=\"dispensed\",1,0))) as taken, sum(eval(if(action=\"scheduled\",1,0))) as due by _time\n"
  "| eval missed=due-taken\n"
  "| where missed>0",
  "Watches an automated pill dispenser and flags days when a scheduled dose was not collected.",
  "For someone with memory difficulties, a missed-dose alert lets a carer step in the same day rather than weeks later.",
  "Ingest dispenser events into `index=personal`; flag days with uncollected doses.",
  "Table of days with missed doses.",
  "It watches the pill dispenser and lets you know the day a dose is missed, so you can check in.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Check-In Call Cadence", "medium", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=checkin:call\n"
  "| stats max(_time) as last_call by contact\n"
  "| eval days_since=round((now()-last_call)/86400,1)\n"
  "| where days_since>3\n"
  "| sort - days_since",
  "Tracks how long it has been since each family member last checked in on a loved one and nudges when the gap grows.",
  "Sharing the caring load is easier when everyone can see who last called and who is overdue.",
  "Ingest check-in calls into `index=personal`; flag contacts who have not called recently.",
  "Table of contacts with days since last check-in.",
  "It keeps track of when each family member last rang, so someone always checks in and nobody is forgotten.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Night-Time Wandering Watch", "high", "intermediate", ["Anomaly", "Availability"],
  "index=personal sourcetype=wandering:alert\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| where hour>=23 OR hour<=5\n"
  "| bin _time span=1d\n"
  "| stats count as night_events, values(location) as places by _time\n"
  "| sort - _time",
  "Flags night-time movement toward doors or outside that can indicate wandering, a serious risk for people with dementia.",
  "Early alerts on night wandering can prevent a loved one leaving the house unsafely in the dark.",
  "Ingest door and motion alerts into `index=personal`; isolate overnight events and summarise per night.",
  "Table of night-time wandering events by night.",
  "It watches for someone moving about or heading for the door in the middle of the night, so you can keep them safe.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Home-Temperature Safety Watch", "high", "beginner", ["Availability", "Anomaly"],
  "index=personal sourcetype=eldercare:activity metric=temperature\n"
  "| timechart span=1h avg(value) as temp_c\n"
  "| eval unsafe=case(temp_c<16,\"too cold\",temp_c>28,\"too hot\",1=1,\"ok\")\n"
  "| where unsafe!=\"ok\"",
  "Watches indoor temperature at an elderly relative's home and flags spells that are dangerously cold or hot.",
  "Older people are vulnerable to cold and heat but may not notice or act; an outside alert protects them.",
  "Ingest indoor temperature into `index=personal`; alert when it leaves the safe range.",
  "Line chart of indoor temperature with safe-band shading.",
  "It keeps an eye on how warm or cold the house is and warns you if it becomes unsafe for your relative.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Meal and Kettle Routine Check", "medium", "intermediate", ["Anomaly", "Availability"],
  "index=personal sourcetype=eldercare:activity (appliance=kettle OR appliance=fridge OR appliance=microwave)\n"
  "| bin _time span=1d\n"
  "| stats dc(appliance) as appliances_used, count as uses by _time\n"
  "| where uses<3",
  "Uses kitchen-appliance activity as a gentle proxy for whether a loved one is eating and drinking normally.",
  "A sudden drop in kettle or fridge use can hint at illness or low mood before anyone visits.",
  "Ingest smart-plug appliance events into `index=personal`; flag days with unusually little kitchen activity.",
  "Table of days with low kitchen activity.",
  "It notices if the kettle and fridge are barely used, a quiet sign your relative may not be eating well.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Accessibility Routine Adherence", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=eldercare:activity activity=routine\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(completed=\"yes\",1,0))) as done, count as planned by _time\n"
  "| eval adherence=round(100*done/planned,1)",
  "Tracks completion of daily supportive routines — exercises, hydration prompts, hearing-aid checks — that keep independence going.",
  "Consistent small routines preserve mobility and confidence; a weekly score keeps carers and the person on track.",
  "Ingest routine completions into `index=personal`; compute weekly adherence.",
  "Column chart of weekly routine adherence.",
  "It checks that daily helpful habits are being kept up each week, supporting your relative's independence.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Carer Visit Coverage", "medium", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=checkin:call type=visit\n"
  "| bin _time span=1d\n"
  "| stats count as visits, values(carer) as carers by _time\n"
  "| eval covered=if(visits>0,1,0)\n"
  "| stats sum(covered) as covered_days, count as total_days\n"
  "| eval coverage_pct=round(100*covered_days/total_days,1)",
  "Measures how many days had at least one in-person carer or family visit, revealing gaps in coverage.",
  "Visible coverage gaps let a family rota fill the days nobody was scheduled to drop by.",
  "Ingest visit logs into `index=personal`; compute the share of days with a visit.",
  "Single-value panel of visit-coverage percentage.",
  "It shows which days had a visit and which had none, so the family can fill the gaps in caring.",
  R(EC_REF), EC_APP, EC_DS)

U("52", "Well-Being Summary for Family", "medium", "intermediate", ["Analytics", "Availability"],
  "index=personal (sourcetype=eldercare:activity OR sourcetype=medreminder:event OR sourcetype=checkin:call)\n"
  "| bin _time span=1d\n"
  "| stats sum(motion_events) as motion, sum(eval(if(action=\"dispensed\",1,0))) as doses, count(eval(sourcetype=\"checkin:call\")) as contacts by _time\n"
  "| sort - _time",
  "Combines activity, medication, and contact into one daily well-being summary a whole family can glance at.",
  "One shared, gentle overview reassures distant relatives and highlights days that deserve a phone call.",
  "Combine care feeds in `index=personal`; produce a shareable daily well-being roll-up.",
  "Daily summary table of movement, doses, and contacts.",
  "It rolls up how active your relative was, whether they took their pills, and who was in touch, into one daily note for the family.",
  R(EC_REF), EC_APP, EC_DS)

# ===========================================================================
# 25.53  Wedding & Event Planning
# ===========================================================================
WE_APP = ("Wedding and event planning — task and budget spreadsheets, RSVP platforms (Zola, "
          "The Knot), vendor contracts, and seating tools — streamed to Splunk HEC via CSV "
          "exports and scripted inputs.")
WE_DS = ("Planning tasks (`event:task`), budget lines (`event:budget`), RSVPs (`event:rsvp`), "
         "vendor bookings (`event:vendor`), countdown milestones (`event:countdown`).")
WE_REF = ("Project Management Institute — planning basics", "https://www.pmi.org/about/what-is-project-management")

U("53", "Wedding Budget Burn-Down", "medium", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=event:budget\n"
  "| stats sum(committed) as committed, sum(paid) as paid, max(total_budget) as budget\n"
  "| eval remaining=budget-committed, over_under=budget-committed",
  "Tracks committed and paid spend against your total wedding budget so you always know how much is left.",
  "Weddings are notorious for budget creep; a live burn-down keeps decisions grounded in what you can afford.",
  "Ingest budget lines into `index=personal`; sum committed and paid against the total.",
  "Bar chart of budget versus committed and paid.",
  "It adds up what you have promised and paid against your wedding budget, so you always know what is left.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "RSVP Response Tracker", "medium", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=event:rsvp\n"
  "| stats count as invited, sum(eval(if(response=\"yes\",1,0))) as attending, sum(eval(if(response=\"no\",1,0))) as declined, sum(eval(if(response=\"pending\",1,0))) as pending\n"
  "| eval response_rate=round(100*(attending+declined)/invited,1)",
  "Counts invitations by response status so you know your head count and who still has not replied.",
  "An accurate, live head count drives catering and seating decisions and flags who needs a gentle chase.",
  "Ingest RSVP records into `index=personal`; tally responses and compute the response rate.",
  "Pie chart of RSVP responses with a response-rate figure.",
  "It counts who has said yes, no, or nothing yet, so you know how many are coming and who to chase.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Task Countdown and Overdue Watch", "medium", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=event:task status!=done\n"
  "| eval days_to_due=round((due_time-now())/86400,1)\n"
  "| eval state=case(days_to_due<0,\"overdue\",days_to_due<7,\"due soon\",1=1,\"upcoming\")\n"
  "| stats count by state",
  "Groups outstanding planning tasks into overdue, due-soon, and upcoming buckets so nothing slips before the big day.",
  "A clear view of what is late and what is next keeps a stressful project moving without last-minute panics.",
  "Ingest planning tasks with due dates into `index=personal`; bucket by urgency.",
  "Column chart of tasks by urgency state.",
  "It sorts your to-do list into late, due soon, and later, so nothing important is forgotten before the day.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Vendor Payment Schedule", "medium", "intermediate", ["Availability", "Business"],
  "index=personal sourcetype=event:vendor\n"
  "| eval days_to_payment=round((next_payment_due-now())/86400,1)\n"
  "| where days_to_payment<30\n"
  "| table vendor next_payment_due amount_due days_to_payment\n"
  "| sort days_to_payment",
  "Lists upcoming vendor deposits and final payments so no supplier bill catches you by surprise.",
  "Missing a vendor deadline can cost a booking; an early payment calendar protects your key suppliers.",
  "Ingest vendor contracts and due dates into `index=personal`; surface payments due soon.",
  "Table of vendor payments due in the next 30 days.",
  "It lists which suppliers need paying soon and how much, so no deposit or final bill sneaks up on you.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Guest Dietary and Access Needs", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=event:rsvp response=yes\n"
  "| stats count by dietary_need\n"
  "| sort - count",
  "Summarises the dietary and accessibility needs of attending guests so caterers and venues can prepare.",
  "Getting needs right shows guests they matter and avoids awkward gaps on the day.",
  "Ingest RSVP dietary fields into `index=personal`; tally needs across attending guests.",
  "Bar chart of guest dietary and access needs.",
  "It counts up guests' food and access needs, so the caterer and venue can look after everyone.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Seating-Plan Completeness", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=event:rsvp response=yes\n"
  "| stats count as guests, sum(eval(if(isnotnull(table_number),1,0))) as seated\n"
  "| eval unseated=guests-seated, complete_pct=round(100*seated/guests,1)",
  "Checks how many confirmed guests have been assigned a table and how many still need seating.",
  "A completeness score keeps the fiddly seating plan on track as RSVPs firm up.",
  "Ingest seating assignments into `index=personal`; compare seated guests against confirmed guests.",
  "Single-value panel of seating-plan completeness.",
  "It checks how many of your confirmed guests have a seat yet, so the seating plan gets finished in time.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Days-to-Event Milestone Wall", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=event:countdown\n"
  "| eval days_left=round((milestone_time-now())/86400,1)\n"
  "| where days_left>=0\n"
  "| table milestone milestone_time days_left\n"
  "| sort days_left",
  "Shows a countdown to every key milestone — dress fitting, final head count, rehearsal — on one wall.",
  "A single milestone wall keeps everyone aligned and calm as the date approaches.",
  "Ingest milestones into `index=personal`; compute days remaining to each.",
  "Table of milestones ordered by days remaining.",
  "It counts down the days to each big moment, so everyone knows what is coming and when.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Budget Category Overspend Alert", "medium", "intermediate", ["Anomaly", "Business"],
  "index=personal sourcetype=event:budget\n"
  "| stats sum(committed) as committed, max(category_budget) as cap by category\n"
  "| eval over=committed-cap, over_pct=round(100*committed/cap,1)\n"
  "| where committed>cap\n"
  "| sort - over",
  "Flags any spending category — flowers, catering, photography — that has blown past the amount you set aside for it.",
  "Catching one runaway category early lets you rebalance before the whole budget is at risk.",
  "Ingest budget lines by category into `index=personal`; flag categories over their cap.",
  "Bar chart of categories over budget.",
  "It spots which part of the wedding is going over its share of the money, so you can rein it in early.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Vendor Booking Coverage", "medium", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=event:vendor\n"
  "| stats count as booked, values(category) as categories by status\n"
  "| eventstats sum(booked) as total",
  "Shows which essential vendor categories are booked, in progress, or still open so nothing critical is left to chance.",
  "A booking-coverage view stops a key supplier being overlooked until it is too late to book one.",
  "Ingest vendor records into `index=personal`; summarise coverage by status and category.",
  "Table of vendor categories by booking status.",
  "It shows which suppliers you have booked and which you still need, so nothing essential is left unbooked.",
  R(WE_REF), WE_APP, WE_DS)

U("53", "Post-Event Thank-You Tracker", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=event:rsvp gift=yes\n"
  "| stats count as gifts, sum(eval(if(thanked=\"yes\",1,0))) as thanked\n"
  "| eval outstanding=gifts-thanked, done_pct=round(100*thanked/gifts,1)",
  "Tracks which gift-givers have received a thank-you note and who is still owed one after the event.",
  "Thank-you notes are easy to lose track of; a simple tally makes sure everyone is acknowledged.",
  "Ingest gift and thank-you records into `index=personal`; track completion.",
  "Single-value panel of thank-you completion.",
  "It keeps track of who you have thanked for gifts and who is still owed a note, so nobody is missed.",
  R(WE_REF), WE_APP, WE_DS)

# ===========================================================================
# 25.54  Home Renovation & Project Management
# ===========================================================================
RN_APP = ("Home-renovation project management — task boards (Trello, Notion), budget and receipt "
          "trackers, material orders, and inspection / permit logs — streamed to Splunk HEC via "
          "APIs and scripted inputs.")
RN_DS = ("Renovation tasks (`reno:task`), budget and receipts (`reno:budget`), material orders "
         "(`reno:material`), inspections (`reno:inspection`), contractor logs (`reno:contractor`).")
RN_REF = ("Project Management Institute — planning basics", "https://www.pmi.org/about/what-is-project-management")

U("54", "Renovation Budget vs Actual", "medium", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=reno:budget\n"
  "| stats sum(estimated) as estimated, sum(actual) as actual by phase\n"
  "| eval variance=actual-estimated, variance_pct=round(100*(actual-estimated)/estimated,1)\n"
  "| sort - variance",
  "Compares estimated versus actual spend for each renovation phase so overruns are obvious as they happen.",
  "Renovations almost always run over; phase-level variance lets you find and control the culprit early.",
  "Ingest estimates and receipts into `index=personal`; compute variance per phase.",
  "Bar chart of estimated versus actual spend by phase.",
  "It compares what each part of the job was meant to cost with what it really cost, so overspending shows up fast.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Task Dependency and Blocker Watch", "medium", "intermediate", ["Availability", "Business"],
  "index=personal sourcetype=reno:task status=blocked\n"
  "| eval days_blocked=round((now()-blocked_since)/86400,1)\n"
  "| table task blocked_by days_blocked\n"
  "| sort - days_blocked",
  "Highlights renovation tasks stuck waiting on something else and how long they have been blocked.",
  "A blocked task stalls everything downstream; surfacing blockers keeps the whole project flowing.",
  "Ingest task states into `index=personal`; list blocked tasks by age.",
  "Table of blocked tasks with days blocked.",
  "It shows which jobs are stuck waiting on something and for how long, so you can unblock them and keep going.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Contractor Progress vs Schedule", "medium", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=reno:task\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as done, count as total by _time\n"
  "| eval completion_pct=round(100*done/total,1)\n"
  "| sort _time",
  "Trends the share of planned tasks completed each week so you can tell whether the job is on schedule.",
  "A weekly completion trend reveals slippage while there is still time to add hands or adjust the plan.",
  "Ingest task completions into `index=personal`; trend weekly completion.",
  "Line chart of weekly task completion percentage.",
  "It tracks how much of the work gets finished each week, so you know if the build is running to time.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Material Order Lead-Time Watch", "medium", "intermediate", ["Availability", "Business"],
  "index=personal sourcetype=reno:material status=ordered\n"
  "| eval days_to_delivery=round((expected_delivery-now())/86400,1)\n"
  "| where days_to_delivery<14\n"
  "| table item supplier expected_delivery days_to_delivery\n"
  "| sort days_to_delivery",
  "Lists materials on order with their expected delivery dates so trades are not left waiting on missing supplies.",
  "Long-lead items like tiles or windows can derail a schedule; tracking them keeps the site working.",
  "Ingest material orders into `index=personal`; surface deliveries due soon.",
  "Table of pending material deliveries.",
  "It keeps track of when ordered materials will arrive, so the builders are never left waiting on supplies.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Permit and Inspection Status", "high", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=reno:inspection\n"
  "| stats latest(status) as status, latest(_time) as updated by permit\n"
  "| eval stale_days=round((now()-updated)/86400,1)\n"
  "| sort - stale_days",
  "Keeps every permit and inspection with its latest status so no legal step is missed before work continues.",
  "Skipping a required inspection can mean expensive rework or fines; a status board prevents that.",
  "Ingest permit and inspection records into `index=personal`; track latest status per permit.",
  "Table of permits with current inspection status.",
  "It keeps a clear list of which permits and inspections are done and which are still needed, so the work stays legal.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Change-Order Cost Impact", "medium", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=reno:budget type=change_order\n"
  "| bin _time span=1w\n"
  "| stats sum(cost_delta) as weekly_change by _time\n"
  "| eventstats sum(cost_delta) as total_change\n"
  "| sort _time",
  "Adds up the cost of every mid-project change so you can see how scope creep is inflating the total.",
  "Small changes add up quietly; a running total keeps you honest about what the wish-list is costing.",
  "Ingest change orders into `index=personal`; total their cost impact over time.",
  "Column chart of change-order cost by week with a running total.",
  "It adds up the cost of every change you make along the way, so scope creep never surprises you at the end.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Contractor Reliability Scorecard", "medium", "advanced", ["Analytics", "Business"],
  "index=personal sourcetype=reno:contractor\n"
  "| stats sum(eval(if(showed_up=\"yes\",1,0))) as days_present, count as scheduled_days, avg(hours_worked) as avg_hours by contractor\n"
  "| eval attendance_pct=round(100*days_present/scheduled_days,1)\n"
  "| sort - attendance_pct",
  "Scores each contractor on attendance and hours worked so you know who is reliable for the next phase.",
  "An evidence-based reliability score helps you keep the good trades and rethink the ones who let you down.",
  "Ingest contractor attendance into `index=personal`; score by attendance and hours.",
  "Table of contractors by attendance and average hours.",
  "It keeps score of which workers turn up and put in the hours, so you know who to trust with the next job.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Receipt and Warranty Vault", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=reno:budget type=receipt\n"
  "| stats count as receipts, sum(actual) as total_spent, sum(eval(if(isnotnull(warranty_expiry),1,0))) as with_warranty by category\n"
  "| sort - total_spent",
  "Catalogues receipts and warranty dates by category so you can find proof of purchase and coverage later.",
  "A searchable record of what you paid and what is under warranty saves money and hassle years down the line.",
  "Ingest receipts into `index=personal`; summarise spend and warranty coverage by category.",
  "Table of spend and warranty coverage by category.",
  "It files away your receipts and warranty dates, so you can always find proof of purchase and what is still covered.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Room-by-Room Completion", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=reno:task\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as done, count as total by room\n"
  "| eval completion_pct=round(100*done/total,1)\n"
  "| sort completion_pct",
  "Shows how finished each room is so you can see what is nearly done and what has barely started.",
  "A room-level view helps you push one space to fully finished — and liveable — rather than leaving everything half-done.",
  "Ingest tasks tagged by room into `index=personal`; compute completion per room.",
  "Bar chart of completion percentage by room.",
  "It shows how done each room is, so you can finish one space properly instead of leaving the whole house half-done.",
  R(RN_REF), RN_APP, RN_DS)

U("54", "Project Health Summary", "medium", "advanced", ["Analytics", "Business"],
  "index=personal (sourcetype=reno:task OR sourcetype=reno:budget)\n"
  "| stats sum(eval(if(status=\"done\",1,0))) as tasks_done, count(eval(sourcetype=\"reno:task\")) as tasks_total, sum(actual) as spent, max(total_budget) as budget\n"
  "| eval pct_complete=round(100*tasks_done/tasks_total,1), pct_budget=round(100*spent/budget,1)",
  "Combines schedule and budget into one project-health snapshot — percent complete against percent of budget spent.",
  "Comparing progress to spend in one view is the classic early-warning of a project heading over budget or behind.",
  "Combine task and budget feeds in `index=personal`; compare completion to budget consumed.",
  "Summary panel of percent complete versus percent of budget spent.",
  "It puts how much is finished next to how much money is gone, giving one honest read on whether the project is healthy.",
  R(RN_REF), RN_APP, RN_DS)

# ===========================================================================
# 25.55  Genealogy & Family History
# ===========================================================================
GN_APP = ("Genealogy and family-history research — tree platforms (Ancestry, FamilySearch), DNA "
          "match exports (23andMe, MyHeritage), and document / archive catalogues — streamed to "
          "Splunk HEC via GEDCOM and CSV exports.")
GN_DS = ("Tree records (`genealogy:record`), DNA matches (`dna:match`), ancestor events "
         "(`ancestor:event`), archive documents (`archive:document`), tree nodes "
         "(`familytree:node`).")
GN_REF = ("FamilySearch — research wiki", "https://www.familysearch.org/en/wiki/Main_Page")

U("55", "Family-Tree Growth Over Time", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=familytree:node\n"
  "| bin _time span=1mon\n"
  "| stats count as added by _time\n"
  "| eventstats sum(added) as total_people\n"
  "| sort _time",
  "Trends how many people you have added to your family tree each month and the running total.",
  "Seeing steady growth keeps a long research project motivating and shows how far the tree has come.",
  "Ingest tree additions into `index=personal`; trend monthly and cumulative counts.",
  "Column chart of people added per month with a running total.",
  "It counts how many relatives you add to your family tree each month, showing how it grows over time.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "DNA Match Clustering by Surname", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=dna:match\n"
  "| stats count as matches, avg(shared_cm) as avg_cm by surname\n"
  "| where matches>=2\n"
  "| sort - avg_cm",
  "Groups your DNA matches by shared surname and average shared DNA to point research toward the strongest family lines.",
  "Clustering matches turns a bewildering match list into clear leads on which branch to research next.",
  "Ingest DNA match exports into `index=personal`; group by surname and shared centimorgans.",
  "Bar chart of matches by surname with average shared DNA.",
  "It groups your DNA relatives by family name, showing which branches your strongest matches point to.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Ancestor Lifespan and Era Analysis", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=ancestor:event event=death\n"
  "| eval lifespan=death_year-birth_year, era=floor(birth_year/50)*50\n"
  "| stats avg(lifespan) as avg_lifespan, count as people by era\n"
  "| sort era",
  "Calculates ancestors' lifespans grouped by the era they were born in, revealing how longevity changed across generations.",
  "Seeing lifespan rise across the centuries makes family history tangible and can hint at health patterns.",
  "Ingest birth and death events into `index=personal`; average lifespan by era.",
  "Column chart of average ancestor lifespan by 50-year era.",
  "It works out how long your ancestors lived in each era, showing how much longer people live now.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Research Source Coverage", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=genealogy:record\n"
  "| stats sum(eval(if(has_source=\"yes\",1,0))) as sourced, count as facts\n"
  "| eval coverage_pct=round(100*sourced/facts,1), unsourced=facts-sourced",
  "Measures what share of the facts in your tree are backed by a real document rather than a guess or a copied tree.",
  "Sourced facts are the difference between a reliable family history and a house of cards; coverage keeps you honest.",
  "Ingest tree facts and their sources into `index=personal`; compute the sourced share.",
  "Single-value panel of source-coverage percentage.",
  "It checks how much of your family tree is backed by real records, so your history rests on proof not guesswork.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Brick-Wall Ancestor Tracker", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=familytree:node status=brickwall\n"
  "| eval days_stuck=round((now()-last_progress)/86400,1)\n"
  "| table ancestor generation last_progress days_stuck\n"
  "| sort - days_stuck",
  "Lists the ancestors where your research has hit a dead end and how long each has been stuck.",
  "Keeping brick walls visible focuses effort and celebrates the day one finally falls.",
  "Ingest brick-wall flags into `index=personal`; list stuck ancestors by age.",
  "Table of brick-wall ancestors by time stuck.",
  "It keeps a list of the relatives you are stuck on, so you know where to focus your next bit of digging.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Document Archive Index", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=archive:document\n"
  "| stats count as docs, sum(eval(if(transcribed=\"yes\",1,0))) as transcribed by doc_type\n"
  "| eval to_do=docs-transcribed\n"
  "| sort - to_do",
  "Catalogues your scanned certificates, letters, and photos by type and flags how many still need transcribing.",
  "A searchable archive index means precious documents are findable and the transcription backlog is visible.",
  "Ingest document metadata into `index=personal`; summarise by type and transcription status.",
  "Bar chart of documents by type and transcription status.",
  "It sorts your family documents by kind and shows which still need typing up, so nothing precious is lost.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Geographic Origin Map", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=ancestor:event event=birth\n"
  "| stats count as births by birth_country\n"
  "| sort - births",
  "Counts where your ancestors were born so you can map the countries and regions your family came from.",
  "A map of origins turns a list of names into a story of migration you can share with relatives.",
  "Ingest birth events with locations into `index=personal`; count by country or region.",
  "Map or bar chart of ancestor birth counts by country.",
  "It counts where your ancestors were born, drawing a map of all the places your family came from.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Living-Relative Contact Log", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=genealogy:record type=interview\n"
  "| stats max(_time) as last_contact by relative\n"
  "| eval months_since=round((now()-last_contact)/2629800,1)\n"
  "| where months_since>12\n"
  "| sort - months_since",
  "Tracks when you last interviewed each living relative for their memories and nudges you before those stories are lost.",
  "Older relatives hold irreplaceable memories; a gentle reminder ensures you capture them in time.",
  "Ingest interview logs into `index=personal`; flag relatives not spoken to recently.",
  "Table of relatives by time since last interview.",
  "It reminds you when you last recorded a relative's memories, so those precious stories are captured in time.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Duplicate-Person Detection", "low", "advanced", ["Anomaly", "Business"],
  "index=personal sourcetype=familytree:node\n"
  "| eval key=name.\"|\".birth_year\n"
  "| stats count as copies, values(node_id) as ids by key\n"
  "| where copies>1\n"
  "| sort - copies",
  "Finds people who appear more than once in your tree with the same name and birth year so you can merge them.",
  "Duplicates tangle a tree and corrupt relationships; catching them keeps the research clean.",
  "Ingest tree nodes into `index=personal`; group by name and birth year to find duplicates.",
  "Table of suspected duplicate people.",
  "It spots the same ancestor entered twice by mistake, so you can tidy the tree and keep it correct.",
  R(GN_REF), GN_APP, GN_DS)

U("55", "Research Session Productivity", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=genealogy:record type=session\n"
  "| bin _time span=1w\n"
  "| stats sum(facts_added) as facts, sum(duration_min) as minutes by _time\n"
  "| eval facts_per_hour=round(facts/(minutes/60),1)\n"
  "| sort - _time",
  "Trends how many new facts you add per hour of research so you can tell which sessions and sources are most productive.",
  "Knowing what makes a productive session helps you spend limited research time where it pays off.",
  "Ingest research sessions into `index=personal`; compute facts added per hour.",
  "Line chart of facts added per research hour.",
  "It shows how much progress you make per hour of research, so you can spend your time where it pays off.",
  R(GN_REF), GN_APP, GN_DS)

# ===========================================================================
# 25.56  Spiritual Practice & Mindfulness
# ===========================================================================
SP_APP = ("Spiritual-practice and mindfulness logs — prayer / meditation timers, scripture-reading "
          "plans (YouVersion), fasting and gratitude journals, and retreat calendars — streamed to "
          "Splunk HEC via APIs and scripted inputs.")
SP_DS = ("Prayer sessions (`prayer:session`), scripture readings (`scripture:reading`), fasting "
         "logs (`fasting:log`), gratitude entries (`gratitude:entry`), retreats (`retreat:event`).")
SP_REF = ("Greater Good Science Center — gratitude research", "https://greatergood.berkeley.edu/topic/gratitude")

U("56", "Prayer and Meditation Consistency", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=prayer:session\n"
  "| bin _time span=1d\n"
  "| stats sum(duration_min) as minutes by _time\n"
  "| eval practised=if(minutes>0,1,0)\n"
  "| streamstats reset_after=\"(practised=0)\" sum(practised) as streak\n"
  "| sort - _time",
  "Tracks your daily prayer or meditation practice and the current run of consecutive days kept.",
  "A gentle consistency streak supports a habit that is easy to let slip when life gets busy.",
  "Ingest practice sessions into `index=personal`; compute the daily streak.",
  "Single-value panel of the current practice-day streak.",
  "It tracks your daily quiet time and how many days in a row you have kept it, gently encouraging the habit.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Scripture Reading-Plan Progress", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=scripture:reading\n"
  "| stats dc(passage) as passages_read, max(plan_total) as plan_total\n"
  "| eval progress_pct=round(100*passages_read/plan_total,1), remaining=plan_total-passages_read",
  "Shows how far through a reading plan you are and how much remains to finish on schedule.",
  "A clear progress bar keeps a long reading plan achievable and encourages you to catch up when behind.",
  "Ingest reading-plan entries into `index=personal`; compute progress against the plan total.",
  "Progress bar of reading-plan completion.",
  "It shows how far through your reading plan you are and how much is left, keeping you on track.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Gratitude Journal Themes", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=gratitude:entry\n"
  "| bin _time span=1mon\n"
  "| stats count as entries, values(theme) as themes by _time\n"
  "| sort - _time",
  "Summarises what you have been grateful for each month, surfacing the recurring themes in your life.",
  "Noticing what consistently brings gratitude helps you invest more in the people and things that matter.",
  "Ingest gratitude entries into `index=personal`; summarise themes per month.",
  "Table of gratitude themes by month.",
  "It gathers up what you have been thankful for each month, showing what really brings you joy.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Fasting Adherence and Pattern", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=fasting:log\n"
  "| bin _time span=1w\n"
  "| stats sum(eval(if(completed=\"yes\",1,0))) as kept, count as planned by _time\n"
  "| eval adherence_pct=round(100*kept/planned,1)",
  "Tracks how consistently you keep planned fasts, whether for faith or health, week by week.",
  "A steady adherence view supports a discipline that benefits from encouragement and honest self-review.",
  "Ingest fasting logs into `index=personal`; compute weekly adherence.",
  "Column chart of weekly fasting adherence.",
  "It tracks how well you keep to your fasting plan each week, supporting the discipline gently.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Practice Time-of-Day Rhythm", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=prayer:session\n"
  "| eval hour=strftime(_time,\"%H\")\n"
  "| stats sum(duration_min) as minutes by hour\n"
  "| sort hour",
  "Shows the times of day you most often pray or meditate, helping you protect a rhythm that works.",
  "Anchoring practice to your natural rhythm makes it far more likely to stick.",
  "Ingest practice sessions into `index=personal`; sum minutes by hour of day.",
  "Column chart of practice minutes by hour of day.",
  "It shows what times of day you usually take quiet time, so you can protect that part of your routine.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Community-Service and Worship Attendance", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=retreat:event type=gathering\n"
  "| bin _time span=1mon\n"
  "| stats count as attended by _time\n"
  "| sort - _time",
  "Counts how often you attend a worship service, group, or gathering each month.",
  "Community is central to most spiritual practice; a simple count helps you stay connected.",
  "Ingest attendance events into `index=personal`; count per month.",
  "Column chart of monthly attendance.",
  "It counts how often you join your worship group or community each month, helping you stay connected.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Gratitude Volume and Mood Link", "low", "advanced", ["Analytics", "Anomaly"],
  "index=personal sourcetype=gratitude:entry\n"
  "| bin _time span=1d\n"
  "| stats count as entries, avg(mood) as mood by _time\n"
  "| eval volume=if(entries>=3,\"3+ entries\",\"1-2 entries\")\n"
  "| stats avg(mood) as avg_mood, count as days by volume",
  "Compares your mood on days you wrote lots of gratitude notes against days you wrote only one or two.",
  "Seeing your own gratitude-mood link, in your own data, is far more convincing than being told it works.",
  "Ingest gratitude entries with a mood score into `index=personal`; compare mood by how much you journaled.",
  "Bar chart of average mood by gratitude-journaling volume.",
  "It compares how you felt on days you counted many blessings versus few, showing gratitude's effect.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Retreat and Rest Balance", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=retreat:event type=retreat\n"
  "| stats max(_time) as last_retreat\n"
  "| eval days_since=round((now()-last_retreat)/86400,1)",
  "Tracks how long it has been since your last retreat or dedicated day of rest and reflection.",
  "Rhythms of rest are easy to neglect; a simple counter prompts you to plan the next one.",
  "Ingest retreat events into `index=personal`; count days since the last one.",
  "Single-value panel of days since last retreat.",
  "It counts how long since you last took a proper day of rest and reflection, nudging you to plan the next.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Reflection-Word Frequency", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=gratitude:entry\n"
  "| rex field=text max_match=0 \"(?<word>\\w{4,})\"\n"
  "| stats count by word\n"
  "| sort - count\n"
  "| head 20",
  "Finds the words you use most often in your reflections and gratitude notes, revealing what is on your heart.",
  "Recurring words are a quiet mirror of your season of life and what you are wrestling with or thankful for.",
  "Ingest reflection text into `index=personal`; count the most frequent meaningful words.",
  "Word list or cloud of most-used reflection words.",
  "It finds the words you write most in your reflections, quietly showing what is on your mind and heart.",
  R(SP_REF), SP_APP, SP_DS)

U("56", "Spiritual-Practice Balance Wheel", "low", "advanced", ["Analytics", "Business"],
  "index=personal (sourcetype=prayer:session OR sourcetype=scripture:reading OR sourcetype=gratitude:entry OR sourcetype=fasting:log OR sourcetype=retreat:event)\n"
  "| bin _time span=1mon\n"
  "| stats count by sourcetype _time\n"
  "| stats avg(count) as avg_per_month by sourcetype\n"
  "| sort - avg_per_month",
  "Brings your different practices — prayer, reading, gratitude, fasting, gathering — into one balance view.",
  "A balance wheel gently reveals which practices you lean on and which you have quietly let go.",
  "Combine practice feeds in `index=personal`; compare monthly frequency across practices.",
  "Radar or bar chart of practices by monthly frequency.",
  "It brings all your different practices together in one picture, showing which you keep up and which have slipped.",
  R(SP_REF), SP_APP, SP_DS)

# ===========================================================================
# 25.57  Volunteering & Community
# ===========================================================================
VO_APP = ("Volunteering and community telemetry — volunteer-hours trackers, donation receipts, "
          "mutual-aid request boards, and community-event calendars — streamed to Splunk HEC via "
          "APIs and scripted inputs.")
VO_DS = ("Volunteer shifts (`volunteer:shift`), donations (`donation:gift`), community events "
         "(`community:event`), mutual-aid requests (`mutualaid:request`), impact metrics "
         "(`impact:metric`).")
VO_REF = ("VolunteerMatch — get involved", "https://www.volunteermatch.org/")

U("57", "Volunteer Hours by Cause", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=volunteer:shift\n"
  "| bin _time span=1mon\n"
  "| stats sum(hours) as hours by cause _time\n"
  "| stats sum(hours) as total_hours by cause\n"
  "| sort - total_hours",
  "Adds up the hours you give to each cause so you can see where your time and heart really go.",
  "Seeing your volunteering by cause helps you give intentionally rather than drifting into whatever asks loudest.",
  "Ingest volunteer shifts into `index=personal`; total hours by cause.",
  "Bar chart of volunteer hours by cause.",
  "It adds up the hours you give to each good cause, showing where your time and heart really go.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Giving Budget vs Actual", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=donation:gift\n"
  "| bin _time span=1mon\n"
  "| stats sum(amount) as given by _time\n"
  "| eventstats avg(given) as monthly_avg\n"
  "| eval vs_target=round(given-monthly_avg,2)",
  "Trends your charitable giving each month against your own target or average so you can give consistently.",
  "Turning generosity into a tracked commitment helps you follow through on the giving you intend.",
  "Ingest donation receipts into `index=personal`; trend monthly giving against a target.",
  "Column chart of monthly giving with a target line.",
  "It tracks how much you give to charity each month against your plan, helping you give as you mean to.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Volunteer-Shift Reliability", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=volunteer:shift\n"
  "| stats sum(eval(if(status=\"attended\",1,0))) as attended, count as signed_up\n"
  "| eval reliability_pct=round(100*attended/signed_up,1), missed=signed_up-attended",
  "Measures how often you actually show up for the shifts you sign up for.",
  "Charities depend on reliable volunteers; an honest attendance rate helps you commit to what you can truly keep.",
  "Ingest sign-ups and attendance into `index=personal`; compute reliability.",
  "Single-value panel of shift reliability percentage.",
  "It checks how often you turn up for the volunteering you signed up for, helping you commit only to what you can keep.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Community-Impact Scorecard", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=impact:metric\n"
  "| bin _time span=1mon\n"
  "| stats sum(value) as total by metric _time\n"
  "| stats sum(total) as lifetime by metric\n"
  "| sort - lifetime",
  "Rolls up the tangible outcomes of your service — meals served, trees planted, tutoring hours — into a lifetime impact tally.",
  "Concrete impact numbers keep volunteering meaningful and are worth sharing to inspire others.",
  "Ingest impact metrics into `index=personal`; total each outcome over time.",
  "Bar chart of lifetime impact by metric.",
  "It adds up the real good you have done — meals served, trees planted — into one inspiring lifetime tally.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Mutual-Aid Request Response", "low", "intermediate", ["Availability", "Business"],
  "index=personal sourcetype=mutualaid:request\n"
  "| stats count as requests, sum(eval(if(status=\"fulfilled\",1,0))) as fulfilled, avg(response_hours) as avg_response\n"
  "| eval fulfil_pct=round(100*fulfilled/requests,1)",
  "Tracks how many neighbourhood mutual-aid requests you helped fulfil and how quickly.",
  "A responsive network depends on knowing which needs got met; this keeps the community loop honest.",
  "Ingest mutual-aid requests into `index=personal`; compute fulfilment rate and response time.",
  "Summary panel of requests fulfilled and response time.",
  "It tracks how many neighbours' requests for help you answered and how fast, keeping the community strong.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Donation Tax-Receipt Readiness", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=donation:gift\n"
  "| stats sum(amount) as total, sum(eval(if(receipt=\"yes\",1,0))) as with_receipt, count as gifts\n"
  "| eval missing_receipts=gifts-with_receipt",
  "Totals your deductible giving for the year and flags gifts still missing a receipt before tax time.",
  "Chasing receipts in advance turns a stressful tax scramble into a simple, complete record.",
  "Ingest donations into `index=personal`; total giving and flag missing receipts.",
  "Summary panel of annual giving and missing receipts.",
  "It adds up your charitable giving for the year and flags any gifts still missing a receipt for tax time.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Community-Event Participation", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=community:event\n"
  "| bin _time span=1mon\n"
  "| stats count as events, dc(event_type) as types by _time\n"
  "| sort - _time",
  "Counts the community events you take part in each month and how varied they are.",
  "Steady, varied participation is a sign of a healthy connection to where you live.",
  "Ingest community events into `index=personal`; count participation per month.",
  "Column chart of monthly community-event participation.",
  "It counts how many local events you join each month, showing how connected you are to your community.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Skills-Based Volunteering Match", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=volunteer:shift\n"
  "| stats sum(hours) as hours by skill_used\n"
  "| eventstats sum(hours) as total\n"
  "| eval share_pct=round(100*hours/total,1)\n"
  "| sort - hours",
  "Shows how much of your volunteering uses your professional skills versus general help.",
  "Skills-based volunteering multiplies your impact; seeing the split helps you offer what you are best at.",
  "Ingest shifts tagged by skill into `index=personal`; break hours down by skill used.",
  "Bar chart of volunteer hours by skill used.",
  "It shows how much of your volunteering uses your special skills, so you can give what you are best at.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Burnout and Balance Watch", "medium", "advanced", ["Anomaly", "Availability"],
  "index=personal sourcetype=volunteer:shift\n"
  "| bin _time span=1w\n"
  "| stats sum(hours) as hours by _time\n"
  "| eventstats avg(hours) as avg_hours, stdev(hours) as sd\n"
  "| eval high=if(hours>avg_hours+2*sd,1,0)\n"
  "| where high=1",
  "Flags weeks where your volunteering hours spike well above normal, an early sign of taking on too much.",
  "Generous people burn out quietly; a gentle warning helps you keep serving sustainably.",
  "Ingest volunteer hours into `index=personal`; flag weeks far above your baseline.",
  "Line chart of weekly volunteer hours with high weeks flagged.",
  "It warns you when you take on far more volunteering than usual, helping you avoid burning out.",
  R(VO_REF), VO_APP, VO_DS)

U("57", "Lifetime Contribution Summary", "low", "beginner", ["Analytics", "Business"],
  "index=personal (sourcetype=volunteer:shift OR sourcetype=donation:gift)\n"
  "| stats sum(hours) as total_hours, sum(amount) as total_given, dc(cause) as causes",
  "Combines your lifetime volunteer hours, giving, and number of causes into one contribution summary.",
  "A single lifetime view of your generosity is a quietly powerful reminder of the difference you have made.",
  "Combine service and giving feeds in `index=personal`; roll up lifetime totals.",
  "Summary panel of lifetime hours, giving, and causes.",
  "It sums up all the hours and money you have given over the years, a reminder of the good you have done.",
  R(VO_REF), VO_APP, VO_DS)

# ===========================================================================
# 25.58  Life-Logging & Memories
# ===========================================================================
LG_APP = ("Life-logging and memory telemetry — photo libraries (Google Photos, Immich), "
          "location history, voice memos, and daily-moment journals — streamed to Splunk HEC via "
          "APIs and scripted inputs.")
LG_DS = ("Photos (`photo:capture`), places visited (`location:visit`), voice memos "
         "(`voicememo:note`), logged moments (`lifelog:moment`), timeline events "
         "(`timeline:event`).")
LG_REF = ("Immich — self-hosted photo library", "https://immich.app/")

U("58", "Photos Taken Over Time", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=photo:capture\n"
  "| timechart span=1mon count as photos",
  "Trends how many photos you take each month, revealing the busy seasons and quiet stretches of your life.",
  "A photo-volume trend is a surprisingly good map of the eventful and restful chapters of a year.",
  "Ingest photo metadata into `index=personal`; count photos per month.",
  "Column chart of photos taken per month.",
  "It counts how many photos you take each month, quietly mapping the busy and quiet times of your life.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Places-Visited Map", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=location:visit\n"
  "| stats count as visits, dc(place) as unique_places by region\n"
  "| sort - visits",
  "Summarises the places and regions you have visited so you can see how far you roam and where you return.",
  "A map of your movements makes the shape of your life visible and surfaces places worth revisiting.",
  "Ingest location history into `index=personal`; count visits by place and region.",
  "Map or bar chart of visits by region.",
  "It maps the places you have been, showing how far you roam and the spots you keep returning to.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "On-This-Day Memory Resurfacing", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=lifelog:moment\n"
  "| eval this_day=strftime(_time,\"%m-%d\"), today=strftime(now(),\"%m-%d\")\n"
  "| where this_day=today AND _time<relative_time(now(),\"-1y@d\")\n"
  "| table _time title place\n"
  "| sort - _time",
  "Resurfaces moments you logged on this calendar date in previous years, like a personal on-this-day feed.",
  "Rediscovering old moments brings unexpected joy and stitches the years of your life together.",
  "Ingest logged moments into `index=personal`; surface entries from the same date in past years.",
  "Table of past moments from today's date.",
  "It brings back things that happened on this very day in past years, a lovely surprise of old memories.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "New-Place Discovery Rate", "low", "intermediate", ["Analytics", "Anomaly"],
  "index=personal sourcetype=location:visit\n"
  "| streamstats dc(place) as places_seen\n"
  "| bin _time span=1mon\n"
  "| stats max(places_seen) as cumulative by _time\n"
  "| delta cumulative as new_places\n"
  "| sort _time",
  "Counts how many genuinely new places you visit each month versus returning to familiar ones.",
  "A discovery rate is a gentle nudge against routine and toward exploring your own city and world.",
  "Ingest location history into `index=personal`; count first-time places per month.",
  "Column chart of new places discovered per month.",
  "It counts how many brand-new places you visit each month, nudging you to keep exploring.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Voice-Memo Capture Habit", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=voicememo:note\n"
  "| bin _time span=1w\n"
  "| stats count as memos, sum(duration_s) as seconds by _time\n"
  "| eval minutes=round(seconds/60,1)\n"
  "| sort - _time",
  "Tracks how often you capture thoughts as voice memos and how much you record each week.",
  "Voice capture is a low-friction way to hold onto ideas; tracking it reinforces a useful habit.",
  "Ingest voice-memo metadata into `index=personal`; count and total duration per week.",
  "Column chart of voice memos captured per week.",
  "It tracks how often you record quick voice notes, encouraging a simple way to hold onto ideas.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Life-Event Timeline", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=timeline:event\n"
  "| bin _time span=1y\n"
  "| stats count as events, values(category) as categories by _time\n"
  "| sort _time",
  "Builds a year-by-year timeline of the milestones and events you have logged across your life.",
  "A single timeline of your life's chapters is a treasure to look back on and to share with family.",
  "Ingest milestone events into `index=personal`; group by year.",
  "Timeline chart of life events by year.",
  "It lays out the big moments of your life year by year, a timeline you will treasure looking back on.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Photo Backup Coverage", "medium", "intermediate", ["Availability", "Anomaly"],
  "index=personal sourcetype=photo:capture\n"
  "| stats count as photos, sum(eval(if(backed_up=\"yes\",1,0))) as backed_up\n"
  "| eval unbacked=photos-backed_up, coverage_pct=round(100*backed_up/photos,1)",
  "Checks what share of your photos are safely backed up and how many exist only on one device.",
  "Photos are irreplaceable; a backup-coverage check prevents the heartbreak of a lost phone taking memories with it.",
  "Ingest photo backup status into `index=personal`; compute backup coverage.",
  "Single-value panel of photo backup coverage.",
  "It checks how many of your photos are safely backed up, so a lost phone never takes your memories with it.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "People-in-Photos Frequency", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=photo:capture\n"
  "| stats count as photos by person\n"
  "| where person!=\"\"\n"
  "| sort - photos\n"
  "| head 15",
  "Counts who appears most in your photos, gently revealing the people you spend the most time with.",
  "Seeing who fills your photo library is a heartfelt reminder of the relationships at the centre of your life.",
  "Ingest photo people-tags into `index=personal`; count photos per person.",
  "Bar chart of photo counts by person.",
  "It counts who shows up most in your photos, a warm reminder of the people closest to you.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Journaling Consistency Streak", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=lifelog:moment\n"
  "| bin _time span=1d\n"
  "| stats count as entries by _time\n"
  "| eval logged=if(entries>0,1,0)\n"
  "| streamstats reset_after=\"(logged=0)\" sum(logged) as streak\n"
  "| sort - _time",
  "Tracks your run of consecutive days with at least one logged moment or journal entry.",
  "A visible streak makes the memory-keeping habit stick, and the record grows richer the longer it runs.",
  "Ingest logged moments into `index=personal`; compute the daily journaling streak.",
  "Single-value panel of the current journaling streak.",
  "It counts how many days in a row you have jotted something down, keeping the memory habit alive.",
  R(LG_REF), LG_APP, LG_DS)

U("58", "Year-in-Review Summary", "low", "advanced", ["Analytics", "Business"],
  "index=personal (sourcetype=photo:capture OR sourcetype=location:visit OR sourcetype=lifelog:moment)\n"
  "| where _time>relative_time(now(),\"-1y@d\")\n"
  "| stats count(eval(sourcetype=\"photo:capture\")) as photos, dc(eval(if(sourcetype=\"location:visit\",place,null()))) as places, count(eval(sourcetype=\"lifelog:moment\")) as moments",
  "Rolls up a year of photos, places, and logged moments into one shareable year-in-review.",
  "A personal year-in-review turns scattered data into a story of the year that is genuinely moving to read.",
  "Combine memory feeds in `index=personal`; summarise the last year in one view.",
  "Summary panel of the year's photos, places, and moments.",
  "It gathers a whole year of photos, places, and moments into one review, telling the story of your year.",
  R(LG_REF), LG_APP, LG_DS)

# ===========================================================================
# 25.59  Personal Life-OS & Gamification
# ===========================================================================
OS_APP = ("The parody-the-enterprise meta layer — a Personal NOC (house-health wall), Personal SOC "
          "(entry / impossible-travel), Personal SRE (SLOs on your own habits), and a gamification "
          "layer (XP, achievements, streaks, household leaderboards) — all computed in Splunk over "
          "`index=personal`.")
OS_DS = ("Life score (`lifeos:score`), quests / tasks (`quest:task`), habit streaks "
         "(`streak:status`), life achievements (`achievement:life`), household leaderboard "
         "(`household:leaderboard`), plus every other `index=personal` sourcetype as input.")
OS_REF = ("Google SRE — service level objectives", "https://sre.google/sre-book/service-level-objectives/")

U("59", "Personal SLOs and Error Budgets", "low", "advanced", ["Analytics", "Business"],
  "index=personal sourcetype=streak:status\n"
  "| bin _time span=1mon\n"
  "| stats sum(eval(if(met=\"yes\",1,0))) as good_days, count as days by habit _time\n"
  "| eval slo_pct=round(100*good_days/days,1), error_budget=round(days*0.1,0), budget_used=days-good_days\n"
  "| where slo_pct<90",
  "Treats your habits like service objectives — a 90% target with an error budget — and flags the ones falling short.",
  "Borrowing the reliability engineer's error-budget idea makes habit-keeping realistic: it allows off-days without abandoning the goal.",
  "Ingest daily habit outcomes into `index=personal`; compute each habit's objective and error budget.",
  "Table of habits with objective attainment and budget used.",
  "It treats your habits like promises with a little room to slip, and flags the ones you are missing too often.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Life-Score Composite Dashboard", "low", "advanced", ["Analytics", "Business"],
  "index=personal sourcetype=lifeos:score\n"
  "| timechart span=1d avg(score) as life_score by domain\n"
  "| untable _time domain life_score",
  "Combines your health, money, relationships, and growth into one daily life score across domains.",
  "A single composite score is the executive dashboard of your own life — a fast read on where to focus.",
  "Ingest per-domain scores into `index=personal`; trend the composite daily.",
  "Line chart of life score by domain over time.",
  "It blends how you are doing in health, money, and relationships into one daily score for your whole life.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "XP and Level-Up Tracker", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=achievement:life\n"
  "| bin _time span=1w\n"
  "| stats sum(xp) as weekly_xp by _time\n"
  "| streamstats sum(weekly_xp) as total_xp\n"
  "| eval level=floor(sqrt(total_xp/100))\n"
  "| sort - _time",
  "Turns your real-life accomplishments into experience points and levels, gamifying self-improvement.",
  "A game layer makes the slow work of building a good life feel rewarding in the moment.",
  "Ingest achievement events into `index=personal`; total XP and compute your level.",
  "Line chart of cumulative XP with level milestones.",
  "It turns the good things you do into points and levels, making self-improvement feel like a game.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Household Chore Leaderboard", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=household:leaderboard\n"
  "| bin _time span=1w\n"
  "| stats sum(points) as points by person _time\n"
  "| stats sum(points) as total by person\n"
  "| sort - total",
  "Ranks household members by chore points earned, turning shared work into a friendly competition.",
  "A leaderboard makes housework fairer and, for families, genuinely fun to keep on top of.",
  "Ingest chore completions into `index=personal`; rank members by points.",
  "Bar chart of household chore points by person.",
  "It ranks who has done the most chores, turning housework into a friendly family competition.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Quest Board and Daily Quests", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=quest:task\n"
  "| stats count as quests, sum(eval(if(status=\"done\",1,0))) as completed by quest_type\n"
  "| eval completion_pct=round(100*completed/quests,1)\n"
  "| sort - completion_pct",
  "Frames your to-dos as daily, weekly, and epic quests and tracks how many you complete.",
  "Reframing chores as quests is a small trick that makes ordinary tasks more inviting to finish.",
  "Ingest tasks tagged as quests into `index=personal`; track completion by quest type.",
  "Bar chart of quest completion by type.",
  "It turns your to-do list into daily and epic quests, making everyday tasks more fun to finish.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Streak Boss-Battle Watch", "low", "intermediate", ["Availability", "Anomaly"],
  "index=personal sourcetype=streak:status\n"
  "| stats max(current_streak) as streak, max(best_streak) as best by habit\n"
  "| eval near_record=if(streak>=best*0.9 AND streak<best,1,0)\n"
  "| where streak>0\n"
  "| sort - streak",
  "Highlights habits where your current streak is closing in on your personal best, framing it as a boss battle.",
  "Knowing you are one good week from a record is powerful motivation to not break the chain.",
  "Ingest habit streaks into `index=personal`; flag streaks near their record.",
  "Table of habits with current versus best streak.",
  "It spots when you are close to beating your own record for a habit, giving you a reason to keep going.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Life-Domain Status Wall", "medium", "advanced", ["Availability", "Analytics"],
  "index=personal (sourcetype=lifeos:score OR sourcetype=streak:status)\n"
  "| stats latest(score) as score by domain\n"
  "| eval status=case(score>=80,\"green\",score>=60,\"amber\",1=1,\"red\")\n"
  "| sort domain",
  "Presents every area of your life as a status tile — green, amber, red — like an operations centre wall for yourself.",
  "A single glance tells you which part of life needs attention today, the way a NOC wall does for systems.",
  "Combine life-domain scores in `index=personal`; render red/amber/green status tiles.",
  "Status-tile wall of life domains by health.",
  "It shows each part of your life as a green, amber, or red light, so one glance tells you what needs attention.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Achievement Unlock Log", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=achievement:life\n"
  "| bin _time span=1mon\n"
  "| stats count as unlocked, values(achievement) as badges by _time\n"
  "| sort - _time",
  "Logs the achievements and badges you unlock each month — first 10k, dry January, read 12 books.",
  "Celebrating unlocked milestones, however small, keeps the momentum of self-improvement going.",
  "Ingest achievement unlocks into `index=personal`; summarise per month.",
  "Table of achievements unlocked by month.",
  "It keeps a log of the milestones you unlock, so you can celebrate every win big or small.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Habit-Chain Break Alert", "low", "intermediate", ["Availability", "Anomaly"],
  "index=personal sourcetype=streak:status\n"
  "| where current_streak=0 AND yesterday_streak>=7\n"
  "| table habit yesterday_streak\n"
  "| sort - yesterday_streak",
  "Alerts you the moment a meaningful habit streak breaks so you can restart before the habit fades.",
  "The day after a broken streak is when habits quietly die; a prompt to restart is the best defence.",
  "Ingest habit streaks into `index=personal`; alert when a long streak resets to zero.",
  "Table of recently broken streaks.",
  "It tells you the moment a good streak breaks, so you can get straight back on it before the habit slips away.",
  R(OS_REF), OS_APP, OS_DS)

U("59", "Weekly Life Retrospective", "low", "advanced", ["Analytics", "Business"],
  "index=personal (sourcetype=lifeos:score OR sourcetype=quest:task OR sourcetype=achievement:life)\n"
  "| where _time>relative_time(now(),\"-7d@d\")\n"
  "| stats avg(score) as avg_score, sum(eval(if(status=\"done\",1,0))) as quests_done, sum(xp) as xp_earned",
  "Produces a weekly retrospective — average life score, quests done, XP earned — like a sprint review for yourself.",
  "A regular retro builds the habit of reflection and steady adjustment that makes real change stick.",
  "Combine life feeds in `index=personal`; summarise the past week for a personal retro.",
  "Weekly summary panel of score, quests, and XP.",
  "It gives you a weekly review of how life went — your score, tasks done, and points earned — to learn and adjust.",
  R(OS_REF), OS_APP, OS_DS)

# ===========================================================================
# 25.60  Self-Forecasting & Prediction Markets on Yourself
# ===========================================================================
PF_APP = ("Personal forecasting and calibration — a private prediction journal of dated forecasts "
          "about your own life, resolved outcomes, and calibration / Brier scoring — streamed to "
          "Splunk HEC via scripted inputs.")
PF_DS = ("Forecasts (`prediction:forecast`), resolved outcomes (`prediction:outcome`), personal "
         "bets (`bet:personal`), calibration scores (`calibration:score`), Brier scores "
         "(`brier:score`).")
PF_REF = ("Good Judgment — forecasting principles", "https://goodjudgment.com/")

U("60", "Forecast Calibration Curve", "low", "advanced", ["Analytics"],
  "index=personal sourcetype=prediction:outcome\n"
  "| eval bucket=round(confidence,-1)\n"
  "| stats avg(eval(if(result=\"correct\",1,0))) as hit_rate, count as n by bucket\n"
  "| eval hit_pct=round(100*hit_rate,1)\n"
  "| sort bucket",
  "Compares how often your predictions come true against how confident you were, building a personal calibration curve.",
  "Good calibration — being right about as often as you claim — is a learnable skill and the core of good judgement.",
  "Ingest forecasts and resolved outcomes into `index=personal`; group hit rate by confidence bucket.",
  "Scatter or line chart of confidence versus actual hit rate.",
  "It checks whether things you were sure about actually happened, showing how well you really judge the future.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Brier-Score Trend", "low", "advanced", ["Analytics", "Anomaly"],
  "index=personal sourcetype=brier:score\n"
  "| timechart span=1mon avg(brier) as avg_brier\n"
  "| eventstats avg(avg_brier) as overall",
  "Trends your Brier score — a measure of forecasting accuracy — over time so you can watch your judgement improve.",
  "A falling Brier score is hard evidence that you are getting better at predicting your own life, not just guessing.",
  "Ingest scored forecasts into `index=personal`; trend the monthly Brier score.",
  "Line chart of monthly Brier score (lower is better).",
  "It tracks a score of how accurate your predictions are, so you can watch your judgement sharpen over time.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Overconfidence Detector", "low", "advanced", ["Anomaly", "Analytics"],
  "index=personal sourcetype=prediction:outcome confidence>=90\n"
  "| stats avg(eval(if(result=\"correct\",1,0))) as hit_rate, count as n\n"
  "| eval hit_pct=round(100*hit_rate,1), overconfidence_gap=round(95-hit_pct,1)",
  "Checks the predictions you were almost certain about and measures how often you were actually right.",
  "Overconfidence is the most common judgement error; measuring your own gap is the first step to fixing it.",
  "Ingest high-confidence forecasts into `index=personal`; compare claimed confidence to the real hit rate.",
  "Single-value panel of the overconfidence gap.",
  "It checks the things you were absolutely sure about and shows how often you were actually right.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Open-Prediction Resolution Queue", "low", "beginner", ["Availability", "Business"],
  "index=personal sourcetype=prediction:forecast status=open\n"
  "| eval days_to_resolve=round((resolve_by-now())/86400,1)\n"
  "| where days_to_resolve<7\n"
  "| table question confidence resolve_by days_to_resolve\n"
  "| sort days_to_resolve",
  "Lists predictions whose resolution date is coming up so you remember to score them honestly and on time.",
  "Unresolved forecasts quietly rot; a resolution queue keeps your track record complete and trustworthy.",
  "Ingest open forecasts into `index=personal`; surface those due to resolve soon.",
  "Table of predictions due to resolve this week.",
  "It reminds you which of your predictions are due to be settled soon, so you always keep an honest score.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Prediction Topic Accuracy", "low", "intermediate", ["Analytics"],
  "index=personal sourcetype=prediction:outcome\n"
  "| stats avg(eval(if(result=\"correct\",1,0))) as hit_rate, count as n by topic\n"
  "| eval hit_pct=round(100*hit_rate,1)\n"
  "| where n>=3\n"
  "| sort - hit_pct",
  "Breaks your forecasting accuracy down by topic — work, health, relationships, money — to reveal your blind spots.",
  "Knowing which subjects you predict well and badly tells you where to trust yourself and where to seek advice.",
  "Ingest resolved outcomes by topic into `index=personal`; compute accuracy per topic.",
  "Bar chart of prediction accuracy by topic.",
  "It shows which parts of life you predict well and which you get wrong, revealing your blind spots.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Personal-Bet Ledger", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=bet:personal status=resolved\n"
  "| stats sum(eval(if(outcome=\"won\",stake,-stake))) as net, count as bets, sum(eval(if(outcome=\"won\",1,0))) as won\n"
  "| eval win_pct=round(100*won/bets,1)",
  "Keeps a ledger of friendly bets you make with yourself or friends and whether you come out ahead.",
  "A bet ledger turns idle 'I bet you' moments into a fun, honest scoreboard of who reads situations best.",
  "Ingest resolved personal bets into `index=personal`; total winnings and win rate.",
  "Summary panel of net result and win rate.",
  "It keeps score of the friendly bets you make, showing whether you come out ahead in the end.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "New-Year-Resolution Forecast", "low", "intermediate", ["Analytics", "Business"],
  "index=personal sourcetype=prediction:forecast topic=resolution\n"
  "| stats avg(confidence) as avg_confidence, count as resolutions, sum(eval(if(status=\"kept\",1,0))) as kept\n"
  "| eval kept_pct=round(100*kept/resolutions,1)",
  "Records your confidence that you will keep each new-year resolution and later scores how many you actually kept.",
  "Predicting your own follow-through — and being proven right or wrong — makes next year's resolutions wiser.",
  "Ingest resolution forecasts into `index=personal`; compare predicted confidence to kept rate.",
  "Summary panel of resolutions kept versus predicted.",
  "It records how sure you were about keeping each resolution, then shows how many you really kept.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Forecast Streak and Volume", "low", "beginner", ["Analytics", "Business"],
  "index=personal sourcetype=prediction:forecast\n"
  "| bin _time span=1mon\n"
  "| stats count as forecasts by _time\n"
  "| eventstats sum(forecasts) as total\n"
  "| sort - _time",
  "Tracks how many predictions you make each month, because a good track record needs a steady volume.",
  "Calibration only improves with practice; keeping your forecasting volume up is what makes the skill grow.",
  "Ingest forecasts into `index=personal`; count per month with a running total.",
  "Column chart of forecasts made per month.",
  "It counts how many predictions you make each month, because getting better needs steady practice.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Surprise-Index Watch", "low", "advanced", ["Anomaly", "Analytics"],
  "index=personal sourcetype=prediction:outcome\n"
  "| eval surprise=if(result=\"incorrect\" AND confidence>=80,1,0)\n"
  "| bin _time span=1mon\n"
  "| stats sum(surprise) as surprises, count as resolved by _time\n"
  "| eval surprise_pct=round(100*surprises/resolved,1)\n"
  "| sort - _time",
  "Counts the outcomes that genuinely surprised you — confident predictions that turned out wrong — each month.",
  "Surprises are the richest learning moments; tracking them makes sure you actually learn from being wrong.",
  "Ingest resolved outcomes into `index=personal`; count high-confidence misses per month.",
  "Column chart of monthly surprise rate.",
  "It counts the times life surprised you by proving a confident guess wrong, so you learn from each one.",
  R(PF_REF), PF_APP, PF_DS)

U("60", "Self-Forecasting Scorecard", "low", "advanced", ["Analytics", "Business"],
  "index=personal (sourcetype=prediction:outcome OR sourcetype=brier:score)\n"
  "| stats count(eval(sourcetype=\"prediction:outcome\")) as resolved, avg(eval(if(result=\"correct\",1,0))) as hit_rate, avg(brier) as avg_brier\n"
  "| eval hit_pct=round(100*hit_rate,1), brier=round(avg_brier,3)",
  "Combines your hit rate, calibration, and Brier score into one self-forecasting scorecard.",
  "One scorecard summarises how good a forecaster of your own life you have become — the ultimate self-knowledge metric.",
  "Combine forecasting feeds in `index=personal`; roll up accuracy and calibration.",
  "Summary panel of hit rate, calibration, and Brier score.",
  "It sums up how good you are at predicting your own life into one honest scorecard of self-knowledge.",
  R(PF_REF), PF_APP, PF_DS)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    total = sum(_counts.values())
    print(f"Wrote {total} use cases across {len(_counts)} subcategories:")
    for sub in sorted(_counts, key=int):
        print(f"  25.{sub}: {_counts[sub]}")
