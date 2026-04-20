---
id: "6.3.23"
title: "Immutable Backup and Ransomware Recovery Readiness"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.3.23 · Immutable Backup and Ransomware Recovery Readiness

## Description

Immutable or air-gapped copies are the last line of defense against ransomware. Verifying immutability and recovery procedure readiness ensures backups cannot be deleted or encrypted by an attacker.

## Value

Immutable or air-gapped copies are the last line of defense against ransomware. Verifying immutability and recovery procedure readiness ensures backups cannot be deleted or encrypted by an attacker.

## Implementation

Poll backup copy configuration for retention lock or immutable flag. Optionally run periodic checksum or catalog validation. Alert when any critical copy is not immutable or when last verification is older than 7 days. Document and test recovery runbook.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup vendor API, object lock compliance check.
• Ensure the following data sources are available: Backup copy retention lock status, object lock (S3), backup integrity checksum.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll backup copy configuration for retention lock or immutable flag. Optionally run periodic checksum or catalog validation. Alert when any critical copy is not immutable or when last verification is older than 7 days. Document and test recovery runbook.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype=backup_immutable
| stats latest(immutable_ok) as ok, latest(last_checksum_verify) as last_verify by copy_name
| where ok != 1 OR (now()-last_verify) > 604800
| table copy_name ok last_verify
```

Understanding this SPL

**Immutable Backup and Ransomware Recovery Readiness** — Immutable or air-gapped copies are the last line of defense against ransomware. Verifying immutability and recovery procedure readiness ensures backups cannot be deleted or encrypted by an attacker.

Documented **Data sources**: Backup copy retention lock status, object lock (S3), backup integrity checksum. **App/TA** (typical add-on context): Backup vendor API, object lock compliance check. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup_immutable. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype=backup_immutable. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by copy_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ok != 1 OR (now()-last_verify) > 604800` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Immutable Backup and Ransomware Recovery Readiness**): table copy_name ok last_verify


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (copy, immutable, last verify), Table (non-compliant copies), Single value (ready for recovery %).

## SPL

```spl
index=backup sourcetype=backup_immutable
| stats latest(immutable_ok) as ok, latest(last_checksum_verify) as last_verify by copy_name
| where ok != 1 OR (now()-last_verify) > 604800
| table copy_name ok last_verify
```

## Visualization

Status grid (copy, immutable, last verify), Table (non-compliant copies), Single value (ready for recovery %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
