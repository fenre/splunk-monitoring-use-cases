<!-- AUTO-GENERATED from UC-8.5.34.json — DO NOT EDIT -->

---
id: "8.5.34"
title: "ActiveMQ Advisory Message Storm Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.5.34 · ActiveMQ Advisory Message Storm Detection

## Description

Advisory topics carry connection and destination lifecycle events; a buggy client or misconfigured bridge that churns subscriptions can generate huge advisory traffic and CPU load. Spikes in HTTP access to `ActiveMQ.Advisory` paths or console polling often precede broker saturation.

## Value

Protects shared brokers from self-inflicted advisory storms that look like organic traffic growth until thread dumps show advisory fan-out.

## Implementation

Ensure Tomcat/Jetty access logs include `uri_path` or `request_uri`. Baseline per environment; tune multiplier and floor. For log-only sites, mirror with `activemq:log` searches on `Advisory`.

## SPL

```spl
index=messaging sourcetype="activemq:web" earliest=-4h
| search uri_path="*Advisory*" OR uri_path="*advisory*" OR request_uri="*ActiveMQ.Advisory*"
| bucket _time span=5m
| stats count as advisory_http_hits by _time, host, client_ip
| eventstats median(advisory_http_hits) as med by host
| where advisory_http_hits > med*5 AND advisory_http_hits > 500
| table _time, host, client_ip, advisory_http_hits, med
```

## Visualization

Line chart (advisory HTTP hits), table (client_ip, count), anomaly overlay vs median.

## References

- [Apache ActiveMQ — Advisory Message](https://activemq.apache.org/advisory-message)
- [Apache ActiveMQ — Web Console](https://activemq.apache.org/web-console)
