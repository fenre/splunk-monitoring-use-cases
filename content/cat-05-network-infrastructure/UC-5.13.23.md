<!-- AUTO-GENERATED from UC-5.13.23.json — DO NOT EDIT -->

---
id: "5.13.23"
title: "P1/P2 Critical Issue Alerting"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.23 · P1/P2 Critical Issue Alerting

## Description

Alerts on unresolved P1 and P2 priority issues from Catalyst Center Assurance, which represent critical and high-impact network problems requiring immediate attention.

## Value

P1 and P2 issues affect large numbers of users or critical infrastructure. Immediate alerting in Splunk ensures they are routed to the right team within minutes.

## Implementation

Enable the `issue` input in the Cisco Catalyst TA. Confirm `status` and `priority` field extractions match Catalyst Center (for example `RESOLVED` for closed issues). Schedule this as an alert with short cadence for P1/P2 backlogs.

## Detailed Implementation

Prerequisites
• The **issue** modular input is enabled; raw JSON exposes `priority`, `status`, `name`, and `category` with the same spelling and case Catalyst Center returns.
• Confirm the **closed** status token (commonly `RESOLVED`) in your tenant—a mismatch causes endless pages or no pages at all.
• On-call runbook: who owns **P1** vs **P2** and when to open a **Cisco TAC** high-severity case in parallel.
• RBAC: **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** (or the tenant equivalent with read access to all active issues). In multi-tenant MSP deployments, align the input scope to the org you page for.
• `docs/implementation-guide.md` for credential rotation and audit logging on the host that runs the modular input.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/issues` with the **active/open** filter set the add-on supports (read the **TA README** for “open only” and default query parameters).
• **TA input name:** **issue**; sourcetype `cisco:dnac:issue`, index `catalyst` (or your chosen index; update the SPL to match).
• **Interval:** **300 seconds (5 minutes)** is typical for fresher P1/P2 backlogs. If the TA polls every 5m but Splunk runs this alert every 15m, that is a deliberate 10–12 minute maximum lag—document it for on-call. Align poll interval, Splunk schedule, and MTTD expectations together.
• **Volume:** the P1/P2 subset should be small in a healthy org; if `open_issues` is huge, the TA may be re-importing full history on every poll (see troubleshooting).
• **Key fields for this alert:** `priority` (P1/P2), `status` (to exclude closed), `name`, `category`; add `issueId` to a v2 of the search for ITSM idempotency and deduplication.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" | stats count as open_issues values(name) as issue_names values(category) as categories by priority | sort priority
```

Understanding this SPL (status strings, payload size, throttling)
• **`status!="RESOLVED"`** follows Cisco’s default string; if your tenant returns `Resolved` or localized text, use `| eval s=upper(status) | where s!="RESOLVED"` in a macro and reference the macro in saved searches.
• **P1/P2 only** by design—route P3/P4 to a daily digest, not the pager.
• **`values(name)`** in email can grow large—truncate with `mvindex` in a `eval` for the email body, or use a ServiceNow/ITSM mid-tier to format the payload.
• For chronic issues, add **`issueId`** in `stats ... by` and use alert suppression on `issueId` so the same TAC case does not re-page every 15 minutes after acknowledgement.

**Pipeline walkthrough**
• The search filters to P1 and P2, excluding resolved issues.
• `stats` counts open items per `priority` and rolls up `name` and `category` for context in the alert body.
• `sort priority` is lexicographic; for strict P1-before-P2 ordering when labels ever change, use a numeric `sev` from `replace`+`tonumber` in a macro (typical P1–P4 strings sort acceptably in most deployments).

Step 3 — Validate
• Create or use a test **P2** in a lab, leave it open, and confirm the search preview returns non-zero `open_issues` with sensible `issue_names` and `categories`.
• On a one-off search, `| where status="RESOLVED"` on recent data to confirm the TA does mark resolution in Splunk; if nothing is ever RESOLVED, fix field extraction or props before relying on the alert filter.
• `| timechart count by priority` for P1/P2 only: healthy orgs should see low sustained lines; a sky-high P2 count often means the TA is re-sending the whole backlog (dedup with `issueId` or fix the input).
• Compare counts to **Catalyst Center > Issues** with active P1/P2 filters in the same 15–30 minute window.

Step 4 — Operationalize (alerting)
• **Schedule:** every **15 minutes** with time range **last 16 minutes** (1 minute overlap) or **last 15 minutes**; overlaps reduce missed edges when polls and the scheduler do not line up.
• **Trigger:** number of results **> 0** (or refine with `open_issues>0` after a stats reshape for your org’s alert builder).
• **Throttle / suppression:** recommend a global cap of one alert per 15 minutes per run, plus per-`issueId` or per-`priority` throttling of 30–60 minutes when NOC has acknowledged in ITSM. Use Splunk’s alert suppression features or a lookup of “paged in last hour” for the same `issueId` once you add it to the search.
• **Actions:** P1 to primary on-call (SMS/voice), P2 to a collaboration channel; include `siteId`/`deviceId` if you extend the search. Deep-link to Catalyst **Issues** in the action template.
• “Recovered” or “all clear” webhooks are optional; many teams close lifecycle in ServiceNow only.

Step 5 — Troubleshooting
• **Pages never stop:** status string mismatch or the same `issueId` re-alerting; normalize status with `upper()` and add `issueId` to the pipeline for deduplication.
• **No page on a known P1:** RBAC on the service account, wrong Catalyst URL or virtual domain, or the **issue** input is pointed at a controller that is not the one showing the P1 in the UI.
• **Thousands of P2 results:** the input may re-pull the entire backlog every poll; enable an “active only” or equivalent filter in the add-on, or pre-dedup on `issueId` in a summary saved search the alert calls.
• **Upgrades** that rename `name` or duplicate `issueId`: deduplicate in a sibling search and document the change in the runbook; re-test after every TA or Catalyst major release.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" | stats count as open_issues values(name) as issue_names values(category) as categories by priority | sort priority
```

## Visualization

Single value or table (open_issues by priority), list of issue names and categories for the alert body.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
