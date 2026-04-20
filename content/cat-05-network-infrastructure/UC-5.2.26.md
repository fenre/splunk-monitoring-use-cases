---
id: "5.2.26"
title: "Client VPN Connections and Remote Access Patterns (Meraki MX)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.26 · Client VPN Connections and Remote Access Patterns (Meraki MX)

## Description

Tracks client VPN usage patterns for remote workers and identifies problematic connections.

## Value

Tracks client VPN usage patterns for remote workers and identifies problematic connections.

## Implementation

Filter VPN logs for client connections. Track by user and source IP.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=vpn client_vpn=true`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Filter VPN logs for client connections. Track by user and source IP.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```

Understanding this SPL

**Client VPN Connections and Remote Access Patterns (Meraki MX)** — Tracks client VPN usage patterns for remote workers and identifies problematic connections.

Documented **Data sources**: `sourcetype=meraki type=vpn client_vpn=true`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by user_id, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where connection_count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Connected users timeline; session duration histogram; geography map of remote users.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```

## Visualization

Connected users timeline; session duration histogram; geography map of remote users.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
