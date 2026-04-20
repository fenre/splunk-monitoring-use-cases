---
id: "6.3.13"
title: "Backup RPO and RTO Compliance"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.13 · Backup RPO and RTO Compliance

## Description

Compares actual backup completion time and restore test duration against business RPO/RTO targets per application tier.

## Value

Compares actual backup completion time and restore test duration against business RPO/RTO targets per application tier.

## Implementation

Maintain lookup of RPO hours per tier. Join to last successful backup. Alert when hours_since_ok exceeds RPO. Add parallel search for restore drill duration vs RTO.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup TA + CMDB lookup.
• Ensure the following data sources are available: Last successful backup time, last restore test duration.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain lookup of RPO hours per tier. Join to last successful backup. Alert when hours_since_ok exceeds RPO. Add parallel search for restore drill duration vs RTO.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup cmdb_systems.csv WHERE backup_tier=*
| join system_name max=0
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_ok by system_name]
| eval hours_since_ok=round((now()-last_ok)/3600,1)
| lookup backup_rpo_hours tier OUTPUT rpo_hours
| where hours_since_ok > rpo_hours
| table system_name tier hours_since_ok rpo_hours
```

Understanding this SPL

**Backup RPO and RTO Compliance** — Compares actual backup completion time and restore test duration against business RPO/RTO targets per application tier.

Documented **Data sources**: Last successful backup time, last restore test duration. **App/TA** (typical add-on context): Backup TA + CMDB lookup. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **hours_since_ok** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where hours_since_ok > rpo_hours` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup RPO and RTO Compliance**): table system_name tier hours_since_ok rpo_hours


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (systems breaching RPO), Gauge (% RPO compliant), Line chart (hours since backup by tier).

## SPL

```spl
| inputlookup cmdb_systems.csv WHERE backup_tier=*
| join system_name max=0
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_ok by system_name]
| eval hours_since_ok=round((now()-last_ok)/3600,1)
| lookup backup_rpo_hours tier OUTPUT rpo_hours
| where hours_since_ok > rpo_hours
| table system_name tier hours_since_ok rpo_hours
```

## Visualization

Table (systems breaching RPO), Gauge (% RPO compliant), Line chart (hours since backup by tier).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
