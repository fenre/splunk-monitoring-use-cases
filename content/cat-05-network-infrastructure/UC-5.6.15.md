<!-- AUTO-GENERATED from UC-5.6.15.json — DO NOT EDIT -->

---
id: "5.6.15"
title: "DHCP Pool Exhaustion and Address Allocation Issues (Meraki)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.15 · DHCP Pool Exhaustion and Address Allocation Issues (Meraki)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We help you know when address pools are filling up or leases look wrong, so new phones and laptops can still get on the network when they need to.*

---

## Description

Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.

## Value

Network operations teams proactively predict DHCP pool exhaustion dates across Meraki-managed sites, enabling planned pool expansion before users are impacted by address unavailability.

## Implementation

1. Configure Splunk Connect for Syslog (SC4S) to receive Meraki MX syslog over UDP/514 and forward to the meraki index. 2. In Meraki Dashboard enable syslog category 'Flows' and 'Events' (Network-wide -> General -> Reporting). 3. DHCP NAK and pool-exhaustion messages match type=events. 4. Also enable the Assurance Alerts input in Splunk_TA_cisco_meraki and create alert profiles in Meraki Dashboard for 'DHCP scope exhausted' and 'DHCP server failure'. 5. For proactive pool-size visibility you must scrape GET /networks/{networkId}/appliance/vlans (returns each VLAN's reservation/exclusion ranges) with a custom modular input — that endpoint is not yet polled by the TA.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side DHCP messages from the MX, plus Splunk_TA_cisco_meraki Assurance Alerts input (sourcetype=meraki:assurancealerts) for DHCP-related Dashboard alerts. NOTE: live DHCP pool size and remaining-lease counters are NOT exposed by either path; monitoring relies on NAK/exhaustion event detection..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure Splunk Connect for Syslog (SC4S) to receive Meraki MX syslog over UDP/514 and forward to the meraki index. 2. In Meraki Dashboard enable syslog category 'Flows' and 'Events' (Network-wide -> General -> Reporting). 3. DHCP NAK and pool-exhaustion messages match type=events. 4. Also enable the Assurance Alerts input in Splunk_TA_cisco_meraki and create alert profiles in Meraki Dashboard for 'DHCP scope exhausted' and 'DHCP server failure'. 5. For proactive pool-size visibility you mus…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki","cisco:meraki") (type=events OR type=flows)
    (DHCP_NACK OR DHCP_lease_alert OR pool_exhausted OR "no leases available")
    earliest=-24h
| stats count as nack_count,
        values(message) as messages,
        latest(_time) as last_seen
         by host, network_name, pool, vlan
| where nack_count > 0
| sort - nack_count
| append [
    search index=meraki sourcetype="meraki:assurancealerts"
        (title="*DHCP*" OR categoryType="appliance") earliest=-24h
    | stats count by scope.devices{}.serial, network.name, title
  ]
```

#### Understanding this SPL

**DHCP Pool Exhaustion and Address Allocation Issues (Meraki)** — Network operations teams proactively predict DHCP pool exhaustion dates across Meraki-managed sites, enabling planned pool expansion before users are impacted by address unavailability.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side DHCP messages from the MX, plus Splunk_TA_cisco_meraki Assurance Alerts input (sourcetype=meraki:assurancealerts) for DHCP-related Dashboard alerts. NOTE: live DHCP pool size and remaining-lease counters are NOT exposed by either path; monitoring relies on NAK/exhaustion event detection. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by host, network_name, pool, vlan** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where nack_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

**DHCP Pool Exhaustion and Address Allocation Issues (Meraki)** — Network operations teams proactively predict DHCP pool exhaustion dates across Meraki-managed sites, enabling planned pool expansion before users are impacted by address unavailability.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side DHCP messages from the MX, plus Splunk_TA_cisco_meraki Assurance Alerts input (sourcetype=meraki:assurancealerts) for DHCP-related Dashboard alerts. NOTE: live DHCP pool size and remaining-lease counters are NOT exposed by either path; monitoring relies on NAK/exhaustion event detection. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Sessions.DHCP` — enable acceleration for that model.
- Filters the current rows with `where count>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

## SPL

```spl
index=meraki sourcetype IN ("meraki","cisco:meraki") (type=events OR type=flows)
    (DHCP_NACK OR DHCP_lease_alert OR pool_exhausted OR "no leases available")
    earliest=-24h
| stats count as nack_count,
        values(message) as messages,
        latest(_time) as last_seen
         by host, network_name, pool, vlan
| where nack_count > 0
| sort - nack_count
| append [
    search index=meraki sourcetype="meraki:assurancealerts"
        (title="*DHCP*" OR categoryType="appliance") earliest=-24h
    | stats count by scope.devices{}.serial, network.name, title
  ]
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

DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.

## Known False Positives

DHCP pools may temporarily fill during BYOD events, conference Wi-Fi spikes, large office moves, or right after an IP scope change while devices renew in bulk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
