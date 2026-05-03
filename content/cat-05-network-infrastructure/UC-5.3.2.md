<!-- AUTO-GENERATED from UC-5.3.2.json — DO NOT EDIT -->

---
id: "5.3.2"
title: "Virtual Server Availability (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.2 · Virtual Server Availability (F5 BIG-IP)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch whether virtual services are up or disabled on the same box so a quiet listener or a bad profile does not go unnoticed in change week.*

---

## Description

VIP down = application unreachable. Direct service impact.

## Value

Application delivery teams track F5 BIG-IP virtual server availability across the fleet, detecting unavailable VIPs and unstable state changes that indicate service disruptions or pool-level failures.

## Implementation

Forward syslog. Monitor VIP status via SNMP or iControl REST. Alert on any state change away from "available".

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680) installed. F5 BIG-IP LTM syslog in `index=network` with `sourcetype=f5:bigip:syslog`. Key messages: virtual server state changes ("Virtual ... has become available/unavailable"), SNMP traps for VS status.
* Optionally, poll F5 iControl REST API (`/mgmt/tm/ltm/virtual/stats`) for real-time VS status. Ingest via HEC as `sourcetype=f5:bigip:api`.
* Create `f5_vip_inventory.csv` lookup: `virtual_server`, `vip_address`, `application`, `owner`, `tier`, `expected_state` (enabled/disabled).

### Step 1 — - Configure data collection
Verify virtual server status data:
```spl
index=network sourcetype="f5:bigip:syslog" ("virtual" AND ("available" OR "unavailable" OR "offline" OR "enabled" OR "disabled")) earliest=-24h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Virtual server availability monitoring:**
```spl
index=network sourcetype="f5:bigip:syslog" ("virtual" AND ("available" OR "unavailable" OR "offline" OR "unknown")) earliest=-4h
| rex "Virtual (?<virtual_server>\S+) has become (?<vs_status>\w+)"
| where isnotnull(virtual_server)
| stats latest(vs_status) as current_status latest(_time) as last_change count as state_changes by host, virtual_server
| lookup f5_vip_inventory.csv virtual_server OUTPUT application, owner, tier, vip_address
| eval is_down=if(match(lower(current_status), "unavailable|offline|unknown"), 1, 0)
| eval severity=case(is_down=1 AND tier="prod", "CRITICAL", is_down=1, "HIGH", state_changes > 3, "WARNING -- unstable", 1==1, "OK")
| where is_down=1 OR state_changes > 3
| table host, virtual_server, vip_address, application, tier, current_status, last_change, state_changes, severity
| sort severity, -last_change
```

**VIP fleet health summary:**
```spl
index=network sourcetype="f5:bigip:syslog" ("virtual" AND ("available" OR "unavailable")) earliest=-4h
| rex "Virtual (?<virtual_server>\S+) has become (?<vs_status>\w+)"
| stats latest(vs_status) as status by host, virtual_server
| eval is_up=if(match(lower(status), "available"), 1, 0)
| stats sum(is_up) as up count as total by host
| eval availability_pct=round(100*up/total, 1)
| sort availability_pct
```

### Step 3 — - Validate
(a) In tmsh: `show ltm virtual` -- compare VS status with Splunk.
(b) Disable a test VS: `tmsh modify ltm virtual <vs> disabled` -- verify the "unavailable" event appears.
(c) Re-enable and verify recovery.

### Step 4 — - Operationalize
Dashboard ("F5 -- Virtual Server Availability"):
* Row 1 -- Single-value: "Total VIPs", "Unavailable", "Fleet availability %", "Unstable VIPs".
* Row 2 -- Down/unstable VIP detail table.
* Row 3 -- Per-F5 fleet health summary.

Alerting:
* Critical (prod VIP unavailable): immediate escalation.
* Warning (VIP with > 3 state changes in 4h): unstable -- investigate underlying pool.

### Step 5 — - Troubleshooting

* **VIP unavailable but pool members are up** -- Check the VS configuration: (1) Is the VIP address reachable? (2) Is the VS admin-enabled? (3) Is there a traffic policy blocking?

* **VIP flapping** -- Usually caused by the underlying pool: if all pool members go down, the VIP becomes unavailable; when one recovers, the VIP comes back. Focus on pool member stability (UC-5.3.1).

* **No VS status events in syslog** -- Ensure the log level for "ltm" is set to Informational: `tmsh modify sys syslog include "local0.* @<splunk_ip>"`.

## SPL

```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```

## Visualization

Status indicator per VIP, Events timeline (critical).

## Known False Positives

Planned changes, test VIPs, and short maintenance windows can disable a listener without user-visible failure.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
