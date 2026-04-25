<!-- AUTO-GENERATED from UC-2.6.26.json — DO NOT EDIT -->

---
id: "2.6.26"
title: "Per-Application Network Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.26 · Per-Application Network Performance

## Description

uberAgent measures network latency, data volume, and connection quality per application and per target host. This reveals which applications are generating the most network traffic, connecting to slow endpoints, or experiencing high latency — critical for optimising CVAD network policies and WAN bandwidth allocation.

## Value

uberAgent measures network latency, data volume, and connection quality per application and per target host. This reveals which applications are generating the most network traffic, connecting to slow endpoints, or experiencing high latency — critical for optimising CVAD network policies and WAN bandwidth allocation.

## Implementation

Enable uberAgent's per-application network monitoring feature. Identify bandwidth-heavy applications and high-latency network targets. Use to validate that HDX redirection policies are routing multimedia traffic efficiently. Detect applications bypassing proxy or connecting to unexpected external hosts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) with Per-Application Network Monitoring.
• Ensure the following data sources are available: `sourcetype="uberAgent:Process:NetworkTargetPerformance"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable uberAgent's per-application network monitoring feature. Identify bandwidth-heavy applications and high-latency network targets. Use to validate that HDX redirection policies are routing multimedia traffic efficiently. Detect applications bypassing proxy or connecting to unexpected external hosts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Process:NetworkTargetPerformance" earliest=-4h
| stats avg(ConnectDurationMs) as avg_latency_ms sum(DataVolumeSentBytes) as bytes_sent sum(DataVolumeReceivedBytes) as bytes_rcvd dc(User) as users by AppName, NetworkTargetName
| eval total_mb=round((bytes_sent+bytes_rcvd)/1048576,1)
| where avg_latency_ms > 100 OR total_mb > 500
| sort -total_mb
| table AppName, NetworkTargetName, avg_latency_ms, total_mb, users
```

Understanding this SPL

**Per-Application Network Performance** — uberAgent measures network latency, data volume, and connection quality per application and per target host. This reveals which applications are generating the most network traffic, connecting to slow endpoints, or experiencing high latency — critical for optimising CVAD network policies and WAN bandwidth allocation.

Documented **Data sources**: `sourcetype="uberAgent:Process:NetworkTargetPerformance"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) with Per-Application Network Monitoring. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Process:NetworkTargetPerformance. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Process:NetworkTargetPerformance", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by AppName, NetworkTargetName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **total_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_latency_ms > 100 OR total_mb > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Per-Application Network Performance**): table AppName, NetworkTargetName, avg_latency_ms, total_mb, users

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top bandwidth consumers), Bar chart (latency by target), Sankey diagram (app to network target flow).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Process:NetworkTargetPerformance" earliest=-4h
| stats avg(ConnectDurationMs) as avg_latency_ms sum(DataVolumeSentBytes) as bytes_sent sum(DataVolumeReceivedBytes) as bytes_rcvd dc(User) as users by AppName, NetworkTargetName
| eval total_mb=round((bytes_sent+bytes_rcvd)/1048576,1)
| where avg_latency_ms > 100 OR total_mb > 500
| sort -total_mb
| table AppName, NetworkTargetName, avg_latency_ms, total_mb, users
```

## Visualization

Table (top bandwidth consumers), Bar chart (latency by target), Sankey diagram (app to network target flow).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
