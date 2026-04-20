---
id: "4.2.47"
title: "Azure VPN Gateway Tunnel Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.2.47 · Azure VPN Gateway Tunnel Status

## Description

VPN gateway tunnel drops break hybrid connectivity between Azure and on-premises networks. Nearly every enterprise Azure customer relies on site-to-site VPN; tunnel status is a fundamental availability signal.

## Value

VPN gateway tunnel drops break hybrid connectivity between Azure and on-premises networks. Nearly every enterprise Azure customer relies on site-to-site VPN; tunnel status is a fundamental availability signal.

## Implementation

Collect Azure Monitor metrics for VPN Gateway resources. Monitor `TunnelAverageBandwidth` (drops to zero when tunnel is down), `TunnelEgressBytes`, `TunnelIngressBytes`, and `BGPPeerStatus`. Alert when tunnel bandwidth drops to zero or BGP peer status changes. Correlate with Azure Service Health events for planned maintenance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Network/vpnGateways).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for VPN Gateway resources. Monitor `TunnelAverageBandwidth` (drops to zero when tunnel is down), `TunnelEgressBytes`, `TunnelIngressBytes`, and `BGPPeerStatus`. Alert when tunnel bandwidth drops to zero or BGP peer status changes. Correlate with Azure Service Health events for planned maintenance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/vpngateways" metric_name="TunnelAverageBandwidth" OR metric_name="TunnelEgressBytes"
| timechart span=5m avg(average) as avg_bandwidth by resource_name
| where avg_bandwidth < 1
```

Understanding this SPL

**Azure VPN Gateway Tunnel Status** — VPN gateway tunnel drops break hybrid connectivity between Azure and on-premises networks. Nearly every enterprise Azure customer relies on site-to-site VPN; tunnel status is a fundamental availability signal.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Network/vpnGateways). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_bandwidth < 1` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure VPN Gateway Tunnel Status** — VPN gateway tunnel drops break hybrid connectivity between Azure and on-premises networks. Nearly every enterprise Azure customer relies on site-to-site VPN; tunnel status is a fundamental availability signal.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Network/vpnGateways). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (tunnel bandwidth over time), Single value (tunnel status up/down), Table (tunnels with status).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/vpngateways" metric_name="TunnelAverageBandwidth" OR metric_name="TunnelEgressBytes"
| timechart span=5m avg(average) as avg_bandwidth by resource_name
| where avg_bandwidth < 1
```

## CIM SPL

```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=5m | sort - agg_value
```

## Visualization

Line chart (tunnel bandwidth over time), Single value (tunnel status up/down), Table (tunnels with status).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
