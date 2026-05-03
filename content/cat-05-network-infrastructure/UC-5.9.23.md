<!-- AUTO-GENERATED from UC-5.9.23.json — DO NOT EDIT -->

---
id: "5.9.23"
title: "Internet Outage Correlation with Internal Alerts"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.23 · Internet Outage Correlation with Internal Alerts

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*When something breaks at work, we immediately check whether the internet itself has a problem — because if the internet is broken, there's nothing wrong with our systems and the team can stop panicking and just wait for the internet to fix itself.*

---

## Description

Correlates ThousandEyes Internet Insights outage events with internally generated Splunk alerts to determine whether internal incidents are caused by external internet infrastructure failures. When a ThousandEyes Network Outage, DNS Issue, or Proxy Issue event is active, this UC automatically checks whether internal Splunk alerts fired during the same window — answering the critical question: "Is our current incident an internal problem or an internet-wide problem?"

## Value

The single most expensive waste of engineering time during an incident is troubleshooting the wrong root cause. When a cloud application goes down, teams spend hours investigating the application, the load balancer, the database, and the CDN — only to discover 4 hours later that the ISP had a routing failure. This UC eliminates that waste by providing immediate causal context: if a ThousandEyes Internet Insights event overlaps with your internal alerts, the external outage is the likely root cause. This can cut MTTR by 60–90% for externally caused incidents by redirecting the team from "fix it" to "wait for provider recovery and communicate to stakeholders." For a 4-hour P1 incident, reducing MTTR to 30 minutes saves hundreds of engineering hours and prevents unnecessary rollbacks or hotfixes.

## Implementation

Combine ThousandEyes Internet Insights events with internal Splunk alert audit trail using time-windowed correlation. The core technique: identify active Internet Insights events, define the outage time window, then query the internal alert audit index for alerts that fired within that window. The `map` command enables dynamic time-range correlation across different indexes.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.18 apply — Event input configured, `event_index` macro set.
- **Internal alerting is operational.** You must have existing Splunk saved searches / alerts that fire during incidents. The correlation works by querying `index=_audit action="fired"` (the triggered alerts audit trail) or your notable events index.
- **Role permissions:** The service account running this search needs read access to both `thousandeyes_events` AND `_audit` (or `notable`) indexes.
- **Understand the `map` command:** This UC uses `map` to perform a subsearch with dynamic time ranges. The `map` command has a default limit of 10 subsearches; increase with `maxsearches` if needed.

### Step 1 — Configure data collection
No additional data collection is needed — this UC consumes data already collected by UC-5.9.18 (events) and your existing Splunk alerting.

Verify data availability:
```spl
index=thousandeyes_events (type="Network Outage" OR type="DNS Issue" OR type="Proxy Issue") earliest=-30d
| stats count by type, severity
```

Verify internal alert audit trail:
```spl
index=_audit action="fired" earliest=-7d
| stats count by search_name
| sort -count
```

### Step 2 — Create the search
**Primary correlation search:**
```spl
`event_index` (type="Network Outage" OR type="DNS Issue" OR type="Proxy Issue") state="active"
| eval outage_start=_time
| eval outage_type=type
| stats earliest(outage_start) as outage_window_start latest(outage_start) as outage_window_end by outage_type, severity
| eval outage_window_end=outage_window_end+900
| map search="search index=_audit action=\"fired\" earliest=$outage_window_start$ latest=$outage_window_end$ | stats count as internal_alerts by search_name | eval outage_type=\"$outage_type$\"" maxsearches=5
| sort -internal_alerts
```

**How this works:**
1. Find active Internet Insights events.
2. Compute the outage time window (earliest event to latest event + 15 minutes buffer).
3. For each outage type, use `map` to search the audit index for alerts that fired in that window.
4. Return correlated alerts sorted by count.

**Simplified alternative (without map):**
```spl
`event_index` (type="Network Outage" OR type="DNS Issue" OR type="Proxy Issue") state="active" earliest=-4h
| rename type as outage_type
| append [
  search index=_audit action="fired" earliest=-4h
  | rename search_name as alert_name
  | eval outage_type="Internal Alert"
]
| timechart span=5m count by outage_type
```
This overlay approach shows internet outages and internal alerts on the same timechart, making visual correlation easy.

