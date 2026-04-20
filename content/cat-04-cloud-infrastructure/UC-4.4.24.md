---
id: "4.4.24"
title: "Hybrid Connectivity Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.4.24 · Hybrid Connectivity Status

## Description

ExpressRoute, Direct Connect, VPN, and Interconnect carry production traffic; tunnel or BGP drops partition workloads between on-prem and cloud.

## Value

ExpressRoute, Direct Connect, VPN, and Interconnect carry production traffic; tunnel or BGP drops partition workloads between on-prem and cloud.

## Implementation

Align metric semantics per provider in lookups; alert on sustained unhealthy state. Correlate with provider status pages ingested as `sourcetype=cloud:status`. Dashboard RTO/RPO targets for hybrid links.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (DX, VPN, TGW), Azure Monitor VPN/ExpressRoute metrics, `sourcetype=google:gcp:monitoring` (VPN/interconnect).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Align metric semantics per provider in lookups; alert on sustained unhealthy state. Correlate with provider status pages ingested as `sourcetype=cloud:status`. Dashboard RTO/RPO targets for hybrid links.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:cloudwatch" (namespace="AWS/DX" OR namespace="AWS/VPN") (metric_name="ConnectionState" OR metric_name="TunnelState"))
 OR (index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Network/expressRouteCircuits" metric_name="BgpPeerStatus")
 OR (index=gcp sourcetype="google:gcp:monitoring" metric.type="vpn.googleapis.com/tunnel_established")
| eval link_up=case(metric_name="ConnectionState" AND maximum=1,1, metric_name="TunnelState" AND maximum=1,1, metric_name="BgpPeerStatus" AND average>0,1, metric.type="vpn.googleapis.com/tunnel_established" AND value>0,1,1=1,0)
| stats min(link_up) as healthy by resourceId, resource.labels.*, bin(_time, 5m)
| where healthy=0
```

Understanding this SPL

**Hybrid Connectivity Status** — ExpressRoute, Direct Connect, VPN, and Interconnect carry production traffic; tunnel or BGP drops partition workloads between on-prem and cloud.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (DX, VPN, TGW), Azure Monitor VPN/ExpressRoute metrics, `sourcetype=google:gcp:monitoring` (VPN/interconnect). **App/TA** (typical add-on context): `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:cloudwatch, mscs:azure:metrics, Microsoft.Network/expressRouteCircuits, google:gcp:monitoring. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **link_up** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resourceId, resource.labels.*, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where healthy=0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (link state), Table (circuit, tunnel, status), Map (peering location if geo fields exist).

## SPL

```spl
(index=aws sourcetype="aws:cloudwatch" (namespace="AWS/DX" OR namespace="AWS/VPN") (metric_name="ConnectionState" OR metric_name="TunnelState"))
 OR (index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Network/expressRouteCircuits" metric_name="BgpPeerStatus")
 OR (index=gcp sourcetype="google:gcp:monitoring" metric.type="vpn.googleapis.com/tunnel_established")
| eval link_up=case(metric_name="ConnectionState" AND maximum=1,1, metric_name="TunnelState" AND maximum=1,1, metric_name="BgpPeerStatus" AND average>0,1, metric.type="vpn.googleapis.com/tunnel_established" AND value>0,1,1=1,0)
| stats min(link_up) as healthy by resourceId, resource.labels.*, bin(_time, 5m)
| where healthy=0
```

## Visualization

Timeline (link state), Table (circuit, tunnel, status), Map (peering location if geo fields exist).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
