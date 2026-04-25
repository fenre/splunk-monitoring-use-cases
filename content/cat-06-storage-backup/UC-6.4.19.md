<!-- AUTO-GENERATED from UC-6.4.19.json — DO NOT EDIT -->

---
id: "6.4.19"
title: "Veeam Backup Copy Job Missing Expected GFS Restore Points"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-6.4.19 · Veeam Backup Copy Job Missing Expected GFS Restore Points

## Description

Backup copy jobs carry Grandfather-Father-Son (GFS) anchors for compliance; if no successful copy lands within the policy window, offsite retention gaps violate internal and external audit requirements.

## Value

Protects legal hold and ransomware recovery postures by catching WAN outages, repository auth failures, or scheduling mistakes before quarterly reviews.

## Implementation

Tag backup copy jobs in Veeam with a consistent naming prefix. Adjust `days_since` threshold to match the tightest GFS interval (weekly anchor = 7 days). Join to a lookup of regulated workloads for routing severity. Use `veeam_vbr_syslog` with the same filters if REST ingestion is unavailable.

## SPL

```spl
index=backup (sourcetype="veeam:backup" OR sourcetype="veeam:job") earliest=-30d
| eval jn=coalesce(job_name, JobName)
| where match(jn,"(?i)copy")
| eval end_epoch=coalesce(if(isnum(end_time), end_time, null()), strptime(job_end,"%Y-%m-%d %H:%M:%S"), strptime(job_end,"%Y-%m-%dT%H:%M:%S%Z"))
| stats latest(end_epoch) as last_success by jn
| eval days_since=round((now()-last_success)/86400,1)
| where isnotnull(last_success) AND days_since > 7
| sort - days_since
```

## Visualization

Table (job, days since success), timeline of successes, single value (worst gap).

## References

- [Veeam App for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/7312)
- [Veeam Help Center — Backup copy](https://helpcenter.veeam.com/docs/backup/vsphere/backup_copy.html)
