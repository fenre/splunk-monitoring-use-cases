<!-- AUTO-GENERATED from UC-7.3.23.json — DO NOT EDIT -->

---
id: "7.3.23"
title: "Elasticsearch Security Audit Authentication Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.23 · Elasticsearch Security Audit Authentication Failures

## Description

Elastic Stack audit logs record REST and transport authentication failures. Security teams ship these JSON events to Splunk for correlation with application and IdP logs.

## Value

Extends SOC coverage to the search tier where service accounts and Kibana users can be brute forced.

## Implementation

Normalize Elastic Common Schema fields at ingest (`user.name`, `source.ip`, `cluster.uuid`). Tune thresholds for service mesh identities. Retain per regulatory index routing.

## SPL

```spl
index=sec sourcetype="elasticsearch:audit"
| search "authentication_failed" OR event.outcome="failure" OR event.action="authentication_failed"
| bin _time span=1h
| stats count as failures dc(user.name) as users dc(source.ip) as sources by cluster_uuid, _time
| where failures > 25
```

## Visualization

Table (user, sources, count), Timeline (failures), Map (source.ip).

## References

- [Elasticsearch audit logging](https://www.elastic.co/guide/en/elasticsearch/reference/current/audit-logging.html)
