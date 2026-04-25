<!-- AUTO-GENERATED from UC-1.2.135.json — DO NOT EDIT -->

---
id: "1.2.135"
title: "macOS Splunk Universal Forwarder Heartbeat and KV Store Queue Backlog"
criticality: "critical"
splunkPillar: "Platform"
---

# UC-1.2.135 · macOS Splunk Universal Forwarder Heartbeat and KV Store Queue Backlog

## Description

A silent Universal Forwarder on macOS still breaks compliance when it stops phone-home or queues explode during VPN outages. Combining presence of `splunkd` forwarded events with TCP output queue metrics surfaces dead agents before log gaps invalidate security monitoring.

## Value

Restores observability SLAs by detecting offline or back-pressured macOS forwarders before log loss exceeds audit windows.

## Implementation

Forward a minimal `_internal` slice (splunkd, metrics) from endpoints only if policy permits—many teams duplicate to a restricted `infra_int` index with transforms dropping payloads. On the search head, build a baseline count of hosts per 15m bucket; alert when a known-population host disappears or when `metrics.log` `tcpout_connections` shows `current_queue` sustained above your tier (example 10k). For pure heartbeat without internal indexes, use a custom `sourcetype=uf_heartbeat` one-liner script instead.

## Detailed Implementation

Prerequisites
• CMDB or saved list of expected `host` values for macOS UFs.
• Legal/security approval for `_internal` forwarding.

Step 1 — If `_internal` is blocked, deploy `sourcetype=uf_heartbeat` with a 5m cron.

Step 2 — Use `inputlookup` expected_hosts and `| stats` to find missing.

Step 3 — Validate by stopping splunkd on a canary.

Step 4 — Route alerts to endpoint ops with VPN health correlation.

## SPL

```spl
index=_internal source=*splunkd.log* host=* TermType=Forwarded
| bin _time span=15m
| stats dc(host) as reporting_hosts by _time
| join type=left _time [
    search index=_internal source=*metrics.log* group=tcpout_connections name=*
    | bin _time span=15m
    | stats avg(current_queue) as avg_queue by _time, host
    | where avg_queue > 10000
    | stats count as hosts_with_queue_pressure by _time
]
| fillnull value=0 hosts_with_queue_pressure
```

## Visualization

Area chart (reporting_hosts over time), Table (missing hosts vs CMDB), Single value (hosts_with_queue_pressure).

## References

- [Splunk Docs: Forward data from Splunk Enterprise internal indexes](https://docs.splunk.com/Documentation/Splunk/latest/Data/Forwarddatafrominternalsindexes)
- [Splunk Docs: Monitor internal Splunk Enterprise logs](https://docs.splunk.com/Documentation/Splunk/latest/Troubleshooting/Monitorinternalsplunklogs)
