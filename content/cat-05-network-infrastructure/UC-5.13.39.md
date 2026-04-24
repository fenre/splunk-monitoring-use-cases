---
id: "5.13.39"
title: "Advisory Severity Distribution and Risk Scoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.39 · Advisory Severity Distribution and Risk Scoring

## Description

Calculates a weighted risk score based on advisory severity and affected device count, providing a prioritized view of organizational vulnerability exposure.

## Value

Raw advisory counts do not reflect actual risk. Weighting by severity provides a more accurate picture of organizational exposure for executive reporting.

## Implementation

Enable the `securityadvisory` input. Adjust `risk_weight` numbers to match your risk team’s model; optionally multiply by `affected_devices` for a population-aware score instead of `advisory_count` alone.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:securityadvisory (severity, advisoryId, deviceId).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `securityadvisory` input. Adjust `risk_weight` numbers to match your risk team’s model; optionally multiply by `affected_devices` for a population-aware score instead of `advisory_count` alone.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(advisoryId) as advisory_count dc(deviceId) as affected_devices by severity | eval risk_weight=case(severity="CRITICAL",10,severity="HIGH",7,severity="MEDIUM",4,severity="LOW",1,1==1,0) | eval weighted_risk=advisory_count*risk_weight | sort -weighted_risk
```

Understanding this SPL

**Advisory Severity Distribution and Risk Scoring** — Raw advisory counts do not reflect actual risk. Weighting by severity provides a more accurate picture of organizational exposure for executive reporting.

**Pipeline walkthrough**

• `stats` measures how many distinct advisories and devices appear for each `severity` band, summarising the exposure envelope.
• `case` maps each severity label to a numeric `risk_weight` for simple scoring.
• `weighted_risk` multiplies the breadth of unique advisories by that weight, and `sort` shows the most significant columns first (extend the formula to include `affected_devices` as needed).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Bar chart (weighted_risk by severity), table combining advisory_count, affected_devices, and weighted_risk.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(advisoryId) as advisory_count dc(deviceId) as affected_devices by severity | eval risk_weight=case(severity="CRITICAL",10,severity="HIGH",7,severity="MEDIUM",4,severity="LOW",1,1==1,0) | eval weighted_risk=advisory_count*risk_weight | sort -weighted_risk
```

## Visualization

Bar chart (weighted_risk by severity), table combining advisory_count, affected_devices, and weighted_risk.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
