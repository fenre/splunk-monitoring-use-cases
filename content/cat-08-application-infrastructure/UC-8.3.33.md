<!-- AUTO-GENERATED from UC-8.3.33.json — DO NOT EDIT -->

---
id: "8.3.33"
title: "Kafka SASL Authentication Failure Spike"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.33 · Kafka SASL Authentication Failure Spike

## Description

Repeated SASL or TLS handshake errors often indicate credential rotation mistakes, misconfigured clients, or brute-force attempts against listeners.

## Value

Protects clusters from silent client lockouts and highlights active authentication attacks or broken automation after secret changes.

## Implementation

Collect broker logs from every listener host. Baseline normal noise from health-check clients. Alert when the 15-minute error count exceeds a cluster-specific threshold or doubles week-over-week.

## SPL

```spl
index=kafka sourcetype="kafka:serverLog"
| search "javax.security.sasl" OR "SaslAuthenticationException" OR "Authentication failed" OR "SSL handshake failed"
| rex "^\[[^\]]+\]\s+(?<log_level>\w+)"
| where log_level IN ("ERROR","WARN")
| timechart span=15m count by host
```

## Visualization

Line chart (auth errors by broker), Table (recent _raw samples), Single value (errors in window).

## References

- [Apache Kafka — Security](https://kafka.apache.org/documentation/#security)
- [Configure monitor inputs for the Splunk Add-on for Kafka](https://docs.splunk.com/Documentation/AddOns/released/Kafka/Configuremonitorinputs)
