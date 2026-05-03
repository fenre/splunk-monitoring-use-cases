<!-- AUTO-GENERATED from UC-5.9.18.json — DO NOT EDIT -->

---
id: "5.9.18"
title: "Network Outage Event Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.18 · Network Outage Event Detection

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We get alerts when major internet outages are detected around the world, so when our service slows down we can immediately tell whether it's our fault or whether the internet itself has a problem.*

---

## Description

Surfaces ThousandEyes Internet Insights events for network outages and path issues affecting your monitored tests. These are not raw test failures — they're correlated, de-duplicated events produced by ThousandEyes' collective intelligence engine, which analyzes traffic patterns across its entire customer base to detect ISP-level and cloud-provider-level outages before individual test metrics show clear degradation.

## Value

When an ISP or cloud provider experiences an outage, individual ThousandEyes test metrics (latency, loss) may show ambiguous results — some agents show degradation, others don't, and the picture is confusing. Internet Insights cuts through this ambiguity by correlating across the entire ThousandEyes customer base: if 50 different organizations' tests all show degradation on the same ISP path simultaneously, that's a confirmed ISP outage, not a coincidence. Ingesting these events into Splunk alongside your internal monitoring gives the NOC a definitive external/internal determination: "The latency spike we're seeing is part of a confirmed Cogent outage affecting 200+ ThousandEyes customers — this is not our infrastructure." That single sentence changes the response from a 2-hour internal troubleshooting exercise to a 5-minute ISP escalation.

## Implementation

Configure the Event input in the ThousandEyes App: **Inputs → Events → Create new input**. Select the ThousandEyes account group and configure the polling interval (default 300 seconds is appropriate). Set the `event_index` macro to point to `thousandeyes_events`. Event types are automatically classified by ThousandEyes' Internet Insights engine.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated).
- **Event input configured.** This is a SEPARATE input from the Tests Stream — Metrics input used in UC-5.9.1–17. Navigate to **Inputs → Events → Create new input**. The Event input polls the ThousandEyes Events API, which is separate from the OTel streaming API.
  - Select the ThousandEyes account group.
  - Set the destination index to `thousandeyes_events`.
  - Set the polling interval (default 300 seconds).
  - The Event input fetches events of all types (Network Outage, DNS Issue, Proxy Issue, Server Issue, Local Agent Issue, Network Path Issue). You filter by type in SPL, not in the input configuration.
- **`event_index` macro configured.** Navigate to **Settings → Advanced Search → Search Macros → event_index** and verify it expands to `index=thousandeyes_events`.
- **ThousandEyes Internet Insights.** Outage detection requires a ThousandEyes Advantage or Premier tier account. Essentials tier accounts can receive events for their own tests but do not have access to the Internet Insights collective intelligence engine. Check your account tier in ThousandEyes → Account Settings.

### Step 1 — Configure data collection
Create the Event input if not already configured:
1. Navigate to **Inputs → Events → Create new input**.
2. Select the ThousandEyes account group (same one used for OAuth authentication).
3. Set the index to `thousandeyes_events`.
4. Set polling interval to 300 seconds (5 minutes).
5. Save. The app begins polling the ThousandEyes Events API.

Verify events are flowing:
```spl
index=thousandeyes_events sourcetype="cisco:thousandeyes:event" earliest=-24h
| stats count by type
```
You should see event counts by type. It's normal for some types to have 0 events — outages don't happen every day. If NO events appear after 24 hours of collection, check:
- The Event input is enabled (Inputs → Events → verify status)
- OAuth token is valid (check `index=_internal "thousandeyes" "event" ERROR`)
- The account group has active tests (events are only generated for monitored tests)

**Events vs Metrics — understanding the difference:**
- **Metrics** (UC-5.9.1–17): raw measurements from individual test rounds (latency, loss, jitter, DNS duration). High volume, high frequency (every 1–15 minutes).
- **Events** (this UC and UC-5.9.20–22): pre-processed, correlated intelligence from ThousandEyes' analytics engine. Low volume, event-driven (only when anomalies are detected). Think of events as "ThousandEyes already analyzed the metrics and is telling you something is wrong."

### Step 2 — Create the search and alert
```spl
`event_index` type="Network Outage" OR type="Network Path Issue"
| stats count earliest(_time) as first_seen latest(_time) as last_seen by type, severity, state
| eval duration_min = round((last_seen - first_seen) / 60, 0)
| sort -count
```

**Understanding this SPL**

`event_index` — expands to `index=thousandeyes_events` (the app-defined macro for event data).

`type="Network Outage" OR type="Network Path Issue"` — filters to network-specific event types. Other event types (DNS Issue, Proxy Issue, Server Issue, Local Agent Issue) are covered in UC-5.9.20–22.

