<!-- AUTO-GENERATED from UC-1.4.4.json — DO NOT EDIT -->

---
id: "1.4.4"
title: "Predictive Disk Failure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.4 · Predictive Disk Failure

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We read the early-warning numbers from each disk’s self-checks so you can schedule a drive swap when it is convenient instead of when it suddenly fails.*

---

## Description

SMART attributes can predict disk failure days or weeks in advance, enabling proactive replacement during maintenance windows.

## Value

A rising count of reallocated or pending sectors is a cheap early warning to swap a drive during a maintenance window instead of after a double fault or unplanned outage.

## Implementation

Install `smartmontools`. Scripted input: `smartctl -A /dev/sd[a-z]`. Run every 3600 seconds. Track key attributes: Reallocated Sector Count, Current Pending Sector, Offline Uncorrectable. Alert on any non-zero values.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Custom scripted input (`smartctl`).
- Ensure the following data sources are available: Custom sourcetype (SMART data).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
On Linux, install `smartmontools` and use a scripted input: for example `smartctl -A` for each target device on a schedule. Map attributes such as `Reallocated_Sector_Ct` to numeric fields. Run every 3600 seconds (tune to policy).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=smart_data
| where Reallocated_Sector_Ct > 0 OR Current_Pending_Sector > 0 OR Offline_Uncorrectable > 0
| table _time host device Reallocated_Sector_Ct Current_Pending_Sector Temperature_Celsius
| sort -Reallocated_Sector_Ct
```

#### Understanding this SPL

**Predictive Disk Failure** — SMART attributes can predict disk failure days or weeks in advance, enabling proactive replacement during maintenance windows.

**Pipeline walkthrough**

- Scopes the data: `index=hardware`, `sourcetype=smart_data`.
- `where` flags disks with any concerning non-zero counters you parse.
- `table` and `sort` list worst cases first.


### Step 3 — Validate
On a test host, run `smartctl -A` and compare numeric fields. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=smart_data
| where Reallocated_Sector_Ct > 0 OR Current_Pending_Sector > 0 OR Offline_Uncorrectable > 0
| table _time host device Reallocated_Sector_Ct Current_Pending_Sector Temperature_Celsius
| sort -Reallocated_Sector_Ct
```

## Visualization

Table per disk, Trend line for sector counts, Heatmap of disk health.

## Known False Positives

A small stable reallocated count on older drives can be benign; trend velocity matters more than a single point. NVMe and SATA attribute names and scales differ; align field names to your `smartctl` output. A machine under heavy stress tests can show transient noise.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
