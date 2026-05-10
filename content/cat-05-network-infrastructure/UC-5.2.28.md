<!-- AUTO-GENERATED from UC-5.2.28.json — DO NOT EDIT -->

---
id: "5.2.28"
title: "BGP Peering Status and Route Stability (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.28 · BGP Peering Status and Route Stability (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch border gateway and route health messages on the same gear so a bad neighbor or wobbly path is easier to spot early.*

---

## Description

Ensures BGP peers remain established and routing remains stable for multi-ISP designs.

## Value

Operations teams monitor Meraki MX BGP peering state transitions and route stability, detecting peer failures and flapping that cause routing disruptions.

## Implementation

1. Enable the Appliance VPN Statuses input in Splunk_TA_cisco_meraki. 2. Each event carries a vpnPeers[] array of {peerNetworkId, peerNetworkName, reachability, usage.{sent,received}}. 3. Trigger an alert when reachability transitions away from 'reachable'. 4. For BGP-specific telemetry deploy a Cisco Catalyst SD-WAN or vManage integration; Meraki MX is not a BGP speaker.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses). NOTE: Meraki MX does NOT speak BGP (it uses Auto VPN / SD-WAN dynamic path selection instead). This UC has been pivoted to monitor Auto VPN peer reachability — the closest semantically-equivalent control. For real BGP monitoring on the Cisco WAN tier, use cat-5.x BGP UCs that target IOS XE / SD-WAN / NSO sourcetypes..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Appliance VPN Statuses input in Splunk_TA_cisco_meraki. 2. Each event carries a vpnPeers[] array of {peerNetworkId, peerNetworkName, reachability, usage.{sent,received}}. 3. Trigger an alert when reachability transitions away from 'reachable'. 4. For BGP-specific telemetry deploy a Cisco Catalyst SD-WAN or vManage integration; Meraki MX is not a BGP speaker.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| spath path=vpnPeers{} output=peer_arr
| mvexpand peer_arr
| spath input=peer_arr
| stats latest(reachability) as reachability,
        latest(usage.sent) as bytes_sent,
        latest(usage.received) as bytes_received
         by networkId, networkName, peerNetworkId, peerNetworkName
| where reachability != "reachable"
| sort networkName
```

#### Understanding this SPL

**BGP Peering Status and Route Stability (Meraki MX)** — Operations teams monitor Meraki MX BGP peering state transitions and route stability, detecting peer failures and flapping that cause routing disruptions.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses). NOTE: Meraki MX does NOT speak BGP (it uses Auto VPN / SD-WAN dynamic path selection instead). This UC has been pivoted to monitor Auto VPN peer reachability — the closest semantically-equivalent control. For real BGP monitoring on the Cisco WAN tier, use cat-5.x BGP UCs that target IOS XE / SD-WAN / NSO sourcetypes. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:appliancesdwanstatuses. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:appliancesdwanstatuses", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- `stats` rolls up events into metrics; results are split **by networkId, networkName, peerNetworkId, peerNetworkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where reachability != "reachable"` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: BGP peer status table; route change timeline; peering stability gauge.

## SPL

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| spath path=vpnPeers{} output=peer_arr
| mvexpand peer_arr
| spath input=peer_arr
| stats latest(reachability) as reachability,
        latest(usage.sent) as bytes_sent,
        latest(usage.received) as bytes_received
         by networkId, networkName, peerNetworkId, peerNetworkName
| where reachability != "reachable"
| sort networkName
```

## Visualization

BGP peer status table; route change timeline; peering stability gauge.

## Known False Positives

Reconvergence, ISPs, and lab peers can jolt route tables; confirm whether the next hop is still intended.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
