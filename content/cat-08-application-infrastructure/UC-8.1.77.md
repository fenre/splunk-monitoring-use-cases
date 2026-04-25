<!-- AUTO-GENERATED from UC-8.1.77.json — DO NOT EDIT -->

---
id: "8.1.77"
title: "Apache Tomcat Session Creation Rate and Active Sessions"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.77 · Apache Tomcat Session Creation Rate and Active Sessions

## Description

Session storms increase memory use and replication traffic. An abnormal `sessionCounter` delta or very large `activeSessions` hints at crawler abuse, misconfigured clients, or sticky-session loss.

## Value

Protects heap and clustering cost by catching abusive session creation early.

## Implementation

Script `curl -u user http://host:8080/manager/text/sessions` or use JMX `Manager` MBean. Ingest as structured KV or JSON HEC.

## SPL

```spl
index=web sourcetype="tomcat:manager"
| eval active=tonumber(activeSessions), created=tonumber(sessionCounter)
| sort 0 host, _time
| streamstats window=2 global=f last(created) as prev_created by host
| eval create_rate=created-prev_created
| where create_rate > 500
| table _time, host, active, create_rate
```

## Visualization

Time charts for utilization, tables for top URIs and deploy events, single-value alerts.

## References

- [Apache Tomcat documentation](https://tomcat.apache.org/tomcat-10.0-doc/manager-howto.html)
