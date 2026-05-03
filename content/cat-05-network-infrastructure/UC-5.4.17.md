<!-- AUTO-GENERATED from UC-5.4.17.json — DO NOT EDIT -->

---
id: "5.4.17"
title: "Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.17 · Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch rogue and unauthorized ap detection — air marshal (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.

## Value

Wireless operations teams identify Meraki MR access points delivering poor client throughput, correlating low performance with client density and interference to target capacity upgrades.

## Implementation

Enable Air Marshal on MR APs and ingest syslog events. Create alert for new rogue AP detections with risk scoring.

## Detailed Implementation

### Prerequisites
- Meraki API or syslog providing per-AP client throughput data. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:events`. Key fields: `client_mac`, `usage` or `sent`/`recv` (bytes), `ap_name`, `ssid`.
- Low throughput causes: (1) high channel utilization (too many clients on same channel), (2) legacy clients forcing low data rates (802.11b at 1 Mbps), (3) excessive retransmissions from weak signal, (4) interference from non-WiFi sources (microwave ovens on 2.4 GHz, Bluetooth).

### Step 1 — Configure data collection
Verify throughput data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(usage) OR isnotnull(sent)
| eval bytes_total=coalesce(usage, sent + recv, 0)
| stats avg(bytes_total) as avg_bytes by ap_name
```

### Step 2 — Create the search and alert

**Primary search — Low throughput detection:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(client_mac)
| eval bytes_total=coalesce(usage, sent + recv, 0)
| stats avg(bytes_total) as avg_client_throughput dc(client_mac) as client_count sum(bytes_total) as total_bytes by ap_name, ssid
| eval avg_kbps=round(avg_client_throughput * 8 / 1024, 1)
| eval total_mbps=round(total_bytes * 8 / (1024*1024), 1)
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor expected_throughput
| eval throughput_rating=case(avg_kbps > 5000, "Good", avg_kbps > 1000, "Fair", avg_kbps > 200, "Low", 1==1, "Very Low")
| where throughput_rating IN ("Low", "Very Low") AND client_count > 5
| eval possible_cause=case(client_count > 30, "High client density", avg_kbps < 100 AND client_count < 10, "Interference or legacy clients", 1==1, "Investigate channel utilization")
| sort avg_kbps
```

### Step 3 — Validate
(a) Run a speed test on a wireless client and compare the throughput with the Splunk-reported value.
(b) Verify high-density APs (conference rooms, auditoriums) show lower per-client throughput due to airtime sharing.
(c) Compare with Meraki Dashboard: Wireless > Monitor > Access Points > Throughput.

### Step 4 — Operationalize
Dashboard ("Meraki — Wireless Throughput"):
- Row 1 — Single-value: "Average throughput/client", "APs with low throughput", "Total clients", "Highest density AP".
- Row 2 — AP throughput table with client count and possible cause.

Alerting:
- Warning (AP avg throughput < 200 kbps with > 10 clients for > 1 hour): investigate.

### Step 5 — Troubleshooting

- **Low throughput everywhere** — Check if there's a global bandwidth limit (traffic shaping) configured per SSID in Meraki Dashboard: Wireless > Firewall & traffic shaping.

- **Low throughput only on 2.4 GHz** — 2.4 GHz has only 3 non-overlapping channels and is prone to interference. Consider band steering or disabling 2.4 GHz on some APs.

- **Low throughput in conference rooms** — High client density. Consider adding APs, enabling channel width optimization, or deploying a dedicated conference room AP.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=air_marshal signature="*Rogue*" OR signature="*Unauthorized*"
| stats count by ssid, bssid, first_detected, last_seen, threat_level
| where threat_level="high" OR threat_level="critical"
| sort - first_detected
```

## Visualization

Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.

## Known False Positives

Failed logins often come from typos, expired passwords, guest self-service, or a single misconfigured device; treat sustained rises across many users as the real signal.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
