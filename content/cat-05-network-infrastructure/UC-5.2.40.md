<!-- AUTO-GENERATED from UC-5.2.40.json — DO NOT EDIT -->

---
id: "5.2.40"
title: "Meraki VPN Tunnel and Failover Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.40 · Meraki VPN Tunnel and Failover Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We keep watch on tunnel and failover state from the cloud dashboard data so a down path is not something you only hear about in a meeting.*

---

## Description

Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.

## Value

NOC teams monitor Meraki MX site-to-site and client VPN tunnel status, detecting tunnel failures and flapping to maintain inter-site connectivity and remote user access.

## Implementation

1. Enable both Appliance VPN Statuses and Appliance VPN Stats inputs in Splunk_TA_cisco_meraki. 2. The Statuses input returns one event per network with an uplinks[] array containing {interface, status, ip, publicIp, gateway} per WAN port and a vpnPeers[] array of remote MX statuses. 3. The Stats input returns per-pair statistics with senderUplink, receiverUplink, latencyMs, jitterMs, lossPercent, mosScore. 4. Tune thresholds (>5% loss, >500ms latency, >50ms jitter) to your SLA. 5. For live tunnel-down events, configure a Meraki alert profile on 'site to site VPN connectivity change' and ingest via the Webhook Logs (HEC) input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API.
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses, daily, OAuth scope sdwan:telemetry:read) and Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics, daily). Both polled from /organizations/{orgId}/appliance/vpn/statuses and /vpn/stats..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable both Appliance VPN Statuses and Appliance VPN Stats inputs in Splunk_TA_cisco_meraki. 2. The Statuses input returns one event per network with an uplinks[] array containing {interface, status, ip, publicIp, gateway} per WAN port and a vpnPeers[] array of remote MX statuses. 3. The Stats input returns per-pair statistics with senderUplink, receiverUplink, latencyMs, jitterMs, lossPercent, mosScore. 4. Tune thresholds (>5% loss, >500ms latency, >50ms jitter) to your SLA. 5. For live tunn…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| spath path=uplinks{} output=uplink_arr
| mvexpand uplink_arr
| spath input=uplink_arr
| stats latest(status) as state,
        latest(ip) as uplink_ip,
        latest(publicIp) as public_ip,
        latest(gateway) as gateway
         by networkId, networkName, interface
| where state != "active" AND state != "ready"
| append [
    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-1h
    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss,
            avg(jitterMs) as avg_jitter, last(receiverUplink) as receiver_uplink
             by networkId, networkName, senderUplink
    | where avg_loss>5 OR avg_latency>500 OR avg_jitter>50
  ]
| sort networkName
```

#### Understanding this SPL

**Meraki VPN Tunnel and Failover Health** — NOC teams monitor Meraki MX site-to-site and client VPN tunnel status, detecting tunnel failures and flapping to maintain inter-site connectivity and remote user access.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses, daily, OAuth scope sdwan:telemetry:read) and Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics, daily). Both polled from /organizations/{orgId}/appliance/vpn/statuses and /vpn/stats. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:appliancesdwanstatuses. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:appliancesdwanstatuses", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- `stats` rolls up events into metrics; results are split **by networkId, networkName, interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where state != "active" AND state != "ready"` — typically the threshold or rule expression for this monitoring goal.
- Appends rows from a subsearch with `append`.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Meraki VPN Tunnel and Failover Health** — NOC teams monitor Meraki MX site-to-site and client VPN tunnel status, detecting tunnel failures and flapping to maintain inter-site connectivity and remote user access.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input (sourcetype=meraki:appliancesdwanstatuses, daily, OAuth scope sdwan:telemetry:read) and Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics, daily). Both polled from /organizations/{orgId}/appliance/vpn/statuses and /vpn/stats. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Sessions.All_Sessions` — enable acceleration for that model.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).

## SPL

```spl
index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h
| spath path=uplinks{} output=uplink_arr
| mvexpand uplink_arr
| spath input=uplink_arr
| stats latest(status) as state,
        latest(ip) as uplink_ip,
        latest(publicIp) as public_ip,
        latest(gateway) as gateway
         by networkId, networkName, interface
| where state != "active" AND state != "ready"
| append [
    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-1h
    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss,
            avg(jitterMs) as avg_jitter, last(receiverUplink) as receiver_uplink
             by networkId, networkName, senderUplink
    | where avg_loss>5 OR avg_latency>500 OR avg_jitter>50
  ]
| sort networkName
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).

## Known False Positives

Tunnels, peers, and monitored paths can flap during routine network work; use duration to separate noise from outage.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
