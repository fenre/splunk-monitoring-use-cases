<!-- AUTO-GENERATED from UC-8.2.39.json — DO NOT EDIT -->

---
id: "8.2.39"
title: "Microsoft IIS Failed Request Tracing (FREB) Log Analysis"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.2.39 · Microsoft IIS Failed Request Tracing (FREB) Log Analysis

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault &middot; **Status:** Draft

*We use this to shortens performance and reliability incidents on Windows-only stacks without full code deploys.*

---

## Description

FREB captures per-request pipeline events—including modules, rewrite rules, and authentication—when requests fail or exceed thresholds. Aggregating failure reasons ranks fixes faster than coarse HTTP status counts alone.

## Value

Shortens performance and reliability incidents on Windows-only stacks without full code deploys.

## Implementation

Enable FREB for 5xx and long-running requests; ship `%SystemDrive%\inetpub\logs\FailedReqLogFiles`. Add `props.conf` XML breaking.

## SPL

```spl
index=web sourcetype="iis:freb" OR sourcetype="ms:iis:freb"
| stats count by url, status_code, failure_reason
| sort - count
| head 30
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Microsoft IIS documentation](https://learn.microsoft.com/en-us/iis/troubleshoot/using-failed-request-tracing)
