<!-- AUTO-GENERATED from UC-2.6.62.json — DO NOT EDIT -->

---
id: "2.6.62"
title: "Citrix Workspace Service Feed Availability"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.62 · Citrix Workspace Service Feed Availability

## Description

The Citrix Workspace service must enumerate feeds, aggregate resources from brokering and cloud sources, and stay responsive over HTTPS. Certificate problems, API throttling, or connector outages can produce empty start menus, missing apps, or flapping resource lists that mimic client bugs. Synthetics and server-side feed diagnostics measure availability and latency to the user-facing document endpoints and tie failures to a specific store, region, or IDP, shortening mean time to restore before broad ticket spikes.

## Value

The Citrix Workspace service must enumerate feeds, aggregate resources from brokering and cloud sources, and stay responsive over HTTPS. Certificate problems, API throttling, or connector outages can produce empty start menus, missing apps, or flapping resource lists that mimic client bugs. Synthetics and server-side feed diagnostics measure availability and latency to the user-facing document endpoints and tie failures to a specific store, region, or IDP, shortening mean time to restore before broad ticket spikes.

## Implementation

Deploy both passive logs (if available from Citrix) and a lightweight synthetic that requests the same feed entry points the clients use, tagged by region. Send results to a dedicated index with five-minute resolution. Set SLOs (for example 99.9 percent under one second) per region. Alert on two consecutive non-200 responses, zero resources returned for any active directory group, or latency above two seconds. Pair alerts with 2.6.16 and 2.6.60 when the failure is identity-related. Keep separate dashboards for on-premises stores versus cloud Workspace.

## Detailed Implementation

Prerequisites
• Known-good feed URL list per environment; HEC token with TLS; optional allowlist of probe sources.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Place synthetics at user-like vantage points: office egress and two home-sim paths if possible. Validate certificates at each step.

Step 2 — Create the search and alert
Tie alerts to a quiet-hours suppression only when maintenance is logged. Add child searches that split identity versus broker failures by outcome codes.

Step 3 — Validate
Induce 403/401 in test with a bad token, confirm the feed search fires. Revert and confirm clear.

Step 4 — Operationalize
Add runbook link for empty catalog: ordered checks for brokering, cloud connector, and identity, with owners.

## SPL

```spl
index=xd sourcetype="citrix:workspace:feed"
| eval ok=if(match(coalesce(http_status, status, "200"), "^(200|204)$"), 1, 0)
| eval lat=tonumber(coalesce(latency_ms, response_time_ms, 0))
| where ok=0 OR lat>2000 OR tonumber(coalesce(resource_count, -1))=0
| eval issue=case(ok=0, "http_or_feed_error", lat>2000, "high_latency", tonumber(coalesce(resource_count,0))=0, "empty_catalog", true(), "other")
| timechart span=5m count by issue, store_name
| fillnull value=0
```

## Visualization

Uptime and latency SLO by region; heatmap of feed errors; single value: resources returned versus expected baseline from yesterday same hour.

## References

- [Citrix Workspace app — technical overview and connectivity](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows.html)
- [Configure Workspace experience (Citrix DaaS)](https://docs.citrix.com/en-us/citrix-daas-service/integrate-identity-serve-apps-and-data.html)
