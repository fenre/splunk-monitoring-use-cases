<!-- AUTO-GENERATED from UC-8.1.93.json — DO NOT EDIT -->

---
id: "8.1.93"
title: "WildFly mod_cluster Node Health and Drain Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.93 · WildFly mod_cluster Node Health and Drain Events

## Description

mod_cluster informs Apache httpd which WildFly nodes are healthy. MCMP errors or DISABLED states mean traffic may stick to bad nodes.

## Value

Keeps HTTP load balanced fairly across the WildFly cluster.

## Implementation

Ensure mod_cluster advertises correctly; compare with HTTP front-end health checks. Alert on DISABLED or failed node chatter.

## SPL

```spl
index=web sourcetype="jboss:server"
| regex _raw="(?i)(mod_cluster|MCMP|STATUS.*DISABLED|node.*failed)"
| stats latest(_time) as last_event count by host
| where count > 0
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#mod_cluster-subsystem)
