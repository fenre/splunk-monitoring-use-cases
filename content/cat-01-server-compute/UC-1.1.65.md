---
id: "1.1.65"
title: "Auditd Rule Violation Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.65 · Auditd Rule Violation Detection

## Description

Auditd violations provide forensic evidence of security incidents and unauthorized system access.

## Value

Auditd violations provide forensic evidence of security incidents and unauthorized system access.

## Implementation

Configure comprehensive auditd rules covering file access, syscalls, and privilege escalation. Monitor AVC (Access Vector Cache) denials. Create alerts on violation patterns indicating potential compromise.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure comprehensive auditd rules covering file access, syscalls, and privilege escalation. Monitor AVC (Access Vector Cache) denials. Create alerts on violation patterns indicating potential compromise.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit type=AVC
| stats count by host, avc_type, comm
| where count > threshold
```

Understanding this SPL

**Auditd Rule Violation Detection** — Auditd violations provide forensic evidence of security incidents and unauthorized system access.

Documented **Data sources**: `sourcetype=linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, avc_type, comm** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > threshold` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=linux_audit type=AVC
| stats count by host, avc_type, comm
| where count > threshold
```

## Visualization

Table, Alert

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
