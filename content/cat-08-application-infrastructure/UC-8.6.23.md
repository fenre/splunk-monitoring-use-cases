<!-- AUTO-GENERATED from UC-8.6.23.json — DO NOT EDIT -->

---
id: "8.6.23"
title: "Traefik Router Backend Resolution Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.6.23 · Traefik Router Backend Resolution Errors

## Description

Router/service errors surface DNS, KV, or Docker socket issues before clients see 404/503 at scale.

## Value

Clarifies misconfigured labels or stale SD entries.

## Implementation

Enable JSON logs with `msg` field for easier `stats`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Traefik application logging.
• Ensure the following data sources are available: `index=platform` `sourcetype=traefik:log`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Combine with provider-specific logs (Kubernetes, Consul).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=platform sourcetype="traefik:log"
| search "error" AND ("Router" OR "service" OR "provider") AND ("unable" OR "cannot" OR "failed")
| stats count by message
| sort -count
```

Understanding this SPL

**Traefik Router Backend Resolution Errors** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=platform` `sourcetype=traefik:log`. **App/TA**: Traefik application logging. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Table (signature), timeline, correlation with Kubernetes events index..

## SPL

```spl
index=platform sourcetype="traefik:log"
| search "error" AND ("Router" OR "service" OR "provider") AND ("unable" OR "cannot" OR "failed")
| stats count by message
| sort -count
```

## Visualization

Table (signature), timeline, correlation with Kubernetes events index.

## References

- [Traefik — Logs and Access Logs](https://doc.traefik.io/traefik/observability/logs-and-access-logs/)
