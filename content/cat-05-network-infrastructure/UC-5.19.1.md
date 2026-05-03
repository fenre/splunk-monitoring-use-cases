<!-- AUTO-GENERATED from UC-5.19.1.json — DO NOT EDIT -->

---
id: "5.19.1"
title: "Ansible Playbook/Job Failure Rate and Duration Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.19.1 · Ansible Playbook/Job Failure Rate and Duration Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Operations, Reliability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We track whether our batch updates to routers and switches finish on time and how often they fail. When failures or slowdowns bunch up, we fix the recipes before the whole network ends up half updated.*

---

## Description

Splunk rolls up Ansible Automation Platform and AWX/Tower job telemetry into hourly failure ratios and duration percentiles per template so brittle playbooks, credential regressions, or slow network pushes surface before change windows stack up unresolved incidents.

## Value

Network and platform teams stabilize automation-led rollouts because recurring playbook failures and runtime creep trigger proactive fixes instead of discovering broken convergence only after devices drift or rollback scripts fire during production incidents.

## Implementation

Forward normalized job completion JSON with explicit duration seconds and terminal status; retain job_template identifiers; run hourly; tune minimum job counts and failure-rate thresholds per environment.

## Detailed Implementation

### Prerequisites
- AWX/Tower logging enabled for job lifecycle events (started, running, successful, failed, canceled) with consistent timestamps (UTC).
- Service account HEC token scoped to `iac` index; TLS termination validated.

### Step 1 — Normalize payloads
Map AWX `job_events` summary records or Tower `/api/v2/jobs/` polling exports into flat fields: `job_id`, `job_template`, `status`, `started`, `finished`, `duration_sec`. Strip ANSI from stdout fields before indexing.

### Step 2 — props.conf
Assign `KV_MODE=json` for structured callbacks; set `TIME_PREFIX` if `_time` skews; create field aliases `duration`→`duration_sec` when vendors differ.

### Step 3 — Saved search
Save SPL as `ansible_job_fail_rate_duration_trend`; alert when hourly `fail_rate`≥10% for templates with ≥3 executions or when `p95_dur` exceeds baseline ×1.5 from lookup `ansible_runtime_baseline.csv`.

### Step 4 — Validate
Replay a known failing playbook in lab; confirm failed increment and duration extraction versus AWX UI job metrics within one-minute skew.

### Step 5 — Operationalize
Dashboard: stacked column of failure rate by template; overlay line chart of p95 duration; drilldown saved search to raw `_raw` for playbook stderr correlation.

## SPL

```spl
index IN ("iac","main","ansible")
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| where match(st,"ansible|awx|tower|automationcontroller")
| eval status_norm=lower(trim(coalesce(status,changed_status,final_status,job_status,"")))
| eval failed=if(match(status_norm,"fail|error|canceled|cancelled|unreachable"),1,0)
| eval dur=tonumber(coalesce(duration_sec,duration,elapsed_time,job_elapsed))
| eval jt=coalesce(job_template,template_name,"unknown")
| bin _time span=1h
| stats count as jobs sum(failed) as failed_jobs avg(dur) as avg_dur perc95(dur) as p95_dur by _time, jt, st
| eval fail_rate=round(100*failed_jobs/nullif(jobs,0),2)
| where jobs>=3 AND (fail_rate>=10 OR p95_dur>3600)
| sort -fail_rate,-p95_dur
```

## Visualization

Dashboard Studio: KPI tiles for overall failure % and worst template; `splunk.timechart` of fail_rate by job_template; table (`jt`,`jobs`,`failed_jobs`,`fail_rate`,`p95_dur`) sorted by impact.

## Known False Positives

**Transient infra:** Runner disk-full or container recycle spikes failures unrelated to playbooks.**Inventory churn:** dynamic inventory timeouts resemble playbook faults unless `unreachable` split out.**Long-running jobs:** backup-style templates inflate p95; baseline per template.**Parallel forks:** duration not comparable across templates with different fork counts unless normalized.**Canceled maintenance:** operator-cancel jobs count as failures unless filtered.

## References

- [Red Hat Ansible Automation Platform — Logging and aggregation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/)
- [Ansible AWX — Integration overview](https://ansible.readthedocs.io/projects/awx/en/latest/)
- [Splunk Lantern — observability patterns](https://lantern.splunk.com/)
