<!-- AUTO-GENERATED from UC-5.16.1.json — DO NOT EDIT -->

---
id: "5.16.1"
title: "WAN Optimizer Throughput and Compression Ratio Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.16.1 · WAN Optimizer Throughput and Compression Ratio Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch how much data shrinks and how quickly it moves across long-distance pipes. When those healthy patterns slump, we catch trouble before everyone notices sluggish files and video calls.*

---

## Description

Hourly Splunk aggregates blend LAN-side versus WAN-side byte counters and vendor-reported compression factors across SteelHead, EdgeConnect, Citrix WANOP, and ZDX-correlated paths so collapsing optimization efficiency appears before circuits saturate.

## Value

Capacity planners receive quantifiable trending that connects shrinking payloads to purchasing fewer Mbps renewals while operators gain early warning before brownouts when ratios drift downward without traffic mix excuses.

## Implementation

Land syslog/metrics on shared indexes, FIELDALIAS common byte and ratio fields, schedule this search as accelerating baseline dataset powering hourly CSV summary plus anomaly alerts on savings_pct drop.

## Detailed Implementation

### Prerequisites
- Dedicated `wanop` summary index or ACL-controlled `network` index receiving SteelHead, EdgeConnect, Citrix WANOP, and optional ZDX feeds.
- Documented field glossary aligning vendor MIB/syslog keys to `pre/post` bytes and ratio metrics.
- Time synchronization (NTP) verified on every appliance pair feeding Splunk.

### Step 1 — Configure data collection
Forward appliance optimization statistics via syslog or modular SNMP polling into Splunk; apply `props.conf` transforms so numeric fields are typed double.

### Step 2 — Create the search and alert
Save the primary SPL as `wanopt_throughput_compression_hourly`; clone an anomaly variant using `streamstats`/`predict` on `savings_pct` per vendor once four weeks of history exist.

### Step 3 — Validate
Pick one branch hour, compare Splunk sums against appliance CLI `show stats` screens or orchestrator UI exports—differences should remain inside rounding tolerance.

### Step 4 — Operationalize
Dashboard row shows dual-axis chart of avg_compression_factor and savings_pct; drilldown passes vendor/host tokens into raw search.

### Step 5 — Troubleshooting
**Null ratios:** confirm FIELDALIAS coverage.**Sudden spikes:** backups or replication swings bypass optimization—annotate maintenance windows.**Multi-site aggregation:** split by `host` when WAN mixes MPLS and DIA paths.

## SPL

```spl
index=wanop OR index=network OR index=infra earliest=-7d@h latest=now
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval pre=tonumber(coalesce(bytes_pre_opt,preopt_bytes,lan_rx_bytes,bytes_before_opt))
| eval post=tonumber(coalesce(bytes_post_opt,postopt_bytes,wan_tx_bytes,bytes_after_opt))
| eval ratio=tonumber(coalesce(compression_ratio,data_reduction_ratio,optimization_ratio))
| eval derived_ratio=if(isnull(ratio) AND pre>0 AND post>0, round(pre/post,3), ratio)
| bin _time span=1h
| stats avg(derived_ratio) as avg_compression_factor sum(pre) as sum_pre sum(post) as sum_post dc(host) as appliance_count by _time vendor
| eval savings_pct=if(sum_pre>0 AND sum_post>=0, round(100*(1-(sum_post/sum_pre)),2), null())
| sort _time vendor
```

## Visualization

Dashboard Studio: top row single-value tiles for 24h savings_pct per vendor; middle `splunk.timechart` of avg_compression_factor; bottom table of appliance_count with sparklines.

## Known False Positives

**Encrypted GRE overlays:** ratios flatline though WAN healthy.**Bulk encrypted video:** legitimately incompressible traffic drags averages.**Mis-tagged sourcetypes:** devices classified `other` disappear from panels yet still consume WAN—watch cardinality.**Scheduled firmware uploads:** temporary ratio dips revert automatically.

## References

- [Splunk Documentation — Get Started with Monitoring Working Examples](https://docs.splunk.com/Documentation/Splunk/latest/Data/MonitorWANtraffic)
- [Riverbed SteelHead Deployment Documentation Portal](https://support.riverbed.com/content/support/software/steelhead.html)
- [HPE Aruba Networking EdgeConnect (Silver Peak) Documentation](https://www.arubanetworks.com/techdocs/EdgeConnect-Premier-orchestrator/introduction/about-this-guide/)
