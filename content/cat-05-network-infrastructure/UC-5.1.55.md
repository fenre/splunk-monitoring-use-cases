<!-- AUTO-GENERATED from UC-5.1.55.json — DO NOT EDIT -->

---
id: "5.1.55"
title: "SIM Status and Plan Monitoring (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.55 · SIM Status and Plan Monitoring (Meraki MG)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know early when something looks wrong with sim status and plan monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.

## Value

Operations teams monitor Meraki MG SIM card status across slots, detecting deactivated, suspended, or error-state SIMs that compromise cellular WAN redundancy.

## Implementation

1. Enable Devices, Devices Availabilities, and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 2. The base inventory comes from meraki:devices (serial, model, firmware, lanIp, network). 3. Online/offline state comes from meraki:devicesavailabilities. 4. Cellular-specific events (SIM lost, registration failure, APN errors) appear in meraki:assurancealerts with deviceType=cellularGateway. 5. For raw SIM inventory and plan expiry data, integrate with your carrier billing portal (AT&T Control Center, Verizon ThingSpace) — those APIs are out of scope for the Meraki TA.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices, Devices Availabilities, and Assurance Alerts inputs. NOTE: SIM card status, ICCID, IMSI, plan expiry, and active carrier are NOT exposed by the Meraki Dashboard API. The closest signal available is the Assurance Alerts feed which fires on cellular registration loss, SIM swap, and APN failure..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices, Devices Availabilities, and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 2. The base inventory comes from meraki:devices (serial, model, firmware, lanIp, network). 3. Online/offline state comes from meraki:devicesavailabilities. 4. Cellular-specific events (SIM lost, registration failure, APN errors) appear in meraki:assurancealerts with deviceType=cellularGateway. 5. For raw SIM inventory and plan expiry data, integrate with your carrier billing portal (AT&T Control Cen…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devices" productType="cellularGateway"
| stats latest(serial) as serial, latest(model) as model, latest(firmware) as firmware,
        latest(lanIp) as lan_ip, latest(network.name) as network_name
         by name
| join type=left serial [
    search index=meraki sourcetype="meraki:devicesavailabilities" productType="cellularGateway"
    | stats latest(status) as status, latest(_time) as last_seen by serial
  ]
| join type=left serial [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h
    | stats values(title) as open_alerts, count as alert_count by deviceSerial
    | rename deviceSerial as serial
  ]
| eval status = coalesce(status, "unknown")
| sort - alert_count
```

#### Understanding this SPL

**SIM Status and Plan Monitoring (Meraki MG)** — Operations teams monitor Meraki MG SIM card status across slots, detecting deactivated, suspended, or error-state SIMs that compromise cellular WAN redundancy.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices, Devices Availabilities, and Assurance Alerts inputs. NOTE: SIM card status, ICCID, IMSI, plan expiry, and active carrier are NOT exposed by the Meraki Dashboard API. The closest signal available is the Assurance Alerts feed which fires on cellular registration loss, SIM swap, and APN failure. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devices. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devices". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: SIM status table; plan expiry countdown; renewal alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:devices" productType="cellularGateway"
| stats latest(serial) as serial, latest(model) as model, latest(firmware) as firmware,
        latest(lanIp) as lan_ip, latest(network.name) as network_name
         by name
| join type=left serial [
    search index=meraki sourcetype="meraki:devicesavailabilities" productType="cellularGateway"
    | stats latest(status) as status, latest(_time) as last_seen by serial
  ]
| join type=left serial [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h
    | stats values(title) as open_alerts, count as alert_count by deviceSerial
    | rename deviceSerial as serial
  ]
| eval status = coalesce(status, "unknown")
| sort - alert_count
```

## Visualization

SIM status table; plan expiry countdown; renewal alert dashboard.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
