<!-- AUTO-GENERATED from UC-5.9.54.json — DO NOT EDIT -->

---
id: "5.9.54"
title: "MTTR Reduction via Network Fault Isolation"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.54 · MTTR Reduction via Network Fault Isolation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*When the network breaks, we immediately figure out whether it's our problem or the internet's problem, and exactly which piece of equipment is causing the trouble, so the team can fix things in minutes instead of spending hours trying to find the problem.*

---

## Description

Combines all four ThousandEyes data sources — metrics, path visualization, events, and alerts — into a fault isolation workflow that determines whether a network issue is internal or external, identifies the specific hop or provider responsible, and reduces Mean Time To Resolution (MTTR) by eliminating the investigation phase.

## Value

The biggest time sink in network incident response isn't fixing the problem — it's finding the problem. A typical network incident lifecycle looks like: Alert (0 min) → Acknowledge (5 min) → Start investigating (10 min) → Check internal network (30 min) → Check application (45 min) → Realize it's an ISP issue (60 min) → Open ISP ticket (65 min) → Wait for ISP (???). This UC compresses the first 60 minutes into 60 seconds by automatically correlating ThousandEyes alerts with Internet Insights events (external?) and path visualization (which hop?). If ThousandEyes shows an Internet Insights Network Outage event at the same time as the alert, the fault is external — skip internal investigation, open the ISP ticket immediately. If no Internet Insights event exists but path visualization shows packet loss starting at a specific router hop, the fault is internal — escalate to the team that owns that router. The result is MTTR reduction from hours to minutes.

## Implementation

Aggregates data from all four ThousandEyes indexes using a multi-search correlation approach. The search starts with active critical alerts, enriches with current metrics, checks for corresponding Internet Insights events, and classifies the fault domain.

## Detailed Implementation

### Prerequisites
- **All four ThousandEyes data inputs configured:**
  - Metrics Stream (HEC push) → `index=thousandeyes_metrics`
  - Alerts Stream (HEC webhook) → `index=thousandeyes_alerts`
  - Events input (API polling) → `index=thousandeyes_events`
  - Path Visualization input (API polling) → `index=thousandeyes_pathvis`
- This is the capstone UC — it builds on UC-5.9.1 (metrics), UC-5.9.5 (path visualization), UC-5.9.18 (events), and UC-5.9.19 (alerts).

### Step 1 — Build the fault isolation search
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" state="active" severity="critical"
| stats earliest(_time) as alert_start by alert.rule.name, alert.test.name
| join type=left alert.test.name [
    search `stream_index` thousandeyes.test.type="agent-to-server"
    | stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss by thousandeyes.test.name
    | rename thousandeyes.test.name as alert.test.name
]
| join type=left alert.test.name [
    search `event_index` (type="Network Outage" OR type="DNS Issue" OR type="Proxy Issue") state="active"
    | stats count as external_events values(type) as external_event_types by thousandeyes.test.name
    | rename thousandeyes.test.name as alert.test.name
]
| eval fault_domain=if(external_events > 0, "External (ISP/Internet)", "Internal (Network/App)")
| eval avg_latency_ms=round(avg_latency*1000,1)
| table alert.rule.name, alert.test.name, alert_start, avg_latency_ms, avg_loss, external_events, external_event_types, fault_domain
| sort -avg_loss
```

### Step 2 — Add path-level drill-down
For incidents classified as Internal, add a drill-down search that identifies the specific hop where packet loss begins:
```spl
`path_viz_index` thousandeyes.test.name="$alert.test.name$" earliest=-1h
| sort _time
| stats avg(hop_latency) as avg_hop_latency avg(hop_loss) as avg_hop_loss by hop_number, hop_ip, hop_prefix
| eval degraded=if(avg_hop_loss > 1 OR avg_hop_latency > 100, "YES", "no")
| sort hop_number
```
This pinpoints the exact network hop where degradation begins, which maps to a specific router, ISP, or peering point.

### Step 3 — Measure MTTR
Track alert lifecycle to measure MTTR:
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-30d
| stats earliest(_time) as alert_start latest(_time) as alert_end by alert.rule.name, alert.test.name, severity
| eval mttr_min=round((alert_end - alert_start) / 60, 0)
| stats avg(mttr_min) as avg_mttr_min p50(mttr_min) as p50_mttr p95(mttr_min) as p95_mttr by severity
| eval avg_mttr_h=round(avg_mttr_min/60,1)
```

