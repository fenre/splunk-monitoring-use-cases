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

Query MG API for SIM status and plan expiry. Alert before expiration.

## Detailed Implementation

### Prerequisites
* Meraki MG SIM status data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:cellular:sim` or `sourcetype=meraki:api:device:status`. Key fields: `sim.slot`, `sim.status`, `sim.iccid`, `sim.carrier`, `sim.apn`.
* Meraki MG supports dual SIM for carrier redundancy. SIM issues (deactivated, expired, data exhausted) cause connectivity loss. Monitoring SIM status ensures cellular failover readiness.

### Step 1 — - Configure data collection
```
[meraki_mg_sim]
interval = 3600
sourcetype = meraki:api:cellular:sim
index = meraki
# API: GET /devices/{serial}/cellular/sims
```
Verify:
```spl
index=meraki sourcetype="meraki:api:cellular:sim" earliest=-7d
| stats latest(sim_status) by host, sim_slot
```

### Step 2 — - Create the search and alert

**Primary search -- SIM status and plan monitoring:**
```spl
index=meraki sourcetype="meraki:api:cellular:sim" earliest=-7d
| eval device=coalesce(serial, host)
| eval slot=coalesce(sim_slot, slot)
| eval sim_status=coalesce(sim_status, status)
| eval iccid=coalesce(sim_iccid, iccid)
| eval carrier=coalesce(sim_carrier, carrier, provider)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| dedup device, slot sortby -_time
| eval severity=case(
    match(sim_status, "(?i)not.*detect|absent|empty"), "WARNING -- SIM ".slot.": not detected",
    match(sim_status, "(?i)deactivat|suspend|disabled"), "CRITICAL -- SIM ".slot.": deactivated/suspended",
    match(sim_status, "(?i)error|fail"), "CRITICAL -- SIM ".slot.": error state",
    match(sim_status, "(?i)active|ready|connected"), "OK",
    1==1, "INFO -- SIM ".slot.": ".sim_status)
| where severity != "OK"
| table network_name, device, site_name, slot, sim_status, carrier, iccid, severity
| sort severity
```

### Step 3 — - Validate
(a) Dashboard: Cellular gateway > SIM management -- check SIM status.
(b) Verify SIM ICCID matches carrier records.
(c) Contact carrier to verify plan is active and data cap not reached.

### Step 4 — - Operationalize
Dashboard ("Meraki MG -- SIM Status"):
* Row 1 -- Single-value: "Active SIMs", "Problem SIMs".
* Row 2 -- SIM status table.

Alert: Critical (SIM deactivated or error): cellular connectivity at risk.

### Step 5 — - Troubleshooting

* **SIM not detected** -- Check: (1) SIM inserted correctly, (2) SIM orientation, (3) SIM tray not damaged, (4) SIM card not physically damaged. Re-seat SIM.

* **SIM deactivated** -- Carrier may have deactivated due to: non-payment, suspicious activity, or data plan expiry. Contact carrier with ICCID to resolve.

* **Dual SIM failover not working** -- Verify secondary SIM is configured as failover in Dashboard. Check SIM carrier compatibility with MG model. Ensure APN is configured correctly.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats latest(sim_status) as sim_status, latest(plan_expiry) as expiry_date by gateway_id, sim_id
| eval days_until_expire=round((strptime(plan_expiry, "%Y-%m-%d")-now())/86400, 0)
| where sim_status != "active" OR days_until_expire < 30
```

## Visualization

SIM status table; plan expiry countdown; renewal alert dashboard.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
