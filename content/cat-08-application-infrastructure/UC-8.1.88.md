<!-- AUTO-GENERATED from UC-8.1.88.json — DO NOT EDIT -->

---
id: "8.1.88"
title: "WildFly Datasource Connection Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.88 · WildFly Datasource Connection Pool Exhaustion

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

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#datasources)
