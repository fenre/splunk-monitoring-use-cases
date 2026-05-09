<!-- AUTO-GENERATED from UC-5.4.38.json — DO NOT EDIT -->

---
id: "5.4.38"
title: "Cisco C9800 WLC AP Join Failures"
status: "community"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.38 · Cisco C9800 WLC AP Join Failures

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch the wireless access points on the ceiling check in with the building's main Wi-Fi controller. When any of them fail to check in, that part of the office loses Wi-Fi entirely — even though the device looks alive on the wall. We alert before users start asking why their phones say no signal.*

---

## Description

Surfaces APs that fail to register with the Cisco Catalyst 9800 wireless LAN controller because of CAPWAP tunnel failures, DTLS certificate-handshake errors, or repeated AP-side crashes. Each failed-join event represents one AP's worth of campus Wi-Fi coverage going dark.

## Value

Cisco Catalyst 9800 wireless controllers are the campus Wi-Fi backbone for thousands of enterprises. AP join failures are uniquely silent: the AP looks 'present' on the wired switch port (LLDP, MAC table, PoE) but never finishes handshaking with the WLC, so users in that coverage cell get no Wi-Fi at all. Three classic failure modes converge here — expired or untrusted controller certificates, CAPWAP MTU / firewall mismatches between AP and WLC, and AP-side crashes that should have triggered a hardware-replacement workflow but did not. Detection at the controller is the only place all three are visible together.

## Implementation

Forward Cisco C9800 syslog to Splunk at severity 3 or lower so the CAPWAP / DTLS / AP_EVENT facilities reach the indexer. Alert when any AP triggers a join failure or repeatedly crashes inside a 15-minute window. Correlate with the certificate-expiry calendar for the WLC trustpoint — most surprise outages trace back to expired CAs.

## SPL

```spl
index=network sourcetype="cisco:ios" host="c9800*"
  ("%CAPWAP-3-ERRORLOG" OR "%DTLS-3-HANDSHAKE_FAILURE" OR "%AP_EVENT-3-CRASH")
| rex "AP (?<ap_name>\S+)"
| stats count by host, ap_name, _raw
| sort - count
```

## Visualization

Table (failed APs with cause), Status grid (AP join state per WLC, coloured by health), Timeline (join failures over time, useful for spotting controller-wide flap events).

## Known False Positives

**Scheduled controller upgrades.** Rolling AP firmware upgrades and WLC HA failovers generate CAPWAP errors as APs reset and rejoin the partner controller. Suppress alerts during announced maintenance windows.

**Powered-down lab APs.** Lab APs that are physically powered off but still configured on the WLC will alarm forever. Filter by AP name pattern or move lab APs to a dedicated WLC.

**Single-AP DTLS handshake retries.** Some AP models retry DTLS handshakes with a brief delay; one or two retries per join is normal. Threshold the alert on count > 3 within 5 minutes for a single AP.

## References

- [Cisco Catalyst 9800 series wireless controllers](https://www.cisco.com/c/en/us/support/wireless/catalyst-9800-series-wireless-controllers/series.html)
- [CAPWAP troubleshooting on Catalyst 9800](https://www.cisco.com/c/en/us/support/docs/wireless/catalyst-9800-series-wireless-controllers/214286-troubleshoot-and-debug-capwap-issues.html)
