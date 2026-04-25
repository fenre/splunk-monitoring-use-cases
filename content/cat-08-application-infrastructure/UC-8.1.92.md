<!-- AUTO-GENERATED from UC-8.1.92.json — DO NOT EDIT -->

---
id: "8.1.92"
title: "WildFly Security Domain Authentication Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.92 · WildFly Security Domain Authentication Failures

## Description

Elytron audit records document authentication outcomes for regulated apps. Clustering denials by domain highlights misconfigured clients or brute force.

## Value

Supports identity governance and SOC investigations.

## Implementation

Enable `audit-log` in Elytron; forward JSON to HEC with `wildfly:audit`. Enrich principal with IdP username mapping.

## SPL

```spl
index=web sourcetype="wildfly:audit"
| search outcome="failure" OR outcome="denied"
| stats count by security_domain, principal, module
| where count > 20
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#elytron-audit)
