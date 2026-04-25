<!-- AUTO-GENERATED from UC-7.1.78.json — DO NOT EDIT -->

---
id: "7.1.78"
title: "Snowflake Snowpipe File Ingest Lag from Pipe Usage"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.78 · Snowflake Snowpipe File Ingest Lag from Pipe Usage

## Description

A sudden collapse in files inserted through a pipe often means stage notifications, IAM roles, or event bridges broke—landing zone data piles up while dashboards still look “fresh enough” until SLAs miss. Comparing hourly inserts to a same-hour baseline catches partial outages.

## Value

Protects near-real-time analytics and revenue reporting fed by cloud storage landing zones.

## Implementation

Enable PIPE_USAGE_HISTORY input; confirm `PIPE_NAME`, `FILES_INSERTED`, `START_TIME` mapping. For multi-region pipes, split by `PIPE_SCHEMA`. Pair with cloud storage object-count metrics. Tune seasonality (use same day-of-week window) if workloads are cyclic.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:pipe_usage"
| eval files=tonumber(FILES_INSERTED)
| eval credits=tonumber(CREDITS_USED)
| bin _time span=1h
| stats sum(files) as files_in sum(credits) as pipe_credits by PIPE_NAME, _time
| streamstats window=24 global=f avg(files_in) as baseline_files by PIPE_NAME
| where baseline_files > 10 AND files_in < baseline_files*0.25
```

## Visualization

Line chart (files_in vs baseline), Single value (worst pipe drop %).

## References

- [Snowflake PIPE_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/pipe_usage_history)
