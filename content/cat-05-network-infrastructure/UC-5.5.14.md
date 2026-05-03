<!-- AUTO-GENERATED from UC-5.5.14.json — DO NOT EDIT -->

---
id: "5.5.14"
title: "Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.14 · Firmware Version Compliance

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Running inconsistent or outdated software versions across the SD-WAN fabric creates security vulnerabilities and feature gaps. Compliance dashboards accelerate upgrade planning and audit readiness.

## Value

Network operations teams assess SD-WAN fleet firmware compliance against target versions, known CVEs, and end-of-life status, enabling prioritized upgrade scheduling and security risk mitigation.

## Implementation

Poll vManage device inventory for software versions and model types. Define a target version per device family. Report on compliance percentage. Alert when devices fall more than two minor versions behind the target. Use to prioritize upgrade batches by site criticality.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for device inventory. Data in `index=sdwan` with `sourcetype=cisco:sdwan:device`. Key fields: `system_ip`, `site_id`, `device_model`, `version` (firmware version), `personality`, `board_serial`, `certificate_status`, `config_status_message`.
- SD-WAN firmware compliance is critical for: (1) Security — older firmware may have known CVEs, (2) Feature parity — different versions support different features, (3) Stability — some versions have known bugs. Cisco publishes recommended firmware versions per device model.
- Build `sdwan_firmware_policy.csv` lookup: `device_model,target_version,min_acceptable_version,eol_versions,notes` (e.g., `C8300-1N4T,17.12.3,17.09.1,16.x|17.03.x,Upgrade before Q2`). This lookup drives compliance reporting.
- Also build `sdwan_cve_versions.csv` lookup: `version,cve_id,severity,description` listing known vulnerabilities by firmware version.

### Step 1 — Configure data collection
Verify device inventory data:
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-1h
| stats count by version, device_model, personality
| sort device_model, version
```

### Step 2 — Create the search and alert

**Primary search — Firmware compliance assessment:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-1h
| dedup system_ip
| lookup sdwan_firmware_policy.csv device_model OUTPUT target_version min_acceptable_version eol_versions
| eval on_target=if(version=target_version, "YES", "NO")
| eval above_minimum=if(version >= min_acceptable_version, "YES", "NO")
| eval is_eol=if(match(version, replace(eol_versions, "\|", "|")), "YES", "NO")
| lookup sdwan_cve_versions.csv version OUTPUT cve_id severity as cve_severity
| eval compliance=case(is_eol="YES", "EOL", isnotnull(cve_id) AND cve_severity="critical", "VULNERABLE", above_minimum="NO", "BELOW_MINIMUM", on_target="NO", "NEEDS_UPGRADE", 1==1, "COMPLIANT")
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| stats count by compliance, device_model, version
| sort compliance, device_model
```

#### Understanding this SPL: Firmware compliance goes beyond "is it the latest version." It evaluates multiple dimensions: is the version end-of-life (no more patches), does it have known critical CVEs, is it below the minimum acceptable version, and is it on the target version. This prioritized approach helps the network team focus upgrades on the most at-risk devices first.

**Device-level compliance detail:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-1h
| dedup system_ip
| lookup sdwan_firmware_policy.csv device_model OUTPUT target_version min_acceptable_version
| lookup sdwan_cve_versions.csv version OUTPUT cve_id cve_severity
| eval compliance=case(version=target_version, "COMPLIANT", isnotnull(cve_id), "VULNERABLE", version < min_acceptable_version, "BELOW_MIN", 1==1, "NEEDS_UPGRADE")
| where compliance!="COMPLIANT"
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| lookup sdwan_devices.csv system_ip OUTPUT hostname
| table hostname, site_name, tier, device_model, version, target_version, compliance, cve_id
| sort compliance, tier
```

**Firmware version distribution:**
```spl
index=sdwan sourcetype="cisco:sdwan:device" earliest=-1h personality IN ("vedge", "cedge")
| dedup system_ip
| stats count as device_count by version, device_model
| eventstats sum(device_count) as total_devices
| eval pct=round(100*device_count/total_devices, 1)
| sort device_model, version
```

### Step 3 — Validate
(a) In vManage: Maintenance > Software Management. Compare device versions with Splunk results.
(b) Cross-check `sdwan_firmware_policy.csv` against Cisco's current recommended release matrix.
(c) Verify CVE lookup: check cisco.com Security Advisories for the firmware versions in your fleet.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Firmware Compliance"):
- Row 1 — Single-value tiles: "Compliant devices", "Needs upgrade", "Vulnerable (CVE)", "EOL firmware".
- Row 2 — Compliance summary table: model, version, compliance status, device count.
- Row 3 — Vulnerable devices: hostname, site, current version, CVE details.
- Row 4 — Firmware distribution pie chart: version breakdown across the fleet.

Alerting:
- Critical (device running firmware with critical CVE): security risk — prioritize upgrade.
- High (device running EOL firmware): no patches available for new vulnerabilities.
- Warning (weekly): compliance report — % of fleet on target version.

### Step 5 — Troubleshooting

- **Version field empty or "unknown"** — The TA may not be parsing the version field correctly. Check raw events for the actual field name (could be `sw_version`, `image_version`, etc.).

- **Device shows wrong model** — vManage device inventory may not have been refreshed after a hardware replacement. Re-sync the device in vManage.

- **Compliance shows BELOW_MIN but device works fine** — Firmware below minimum may still function, but it's not supported for new features and may have unpatched security issues. The compliance check is a risk assessment, not a functionality check.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(version) as sw_version, latest(model) as model by hostname, system_ip, site_id
| eventstats count by sw_version
| eval target_version="17.12.04"
| eval compliant=if(sw_version=target_version,"yes","no")
| stats count as total, count(eval(compliant="yes")) as compliant_count by sw_version
| eval pct=round(compliant_count/total*100,1)
| sort -total
```

## Visualization

Pie chart (version distribution), Table (non-compliant devices), Single value (compliance percentage).

## Known False Positives

Staging upgrades, RMA replacements, and deferred maintenance windows can leave devices on non-target versions briefly; align alerts with your change calendar.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
