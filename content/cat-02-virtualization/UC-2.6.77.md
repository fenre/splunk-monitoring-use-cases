<!-- AUTO-GENERATED from UC-2.6.77.json — DO NOT EDIT -->

---
id: "2.6.77"
title: "Citrix Per-Application Perceived Performance (Startup vs Hang vs Network)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.77 · Citrix Per-Application Perceived Performance (Startup vs Hang vs Network)

## Description

Not all “Citrix is slow” tickets are a network problem. Perceived slowness may be slow application startup, long UI busy states, or real ICA network delay. Combining process startup and hang signals from the VDA with network metrics and broker-reported app ready time splits accountability between packaging, the app itself, the profile, and the path between user and host.

## Value

Not all “Citrix is slow” tickets are a network problem. Perceived slowness may be slow application startup, long UI busy states, or real ICA network delay. Combining process startup and hang signals from the VDA with network metrics and broker-reported app ready time splits accountability between packaging, the app itself, the profile, and the path between user and host.

## Implementation

Standardize on one app name key (avoid publisher vs start-menu title drift). In uberAgent, enable process and network packs for gold images only first. If ICA RTT is missing in uberAgent, add broker or gateway RTT. Build three small alerts: p95 startup, p95 RTT, and not-responding process count, each routed to a different team owner.

## Detailed Implementation

Prerequisites
• `index=xd` with `uberAgent:Process:ProcessStartup`, `Network:Performance`, and `citrix:broker:app_usage`. UberAgent in gold image; broker exports `launch_to_ready_ms` and app title.

Step 1 — Configure data collection
`lookups/citrix_app_friendly_names.csv` maps `process_name` to `app` for LOB. Exclude backup/AV using a `lookup` column on noisy `process_name` (avoid brittle regexes on `app` alone). Pilot 2 LOB + Office. Verify `startup_ms` is milliseconds, not seconds.

Step 2 — Create the search and alert
Baseline p50/p95 per app 14d; replace static 10000/100 with lookup-driven SLO. Split alerts: p95 `med_start` to app team; p95 `med_ica` to network; `hang_ev` sustained 3x15m to EUC. Add `by host` to find noisy VDAs.

Step 3 — Validate
On one ticket, align `_time` to Director/HDX and a screen cap showing not-responding vs high RTT. Confirm uberAgent and broker clocks within 1s.

Step 4 — Operationalize
Dashboard: small-multiples for top 10 `app`. QBR: split accountability chart. Escalation: packaging vs net vs VDA. Re-baseline after uberAgent, VDA, or broker upgrade.

## SPL

```spl
index=xd (sourcetype="uberAgent:Process:ProcessStartup" OR sourcetype="uberAgent:Network:Performance" OR sourcetype="citrix:broker:app_usage") earliest=-4h
| eval app=coalesce(app_name, process_name, title, "unknown"), start_ms=tonumber(startup_ms), ica=tonumber(ica_rtt_ms), hang=if(match(_raw, "(?i)not.?(responding)"),1,0)
| bin _time span=15m
| stats median(start_ms) as med_start, median(ica) as med_ica, sum(hang) as hang_ev by _time, app, host
| where med_start>10000 OR med_ica>100 OR hang_ev>0
| table _time, app, host, med_start, med_ica, hang_ev
```

## Visualization

Small multiples: one row per app with startup, hang count, and RTT; table: top hosts driving bad p95; overlay change markers on image or app version.

## References

- [uberAgent — Process and network metrics](https://splunkbase.splunk.com/app/1448)
- [Citrix — HDX and session performance](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-adaptive-technologies.html)
