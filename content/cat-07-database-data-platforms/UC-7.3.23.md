<!-- AUTO-GENERATED from UC-7.3.23.json — DO NOT EDIT -->

---
id: "7.3.23"
title: "Elasticsearch Security Audit Authentication Failures"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.23 · Elasticsearch Security Audit Authentication Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Draft

*We watch for repeated or suspicious sign-in activity on our databases so we can catch brute-force and misconfiguration before they become account takeovers.*

---

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

## Known False Positives

Planned access reviews, recertification, break-glass accounts, and vendor maintenance can emit privilege- or access-change events that match the rule but are already approved; require a change ticket for context.

## References

- [Elasticsearch audit logging](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
