<!-- AUTO-GENERATED from UC-5.17.1.json — DO NOT EDIT -->

---
id: "5.17.1"
title: "Packet Broker Port Utilization and Oversubscription"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.17.1 · Packet Broker Port Utilization and Oversubscription

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch how full the special switches are that copy internet traffic to our safety tools. When those lanes stay stuffed too long, we raise our hands before copies get trimmed and something important goes unseen.*

---

## Description

Splunk rolls half-hour utilization percentiles per packet-broker host so saturated ingress-to-tool paths and asymmetric RX/TX spikes surface before filters drop packets or tools miss flows during renewal-driven traffic growth.

## Value

Network visibility owners defend tool-chain budgets with quantitative port-headroom evidence while NOC teams shrink blind spots by paging before oversubscribed maps exhaust buffering during peak east-west bursts.

## Implementation

Normalize utilization and nominal speed fields across SNMP and vendor APIs, land data on a shared visibility index, schedule the search hourly with an alert on sustained p95_util ≥90% for two consecutive buckets per host.

## Detailed Implementation

### Prerequisites
- Authoritative inventory tying `host`, rack, `port_id`, connected TAP/SPAN sources, and subscribed tool destinations.
- Agreed baseline index (`visibility` recommended) with ACLs shared by NetOps and SecOps.
- Verified clock sync on brokers and pollers so `_time` aligns with CLI graphs.

### Step 1 — Configure data collection
Enable SNMP `IF-MIB` walks or streaming telemetry from Gigamon, Keysight Vision, cPacket, APCON, and Garland controllers; supplement with REST pulls where utilization is only exposed via API. Map octet counters to Mbps using documented sampling intervals.

### Step 2 — Field normalization
Use `props.conf` transforms and `FIELDALIAS` so multiple vendor keys collapse into `worst`, `cap_mbps`, and `port_id`. Document null-handling when hardware omits TX utilization on passive optical paths.

### Step 3 — Create saved search and alert
Save SPL as `pktbrk_port_util_oversub`; alert when `oversubscribed=1` for three thirty-minute buckets within six hours for any production `host`, excluding tagged maintenance windows via a lookup.

### Step 4 — Validate
Pick three interfaces, compare Splunk `peak_util` against vendor GUI or CLI `show port` statistics during a known backup window; discrepancies beyond five points trigger TA review.

### Step 5 — Operationalize
Dashboard row stacks timecharts per vendor with drilldown to raw interface events; annotate planned bandwidth uplifts as Splunk suppress markers so auditors understand acknowledged debt.

## SPL

```spl
index=network OR index=infra OR index=visibility earliest=-24h@h latest=now
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"gigamon"),"Gigamon GigaVUE",match(v,"keysight|ixia|vision|hawk"),"Keysight Vision",match(v,"cpacket|cstor"),"cPacket cStor",match(v,"apcon"),"APCON",match(v,"garland"),"Garland","other")
| where vendor!="other"
| eval rx=tonumber(coalesce(rx_util_pct,ingress_util_pct,if_in_util_pct,line_rx_util))
| eval tx=tonumber(coalesce(tx_util_pct,egress_util_pct,if_out_util_pct,line_tx_util))
| eval worst=coalesce(if(rx>tx OR isnull(tx),rx,null()), if(tx>rx OR isnull(rx),tx,null()), rx, tx)
| eval cap_mbps=tonumber(coalesce(port_speed_mbps,line_speed_mbps,if_speed_mbps))
| bin _time span=30m
| stats perc95(worst) as p95_util max(worst) as peak_util avg(worst) as avg_util latest(cap_mbps) as nominal_speed values(port_alias) as labels dc(port_id) as ports_seen by _time vendor host
| eval oversubscribed=if(p95_util>=90 OR peak_util>=98,1,0)
| where oversubscribed=1 OR peak_util>=85
| sort - peak_util vendor host _time
```

## Visualization

Dashboard Studio: KPI row for count of oversubscribed hosts; middle `splunk.timechart` of p95_util by vendor; bottom drilldown table (`host`, `port_id`, `peak_util`, `nominal_speed`, labels).

## Known False Positives

**SNMP counter wraps / 32-bit ifSpeed:** bogus 100% spikes after rollover until transforms upgrade to 64-bit counters.**Passive TAP legs:** may lack meaningful TX utilization—exclude via lookup.**Transient backup spikes:** fifteen-minute peaks during DR tests mimic chronic oversubscription.**Mis-labeled line speeds:** incorrect `ifHighSpeed` yields false headroom—cross-check procurement BOM.**Duplicate polls:** double-counted utilization inflates averages—dedupe by `(host,port_id,_time)`.

## References

- [Splunk Documentation — Splunk Connect for SNMP overview](https://docs.splunk.com/Documentation/SC4SNMP/)
- [Gigamon Product Documentation — GigaVUE Fabric Manager](https://docs.gigamon.com/)
- [Keysight Network Visibility Solutions — Vision portfolio](https://www.keysight.com/us/en/products/network-test/network-visibility-solutions.html)
