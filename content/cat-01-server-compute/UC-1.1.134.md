<!-- AUTO-GENERATED from UC-1.1.134.json — DO NOT EDIT -->

---
id: "1.1.134"
title: "macOS Filesystem Capacity from Splunk TA df"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.134 · macOS Filesystem Capacity from Splunk TA df

## Description

macOS endpoints exhaust `/System/Volumes/Data` quickly with local Time Machine snapshots, Xcode caches, and mail attachments. The TA `df` input already exposes per-mount utilization; scoping to root and Data volumes catches impending fullness before logging and MDM operations fail.

## Value

Prevents OS instability and failed security tooling updates by alerting on critical mount points before they hit 100% utilization.

## Implementation

Enable the `df` scripted input in `Splunk_TA_nix` on macOS UF installs (Darwin is supported for many collectors). Confirm field extractions: prefer `UsePct`; if your build emits `UsedKB`/`SizeKB`, derive percent as in the SPL. Poll every 5–15 minutes. Exclude network mounts with a `where NOT match(Filesystem, "^//")` clause if noisy. Alert above 90% on `/` and `/System/Volumes/Data` (adjust for Silicon vs Intel layout).

## Detailed Implementation

Prerequisites
• `Splunk_TA_nix` deployed to the UF with `df` enabled in `inputs.conf`.
• Verify whether your TA version uses `UsePct` vs raw KB fields via Search `| head 1` on a pilot host.

Step 1 — Add lookup for allowed minimum free space per department if needed.

Step 2 — Create the search and optional CIM variant

Primary SPL (as in this UC’s `spl` field) stays on `sourcetype=df` for macOS (and Linux) full-fidelity field math.

If the same data is CIM-tagged to **Performance.Storage** with acceleration:

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.filesystem span=15m
| where used_pct > 90
```

Step 3 — Schedule alert; throttle per host to once per hour.

Step 4 — Validate by filling a test volume in a lab; compare to Finder and `diskutil apfs listSnapshots` when APFS snapshots distort free space.

Step 5 — Pair with UC-1.3.x macOS crash monitoring when disks are critically full.

## SPL

```spl
index=os sourcetype=df host=*
| where MountedOn="/" OR match(MountedOn, "^/System/Volumes/Data$")
| eval use_pct=coalesce(tonumber(UsePct), tonumber(PercentUsed), round((UsedKB/SizeKB)*100,2))
| where use_pct > 90
| table _time, host, Filesystem, MountedOn, SizeKB, AvailKB, use_pct
| sort - use_pct
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.filesystem span=15m
| where used_pct > 90
```

## Visualization

Table (host, mount, use_pct), Line chart (use_pct trend for Data volume), Single value (count of hosts over threshold).

## References

- [Splunk Documentation: Splunk Add-on for Unix and Linux](https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/ConfigureUnix)
- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
