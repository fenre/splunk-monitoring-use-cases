---
id: "5.13.30"
title: "Compliance Status Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.30 · Compliance Status Trending

## Description

Tracks compliance status over time to measure remediation progress, detect compliance drift, and demonstrate continuous compliance for auditors.

## Value

Auditors want to see continuous compliance, not point-in-time snapshots. Trending demonstrates that compliance is maintained and that violations are remediated promptly.

## Implementation

Enable the `compliance` input. Use a 30-90d window for the timechart. If divisor is zero, handle nulls in a wrapper query or add a guard eval for empty days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:compliance (complianceStatus over time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `compliance` input. Use a 30-90d window for the timechart. If divisor is zero, handle nulls in a wrapper query or add a guard eval for empty days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant | eval compliance_pct=round(compliant*100/(compliant+non_compliant),1)
```

Understanding this SPL

**Compliance Status Trending** — Auditors want to see continuous compliance, not point-in-time snapshots. Trending demonstrates that compliance is maintained and that violations are remediated promptly.

**Pipeline walkthrough**

• Baselines the compliance feed and buckets events daily.
• `timechart` counts how many results per day were `COMPLIANT` vs `NON_COMPLIANT` using `eval` inside `count()`.
• `compliance_pct` approximates the proportion of checks passing each day, suitable for a rolling executive KPI.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Stacked area (compliant vs non_compliant), line chart of compliance_pct, annotations for change freezes.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant | eval compliance_pct=round(compliant*100/(compliant+non_compliant),1)
```

## Visualization

Stacked area (compliant vs non_compliant), line chart of compliance_pct, annotations for change freezes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
