<!-- AUTO-GENERATED from UC-8.1.88.json — DO NOT EDIT -->

---
id: "8.1.88"
title: "WildFly Datasource Connection Pool Exhaustion"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.88 · WildFly Datasource Connection Pool Exhaustion

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Capacity &middot; **Status:** Draft

*We use this to speed isolation of DB incidents from application code defects.*

---

## Description

JDBC pool saturation blocks servlet threads and causes cascading timeouts. JMX statistics expose active versus available connections without parsing stacks.

## Value

Speeds isolation of DB incidents from application code defects.

## Implementation

Set `statistics-enabled=true` on datasource in `standalone.xml`. Ingest via `Splunk_TA_jmx`. Page when active/max ≥95%.

## SPL

```spl
index=web sourcetype="jmx:jboss"
| search mbean="*data-source=*statistics*jdbc*"
| eval active=tonumber(ActiveCount) max=tonumber(MaxPoolSize)
| eval pct=if(max>0, round(100*active/max,1), null())
| where pct >= 95
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## Known False Positives

Thread or worker pools fill during traffic spikes, slow upstream services, or DoS-style load. A surge alone can be benign if backends recover.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#datasources)
