<!-- AUTO-GENERATED from UC-8.1.91.json — DO NOT EDIT -->

---
id: "8.1.91"
title: "WildFly JSR-352 Batch Job Execution Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.91 · WildFly JSR-352 Batch Job Execution Failures

## Description

Batch jobs often power billing and reporting; silent failures skew business numbers. Centralizing JSR-352 errors aids operations handoff.

## Value

Reduces financial and compliance risk from missed batch completion.

## Implementation

Enable batch job logging; tag batch hosts. Create ticket automation on first failure in prod windows.

## SPL

```spl
index=web sourcetype="jboss:server"
| regex _raw="(?i)(BATCH.*FAILED|JobRepository.*FAILURE|javax.batch.*Exception)"
| rex field=_raw "job=(?<job_name>\S+)"
| stats count by host, job_name
| where count >= 1
```

## Visualization

Time series for pool/queue metrics, top stats for failures, event timeline for deploys.

## References

- [WildFly Admin Guide](https://docs.wildfly.org/30/Admin_Guide.html#batch-jberet-subsystem)
