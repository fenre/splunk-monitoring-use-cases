<!-- AUTO-GENERATED from UC-8.5.22.json — DO NOT EDIT -->

---
id: "8.5.22"
title: "ActiveMQ Broker Restart and Persistence Adapter Change"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-8.5.22 · ActiveMQ Broker Restart and Persistence Adapter Change

## Description

Broker start/stop banners and persistence adapter swaps flag maintenance windows, failed automatic restarts, or unplanned data-directory changes.

## Value

Correlates application errors with broker lifecycle events faster than host-level uptime checks alone.

## Implementation

Capture both wrapper logs and `activemq.log`. Filter known autoscaler churn via lookup. Alert on stop events outside approved windows.

## SPL

```spl
index=messaging sourcetype="activemq:log"
| search "Apache ActiveMQ" AND ("started" OR "Starting" OR "stopped" OR "Stopping" OR "Persistence Adapter" OR "KahaDB")
| table _time, host, _raw
```

## Visualization

Timeline (broker lifecycle), Table (host, message), Single value (restarts per day).

## References

- [Apache ActiveMQ — Installation](https://activemq.apache.org/components/classic/documentation/installation)
- [Apache ActiveMQ — KahaDB](https://activemq.apache.org/components/classic/documentation/kahadb)
