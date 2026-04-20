---
id: "6.1.21"
title: "Multipath Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.21 · Multipath Failover Events

## Description

Path failovers indicate cable, SFP, HBA, or array port issues. Rapid detection limits prolonged single-path exposure and data loss risk.

## Value

Path failovers indicate cable, SFP, HBA, or array port issues. Rapid detection limits prolonged single-path exposure and data loss risk.

## Implementation

Forward multipath daemon logs from all SAN-attached hosts. Tag events for failback/failover. Alert on any path down >5m or repeated failovers per hour.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Linux `multipathd` journal, Windows MPIO events, syslog.
• Ensure the following data sources are available: `multipathd` logs, `mpathadm` status (Solaris), OS MPIO event logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward multipath daemon logs from all SAN-attached hosts. Tag events for failback/failover. Alert on any path down >5m or repeated failovers per hour.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os (sourcetype=linux_syslog OR sourcetype=syslog) (multipath OR "path failed" OR "switching path" OR mpio)
| rex "(?i)path (?<path_id>\S+).*failed|(?i)switching.*path"
| bin _time span=1h
| stats count by host, path_id, _time
| where count > 0
```

Understanding this SPL

**Multipath Failover Events** — Path failovers indicate cable, SFP, HBA, or array port issues. Rapid detection limits prolonged single-path exposure and data loss risk.

Documented **Data sources**: `multipathd` logs, `mpathadm` status (Solaris), OS MPIO event logs. **App/TA** (typical add-on context): Linux `multipathd` journal, Windows MPIO events, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_syslog, syslog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by host, path_id, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Table (host, path, count), Single value (failovers last 24h).

## SPL

```spl
index=os (sourcetype=linux_syslog OR sourcetype=syslog) (multipath OR "path failed" OR "switching path" OR mpio)
| rex "(?i)path (?<path_id>\S+).*failed|(?i)switching.*path"
| bin _time span=1h
| stats count by host, path_id, _time
| where count > 0
```

## Visualization

Timeline (failover events), Table (host, path, count), Single value (failovers last 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
