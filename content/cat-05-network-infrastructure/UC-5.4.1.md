<!-- AUTO-GENERATED from UC-5.4.1.json — DO NOT EDIT -->

---
id: "5.4.1"
title: "AP Offline Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.1 · AP Offline Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch ap offline detection so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Offline APs create coverage dead zones. Users lose connectivity in affected areas.

## Value

Network operations teams detect offline wireless access points with physical location context, correlate multi-AP outages to identify upstream infrastructure failures (PoE switch, power), and assess wireless coverage impact per building and floor.

## Implementation

For Meraki: configure syslog in Dashboard, or use Meraki API TA. For WLC: forward syslog. Alert when APs go offline. Maintain AP inventory lookup for location context.

## Detailed Implementation

### Prerequisites
- Wireless controller or cloud management platform forwarding AP status data to Splunk. Sources: (1) Cisco WLC syslog (`sourcetype=cisco:wlc`) — AP join/disjoin events, (2) Meraki Dashboard API via Splunk_TA_cisco_meraki (`sourcetype=meraki:api:devices`) — AP status online/offline, (3) Aruba Central/AOS-CX syslog (`sourcetype=aruba:controller`) — AP state changes. Data in `index=wireless` (or `index=network`).
- Key fields vary by platform: Cisco WLC: `ap_name`, `ap_mac`, `controller`, `event_type` (AP-DISJOIN, AP-JOIN); Meraki: `name`, `serial`, `status` (online/offline); Aruba: `ap_name`, `ap_group`, `status`.
- Build `wireless_ap_inventory.csv` lookup: `ap_name,ap_mac,building,floor,zone,ap_model,expected_controller` for location context and coverage impact assessment.

### Step 1 — Configure data collection
Verify AP status events:
```spl
index=wireless (sourcetype="cisco:wlc" ("AP-DISJOIN" OR "AP-JOIN" OR "NOT_RESPONDING")) OR (sourcetype="meraki:api:devices" model="MR*") OR (sourcetype="aruba:controller" "AP" ("down" OR "up")) earliest=-4h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — AP offline detection with coverage impact:**
```spl
index=wireless earliest=-15m
| eval ap_offline=case(sourcetype="cisco:wlc" AND match(_raw, "(?i)(AP-DISJOIN|NOT.RESPONDING)"), 1, sourcetype="meraki:api:devices" AND status="offline" AND match(model, "^MR"), 1, sourcetype="aruba:controller" AND match(_raw, "(?i)ap.*down"), 1, 1==1, 0)
| where ap_offline=1
| eval ap_id=coalesce(ap_name, name, ap_mac)
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor zone ap_model
| eval coverage_impact=case(isnotnull(building) AND isnotnull(floor), building." / ".floor." / ".zone, isnotnull(building), building, 1==1, "Unknown location")
| stats count as offline_events latest(_time) as last_seen by ap_id, ap_model, coverage_impact, sourcetype
| eval offline_min=round((now() - last_seen)/60, 0)
| eval severity=case(offline_min > 60, "CRITICAL", offline_min > 15, "HIGH", 1==1, "WARNING")
| sort severity, -offline_min
```

#### Understanding this SPL: An offline AP means users in that physical area lose wireless connectivity. The coverage_impact field maps the AP to a building/floor/zone so the NOC knows exactly which area is affected. Multiple APs offline in the same building suggest a switch or power issue (PoE switch failure), not individual AP failures.

**Multi-AP outage correlation (PoE switch failure detection):**
```spl
index=wireless earliest=-30m
| eval ap_offline=case(match(_raw, "(?i)(AP-DISJOIN|NOT.RESPONDING|offline|ap.*down)"), 1, 1==1, 0)
| where ap_offline=1
| eval ap_id=coalesce(ap_name, name, ap_mac)
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor
| stats dc(ap_id) as offline_aps values(ap_id) as ap_list by building, floor
| where offline_aps > 2
| eval likely_cause=case(offline_aps > 10, "Power/switch failure — entire floor", offline_aps > 5, "PoE switch failure — partial floor", 1==1, "Multiple AP failures — investigate")
```

### Step 3 — Validate
(a) Power off a test AP and verify it appears as offline in Splunk within the expected detection time (syslog: seconds; API poll: 5-15 minutes).
(b) Verify AP inventory lookup: spot-check 20 APs against the wireless management platform for correct building/floor/zone mapping.
(c) Cross-check offline AP count with the wireless controller/dashboard.

### Step 4 — Operationalize
Dashboard ("Wireless — AP Status"):
- Row 1 — Single-value tiles: "APs online", "APs offline", "APs offline > 1 hour", "Buildings affected".
- Row 2 — Offline AP table: AP name, model, building/floor/zone, offline duration, severity.
- Row 3 — Multi-AP outage correlation: buildings/floors with multiple offline APs.
- Row 4 — AP offline trending (24h).

Alerting:
- Critical (> 5 APs offline on same floor): PoE switch or power failure — dispatch facilities.
- High (AP offline > 60 minutes): individual AP failure — dispatch replacement.
- Warning (AP offline): track and investigate if not resolved in 15 minutes.

### Step 5 — Troubleshooting

- **AP shows offline in Splunk but users have wireless** — The AP may have re-joined on a different controller (load balancing), or the detection is from a stale API poll. Check the controller for the AP's current status.

- **No AP offline events from Cisco WLC** — Verify the WLC syslog level: `config syslog level AP-COMMON 5` to capture AP join/disjoin events at level 5 (notifications).

- **Multiple APs cycle offline/online repeatedly** — Likely a PoE switch flapping or controller HA failover. Correlate with switch syslog (UC-5.1.x) and controller events.

## SPL

```spl
index=network sourcetype="meraki" type="access point" ("went offline" OR "unreachable")
| table _time host ap_name network status | sort -_time
```

## Visualization

Map (AP locations with status), Table, Status grid, Single value (APs offline).

## Known False Positives

Access points may go offline during scheduled firmware updates, PoE switch reboots, cabling work, or RF site surveys, which can look like an outage without a real coverage problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
