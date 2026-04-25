<!-- AUTO-GENERATED from UC-5.13.50.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on (7538) with the **audit_logs** input and sourcetype `cisco:dnac:audit:logs` in `index=catalyst` (Intent `GET /dna/intent/api/v1/audit/logs`, typically 300s poll).
• `eventstats` `avg` and `stdev` here apply only to the hourly table already in the search pipeline—not a 30d seasonal baseline. For production, consider a 30+ day `summary` index of hourly counts or a precomputed `lookup` of expected volume per day-of-week.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Baseline and scope
• Decide whether a **zero** event hour in **production** is ever acceptable. In large estates it should be rare; in lab, silence may be common—run separate schedulers per index or per environment.

Step 2 — Volume anomaly and gap
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | bin _time span=1h | stats count as log_count by _time | eventstats avg(log_count) as avg_logs stdev(log_count) as stdev_logs | where log_count < (avg_logs - 2*stdev_logs) OR log_count=0 | eval gap_severity=if(log_count=0, "Complete gap", "Unusual drop") | sort _time
```

Understanding this SPL (throughput, not per-field forensics)
**Audit log completeness** — Flags hours where audit **event** **count** is anomalously low or empty relative to the **same** search’s `avg`/`stdev` window. A drop can mean the TA, network path, or Catalyst **API** did not return events; it is **one** **signal** for investigation, not proof of tampering by itself. Pair with `metadata` and other sourcetypes in the `catalyst` index to distinguish **Splunk** pipeline loss from a **Catalyst**-side pause.

**Pipeline walkthrough**
• `bin` hour → `count` as `log_count` → `eventstats` for mean and standard deviation in the result set → `where` below `avg - 2*stdev` or `log_count=0` → `gap_severity` label → `sort` by time for incident handoff.

Step 3 — Validate
• In lab, block outbound from the add-on for one poll window and confirm a zero- or low-count hour appears; restore and confirm return to baseline. Compare a flagged hour to Catalyst’s own **Monitoring** and **api** service health in that time slice.

Step 4 — Operationalize (incident and GRC)
• **Complete gap:** page platform owners (Catalyst) and the Splunk index team in parallel. **Unusual drop:** GRC can open a “logging completeness” case with RFO. Store search history as evidence the control fired.

Step 5 — Troubleshooting
• **Too many** alerts: use a 7–30d **saved** baseline, raise to `3*stdev`, or require **N** consecutive bad hours. **stdev=0** (flat volume) in small windows: fall back to min-threshold in `where` (for example, `log_count < 10`).


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | bin _time span=1h | stats count as log_count by _time | eventstats avg(log_count) as avg_logs stdev(log_count) as stdev_logs | where log_count < (avg_logs - 2*stdev_logs) OR log_count=0 | eval gap_severity=if(log_count=0, "Complete gap", "Unusual drop") | sort _time
```

## Visualization

Time series of `log_count` with overlaid control limits, table of anomalous buckets with `gap_severity`, alert when Complete gap or persistent unusual drop.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
