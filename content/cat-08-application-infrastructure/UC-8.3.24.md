<!-- AUTO-GENERATED from UC-8.3.24.json — DO NOT EDIT -->

---
id: "8.3.24"
title: "HAProxy SSL Handshake and Client Certificate Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.3.24 · HAProxy SSL Handshake and Client Certificate Failures

## Description

TLS failures may indicate expired client certs, weak ciphers, or MITM attempts on public listeners.

## Value

Preserves cryptographic hygiene for zero-trust and mutual TLS designs.

## Implementation

Extend `log-format` with SSL variables; sample baseline noise before alerting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HAProxy syslog with `%sslc` / `%sslfc` log variables or custom format.
• Ensure the following data sources are available: `index=proxy` TLS termination logs (`sourcetype=haproxy:tcp` or `haproxy:http` with SSL fields).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Match phrases to your HAProxy TLS log output; many shops ship TLS termination logs only at info level.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=proxy (sourcetype="haproxy:http" OR sourcetype="haproxy:tcp")
| search "SSL" ("handshake failure" OR "verify error" OR "alert unknown ca")
| stats count by host
| sort -count
```

Understanding this SPL

**HAProxy SSL Handshake and Client Certificate Failures** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=proxy` TLS termination logs (`sourcetype=haproxy:tcp` or `haproxy:http` with SSL fields). **App/TA**: HAProxy syslog with `%sslc` / `%sslfc` log variables or custom format. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timechart (SSL errors), table (frontend), link to PKI calendar..

## SPL

```spl
index=proxy (sourcetype="haproxy:http" OR sourcetype="haproxy:tcp")
| search "SSL" ("handshake failure" OR "verify error" OR "alert unknown ca")
| stats count by host
| sort -count
```

## Visualization

Timechart (SSL errors), table (frontend), link to PKI calendar.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [HAProxy Management Guide — Logging](https://www.haproxy.com/documentation/haproxy-management-guide/latest/observability/logging/)
