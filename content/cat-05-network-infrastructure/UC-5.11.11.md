<!-- AUTO-GENERATED from UC-5.11.11.json — DO NOT EDIT -->

---
id: "5.11.11"
title: "ACL Hit Counter Analysis via Streaming Telemetry"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.11.11 · ACL Hit Counter Analysis via Streaming Telemetry

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance

*We help you see which firewall or switch rules are really being hit, so you can clean dead rules and see where attacks or mistakes show up in traffic.*

---

## Description

ACL rules that never match traffic are dead weight that slows TCAM lookups and obscures security intent. Conversely, deny rules with climbing hit counts reveal active attack patterns. Streaming ACL counters via gNMI at 30-second intervals provides the data needed for security policy effectiveness analysis and ACL cleanup — tasks that are nearly impossible with periodic SNMP polling.

## Value

Security and network operations teams leverage ACL hit counter streaming to detect active scanning/probing in real time, identify dead rules for TCAM optimization, and validate that security policies are being enforced as designed.

## Implementation

Subscribe to `/acl/acl-sets/acl-set/acl-entries/acl-entry/state` at 30s intervals. Identify deny rules with increasing hit counts — these represent blocked attack traffic. Identify permit rules with zero hits over 30 days — candidates for cleanup. Cross-reference with firewall logs and IDS alerts for security correlation. Generate monthly ACL effectiveness reports for compliance.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with SAMPLE subscription to ACL hit counters. OpenConfig path: `/acl/acl-sets/acl-set/acl-entries/acl-entry/state/matched-packets` and `matched-octets`. These are cumulative counters per ACL entry — use `mstats rate_avg()` to compute hit rates.
- Vendor-specific paths: Cisco NX-OS: `openconfig-acl` supported for some ACL types; IOS-XR: `Cisco-IOS-XR-ipv4-acl-oper:ipv4-acl-and-prefix-list/oper` or native YANG; Arista EOS: OpenConfig ACL counters supported; Juniper: `junos-firewall-state`.
- Understanding ACL analytics: ACL hit counters reveal which rules are actually being used (and which are dead rules that can be cleaned up), which deny rules are being triggered (security events), and how traffic patterns change over time. Streaming ACL counters at 30s intervals enables near-real-time security event detection.
- Build an `acl_rules.csv` lookup: `host,acl_name,sequence_num,action,description` (e.g., `leaf-01,EDGE-IN,10,permit,Allow HTTPS`, `leaf-01,EDGE-IN,100,deny,Default deny`).
- ACL counters are TCAM-resident on hardware switches. Not all platforms support per-entry counters via gNMI — some only provide aggregate counters per ACL. Verify platform support.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_acl"
  origin = "openconfig"
  path = "/acl/acl-sets/acl-set/acl-entries/acl-entry/state"
  subscription_mode = "sample"
  sample_interval = "30s"
```

Verify ACL metrics:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics
| search metric_name="openconfig_acl*"
```

### Step 2 — Create the search and alert

**Primary search — ACL deny rule hit rate (security events):**
```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hit_rate WHERE index=gnmi_metrics BY host, acl_name, sequence_num span=1m
| eval hits_per_min=round(hit_rate*60, 0)
| where hits_per_min > 0
| lookup acl_rules.csv host acl_name sequence_num OUTPUT action description
| where action="deny"
| eval severity=case(hits_per_min > 1000, "CRITICAL", hits_per_min > 100, "HIGH", hits_per_min > 10, "MEDIUM", 1==1, "LOW")
| sort -hits_per_min
```

#### Understanding this SPL: Every hit on a deny ACL rule is a blocked connection attempt. High hit rates on deny rules indicate: active scanning/probing against your network, misconfigured applications trying to reach blocked destinations, or DDoS traffic being filtered. The `acl_rules.csv` lookup provides the business context for each rule — "Default deny hit rate of 10,000/min" vs. "Block SSH from outside hit rate of 10,000/min" have very different severity implications.

**Dead rule detection — unused ACL entries:**
```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hit_rate WHERE index=gnmi_metrics BY host, acl_name, sequence_num span=1d earliest=-30d
| stats sum(hit_rate) AS total_hit_rate by host, acl_name, sequence_num
| where total_hit_rate < 0.001
| lookup acl_rules.csv host acl_name sequence_num OUTPUT action description
| eval recommendation="Rule has zero hits in 30 days — candidate for removal or review"
| sort host, acl_name, sequence_num
```

