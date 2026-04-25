<!-- AUTO-GENERATED from UC-5.4.34.json — DO NOT EDIT -->

---
id: "5.4.34"
title: "Aruba ClearPass RADIUS Authentication Health (HPE Aruba)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.34 · Aruba ClearPass RADIUS Authentication Health (HPE Aruba)

## Description

ClearPass Policy Manager is the authentication backbone for Aruba wireless networks, handling 802.1X, MAC auth, and captive portal. RADIUS authentication failures, timeouts, and server unreachability directly prevent users from connecting. Track auth success/failure ratios, latency, and server health.

## Value

ClearPass Policy Manager is the authentication backbone for Aruba wireless networks, handling 802.1X, MAC auth, and captive portal. RADIUS authentication failures, timeouts, and server unreachability directly prevent users from connecting. Track auth success/failure ratios, latency, and server health.

## Implementation

Ingest ClearPass access tracker and RADIUS-related logs via the ClearPass app. Normalize `Accept`/`Reject`/`Challenge` and timeout/unreachable patterns. Alert when reject rate or timeouts spike versus baseline, or when average RADIUS latency exceeds policy (e.g. 500ms). Segment by `nas_ip` (controller/AP cluster) to isolate WLAN vs ClearPass issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `HPE Aruba ClearPass App for Splunk` (Splunkbase 7865).
• Ensure the following data sources are available: `sourcetype=aruba:clearpass`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest ClearPass access tracker and RADIUS-related logs via the ClearPass app. Normalize `Accept`/`Reject`/`Challenge` and timeout/unreachable patterns. Alert when reject rate or timeouts spike versus baseline, or when average RADIUS latency exceeds policy (e.g. 500ms). Segment by `nas_ip` (controller/AP cluster) to isolate WLAN vs ClearPass issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="aruba:clearpass" ("RADIUS" OR TipsService="RADIUS" OR module="RADIUS")
| eval result=coalesce(Enforcement_Result, Auth_Result, Status, if(match(_raw,"Access-Accept"),"Accept",if(match(_raw,"Access-Reject"),"Reject",null())))
| rex field=_raw max_match=0 "(?i)Access-(?<radius_reply>Accept|Reject|Challenge)"
| eval outcome=coalesce(result, radius_reply)
| eval latency_ms=coalesce(request_latency_ms, Radius_Request_Time, elapsed_ms, duration_ms)
| eval is_timeout=if(match(_raw,"(?i)timeout|timed out|server.unreachable|no.response.from"),1,0)
| stats count as events, sum(is_timeout) as timeouts, avg(latency_ms) as avg_latency_ms by outcome, radius_server, nas_ip
| where like(outcome,"%Reject%") OR like(lower(outcome),"%fail%") OR timeouts>0 OR avg_latency_ms>500
| sort -events
```

Understanding this SPL

**Aruba ClearPass RADIUS Authentication Health (HPE Aruba)** — ClearPass Policy Manager is the authentication backbone for Aruba wireless networks, handling 802.1X, MAC auth, and captive portal. RADIUS authentication failures, timeouts, and server unreachability directly prevent users from connecting. Track auth success/failure ratios, latency, and server health.

Documented **Data sources**: `sourcetype=aruba:clearpass`. **App/TA** (typical add-on context): `HPE Aruba ClearPass App for Splunk` (Splunkbase 7865). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: aruba:clearpass. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="aruba:clearpass". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **result** — often to normalize units, derive a ratio, or prepare for thresholds.
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **outcome** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **is_timeout** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by outcome, radius_server, nas_ip** so each row reflects one combination of those dimensions.
• Filters the current rows with `where like(outcome,"%Reject%") OR like(lower(outcome),"%fail%") OR timeouts>0 OR avg_latency_ms>500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Aruba Central, the mobility controller UI, or ClearPass Policy Manager (Access Tracker / policy views), compare authentication and health events with the search for the same timeframe.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (accept vs reject vs timeout), Bar chart (outcomes by NAS), Table (radius_server, NAS, latency, counts), Single value (auth availability %).

## SPL

```spl
index=network sourcetype="aruba:clearpass" ("RADIUS" OR TipsService="RADIUS" OR module="RADIUS")
| eval result=coalesce(Enforcement_Result, Auth_Result, Status, if(match(_raw,"Access-Accept"),"Accept",if(match(_raw,"Access-Reject"),"Reject",null())))
| rex field=_raw max_match=0 "(?i)Access-(?<radius_reply>Accept|Reject|Challenge)"
| eval outcome=coalesce(result, radius_reply)
| eval latency_ms=coalesce(request_latency_ms, Radius_Request_Time, elapsed_ms, duration_ms)
| eval is_timeout=if(match(_raw,"(?i)timeout|timed out|server.unreachable|no.response.from"),1,0)
| stats count as events, sum(is_timeout) as timeouts, avg(latency_ms) as avg_latency_ms by outcome, radius_server, nas_ip
| where like(outcome,"%Reject%") OR like(lower(outcome),"%fail%") OR timeouts>0 OR avg_latency_ms>500
| sort -events
```

## Visualization

Timechart (accept vs reject vs timeout), Bar chart (outcomes by NAS), Table (radius_server, NAS, latency, counts), Single value (auth availability %).

## References

- [Splunkbase app 7865](https://splunkbase.splunk.com/app/7865)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
