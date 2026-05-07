<!-- AUTO-GENERATED from UC-5.13.42.json — DO NOT EDIT -->

---
id: "5.13.42"
title: "Client RSSI/SNR Quality Monitoring (Wireless)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.42 · Client RSSI/SNR Quality Monitoring (Wireless)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how strong the Wi-Fi signal is for every person connected — like checking how many bars you have on your phone. When the signal is weak in certain areas, we flag those spots so your team can move or add equipment to fix the dead zones before people start complaining about slow connections.*

---

## Description

Measures wireless signal quality (RSSI and SNR) per AP and frequency band, identifying APs and locations where clients experience weak signal or high noise — the root cause of slow Wi-Fi, dropped connections, and poor VoIP quality that general health scores may not surface because the client is technically 'connected' but performing terribly.

## Value

When users say 'the Wi-Fi is slow,' RSSI and SNR tell you whether the problem is the radio layer (weak signal, high interference) or something else (DHCP, RADIUS, DNS, application). A client with RSSI -82 dBm is at the edge of usability — it will experience 50%+ packet loss, 200ms+ latency, and constant retransmissions. Fixing this requires physical changes (AP placement, transmit power, antenna orientation) that no amount of software tuning can substitute. This UC identifies which APs have coverage gaps *before* users complain, and validates whether AP placements or power adjustments actually improved signal quality.

## Implementation

Same `client` detail input as UC-5.13.40. Confirm `rssi` and `snr` fields are populated for wireless clients with `| fieldsummary`. Group by `apName` and `frequency` to isolate per-AP, per-band signal quality. RSSI thresholds: ≥-65 Good (reliable for voice), -65 to -72 Acceptable (data OK, voice marginal), -72 to -80 Poor (data degraded), <-80 Critical (unusable). SNR thresholds: ≥25 Good, 15–25 Marginal, <15 Poor.

## Detailed Implementation

### Prerequisites
- UC-5.13.40 (Client Inventory) operational — same `client` detail input.
- Confirm `rssi` and `snr` are populated for wireless clients:
  ```spl
  index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" earliest=-1h
  | stats count(eval(isnum(rssi))) as has_rssi, count(eval(isnum(snr))) as has_snr, count as total
  | eval rssi_pct=round(has_rssi*100/total,1), snr_pct=round(has_snr*100/total,1)
  ```
  If `rssi_pct < 80%`, some client types don't report RSSI (common for IoT devices). If `snr_pct = 0`, your Catalyst Center version may not include SNR in the API — use RSSI alone.
- Understand RF fundamentals for interpretation:
  - **RSSI** (Received Signal Strength Indicator): measured in dBm. Higher (less negative) is better. -30 dBm is excellent (right next to the AP). -90 dBm is unusable. Industry thresholds: **≥-65** for voice/video, **≥-72** for reliable data, **≥-80** for basic connectivity.
  - **SNR** (Signal-to-Noise Ratio): measured in dB. Higher is better. ≥25 dB supports high data rates. 15–25 dB is marginal. <15 dB means the signal is barely distinguishable from noise.
  - **Frequency band**: 2.4 GHz has longer range but more interference. 5 GHz has shorter range but more channels. 6 GHz (Wi-Fi 6E) is cleanest but shortest range. RSSI thresholds should be band-aware.

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.40. The `rssi`, `snr`, `apName`, and `frequency` fields are included in the per-client JSON response for wireless clients.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" earliest=-30m
| stats avg(rssi) as fleet_avg_rssi, avg(snr) as fleet_avg_snr, dc(apName) as ap_count, dc(macAddress) as client_count
```
Typical healthy campus: `fleet_avg_rssi` between -55 and -70, `fleet_avg_snr` between 20 and 35. If `fleet_avg_rssi < -75`, you have a significant coverage problem campus-wide.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(rssi) as avg_rssi avg(snr) as avg_snr dc(macAddress) as client_count by apName, siteId, frequency
| eval rssi_quality=case(avg_rssi>=-65,"Good", avg_rssi>=-72,"Acceptable", avg_rssi>=-80,"Poor", 1==1,"Critical")
| eval snr_quality=case(avg_snr>=25,"Good", avg_snr>=15,"Marginal", 1==1,"Poor")
| sort avg_rssi
```

Why group `by apName, siteId, frequency`: this gives per-AP, per-band signal quality metrics. An AP with good 5 GHz RSSI but poor 2.4 GHz RSSI has a specific problem (2.4 GHz interference, not placement). An AP with poor RSSI on both bands has a placement or power problem.

