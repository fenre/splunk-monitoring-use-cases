<!-- AUTO-GENERATED from UC-5.15.8.json — DO NOT EDIT -->

---
id: "5.15.8"
title: "Infoblox DNS Query Volume Anomalies per Client (DGA and Tunneling Indicators) (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.15.8 · Infoblox DNS Query Volume Anomalies per Client (DGA and Tunneling Indicators) (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly &middot; **Wave:** Run &middot; **Status:** Verified

*We notice when one computer asks for an unusually huge mix of weird website names in a short time, because that pattern sometimes means trouble hiding inside normal internet lookups.*

---

## Description

Statistical profiling flags internal DNS clients issuing unusually high query counts with high ratios of unique labels and longer average hostname lengths—patterns commonly associated with DGAs or tunnel-like chatter needing analyst review.

## Value

Security operations gain an early hunting signal grounded in resolver telemetry already collected for operations, prioritizing hosts before DNS tunneling saturates resolver CPU or exfiltration succeeds.

## Implementation

Require consistent client IP visibility (avoid blind forwarding chains); tune floors (`count`, `ratio`) per campus; feed results into ES notable or SOAR playbook for host isolation decisions.

## Detailed Implementation

### Prerequisites
- Recursive query logging enabled at manageable sampling if necessary.
- Known resolver IPs excluded via `infoblox_known_resolvers.csv` lookup.
- Legal/privacy review for monitoring internal client DNS metadata.

### Step 1 — Configure data collection
Validate extracted fields (`src_ip`, `qname`). If only upstream resolver IP appears, enrich via DHCP correlation or postpone use case.

### Step 2 — Create the search and alert
Use primary SPL nightly; clone with `bucket span=5m` for faster detection in SOC tier. Combine with `infoblox:threatprotect` hits when available.

### Step 3 — Validate
Replay PCAP-derived DNS from test malware samples in lab—ensure SPL surfaces seeded victim IP without flooding benign AV updaters (whitelist vendors).

### Step 4 — Operationalize
Risk scoring widget, analyst worksheet linking to sandbox DNS visualization, feedback loop lowering threshold for crown-jewel subnets.

### Step 5 — Troubleshooting
**CDN browsers:** Some patch engines mimic high uniqueness—maintain vendor domain allowlists.**IPv6 privacy:** rotating addresses dilute `src_ip` correlation.**Performance:** narrow earliest window or adopt summary indexing.

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-24h
| where match(lower(coalesce(query_type,qtype_name,"")),"a|aaaa|any")
| eval qlen=len(qname)
| stats count dc(qname) as uniq_names avg(qlen) as avg_label_len stdev(qlen) as sd_label by src_ip host
| eval ratio=if(count>0, round(uniq_names/count,3), 0)
| eventstats median(count) as med_cnt p95(count) as p95_cnt
| eval volume_score=if(count > p95_cnt, count/med_cnt, 0)
| where count>=500 AND ratio>=0.85 AND avg_label_len>=18 AND volume_score>=3
| sort - volume_score
| head 100
```

## CIM SPL

```spl
| tstats `summariesonly` dc(DNS.query) as uq count from datamodel=Network_Resolution where nodename=Network_Resolution.DNS by DNS.src span=15m
| where count>100
```

## Visualization

Scatter plot uniq_names vs count, table with avg_label_len and ratio, drilldown to raw queries filtered by src_ip.

## Known False Positives

**Security scanners:** Vulnerability tools generate massive unique fqdns legitimately.**Misconfigured IoT:** buggy firmware can mimic random labels.**NAT pooling:** Shared egress hides true offenders until DHCP correlation applied.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [MITRE ATT&CK — Application Layer Protocol (DNS)](https://attack.mitre.org/)
