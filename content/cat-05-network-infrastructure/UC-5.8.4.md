<!-- AUTO-GENERATED from UC-5.8.4.json — DO NOT EDIT -->

---
id: "5.8.4"
title: "Network Device Inventory"
criticality: "low"
splunkPillar: "Security"
---

# UC-5.8.4 · Network Device Inventory

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Configuration

*We keep a clear list of what each network device is and where it lives, which helps with updates, security checks, and replacing boxes on time.*

---

## Description

Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.

## Value

Network operations teams maintain a unified device inventory across Catalyst Center, Meraki, and SNMP-discovered devices, detecting unmanaged shadow IT, tracking warranty status, and reconciling against the CMDB.

## Implementation

Poll SNMP sysDescr, sysName, sysLocation from all devices. Cross-reference with NMS discovery exports. Maintain inventory lookup for enrichment.

## Detailed Implementation

### Prerequisites
- Network device inventory data from one or more sources: (1) Catalyst Center API via TA_cisco_catalyst (`sourcetype=cisco:dnac:device`), (2) Meraki Dashboard API via Splunk_TA_cisco_meraki (`sourcetype=meraki:api:devices`), (3) SNMP polling via SC4SNMP or custom scripts (`sourcetype=snmp:device`), (4) NetBox/CMDB exports via scripted inputs or CSV uploads.
- Data in `index=network` (or platform-specific indexes). Key fields vary by source: `hostname`, `managementIpAddress`/`lanIp`, `platformId`/`model`, `softwareVersion`/`firmware`, `serialNumber`/`serial`, `role`/`device_type`, `location`/`siteNameHierarchy`/`network`.
- The goal is a unified device inventory across all management platforms. Build a `master_device_inventory.csv` lookup as the single source of truth: `serial,hostname,management_ip,model,vendor,software_version,site,role,purchase_date,warranty_expiry,owner`.

### Step 1 — Configure data collection
Verify device inventory from each source:
```spl
(index=catalyst sourcetype="cisco:dnac:device") OR (index=meraki sourcetype="meraki:api:devices") OR (index=snmp sourcetype="snmp:device") earliest=-1h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — Unified device inventory:**
```spl
(index=catalyst sourcetype="cisco:dnac:device") OR (index=meraki sourcetype="meraki:api:devices") OR (index=snmp sourcetype="snmp:device") earliest=-24h
| eval unified_hostname=coalesce(hostname, name, sysName)
| eval unified_ip=coalesce(managementIpAddress, lanIp, src)
| eval unified_model=coalesce(platformId, model, sysDescr)
| eval unified_version=coalesce(softwareVersion, firmware, sw_version)
| eval unified_serial=coalesce(serialNumber, serial, chassis_serial)
| eval source_platform=case(sourcetype="cisco:dnac:device", "Catalyst Center", sourcetype="meraki:api:devices", "Meraki Dashboard", sourcetype="snmp:device", "SNMP Discovery", 1==1, "Other")
| dedup unified_serial sortby -_time
| lookup master_device_inventory.csv serial as unified_serial OUTPUT site role purchase_date warranty_expiry owner
| eval in_cmdb=if(isnotnull(owner), "YES", "NO")
| eval warranty_status=case(isnotnull(warranty_expiry) AND strptime(warranty_expiry, "%Y-%m-%d") < now(), "EXPIRED", isnotnull(warranty_expiry) AND strptime(warranty_expiry, "%Y-%m-%d") < now() + 7776000, "EXPIRING_90D", isnotnull(warranty_expiry), "ACTIVE", 1==1, "UNKNOWN")
| table unified_hostname, unified_ip, unified_model, unified_version, unified_serial, source_platform, site, role, warranty_status, in_cmdb
| sort source_platform, site
```

#### Understanding this SPL: Multi-source device inventory is the foundation of network management. Without knowing what you have, you can't manage it. The `coalesce` functions normalize field names across platforms (Catalyst Center uses `hostname`, Meraki uses `name`, SNMP uses `sysName`). The CMDB lookup validation (`in_cmdb`) identifies shadow IT — devices discovered by monitoring but not tracked in the asset management system.

**Rogue/unmanaged device detection:**
```spl
(index=catalyst sourcetype="cisco:dnac:device") OR (index=meraki sourcetype="meraki:api:devices") OR (index=snmp sourcetype="snmp:device") earliest=-24h
| eval unified_serial=coalesce(serialNumber, serial, chassis_serial)
| dedup unified_serial
| lookup master_device_inventory.csv serial as unified_serial OUTPUT owner
| where isnull(owner)
| eval unified_hostname=coalesce(hostname, name, sysName)
| eval unified_ip=coalesce(managementIpAddress, lanIp, src)
| eval unified_model=coalesce(platformId, model)
| table unified_hostname, unified_ip, unified_model, unified_serial
| sort unified_ip
```

**Inventory change detection (new devices):**
```spl
(index=catalyst sourcetype="cisco:dnac:device") OR (index=meraki sourcetype="meraki:api:devices") earliest=-24h
| eval unified_serial=coalesce(serialNumber, serial)
| dedup unified_serial
| eval unified_hostname=coalesce(hostname, name)
| search NOT [| inputlookup master_device_inventory.csv | fields serial | rename serial as unified_serial]
| table _time, unified_hostname, unified_serial, sourcetype
```

### Step 3 — Validate
(a) Compare total device count against each management platform: Catalyst Center device count, Meraki Dashboard device count, SNMP polled devices.
(b) Spot-check 20 serial numbers: verify hostname, IP, model, and version match the source platform.
(c) Verify CMDB coverage: check that the `in_cmdb` ratio matches expectations (> 95% for managed networks).

### Step 4 — Operationalize
Dashboard ("Network Device Inventory"):
- Row 1 — Single-value tiles: "Total devices", "In CMDB", "Not in CMDB (shadow IT)", "Warranty expired".
- Row 2 — Device inventory table: hostname, IP, model, version, serial, source, site, warranty status.
- Row 3 — Rogue device alert: devices discovered but not in CMDB.
- Row 4 — Warranty expiration timeline: devices approaching warranty end.

Alerting:
- High (new device discovered not in CMDB): shadow IT detection — investigate.
- Warning (warranty expiring within 90 days): plan renewal or replacement.
- Info (weekly): full inventory report for asset management reconciliation.

### Step 5 — Troubleshooting

- **Duplicate devices across platforms** — A device managed by both Catalyst Center and discovered via SNMP appears twice. The `dedup unified_serial` handles this if serial numbers are consistent. If not, add IP-based dedup as fallback.

- **Serial number field empty** — Some devices don't report serial via SNMP. Use `sysName` + `managementIpAddress` as alternative unique key.

- **Version field inconsistent** — Catalyst Center reports full version strings (e.g., "17.09.04a"), Meraki reports firmware codes. Normalize with `eval` or lookup for version comparison.

## SPL

```spl
index=network sourcetype="snmp:system"
| stats latest(sysDescr) as description, latest(sysLocation) as location by host
| table host description location
```

## Visualization

Table (device, model, location, version), Pie chart (by model/vendor).

## Known False Positives

SNMP sysDescr and location strings can change in harmless upgrades; only alert when identity or site metadata shifts outside change records.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
