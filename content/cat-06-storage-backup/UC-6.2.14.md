<!-- AUTO-GENERATED from UC-6.2.14.json — DO NOT EDIT -->

---
id: "6.2.14"
title: "Commvault Auxiliary Copy Job Failures"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-6.2.14 · Commvault Auxiliary Copy Job Failures

## Description

Auxiliary copies move data to secondary disk, tape, or cloud libraries; failures break 3-2-1 strategies and leave only primary copies during ransomware or site disasters.

## Value

Ensures air-gapped and offsite copies actually exist—catching library mount issues, network auth failures, and throttling before audit or insurance reviews find gaps.

## Implementation

Complete the Commvault Splunk integration wizard so finished jobs stream with consistent `status` tokens. If your export uses different field names, add aliases in `props.conf`. Correlate with media agent uptime (UC can be cloned) when errors reference `Error Mount Path`.

## SPL

```spl
index=backup sourcetype="commvault:job" earliest=-48h
| eval jt=lower(coalesce(job_type, operation, job_type_name))
| eval st=lower(coalesce(status, job_status, Status))
| where match(jt,"(?i)aux") OR match(job_name,"(?i)auxiliary")
| where st!="completed" AND st!="success"
| stats latest(st) as status latest(error_code) as err latest(_time) as last_run by job_name subclient_name
| sort - last_run
```

## Visualization

Table (aux copy job, subclient, status, error), timeline of failures.

## References

- [Commvault Splunk App (Splunkbase)](https://splunkbase.splunk.com/app/5718)
- [Commvault documentation — Splunk plug-in](https://documentation.commvault.com/commvault/v11/software/articles/splunk_plug_in.html)
