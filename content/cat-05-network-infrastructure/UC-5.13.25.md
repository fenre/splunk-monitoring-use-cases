<!-- AUTO-GENERATED from UC-5.13.25.json — DO NOT EDIT -->

---
id: "5.13.25"
title: "Top Recurring Issues (Repeat Offenders)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.25 · Top Recurring Issues (Repeat Offenders)

## Description

Identifies Catalyst Center assurance issues that recur most frequently, revealing persistent problems that need root-cause investigation rather than repeated remediation.

## Value

Recurring issues waste operations time. Identifying repeat offenders enables root-cause analysis and permanent fixes instead of repeated band-aid responses.

## Implementation

Enable the `issue` input. Tune the `occurrence_count > 5` threshold to match environment size. Consider extending the time range for monthly reporting.

## Detailed Implementation

Prerequisites
• **issue** data in `cisco:dnac:issue` (Cisco Catalyst Add-on 7538).
• **Triage rule:** the **`occurrence_count > 5`** floor is arbitrary—**lower** for small sites (**>2**) and **raise** for global carriers where thousands of access points share the same **title** string.
• If the **TA logs every poll** of the same open issues, **count** is **inflated**; fix at source (**active-only** filter) or pre-dedup: **`| dedup issueId` per day** in a **summary** before this panel.
• `docs/implementation-guide.md` for summary-index patterns at scale.

Step 1 — Configure data collection
• **API:** `GET /dna/intent/api/v1/issues`.
• **Input:** **issue**; **interval** 300s typical for fresher work queues.
• **Key fields:** `name`, `category`, `deviceId` (optional **serial** in v2 for AP stacks).

Step 2 — Create the report
```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as occurrence_count dc(deviceId) as affected_devices earliest(_time) as first_seen latest(_time) as last_seen by name, category | where occurrence_count > 5 | eval days_active=round((last_seen-first_seen)/86400,0) | sort -occurrence_count
```

Understanding this SPL (chronic noise vs real repeaters)
• **`affected_devices`** (distinct `deviceId`) shows **blast radius**; if it is always **1**, you may be seeing **stale re-poll** of one flapping line, not a fleet-wide **bug** class.
• **`days_active`** is **search-window relative**; **30d** vs **7d** time picker changes the story—**pin** a **default** in the dashboard token.

**Pipeline walkthrough**
• Groups by human-readable **name** and **Assurance** **category**; surfaces **highest-occurrence** families for **problem management** and **Cisco** defect tracking.

Step 3 — Validate
• Pick the **#1** **name** and search raw **`issueId` values**; confirm they are **distinct** incidences or a **true** **repeat** pattern.
• Cross-check the **Catalyst** UI’s **'top issues'** (if available) in the same **time** frame.

Step 4 — Operationalize
• **Monthly** **problem** review: attach **Cisco** **bug** IDs and **TAC** SRs.
• **Not** a page-by-default alert; optional **low-priority** email when a **new** name enters the top five week-over-week.

Step 5 — Troubleshooting
• **Explosive** counts after **TA** restart: **history replay**; narrow time range after steady state or **dedup** `issueId`.
• **Empty table:** **floor** too high for your data volume; lower **5** to **2** in lab.
• **Nonsensical `deviceId`:** some issues are **system-wide** with **empty** `deviceId`—allow **NULL** in documentation.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as occurrence_count dc(deviceId) as affected_devices earliest(_time) as first_seen latest(_time) as last_seen by name, category | where occurrence_count > 5 | eval days_active=round((last_seen-first_seen)/86400,0) | sort -occurrence_count
```

## Visualization

Table (occurrence_count, affected_devices, days_active), bar chart of top issues by name.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
