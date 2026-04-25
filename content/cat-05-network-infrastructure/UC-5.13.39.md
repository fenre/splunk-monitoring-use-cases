<!-- AUTO-GENERATED from UC-5.13.39.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on (7538) with `cisco:dnac:securityadvisory` in `index=catalyst`.
• Agree on numeric weights (the sample uses 10/7/4/1 for CRITICAL/HIGH/MEDIUM/LOW) with risk or security leadership before the chart is used in executive reporting. Adjust the `case()` table if Cisco adds new severity labels—include a final default and monitor for UNKNOWN.
• `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Same `securityadvisory` input and polling cadence as in `UC-5.13.34`. For very small sites, use a 7d window so `dc(advisoryId)` is not always 1 in every band.

Step 2 — Weighted risk roll-up
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(advisoryId) as advisory_count dc(deviceId) as affected_devices by severity | eval risk_weight=case(severity="CRITICAL",10,severity="HIGH",7,severity="MEDIUM",4,severity="LOW",1,1==1,0) | eval weighted_risk=advisory_count*risk_weight | sort -weighted_risk
```

Understanding this SPL (portfolio, not per-CVE CVSS)
**Advisory Severity & Risk** — `weighted_risk` multiplies distinct advisory count by a severity weight. A v2 for leadership might incorporate `affected_devices` (for example `advisory_count * risk_weight * log(affected_devices+1)`) so population impact matters.

**Pipeline walkthrough**
• `stats` of distinct `advisoryId` and `deviceId` per `severity` → `risk_weight` from `case` → product → `sort` descending.

Step 3 — Validate
• Compare counts per `severity` to the Catalyst or Cisco PSIRT portfolio view; explain any mismatch where Splunk’s `dc(advisoryId)` counts distinct IDs that map to a smaller number of public bulletins.

Step 4 — Operationalize
• Export the table to quarterly GRC; trend `weighted_risk` from a summary index if you need month-over-month KPI without rescanning raw events.

Step 5 — Troubleshooting
• Zero rows: no advisories in the window or index scope wrong—`tstats count` the sourcetype.
• Weights that feel misleading: re-tune the `case` table, or add `affected_devices` into the `eval` as above.
• After upgrades, confirm `severity` strings have not changed (new enum values need new `case` arms).


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(advisoryId) as advisory_count dc(deviceId) as affected_devices by severity | eval risk_weight=case(severity="CRITICAL",10,severity="HIGH",7,severity="MEDIUM",4,severity="LOW",1,1==1,0) | eval weighted_risk=advisory_count*risk_weight | sort -weighted_risk
```

## Visualization

Bar chart (weighted_risk by severity), table combining advisory_count, affected_devices, and weighted_risk.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
