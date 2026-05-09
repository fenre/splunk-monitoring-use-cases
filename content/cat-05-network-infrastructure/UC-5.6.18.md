<!-- AUTO-GENERATED from UC-5.6.18.json — DO NOT EDIT -->

---
id: "5.6.18"
title: "BlueCat DNS Edge Query Analytics"
status: "community"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.18 · BlueCat DNS Edge Query Analytics

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Security &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch how the company's name-lookup service answers questions like 'what's the address for this website?'. When too many lookups come back as 'no such name', that is often the early signal of either a configuration mistake or malware on a computer trying to phone home through randomly-generated domain names.*

---

## Description

Aggregates BlueCat DNS Edge query telemetry by query type and response code, computing the share of NXDOMAIN responses. Surfaces hosts and clients producing elevated NXDOMAIN volume — a classic DGA / C2 telemetry signal — alongside the basic resolver throughput needed for capacity planning.

## Value

BlueCat DNS Edge is the DDI platform of choice for many large enterprises and government deployments where native cloud DNS is not an option. Without the equivalent of bind query logging or Infoblox QIP analytics, BlueCat resolver issues stay invisible until users complain. NXDOMAIN spikes are also one of the most reliable DGA / C2 indicators in the SOC's toolbox — DGA-based malware blasts thousands of randomly-generated domains looking for their command channel, and almost all of them resolve to NXDOMAIN. This UC catches both operational drift and security signals from the same stream.

## Implementation

Configure BlueCat DNS Edge service points to forward query logs to Splunk via syslog or HEC. Install a local props.conf/transforms.conf pair for BlueCat field extraction. Alert on NXDOMAIN spikes (potential DGA/C2 activity) and query volume anomalies.

## SPL

```spl
index=dns sourcetype="bluecat:dns"
| stats count by query_type, response_code
| eventstats sum(count) as total
| eval pct_nxdomain=round(count/total*100,2)
| where response_code="NXDOMAIN"
| sort - count
```

## Visualization

Line chart (query volume over time, separated by response code), Pie chart (response code distribution), Table (top NXDOMAIN domains in the search window).

## Known False Positives

**Recursive resolver caches and local hostname typos.** End users mistyping internal hostnames (`intra.exmaple.com`) generate legitimate NXDOMAIN traffic. Filter on second-level domain or apply a denylist of known internal-typo domains.

**Public chrome-prefetch traffic.** Chromium-based browsers issue speculative NXDOMAIN queries to detect DNS hijacking by network operators. This is a known floor of NXDOMAIN noise that varies by browser version. Use percentile baselines, not absolute counts, for alerting.

**Newly-deployed CNAMEs in transition.** During a CNAME cutover, both the old and new names may serve traffic for hours; clients that cached the old name resolve to NXDOMAIN until TTL expiry. Mute alerts for known-cutover domains during the announced transition window.

## References

- [BlueCat DNS Edge documentation](https://docs.bluecatnetworks.com/r/DNS-Edge-Service-Point-Administration-Guide)
- [BlueCat DDI overview](https://bluecatnetworks.com/products/)
