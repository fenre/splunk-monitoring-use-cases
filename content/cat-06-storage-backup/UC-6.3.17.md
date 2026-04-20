---
id: "6.3.17"
title: "Incremental Backup Chain Integrity"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.17 · Incremental Backup Chain Integrity

## Description

Broken increment chains (missing full or corrupted metadata) make restores impossible. Vendor-specific checks detect chain gaps before a failure at restore time.

## Value

Broken increment chains (missing full or corrupted metadata) make restores impossible. Vendor-specific checks detect chain gaps before a failure at restore time.

## Implementation

Ingest synthetic full verification or chain validation jobs. Alert on any `chain_ok=0`. Weekly full verification of random samples for large environments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Veeam/Commvault verification APIs, catalog exports.
• Ensure the following data sources are available: Backup chain metadata, `Verify` job results.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest synthetic full verification or chain validation jobs. Alert on any `chain_ok=0`. Weekly full verification of random samples for large environments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="backup:chain_verify"
| where chain_ok=0 OR missing_restore_point=1 OR verify_status="Failed"
| stats latest(_time) as last_check by job_name, vm_name
| table job_name vm_name chain_ok missing_restore_point verify_status last_check
```

Understanding this SPL

**Incremental Backup Chain Integrity** — Broken increment chains (missing full or corrupted metadata) make restores impossible. Vendor-specific checks detect chain gaps before a failure at restore time.

Documented **Data sources**: Backup chain metadata, `Verify` job results. **App/TA** (typical add-on context): Veeam/Commvault verification APIs, catalog exports. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: backup:chain_verify. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="backup:chain_verify". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where chain_ok=0 OR missing_restore_point=1 OR verify_status="Failed"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by job_name, vm_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Incremental Backup Chain Integrity**): table job_name vm_name chain_ok missing_restore_point verify_status last_check


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (broken chains), Single value (VMs with integrity issues), Timeline (verify jobs).

## SPL

```spl
index=backup sourcetype="backup:chain_verify"
| where chain_ok=0 OR missing_restore_point=1 OR verify_status="Failed"
| stats latest(_time) as last_check by job_name, vm_name
| table job_name vm_name chain_ok missing_restore_point verify_status last_check
```

## Visualization

Table (broken chains), Single value (VMs with integrity issues), Timeline (verify jobs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
