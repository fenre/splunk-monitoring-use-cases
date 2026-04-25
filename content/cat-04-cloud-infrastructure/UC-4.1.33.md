<!-- AUTO-GENERATED from UC-4.1.33.json — DO NOT EDIT -->

---
id: "4.1.33"
title: "VPN Connection State and Tunnel Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.1.33 · VPN Connection State and Tunnel Status

## Description

VPN down breaks hybrid connectivity. Tunnel state monitoring ensures quick detection and failover to secondary tunnel or connection.

## Value

VPN down breaks hybrid connectivity. Tunnel state monitoring ensures quick detection and failover to secondary tunnel or connection.

## Implementation

TunnelState 1 = UP, 0 = DOWN. Alert when either tunnel is down. Monitor TunnelDataIn/Out for traffic; zero traffic may indicate routing or peer issue even if state is UP.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch VPN metrics (TunnelState, TunnelDataIn, TunnelDataOut).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
TunnelState 1 = UP, 0 = DOWN. Alert when either tunnel is down. Monitor TunnelDataIn/Out for traffic; zero traffic may indicate routing or peer issue even if state is UP.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/VPN" metric_name="TunnelState"
| where Average != 1
| table _time VpnId TunnelIpAddress Average
```

Understanding this SPL

**VPN Connection State and Tunnel Status** — VPN down breaks hybrid connectivity. Tunnel state monitoring ensures quick detection and failover to secondary tunnel or connection.

Documented **Data sources**: CloudWatch VPN metrics (TunnelState, TunnelDataIn, TunnelDataOut). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average != 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VPN Connection State and Tunnel Status**): table _time VpnId TunnelIpAddress Average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (tunnel up/down), Table (VPN, tunnel, state), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/VPN" metric_name="TunnelState"
| where Average != 1
| table _time VpnId TunnelIpAddress Average
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Status panel (tunnel up/down), Table (VPN, tunnel, state), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
