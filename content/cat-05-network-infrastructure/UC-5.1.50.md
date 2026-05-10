<!-- AUTO-GENERATED from UC-5.1.50.json — DO NOT EDIT -->

---
id: "5.1.50"
title: "Cable Test Results and Port Diagnostics (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.50 · Cable Test Results and Port Diagnostics (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with cable test results and port diagnostics so the team can act before it grows into a bigger outage.*

---

## Description

Analyzes cable integrity test results to identify wiring faults before they cause outages.

## Value

Operations teams run and analyze Meraki MS cable test diagnostics (TDR), identifying cable breaks, shorts, and impedance mismatches causing port connectivity issues.

## Implementation

1. Enable both Assurance Alerts and Switch Ports Transceivers Readings History inputs in Splunk_TA_cisco_meraki. 2. The Transceivers input polls GET /organizations/{orgId}/switch/ports/transceivers/readings/history/bySwitch and returns intervals[] of {ts, temperature.celsius, power.{transmit,receive}.dbm, voltage.volts, currentBias.milliamps}. 3. Alert on rx power below -20 dBm or transceiver temperature above 70 °C. 4. For the interactive cable diagnostics (open/short/length) use Meraki Dashboard -> Switch -> Switches -> [serial] -> Tools -> Cable test.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input + Switch Ports Transceivers Readings History by Switch input (sourcetype=meraki:portstransceiversreadingshistorybyswitch, TA v3.2+, OAuth scope switch:telemetry:read). NOTE: The Meraki Dashboard 'Cable Test' tool result is NOT delivered via syslog or as a polled API — it is only available interactively in the Dashboard UI..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable both Assurance Alerts and Switch Ports Transceivers Readings History inputs in Splunk_TA_cisco_meraki. 2. The Transceivers input polls GET /organizations/{orgId}/switch/ports/transceivers/readings/history/bySwitch and returns intervals[] of {ts, temperature.celsius, power.{transmit,receive}.dbm, voltage.volts, currentBias.milliamps}. 3. Alert on rx power below -20 dBm or transceiver temperature above 70 °C. 4. For the interactive cable diagnostics (open/short/length) use Meraki Dashboa…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="switch"
    (title="*cable*" OR title="*physical*" OR title="*transceiver*"
     OR title="*SFP*")
    earliest=-7d
| stats count as alert_count,
        values(title) as cable_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
| append [
    search index=meraki sourcetype="meraki:portstransceiversreadingshistorybyswitch" earliest=-7d
    | spath path=intervals{} output=interval_arr
    | mvexpand interval_arr
    | spath input=interval_arr
    | stats avg(temperature.celsius) as avg_temp_c,
            min(power.transmit.dbm) as min_tx_dbm,
            min(power.receive.dbm) as min_rx_dbm
             by serial, portId
    | where min_rx_dbm < -20 OR avg_temp_c > 70
  ]
```

#### Understanding this SPL

**Cable Test Results and Port Diagnostics (Meraki MS)** — Operations teams run and analyze Meraki MS cable test diagnostics (TDR), identifying cable breaks, shorts, and impedance mismatches causing port connectivity issues.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input + Switch Ports Transceivers Readings History by Switch input (sourcetype=meraki:portstransceiversreadingshistorybyswitch, TA v3.2+, OAuth scope switch:telemetry:read). NOTE: The Meraki Dashboard 'Cable Test' tool result is NOT delivered via syslog or as a polled API — it is only available interactively in the Dashboard UI. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of failed cable tests; port detail with diagnostic results; failure timeline.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="switch"
    (title="*cable*" OR title="*physical*" OR title="*transceiver*"
     OR title="*SFP*")
    earliest=-7d
| stats count as alert_count,
        values(title) as cable_alerts,
        latest(severity) as severity
         by deviceSerial, deviceName, networkName
| sort - alert_count
| append [
    search index=meraki sourcetype="meraki:portstransceiversreadingshistorybyswitch" earliest=-7d
    | spath path=intervals{} output=interval_arr
    | mvexpand interval_arr
    | spath input=interval_arr
    | stats avg(temperature.celsius) as avg_temp_c,
            min(power.transmit.dbm) as min_tx_dbm,
            min(power.receive.dbm) as min_rx_dbm
             by serial, portId
    | where min_rx_dbm < -20 OR avg_temp_c > 70
  ]
```

## Visualization

Table of failed cable tests; port detail with diagnostic results; failure timeline.

## Known False Positives

Cabling work and flaky patch panels can fail a test one run and pass the next. Re-run and compare with a cable certifier for chronic ports.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
