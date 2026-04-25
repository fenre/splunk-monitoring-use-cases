<!-- AUTO-GENERATED from UC-8.1.75.json — DO NOT EDIT -->

---
id: "8.1.75"
title: "Apache Tomcat Thread Pool Exhaustion (activeThreads vs maxThreads)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.75 · Apache Tomcat Thread Pool Exhaustion (activeThreads vs maxThreads)

## Description

Tomcat's HTTP worker threads handle every concurrent request. When `currentThreadsBusy` approaches `maxThreads`, new work queues or times out at the connector. Early detection prevents cascading failures at the load balancer.

## Value

Preserves user experience by scaling or tuning connectors before thread starvation.

## Implementation

Install Splunk Add-on for JMX (`Splunk_TA_jmx`); configure `jmx.conf` for `Catalina:type=ThreadPool,name=*`. Poll 60s. Alert when `currentThreadsBusy/maxThreads` ≥90% for 15m.

## SPL

```spl
index=web sourcetype="jmx:tomcat:threadpool"
| eval maxt=tonumber(maxThreads), act=tonumber(currentThreadsBusy)
| eval util_pct=if(maxt>0, round(100*act/maxt,1), null())
| where util_pct >= 90
| timechart span=5m max(util_pct) as thread_util by host, mbean
```

## Visualization

Time charts for utilization, tables for top URIs and deploy events, single-value alerts.

## References

- [Apache Tomcat documentation](https://tomcat.apache.org/tomcat-10.0-doc/config/executor.html)
