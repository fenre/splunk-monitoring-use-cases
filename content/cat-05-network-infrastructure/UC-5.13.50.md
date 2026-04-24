---
id: "5.13.50"
title: "Audit Log Completeness and Gap Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.50 · Audit Log Completeness and Gap Detection

## Description

Detects gaps or unusual drops in audit log volume that may indicate logging failure, tampering, or collection issues.

## Value

Gaps in audit logs undermine accountability and compliance. Detecting them ensures the audit trail is continuous and tamper-evident.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:audit:logs (Catalyst Center audit; continuous polling baseline for log volume per hour).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | bin _time span=1h | stats count as log_count by _time | eventstats avg(log_count) as avg_logs stdev(log_count) as stdev_logs | where log_count < (avg_logs - 2*stdev_logs) OR log_count=0 | eval gap_severity=if(log_count=0, "Complete gap", "Unusual drop") | sort _time
```

Understanding this SPL

**Audit Log Completeness and Gap Detection** — Gaps in audit logs undermine accountability and compliance. Detecting them ensures the audit trail is continuous and tamper-evident.

**Pipeline walkthrough**

• `bin _time span=1h` groups audit events into hourly buckets to measure throughput.
• `stats` counts `log_count` per bucket, then `eventstats` adds rolling mean and standard deviation of hourly counts in the result set (extend lookback in production if you need a longer seasonal baseline).
• `where` flags buckets below the mean minus two standard deviations or completely empty, catching silence or sharp drops.
• `eval gap_severity` labels complete outages versus soft dips, and `sort _time` lists gaps chronologically for incident handoff.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Time series of `log_count` with overlaid control limits, table of anomalous buckets with `gap_severity`, alert when Complete gap or persistent unusual drop.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | bin _time span=1h | stats count as log_count by _time | eventstats avg(log_count) as avg_logs stdev(log_count) as stdev_logs | where log_count < (avg_logs - 2*stdev_logs) OR log_count=0 | eval gap_severity=if(log_count=0, "Complete gap", "Unusual drop") | sort _time
```

## Visualization

Time series of `log_count` with overlaid control limits, table of anomalous buckets with `gap_severity`, alert when Complete gap or persistent unusual drop.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
