---
id: "6.4.6"
title: "Backup Encryption and Key Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.4.6 · Backup Encryption and Key Access Audit

## Description

Backup encryption keys must be used only by authorized backup jobs. Unusual key access or decryption attempts may indicate theft or ransomware. Auditing supports compliance and incident response.

## Value

Backup encryption keys must be used only by authorized backup jobs. Unusual key access or decryption attempts may indicate theft or ransomware. Auditing supports compliance and incident response.

## Implementation

Forward backup software audit logs and cloud KMS/key vault audit logs. Extract key ID, user, and action. Alert on high volume of decrypt or key access from unexpected principal or outside backup window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Backup vendor logs, KMS/HSM audit logs.
• Ensure the following data sources are available: Backup software audit log, AWS KMS CloudTrail, Azure Key Vault audit.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward backup software audit logs and cloud KMS/key vault audit logs. Extract key ID, user, and action. Alert on high volume of decrypt or key access from unexpected principal or outside backup window.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype=backup_audit (event="key_access" OR event="decrypt")
| bin _time span=1h
| stats count by user, key_id, event, _time
| where count > 20
| sort -count
```

Understanding this SPL

**Backup Encryption and Key Access Audit** — Backup encryption keys must be used only by authorized backup jobs. Unusual key access or decryption attempts may indicate theft or ransomware. Auditing supports compliance and incident response.

Documented **Data sources**: Backup software audit log, AWS KMS CloudTrail, Azure Key Vault audit. **App/TA** (typical add-on context): Backup vendor logs, KMS/HSM audit logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup_audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype=backup_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by user, key_id, event, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, key, count), Timeline of key access, Bar chart by principal.

## SPL

```spl
index=backup sourcetype=backup_audit (event="key_access" OR event="decrypt")
| bin _time span=1h
| stats count by user, key_id, event, _time
| where count > 20
| sort -count
```

## Visualization

Table (user, key, count), Timeline of key access, Bar chart by principal.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