### Step 4 — Operationalize
**Triage runbook (automated in dashboard):**

1. **Alert fires** → search runs automatically.
2. **Check fault_domain:**
   - External → Open ISP ticket. Link Internet Insights event. Wait for resolution. No internal escalation needed.
   - Internal → Continue investigation.
3. **For Internal faults → Check path visualization:**
   - Degradation starts at hop N → Identify the owner of that hop (internal router, peering, transit).
   - No path data available → Wait 10 minutes for API poll cycle, or investigate using metrics only.
4. **Escalate with evidence:**
   - Internal router → Network team with hop IP, latency, loss data.
   - Transit/peering → ISP with path trace evidence.
   - Application → App team with HTTP metrics showing server processing is the bottleneck (UC-5.9.52).

**Dashboard design:** Build as a triage dashboard with three panels:
- Top: Active critical alerts with fault domain classification.
- Middle: Path visualization drill-down for selected alert.
- Bottom: MTTR trending over 30 days.

### Step 5 — Troubleshooting
- **Fault domain always shows Internal** — Verify the Events input is configured and polling. Check `index=thousandeyes_events | stats count` for recent data.
- **Path visualization data missing** — Path viz is polled, not streamed. Verify the path visualization input is enabled and the OAuth token has access.
- **Join returns incomplete results** — Test names in alerts (`alert.test.name`) must exactly match test names in metrics (`thousandeyes.test.name`). Verify with `| stats dc(alert.test.name)` vs `| stats dc(thousandeyes.test.name)`.
- **MTTR appears artificially long** — Some alerts remain in `active` state if the ThousandEyes alert rule uses a high clearing threshold. Check ThousandEyes alert rule configuration.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" state="active" severity="critical"
| stats earliest(_time) as alert_start by alert.rule.name, alert.test.name
| join type=left alert.test.name [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss by thousandeyes.test.name | rename thousandeyes.test.name as alert.test.name]
| join type=left alert.test.name [search `event_index` (type="Network Outage" OR type="DNS Issue") state="active" | stats count as external_events by thousandeyes.test.name | rename thousandeyes.test.name as alert.test.name]
| eval fault_domain=if(external_events > 0, "External (ISP/Internet)", "Internal (Network/App)")
| eval avg_latency_ms=round(avg_latency*1000,1)
| table alert.rule.name, alert.test.name, alert_start, avg_latency_ms, avg_loss, external_events, fault_domain
| sort -avg_loss
```

## Visualization

(1) Fault domain classification: pie chart of Internal vs External faults. (2) Active incident table with fault domain, impacted tests, and metrics. (3) MTTR trend: timechart showing alert-to-resolution time over weeks. (4) Triage decision tree as a dashboard note.

## Known False Positives

**Fault domain misclassification.** An internal network issue (e.g., a misconfigured firewall) may not generate an Internet Insights event but may also not show clearly in path visualization if the affected hop doesn't respond to ICMP. The absence of an external event doesn't definitively prove an internal fault.

**Partial outages.** An ISP issue affecting only some agents may not trigger an Internet Insights event (which requires a threshold of affected vantage points). The fault domain may classify as Internal when it's actually a localized external issue.

**Stale path visualization data.** Path visualization data is polled via API, not pushed in real-time. During the first minutes of an incident, path data may not yet reflect the current state. Wait at least 10 minutes before relying on path data for fault isolation.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Internet Insights](https://docs.thousandeyes.com/product-documentation/internet-insights)
- [ThousandEyes path visualization](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/)
