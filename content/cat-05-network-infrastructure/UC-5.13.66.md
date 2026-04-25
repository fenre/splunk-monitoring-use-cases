<!-- AUTO-GENERATED from UC-5.13.66.json — DO NOT EDIT -->

---
id: "5.13.66"
title: "Event Notification Delivery Failure Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.66 · Event Notification Delivery Failure Tracking

## Description

Monitors the flow of event notifications from Catalyst Center to detect delivery failures, gaps, or webhook connectivity issues.

## Value

If the webhook pipeline fails, critical events go undetected. Monitoring delivery health ensures the real-time alerting channel stays reliable.

## Implementation

**Primary data:** `index=catalyst` `sourcetype=cisco:dnac:event:notification` (HEC as in UC-5.13.64). **HEC health:** In parallel, monitor `index=_internal` `source=*metrics.log* OR source=*splunkd.log*` for HEC 4xx/5xx, connection errors, or token failures (tune to your log volume). If HEC is on a forwarder, also watch `metrics.log` for `group=per_source_metrics` and `per_sourcetype` throughput. **Catalyst Center side:** if the product exposes webhook **delivery** status in the admin UI, align drops with Splunk gaps. For this UC’s SPL: hourly bucketing and statistical drop detection flag "quiet" hours; tune `stdev` when volume is very low. **Catalyst Center** webhook URL remains `https://<splunk>:8088/services/collector/event` with the Splunk HEC `Authorization` header. Document maintenance windows (Catalyst or Splunk) so the alert can be suppressed.

## Detailed Implementation

Prerequisites
• Steady HEC event flow from UC-5.13.64 for at least a week to build a non-zero `avg_events` baseline per hour; otherwise `stdev` is unstable (consider longer `span=1d` in quiet environments or use fixed minimum thresholds).

Step 1 — HEC and webhook stability
- Verify Catalyst Center can reach `https://<host>:8088` and that TLS, DNS, and firewall rules are static.
- In Splunk, watch `index=_internal` for `httpevent` / `httpinput` (exact component names depend on version) and failed parsing.
- Optional: a synthetic "heartbeat" subscription in Catalyst Center that emits a low-severity test event (if your policy allows) to guarantee non-zero volume.

Step 2 — Anomaly search

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" | bin _time span=1h | stats count as received_events by _time | eventstats avg(received_events) as avg_events stdev(received_events) as stdev_events | where received_events < (avg_events - 2*stdev_events) OR received_events=0 | eval gap_type=if(received_events=0, "Complete delivery gap", "Unusual drop in notifications") | table _time received_events avg_events gap_type
```

Step 3 — Complementary check
- `index=_internal log_level=ERROR *http* *collector*` (adjust) for HEC server-side issues.

Step 4 — Validate
- Pause webhook in lab (or block port) and confirm this search fires within a bucket or two. Restore and confirm return to normal.

Step 5 — Operationalize
- Page when `gap_type` is `Complete delivery gap` during business-impacting hours; for `Unusual drop`, require correlation with known change tickets.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:event:notification" | bin _time span=1h | stats count as received_events by _time | eventstats avg(received_events) as avg_events stdev(received_events) as stdev_events | where received_events < (avg_events - 2*stdev_events) OR received_events=0 | eval gap_type=if(received_events=0, "Complete delivery gap", "Unusual drop in notifications") | table _time received_events avg_events gap_type
```

## Visualization

Time series of `received_events` with `avg_events` band, table of `gap_type` and timestamps, combine with a panel of HEC error count from _internal on the same dashboard.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