Why `avg(rssi)` across clients: averaging RSSI across all clients associated with an AP gives the mean client experience. APs where the average is poor have systematic coverage issues. For a more sensitive view, use `perc10(rssi)` to see what the worst 10% of clients experience — this catches the "edge of coverage" problem that averages hide.

Why separate RSSI and SNR quality bands: RSSI measures signal strength; SNR measures signal quality relative to noise. An AP can have adequate RSSI (-68 dBm) but terrible SNR (12 dB) due to co-channel interference from a neighbouring AP or non-Wi-Fi source (microwave, Bluetooth). Both metrics are needed to diagnose the problem correctly.

RSSI thresholds by application:
- **Voice/video** (Webex, Teams): ≥ -65 dBm, SNR ≥ 25 dB. Below this, voice quality degrades noticeably.
- **Reliable data**: ≥ -72 dBm, SNR ≥ 20 dB. Web browsing and email work; large file transfers may be slow.
- **Basic connectivity**: ≥ -80 dBm, SNR ≥ 15 dB. Slow and unreliable. High retransmission rate.
- **Critical/unusable**: < -80 dBm. Client will roam if possible or experience near-total packet loss.

This is a report and dashboard panel, not a real-time alert. For alerting on AP-level signal quality degradation, schedule with `| where rssi_quality IN ("Poor","Critical") AND client_count > 5` every hour.

### Step 3 — Validate
(a) Pick an AP from the results. In **Catalyst Center > Assurance > Device 360 > [that AP]**, check the client RSSI values shown in the radial chart or client list. The average should be comparable to the Splunk value.

(b) On-site validation: walk to the AP's location with a Wi-Fi analyser app (WiFi Analyzer on Android, AirPort Utility on iOS). Measure the RSSI at the AP and at the expected cell edge. The Splunk average should fall between these two values.

(c) Band comparison: run the search and compare 2.4 GHz vs 5 GHz avg_rssi for the same AP. 5 GHz should be 5–15 dBm lower (shorter range). If 2.4 GHz is significantly worse despite longer range, suspect 2.4 GHz interference.

(d) Check for outlier APs: `| where rssi_quality="Critical" | stats count`. If > 10% of APs are Critical, the problem is systemic (power settings, design issue), not localised.

(e) Cross-reference with UC-5.13.12 (Client Health by SSID): poor RSSI per AP should correlate with poor client health on the SSIDs served by those APs.

### Step 4 — Operationalize
Dashboard placement (dedicated "Wireless RF Quality" dashboard or as a row on the Client Experience dashboard):
- Table: apName | siteId | frequency | avg_rssi | avg_snr | client_count | rssi_quality | snr_quality — sorted worst-first. Colour-code: Critical red, Poor orange, Acceptable yellow, Good green.
- RSSI histogram: `| bin rssi span=5 | stats count by rssi` showing the fleet-wide signal quality distribution curve. A bimodal distribution (peak at -55 and another at -78) indicates a split between well-covered and poorly-covered areas.
- AP heatmap: if floor-plan data is available, plot APs by location with colour = avg_rssi.

Runbook (owner: Wireless Engineering):
1. Identify APs with `rssi_quality = Critical` or `Poor`.
2. Check client count: APs with poor RSSI but 0 clients may have no coverage problem — they might be in a closet or storage room. Focus on APs with ≥ 5 clients.
3. For poor RSSI:
   - Check AP transmit power: `show ap config general <ap-name>` → Tx Power Level. If set to minimum, consider increasing.
   - Check AP placement: is the AP mounted in a ceiling tile, behind a pillar, or in a cabinet?
   - Check for obstructions: recent renovations, furniture changes, or new walls can degrade RF.
4. For poor SNR with acceptable RSSI:
   - Check co-channel interference: run `| stats dc(apName) by frequency` for APs on the same channel in the same area. Too many APs on the same channel degrades SNR.
   - Check non-Wi-Fi interference: microwave ovens (2.4 GHz), Bluetooth devices, and wireless video transmitters can raise the noise floor.
5. After remediation (power adjustment, AP relocation, channel change), monitor this UC for 48 hours to confirm improvement.

Site survey trigger:
- APs consistently showing `Poor` or `Critical` RSSI should be flagged for a physical RF site survey. Use the AP list from this UC as the survey scope document.

### Step 5 — Troubleshooting

- **RSSI values all appear as null** — the `client` input may not extract wireless RF metrics. Check `| fieldsummary | search field=rssi` for the field name. Variants: `rssi`, `Rssi`, `signalStrength`. Also check whether your Catalyst Center version includes RSSI in the client detail API response.

