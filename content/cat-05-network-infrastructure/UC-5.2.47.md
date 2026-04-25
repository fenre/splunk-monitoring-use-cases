<!-- AUTO-GENERATED from UC-5.2.47.json — DO NOT EDIT -->

---
id: "5.2.47"
title: "Check Point ClusterXL Failover Events (Check Point)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.47 · Check Point ClusterXL Failover Events (Check Point)

## Description

ClusterXL provides gateway high availability via active-standby or active-active clusters. Failover events — whether planned (manual switchover) or unplanned (process crash, NIC failure, sync timeout) — cause brief traffic interruption and may indicate underlying hardware or software instability. Monitoring failover frequency, duration, and trigger reason supports SLA reporting and proactive hardware replacement before repeated failovers degrade user experience.

## Value

ClusterXL provides gateway high availability via active-standby or active-active clusters. Failover events — whether planned (manual switchover) or unplanned (process crash, NIC failure, sync timeout) — cause brief traffic interruption and may indicate underlying hardware or software instability. Monitoring failover frequency, duration, and trigger reason supports SLA reporting and proactive hardware replacement before repeated failovers degrade user experience.

## Implementation

Forward Check Point system/cluster logs via Log Exporter or Smart-1 Cloud. Extract ClusterXL state change messages (member down, sync lost, failover). Alert on any unplanned failover immediately. Track failover frequency per cluster — more than 2 in 7 days warrants investigation. Correlate with gateway CPU/memory UC-10.11.35 to find resource-triggered failovers. Page on-call for active-active cluster degradation to single member.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (cluster/system logs), SNMP traps.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Check Point system/cluster logs via Log Exporter or Smart-1 Cloud. Extract ClusterXL state change messages (member down, sync lost, failover). Alert on any unplanned failover immediately. Track failover frequency per cluster — more than 2 in 7 days warrants investigation. Correlate with gateway CPU/memory UC-10.11.35 to find resource-triggered failovers. Page on-call for active-active cluster degradation to single member.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)cluster|clusterxl|ha") OR match(lower(logdesc),"(?i)failover|switchover|member.*down|sync.*fail")
| eval gw=coalesce(orig, src, hostname)
| stats count earliest(_time) as first latest(_time) as last values(logdesc) as events by gw
| sort -count
```

Understanding this SPL

**Check Point ClusterXL Failover Events (Check Point)** — ClusterXL provides gateway high availability via active-standby or active-active clusters. Failover events — whether planned (manual switchover) or unplanned (process crash, NIC failure, sync timeout) — cause brief traffic interruption and may indicate underlying hardware or software instability. Monitoring failover frequency, duration, and trigger reason supports SLA reporting and proactive hardware replacement before repeated failovers degrade user experience.

Documented **Data sources**: `sourcetype=cp_log` (cluster/system logs), SNMP traps. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)cluster|clusterxl|ha") OR match(lower(logdesc),"(?i)failover|switchover|member.*down|sync.*…` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gw** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by gw** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare key fields and timestamps in SmartConsole, SmartView, or the gateway’s local view so Splunk and Check Point match for the same events.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Table (clusters with recent failovers), Single value (failovers this week), Bar chart (failovers by reason).

## SPL

```spl
index=firewall sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)cluster|clusterxl|ha") OR match(lower(logdesc),"(?i)failover|switchover|member.*down|sync.*fail")
| eval gw=coalesce(orig, src, hostname)
| stats count earliest(_time) as first latest(_time) as last values(logdesc) as events by gw
| sort -count
```

## Visualization

Timeline (failover events), Table (clusters with recent failovers), Single value (failovers this week), Bar chart (failovers by reason).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
