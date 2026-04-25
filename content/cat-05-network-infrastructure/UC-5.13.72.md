<!-- AUTO-GENERATED from UC-5.13.72.json — DO NOT EDIT -->

---
id: "5.13.72"
title: "Catalyst Center + Cyber Vision OT Device Correlation"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.13.72 · Catalyst Center + Cyber Vision OT Device Correlation

## Description

Correlates Catalyst Center network device health with Cyber Vision OT device inventory to identify network switches that serve operational technology environments and monitor their health priority.

## Value

Network devices serving OT environments have higher criticality — a switch failure affecting a manufacturing floor or SCADA system has safety and production implications beyond typical IT impact.

## Implementation

1. **TA 7538:** Enable Catalyst **devicehealth** (Intent API) to `index=catalyst` `cisco:dnac:devicehealth` with `managementIpAddress`, `deviceName`, `siteId`, `overallHealth` (UC-5.13.1).
2. **Cyber Vision in same TA:** Configure Cyber Vision account/inputs for **devices** data → `sourcetype=cisco:cybervision:devices` (often `index=cybervision` — align with the SPL or change the index in the subsearch).
3. **Join key:** Map Cyber Vision `gatewayIp` to Catalyst **management** IP of the L3/L2 gateway serving OT segments; adjust to `ip`/`deviceId` if your CV export uses a different key.
4. **Scope:** Use `siteId` in dashboards to separate IT-only from OT-adjacent sites after validation in lab.

## Detailed Implementation

Prerequisites
• UC-5.13.1 live for device health.
• Cyber Vision inventory flowing through TA 7538 as `cisco:cybervision:devices` (confirm index name and field names: `gatewayIp`, `deviceType`).

Step 1 — API / inputs (7538)
- **Catalyst Center:** `GET /dna/intent/api/v1/device-health` (poll via TA) — see Catalyst Center API documentation for version-specific paths.
- **Cyber Vision:** Enable the **devices** (or device inventory) input in the TA; verify in Splunk: `index=cybervision sourcetype="cisco:cybervision:devices" | head 5` and confirm `gatewayIp` matches your Catalyst management IPs or adjust join keys.

Step 2 — Correlation key hygiene
- If `gatewayIp` is not the same as Catalyst `managementIpAddress`, use a **lookup** CSV of gateway IP ↔ switch Mgmt IP, or `eval` a normalized IP from FQDN.
- For IPv6, ensure string formats match (no compressed vs full mismatch).

Step 3 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(overallHealth) as network_health by managementIpAddress, deviceName, siteId | join type=left managementIpAddress [search index=cybervision sourcetype="cisco:cybervision:devices" | stats count as ot_devices values(deviceType) as ot_types by gatewayIp | rename gatewayIp as managementIpAddress] | where isnotnull(ot_devices) | table deviceName managementIpAddress siteId network_health ot_devices ot_types | sort -ot_devices
```

Step 4 — Runbook
- **High `ot_devices`, low `network_health`:** treat as SEV for OT-impacting outage; loop in OT/ICS and physical plant.
- **OT types unexpected:** possible mis-attribution of gateway IP — revalidate the join in lab.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(overallHealth) as network_health by managementIpAddress, deviceName, siteId | join type=left managementIpAddress [search index=cybervision sourcetype="cisco:cybervision:devices" | stats count as ot_devices values(deviceType) as ot_types by gatewayIp | rename gatewayIp as managementIpAddress] | where isnotnull(ot_devices) | table deviceName managementIpAddress siteId network_health ot_devices ot_types | sort -ot_devices
```

## Visualization

Table: deviceName, managementIpAddress, siteId, network_health, ot_devices, ot_types; color network_health by band; bar chart of ot_devices per site.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
