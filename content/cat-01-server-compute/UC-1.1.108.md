<!-- AUTO-GENERATED from UC-1.1.108.json — DO NOT EDIT -->

---
id: "1.1.108"
title: "Password Policy Violation Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.108 · Password Policy Violation Detection

## Description

Password policy violations indicate accounts with weak credentials vulnerable to compromise.

## Value

Password policy violations indicate accounts with weak credentials vulnerable to compromise.

## Implementation

Periodically scan /etc/shadow for passwords that violate policy (too simple, too old, etc.) via custom scripts. Create alerts for violations. Include remediation instructions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=linux_audit, /etc/shadow audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically scan /etc/shadow for passwords that violate policy (too simple, too old, etc.) via custom scripts. Create alerts for violations. Include remediation instructions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_audit path="/etc/shadow"
| stats count by host, user
| eval policy_violation="yes"
```

Understanding this SPL

**Password Policy Violation Detection** — Password policy violations indicate accounts with weak credentials vulnerable to compromise.

Documented **Data sources**: `sourcetype=linux_audit, /etc/shadow audit`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_audit. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, user** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **policy_violation** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

## SPL

```spl
index=os sourcetype=linux_audit path="/etc/shadow"
| stats count by host, user
| eval policy_violation="yes"
```

## Visualization

Table, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
