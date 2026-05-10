<!-- AUTO-GENERATED from UC-5.1.54.json — DO NOT EDIT -->

---
id: "5.1.54"
title: "Carrier Connection Health and Network Performance (Meraki MG)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.54 · Carrier Connection Health and Network Performance (Meraki MG)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch the cellular or backup-WAN link on your Meraki gateway and tell you when carrier or network errors pile up so you can fix the path before sites go dark.*

---

## Description

Monitors carrier connectivity and network performance metrics for backup internet links.

## Value

Operations teams monitor Meraki MG carrier connection health including connection type, latency, and loss to detect carrier network degradation and connection downgrades affecting WAN performance.

## Implementation

1. Configure SC4S for Meraki appliance syslog and enable the Appliance event log. 2. Use rex to extract the cellular state from the message. 3. Enable the Assurance Alerts input for cellularGateway-specific alerts (registration loss, SIM swap, APN failure). 4. For RSSI / data-plan / carrier visibility, integrate with the carrier portal API (AT&T Control Center, Verizon ThingSpace) — the Meraki TA does not expose those fields.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) for syslog from MX/MG cellular uplinks (Cellular connection up/down messages) and Splunk_TA_cisco_meraki Assurance Alerts input for cellular-specific alerts. NOTE: carrier name, RSSI, data plan usage and SIM status are NOT in syslog; the Dashboard API does not expose them either..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for Meraki appliance syslog and enable the Appliance event log. 2. Use rex to extract the cellular state from the message. 3. Enable the Assurance Alerts input for cellularGateway-specific alerts (registration loss, SIM swap, APN failure). 4. For RSSI / data-plan / carrier visibility, integrate with the carrier portal API (AT&T Control Center, Verizon ThingSpace) — the Meraki TA does not expose those fields.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("Cellular" OR "cellular" OR "carrier" OR "LTE" OR "5G")
    earliest=-24h
| rex "Cellular connection (?<state>up|down)"
| stats count as event_count,
        values(state) as states
         by host
| sort - event_count
| append [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h
    | stats count as alert_count, values(title) as alerts by deviceSerial, networkName
  ]
```

#### Understanding this SPL

**Carrier Connection Health and Network Performance (Meraki MG)** — Operations teams monitor Meraki MG carrier connection health including connection type, latency, and loss to detect carrier network degradation and connection downgrades affecting WAN performance.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) for syslog from MX/MG cellular uplinks (Cellular connection up/down messages) and Splunk_TA_cisco_meraki Assurance Alerts input for cellular-specific alerts. NOTE: carrier name, RSSI, data plan usage and SIM status are NOT in syslog; the Dashboard API does not expose them either. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Carrier health timeline; connection error table; network performance gauge.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("Cellular" OR "cellular" OR "carrier" OR "LTE" OR "5G")
    earliest=-24h
| rex "Cellular connection (?<state>up|down)"
| stats count as event_count,
        values(state) as states
         by host
| sort - event_count
| append [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h
    | stats count as alert_count, values(title) as alerts by deviceSerial, networkName
  ]
```

## Visualization

Carrier health timeline; connection error table; network performance gauge.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
