<!-- AUTO-GENERATED from UC-5.2.37.json — DO NOT EDIT -->

---
id: "5.2.37"
title: "Auto VPN Path Changes and Tunnel Switching (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.37 · Auto VPN Path Changes and Tunnel Switching (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We log automatic tunnel and path changes so the team can tell normal reroutes from a misconfiguration that strands users.*

---

## Description

Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.

## Value

Network engineers track Meraki Auto VPN path changes and tunnel switching to identify SD-WAN path instability and optimize uplink selection thresholds.

## Implementation

1. Configure SC4S for MX syslog and enable VPN logging in Meraki Dashboard. 2. Auto VPN tunnel state changes are emitted as type=events with structured type=vpn_connectivity_change fields. 3. Use rex to extract peer / peer_ident / connectivity. 4. Sustained flapping (path_change_count > 3 in 24h) usually indicates underlay quality issues; correlate with the API-side meraki:appliancesdwanstatistics input for the WAN-link metrics during the same window.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) for Auto VPN connectivity_change events as type=events with the structured 'type=vpn_connectivity_change vpn_type=... peer_contact=... peer_ident=... connectivity=...' payload, plus Splunk_TA_cisco_meraki Appliance VPN Stats input for tunnel performance context..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog and enable VPN logging in Meraki Dashboard. 2. Auto VPN tunnel state changes are emitted as type=events with structured type=vpn_connectivity_change fields. 3. Use rex to extract peer / peer_ident / connectivity. 4. Sustained flapping (path_change_count > 3 in 24h) usually indicates underlay quality issues; correlate with the API-side meraki:appliancesdwanstatistics input for the WAN-link metrics during the same window.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    "type=vpn_connectivity_change"
    earliest=-24h
| rex "peer_contact='(?<peer>[\d\.:]+)'"
| rex "peer_ident='(?<peer_ident>[a-f0-9]+)'"
| rex "connectivity='(?<connectivity>true|false)'"
| rex "vpn_type='(?<vpn_type>[\w\-]+)'"
| stats count as path_change_count,
        values(connectivity) as states,
        latest(_time) as last_change
         by host, peer, vpn_type
| where path_change_count > 3
| sort - path_change_count
| append [
    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-24h
    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss
             by senderUplink, receiverUplink
  ]
```

#### Understanding this SPL

**Auto VPN Path Changes and Tunnel Switching (Meraki MX)** — Network engineers track Meraki Auto VPN path changes and tunnel switching to identify SD-WAN path instability and optimize uplink selection thresholds.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) for Auto VPN connectivity_change events as type=events with the structured 'type=vpn_connectivity_change vpn_type=... peer_contact=... peer_ident=... connectivity=...' payload, plus Splunk_TA_cisco_meraki Appliance VPN Stats input for tunnel performance context. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, peer, vpn_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where path_change_count > 3` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Path change timeline; tunnel path change distribution; convergence analysis.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    "type=vpn_connectivity_change"
    earliest=-24h
| rex "peer_contact='(?<peer>[\d\.:]+)'"
| rex "peer_ident='(?<peer_ident>[a-f0-9]+)'"
| rex "connectivity='(?<connectivity>true|false)'"
| rex "vpn_type='(?<vpn_type>[\w\-]+)'"
| stats count as path_change_count,
        values(connectivity) as states,
        latest(_time) as last_change
         by host, peer, vpn_type
| where path_change_count > 3
| sort - path_change_count
| append [
    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-24h
    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss
             by senderUplink, receiverUplink
  ]
```

## Visualization

Path change timeline; tunnel path change distribution; convergence analysis.

## Known False Positives

Route optimization and ISP issues can re-path tunnels; verify impact before calling it a security problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
