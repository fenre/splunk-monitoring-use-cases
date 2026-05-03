<!-- AUTO-GENERATED from UC-5.21.1.json — DO NOT EDIT -->

---
id: "5.21.1"
title: "Network Device NTP Peer Reachability and Stratum Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.21.1 · Network Device NTP Peer Reachability and Stratum Tracking

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We make sure all the clocks on our network equipment are keeping accurate time by watching their connection to the master clock. If a router's clock drifts, it can mess up security, log records, and everything that depends on knowing the exact time.*

---

## Description

Monitors NTP peer reachability and stratum on network devices. Network routers and switches typically serve as stratum-2 or stratum-3 NTP servers for downstream infrastructure. If these devices lose NTP synchronization, clock drift propagates to every system that references them, breaking log correlation, certificate validation, DNSSEC, Kerberos authentication, and forensic timelines.

## Value

Accurate time synchronization is foundational for security (Kerberos has a 5-minute tolerance, DNSSEC signatures have validity windows, log correlation requires sub-second accuracy). When a core router loses NTP sync, hundreds of downstream devices inherit the drift. This UC catches NTP failures at the network device level — the root of the time hierarchy — before the impact cascades to applications and security systems.

## Implementation

Monitor NTP syslog events from network devices. Track peer reachability, synchronization status, and stratum changes. Alert on clock unsynchronized or peer unreachable events.

## Detailed Implementation

### Prerequisites
- NTP configured on all network devices with at least 2 upstream peers for redundancy.
- Syslog from network devices to Splunk via `TA-cisco_ios` or vendor-specific TA.
- Cisco: `ntp logging` enabled in global configuration to generate syslog events for NTP state changes.
- Juniper: `set system ntp` with multiple server entries.

### Step 1 — Configure NTP logging on devices
Cisco IOS/IOS-XE:
```
ntp logging
ntp server 10.1.1.1
ntp server 10.1.1.2
ntp authenticate
ntp authentication-key 1 md5 <key>
ntp trusted-key 1
```

Verify NTP events arrive:
```spl
index=network sourcetype="cisco:ios" NTP earliest=-24h | stats count by host
```

### Step 2 — Create monitoring searches
The primary search (above) classifies NTP events by severity.

**SNMP-based NTP peer status (complement to syslog):**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ntpAssocStatReach" earliest=-1h
| eval reach_hex=printf("%02x", metric_value)
| eval reachable=if(metric_value > 0, "yes", "no")
| stats latest(reachable) as status latest(reach_hex) as reach_register by host
| where status="no"
```

### Step 3 — Validate
(a) On a router, run `show ntp status` and `show ntp associations`. Compare stratum, peer reachability, and offset with Splunk data.
(b) Temporarily add an unreachable NTP server. Verify the PEER_UNREACHABLE alert fires.
(c) Check that the router's stratum matches expectations (stratum-2 if peering with a stratum-1 GPS/atomic source, stratum-3 if peering with a stratum-2).

### Step 4 — Operationalize
Dashboard ("Network Device NTP Health"):
- Row 1 — Single-value: devices with clock unsynchronized (red if >0), devices with peer unreachable (yellow if >0).
- Row 2 — Table: host, peers, stratum, last_event, severity.
- Row 3 — Timechart: NTP events over 7 days.

Alerting:
- CLOCK_UNSYNC on any core/distribution device: page network operations immediately.
- PEER_UNREACHABLE persisting >30 minutes: investigate — upstream NTP server may be down.

### Step 5 — Troubleshooting
- **All peers unreachable simultaneously:** Upstream NTP servers or the network path to them is down. Check firewall rules for UDP 123. Verify DNS resolution if using NTP server FQDNs.
- **Stratum increased unexpectedly:** The primary upstream peer is down and the device fell back to a secondary with higher stratum. Investigate the primary peer.
- **Clock offset >128ms:** NTP will refuse to step the clock if offset exceeds the panic threshold. Manual intervention: `clock set` then restart NTP.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos:structured") earliest=-24h
  ("NTP" AND ("reachable" OR "not reachable" OR "sync" OR "unsync" OR "stratum" OR "peer"))
| eval ntp_event=case(
    match(_raw, "(?i)not.?reachable|unreachable|peer.*lost"), "PEER_UNREACHABLE",
    match(_raw, "(?i)clock.*not.*sync|unsynchronized|no.*valid"), "CLOCK_UNSYNC",
    match(_raw, "(?i)reachable|peer.*up"), "PEER_REACHABLE",
    match(_raw, "(?i)stratum.*change|stratum"), "STRATUM_CHANGE",
    1=1, "NTP_EVENT")
| rex field=_raw "(?:peer|server)\s*(?<ntp_peer>[\d\.]+|[0-9a-fA-F:]+)"
| rex field=_raw "stratum\s*(?<stratum>\d+)"
| stats count as events latest(ntp_event) as last_event values(ntp_peer) as peers values(stratum) as stratum by host
| eval severity=case(
    last_event="CLOCK_UNSYNC", "CRITICAL — " . host . " clock unsynchronized",
    last_event="PEER_UNREACHABLE" AND events > 3, "HIGH — NTP peer unreachable on " . host,
    last_event="STRATUM_CHANGE", "MEDIUM — stratum changed on " . host,
    1=1, null())
| where isnotnull(severity)
| sort -events
```

## Visualization

(1) Single-value: unsynchronized devices. (2) Table: NTP peer status per device. (3) Timechart: NTP events. (4) Gauge: fleet NTP health %.

## Known False Positives

**Brief NTP peer flaps.** NTP peers may briefly show unreachable during network convergence events. Require sustained unreachability (>15 minutes) before alerting.

**Stratum changes during planned maintenance.** When primary NTP servers are taken offline for maintenance, devices naturally fall back to secondary peers at higher stratum. Correlate with maintenance windows.

## References

- [Cisco — NTP Configuration Guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/bsm/configuration/xe-3s/bsm-xe-3s-book/bsm-time-ntp.html)
- [RFC 5905 — Network Time Protocol Version 4](https://www.rfc-editor.org/rfc/rfc5905)
