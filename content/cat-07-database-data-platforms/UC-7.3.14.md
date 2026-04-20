---
id: "7.3.14"
title: "Managed Backup Retention Compliance"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.14 · Managed Backup Retention Compliance

## Description

Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

## Value

Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

## Implementation

Ingest daily snapshot inventory from AWS/Azure/GCP APIs. Compare to RPO policy (e.g., last snapshot <25h). Alert on missing snapshot for production tier.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cloud APIs (describe-db-snapshots, backup list).
• Ensure the following data sources are available: Snapshot timestamps, backup policy metadata.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest daily snapshot inventory from AWS/Azure/GCP APIs. Compare to RPO policy (e.g., last snapshot <25h). Alert on missing snapshot for production tier.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="rds:snapshot_inventory"
| stats latest(snapshot_time) as last_snap by db_instance_identifier
| eval days_since=round((now()-strptime(last_snap,"%Y-%m-%d %H:%M:%S"))/86400)
| where days_since > 1
| table db_instance_identifier last_snap days_since
```

Understanding this SPL

**Managed Backup Retention Compliance** — Verifies automated backup snapshots exist within required retention for RDS, Azure SQL LTR, and Cloud SQL backups.

Documented **Data sources**: Snapshot timestamps, backup policy metadata. **App/TA** (typical add-on context): Cloud APIs (describe-db-snapshots, backup list). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: rds:snapshot_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="rds:snapshot_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by db_instance_identifier** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **days_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Managed Backup Retention Compliance**): table db_instance_identifier last_snap days_since


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (instances missing recent backup), Single value (non-compliant count), Calendar (snapshot coverage).

## SPL

```spl
index=cloud sourcetype="rds:snapshot_inventory"
| stats latest(snapshot_time) as last_snap by db_instance_identifier
| eval days_since=round((now()-strptime(last_snap,"%Y-%m-%d %H:%M:%S"))/86400)
| where days_since > 1
| table db_instance_identifier last_snap days_since
```

## Visualization

Table (instances missing recent backup), Single value (non-compliant count), Calendar (snapshot coverage).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
