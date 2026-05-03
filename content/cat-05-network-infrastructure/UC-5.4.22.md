<!-- AUTO-GENERATED from UC-5.4.22.json — DO NOT EDIT -->

---
id: "5.4.22"
title: "Splash Page Engagement and Redirection Analytics (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.22 · Splash Page Engagement and Redirection Analytics (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch splash page engagement and redirection analytics (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks guest network splash page performance and user acceptance rates for marketing and network access purposes.

## Value

Wireless operations teams monitor Meraki MR per-AP channel utilization levels to detect airtime congestion and non-WiFi interference, guiding channel planning and RF environment optimization.

## Implementation

Capture splash page interaction events from syslog. Track accepts vs. denies.

## Detailed Implementation

### Prerequisites
- Meraki providing per-AP channel utilization data. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:events`. Key fields: `ap_name`, `channel`, `band` (2.4 GHz / 5 GHz), `utilization` (percentage), `non_wifi_interference` (percentage from non-WiFi sources).
- Channel utilization is the percentage of time the radio medium is busy. It includes: (1) WiFi transmissions from your APs and clients, (2) WiFi from neighboring networks (co-channel interference), (3) non-WiFi interference (microwaves, Bluetooth, cordless phones). When utilization exceeds 60-70%, clients experience increased contention, retransmissions, and throughput degradation.

### Step 1 — Configure data collection
Verify channel data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(channel) OR isnotnull(utilization)
| stats avg(utilization) as avg_util by ap_name, channel, band
| sort -avg_util
```

### Step 2 — Create the search and alert

**Primary search — Channel utilization by AP:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(utilization) OR isnotnull(channel)
| stats avg(utilization) as avg_util max(utilization) as max_util avg(non_wifi_interference) as non_wifi dc(client_mac) as client_count by ap_name, channel, band
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor zone
| eval util_status=case(avg_util > 80, "CRITICAL", avg_util > 60, "HIGH", avg_util > 40, "MODERATE", 1==1, "OK")
| eval interference_note=if(non_wifi > 10, "Non-WiFi interference detected (".round(non_wifi,1)."%)", "Clean")
| where util_status IN ("CRITICAL", "HIGH")
| sort -avg_util
```

**Channel overlap detection:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(channel) AND band="2.4 GHz"
| stats dc(ap_name) as aps_on_channel values(ap_name) as ap_list by channel
| where aps_on_channel > 3
| eval concern=if(aps_on_channel > 5, "Too many APs on same channel — co-channel interference", "Monitor")
| sort -aps_on_channel
```

### Step 3 — Validate
(a) Compare channel utilization with Meraki Dashboard: Wireless > Radio settings > RF spectrum.
(b) Identify APs in high-density areas (conference rooms) and verify higher utilization.
(c) During off-hours, verify utilization drops significantly (indicating it's client-driven, not interference).

### Step 4 — Operationalize
Dashboard ("Meraki — RF Environment"):
- Row 1 — Single-value: "APs with critical utilization", "Average 5 GHz utilization", "Average 2.4 GHz utilization", "Non-WiFi interference APs".
- Row 2 — Per-AP channel utilization table with building/floor context.
- Row 3 — Channel assignment heatmap (APs per channel).

Alerting:
- Warning (AP avg utilization > 70% for > 30 min): airtime congestion.
- Info (non-WiFi interference > 15% on any AP): physical environment investigation needed.

### Step 5 — Troubleshooting

- **High utilization on 2.4 GHz, not 5 GHz** — 2.4 GHz has fewer channels and more interference. Enable band steering (Meraki: Wireless > Radio settings > Band selection) to push dual-band clients to 5 GHz.

- **Non-WiFi interference** — Physical investigation needed. Common sources: microwave ovens (2.4 GHz ch 6-11), Bluetooth, wireless cameras, baby monitors. Meraki's "Spectrum analysis" (on supported models) can help identify the source.

- **Co-channel interference between your own APs** — Too many APs on the same channel. Enable Meraki auto-channel assignment (Wireless > Radio settings > Channel planning: Auto).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Splash*"
| stats count as redirect_count by result, ap_name
| eval acceptance_rate=round(count*100/sum(count), 2)
```

## Visualization

Pie chart of acceptance rates; funnel chart of splash interactions; time-series trending.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
