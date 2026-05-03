<!-- AUTO-GENERATED from UC-5.1.32.json — DO NOT EDIT -->

---
id: "5.1.32"
title: "Network Device End-of-Life Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.32 · Network Device End-of-Life Tracking

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you know early when something looks wrong with network device end-of-life tracking so the team can act before it grows into a bigger outage.*

---

## Description

Devices approaching EOL/EOS dates.

## Value

Operations teams track network device end-of-life and end-of-support dates, identifying devices that can no longer receive security patches and planning hardware refresh cycles.

## Implementation

Maintain device_inventory lookup (host, model) and eol_lookup (model, eol_date) from Cisco EOL/EOS bulletins. Run scheduled search or dashboard. Alert when days_to_eol < 180. Update lookups annually.

## Detailed Implementation

### Prerequisites
* Device end-of-life (EoL) and end-of-support (EoS) data. Data from vendor lifecycle databases (Cisco EoX API, Juniper), network management platforms, or custom inventory enrichment. Data in `index=network` or `index=cmdb`.
* EoL tracking: devices past End-of-Sale, End-of-Software-Maintenance, End-of-Security-Vulnerability-Support, or End-of-Support dates are at risk of unpatched vulnerabilities, no hardware replacement, and no TAC support.

### Step 1 — - Configure data collection
```
# Create or maintain EoL lookup
# eol_lifecycle.csv
# model, eos_date (end-of-sale), eosw_date (end-of-sw-maintenance),
# eovs_date (end-of-vulnerability-support), eol_date (end-of-support), replacement_model

# Cisco EoX API (automated):
# GET https://apix.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/WS-C3850-48T-S
```
Verify:
```spl
| inputlookup eol_lifecycle.csv | stats count by model
```

### Step 2 — - Create the search and alert

**Primary search -- EoL device inventory:**
```spl
index=network sourcetype="snmp:inventory" earliest=-2d
| rex field=sysDescr "(?i)(?<hw_model>[A-Z]+-?\d{4}\S*)"
| eval device=coalesce(host, device_name)
| eval model=coalesce(hw_model, hardware_model)
| lookup eol_lifecycle.csv model OUTPUT eos_date, eosw_date, eovs_date, eol_date, replacement_model
| where isnotnull(eol_date) OR isnotnull(eos_date)
| eval today=strftime(now(), "%Y-%m-%d")
| eval days_to_eol=if(isnotnull(eol_date), round((strptime(eol_date, "%Y-%m-%d") - now())/86400), null())
| eval severity=case(
    isnotnull(days_to_eol) AND days_to_eol < 0, "CRITICAL -- device past End-of-Life",
    isnotnull(eovs_date) AND today > eovs_date, "HIGH -- past End-of-Vulnerability-Support",
    isnotnull(eosw_date) AND today > eosw_date, "WARNING -- past End-of-SW-Maintenance",
    isnotnull(days_to_eol) AND days_to_eol < 365, "INFO -- End-of-Life within 12 months",
    1==1, "OK")
| where severity != "OK"
| table device, model, eos_date, eosw_date, eovs_date, eol_date, days_to_eol, replacement_model, severity
| sort severity, days_to_eol
```

### Step 3 — - Validate
(a) Verify lifecycle dates against vendor official announcements.
(b) Cross-reference with hardware asset management system.
(c) Confirm replacement models are approved and available.

### Step 4 — - Operationalize
Dashboard ("Network -- EoL Tracking"):
* Row 1 -- Single-value: "Past EoL", "Past EoVS (no security patches)", "EoL within 12 months".
* Row 2 -- EoL device inventory table.

Alert: Critical (device past EoVS): no security patches available.

### Step 5 — - Troubleshooting

* **Budget planning** -- Use EoL dates to plan hardware refresh budget cycles. Group devices by lifecycle stage for batch replacement.

* **Risk assessment** -- Devices past EoVS have no security patches. Compensating controls: network segmentation, enhanced monitoring, IPS protection.

* **Migration planning** -- Map replacement models and verify feature parity. Plan migration timeline based on EoL urgency.

## SPL

```spl
| inputlookup device_inventory
| lookup eol_lookup model OUTPUT eol_date eos_date
| eval days_to_eol=round((strptime(eol_date,"%Y-%m-%d")-now())/86400,0)
| where days_to_eol < 365 OR days_to_eol < 0
| table host model eol_date days_to_eol
| sort days_to_eol
```

## Visualization

Table (device, model, days to EOL), Single value (devices within 6 months), Gauge.

## Known False Positives

Version drift can reflect staged rollouts and golden-image lag between regions—match to your release calendar.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
