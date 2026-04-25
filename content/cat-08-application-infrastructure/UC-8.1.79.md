<!-- AUTO-GENERATED from UC-8.1.79.json — DO NOT EDIT -->

---
id: "8.1.79"
title: "Apache Tomcat Deployment Descriptor Change Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.79 · Apache Tomcat Deployment Descriptor Change Detection

## Description

Unplanned deploy log lines in Catalina indicate configuration drift, hot redeploy, or supply-chain risk. Correlating descriptor paths with change tickets catches shadow releases.

## Value

Reduces unauthorized or accidental production deployments on Java stacks.

## Implementation

Monitor `$CATALINA_BASE/logs/catalina*.log` with UF; use `multiline` for Java stack traces. Alert on unexpected deploy strings outside change windows.

## SPL

```spl
index=web sourcetype="tomcat:catalina"
| regex _raw="(?i)(Deploying web application|Deployment of web application|Starting ProtocolHandler|Stopping ProtocolHandler)"
| rex field=_raw "descriptor\[(?<descriptor>[^\]]+)\]"
| stats earliest(_time) as first_seen latest(_time) as last_seen by host, descriptor
| where isnotnull(descriptor)
```

## Visualization

Time charts for utilization, tables for top URIs and deploy events, single-value alerts.

## References

- [Apache Tomcat documentation](https://tomcat.apache.org/tomcat-10.0-doc/deployer-howto.html)
