<!-- AUTO-GENERATED from UC-6.1.38.json — DO NOT EDIT -->

---
id: "6.1.38"
title: "TrueNAS SCALE ZFS Pool Scrub Errors and Stalled Scrubs"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.38 · TrueNAS SCALE ZFS Pool Scrub Errors and Stalled Scrubs

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Data Quality, Fault &middot; **Status:** Draft

*We help you see how your arrays and related gear are doing before small issues turn into full outages or restore surprises.*

---

## Description

Scrubs that stop mid-flight or report checksum errors indicate latent disk or controller issues; ignoring them allows silent corruption to spread before replication catches it.

## Value

Forces timely disk replacement and validates that automated scrub schedules actually complete—critical for ZFS pools backing VMware, backup landing zones, and file shares.

## Implementation

Poll `/api/v2.0/pool` and expand nested `scan` data. Normalize TrueNAS CORE vs SCALE field paths (`scan.state` vs flat keys). Alert on any `scan_errors > 0` immediately; warn if a scrub stays non-`FINISHED` longer than twice your expected duration.

## SPL

```spl
index=storage sourcetype="truenas:pool" earliest=-24h
| eval scan_fn=coalesce(scan_function, scan.type)
| eval scan_st=coalesce(scan_state, scan.state)
| eval scan_err=coalesce(scan_errors, scan.errors, 0)
| where scan_fn="SCRUB" AND (scan_err > 0 OR scan_st!="FINISHED" AND scan_st!="ACTIVE")
| stats latest(scan_err) as scrub_errors latest(scan_st) as scrub_state latest(scan_progress) as progress by hostname pool_name
| sort - scrub_errors
```

## Visualization

Table (pool, scrub state, errors), timeline (scrub start/stop), single value (pools with errors).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS API documentation](https://www.truenas.com/docs/scale/scaleuireference/systemsettings/advanced/)
- [OpenZFS — zpool scrub](https://openzfs.github.io/openzfs-docs/man/master/8/zpool-scrub.8.html)
