<!-- AUTO-GENERATED from UC-5.13.24.json — DO NOT EDIT -->

---
id: "5.13.24"
title: "Issue Resolution Time Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.24 · Issue Resolution Time Tracking

## Description

Measures how long it takes to resolve Catalyst Center assurance issues by priority and category, tracking mean time to resolve (MTTR).

## Value

MTTR is a key operational metric. Tracking resolution times by priority and category reveals bottlenecks and measures the effectiveness of the operations team.

## Implementation

Enable the `issue` input. Ensure `issue_time` and `resolved_time` (epoch seconds) are present in events or normalized via the TA. Validate field names if your build uses different aliases.

## Detailed Implementation

Prerequisites
• **issue** modular input to `cisco:dnac:issue` in `index=catalyst` (Cisco Catalyst Add-on 7538).
• **Validate field names** for **open** and **close** times on a **RESOLVED** raw event: `issue_time` and `resolved_time` are assumed to be **epoch seconds** as the SPL expects. If your TA uses **milliseconds** or **ISO strings**, add a normalizing **eval** in a macro before this search.
• **Status token** for closed issues (commonly **`RESOLVED`**) must match **case** your JSON uses—adjust the search filter if your tenant differs.
• `docs/implementation-guide.md` for retention (MTTR reports often need **90–180 days** of issues).

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/issues` (paged issue list).
• **TA input:** **issue**; typical **300–900s** poll; confirm whether **closed** issues are re-sent each cycle (affects how many **RESOLVED** rows you have per `issueId`).
• **Deduplication:** for MTTR, prefer **one row per `issueId` per state transition**; if the TA **replays** the same resolved issue, use **`| stats latest(resolved_time) as resolved_time ... by issueId`** in an intermediate saved search or **dedup** in validation first.

Step 2 — Create the report
```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval resolve_time_hrs=round((resolved_time-issue_time)/3600, 1) | stats avg(resolve_time_hrs) as avg_resolve_hrs median(resolve_time_hrs) as median_resolve_hrs max(resolve_time_hrs) as max_resolve_hrs by priority, category | sort priority
```

Understanding this SPL (time math, outliers, P1 first)
• **Negative** `resolve_time_hrs` means **data error** (clock skew or swapped fields); add **`| where resolve_time_hrs>=0`** in production.
• **Max** is sensitive to a single long-running TAC case; show **p95** in a v2 for leadership slides.
• **`sort priority`** is **lexicographic**—document if **P10**-style values ever appear.

**Pipeline walkthrough**
• Keeps **resolved** work only, converts duration to **hours**, aggregates **mean/median/max** by **priority** and **Assurance** **category**.

Step 3 — Validate
• Hand-check **2–3** issues in the **Catalyst** UI: compare **created/resolved** times to `issue_time`/`resolved_time` in Splunk in the same **TZ**.
• **`| timechart` count** of **RESOLVED** to ensure steady ingest, not a **one-time** bulk import that distorts **avg** for the week.
• **Sanity cap:** if **median** is **>10 days** and that surprises the team, segment by **category** and exclude **'informational'** in a v2.

Step 4 — Operationalize
• **Dashboard:** table of **avg/median/max**; **add** a **bar** of **median** by **category** for QBRs.
• **Cadence:** **monthly** PDF for service owners; not typically a **real-time** alert—pair with **UC-5.13.25** (repeaters) to drive **root cause** work.

Step 5 — Troubleshooting
• **NULL times:** `issue_time` / `resolved_time` not extracted—check **JSON** path in **props** and TA version.
• **Zeros everywhere:** you may have **ingest** of **placeholders**; confirm **raw** has non-zero epoch values.
• **Dramatic change after upgrade:** field rename in **Assurance** API—`fieldsummary` the **release week** and update **aliases** in **props**.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" status="RESOLVED" | eval resolve_time_hrs=round((resolved_time-issue_time)/3600, 1) | stats avg(resolve_time_hrs) as avg_resolve_hrs median(resolve_time_hrs) as median_resolve_hrs max(resolve_time_hrs) as max_resolve_hrs by priority, category | sort priority
```

## Visualization

Table (avg, median, max resolve hours by priority and category), bar chart of median MTTR by category.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
