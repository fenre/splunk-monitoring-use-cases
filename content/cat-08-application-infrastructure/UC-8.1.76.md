<!-- AUTO-GENERATED from UC-8.1.76.json — DO NOT EDIT -->

---
id: "8.1.76"
title: "Apache Tomcat JDBC Pool Utilization (active vs idle vs max)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.76 · Apache Tomcat JDBC Pool Utilization (active vs idle vs max)

## Description

JDBC pool exhaustion manifests as slow responses even when CPU is low. Tracking `numActive` against `maxActive` shows when the database or pool sizing blocks the servlet tier.

## Value

Separates database contention from application bugs and guides pool and DB scale decisions.

## Implementation

Enable JMX on Tomcat (`setenv.sh` CATALINA_OPTS). Map datasource MBeans in `Splunk_TA_jmx`. Create lookup from `name` to application service.

## SPL

```spl
index=web (sourcetype="jmx:tomcat:datasource" OR sourcetype="tomcat:jmx")
| search mbean="*DataSource*" OR mbean="*ConnectionPool*"
| eval active=tonumber(numActive), idle=tonumber(numIdle), max=tonumber(maxActive)
| eval pool_pct=if(max>0, round(100*active/max,1), null())
| where pool_pct >= 85
| table _time, host, mbean, active, idle, max, pool_pct
```

## Visualization

Time charts for utilization, tables for top URIs and deploy events, single-value alerts.

## References

- [Apache Tomcat documentation](https://tomcat.apache.org/tomcat-10.0-doc/jdbc-pool.html)
