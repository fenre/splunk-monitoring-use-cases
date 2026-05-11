<!-- AUTO-GENERATED from UC-5.18.5.json — DO NOT EDIT -->

---
id: "5.18.5"
title: "MPLS Label Table Utilization"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.18.5 · MPLS Label Table Utilization

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We meter how many sticky numbered tags our routers still have left to hand out. When the sticker book fills up, we plan upgrades before new offices cannot plug in at all.*

---

## Description

Splunk trends MPLS label-space consumption per forwarding plane so platforms approaching vendor-imposed LFIB or dynamic label limits trigger proactive hardware upgrades before RSVP or LDP admissions fail catastrophically.

## Value

Capacity governance avoids midnight Sev1 failures where new VPN sites cannot signal because free labels dropped below safe margins while dashboards still showed green interface utilization unrelated to control-plane resource exhaustion.

## Implementation

Schedule fifteen-minute SNMP or telemetry polls into metrics index, compute percent used vs platform caps from CMDB, alert when sustained ≥85% for four buckets or syslog reports critical label exhaustion.

## Detailed Implementation

### Prerequisites
- Hardware SKU matrix documenting global vs per-line-card label pools.
- Normalized `host` aligning SNMP agent address with syslog identity.

### Step 1 — Discover OIDs/sensors
Cisco: identify platform-specific MPLS label counters via CLI `show mpls label table summary` vs SNMP tree availability. Juniper: confirm sensor paths exposing `allocated-label-blocks`. Nokia: validate TIMOS model exposes free dynamic labels via SNMP or streaming.

### Step 2 — Build modular input
Use SC4SNMP profiles polling counters every five minutes; backoff on timeout; tag `site` and `role` via lookup.

### Step 3 — SPL thresholds
Implement staged alerts: warn ≥75%, page ≥90% for two consecutive intervals unless suppress.

### Step 4 — Validation
During acceptance, artificially inflate VPN scale in lab (mass RD churn) while observing Splunk pct tracking CLI counters within ±2%.

### Step 5 — Lifecycle integration
Feed Splunk summary index monthly into Capex workflow; attach trending screenshots for steering committee.

## SPL

```spl
index=network OR index=infra_metrics earliest=-24h@h latest=now
| eval metric_name=lower(coalesce(metric_name,name,""))
| eval msg=lower(_raw)
| eval lab_use=match(metric_name,"label|lfib|mpls.*table|mpls.*usage") OR match(msg,"label.*(?:space|range|table)|(?:mpls|lfib).*(?:full|exhaust|threshold|high.?water)|free.?labels|in.?use.?labels")
| where lab_use=1
| eval used=tonumber(coalesce(labels_in_use,in_use_labels,mpls_labels_used,lfib_entries))
| eval total=tonumber(coalesce(label_space_total,max_labels,platform_label_capacity))
| eval pct=if(isnotnull(used) AND isnotnull(total) AND total>0, round(100*used/total,2), null())
| eval syslog_crit=if(match(msg,"(?:critical|major).*label"),1,0)
| bin _time span=15m
| stats latest(used) as used latest(total) as total latest(pct) as pct max(pct) as peak_pct max(syslog_crit) as syslog_crit by _time host
| where pct>=85 OR peak_pct>=85 OR syslog_crit>=1
| sort host _time
```

## Visualization

Dashboard Studio: KPI row for PEs above warn threshold; timechart of `pct` by `host`; overlay syslog exhaustion markers as annotations.

## Known False Positives

**Per-LC vs global counters:** polling global only misses hot LC—split by slot.**SNMP 32-bit wraps:** rare but possible—use 64-bit HC counters.**Telemetry sparsity:** null `pct` skips alert—fallback to syslog.**Vendor MIB drift:** upgrades rename OIDs—version-pin TA.**Burst churn:** transient spikes during reconvergence—smooth with median window.

## References

- [Cisco IOS XR MPLS Label Allocation Overview](https://www.cisco.com/c/en/us/)
- [Juniper MPLS Applications User Guide — Label Allocation](https://www.juniper.net/documentation/us/en/software/junos/mpls/)
- [IETF RFC 3032 — MPLS Label Stack Encoding](https://www.rfc-editor.org/rfc/rfc3032)