**Enterprise Security variant:**
```spl
`event_index` (type="Network Outage" OR type="DNS Issue") state="active" earliest=-4h
| append [
  search index=notable earliest=-4h
  | eval type="Notable Event: " + rule_name
]
| table _time, type, severity, state
| sort _time
```

**Scheduling:** This should run as an on-demand investigation search during active incidents, not as a continuously scheduled search. However, you can create a lightweight scheduled version: cron `*/15 * * * *`, range `-30m`.

### Step 3 — Validate
(a) **Backtest.** Find a historical Internet Insights event: `index=thousandeyes_events earliest=-90d | stats count by type | sort -count`. Take the timestamp range and run the correlation search against that window.

(b) **Simulate.** Create a test alert that fires every 5 minutes (e.g., `| makeresults | where 1=1`). Then check if it appears in the correlation results during any active Internet Insights event.

### Step 4 — Operationalize
**Dashboard** ("Outage Impact Analysis" — used during major incidents):
- Timeline: Internet Insights events overlaid with internal alert triggers.
- Correlation table: which internal alerts fired during outage windows.
- Summary: "During the last [Network Outage], [X] internal alerts fired, suggesting external causality."

**Runbook** (owner: incident commander / SRE lead):
1. Major incident declared. Check this dashboard FIRST.
2. If an Internet Insights event is active and correlates with internal alerts → external root cause. Communicate to stakeholders: "The issue is caused by [ISP/DNS provider] outage. Our infrastructure is healthy. We are monitoring for recovery."
3. If no Internet Insights event correlates → internal root cause. Proceed with standard incident response.
4. After resolution, document correlation findings in the post-incident review.

### Step 5 — Troubleshooting

- **`map` command errors** — Ensure the subsearch syntax is correct. `map` is sensitive to escaping. Test the inner search independently first, then wrap in `map`.

- **No results from _audit** — Check that `index=_audit` contains triggered alert records. On some Splunk deployments, audit logging may be disabled or the index name may differ.

- **Time window too wide / too narrow** — The `+900` buffer (15 minutes) may need adjustment. For fast-moving outages, reduce to `+300` (5 minutes). For slow-onset issues (like DNS propagation), increase to `+1800` (30 minutes).

- **Performance** — The `map` command runs subsearches sequentially. For large audit indexes, ensure the time range is narrow. Consider pre-summarizing internal alerts with `collect` or `summary indexing` for faster correlation.

## SPL

```spl
`event_index` (type="Network Outage" OR type="DNS Issue" OR type="Proxy Issue") state="active"
| eval outage_start=_time
| eval outage_type=type
| stats earliest(outage_start) as outage_window_start latest(outage_start) as outage_window_end by outage_type, severity
| eval outage_window_end=outage_window_end+900
| map search="search index=_audit action=\"fired\" earliest=$outage_window_start$ latest=$outage_window_end$ | stats count as internal_alerts by search_name | eval outage_type=\"$outage_type$\"" maxsearches=5
| sort -internal_alerts
```

## Visualization

(1) Timeline: ThousandEyes outage events and internal alerts overlaid on the same timeline. (2) Correlation table: outage type, severity, internal alerts that fired during the window. (3) Single value: count of correlated alerts ("X internal alerts potentially caused by internet outage"). (4) Sparkline: internal alert volume overlaid with outage event start/end.

## Known False Positives

**Coincidental timing.** An internal alert fires during an Internet Insights outage window but is completely unrelated (e.g., a disk full alert during a network outage). Use domain knowledge to filter correlations — only match internal alerts related to network, application performance, or external connectivity.

**Internal issues triggering downstream internet symptoms.** Your own misconfiguration (e.g., a firewall rule change) might cause ThousandEyes tests to fail, which could be interpreted as an internet issue. Check whether the Internet Insights event affects multiple ThousandEyes customers (true internet outage) or only your tests (your issue).

**Time zone misalignment.** Ensure both ThousandEyes events and internal alerts use the same time reference. ThousandEyes uses UTC; internal alerts use whatever timezone the Splunk search head is configured for. The `| eval` time window calculation should work in epoch seconds to avoid TZ issues.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Internet Insights — Outage detection](https://docs.thousandeyes.com/product-documentation/internet-insights)
- [Splunk search command reference — map](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Map)
