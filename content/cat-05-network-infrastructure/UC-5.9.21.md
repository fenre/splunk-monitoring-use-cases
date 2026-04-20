---
id: "5.9.21"
title: "Proxy Issue Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.21 · Proxy Issue Detection

## Description

Detects when proxy infrastructure (forward proxies, web gateways, SASE secure edges) becomes the root cause of connectivity issues, helping teams quickly identify whether the problem is in the proxy layer or the destination.

## Value

Detects when proxy infrastructure (forward proxies, web gateways, SASE secure edges) becomes the root cause of connectivity issues, helping teams quickly identify whether the problem is in the proxy layer or the destination.

## Implementation

Events with type "Proxy Issue" indicate problems in proxy/web gateway infrastructure. These are automatically detected when ThousandEyes agents traverse proxy paths. Correlate with SASE or web security gateway logs in Splunk for root cause analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Event API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Events with type "Proxy Issue" indicate problems in proxy/web gateway infrastructure. These are automatically detected when ThousandEyes agents traverse proxy paths. Correlate with SASE or web security gateway logs in Splunk for root cause analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`event_index` type="Proxy Issue"
| stats count by severity, state
| sort -count
```

Understanding this SPL

**Proxy Issue Detection** — Detects when proxy infrastructure (forward proxies, web gateways, SASE secure edges) becomes the root cause of connectivity issues, helping teams quickly identify whether the problem is in the proxy layer or the destination.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Event API. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `event_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by severity, state** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table, Single value (active proxy issues).

## SPL

```spl
`event_index` type="Proxy Issue"
| stats count by severity, state
| sort -count
```

## Visualization

Events timeline, Table, Single value (active proxy issues).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
