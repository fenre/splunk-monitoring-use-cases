<!-- AUTO-GENERATED from UC-1.2.137.json — DO NOT EDIT -->

---
id: "1.2.137"
title: "macOS Secure Time Offset vs Stratum-1 Reference"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.137 · macOS Secure Time Offset vs Stratum-1 Reference

## Description

TLS authentication, Kerberos, and MDM certificate validation break when macOS clock skew exceeds hundreds of milliseconds. Lightweight NTP offset probes per host catch silent time drift from dead batteries, virtualization glitches, or captive portal blocks before MFA and VPN begin failing intermittently.

## Value

Stops sporadic auth and VPN failures by proving whether endpoints have drifted from trusted time.

## Implementation

Run a non-privileged `sntp` or `ntpdate -q` against two corporate-approved NTP servers every 15–30 minutes. Parse `offset` into signed `offset_ms`. Include `stratum` if printed. Use `index=os`, `sourcetype=macos_time_sync`. Alert when absolute offset exceeds 500 ms (tighten for finance). Exclude VMs if hypervisor time sync policy differs.

## Detailed Implementation

Prerequisites
• Allow outbound UDP/123 or NTP-over-HTTPS per security policy.
• If `sntp` is absent, bundle `ntpdate` from macOS Command Line Tools.

Step 1 — Scripted input emits JSON: `{"offset_ms":-12.4,"stratum":2}`.

Step 2 — Correlate alerts with Wi-Fi captive portal incidents.

Step 3 — Validate by manually setting clock wrong in lab.

Step 4 — Document tolerance for VMs using host sync.

## SPL

```spl
index=os sourcetype=macos_time_sync host=*
| stats latest(offset_ms) as offset_ms, latest(stratum) as stratum by host
| where abs(offset_ms) > 500
| eval abs_offset=abs(offset_ms)
| table host, offset_ms, abs_offset, stratum
| sort - abs_offset
```

## Visualization

Table (host, offset_ms), Histogram (offset distribution), Map (optional site).

## References

- [NIST SP 800-52 Rev. 2 — TLS guidance (time synchronization context)](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final)
- [Splunk Universal Forwarder macOS install](https://docs.splunk.com/Documentation/Forwarder/latest/Deployment/InstallonmacOS)
