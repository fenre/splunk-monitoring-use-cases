<!-- AUTO-GENERATED from UC-8.1.85.json — DO NOT EDIT -->

---
id: "8.1.85"
title: "WildFly Undertow Worker Thread Saturation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.85 · WildFly Undertow Worker Thread Saturation

## Description

Undertow uses XNIO worker threads for blocking servlet work. When workers are exhausted, latency climbs while CPU may look healthy. Log-derived utilization complements JMX for quick alerting.

## Value

Protects user-facing latency on WildFly-hosted APIs and portals.

## Implementation

Forward `$JBOSS_HOME/standalone/log/server.log` via UF. For precision, add `Splunk_TA_jmx` MBeans `undertow` worker. Alert on worker utilization ≥90%.

## SPL

```spl
index=web sourcetype="jboss:server"
| regex _raw="(?i)XNIO.*worker"
| rex field=_raw "IO-threads=(?<io_threads>\d+).*worker-threads=(?<worker_current>\d+)/(?<worker_max>\d+)"
| eval w_util=if(worker_max>0, round(100*tonumber(worker_current)/tonumber(worker_max),1), null())
| where w_util >= 90
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#undertow-subsystem)
