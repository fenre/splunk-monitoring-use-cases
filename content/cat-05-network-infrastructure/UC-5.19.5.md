<!-- AUTO-GENERATED from UC-5.19.5.json — DO NOT EDIT -->

---
id: "5.19.5"
title: "Change Window Compliance (Automation Jobs Outside Approved Windows)"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.19.5 · Change Window Compliance (Automation Jobs Outside Approved Windows)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Compliance, Governance, Audit &middot; **Wave:** Walk &middot; **Status:** Verified

*We compare scheduled fix-it jobs to the approved hours on the calendar. If someone pushes big network changes during forbidden times, we get a clear record for managers and auditors without digging through many consoles.*

---

## Description

Splunk compares automation job start and stop timestamps against approved maintenance windows and blackout calendars so controller-driven pushes that bypass CAB governance generate evidence-grade violations linked to owning teams and workspaces.

## Value

Risk and network leadership restore audit trust because after-hours Terraform applies and Ansible bulk runs cannot hide behind shared service accounts—every excursion ties to a ticketless window breach ready for SOC2 or internal controls review.

## Implementation

Maintain authoritative lookup keyed by `team` with local HH:MM ranges converted consistently to UTC; ingest automation audit with reliable `_time`; weekly reconcile lookup against change-management exports; suppress break-glass tagged jobs via field.

## Detailed Implementation

### Prerequisites
- CAB publishes recurring windows per team with timezone; blackout holidays listed explicitly.
- Automation jobs emit `owner_team` or mappable cost-center metadata.

### Step 1 — Build lookup
Author `approved_change_windows.csv` with columns validated via `inputlookup` preview; version-control file in Git.

### Step 2 — Normalize timestamps
Ensure Splunk `_time` reflects job start (not log ingest lag); for long jobs capture min/max event times per `job_id`.

### Step 3 — Saved search
Schedule `automation_change_window_compliance_daily`; alert on any row where `violation` present unless `break_glass=true`.

### Step 4 — Validate
Execute controlled job inside and outside windows in lab; confirm expected detection polarity.

### Step 5 — Operationalize
Dashboard: stacked bar of violations by team; CSV export for GRC; integrate optional ServiceNow CMDB correlation macro.

## SPL

```spl
index=iac earliest=-7d@d latest=now
| eval st=lower(coalesce(sourcetype,_sourcetype,""))
| where match(st,"ansible|awx|tower|automationcontroller|terraform|tfc|hcp")
| eval team=lower(trim(coalesce(owner_team,business_unit,cost_center,"network-core")))
| eval job_key=coalesce(tostring(job_id),tostring(run_id),tostring(build_id),tostring(pipeline_id))
| stats earliest(_time) as job_start latest(_time) as job_end values(playbook) as playbook values(workspace) as workspace by team job_key
| lookup approved_change_windows.csv team OUTPUT window_start_local window_end_local timezone blackout_dates
| eval cal_date=strftime(job_start,"%Y-%m-%d")
| eval on_blackout=if(match(coalesce(blackout_dates,""),cal_date),1,0)
| eval win_open=strptime(cal_date." ".window_start_local,"%Y-%m-%d %H:%M:%S")
| eval win_close=strptime(cal_date." ".window_end_local,"%Y-%m-%d %H:%M:%S")
| eval within_hours=if(job_start>=win_open AND job_end<=win_close AND on_blackout=0,1,0)
| where isnotnull(job_key) AND isnotnull(window_start_local) AND (within_hours=0 OR on_blackout=1)
| eval violation=if(on_blackout=1,"holiday_blackout","outside_approved_window")
| table team job_key job_start job_end playbook workspace violation
```

## Visualization

Dashboard Studio: KPI violations last seven days; bar chart by team; drilldown timeline aligning runs against shaded approved bands (reference visualization via secondary dataset).

## Known False Positives

**Timezone DST transitions:** miscomputed boundaries around clock shifts.**Rolling jobs:** jobs spanning windows partially violate though benign—consider overlap tolerance.**Lookup staleness:** outdated CAB CSV flags legitimate work.**Shared teams:** coarse `team` keys blame wrong org.**Emergency fixes:** legitimate incidents need `break_glass` tagging discipline.

## References

- [Red Hat Ansible Automation Platform — Role-based access control and auditing](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/)
- [HashiCorp Terraform Cloud — Workspace permissions and audit log events](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/audit-trails)
- [ITIL — Change management practice summary (Axelos)](https://www.axelos.com/best-practice-solutions/itil)
