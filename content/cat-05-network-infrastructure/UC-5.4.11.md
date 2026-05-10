<!-- AUTO-GENERATED from UC-5.4.11.json — DO NOT EDIT -->

---
id: "5.4.11"
title: "Band Steering Effectiveness"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.11 · Band Steering Effectiveness

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch band steering effectiveness so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.

## Value

Network operations teams measure band steering effectiveness across SSIDs by tracking the 5GHz/6GHz vs. 2.4GHz client distribution, optimizing wireless performance by ensuring dual-band clients use higher-capacity bands.

## Implementation

1. Configure SC4S to receive Cisco WLC syslog. 2. The query categorises clients by 2.4GHz vs 5GHz from the channel value in association events. 3. If you are running Meraki MR instead: enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki and configure a 'client connection changed' alert in Meraki Dashboard. The webhook alertData.band field carries 2.4GHz / 5GHz / 6GHz (see UC-5.4.19 for the canonical Meraki SPL pattern). Polled Meraki TA does not expose per-client band information.

## Detailed Implementation

### Prerequisites
- Wireless controller or cloud platform reporting band steering metrics. Sources: (1) Cisco WLC — Band Select statistics, (2) Meraki — band steering events in API/syslog, (3) Aruba — ARM band steering data.
- Key fields: `client_mac`, `attempted_band` (2.4GHz), `steered_to` (5GHz), `result` (success/failure), `ap_name`, `ssid`.
- Band steering encourages dual-band capable clients to connect on 5GHz instead of 2.4GHz. Benefits: 5GHz has more channels (less co-channel interference), wider channel widths (more throughput), and less interference from non-WiFi devices. The 2.4GHz band is reserved for legacy/IoT devices.

### Step 1 — Configure data collection
Verify band steering events:
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(band.steer|band.select|probe.suppress|5ghz.prefer)")
| stats count by sourcetype, ssid
```

### Step 2 — Create the search and alert

**Primary search — Band steering effectiveness:**
```spl
index=wireless earliest=-4h
| where isnotnull(radio_band) OR isnotnull(band)
| eval client_band=coalesce(radio_band, band)
| eval client_id=coalesce(client_mac, src_mac)
| stats count as connections by ssid, client_band, ap_name
| chart sum(connections) as clients by ssid client_band
| eval total=coalesce('2.4GHz', 0) + coalesce('5GHz', 0) + coalesce('6GHz', 0)
| eval pct_5ghz=round(100*coalesce('5GHz', 0)/total, 1)
| eval pct_6ghz=round(100*coalesce('6GHz', 0)/total, 1)
| eval pct_24ghz=round(100*coalesce('2.4GHz', 0)/total, 1)
| eval band_score=case(pct_5ghz + pct_6ghz > 80, "EXCELLENT", pct_5ghz + pct_6ghz > 60, "GOOD", pct_5ghz + pct_6ghz > 40, "FAIR", 1==1, "POOR")
| sort band_score
```

#### Understanding this SPL: A healthy wireless environment should have > 70% of clients on 5GHz/6GHz. If the majority are on 2.4GHz, band steering is either not enabled, not aggressive enough, or the client population is primarily 2.4GHz-only devices. The SSID-level breakdown helps identify which networks need attention — corporate SSIDs should target > 80% on 5GHz.

**Band steering attempt success rate:**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(band.steer|band.select)")
| eval steer_result=case(match(_raw, "(?i)(success|steered|moved)"), "SUCCESS", match(_raw, "(?i)(fail|refuse|reject|ignore)"), "FAILURE", 1==1, "UNKNOWN")
| stats count as attempts count(eval(steer_result="SUCCESS")) as successes by ssid
| eval success_rate=round(100*successes/attempts, 1)
```

**Band distribution trending:**
```spl
index=wireless earliest=-7d
| where isnotnull(radio_band) OR isnotnull(band)
| eval client_band=coalesce(radio_band, band)
| bin _time span=1h
| stats count by _time, client_band
| timechart span=1h sum(count) by client_band
```

### Step 3 — Validate
(a) Check the wireless controller's band steering configuration: is it enabled on the corporate SSID?
(b) Connect a dual-band client (laptop) and verify it connects on 5GHz. Connect a 2.4GHz-only IoT device and verify it connects on 2.4GHz.
(c) Compare band distribution percentages with the controller's client analytics.

### Step 4 — Operationalize
Dashboard ("Wireless — Band Steering"):
- Row 1 — Single-value tiles: "5GHz clients %", "2.4GHz clients %", "Band score", "Steering success rate".
- Row 2 — Band distribution by SSID: SSID, 2.4GHz count, 5GHz count, 6GHz count, score.
- Row 3 — Band distribution trending (7 days).

Alerting:
- Warning (5GHz percentage drops below 60% on corporate SSID): investigate band steering configuration.
- Info (monthly): band distribution report for RF planning.

### Step 5 — Troubleshooting

- **Most clients on 2.4GHz despite band steering enabled** — Band steering may not be aggressive enough. Increase the probe response suppression threshold. Some controllers have "prefer 5GHz" vs. "force 5GHz" modes.

- **IoT devices can't connect after enabling aggressive band steering** — 2.4GHz-only IoT devices may be blocked. Create a separate SSID for IoT devices without band steering, or use MAC-based exceptions.

- **5GHz percentage varies significantly by building** — 5GHz range is shorter than 2.4GHz. Buildings with sparse AP deployment may have 5GHz coverage gaps, forcing clients to 2.4GHz. Check coverage with a site survey.

## SPL

```spl
index=network sourcetype="cisco:wlc" "associated"
| eval band=if(match(channel,"^(1|6|11)$"),"2.4GHz","5GHz")
| stats count by band, ssid
| eventstats sum(count) as total by ssid
| eval pct=round(count/total*100,1)
```

## Visualization

Pie chart (band distribution), Bar chart (by SSID), Timechart (trending).

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
