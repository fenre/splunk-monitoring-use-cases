<!-- AUTO-GENERATED from UC-8.1.89.json — DO NOT EDIT -->

---
id: "8.1.89"
title: "WildFly Deployment Scanner Hot-Deploy Activity"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.89 · WildFly Deployment Scanner Hot-Deploy Activity

## Description

The deployment scanner can add or replace deployments automatically. Unexpected deploy messages may indicate compromised CI/CD credentials or mis-scoped directories.

## Value

Strengthens change control on Java middleware.

## Implementation

Set deployment scanner logging to INFO in dev-like environments; alert on deploy events outside maintenance on prod.

## SPL

```spl
index=web sourcetype="jboss:server"
| regex _raw="(?i)(WFLYSRV00(1|2|4)|Deployed.*\.war|Undeployed)"
| stats count by host, _raw
| sort - count
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#deployment-scanner)
