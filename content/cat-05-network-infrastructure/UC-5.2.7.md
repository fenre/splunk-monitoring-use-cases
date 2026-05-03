<!-- AUTO-GENERATED from UC-5.2.7.json — DO NOT EDIT -->

---
id: "5.2.7"
title: "Connection Rate Anomalies"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.7 · Connection Rate Anomalies

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Anomaly, Performance

*We flag sudden surges in how many connections one host opens so we can see scanning, broken apps, and overload before the network stumbles.*

---

## Description

Sudden connection spikes indicate DDoS, scanning, or worm propagation.

## Value

Security teams detect connection rate anomalies using statistical z-score analysis, distinguishing network scanning, port sweeps, and brute force attacks from legitimate traffic bursts.

## Implementation

Baseline connection rates over 7 days. Alert when rate exceeds 3 standard deviations.

## Detailed Implementation

### Prerequisites
* Firewall traffic/session logs in `index=firewall`. Key fields: `src_ip`, `sessions`, `connections`, `action`. Connection rate anomalies indicate: (1) DDoS attacks, (2) brute force, (3) worm propagation, (4) compromised host scanning.

### Step 1 — - Configure data collection
Verify session/connection data:
```spl
index=firewall earliest=-4h
| eval src=coalesce(src_ip, src, srcaddr)
| bin _time span=5m
| stats count as connections dc(coalesce(dest_ip, dest)) as unique_targets by _time, src
| sort -connections | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Connection rate anomaly detection:**
```spl
index=firewall earliest=-4h
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| eval dport=coalesce(dest_port, dstport)
| bin _time span=5m
| stats count as connections dc(dst) as unique_targets dc(dport) as unique_ports by _time, src, host
| eventstats avg(connections) as avg_conn stdev(connections) as stdev_conn by src
| eval zscore=if(stdev_conn > 0, round((connections - avg_conn) / stdev_conn, 2), 0)
| eval anomaly_type=case(zscore > 5 AND unique_targets > 100, "SCAN -- high target diversity", zscore > 5 AND unique_ports > 50, "PORT_SWEEP -- many ports on few targets", zscore > 5 AND unique_ports = 1 AND connections > 1000, "BRUTE_FORCE -- single port, high rate", zscore > 3, "RATE_ANOMALY", 1==1, null())
| where isnotnull(anomaly_type)
| eval severity=case(match(anomaly_type, "SCAN"), "CRITICAL", match(anomaly_type, "BRUTE_FORCE"), "HIGH", match(anomaly_type, "PORT_SWEEP"), "HIGH", 1==1, "WARNING")
| sort severity, -zscore
```

### Step 3 — - Validate
(a) Baseline connection rates for known hosts during normal operation.
(b) Generate a test scan (nmap from a test host) and verify anomaly detection triggers.
(c) Verify z-score calculation produces sensible results by checking avg_conn and stdev_conn.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Connection Rate Anomalies"):
* Row 1 -- Single-value: "Active anomalies", "Scanning hosts", "Brute force sources".
* Row 2 -- Anomaly events table with z-score.
* Row 3 -- Connection rate timechart for anomalous sources.

Alerting:
* Critical (scan pattern: > 100 unique targets): active network reconnaissance.
* High (brute force: single port > 1K connections): credential attack.
* Warning (rate anomaly z-score > 3): unusual activity.

### Step 5 — - Troubleshooting

* **High z-score but legitimate traffic** -- Backup servers, vulnerability scanners, and monitoring tools naturally create high connection rates. Add to a suppression list after verification.

* **Scanning detection but action=deny** -- The firewall is already blocking the scan, but the volume indicates an active attacker. Consider: (1) block the source at perimeter, (2) report to abuse contact, (3) check for successful connections from the same source.

* **Brute force detection** -- Correlate with authentication logs (UC-5.2.10). Check: did any login succeed from this source? If yes, account may be compromised.

## SPL

```spl
index=firewall
| bin _time span=5m
| stats count as connections by src, _time
| eventstats avg(connections) as avg_c, stdev(connections) as std_c by src
| where connections > (avg_c + 3*std_c)
| sort -connections
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

Line chart with threshold overlay, Table, Timechart.

## Known False Positives

Backups, patches, and file shares can open many connections in a short window and look like a burst.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
