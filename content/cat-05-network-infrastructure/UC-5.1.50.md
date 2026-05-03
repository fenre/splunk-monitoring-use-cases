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

Periodically run cable tests on switch ports. Ingest results into syslog.

## Detailed Implementation

### Prerequisites
* Meraki MS cable test and port diagnostic data. Data in `index=meraki` from Dashboard API live tools. Key API: `POST /devices/{serial}/liveTools/cableTest` and results from `GET /devices/{serial}/liveTools/cableTest/{cableTestId}`.
* Meraki Dashboard live tools: cable test performs time-domain reflectometry (TDR) to check cable quality, length, and pair status. Results indicate: OK, open (broken), short (wires touching), or impedance mismatch.

### Step 1 — - Configure data collection
```
# Scripted input to run periodic cable tests on critical ports
[script:///opt/splunk/etc/apps/meraki_mon/bin/cable_test.py]
interval = 86400
sourcetype = meraki:cabletest
index = meraki
# Runs cable test API on configured critical ports
```
Verify:
```spl
index=meraki sourcetype="meraki:cabletest" earliest=-7d
| stats count by host, port
```

### Step 2 — - Create the search and alert

**Primary search -- Cable test results and port diagnostics:**
```spl
index=meraki sourcetype="meraki:cabletest" earliest=-7d
| eval device=coalesce(serial, host)
| eval port=coalesce(portId, port_id)
| lookup meraki_networks.csv serial AS device OUTPUT network_name
| eval cable_status=coalesce(status, result)
| eval pair_statuses=coalesce(pairs, pair_status)
| eval cable_length=tonumber(coalesce(lengthMeters, length))
| eval is_ok=if(match(cable_status, "(?i)ok|good|pass"), "YES", "NO")
| where is_ok="NO"
| eval issue=case(
    match(cable_status, "(?i)open"), "OPEN -- cable break detected",
    match(cable_status, "(?i)short"), "SHORT -- wire pairs shorted",
    match(cable_status, "(?i)impedance|mismatch"), "IMPEDANCE MISMATCH",
    match(cable_status, "(?i)crosstalk"), "CROSSTALK -- interference between pairs",
    1==1, "CABLE ISSUE: ".cable_status)
| table network_name, device, port, issue, cable_length, _time
| eval severity="WARNING -- cable issue on port ".port.": ".issue
| sort network_name, device, port
```

### Step 3 — - Validate
(a) Dashboard: Switch > Switch ports > Live tools > Cable test -- run on-demand test.
(b) Physical inspection of the cable and connectors.
(c) Compare cable length reported vs expected.

### Step 4 — - Operationalize
Dashboard ("Meraki MS -- Cable Diagnostics"):
* Row 1 -- Single-value: "Cable issues detected", "Ports tested".
* Row 2 -- Cable test results table.

### Step 5 — - Troubleshooting

* **Open cable** -- Break in the cable. Replace the patch cable. Check cable length reported to estimate break location.

* **Short** -- Wires touching inside the cable. Usually indicates damaged RJ-45 termination. Re-terminate or replace cable.

* **Impedance mismatch** -- Mixing cable categories (Cat5e/Cat6/Cat6a) or bad connector. Replace cable with consistent category throughout.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cable*" OR signature="*diagnostic*")
| stats count as test_count by switch_name, port_id, test_result
| where test_result="FAIL"
```

## Visualization

Table of failed cable tests; port detail with diagnostic results; failure timeline.

## Known False Positives

Cabling work and flaky patch panels can fail a test one run and pass the next. Re-run and compare with a cable certifier for chronic ports.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
