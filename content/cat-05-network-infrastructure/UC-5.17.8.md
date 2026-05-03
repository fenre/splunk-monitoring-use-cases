<!-- AUTO-GENERATED from UC-5.17.8.json — DO NOT EDIT -->

---
id: "5.17.8"
title: "License and Module Capacity Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.17.8 · License and Module Capacity Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Platform &middot; **Type:** Capacity, Governance, Operations &middot; **Wave:** Crawl &middot; **Status:** Verified

*These fancy copying switches come with subscriptions like a phone plan—speed limits and renewal dates. We track how close we are to the limits and how soon bills renew so teams order upgrades calmly instead of hitting a sudden stop.*

---

## Description

Daily Splunk rollups compare entitlement utilization, concurrent map counts, and subscription throughput meters against licensed ceilings plus expiry horizons so finance and engineering negotiate renewals before hard enforcement throttles visibility ports.

## Value

Budget cycles gain data-driven renewal forecasts anchored to actual broker consumption instead of vendor anecdotes while audit responses cite Splunk histories proving continuous license compliance.

## Implementation

Redact serial keys from `_raw` via `SEDCMD`; route procurement dashboard to restricted role; sync `_time` to vendor midnight UTC for apples-to-apples daily deltas.

## Detailed Implementation

### Prerequisites
- Legal-approved sharing scope for entitlement identifiers (often confidential).
- Integration service account with least-privilege API tokens rotated quarterly.
- Procurement SLA defining lead times versus Splunk alert horizons.

### Step 1 — Secure collection
Use encrypted scripted inputs pulling HTTPS APIs; never index raw license keys—hash identifiers if correlation needed.

### Step 2 — Normalize metrics
Convert epoch expirations consistently; harmonize throughput counters where vendors mix Mb/s vs Gb/s naming.

### Step 3 — Implement dashboards
Executive summary highlights hosts crossing 75% utilization; technical drill exposes map quotas vs active_maps.

### Step 4 — Validate
Compare Splunk `lic_util` against vendor GUI entitlement screen monthly; reconcile discrepancies via support ticket trail documented in Splunk notes.

### Step 5 — Governance
Attach Splunk PDF exports to renewal RFCs; archive yearly snapshots to object storage with immutability flags for compliance archives.

## SPL

```spl
index=visibility OR index=infra earliest=-7d@d latest=now
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"gigamon"),"Gigamon",match(v,"keysight|ixia|vision"),"Keysight",match(v,"cpacket"),"cPacket",match(v,"apcon"),"APCON","other")
| where vendor!="other"
| eval util_pct=tonumber(coalesce(license_util_pct,map_quota_used_pct,throughput_license_pct))
| eval days_left=floor((tonumber(expiry_epoch)-now())/86400)
| eval cap_gbps=tonumber(coalesce(licensed_throughput_gbps,subscription_gbps))
| eval metered_gbps=tonumber(coalesce(metered_throughput_gbps,observed_throughput_gbps,billed_peak_gbps))
| bin _time span=1d
| stats latest(util_pct) as lic_util latest(days_left) as expire_in latest(cap_gbps) as entitled_speed latest(metered_gbps) as metered_peak latest(active_maps) as maps_used latest(map_quota) as maps_cap by _time vendor host
| eval renew_risk=case(isnull(expire_in),0,expire_in<=45,2,expire_in<=120,1,0)
| eval capacity_risk=case(maps_cap>0 AND maps_used/maps_cap>=0.9,2,lic_util>=90 OR entitled_speed>0 AND metered_peak>entitled_speed,2,lic_util>=75,1,0)
| where renew_risk>0 OR capacity_risk>0
| sort - renew_risk - capacity_risk vendor host
```

## Visualization

Single-value tiles for hosts expiring <45 days; bar chart of lic_util by vendor; detailed table with entitled_speed vs measured throughput if meter fields exist.

## Known False Positives

**Grace-period licenses:** vendors grant temporary overages Splunk flags as risk—annotate grace metadata.**API caching delays:** stale utilization underestimates pressure—poll near billing boundary.**Lab chassis sharing prod SKUs:** triggers false renew_risk—exclude via environment tag.**Bursty metering:** short spikes exceed sustained entitlement though averages remain safe—use weekly smoothing.

## References

- [Splunk Documentation — REST API input overview](https://docs.splunk.com/Documentation/Splunk/latest/Data/RESTAPIInputs)
- [Gigamon Customer Documentation Portal](https://docs.gigamon.com/)
- [ITIL 4 — Capacity management practice summary (renewal alignment)](https://www.axelos.com/best-practice-solutions/itil)
