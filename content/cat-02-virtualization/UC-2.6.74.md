<!-- AUTO-GENERATED from UC-2.6.74.json — DO NOT EDIT -->

---
id: "2.6.74"
title: "Citrix ShareFile User Activity Audit Trail"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.74 · Citrix ShareFile User Activity Audit Trail

## Description

A complete audit layer for ShareFile supports investigations and compliance: who accessed, changed, or shared which content; administrative actions in zones; and time-bounded reports for internal review or external auditors. The search summarizes daily activity mix and breadth so teams can spot gaps in logging and prove retention of evidence.

## Value

A complete audit layer for ShareFile supports investigations and compliance: who accessed, changed, or shared which content; administrative actions in zones; and time-bounded reports for internal review or external auditors. The search summarizes daily activity mix and breadth so teams can spot gaps in logging and prove retention of evidence.

## Implementation

Enable ShareFile audit trail export to Splunk with full coverage (user and admin). Retain per policy (often 1–7 years for regulated data). Create scheduled reports for business reviews and a drill-down form with raw events for cases. Do not over-collect PII; mask where required.

## Detailed Implementation

Prerequisites: ShareFile audit export to Splunk with test events visible; legal sign-off for fields stored and retention. Step 1: Configure data collection — Map admin vs user streams to sourcetype citrix:sharefile:audit and citrix:sharefile:admin (or one sourcetype with actor_type); add props.conf [citrix:sharefile:audit] with EXTRACT-action for event_type/action/operation and FIELDALIAS-user so reports join cleanly. Step 2: Create the search and report — Save the base SPL as a scheduled weekly compliance report; add an ad-hoc drill form that runs `index=sharefile (sourcetype="citrix:sharefile:audit" OR sourcetype="citrix:sharefile:admin") user="$user$" earliest=-24h` for investigations. Step 3: Validate — Compare `| bin _time span=1d | stats count` to a manual sample from the ShareFile admin UI for one day; reconcile field coverage. Step 4: Operationalize — Assign data owner, index retention, and role-based access; document under records management; if totals diverge from the product, escalate to the ShareFile administration team.

## SPL

```spl
index=sharefile (sourcetype="citrix:sharefile:audit" OR sourcetype="citrix:sharefile:admin") earliest=-7d
| eval act=lower(coalesce(event_type, action, operation, "unknown"))
| eval actor=if(isnull(actor_type) OR actor_type="", "user", actor_type)
| bin _time span=1d
| stats count as events, dc(user) as users, values(act) as actions by _time, actor
| table _time, actor, events, users, actions
```

## Visualization

Table: daily event counts; pie: user vs admin share; drill to raw event list; optional PDF/CSV scheduled report for auditors.

## References

- [Citrix — ShareFile audit and logging](https://docs.citrix.com/en-us/citrix-content-collaboration/audit-trail-logs.html)