- **SNR values not populated** — some Catalyst Center versions or AP models don't report SNR in the client API. Use RSSI alone for quality assessment. SNR can also be estimated: if you know the noise floor (typically -92 to -95 dBm for indoor), SNR ≈ RSSI - noise_floor.

- **Average RSSI misleading for high-density venues** — in stadiums or lecture halls, the average RSSI is expected to be lower because many clients sit at the cell edge. Use per-site thresholds from a `catalyst_site_thresholds` lookup rather than global thresholds.

- **RSSI suddenly improves for all APs** — transmit power was globally increased (check `index=catalyst sourcetype="cisco:dnac:audit:logs"` for RF profile changes). Higher Tx power improves RSSI but doesn't necessarily improve SNR — it may increase co-channel interference.

- **One AP shows much worse RSSI than neighbouring APs** — the AP may have a hardware issue (failed antenna, damaged cable), been moved, or had its power reduced by RRM. Check `show ap config general <ap-name>` for power level and antenna status.

- **RSSI differs significantly between 2.4 GHz and 5 GHz on the same AP** — expected. 5 GHz signals attenuate faster. If 2.4 GHz is *worse* than 5 GHz for the same AP, suspect 2.4 GHz interference.

- **Client count per AP seems too low** — clients may be roaming between APs during the search window. `dc(macAddress)` counts clients that were associated at any point, not simultaneously. For concurrent client count, narrow to `earliest=-5m`.

- **Search is very slow** — the `client` sourcetype is high-volume. Add `earliest=-20m` for a snapshot. For trending, use summary indexing: `| stats avg(rssi) avg(snr) dc(macAddress) by apName, siteId, frequency | collect index=catalyst_summary sourcetype=rf_quality_summary`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(rssi) as avg_rssi avg(snr) as avg_snr dc(macAddress) as client_count by apName, siteId, frequency
| eval rssi_quality=case(avg_rssi>=-65,"Good", avg_rssi>=-72,"Acceptable", avg_rssi>=-80,"Poor", 1==1,"Critical")
| eval snr_quality=case(avg_snr>=25,"Good", avg_snr>=15,"Marginal", 1==1,"Poor")
| sort avg_rssi
```

## Visualization

(1) Table: apName, siteId, frequency, avg_rssi, avg_snr, client_count, rssi_quality, snr_quality — sorted by avg_rssi ascending (worst APs first). (2) Heatmap: APs (rows) × frequency bands (columns) with avg_rssi as colour intensity (-65 green to -85 red). (3) Histogram: RSSI distribution across all wireless clients `| bin rssi span=5 | stats count by rssi` to show the coverage quality curve. (4) Scatter plot: avg_rssi (x) vs avg_snr (y) per AP — APs in the bottom-left quadrant (low signal AND low SNR) need immediate attention.

## Known False Positives

**High-density venue with inherently low RSSI at the cell edge.** In stadiums, convention centres, and lecture halls, AP placement is optimised for capacity rather than uniform signal strength. Clients at the cell edge may report RSSI values in the -72 to -80 dBm range, which is expected in high-density designs. Distinguish by checking whether the affected `siteId` corresponds to a known high-density venue. Suppress by maintaining a `catalyst_site_thresholds` lookup with per-site RSSI thresholds.

**Building construction materials attenuating signal in specific zones.** Concrete walls, metal partitions, elevator shafts, and glass facades create RF dead zones where RSSI is consistently low without indicating an AP problem. Distinguish by checking whether low-RSSI clients are concentrated in specific physical areas. Suppress by excluding known dead zones from RSSI alerting — these require physical site survey remediation.

**Client device with weak antenna or driver issue reporting abnormally low RSSI.** Some client device models (older laptops, IoT sensors, medical devices) have weaker antennas or driver bugs causing them to report lower RSSI than other clients on the same AP. Distinguish by checking whether the low RSSI is specific to certain MAC addresses or `hostType` values while other clients on the same AP report normal RSSI. Suppress by filtering known weak-antenna device types.

**5 GHz RSSI inherently lower than 2.4 GHz.** 5 GHz signals attenuate faster than 2.4 GHz due to higher frequency. APs will naturally show lower avg_rssi on 5 GHz than 2.4 GHz even with the same transmit power and client distance. Distinguish by comparing within the same frequency band (use the `frequency` split-by). Suppress by setting band-specific thresholds: -65 for 5 GHz is good, while -65 for 2.4 GHz is mediocre.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco Wireless Design — RF Coverage and Signal Requirements](https://www.cisco.com/c/en/us/solutions/design-zone/networking-design-guides/campus-wired-wireless.html)
