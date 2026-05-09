<!-- AUTO-GENERATED from UC-5.1.70.json — DO NOT EDIT -->

---
id: "5.1.70"
title: "NTP Stratum and Peer Health on Network Devices"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.70 · NTP Stratum and Peer Health on Network Devices

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance, Availability &middot; **Wave:** Crawl &middot; **Status:** Community

*We make sure every router and switch has the right time. Wrong time on even one device corrupts every log we collect from it — making investigations and audits unreliable. We catch a device the moment its clock starts to drift and tell the team to fix it before the wrong-time data gets baked into reports.*

---

## Description

Surfaces network devices whose NTP peer associations have failed or whose local clock has drifted unsynchronised. Counts events per host and presents the worst offenders at the top — these are the routers and switches whose log timestamps are about to skew, breaking SIEM correlation and forensics integrity.

## Value

Accurate time on every device is a foundational requirement that nobody notices until it breaks: log correlation across vendors requires sub-second alignment, X.509 certificates check `Not Before` / `Not After` against device clock, regulatory frameworks (PCI DSS 10.4, HIPAA `§164.312(b)`, SOX ITGC) explicitly require time synchronisation, and Splunk's own `_time` field comes from the device clock. Stratum drift on a single core router can cascade into stratum drift on every downstream peer that points at it. This is a low-difficulty, high-leverage UC — every Splunk deployment should have it as a crawl-tier baseline because the cost of having every other UC silently mis-correlated is enormous and discovered after the fact.

## Implementation

Configure NTP on every network device, pointing at internal NTP servers (never public pools) for compliance reasons. Enable NTP syslog at severity 4 or lower. Optionally poll the NTP-MIB via SNMP for `ntpSysPeerOffset` (millisecond drift from peer) and `ntpSysStratum` (the device's stratum number). Alert when stratum exceeds 4 (you have left the trusted internal time hierarchy) or when peer associations drop entirely.

## SPL

```spl
index=network (sourcetype="cisco:ios" "%NTP-4-PEER_NO_ASSOC" OR "%NTP-4-CLOCK_UNSYNC")
  OR (sourcetype="junos:syslog" "NTPD_PEER_NO_RESPONSE")
| stats count by host
| where count > 0
| sort - count
```

## Visualization

Single-value (devices with NTP issues right now), Table (per-device NTP-event counts and last-seen timestamps), Gauge (stratum distribution across the fleet — concentration at stratum 2–3 is healthy, drift to 4–5 is a warning).

## Known False Positives

**Initial sync after device reboot.** A device that has just booted will spend several minutes unsynchronised before its first NTP poll completes. Tolerate a 5-minute warm-up window after `%SYS-5-RESTART`.

**Internet-bound NTP servers blocked by firewall change.** A new firewall rule that blocks egress UDP 123 will silently break NTP for every device pointing at an external pool. The alert here is correct — make the actionable owner the firewall team, not the network team.

**Lab devices intentionally desynchronised.** Test devices where engineers are validating clock-skew behaviour will alarm forever. Filter alerts to production loopback ranges only.

## References

- [RFC 5905 — Network Time Protocol Version 4](https://www.rfc-editor.org/rfc/rfc5905)
- [Cisco NTP best practices](https://www.cisco.com/c/en/us/support/docs/availability/high-availability/19643-ntpm.html)
- [PCI DSS Requirement 10.4 — time synchronisation](https://www.pcisecuritystandards.org/document_library/)
