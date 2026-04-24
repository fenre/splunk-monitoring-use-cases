---
id: "5.13.21"
title: "Assurance Issue Summary by Priority and Category"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.21 · Assurance Issue Summary by Priority and Category

## Description

Provides a summary of all active Catalyst Center Assurance issues grouped by priority (P1-P4) and category, enabling rapid triage.

## Value

Catalyst Center's AI/ML engine detects issues automatically. Centralizing these in Splunk enables cross-domain correlation and unified incident management.

## Implementation

Enable the `issue` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls the Intent API `/dna/intent/api/v1/issues` endpoint. Key fields: `priority` (P1-P4), `category` (Onboarding, Connected, Performance, etc.), `name` (issue description), `status`, `deviceId`.

## Detailed Implementation

Prerequisites
• **issue** modular input writing `cisco:dnac:issue` to `index=catalyst` (Cisco Catalyst Add-on 7538).
• Catalyst **2.3.5+** for stable **`priority` / `status` / `category` / `name`** strings; confirm **`RESOLVED` vs `Resolved` vs localized** text matches your `stats` and filters in downstream searches.
• Service account: **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** with read rights to the **issues** API (tenant-specific—**observer**-only is often too limited in **MSP**-locked orgs).
• Map **`category`** (e.g. **Onboarding, Connected, Performance**) to your **ITIL** or **ServiceNow** service taxonomy in documentation before automating tickets.
• `docs/implementation-guide.md` for modular input **secrets** and **logging** level on the **heavy forwarder** / **search head** running the input.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/issues` (paged; the TA may pass **query parameters** for **active** vs. **all**—check the add-on’s **Advanced** options and `README` for the exact filter set).
• **TA input name:** **issue**; sourcetype `cisco:dnac:issue`, index `catalyst`.
• **Default / recommended interval:** **300 seconds (5 minutes)** is common for fresher backlogs; **15 minutes** is acceptable in rate-limited environments—**match** the interval to your **NOC**’s “how stale is acceptable” policy.
• **Volume:** **one row per issue** on each successful poll, or paged **batches**—scales with **open** and **reopened** issues, not with traffic flows.
• **Key fields in raw data:** `priority` (P1–P4), `category`, `name` (title), `status`, `deviceId`, `issueId` (or equivalent) for ITSM **correlation**.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count by priority, category, name | sort -priority -count
```

Understanding this SPL (Pareto triage, text sort of `P*`, and noise)
• This is a **top-N Pareto** for **triage**—not a full issue **queue** list. The highest **counts** are **repeaters**; a **rare** **P1** can still be **one row** but must not be **ignored** in real ops (pair with a **P1** **alerting** UC).
• **Lexicographic** sort on **`priority`**: for plain **`P1`…`P4`** strings this is usually **fine**; if Cisco ever adds **`P10`**, add **`| eval sev=replace(priority,"P(\d+)", "\1") | ...`** in a **macro**—for crawl, monitor after upgrades.
• If the TA sends **closed** issues in every poll, **add** `where status!="RESOLVED"` in a v2 (or filter at the **input** if supported) so **counts** reflect **workable** backlog.
• **Name churn** on upgrades: keep a **lookup** to map **retired** issue titles for **year-over-year** **reports**.

**Pipeline walkthrough**
• Scopes **`cisco:dnac:issue`** in `catalyst`.
• **`stats count`** for each **priority / category / name** combination.
• **`sort -priority -count`** lists higher **priority** first, then **highest** **volume** within the band (subject to string sort caveat above).

Step 3 — Validate
• Run **`| stats count by priority`** to see the **P1–P4** mix; a sudden **P1** spike is either an **outage** or a **product** classification change.
• Compare top **name/category** rows to **Catalyst Center > Issues** for the **same** window; **Splunk** may count **repeated** **polls** of the same open issue as multiple events if the TA is misconfigured—**dedup** `issueId` in a validation search if you see **inflated** counts.
• `| timechart count` to confirm **continuous** **ingest**, not a **one-time** import.
• **`where isnotnull(issueId)`** if you plan **ITSM** **correlation**.

Step 4 — Operationalize
• **Dashboard layout:** **table** in the **left two-thirds** of a **NOC** triage page; **bar chart of count by `priority`** on the right for **at-a-glance** **severity** mix.
• **Time picker default:** **7 days** for **weekly** ops; **24 hours** in **incident** mode.
• **Row color:** in Dashboard Studio, set **`P1`** **rows** to **red**; **P4** **muted** so teams focus correctly.
• **Hand-off** to **Problem Management** when the same **name** sits at high **count** for **weeks**.

Step 5 — Troubleshooting
• **No `issue` events:** **issue** **input** disabled, **wrong** **index**, or **RBAC**—fix **API** user **role** and **Catalyst** **URL** first.
• **All issues `RESOLVED` in Splunk but UI shows open**—enable **“active only”**-style **filters** in the add-on, or the TA is pulling the **wrong** **status** set.
• **Spike on first** **poll**—**historical** **replay**; narrow the time **range** after **steady** state.
• **Priority** **strings** **changed** in an upgrade—**normalize** in a **macro** and re-test **triage** **dashboards** before **executive** review.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count by priority, category, name | sort -priority -count
```

## Visualization

Table (count by priority, category, name), bar chart (count by priority), pie chart (share by category).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
