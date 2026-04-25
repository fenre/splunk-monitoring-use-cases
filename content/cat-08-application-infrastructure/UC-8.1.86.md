<!-- AUTO-GENERATED from UC-8.1.86.json — DO NOT EDIT -->

---
id: "8.1.86"
title: "WildFly EJB Pool max-pool-size Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.86 · WildFly EJB Pool max-pool-size Pressure

## Description

Stateless EJB pools bound the number of concurrent business method executions. Hitting `max-pool-size` forces waits or timeouts that resemble database issues.

## Value

Improves throughput planning for session beans without blind pool increases.

## Implementation

Expose JMX on management interface; whitelist EJB pool MBeans in `jmx.conf`. Map pools to applications with lookups.

## SPL

```spl
index=web sourcetype="jmx:jboss"
| search mbean="*ejb3*Pool*" OR name="*EJB*Pool*"
| eval in_use=tonumber(CurrentSize), max_pool=tonumber(MaxSize)
| eval util=if(max_pool>0, round(100*in_use/max_pool,1), null())
| where util >= 95
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Developer_Guide.html#ejb)
