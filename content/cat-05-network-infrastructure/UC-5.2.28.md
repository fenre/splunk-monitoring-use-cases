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

1. Enable the Appliance VPN Statuses input in Splunk_TA_cisco_meraki — it requires the OAuth scope `sdwan:telemetry:read`. 2. Each event represents one MX appliance and carries a `merakiVpnPeers[]` array (NOT `vpnPeers[]`); each peer struct contains `{networkId, networkName, reachability, priority}` per Meraki API v1. 3. Use `spath path=merakiVpnPeers{} output=peer_arr` then `mvexpand peer_arr` then `spath input=peer_arr` to flatten one row per peer. Rename the outer hub identifiers first (the inner `networkId`/`networkName` are the peer's identity, NOT the hub's). 4. Trigger an alert when `reachability` transitions away from 'reachable'. 5. If you also need per-peer byte/utilization counters, enable the Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics) — those metrics are on a separate API endpoint (`getOrganizationApplianceVpnStats`). 6. For BGP-specific telemetry deploy a Cisco Catalyst SD-WAN or vManage integration; the Meraki MX appliance does not expose BGP state via the dashboard API.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses, daily) — calls GET /organizations/{orgId}/appliance/vpn/statuses. NOTE 1: Meraki MX does NOT speak BGP at the appliance level (it uses Auto VPN / SD-WAN dynamic path selection instead). This UC has been pivoted to monitor Auto VPN peer reachability — the closest semantically-equivalent control. For real BGP monitoring on the Cisco WAN tier, use the cat-5.x BGP UCs that target IOS XE / SD-WAN / NSO sourcetypes. NOTE 2: per the Meraki API v1 spec, the per-network peer array is `merakiVpnPeers{}` (NOT `vpnPeers{}`); each peer struct exposes `networkId`, `networkName`, `reachability`, `priority`. Per-peer byte counters are NOT on this endpoint — they live on the separate Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Appliance VPN Statuses input in Splunk_TA_cisco_meraki — it requires the OAuth scope `sdwan:telemetry:read`. 2. Each event represents one MX appliance and carries a `merakiVpnPeers[]` array (NOT `vpnPeers[]`); each peer struct contains `{networkId, networkName, reachability, priority}` per Meraki API v1. 3. Use `spath path=merakiVpnPeers{} output=peer_arr` then `mvexpand peer_arr` then `spath input=peer_arr` to flatten one row per peer. Rename the outer hub identifiers first (the i…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| rename networkId as hub_network_id, networkName as hub_network_name
| spath path=merakiVpnPeers{} output=peer_arr
| mvexpand peer_arr
| spath input=peer_arr
| stats latest(reachability) as reachability,
        latest(priority)     as priority
         by hub_network_id, hub_network_name, networkId, networkName
| where reachability != "reachable"
| sort hub_network_name
```

#### Understanding this SPL

**BGP Peering Status and Route Stability (Meraki MX)** — Operations teams monitor Meraki MX BGP peering state transitions and route stability, detecting peer failures and flapping that cause routing disruptions.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses, daily) — calls GET /organizations/{orgId}/appliance/vpn/statuses. NOTE 1: Meraki MX does NOT speak BGP at the appliance level (it uses Auto VPN / SD-WAN dynamic path selection instead). This UC has been pivoted to monitor Auto VPN peer reachability — the closest semantically-equivalent control. For real BGP monitoring on the Cisco WAN tier, use the cat-5.x BGP UCs that target IOS XE / SD-WAN / NSO sourcetypes. NOTE 2: per the Meraki API v1 spec, the per-network peer array is `merakiVpnPeers{}` (NOT `vpnPeers{}`); each peer struct exposes `networkId`, `networkName`, `reachability`, `priority`. Per-peer byte counters are NOT on this endpoint — they live on the separate Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:appliancesdwanstatuses. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:appliancesdwanstatuses", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Renames fields with `rename` for clarity or joins.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- `stats` rolls up events into metrics; results are split **by hub_network_id, hub_network_name, networkId, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where reachability != "reachable"` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: BGP peer status table; route change timeline; peering stability gauge.

## SPL

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| rename networkId as hub_network_id, networkName as hub_network_name
| spath path=merakiVpnPeers{} output=peer_arr
| mvexpand peer_arr
| spath input=peer_arr
| stats latest(reachability) as reachability,
        latest(priority)     as priority
         by hub_network_id, hub_network_name, networkId, networkName
| where reachability != "reachable"
| sort hub_network_name
```

## Visualization

BGP peer status table; route change timeline; peering stability gauge.

## Known False Positives

Reconvergence, ISPs, and lab peers can jolt route tables; confirm whether the next hop is still intended.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
