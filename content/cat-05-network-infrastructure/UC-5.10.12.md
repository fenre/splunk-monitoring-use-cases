<!-- AUTO-GENERATED from UC-5.10.12.json — DO NOT EDIT -->

---
id: "5.10.12"
title: "Carrier Maintenance Window Correlation"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.10.12 · Carrier Maintenance Window Correlation

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations, Change &middot; **Wave:** Walk &middot; **Status:** Verified

*We line up scary network alarms with the supplier’s published work windows so after-hours pages only happen for surprises, not for appointments we already knew about.*

---

## Description

Tags carrier-impacting interface and BGP churn events with synchronized carrier-published maintenance windows so only unexpected outages bubble into paging queues—while still retaining forensic copies of in-window noise.

## Value

Operations stops burning bridge calls on planned fibre swaps or PE reloads, yet preserves timestamps proving whether incidents aligned with notifications—critical when negotiating SLA penalties versus coordinated maintenance carve-outs.

## Implementation

Ingest carrier CSV/RSS feeds into KV store or scheduled CSV refresh; normalize all timestamps to UTC; map interfaces via authoritative CMDB export; auto-close tickets when `in_maint=1` while logging correlation ratio KPIs monthly.

## Detailed Implementation

### Prerequisites
- Structured maintenance calendar per upstream including rollback buffers (often ±2h).
- CMDB rows tying router interfaces and BGP neighbor IPs to `carrier_id`.
- Governance defining whether partial overlaps suppress alerts entirely vs downgrade severity.
- Splunk lookup replication schedule faster than maintenance updates.

### Step 1 — Build `carrier_maintenance_windows.csv` loader (REST or SharePoint) landing under `lookups/` with version metadata.

### Step 2 — Parse syslog extractions for interface/neighbor tokens even when formats differ between IOS-XR and Junos—maintain vendor-specific `rex` macros.

### Step 3 — Evaluate `_time` boundaries inclusively; guard against overlapping windows using `max` aggregation per carrier.

### Step 4 — Dashboard contrasts suppressed vs escalated counts; drilldown opens carrier portal hyperlinks stored in lookup.

### Step 5 — Troubleshooting: DST drift breaks correlations—force UTC; ambiguous neighbor strings behind dynamic peers require dedup via SNMP-index substitution; stale CSV causes false escalations—monitor lookup freshness via `inputlookup` diff alerts.

## SPL

```spl
index=network earliest=-24h (sourcetype="cisco:ios" OR sourcetype="juniper:junos")
    ("%BGP-5-ADJCHANGE" OR "BGP_NOTIFICATION" OR "LINK-3-UPDOWN" OR "LINEPROTO-5-UPDOWN" OR "SNMP_TRAP_LINK")
| rex field=_raw "(?i)interface (?<if_name>[^,:]+)"
| rex field=_raw "neighbor (?<bgp_nbr>[0-9a-fA-F:\.:\]]+)"
| eval circuit_key=host."|".coalesce(if_name,"na")
| lookup carrier_circuits.csv circuit_key OUTPUT carrier_id carrier_name
| lookup carrier_maintenance_windows.csv carrier_id OUTPUT utc_start utc_end ticket_ref suppress_alert
| eval in_maint=if(suppress_alert=="true" AND _time>=utc_start AND _time<=utc_end,1,0)
| where in_maint==0 OR isnull(utc_start)
| eval severity=case(match(_raw,"(?i)down|idle"),"high", match(_raw,"(?i)UPDOWN.*down"),"high", true(),"medium")
| stats count values(ticket_ref) as tickets values(_raw) as samples by carrier_name host bgp_nbr if_name severity
| sort -count
```

## Visualization

Stacked bar of events suppressed versus escalated per carrier; timeline annotated with maintenance shading; table listing outliers with samples column truncated.

## Known False Positives

Emergency carrier patches absent from calendars page loudly—maintain phone-verified override rows; rolling brownouts spanning multi-day windows need segmented rows or alerts fatigue returns.

## References

- [MEF — Maintenance Coordination Primer (carrier operational practices)](https://www.mef.net/)
- [Splunk Lantern — correlation searches](https://lantern.splunk.com/)
