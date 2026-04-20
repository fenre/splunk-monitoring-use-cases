---
id: "9.4.17"
title: "Just-in-Time Access Request Analysis"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.17 · Just-in-Time Access Request Analysis

## Description

Analytics on JIT volume, self-approval, and after-hours patterns complements simple volume alerts (UC-9.4.10).

## Value

Analytics on JIT volume, self-approval, and after-hours patterns complements simple volume alerts (UC-9.4.10).

## Implementation

Require justification text; alert on empty justification with approval. Report monthly JIT metrics to IAM governance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: PAM JIT / Entra PIM logs.
• Ensure the following data sources are available: Request ID, requester, approver, time-to-approve, business justification field.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Require justification text; alert on empty justification with approval. Report monthly JIT metrics to IAM governance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="jit:requests"
| eval same_approver=if(requester=approver,1,0)
| eval after_hours=if(hour(_time) < 6 OR hour(_time) > 22,1,0)
| stats count, sum(same_approver) as self_approvals, sum(after_hours) as off_hours by requester
| where self_approvals > 0 OR off_hours > 5
| sort -count
```

Understanding this SPL

**Just-in-Time Access Request Analysis** — Analytics on JIT volume, self-approval, and after-hours patterns complements simple volume alerts (UC-9.4.10).

Documented **Data sources**: Request ID, requester, approver, time-to-approve, business justification field. **App/TA** (typical add-on context): PAM JIT / Entra PIM logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: jit:requests. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="jit:requests". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **same_approver** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **after_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by requester** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where self_approvals > 0 OR off_hours > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Just-in-Time Access Request Analysis** — Analytics on JIT volume, self-approval, and after-hours patterns complements simple volume alerts (UC-9.4.10).

Documented **Data sources**: Request ID, requester, approver, time-to-approve, business justification field. **App/TA** (typical add-on context): PAM JIT / Entra PIM logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (risky patterns), Bar chart (self-approvals), Heatmap (hour × requester).

## SPL

```spl
index=pam sourcetype="jit:requests"
| eval same_approver=if(requester=approver,1,0)
| eval after_hours=if(hour(_time) < 6 OR hour(_time) > 22,1,0)
| stats count, sum(same_approver) as self_approvals, sum(after_hours) as off_hours by requester
| where self_approvals > 0 OR off_hours > 5
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (risky patterns), Bar chart (self-approvals), Heatmap (hour × requester).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
