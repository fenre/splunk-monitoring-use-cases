<!-- AUTO-GENERATED from UC-1.2.52.json — DO NOT EDIT -->

---
id: "1.2.52"
title: "NIC Teaming / LBFO Failover (Windows)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.52 · NIC Teaming / LBFO Failover (Windows)

## Description

NIC team member failures reduce redundancy silently. A second failure causes full network loss. Detecting the first failure enables proactive repair.

## Value

App HA depends on the network under it—if the team is down and you do not know, your cluster quorum story is shaky on paper only.

## Implementation

NIC Teaming (LBFO) events log automatically. EventCode 101=team degraded (member lost), 105=member disconnected, 106=reconnected, 115=standby activated. Alert immediately when team degrades — the remaining NIC is now a single point of failure. Track flapping (repeated 105→106 cycles) which indicates cable, switch port, or driver issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-NlbFo/Operational` (EventCode 101, 105, 106, 115).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
NIC Teaming (LBFO) events log automatically. EventCode 101=team degraded (member lost), 105=member disconnected, 106=reconnected, 115=standby activated. Alert immediately when team degrades — the remaining NIC is now a single point of failure. Track flapping (repeated 105→106 cycles) which indicates cable, switch port, or driver issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NlbFo/Operational"
  EventCode IN (101, 105, 106, 115)
| eval event=case(EventCode=101,"Team degraded",EventCode=105,"Member disconnected",EventCode=106,"Member reconnected",EventCode=115,"Standby activated")
| table _time, host, event, TeamName, MemberName
| sort -_time
```

Understanding this SPL

**NIC Teaming / LBFO Failover (Windows)** — NIC team member failures reduce redundancy silently. A second failure causes full network loss. Detecting the first failure enables proactive repair.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-NlbFo/Operational` (EventCode 101, 105, 106, 115). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **event** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **NIC Teaming / LBFO Failover (Windows)**): table _time, host, event, TeamName, MemberName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (team × member status), Timeline (failover events), Single value (degraded teams).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NlbFo/Operational"
  EventCode IN (101, 105, 106, 115)
| eval event=case(EventCode=101,"Team degraded",EventCode=105,"Member disconnected",EventCode=106,"Member reconnected",EventCode=115,"Standby activated")
| table _time, host, event, TeamName, MemberName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action span=1h
| where count>0
```

## Visualization

Status grid (team × member status), Timeline (failover events), Single value (degraded teams).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
