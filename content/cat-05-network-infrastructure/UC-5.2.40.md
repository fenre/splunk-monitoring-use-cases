---
id: "5.2.40"
title: "Meraki VPN Tunnel and Failover Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.40 · Meraki VPN Tunnel and Failover Health

## Description

Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.

## Value

Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.

## Implementation

Poll Meraki API for VPN tunnel status or ingest MX syslog for tunnel events. Alert when any tunnel is down. Track failover events for active/standby links.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API.
• Ensure the following data sources are available: `sourcetype=meraki:api` (VPN status), syslog from MX.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Meraki API for VPN tunnel status or ingest MX syslog for tunnel events. Alert when any tunnel is down. Track failover events for active/standby links.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" vpn_tunnel=*
| stats latest(tunnel_state) as state, latest(peer_ip) as peer by device_serial, tunnel_id
| where state != "up"
| table device_serial tunnel_id peer state _time
```

Understanding this SPL

**Meraki VPN Tunnel and Failover Health** — Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.

Documented **Data sources**: `sourcetype=meraki:api` (VPN status), syslog from MX. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_serial, tunnel_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where state != "up"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Meraki VPN Tunnel and Failover Health**): table device_serial tunnel_id peer state _time


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).

## SPL

```spl
index=cisco_network sourcetype="meraki:api" vpn_tunnel=*
| stats latest(tunnel_state) as state, latest(peer_ip) as peer by device_serial, tunnel_id
| where state != "up"
| table device_serial tunnel_id peer state _time
```

## Visualization

Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
