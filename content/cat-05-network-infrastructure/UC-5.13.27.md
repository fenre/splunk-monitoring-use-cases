---
id: "5.13.27"
title: "Issue Volume Anomaly Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.27 · Issue Volume Anomaly Detection

## Description

Detects statistically unusual spikes in assurance issue volume that may indicate a network event, failed change, or emerging attack.

## Value

A sudden surge in issues often correlates with a failed change, configuration push, or emerging infrastructure problem. Anomaly detection catches these faster than fixed thresholds.

## Implementation

Enable the `issue` input. Run over a time window with enough 4h buckets to estimate a stable baseline; tune the `2*stdev` multiplier for sensitivity. Use alongside change calendars for triage context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:issue.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `issue` input. Run over a time window with enough 4h buckets to estimate a stable baseline; tune the `2*stdev` multiplier for sensitivity. Use alongside change calendars for triage context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:issue" | bin _time span=4h | stats count as issue_count by _time | eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues | where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0 | eval deviation=round((issue_count-baseline)/stdev_issues,1) | sort -deviation
```

Understanding this SPL

**Issue Volume Anomaly Detection** — A sudden surge in issues often correlates with a failed change, configuration push, or emerging infrastructure problem. Anomaly detection catches these faster than fixed thresholds.

**Pipeline walkthrough**

• `bin _time` aligns events to four-hour windows consistent with the trending use case for comparable cadence.
• `stats` counts issues per time bucket, then `eventstats` adds fleet-wide mean and standard deviation of those counts across the window.
• The `where` clause keeps buckets more than two standard deviations above the mean (with nonzero spread), and `deviation` quantifies how extreme each spike is.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Timechart of issue_count with reference lines, table of anomalous buckets with deviation score.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | bin _time span=4h | stats count as issue_count by _time | eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues | where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0 | eval deviation=round((issue_count-baseline)/stdev_issues,1) | sort -deviation
```

## Visualization

Timechart of issue_count with reference lines, table of anomalous buckets with deviation score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
