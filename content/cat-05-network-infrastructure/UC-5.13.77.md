---
id: "5.13.77"
title: "Network Change MTTR Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.77 · Network Change MTTR Analysis

## Description

Analyzes mean time to repair (MTTR) for Catalyst Center issues and correlates with configuration changes to determine whether changes are improving or degrading resolution times.

## Value

MTTR is the key operational efficiency metric. Correlating with configuration changes reveals whether changes are helping (reducing MTTR) or hurting (introducing new issues).

## Implementation

1. **Issues:** Requires `cisco:dnac:issue` with `status=RESOLVED`, a valid **creation** time and **resolved** time — the SPL uses `_time` as detect and `resolved_time` as resolution; if your payload uses `creationTime`/`lastUpdatedTime`, rewrite `eval` lines to match **epoch** seconds.
2. **Audit:** `cisco:dnac:audit:logs` from Intent API audit stream; `auditRequestType="CONFIG*"` filters configuration changes. If your field is `auditRequestType` vs `requestType`, adjust.
3. **Join on category:** Both issue and audit must share a stable `category` string; if audit lacks `category`, join on `siteId` + time window instead (advanced).
4. **Schedule:** Weekly or monthly report; store in summary index for trending.
5. **Privacy:** Audit logs may contain usernames — restrict role access to this report.

## Detailed Implementation

Prerequisites
• UC-5.13.21 (issues) and UC-5.13.46 (audit / change awareness) with time-aligned data.
• Confirmed field names for resolution time on `cisco:dnac:issue` — common names: `resolvedTime`, `resolved_time`, or epoch in `status` transition — inspect one RESOLVED event with `| fieldsummary`.

Step 1 — Intent API context
- **Issues:** `GET /dna/intent/api/v1/issues` (poll via TA) — fields depend on DNAC version; map to `resolved_time` in props if needed.
- **Audit:** Intent API audit logs (path per version) — filter configuration-related operations; `auditRequestType` often prefixes with `CONFIG`.

Step 2 — Join reality check
- If `category` is not present on audit events, replace the join with:
  - `| join siteId [ search ... audit ... | ... ]` or
  - **Transaction** on `siteId` with `maxspan=24h` between issue open and audit (heavier).

Step 3 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval detect_time=_time | eval resolve_duration_hrs=round((resolved_time-detect_time)/3600,1) | stats avg(resolve_duration_hrs) as avg_mttr_hrs median(resolve_duration_hrs) as median_mttr_hrs p90(resolve_duration_hrs) as p90_mttr_hrs count as resolved_issues by category | join type=left category [search index=catalyst sourcetype="cisco:dnac:audit:logs" auditRequestType="CONFIG*" | stats count as related_changes by category] | eval change_correlation=if(isnotnull(related_changes),"Changes detected","No changes") | sort avg_mttr_hrs
```

Step 4 — Interpretation
- **Rising MTTR with high related_changes:** review change windows, CAB, and back-out plans.
- **Falling MTTR with changes:** may indicate faster automation (good) or under-reporting of issues (validate data quality).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval detect_time=_time | eval resolve_duration_hrs=round((resolved_time-detect_time)/3600,1) | stats avg(resolve_duration_hrs) as avg_mttr_hrs median(resolve_duration_hrs) as median_mttr_hrs p90(resolve_duration_hrs) as p90_mttr_hrs count as resolved_issues by category | join type=left category [search index=catalyst sourcetype="cisco:dnac:audit:logs" auditRequestType="CONFIG*" | stats count as related_changes by category] | eval change_correlation=if(isnotnull(related_changes),"Changes detected","No changes") | sort avg_mttr_hrs
```

## Visualization

Table: category, avg_mttr_hrs, median_mttr_hrs, p90_mttr_hrs, resolved_issues, related_changes, change_correlation; optional timechart of avg MTTR by week; box plot of resolve_duration_hrs.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
