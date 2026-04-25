<!-- AUTO-GENERATED from UC-6.4.20.json — DO NOT EDIT -->

---
id: "6.4.20"
title: "Commvault Deduplication Database Disk Library Free Space Pressure"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-6.4.20 · Commvault Deduplication Database Disk Library Free Space Pressure

## Description

Deduplication databases and their backing disk libraries must retain contiguous free space for compaction and sealing; exhaustion corrupts backup chains and blocks new auxiliary copies.

## Value

Prevents catastrophic Commvault outages where DDB partitions go read-only and synthetic fulls fail—typically during rapid data growth or mis-sized commodity storage.

## Implementation

Enable Commvault’s Splunk integration for library capacity metrics or schedule `qoperation execscript` exports to HEC. Because field names differ by plugin version, validate `free_space_*` tokens on a sample event and alias them to `free_tb`. Alert at 15% free warning and 8% critical. Pair with hardware monitoring of the Windows/Linux mount hosting the DDB.

## SPL

```spl
index=backup (sourcetype="commvault:storage" OR sourcetype="commvault:library")
| eval free_tb=coalesce(free_space_tb, freespace_tb, library_free_tb)
| eval total_tb=coalesce(total_space_tb, capacity_tb, library_size_tb)
| eval pct_free=if(total_tb>0 AND isnotnull(free_tb), round(free_tb/total_tb*100,2), null())
| where isnotnull(pct_free) AND pct_free < 15
| stats latest(pct_free) as pct_free latest(free_tb) as free_tb latest(total_tb) as total_tb by library_name media_agent
| sort pct_free
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Gauge (% free), table (library, media agent, TB free), predictor on free TB.

## References

- [Commvault Splunk App (Splunkbase)](https://splunkbase.splunk.com/app/5718)
- [Commvault documentation — Deduplication](https://documentation.commvault.com/commvault/v11/expert/what_is_deduplication.html)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