`earliest(_time) ... latest(_time)` — captures the event lifecycle. A long `duration_min` indicates a sustained outage.

`state` — `active` means the outage is ongoing; `resolved` means it has ended. For alerting, filter to `state="active"` to avoid re-alerting on resolved events.

**Active outage alert:**
```spl
`event_index` type="Network Outage" state="active" severity="high"
| stats count by type, severity, state, thousandeyes.test.name
| where count > 0
```

**Scheduling:** cron `*/5 * * * *`, time range `-15m to now`. Use 5-minute schedule because outage events are high-severity. Throttle by `type` for 1 hour.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Internet Insights → Overview** to see the global outage map. Active outages should appear both in the UI and in Splunk.

(b) **Check event_index macro.** `| makeresults | eval test="\`event_index\`"` — verify it expands to the correct index.

(c) **Historical validation.** If a known internet outage occurred recently (check ThousandEyes Outage Detection page or social media reports), verify that Splunk has a corresponding event.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes — Internet Health & Events"):
- Row 1 — Active outage count (single value, red ≥ 1). Active path issues count. Time since last outage event.
- Row 2 — Events timeline: `| timechart span=15m count by type` over 24 hours.
- Row 3 — Table: type | severity | state | test name | first seen | duration — sorted by state (active first) then severity.

**Alerting:**
- Active "Network Outage" with severity "high" → immediate notification to NOC. This is a confirmed ISP-level event.
- Include the event type, severity, affected test names, and ThousandEyes permalink in the alert payload.

**Runbook** (owner: NOC):
1. **Active Network Outage event detected.** Check the ThousandEyes permalink to identify the affected ISP/provider.
2. **Correlate with internal alerts.** Check whether internal monitoring (ITSI, application alerts) shows degradation during the same window. If yes → the external outage is affecting your services. If no → the outage is not on your traffic's path.
3. **Communicate.** If the outage affects your users, post to the internal status page: "Degradation caused by [ISP] network outage, not our infrastructure. ThousandEyes tracking, ETA from ISP: [time]."
4. **Mitigate.** If you have redundant ISP paths or SD-WAN, verify failover occurred. If not, manually reroute traffic.
5. **Track resolution.** Monitor the event `state` — when it changes to `resolved`, verify your metrics (UC-5.9.1–3) return to baseline.

### Step 5 — Troubleshooting

- **No events appear even during known outages** — Check your ThousandEyes account tier. Internet Insights (which generates outage events) requires Advantage or Premier tier. Essentials tier only generates events for your own test failures, not correlated outage intelligence.

- **Events appear in ThousandEyes UI but not in Splunk** — The Event input may not be configured, or the polling interval may be too long. Check Inputs → Events → verify the input is enabled and running. Check `index=_internal "thousandeyes" "event"` for API errors.

- **Too many events / noisy** — Internet Insights can be verbose for organizations monitoring many paths. Filter to `severity="high"` for alerting and use lower severities for dashboard trending only.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for OAuth refresh, macro configuration, and general app troubleshooting.

## SPL

```spl
`event_index` type="Network Outage" OR type="Network Path Issue"
| stats count earliest(_time) as first_seen latest(_time) as last_seen by type, severity, state
| eval duration_min = round((last_seen - first_seen) / 60, 0)
| sort -count
```

## Visualization

(1) Events timeline: `| timechart span=15m count by type` showing outage events over 24 hours. (2) Table: type, severity, state, count, duration (minutes) — sorted by severity then count. (3) Single value: count of active "Network Outage" events (red ≥ 1). (4) Pie chart: events by type, showing the distribution of network outages, path issues, DNS issues, etc. (5) The ThousandEyes Splunk app includes built-in event dashboards.

## Known False Positives

**Events for ISPs/providers you don't directly use.** Internet Insights may detect outages on ISP networks that your traffic doesn't traverse — the event is real but doesn't affect your users. Distinguish by cross-referencing the affected ISP/provider in the event with your actual network paths (UC-5.9.5/6). Focus on events that name ISPs present in your test results' AS paths.

**Brief flaps classified as outage events.** ThousandEyes may classify a brief network flap (< 5 minutes) as an outage event before it auto-resolves. Check the `state` field — if it transitions to `resolved` quickly, it was transient. For alerting, consider adding `state="active"` and waiting one polling interval before paging.

**Overlapping events for the same underlying cause.** A single backbone failure can generate multiple events (Network Outage, Network Path Issue, DNS Issue) as different symptoms surface. These are related events for the same root cause. Check whether multiple event types fire at the same time and correlate to the same ISP/provider.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Internet Insights — Outage detection](https://docs.thousandeyes.com/product-documentation/internet-insights)
- [ThousandEyes Splunk App — Event inputs](https://docs.thousandeyes.com/product-documentation/integration-guides/custom-built-integrations/splunk-app/inputs)
