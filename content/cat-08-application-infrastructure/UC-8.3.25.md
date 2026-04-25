<!-- AUTO-GENERATED from UC-8.3.25.json — DO NOT EDIT -->

---
id: "8.3.25"
title: "Envoy External Authorization Denied Responses"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.3.25 · Envoy External Authorization Denied Responses

## Description

External authorization denials (`UAEX`) highlight policy changes, token outages, or attacks against protected routes.

## Value

Validates zero-trust enforcement at the data plane.

## Implementation

Enable detailed response flags in access logs; redact sensitive headers at ingest.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Envoy access logging to HEC / forwarder.
• Ensure the following data sources are available: `index=mesh` `sourcetype=envoy:access` (`response_code`, `response_flags`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Flag semantics depend on Envoy version; consult response_codes docs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="envoy:access"
| search response_flags=*UAEX* OR response_flags=*ext_authz*
| where response_code >= 403
| stats count by route_name, response_code
| sort -count
```

Understanding this SPL

**Envoy External Authorization Denied Responses** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=mesh` `sourcetype=envoy:access` (`response_code`, `response_flags`). **App/TA**: Envoy access logging to HEC / forwarder. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Stacked bar (403/401), table (route), join with IdP health metrics..

## SPL

```spl
index=mesh sourcetype="envoy:access"
| search response_flags=*UAEX* OR response_flags=*ext_authz*
| where response_code >= 403
| stats count by route_name, response_code
| sort -count
```

## Visualization

Stacked bar (403/401), table (route), join with IdP health metrics.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Envoy — Access logging](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
