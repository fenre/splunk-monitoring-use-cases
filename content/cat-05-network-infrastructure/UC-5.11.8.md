<!-- AUTO-GENERATED from UC-5.11.8.json — DO NOT EDIT -->

---
id: "5.11.8"
title: "BGP Prefix Count and Route Churn Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.11.8 · BGP Prefix Count and Route Churn Monitoring

## Description

A sudden jump in received BGP prefixes could indicate a route leak, hijack, or misconfigured peer advertising a full table into a leaf switch. Conversely, a prefix count drop means routes are being withdrawn — potentially black-holing traffic. Streaming prefix counts via gNMI at 30-second intervals detects these events far faster than waiting for syslog or SNMP traps.

## Value

A sudden jump in received BGP prefixes could indicate a route leak, hijack, or misconfigured peer advertising a full table into a leaf switch. Conversely, a prefix count drop means routes are being withdrawn — potentially black-holing traffic. Streaming prefix counts via gNMI at 30-second intervals detects these events far faster than waiting for syslog or SNMP traps.

## Implementation

Subscribe to BGP AFI-SAFI state at 30s intervals. Baseline normal prefix counts per peer. Alert on >10% change in a 5-minute window or absolute change >1000 prefixes. A full BGP table leak (800k+ IPv4 prefixes) into a leaf with 64k TCAM will crash forwarding — detect it before the FIB overflows. Correlate with CPU spikes (UC-5.11.4) during convergence events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state` (prefixes/received, prefixes/installed); Telegraf metric: `openconfig_bgp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to BGP AFI-SAFI state at 30s intervals. Baseline normal prefix counts per peer. Alert on >10% change in a 5-minute window or absolute change >1000 prefixes. A full BGP table leak (800k+ IPv4 prefixes) into a leaf with 64k TCAM will crash forwarding — detect it before the FIB overflows. Correlate with CPU spikes (UC-5.11.4) during convergence events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats latest("openconfig_bgp.prefixes_received") AS prefixes WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name span=5m
| streamstats current=f last(prefixes) AS prev_prefixes by host, neighbor_address, afi_safi_name
| eval delta=prefixes - prev_prefixes, pct_change=if(prev_prefixes>0, round(delta*100/prev_prefixes, 1), 0)
| where abs(pct_change) > 10 OR abs(delta) > 1000
| table _time, host, neighbor_address, afi_safi_name, prev_prefixes, prefixes, delta, pct_change
| sort -abs(delta)
```

Understanding this SPL

**BGP Prefix Count and Route Churn Monitoring** — A sudden jump in received BGP prefixes could indicate a route leak, hijack, or misconfigured peer advertising a full table into a leaf switch. Conversely, a prefix count drop means routes are being withdrawn — potentially black-holing traffic. Streaming prefix counts via gNMI at 30-second intervals detects these events far faster than waiting for syslog or SNMP traps.

Documented **Data sources**: gNMI path: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state` (prefixes/received, prefixes/installed); Telegraf metric: `openconfig_bgp`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `streamstats` rolls up events into metrics; results are split **by host, neighbor_address, afi_safi_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where abs(pct_change) > 10 OR abs(delta) > 1000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **BGP Prefix Count and Route Churn Monitoring**): table _time, host, neighbor_address, afi_safi_name, prev_prefixes, prefixes, delta, pct_change
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

CIM and metrics: BGP prefix counts use **mstats**; do not use Network_Traffic CIM as a stand-in for prefix churn.


Step 3 — Validate
Compare prefix counts or update churn in Splunk to `show bgp` table size or the vendor’s monitoring tile for the same peer; long BGP refresh windows can look like false churn.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (prefix count per peer over time), Table (peers with recent churn), Single value (total fabric prefix count), Alert list (abnormal changes).

## SPL

```spl
| mstats latest("openconfig_bgp.prefixes_received") AS prefixes WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name span=5m
| streamstats current=f last(prefixes) AS prev_prefixes by host, neighbor_address, afi_safi_name
| eval delta=prefixes - prev_prefixes, pct_change=if(prev_prefixes>0, round(delta*100/prev_prefixes, 1), 0)
| where abs(pct_change) > 10 OR abs(delta) > 1000
| table _time, host, neighbor_address, afi_safi_name, prev_prefixes, prefixes, delta, pct_change
| sort -abs(delta)
```

## Visualization

Line chart (prefix count per peer over time), Table (peers with recent churn), Single value (total fabric prefix count), Alert list (abnormal changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
