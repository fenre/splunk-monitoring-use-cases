<!-- AUTO-GENERATED from UC-6.3.6.json — DO NOT EDIT -->

---
id: "6.3.6"
title: "Backup SLA Compliance"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.6 · Backup SLA Compliance

## Description

Consolidated view of backup coverage and RPO/RTO compliance. Essential for management reporting and audit evidence.

## Value

Consolidated view of backup coverage and RPO/RTO compliance. Essential for management reporting and audit evidence.

## Implementation

Cross-reference CMDB inventory with backup job data. Identify systems with no backup coverage. Calculate RPO compliance (time since last successful backup vs required RPO). Produce weekly executive report.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Combined backup data + CMDB lookup.
• Ensure the following data sources are available: Backup job logs, CMDB/asset inventory.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Cross-reference CMDB inventory with backup job data. Identify systems with no backup coverage. Calculate RPO compliance (time since last successful backup vs required RPO). Produce weekly executive report.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup cmdb_systems.csv WHERE requires_backup="yes"
| join type=left max=1 system_name
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_backup, max(data_size) as backup_size by system_name]
| eval compliant=if(isnotnull(last_backup),"Yes","No")
| stats count(eval(compliant="Yes")) as covered, count as total
| eval coverage_pct=round(covered/total*100,1)
```

Understanding this SPL

**Backup SLA Compliance** — Consolidated view of backup coverage and RPO/RTO compliance. Essential for management reporting and audit evidence.

Documented **Data sources**: Backup job logs, CMDB/asset inventory. **App/TA** (typical add-on context): Combined backup data + CMDB lookup. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **coverage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Compare job session state, duration, and transferred bytes with Veeam Backup & Replication or Veeam Enterprise Manager for the same job and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Single value (SLA compliance %), Table (non-compliant systems), Pie chart (covered vs uncovered), Dashboard with filters by business unit.

## SPL

```spl
| inputlookup cmdb_systems.csv WHERE requires_backup="yes"
| join type=left max=1 system_name
    [search index=backup sourcetype="veeam:job" status="Success" earliest=-7d
     | stats latest(_time) as last_backup, max(data_size) as backup_size by system_name]
| eval compliant=if(isnotnull(last_backup),"Yes","No")
| stats count(eval(compliant="Yes")) as covered, count as total
| eval coverage_pct=round(covered/total*100,1)
```

## Visualization

Single value (SLA compliance %), Table (non-compliant systems), Pie chart (covered vs uncovered), Dashboard with filters by business unit.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