#### Understanding this SPL: Rules with zero hits over 30 days are likely dead (no longer needed). Removing dead rules reduces TCAM utilization (critical on hardware switches with limited TCAM), simplifies policy management, and reduces the risk of "shadow rules" (unused rules that accidentally permit traffic if a preceding rule is removed).

**ACL hit rate anomaly — sudden deny spike:**
```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hit_rate WHERE index=gnmi_metrics BY host, acl_name, sequence_num span=5m earliest=-24h
| lookup acl_rules.csv host acl_name sequence_num OUTPUT action description
| where action="deny"
| eval hits_per_min=round(hit_rate*60, 0)
| eventstats avg(hits_per_min) AS avg_hits stdev(hits_per_min) AS std_hits by host, acl_name, sequence_num
| where hits_per_min > avg_hits + (4 * std_hits) AND hits_per_min > 50
| eval spike_factor=round(hits_per_min/if(avg_hits>0, avg_hits, 1), 1)
| sort -spike_factor
```

### Step 3 — Validate
(a) On the device: `show access-lists <name>` (with hit counters enabled). Compare hit counts with the `mstats` rate.
(b) Test: generate traffic that matches a specific deny rule and verify the hit rate increases in Splunk.
(c) Verify the `acl_rules.csv` lookup by comparing with the running ACL configuration on each device.

### Step 4 — Operationalize
Dashboard ("Security — ACL Hit Counter Analysis"):
- Row 1 — Single-value tiles: "Active deny hits/min", "Deny rules with activity", "Dead rules (30d)", "ACL anomaly alerts".
- Row 2 — Table: deny rule hits — host, acl_name, rule description, hits_per_min, severity.
- Row 3 — Timechart: deny hit rates over 24h for top 10 rules.
- Row 4 — Dead rule table: host, ACL, sequence, description, recommendation.

Alerting:
- Critical (deny rule spike > 4 sigma, sustained 5+ minutes): possible scan or DDoS — alert security.
- High (default deny hits > 1000/min from a single source): active probing — investigate source.
- Informational (monthly dead rule report): email to ACL policy owners for cleanup.

Runbook:
1. **Deny rule spike**: Identify the source IPs being denied (if gNMI provides per-source counters, or correlate with firewall logs). Determine if it's a scan (many sources), a misconfigured application (one source, known internal), or an attack.
2. **Dead rule cleanup**: Review each dead rule with the original author/owner. Confirm it's safe to remove. Implement change during maintenance window with a backout plan.
3. **High baseline deny rate**: Some deny rules always get hits (broadcast filtering, general internet noise). Set per-rule baselines to avoid alert fatigue.

### Step 5 — Troubleshooting

- **ACL counter metrics not available** — Some platforms don't expose per-entry ACL counters via gNMI. Check platform documentation. Alternatives: use SNMP (if ACL MIBs are available) or parse `show access-lists` output via Splunk scripted inputs.

- **Counters always zero despite known traffic** — ACL hit counting may need to be explicitly enabled on some platforms. On Cisco NX-OS: `ip access-list <name>` then `statistics per-entry`. On Arista: counters are enabled by default.

- **ACL names differ between gNMI and CLI** — Some platforms use different naming conventions in gNMI (e.g., prefixed with the interface or direction). Normalize in the lookup.

- **TCAM utilization not visible via gNMI** — TCAM usage is typically platform-specific and not part of OpenConfig. Use SNMP or CLI-based monitoring for TCAM capacity.

## SPL

```spl
| mstats rate_avg("openconfig_acl.matched_packets") AS hits_per_sec WHERE index=gnmi_metrics BY host, acl_name, sequence_id, description span=5m
| where hits_per_sec > 0
| eval daily_hits=round(hits_per_sec * 86400, 0)
| table host, acl_name, sequence_id, description, hits_per_sec, daily_hits
| sort -hits_per_sec
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -count
```

## Visualization

Table (ACL rules sorted by hit rate), Bar chart (top 10 deny rules by hits), Stacked chart (permit vs deny hits over time), List (zero-hit rules for cleanup).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
