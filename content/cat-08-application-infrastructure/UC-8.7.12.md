<!-- AUTO-GENERATED from UC-8.7.12.json — DO NOT EDIT -->

---
id: "8.7.12"
title: "Kafka Client Topic Authorization Failure Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.7.12 · Kafka Client Topic Authorization Failure Audit

## Description

Denied produce/fetch attempts document who tried to access which topic—evidence for least-privilege reviews and insider-threat investigations.

## Value

Produces auditor-friendly evidence that sensitive topics reject unauthorized clients and highlights misconfigured service accounts early.

## Implementation

Ensure broker logging includes principal/topic context. Retain 13 months in a restricted index for regulated workloads. Mask client secrets if present.

## SPL

```spl
index=kafka sourcetype="kafka:serverLog"
| search "TopicAuthorizationException" OR "Authorization failed" OR ("DENIED" AND "Principal")
| table _time, host, _raw
```

## Visualization

Table (recent denials), Timeline (authorization failures), Stats (count by principal).

## References

- [Apache Kafka — Authorization and ACLs](https://kafka.apache.org/documentation/#security_authz)
- [Source types for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Sourcetypes)
