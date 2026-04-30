<!-- AUTO-GENERATED from UC-5.13.72.json — DO NOT EDIT -->

---
id: "5.13.72"
title: "Catalyst Center + Cyber Vision OT Device Correlation"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.13.72 · Catalyst Center + Cyber Vision OT Device Correlation

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Inventory &middot; **Wave:** Run &middot; **Status:** Verified

*We connect the dots between the office network health and the factory floor equipment. When a network switch fails and the factory machines lose their connection, we show that the two events are related — so your team fixes the switch instead of investigating each machine separately, getting production back online faster.*

---

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

### Prerequisites
- UC-5.13.1 (Device Health) must be operational for the Catalyst Center campus health dimension.
- **Cisco Cyber Vision integration** must be configured — Cyber Vision sends OT/ICS network events via syslog to Splunk. Typical sourcetypes: `cisco:cybervision:events`, `cisco:cybervision:flows`. Data lands in a dedicated index (e.g., `index=ot` or `index=cybervision`).
- **Join field**: correlation between Catalyst Center and Cyber Vision is based on network segment or IP subnet. Cyber Vision monitors OT/ICS devices on specific VLANs/subnets; Catalyst Center manages the switches and APs those OT devices connect to. A `ot_subnet_to_site` lookup maps OT subnets to Catalyst Center `siteId` values.
- This UC bridges the IT/OT monitoring gap — when a Catalyst Center-managed switch degrades, it may affect OT devices monitored by Cyber Vision. Conversely, when Cyber Vision detects anomalous OT traffic, the root cause may be a misbehaving switch.

### Step 1 — Configure data collection
Catalyst Center: same `devicehealth` input as UC-5.13.1.

Cyber Vision: configure syslog export from Cyber Vision sensors to Splunk:
- Protocol: UDP/TCP syslog on port 514 or a custom port
- Format: CEF or native Cyber Vision JSON
- Sourcetype: `cisco:cybervision:events`
- Index: `ot` or `cybervision`

Build the OT-to-site mapping lookup:
```
ot_subnet,ot_vlan,siteId,siteName,ot_zone
10.100.0.0/24,100,a1b2c3-uuid,Plant-Floor-A,Manufacturing
10.100.1.0/24,101,d4e5f6-uuid,Plant-Floor-B,Assembly
```

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | stats count as catalyst_events
| appendcols [search index=ot OR index=cybervision earliest=-1h | stats count as cv_events]
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats avg(overallHealth) as switch_health dc(deviceName) as switches by siteId
| lookup ot_subnet_to_site siteId OUTPUT ot_zone
| where isnotnull(ot_zone)
| join type=left siteId
    [search index=ot sourcetype="cisco:cybervision:events" severity>=7
     | lookup ot_subnet_to_site src_subnet OUTPUT siteId
     | stats count as ot_alerts dc(src_ip) as ot_devices by siteId]
| eval ot_alerts=coalesce(ot_alerts, 0)
| eval correlation=case(
    switch_health < 50 AND ot_alerts > 0, "IT/OT CORRELATED — switch failure affecting OT devices",
    switch_health >= 80 AND ot_alerts > 5, "OT-only anomaly — investigate Cyber Vision",
    switch_health < 50 AND ot_alerts = 0, "IT-only — switch issue not affecting OT",
    1==1, "Both healthy")
