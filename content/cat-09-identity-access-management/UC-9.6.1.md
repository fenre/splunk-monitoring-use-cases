---
id: "9.6.1"
title: "Device Compliance Status and Policy Enforcement"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.6.1 · Device Compliance Status and Policy Enforcement

## Description

Ensures all managed devices comply with security policies and configuration standards.

## Value

Ensures all managed devices comply with security policies and configuration standards.

## Implementation

Query device compliance status from SM API. Alert on noncompliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api compliance_status=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query device compliance status from SM API. Alert on noncompliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" compliance_status=*
| stats count as total_devices,
        count(eval(compliance_status IN ("noncompliant","unknown"))) as noncompliant_count
        by os_type, compliance_reason
| eval compliance_pct=round(noncompliant_count*100/total_devices, 2)
| where noncompliant_count > 0
```

Understanding this SPL

**Device Compliance Status and Policy Enforcement** — Ensures all managed devices comply with security policies and configuration standards.

Documented **Data sources**: `sourcetype=meraki:api compliance_status=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by os_type, compliance_reason** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **compliance_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where noncompliant_count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Compliance status table; compliance percentage gauge; noncompliant device list.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" compliance_status=*
| stats count as total_devices,
        count(eval(compliance_status IN ("noncompliant","unknown"))) as noncompliant_count
        by os_type, compliance_reason
| eval compliance_pct=round(noncompliant_count*100/total_devices, 2)
| where noncompliant_count > 0
```

## Visualization

Compliance status table; compliance percentage gauge; noncompliant device list.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
