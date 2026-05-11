<!-- AUTO-GENERATED from UC-5.2.26.json — DO NOT EDIT -->

---
id: "5.2.26"
title: "Client VPN Connections and Remote Access Patterns (Meraki MX)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.26 · Client VPN Connections and Remote Access Patterns (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count remote access use over time so you can plan capacity, spot odd login surges, and help people who are stuck at home or on the road.*

---

## Description

Tracks client VPN usage patterns for remote workers and identifies problematic connections.

## Value

Security teams monitor Meraki MX Client VPN connections and authentication failures, detecting brute force attempts and tracking remote access patterns.

## Implementation

Filter VPN logs for client connections. Track by user and source IP.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: `sourcetype=meraki type=events ("client_vpn_connect" OR "client_vpn_disconnect")` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Filter VPN logs for client connections. Track by user and source IP.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events ("client_vpn_connect" OR "client_vpn_disconnect")
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```

#### Understanding this SPL

**Client VPN Connections and Remote Access Patterns (Meraki MX)** — Security teams monitor Meraki MX Client VPN connections and authentication failures, detecting brute force attempts and tracking remote access patterns.

Documented **Data sources**: `sourcetype=meraki type=events ("client_vpn_connect" OR "client_vpn_disconnect")` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by user_id, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where connection_count > 10` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Client VPN Connections and Remote Access Patterns (Meraki MX)** — Security teams monitor Meraki MX Client VPN connections and authentication failures, detecting brute force attempts and tracking remote access patterns.

Documented **Data sources**: `sourcetype=meraki type=events ("client_vpn_connect" OR "client_vpn_disconnect")` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Sessions.All_Sessions` — enable acceleration for that model.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Connected users timeline; session duration histogram; geography map of remote users.

## SPL

```spl
index=meraki sourcetype="meraki" type=events ("client_vpn_connect" OR "client_vpn_disconnect")
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

## Known False Positives

Travel peaks, on-call surges, and class schedules can make remote access login counts swing widely.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
