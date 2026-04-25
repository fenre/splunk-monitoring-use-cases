<!-- AUTO-GENERATED from UC-8.5.36.json — DO NOT EDIT -->

---
id: "8.5.36"
title: "ActiveMQ Network of Brokers Topology and Bridge Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.36 · ActiveMQ Network of Brokers Topology and Bridge Events

## Description

In a network of brokers, bridge connections carry cross-site traffic; unexpected stops or flapping `NetworkConnector` lines correlate with split-brain message routing and duplicate delivery risk. Structured alerting on these log signatures supports DR drills and firewall change validation.

## Value

Makes hub-and-spoke or mesh broker layouts observable from the canonical broker log stream without relying on ad-hoc grep during incidents.

## Implementation

Normalize multi-line log wrapping. Build allowlists for planned maintenance connectors. Enrich with CMDB site codes via `host` lookup. For duplex=false links, separate inbound vs outbound patterns in follow-on searches.

## SPL

```spl
index=messaging sourcetype="activemq:log" earliest=-7d
| search ("NetworkConnector" OR "network bridge" OR "duplex" OR "DiscoveryNetworkConnector" OR "Started network bridge" OR "Stopped network bridge" OR "bridge to" OR "Establishing network connection")
| rex field=_raw "NetworkConnector\s+(?<connector>\S+)"
| stats count as events latest(_raw) as sample by host, connector
| sort -events
```

## Visualization

Timeline of connector keywords, top connectors by event volume, geographic/site facet if enriched.

## References

- [Apache ActiveMQ — Networks of Brokers](https://activemq.apache.org/networks-of-brokers)
- [Apache ActiveMQ — Discovery](https://activemq.apache.org/features)
