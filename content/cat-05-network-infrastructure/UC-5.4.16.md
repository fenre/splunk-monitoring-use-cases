<!-- AUTO-GENERATED from UC-5.4.16.json — DO NOT EDIT -->

---
id: "5.4.16"
title: "WiFi Channel Utilization and Interference Detection (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.16 · WiFi Channel Utilization and Interference Detection (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wifi channel utilization and interference detection (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies channel congestion and interference sources to optimize channel assignments and reduce co-channel interference.

## Value

Wireless operations teams track Meraki MR DHCP transaction completion rates per AP and SSID to detect IP addressing failures that leave clients connected but without network access.

## Implementation

Query API device data for MR access points; track channel assignments. Correlate with interference signature logs.

## Detailed Implementation

### Prerequisites
- Meraki MR sending client DHCP events. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `type` (DHCP events — discover, offer, request, ack, nak), `client_mac`, `client_ip`, `dhcp_server`, `ap_name`.
- DHCP failures on wireless: A client successfully associates to the SSID (layer 2) but fails to obtain an IP address (layer 3). This leaves the client in a "connected but no Internet" state — the most frustrating user experience. Common causes: (1) DHCP scope exhaustion, (2) VLAN misconfiguration on the AP/switch trunk, (3) DHCP relay agent issues, (4) DHCP server down.

### Step 1 — Configure data collection
Verify DHCP events from Meraki:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)dhcp")
| stats count by type
```

### Step 2 — Create the search and alert

**Primary search — DHCP failure analysis:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)dhcp")
| eval dhcp_state=case(match(type, "(?i)discover"), "discover", match(type, "(?i)offer"), "offer", match(type, "(?i)request"), "request", match(type, "(?i)ack"), "ack", match(type, "(?i)nak"), "nak", 1==1, "other")
| stats count(eval(dhcp_state="discover")) as discovers count(eval(dhcp_state="offer")) as offers count(eval(dhcp_state="ack")) as acks count(eval(dhcp_state="nak")) as naks by ap_name, ssid
| eval offer_rate=if(discovers > 0, round(100*offers/discovers, 1), "N/A")
| eval ack_rate=if(discovers > 0, round(100*acks/discovers, 1), "N/A")
| eval status=case(naks > 5, "NAK — scope exhausted?", ack_rate < 50 AND discovers > 10, "DHCP failure — server unreachable?", offer_rate < 80 AND discovers > 10, "DHCP relay issue?", 1==1, "OK")
| where status != "OK"
| sort -discovers
```

**Client-level DHCP failures:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(type, "(?i)dhcp") AND (match(type, "(?i)nak") OR match(type, "(?i)timeout") OR match(type, "(?i)no.offer"))
| stats count as dhcp_failures latest(ap_name) as last_ap latest(ssid) as last_ssid by client_mac
| where dhcp_failures > 3
| sort -dhcp_failures
```

### Step 3 — Validate
(a) Force a DHCP renewal (ipconfig /renew or dhclient -r) on a wireless client and verify the DHCP sequence appears in Splunk.
(b) If possible, test a DHCP failure scenario (disconnect the DHCP server on a test VLAN) and verify the alarm triggers.
(c) Compare with Meraki Dashboard: Network-wide > Clients > DHCP events.

### Step 4 — Operationalize
Dashboard ("Meraki — Wireless DHCP Health"):
- Row 1 — Single-value: "DHCP Discovers (4h)", "Offer Rate", "ACK Rate", "NAK Count".
- Row 2 — Per-AP DHCP health table with status classification.
- Row 3 — Client-level DHCP failure detail.

Alerting:
- Critical (ACK rate < 50% with > 20 discovers in 15 min on any AP): likely DHCP server or VLAN issue.
- Warning (NAK count > 5 in 1 hour): possible scope exhaustion.

### Step 5 — Troubleshooting

- **Low offer rate, NAKs are zero** — DHCP discover packets are not reaching the DHCP server. Check: (1) VLAN tagging on the switch trunk to the AP, (2) DHCP relay/helper address on the SVI, (3) ACLs blocking UDP 67/68.

- **NAKs present** — DHCP server is responding but rejecting requests. Usually scope exhaustion or MAC-based reservation conflict.

- **DHCP issues only on specific SSID** — Each SSID maps to a VLAN. Check the SSID-to-VLAN mapping in Meraki Dashboard: Wireless > SSIDs > Addressing and traffic.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats count by channel, band
| eval utilization_pct=round(count*100/sum(count), 2)
| where utilization_pct > 40
| sort - utilization_pct
```

## Visualization

Stacked bar chart of channel utilization by band; channel heatmap over time; interference event timeline.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
