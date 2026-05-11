<!-- AUTO-GENERATED from UC-5.6.13.json — DO NOT EDIT -->

---
id: "5.6.13"
title: "Failed DHCP Assignments and IP Pool Exhaustion (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.13 · Failed DHCP Assignments and IP Pool Exhaustion (Meraki)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.

## Value

Network operations teams monitoring Meraki environments detect DHCP assignment failures and pool exhaustion per site/subnet, enabling proactive pool expansion before users lose network connectivity.

## Implementation

1. Configure SC4S for Meraki MX/MS syslog and enable Appliance + Switch event logs in Meraki Dashboard. 2. 'dhcp no offers' indicates the DHCP server pool is exhausted or unreachable; 'DHCP NACK' indicates a lease conflict; 'Blocked DHCP' indicates DHCP guard caught a rogue server. 3. Threshold per AP/switch and trigger Splunk alerts on sustained exhaustion. 4. For real-time pool sizing use GET /networks/{networkId}/appliance/vlans (VLAN reservation/exclusion ranges) with a custom modular input — that endpoint is not yet polled by the TA.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MX/MS syslog. DHCP events appear as type=events with message bodies 'dhcp no offers for mac <mac>', 'dhcp lease of ip <ip> from server mac <mac> for client mac <mac>', and 'Blocked DHCP server response from <mac> on VLAN <id>'..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for Meraki MX/MS syslog and enable Appliance + Switch event logs in Meraki Dashboard. 2. 'dhcp no offers' indicates the DHCP server pool is exhausted or unreachable; 'DHCP NACK' indicates a lease conflict; 'Blocked DHCP' indicates DHCP guard caught a rogue server. 3. Threshold per AP/switch and trigger Splunk alerts on sustained exhaustion. 4. For real-time pool sizing use GET /networks/{networkId}/appliance/vlans (VLAN reservation/exclusion ranges) with a custom modular input …

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("dhcp no offers" OR "dhcp lease" OR "DHCP NACK" OR "Blocked DHCP")
    earliest=-24h
| rex "for mac (?<client_mac>[0-9A-Fa-f:]+)"
| rex "host = (?<dhcp_server>[\d\.]+)"
| eval failure_type = case(
    match(_raw, "dhcp no offers"), "no_offers",
    match(_raw, "DHCP NACK"), "nack",
    match(_raw, "Blocked DHCP"), "blocked_rogue",
    1=1, "lease")
| stats count as failure_count,
        values(client_mac) as failed_clients,
        values(dhcp_server) as servers
         by host, failure_type
| where failure_type != "lease" AND failure_count > 5
| sort - failure_count
```

#### Understanding this SPL

**Failed DHCP Assignments and IP Pool Exhaustion (Meraki)** — Network operations teams monitoring Meraki environments detect DHCP assignment failures and pool exhaustion per site/subnet, enabling proactive pool expansion before users lose network connectivity.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MX/MS syslog. DHCP events appear as type=events with message bodies 'dhcp no offers for mac <mac>', 'dhcp lease of ip <ip> from server mac <mac> for client mac <mac>', and 'Blocked DHCP server response from <mac> on VLAN <id>'. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `eval` defines or adjusts **failure_type** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by host, failure_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where failure_type != "lease" AND failure_count > 5` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

**Failed DHCP Assignments and IP Pool Exhaustion (Meraki)** — Network operations teams monitoring Meraki environments detect DHCP assignment failures and pool exhaustion per site/subnet, enabling proactive pool expansion before users lose network connectivity.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MX/MS syslog. DHCP events appear as type=events with message bodies 'dhcp no offers for mac <mac>', 'dhcp lease of ip <ip> from server mac <mac> for client mac <mac>', and 'Blocked DHCP server response from <mac> on VLAN <id>'. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Sessions.DHCP` — enable acceleration for that model.
- Filters the current rows with `where count>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("dhcp no offers" OR "dhcp lease" OR "DHCP NACK" OR "Blocked DHCP")
    earliest=-24h
| rex "for mac (?<client_mac>[0-9A-Fa-f:]+)"
| rex "host = (?<dhcp_server>[\d\.]+)"
| eval failure_type = case(
    match(_raw, "dhcp no offers"), "no_offers",
    match(_raw, "DHCP NACK"), "nack",
    match(_raw, "Blocked DHCP"), "blocked_rogue",
    1=1, "lease")
| stats count as failure_count,
        values(client_mac) as failed_clients,
        values(dhcp_server) as servers
         by host, failure_type
| where failure_type != "lease" AND failure_count > 5
| sort - failure_count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

## Visualization

Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
