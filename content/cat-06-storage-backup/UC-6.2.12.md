---
id: "6.2.12"
title: "Object Lock Integrity"
criticality: "critical"
splunkPillar: "Security"
---

# UC-6.2.12 · Object Lock Integrity

## Description

WORM/immutability protects against ransomware and deletion. Verifies Object Lock retention mode and legal hold on regulated buckets.

## Value

WORM/immutability protects against ransomware and deletion. Verifies Object Lock retention mode and legal hold on regulated buckets.

## Implementation

Scripted audit comparing required lock settings from lookup to actual API responses. Alert on drift or disabled lock. Log tamper-evident checksum of policy JSON if stored in Splunk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: AWS Config, S3 API inventory.
• Ensure the following data sources are available: `GetObjectLockConfiguration`, Config compliance, S3 Inventory `ObjectLockEnabled`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted audit comparing required lock settings from lookup to actual API responses. Alert on drift or disabled lock. Log tamper-evident checksum of policy JSON if stored in Splunk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:s3:object_lock_audit"
| where object_lock_enabled!=1 OR retention_mode="null" OR compliance_gap=1
| stats latest(_time) as last_check by bucket_name, region
| table bucket_name region object_lock_enabled retention_mode compliance_gap
```

Understanding this SPL

**Object Lock Integrity** — WORM/immutability protects against ransomware and deletion. Verifies Object Lock retention mode and legal hold on regulated buckets.

Documented **Data sources**: `GetObjectLockConfiguration`, Config compliance, S3 Inventory `ObjectLockEnabled`. **App/TA** (typical add-on context): AWS Config, S3 API inventory. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:s3:object_lock_audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:s3:object_lock_audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where object_lock_enabled!=1 OR retention_mode="null" OR compliance_gap=1` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by bucket_name, region** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Object Lock Integrity**): table bucket_name region object_lock_enabled retention_mode compliance_gap


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (buckets failing lock check), Single value (drift count), Timeline (audit runs).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=aws sourcetype="aws:s3:object_lock_audit"
| where object_lock_enabled!=1 OR retention_mode="null" OR compliance_gap=1
| stats latest(_time) as last_check by bucket_name, region
| table bucket_name region object_lock_enabled retention_mode compliance_gap
```

## Visualization

Table (buckets failing lock check), Single value (drift count), Timeline (audit runs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
