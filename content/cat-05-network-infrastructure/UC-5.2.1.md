<!-- AUTO-GENERATED from UC-5.2.1.json — DO NOT EDIT -->

---
id: "5.2.1"
title: "Top Denied Traffic Sources"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.1 · Top Denied Traffic Sources

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch which sources are blocked most often on the firewall so we can fix misrouted traffic, bad rules, and scanning before a small problem spreads.*

---

## Description

Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps. NIST SP 800-119 expects IPv6 firewall and filtering parity with IPv4 — include IPv6 deny visibility in the same program.

## Value

Security teams identify top denied traffic sources across multi-vendor firewalls, distinguishing reconnaissance scanning from misconfigured applications using target diversity and port spread analysis.

## Implementation

Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.

## Detailed Implementation

### Prerequisites
* Firewall traffic logs forwarded to Splunk. Data in `index=firewall` with sourcetypes per vendor: Palo Alto `pan:traffic`, Fortinet `fgt_traffic`, Cisco FTD `cisco:firepower:syslog`, Juniper SRX `juniper:junos:firewall`. Key fields: `action=denied/blocked/drop`, `src_ip`, `dest_ip`, `dest_port`, `rule`, `app`.
* Install the appropriate TA: `Splunk_TA_paloalto` (Splunkbase 2757), `TA-fortinet_fortigate` (Splunkbase 2846), `Splunk_TA_cisco-firepower` (Splunkbase 4830), `Splunk_TA_juniper` (Splunkbase 2847).
* Create `firewall_zones.csv` lookup: `src_zone`, `dest_zone`, `zone_classification` (internal/dmz/external/partner).

### Step 1 — - Configure data collection
**Palo Alto (syslog):**
```
# Device > Server Profiles > Syslog > add profile
# Objects > Log Forwarding > add traffic log filter: action=deny
# Commit and push to managed devices
```
**Fortinet (syslog):**
```
config log syslogd setting
    set status enable
    set server <splunk_syslog_ip>
    set port 514
    set facility local7
end
```
Verify ingestion:
```spl
index=firewall (action=denied OR action=blocked OR action=drop OR action=deny) earliest=-4h
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Top denied traffic sources with context:**
```spl
index=firewall (action=denied OR action=blocked OR action=drop OR action=deny) earliest=-4h
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| eval dport=coalesce(dest_port, dstport, dst_port)
| eval fw_action=lower(coalesce(action, policy_action))
| eval app_name=coalesce(app, application, service)
| lookup firewall_zones.csv src_zone, dest_zone OUTPUT zone_classification
| stats count as denials dc(dst) as unique_targets dc(dport) as unique_ports values(app_name) as apps latest(_time) as last_seen by src, host
| eval severity=case(denials > 10000 AND unique_targets > 100, "CRITICAL -- possible scanning/worm", denials > 5000 AND unique_ports > 50, "HIGH -- port sweep", denials > 1000, "WARNING -- elevated denials", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -denials
```

**Denied traffic by zone pair (identifies policy gaps):**
```spl
index=firewall (action=denied OR action=blocked OR action=drop) earliest=-4h
| eval src_z=coalesce(src_zone, from_zone, ingress_zone)
| eval dst_z=coalesce(dest_zone, to_zone, egress_zone)
| stats count as denials dc(src_ip) as unique_sources by src_z, dst_z
| sort -denials
```

### Step 3 — - Validate
(a) Cross-reference top denied source with firewall management console (Panorama, FortiAnalyzer, FMC).
(b) Verify action field normalization: run `| stats count by action` and confirm deny/block/drop variants are captured.
(c) Confirm no legitimate traffic is being denied by checking a sample of denied flows against change tickets.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Denied Traffic Analysis"):
* Row 1 -- Single-value: "Total denials (4h)", "Unique denied sources", "Unique targets", "Top denied app".
* Row 2 -- Top denied sources with severity rating.
* Row 3 -- Denied flows by zone pair.

Alerting:
* Critical (> 10K denials from single source with > 100 targets): active scanning.
* High (> 5K denials with > 50 ports): port sweep reconnaissance.
* Warning (new source with > 1K denials): investigate new deny patterns.

### Step 5 — - Troubleshooting

* **Legitimate traffic denied** -- Check: (1) recent firewall policy change (UC-5.2.2), (2) expired temporary rule, (3) application update using new ports/IPs. Cross-reference with change management.

* **Single IP generating massive denials** -- Possible causes: (1) compromised host scanning internally, (2) misconfigured application retrying failed connections, (3) worm propagation. Quarantine and investigate.

* **Deny counts differ between Splunk and firewall console** -- Verify: (1) all firewall nodes are forwarding logs, (2) syslog transport is reliable (use TCP, not UDP), (3) Splunk indexing lag.

**IPv6 Coverage:** NIST SP 800-119 requires equivalent IPv6 firewall rules. Add `| eval ip_version=if(match(src, ":"), "IPv6", "IPv4")` to segment by protocol version. Verify IPv6 deny logs are being captured — many firewalls have IPv6 logging disabled by default.

## SPL

```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest) as unique_dests by src
| sort -denials | head 20 | lookup geoip ip as src OUTPUT Country
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
| sort -count
```

## Visualization

Table (source, denials, dests), Map (GeoIP), Bar chart.

## Known False Positives

Traffic spikes during backup windows, software distribution, or scheduled data syncs can add denied flows without an attack.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
