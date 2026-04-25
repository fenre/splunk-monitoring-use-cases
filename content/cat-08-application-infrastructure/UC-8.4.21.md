<!-- AUTO-GENERATED from UC-8.4.21.json — DO NOT EDIT -->

---
id: "8.4.21"
title: "HAProxy Frontend Session Rate Versus ulimit"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.21 · HAProxy Frontend Session Rate Versus ulimit

## Description

`scur` approaching `slim` on a frontend signals connection limits or ulimit pressure during campaigns.

## Value

Informs tuning of `maxconn`, kernel limits, and cloud LB pairing.

## Implementation

Poll stats frequently; `slim` may be 0 if unlimited—handle with `eval`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: HAProxy stats CSV scripted input.
• Ensure the following data sources are available: `index=haproxy` `sourcetype=haproxy:stats` (`rate`, `scur`, `slim`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
CSV field names must match HAProxy version; confirm `slim` presence.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=haproxy sourcetype="haproxy:stats" type=frontend
| eval sess_pct=if(slim>0, round(100*scur/slim,1), null())
| where sess_pct > 85
| table _time, pxname, scur, slim, sess_pct
```

Understanding this SPL

**HAProxy Frontend Session Rate Versus ulimit** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=haproxy` `sourcetype=haproxy:stats` (`rate`, `scur`, `slim`). **App/TA**: HAProxy stats CSV scripted input. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (scur vs slim), single value alert..

## SPL

```spl
index=haproxy sourcetype="haproxy:stats" type=frontend
| eval sess_pct=if(slim>0, round(100*scur/slim,1), null())
| where sess_pct > 85
| table _time, pxname, scur, slim, sess_pct
```

## Visualization

Line chart (scur vs slim), single value alert.

## References

- [HAProxy Management Guide — Logging](https://www.haproxy.com/documentation/haproxy-management-guide/latest/observability/logging/)
