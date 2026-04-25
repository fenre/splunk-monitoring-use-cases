<!-- AUTO-GENERATED from UC-2.6.24.json — DO NOT EDIT -->

---
id: "2.6.24"
title: "Citrix Site Delivery Group Capacity and Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.24 · Citrix Site Delivery Group Capacity and Health

## Description

uberAgent's Citrix Site Monitoring queries the Broker Service directly to provide real-time visibility into delivery group capacity — total machines, registered machines, active sessions, load index, and machines in maintenance mode. When available capacity drops below a threshold, new user connections may fail or be delayed.

## Value

uberAgent's Citrix Site Monitoring queries the Broker Service directly to provide real-time visibility into delivery group capacity — total machines, registered machines, active sessions, load index, and machines in maintenance mode. When available capacity drops below a threshold, new user connections may fail or be delayed.

## Implementation

Enable uberAgent's Citrix Site Monitoring feature, which queries the Citrix Broker Service at configurable intervals. Alert when available capacity drops below 20% of total machines for any delivery group. Track session density trends for capacity planning. Correlate with VDA registration health (UC-2.6.4) for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) with Citrix Site Monitoring enabled.
• Ensure the following data sources are available: `sourcetype="uberAgent:Citrix:DesktopGroups"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable uberAgent's Citrix Site Monitoring feature, which queries the Citrix Broker Service at configurable intervals. Alert when available capacity drops below 20% of total machines for any delivery group. Track session density trends for capacity planning. Correlate with VDA registration health (UC-2.6.4) for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Citrix:DesktopGroups"
| stats latest(MachinesTotal) as total, latest(MachinesRegistered) as registered, latest(SessionsActive) as active, latest(MachinesInMaintenanceMode) as maint by DeliveryGroupName
| eval available=registered-active-maint, avail_pct=round(available/total*100,1)
| where avail_pct < 20 OR registered < total*0.8
| table DeliveryGroupName, total, registered, maint, active, available, avail_pct
| sort avail_pct
```

Understanding this SPL

**Citrix Site Delivery Group Capacity and Health** — uberAgent's Citrix Site Monitoring queries the Broker Service directly to provide real-time visibility into delivery group capacity — total machines, registered machines, active sessions, load index, and machines in maintenance mode. When available capacity drops below a threshold, new user connections may fail or be delayed.

Documented **Data sources**: `sourcetype="uberAgent:Citrix:DesktopGroups"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) with Citrix Site Monitoring enabled. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Citrix:DesktopGroups. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Citrix:DesktopGroups". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by DeliveryGroupName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **available** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avail_pct < 20 OR registered < total*0.8` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Site Delivery Group Capacity and Health**): table DeliveryGroupName, total, registered, maint, active, available, avail_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (delivery group capacity), Gauge (available capacity %), Bar chart (session counts by group).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Citrix:DesktopGroups"
| stats latest(MachinesTotal) as total, latest(MachinesRegistered) as registered, latest(SessionsActive) as active, latest(MachinesInMaintenanceMode) as maint by DeliveryGroupName
| eval available=registered-active-maint, avail_pct=round(available/total*100,1)
| where avail_pct < 20 OR registered < total*0.8
| table DeliveryGroupName, total, registered, maint, active, available, avail_pct
| sort avail_pct
```

## Visualization

Table (delivery group capacity), Gauge (available capacity %), Bar chart (session counts by group).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