| where correlation != "Both healthy"
| table siteId, ot_zone, switch_health, switches, ot_alerts, ot_devices, correlation
| sort switch_health
```

Why IT/OT correlation matters: in manufacturing and industrial environments, OT devices (PLCs, HMIs, sensors) connect to the IT network through Catalyst Center-managed switches. When a switch degrades, OT devices may lose connectivity — which in a manufacturing plant means production stops. The correlation distinguishes three scenarios:
- **IT/OT correlated**: switch failure is the root cause of OT alerts → fix the switch to restore production
- **OT-only**: switches are healthy but OT devices are misbehaving → investigate in Cyber Vision (possible rogue device, protocol anomaly, or OT-specific issue)
- **IT-only**: switch is unhealthy but OT is unaffected → standard switch remediation, no production impact

Why `severity >= 7` for Cyber Vision: focuses on high-severity OT events (protocol violations, unauthorised device communications, safety-related alerts). Low-severity events (flow statistics, normal heartbeats) would create noise.

Schedule: real-time dashboard panel for manufacturing NOC. Alert on "IT/OT CORRELATED" immediately — production impact requires fastest possible response.

### Step 3 — Validate
(a) During a known switch failure at an OT site, verify the search shows "IT/OT CORRELATED" with `switch_health < 50` AND `ot_alerts > 0`.
(b) Cross-reference Cyber Vision alerts with Catalyst Center device health for the same site and time window.
(c) Verify the `ot_subnet_to_site` lookup correctly maps OT network segments to Catalyst Center sites.
(d) Check that `severity >= 7` filters appropriately for your Cyber Vision severity scale.

### Step 4 — Operationalize
- Manufacturing NOC dashboard: real-time IT/OT correlation panel alongside UC-5.13.1 (device health) and Cyber Vision alerts.
- Alert: "IT/OT CORRELATED" → page plant operations AND network operations simultaneously. Both teams need to respond: network to fix the switch, operations to assess production impact.
- SLA: IT/OT correlated events affecting production require < 30 minute response time.

Runbook (owner: Plant Network Engineering):
1. "IT/OT CORRELATED": identify the affected switch (UC-5.13.1 filtered by site). Check power, uplink, and PoE status. The OT devices connected to this switch may have lost connectivity.
2. "OT-only anomaly": the switch infrastructure is healthy. The OT issue is likely a device-level problem (PLC firmware, protocol misconfiguration, rogue device). Investigate in Cyber Vision's device inventory and flow analysis.
3. "IT-only": the switch is degraded but OT traffic is unaffected (may be on a resilient ring or redundant path). Standard switch remediation applies but verify OT continues to operate.
4. For all production-impacting events: notify the plant operations team and log in the OT incident management system.

### Step 5 — Troubleshooting

- **No Cyber Vision data** — syslog export from Cyber Vision sensors is not configured, or the data is landing in a different index/sourcetype. Check `index=* sourcetype="*cybervision*" | stats count`.

- **`ot_subnet_to_site` lookup is empty** — create it manually. Work with the OT network architect to map OT VLANs/subnets to physical locations and Catalyst Center siteIds.

- **Join produces no results** — no sites have both Catalyst Center AND Cyber Vision data. Verify the lookup maps the correct siteId values.

- **All results show "Both healthy"** — either no degradation events occurred or the thresholds are too loose. Check individual metrics.

- **`severity` field not matching** — Cyber Vision severity scale may differ from expectations. Check `| stats values(severity)` on the Cyber Vision data.

- **OT alerts don't correlate with switch failures** — the OT issue may be on a different network segment than the affected switch. Check whether the OT devices are actually connected to the unhealthy switch (verify via VLAN/port mapping).

- **Want to add Modbus/OPC-UA protocol analysis** — extend the Cyber Vision subsearch with protocol-specific filters for deeper OT analysis.

- **Latency sensitivity** — OT protocols (Modbus, EtherNet/IP) are latency-sensitive. Even a switch with health=60 (above the < 50 threshold) may cause OT issues. Lower the threshold for OT-critical sites.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(overallHealth) as network_health by managementIpAddress, deviceName, siteId | join type=left managementIpAddress [search index=cybervision sourcetype="cisco:cybervision:devices" | stats count as ot_devices values(deviceType) as ot_types by gatewayIp | rename gatewayIp as managementIpAddress] | where isnotnull(ot_devices) | table deviceName managementIpAddress siteId network_health ot_devices ot_types | sort -ot_devices
```

## Visualization

Table: deviceName, managementIpAddress, siteId, network_health, ot_devices, ot_types; color network_health by band; bar chart of ot_devices per site.

## Known False Positives

**Gateway IP mismatch between Cisco Cyber Vision and Catalyst Center.** The correlation joins on `managementIpAddress`, but Cyber Vision may associate OT devices with a different gateway IP (e.g., an SVI or HSRP VIP) than the switch's management IP known to Catalyst Center. Distinguish by reviewing the join key: if Cyber Vision reports a VLAN SVI IP and Catalyst Center reports the physical management IP, the join will miss valid matches. This is a query design issue — consider joining on subnet or using a `catalyst_cybervision_ip_map` lookup to translate between Cyber Vision gateway IPs and Catalyst Center management IPs.

**VRF or shared SVI making OT device association ambiguous.** In networks with VRF-lite or multi-tenancy, the same switch may serve both IT and OT VRFs. Cyber Vision may report OT devices behind a VRF that Catalyst Center does not expose as a distinct entity. Distinguish by checking whether the affected switch serves multiple VRFs and whether OT devices are in a different VRF from the management interface. Suppress by scoping the correlation to specific VLANs or VRFs known to carry OT traffic.

**Firewall or segmentation between OT and IT networks obscuring the correlation.** A firewall between the OT segment and the campus network may mean that the switch Catalyst Center monitors is not the same device Cyber Vision sees as the OT gateway. Distinguish by tracing the network path: if a firewall sits between the Cyber Vision sensor and the Catalyst Center-managed switch, the correlation may not be meaningful. Suppress by limiting the correlation to sites where Cyber Vision sensors are directly connected to Catalyst Center-managed switches.

**Cyber Vision sensor offline or not reporting, showing no OT devices on a healthy switch.** If the Cyber Vision sensor is offline or misconfigured, the correlation will show switches with no associated OT devices, which may be incorrectly interpreted as switches not serving OT. Distinguish by verifying Cyber Vision sensor health independently: `index=cybervision sourcetype=cisco:cybervision:sensor | stats latest(_time) as last_seen by sensor_name`. Do not suppress — a silent Cyber Vision sensor is its own operational issue.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Device Health API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
