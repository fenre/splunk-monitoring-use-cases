<!-- AUTO-GENERATED from UC-5.21.2.json — DO NOT EDIT -->

---
id: "5.21.2"
title: "NTP Clock Drift Exceeding Threshold on Routers and Switches"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.21.2 · NTP Clock Drift Exceeding Threshold on Routers and Switches

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch how far each network device's clock has drifted from the correct time. Even a small error means security systems and log records won't match up. We alert before the drift gets big enough to cause real problems like failed logins or unreliable records.*

---

## Description

Monitors the NTP clock offset on network devices and alerts when drift exceeds operational thresholds. Even small clock drift (>50ms) degrades log correlation accuracy, and drift beyond 300ms breaks Kerberos authentication and DNSSEC validation. Network devices serving as NTP sources amplify drift to all downstream clients.

## Value

Kerberos authentication fails at 5-minute clock skew (configurable, default 300 seconds). DNSSEC signatures have validity windows — clock drift causes validation failures. Forensic investigations depend on sub-second timestamp accuracy across all devices. This UC catches gradual drift before it reaches the breaking point, when a simple NTP restart fixes the issue rather than an emergency involving cascading authentication failures.

## Implementation

Poll NTP offset via SNMP (ntpSysOffset). Supplement with syslog clock skew events. Alert on drift >50ms (warning), >100ms (high), >500ms (critical).

## Detailed Implementation

### Prerequisites
- SNMP polling enabled on network devices with NTP MIB objects accessible.
- SC4SNMP or SNMP Modular Input polling `ntpSysOffset` every 300 seconds.
- For Cisco devices: `snmp-server enable traps ntp` to enable NTP SNMP traps.

### Step 1 — Configure SNMP polling for NTP offset
Add NTP MIB objects to SC4SNMP polling profile:
```yaml
profiles:
  ntp_health:
    frequency: 300
    varBinds:
      - ['1.3.6.1.4.1.9.9.168.1.1.4']  # ntpSysOffset (Cisco)
      - ['1.3.6.1.4.1.9.9.168.1.1.3']  # ntpSysStratum (Cisco)
```

For standard NTP MIB (RFC 5907):
```yaml
      - ['1.3.6.1.2.1.197.1.2.1']  # ntpEntStatusCurrentMode
      - ['1.3.6.1.2.1.197.1.2.3']  # ntpEntStatusStratum
```

### Step 2 — Create drift monitoring search
The primary search (above) tracks offset in milliseconds.

**Syslog-based immediate detection (complements SNMP):**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe")
  "NTP" ("skew" OR "drift" OR "offset" OR "clock.*adjust")
| rex field=_raw "offset\s*(?<offset_value>[\-\d\.]+)"
| eval offset_ms=abs(tonumber(offset_value))
| where offset_ms > 50
| stats latest(offset_ms) as current_offset by host
| sort -current_offset
```

**30-day drift trend (capacity planning):**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ntpSysOffset" earliest=-30d
| eval offset_ms=abs(metric_value * 1000)
| timechart span=1d max(offset_ms) as max_daily_offset_ms by host
```

### Step 3 — Validate
(a) On a router, run `show ntp status` and note the `root dispersion` and `clock offset` values. Compare with the SNMP-polled offset in Splunk.
(b) Typical healthy offset: <10ms to local stratum-1, <50ms to internet NTP peers.
(c) Introduce deliberate drift by temporarily removing all NTP peers. Verify the alert fires within one poll interval.

### Step 4 — Operationalize
Dashboard ("NTP Clock Drift"):
- Row 1 — Single-value: worst clock offset across fleet (red >500ms, yellow >100ms, green <50ms).
- Row 2 — Table: devices with drift >50ms, showing current offset and status.
- Row 3 — Timechart: 30-day offset trend per device.

Alerting:
- >500ms drift on any device: Critical page — Kerberos and DNSSEC at risk.
- >100ms drift on any core/distribution device: High priority — investigate root cause.
- >50ms sustained for >1 hour: Warning — NTP peering may be degraded.

### Step 5 — Troubleshooting
- **Gradual drift increasing over days.** The hardware clock (NVRAM/battery-backed) may be failing. Check `show clock detail` for hardware vs NTP source.
- **Sudden large offset.** Upstream NTP server may have jumped. Check upstream peer health. If using internet NTP, verify no BGP hijack of NTP server IPs.
- **Offset oscillating.** Network latency to NTP peer is variable (common with internet peers). Use closer/more stable NTP sources. Consider GPS-synced stratum-1 for critical infrastructure.

## SPL

```spl
index=network (sourcetype="sc4snmp:metric" OR sourcetype="snmp:metric") metric_name="ntpSysOffset" earliest=-24h
| eval offset_ms=abs(metric_value * 1000)
| timechart span=1h avg(offset_ms) as avg_offset_ms max(offset_ms) as max_offset_ms by host
| untable _time host values
| rex field=host "^(?<device>.+)$"
| stats latest(avg_offset_ms) as current_offset_ms by device
| eval status=case(
    current_offset_ms > 500, "CRITICAL — " . round(current_offset_ms, 1) . "ms drift (Kerberos will fail)",
    current_offset_ms > 100, "HIGH — " . round(current_offset_ms, 1) . "ms drift (log correlation impacted)",
    current_offset_ms > 50, "WARNING — " . round(current_offset_ms, 1) . "ms drift",
    1=1, null())
| where isnotnull(status)
| sort -current_offset_ms
```

## Visualization

(1) Gauge: worst fleet clock offset. (2) Table: devices with excessive drift. (3) Timechart: 30-day drift trend.

## Known False Positives

**Initial boot offset.** After a router reboot, NTP takes 5-15 minutes to synchronize. The offset may be large initially. Exclude devices with uptime <30 minutes from alerting.

**Network path latency spikes.** Transient network congestion between device and NTP peer can cause brief offset spikes. Require sustained drift (>1 hour) before alerting.

## References

- [RFC 5905 — Network Time Protocol Version 4](https://www.rfc-editor.org/rfc/rfc5905)
- [RFC 5907 — Definitions of Managed Objects for NTP](https://www.rfc-editor.org/rfc/rfc5907)
