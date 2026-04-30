<!-- AUTO-GENERATED from UC-6.2.13.json — DO NOT EDIT -->

---
id: "6.2.13"
title: "Veeam SureBackup Virtual Lab Verification Failures"
status: "draft"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-6.2.13 · Veeam SureBackup Virtual Lab Verification Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Quality, Availability &middot; **Status:** Draft

*We help you see which backup runs finished cleanly and which did not, so you are not caught thinking data was protected when a job really failed or stopped early.*

---

## Description

SureBackup jobs prove that backups are bootable and application-consistent; silent failures mean DR rehearsals would fail exactly when ransomware or datacenter loss demands them.

## Value

Protects leadership confidence in recovery drills by catching verification regressions, networking issues in virtual labs, or guest OS boot errors immediately after each run.

## Implementation

Enable Splunk-oriented logging in Veeam Backup & Replication or Enterprise Manager per the Veeam App for Splunk deployment guide. Normalize `result` field casing. Exclude lab jobs under maintenance via a lookup. Treat `Warning` per internal policy—many teams page on `Failed` only but track warnings for trend dashboards.

## SPL

```spl
index=backup (sourcetype="veeam:backup" OR sourcetype="veeam:Backup.JobSession" OR sourcetype="veeam_vbr_syslog") earliest=-24h
| eval jn=coalesce(job_name, JobName, JobSessionName)
| eval res=lower(coalesce(result, Result, status, JobResult))
| where match(jn,"(?i)SureBackup")
| where res!="success" AND res!="none" AND isnotnull(res)
| stats latest(res) as outcome latest(_time) as last_run by jn
| sort - last_run
```

## Visualization

Table (SureBackup job, outcome, last run), pie chart (success vs warning vs failed).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Veeam App for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/7312)
- [Veeam Help Center — Configuring data inputs for Splunk](https://helpcenter.veeam.com/docs/security_plugins_splunk/guide/splunk_configure_data_inputs.html)
