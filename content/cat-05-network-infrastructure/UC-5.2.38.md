<!-- AUTO-GENERATED from UC-5.2.38.json — DO NOT EDIT -->

---
id: "5.2.38"
title: "Connection Rate Analysis and DOS Detection (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.38 · Connection Rate Analysis and DOS Detection (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We look at new connection rates on small office traffic so floods, scans, and misbehaving clients stand out from everyday browsing.*

---

## Description

Detects denial of service attacks by analyzing abnormal connection establishment rates.

## Value

SOC teams detect denial-of-service attacks against Meraki MX firewalls by analyzing connection rate anomalies and IDS/IPS threat events, enabling rapid incident response.

## Implementation

Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.

## Detailed Implementation

### Prerequisites
* Meraki MX connection and flow data. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:flows`. Key fields: `src`, `dst`, `protocol`, `dport`, `action`.
* DoS detection: analyze connection rates per source IP, SYN flood patterns, and abnormal traffic volumes. Meraki MX IDS/IPS (Snort-based) provides additional detection. Dashboard > Security & SD-WAN > Threat protection.

### Step 1 — - Configure data collection
```
# Meraki Dashboard > Security & SD-WAN > Threat protection
# Mode: Prevention (recommended) or Detection
# Ruleset: Connectivity, Balanced, or Security
# Syslog: enable IDS Alerts and Flows
```
Verify:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:flows") earliest=-1h
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Connection rate anomaly and DoS detection:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:flows") earliest=-1h
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip, dst)
| eval dport=coalesce(dest_port, dport)
| eval proto=coalesce(protocol, transport)
| bin _time span=1m
| stats count as connections dc(dst) as unique_targets dc(dport) as unique_ports by _time, src
| eventstats avg(connections) as avg_conn stdev(connections) as stdev_conn by src
| eval z_score=if(stdev_conn > 0, round((connections - avg_conn)/stdev_conn, 2), 0)
| eval severity=case(
    connections > 1000 AND unique_targets > 50, "CRITICAL -- potential DDoS or scan (high rate + fan-out)",
    z_score > 4 AND connections > 500, "CRITICAL -- anomalous connection spike (z > 4)",
    connections > 500 AND unique_ports > 20, "WARNING -- potential port scan",
    z_score > 3, "WARNING -- elevated connection rate",
    1==1, "OK")
| where severity != "OK"
| iplocation src prefix=src_
| table _time, src, src_Country, connections, unique_targets, unique_ports, z_score, severity
| sort severity, -connections
```

**Secondary search -- IDS/IPS threat events:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)ids|ips|intrusion|threat|signature|attack")
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip, dst)
| eval sig=coalesce(signature, message, priority)
| stats count as hits dc(src) as unique_sources values(src) as source_ips by sig, dst
| sort -hits | head 20
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Threat protection -- compare event counts.
(b) Verify IDS mode (Detection vs Prevention) and ruleset level.
(c) Test with controlled port scan and verify detection.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- DoS and Threat Detection"):
* Row 1 -- Single-value: "Connection anomalies", "IDS events (4h)", "Unique threat sources".
* Row 2 -- Connection rate timechart with anomaly overlay.
* Row 3 -- IDS signature match table.

Alert: Critical (connection rate z-score > 4 with fan-out): immediate SOC investigation.

### Step 5 — - Troubleshooting

* **False positive on high connection rate** -- Legitimate services (CDN, backup, bulk data transfer) can generate high connection rates. Whitelist known services by IP/subnet.

* **IDS not detecting threats** -- Verify IDS is in Prevention mode with Security ruleset. Check that Meraki IDS signature database is current (auto-updated by Meraki cloud).

* **Distributed attack from many sources** -- Per-source analysis may not trigger. Add aggregate connection rate monitoring across all sources to a single destination.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src
| where new_connections > 1000
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Connection rate timeline; source IP detail table; DOS alert dashboard.

## Known False Positives

Scanners, new internet-facing apps, and broken clients can look like a SYN flood in raw statistics.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
