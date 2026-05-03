<!-- AUTO-GENERATED from UC-5.1.26.json — DO NOT EDIT -->

---
id: "5.1.26"
title: "Network Device Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.26 · Network Device Firmware Version Compliance

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you know early when something looks wrong with network device firmware version compliance so the team can act before it grows into a bigger outage.*

---

## Description

Devices running unapproved or EOL firmware versions.

## Value

Compliance teams track network device firmware versions against approved baselines, identifying devices running vulnerable or non-compliant software requiring security upgrades.

## Implementation

Poll SNMP sysDescr or ingest `show version` via scripted input. Create lookup table (ios_version, approved, eol_date) from vendor EOL/EOS bulletins. Alert on non-approved or past-EOL versions. Update lookup quarterly.

## Detailed Implementation

### Prerequisites
* Device firmware/software version data from SNMP or inventory systems. Data in `index=network` with SNMP (`sysDescr` OID .1.3.6.1.2.1.1.1.0) or Cisco DNA Center/network management platform exports. Key fields: `host`, `software_version`, `hardware_model`, `serial_number`.
* Firmware compliance: ensures all devices run approved software versions. Non-compliant firmware may contain security vulnerabilities, lack required features, or be unsupported by TAC. Required for regulatory compliance (PCI-DSS, HIPAA).

### Step 1 — - Configure data collection
```
# SNMP polling for version info
[snmp_inventory]
interval = 86400
sourcetype = snmp:inventory
index = network
# OID: sysDescr (.1.3.6.1.2.1.1.1.0) contains version info

# Approved firmware lookup
# firmware_compliance.csv
# model, approved_version, minimum_version, eol_date, notes
```
Verify:
```spl
index=network sourcetype="snmp:inventory" earliest=-2d
| rex field=sysDescr "Version\s+(?<sw_version>[\d\.\(\)A-Za-z]+)"
| stats latest(sw_version) by host
```

### Step 2 — - Create the search and alert

**Primary search -- Firmware version compliance:**
```spl
index=network sourcetype="snmp:inventory" earliest=-2d
| rex field=sysDescr "(?i)Version\s+(?<sw_version>[\d\.\(\)A-Za-z]+)"
| rex field=sysDescr "(?i)(?<hw_model>[A-Z]+-?\d{4}\S*)"
| eval device=coalesce(host, device_name)
| eval version=coalesce(sw_version, software_version)
| eval model=coalesce(hw_model, hardware_model)
| lookup firmware_compliance.csv model OUTPUT approved_version, minimum_version, eol_date
| eval compliant=if(version=approved_version, "YES", "NO")
| eval below_minimum=if(isnotnull(minimum_version) AND version < minimum_version, "YES", "NO")
| eval severity=case(
    below_minimum="YES", "CRITICAL -- firmware below minimum security baseline",
    compliant="NO" AND isnotnull(approved_version), "WARNING -- firmware not at approved version",
    isnull(approved_version), "INFO -- no compliance baseline defined for model",
    1==1, "OK")
| where severity != "OK"
| table device, model, version, approved_version, minimum_version, severity
| sort severity
```

### Step 3 — - Validate
(a) CLI: `show version` -- verify current firmware on device.
(b) Check vendor security advisories for known vulnerabilities in current version.
(c) Verify approved_version list is current with latest stable releases.

### Step 4 — - Operationalize
Dashboard ("Network -- Firmware Compliance"):
* Row 1 -- Single-value: "Compliant devices", "Non-compliant", "Below minimum".
* Row 2 -- Firmware compliance table.

Alert: Critical (device below minimum security baseline): schedule upgrade.

### Step 5 — - Troubleshooting

* **Upgrade planning** -- Schedule firmware upgrades during maintenance windows. Verify compatibility with current configuration. Test in lab first if possible.

* **Version not in compliance lookup** -- New model or version not yet classified. Add to `firmware_compliance.csv` after evaluating vendor release notes and security advisories.

* **EOL firmware** -- Device running end-of-life software with no security patches available. Plan hardware refresh or upgrade to supported release.

## SPL

```spl
index=network sourcetype=snmp:sysinfo OR sourcetype=cisco:ios:version
| rex field=_raw "Version (?<ios_version>\S+)" | rex field=sysDescr "Version (?<ios_version>\S+)"
| lookup firmware_compliance ios_version OUTPUT approved eol_date
| where approved!="yes" OR (eol_date!="" AND strptime(eol_date,"%Y-%m-%d")<now())
| table host ios_version approved eol_date
```

## Visualization

Table (device, version, status), Bar chart (version distribution), Single value (non-compliant count).

## Known False Positives

Version drift can reflect staged rollouts and golden-image lag between regions—match to your release calendar.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
