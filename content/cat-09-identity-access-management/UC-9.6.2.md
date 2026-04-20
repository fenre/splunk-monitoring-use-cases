---
id: "9.6.2"
title: "Mobile Device Enrollment and MDM Status Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.6.2 · Mobile Device Enrollment and MDM Status Tracking

## Description

Tracks device enrollment status to ensure mobile device management coverage.

## Value

Tracks device enrollment status to ensure mobile device management coverage.

## Implementation

Query device enrollment status. Track pending and failed enrollments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api enrollment_status=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query device enrollment status. Track pending and failed enrollments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" enrollment_status IN ("enrolled", "pending", "failed")
| stats count as device_count by enrollment_status, os_type
| eval enrollment_pct=round(count*100/sum(count), 2)
```

Understanding this SPL

**Mobile Device Enrollment and MDM Status Tracking** — Tracks device enrollment status to ensure mobile device management coverage.

Documented **Data sources**: `sourcetype=meraki:api enrollment_status=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by enrollment_status, os_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **enrollment_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Enrollment status pie chart; pending enrollment timeline; device count by OS.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" enrollment_status IN ("enrolled", "pending", "failed")
| stats count as device_count by enrollment_status, os_type
| eval enrollment_pct=round(count*100/sum(count), 2)
```

## Visualization

Enrollment status pie chart; pending enrollment timeline; device count by OS.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
