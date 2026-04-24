---
id: "5.13.25"
title: "Top Recurring Issues (Repeat Offenders)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.25 · Top Recurring Issues (Repeat Offenders)

## Description

Identifies Catalyst Center assurance issues that recur most frequently, revealing persistent problems that need root-cause investigation rather than repeated remediation.

## Value

Recurring issues waste operations time. Identifying repeat offenders enables root-cause analysis and permanent fixes instead of repeated band-aid responses.

## Implementation

Enable the `issue` input. Tune the `occurrence_count > 5` threshold to match environment size. Consider extending the time range for monthly reporting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:issue (fields name, category, deviceId, _time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `issue` input. Tune the `occurrence_count > 5` threshold to match environment size. Consider extending the time range for monthly reporting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as occurrence_count dc(deviceId) as affected_devices earliest(_time) as first_seen latest(_time) as last_seen by name, category | where occurrence_count > 5 | eval days_active=round((last_seen-first_seen)/86400,0) | sort -occurrence_count
```

Understanding this SPL

**Top Recurring Issues (Repeat Offenders)** — Recurring issues waste operations time. Identifying repeat offenders enables root-cause analysis and permanent fixes instead of repeated band-aid responses.

**Pipeline walkthrough**

• `stats` groups issues by the human-readable `name` and `category` and measures how often each pattern appears, how many distinct `deviceId` values were impacted, and the first/last time seen in the search window.
• `where occurrence_count > 5` keeps only high-chronicity patterns; adjust the floor for your fleet size.
• `eval days_active` reports how long each issue has been present in the window in days, and the final sort shows the heaviest repeat offenders at the top.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (occurrence_count, affected_devices, days_active), bar chart of top issues by name.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as occurrence_count dc(deviceId) as affected_devices earliest(_time) as first_seen latest(_time) as last_seen by name, category | where occurrence_count > 5 | eval days_active=round((last_seen-first_seen)/86400,0) | sort -occurrence_count
```

## Visualization

Table (occurrence_count, affected_devices, days_active), bar chart of top issues by name.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
