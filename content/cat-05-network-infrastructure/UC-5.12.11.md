<!-- AUTO-GENERATED from UC-5.12.11.json — DO NOT EDIT -->

---
id: "5.12.11"
title: "Call Quality Metrics Monitoring (MOS, Jitter, Packet Loss per Call Leg)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.11 · Call Quality Metrics Monitoring (MOS, Jitter, Packet Loss per Call Leg)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Quality &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch each half of a phone call separately so we can tell if scratchy sound is coming from your office network or from the path out to the phone company, instead of guessing from one blended score.*

---

## Description

Tracks MOS, jitter, and packet loss segmented by individual media legs (ingress vs egress paths) so degradations map to a specific border element, endpoint, or codec slice rather than averaging away localized impairments.

## Value

Engineering isolates which side of a SIP session or which trunk injects loss or jitter before opening carrier disputes, tuning jitter buffers, or rolling back codec changes—shortening mean time to repair versus aggregate MOS-only views.

## Implementation

Normalize leg identifiers from SBC RTCP reports and CDR call correlation keys; baseline per trunk_group and codec; alert on composite thresholds with directional tagging.

## Detailed Implementation

### Prerequisites
- RTCP-XR or vendor QoE logs must expose `leg_id` (or derivable `call_id`+`media_index`), `direction`, `mos`, `jitter_ms`, `packet_loss_pct`, and ideally `codec`. Without leg granularity, fall back to correlating two QoE records per call via timestamps and RTP SSRC.
- Agreement on clocks (NTP on SBC/media servers) so Splunk `_time` aligns with signaling completes.
- Document codec naming (`PCMU`, `opus`, `G729`) for consistent splits.

### Step 1 — Onboard QoE
Land QoE into `index=voip` with props extracting numeric jitter/loss; verify dual-leg presence on sample calls.

### Step 2 — Validate joins
Spot-check a known good call: both legs should show MOS >3.8 when loss <1%.

### Step 3 — Build thresholds
Set directional baselines per site/trunk (p95 jitter, p95 loss); escalate when MOS <3.6 AND loss or jitter breaches baseline.

### Step 4 — Dashboard
Five-minute timecharts per leg_id with MOS, jitter, loss overlays; matrix by codec x direction.

### Step 5 — Operational feedback and troubleshooting
When alarms fire, compare ingress vs egress; if only one leg fails, scope to LAN/WAN segment before blaming core. Null MOS often signals one-way RTCP—enable bilateral XR on phones/SBC. Wi‑Fi roam spikes may trip loss without carrier fault—annotate SSID context when exported.

## SPL

```spl
index=voip (sourcetype="qos:rtcp" OR sourcetype="cdr:voip")
| where isnotnull(leg_id) AND (isnotnull(mos) OR isnotnull(jitter_ms) OR isnotnull(packet_loss_pct))
| bin _time span=5m
| stats avg(mos) as avg_mos avg(jitter_ms) as avg_jitter avg(packet_loss_pct) as avg_loss count as samples by _time, leg_id, codec, direction
| where avg_mos < 3.6 OR avg_jitter > 35 OR avg_loss > 1.5
| sort _time, leg_id
```

## Visualization

Small multiples: MOS/jitter/loss per leg_id over time; heatmap of worst legs by trunk_group; drilldown table linking leg_id to last SIP INVITE host.

## Known False Positives

Bluetooth headsets and mobile handovers can inflate jitter on one leg only; VPN split-tunnel changes duplicate QoE paths; some SBCs round-trip MOS from near-end only, masking far-end impairments; scheduled codec migrations temporarily depress MOS until caches refresh.

## References

- [RFC 3611 — RTP Control Extended Reports (RTCP XR)](https://www.rfc-editor.org/rfc/rfc3611)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
