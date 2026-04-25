<!-- AUTO-GENERATED from UC-1.4.6.json — DO NOT EDIT -->

---
id: "1.4.6"
title: "Memory ECC Error Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.6 · Memory ECC Error Trending

## Description

Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.

## Value

A rising weekly total of single-bit correctable events points to a bad stick or slot before a machine starts throwing uncorrectable errors and taking applications down with it.

## Implementation

Create scripted input: `edac-util -s` or parse `/sys/devices/system/edac/mc/mc*/ce_count`. Run hourly. Alert when correctable errors increase by >10/week. Track per-DIMM slot for targeted replacement.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`edac-util`, IPMI SEL).
• Ensure the following data sources are available: `edac-util`, `/sys/devices/system/edac/mc/`, IPMI SEL.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux with EDAC, run `edac-util` or read `/sys/devices/system/edac/mc/.../ce_count` on a schedule and emit `correctable_errors` (optionally by DIMM). You can also supplement with IPMI memory-related SELs in a second sourcetype. Run hourly and align the field name with the search.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust weekly threshold as needed):

```spl
index=hardware sourcetype=ecc_errors
| timechart span=1d sum(correctable_errors) as ecc_errors by host
| where ecc_errors > 0
| streamstats window=7 sum(ecc_errors) as weekly_errors by host
| where weekly_errors > 10
```

Note: the sample chains `timechart` with `streamstats`—tune or split into a base `stats` if your Splunk version or data shape needs a flatter pre-chart dataset.

Understanding this SPL

**Memory ECC Error Trending** — Correctable ECC errors that increase over time strongly predict impending DIMM failure. Proactive replacement avoids unrecoverable memory errors and system crashes.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=ecc_errors`.
• `timechart` daily sums of correctable events per **host**.
• `streamstats` over a seven-bucket window approximates a rolling week for the sample threshold.


Step 3 — Validate
Compare counts to `edac-util` and `dmesg` on a test host. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ecc_errors
| timechart span=1d sum(correctable_errors) as ecc_errors by host
| where ecc_errors > 0
| streamstats window=7 sum(ecc_errors) as weekly_errors by host
| where weekly_errors > 10
```

## CIM SPL

```spl
N/A — correctable ECC counts from the Linux EDAC driver or related SELs are not a CIM data model; use a custom `ecc_errors` sourcetype (and optionally per-DIMM fields).
```

## Visualization

Line chart (errors over time by host), Table (host, DIMM, error count), Trend chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
