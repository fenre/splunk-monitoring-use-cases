<!-- AUTO-GENERATED from UC-2.6.72.json — DO NOT EDIT -->

---
id: "2.6.72"
title: "Citrix ShareFile Mass Download and Data Exfiltration Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.72 · Citrix ShareFile Mass Download and Data Exfiltration Detection

## Description

Unusual file movement through ShareFile can indicate exfiltration: large or repeated downloads, bursts of public link creation, off-hours bulk export, and access from anomalous locations. This use case focuses on high-signal mass behaviors rather than every single file open so analysts can respond quickly to theft or account abuse.

## Value

Unusual file movement through ShareFile can indicate exfiltration: large or repeated downloads, bursts of public link creation, off-hours bulk export, and access from anomalous locations. This use case focuses on high-signal mass behaviors rather than every single file open so analysts can respond quickly to theft or account abuse.

## Implementation

Ingest high-fidelity audit and API link events. Establish per-role baselines (sales vs finance). Tune byte and count thresholds; exclude known migration service accounts. Correlate with identity risk scores and end-point alerts. Contain with session revoke and link disable playbooks. Review privacy rules before full raw logging of filenames in regulated sectors.

## Detailed Implementation

Prerequisites
• ShareFile audit API or log export to Splunk with user, time, event type, and byte counts where available.
• Exclusion list of backup and migration users.

Step 1 — Configure data collection
Use a dedicated index and consistent sourcetype. Truncate or hash file names in regulated environments if required.

Step 2 — Create the search and alert
Adjust thresholds to your data volume. Add correlation to impossible travel in a separate use case. Alert on any row in the `where` clause with severity by tier (mass bytes vs public link storm).

Step 3 — Validate
Run against historical data from a known security drill if available. Compare counts to vendor reporting.

Step 4 — Operationalize
Tie alerts to a response playbook, assign an owner, and add drill links to the ShareFile admin UI.

## SPL

```spl
index=sharefile (sourcetype="citrix:sharefile:audit" OR sourcetype="citrix:sharefile:api") earliest=-24h
| eval evt=lower(coalesce(event_type, action, "")), is_dl=if(match(evt, "(?i)download|fetch|get"),1,0), is_link=if(match(evt, "(?i)create.*link|public.*link|share.*link"),1,0), b=tonumber(bytes), hour=strftime(_time, "%H"), fc=tonumber(file_count)
| eval off_hours=if(tonumber(hour)<6 OR tonumber(hour)>20,1,0)
| eval bulk=if(is_dl=1 AND (b>200000000 OR fc>200),1,0)
| bin _time span=1h
| stats sum(b) as tot_bytes, sum(bulk) as bulk_events, sum(is_link) as link_creates, sum(eval(off_hours=1 AND is_dl=1)) as offh_dl by _time, user, client_ip
| where tot_bytes>500000000 OR bulk_events>0 OR link_creates>50 OR offh_dl>30
| table _time, user, client_ip, tot_bytes, bulk_events, link_creates, offh_dl
```

## Visualization

Timechart: total bytes and link creates per hour; table: top users for bulk and off-hours; map or table: source IPs for flagged sessions (where available).

## References

- [Citrix — ShareFile audit logging overview](https://docs.citrix.com/en-us/citrix-content-collaboration/audit-trail-logs.html)
