<!-- AUTO-GENERATED from UC-5.2.26.json — DO NOT EDIT -->

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
• `stats` rolls up events into metrics; results are split **by user_id, src** so each row reflects one combination of those dimensions.
• Filters the current rows with `where connection_count > 10` — typically the threshold or rule expression for this monitoring goal.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Network_Sessions data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Network_Sessions model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm VPN paths, tunnel states, uplinks, and device names you expect there match the Splunk view.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Connected users timeline; session duration histogram; geography map of remote users.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Connected users timeline; session duration histogram; geography map of remote users.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
