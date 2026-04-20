---
id: "9.3.15"
title: "OAuth Scope Creep Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.3.15 · OAuth Scope Creep Detection

## Description

Applications accumulating scopes over time violate least privilege; comparing current vs approved scopes finds drift.

## Value

Applications accumulating scopes over time violate least privilege; comparing current vs approved scopes finds drift.

## Implementation

Export delegated/app role assignments from Graph weekly. Join with approved baseline. Alert on new sensitive scopes (`Mail.ReadWrite`, `Directory.ReadWrite.All`).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Graph API inventory, Okta `app.oauth2.*` events.
• Ensure the following data sources are available: OAuth scope grants per `client_id`, approved scope lookup CSV.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export delegated/app role assignments from Graph weekly. Join with approved baseline. Alert on new sensitive scopes (`Mail.ReadWrite`, `Directory.ReadWrite.All`).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=oauth sourcetype="oauth:scope_inventory"
| lookup oauth_scope_approved client_id OUTPUT approved_scopes
| eval extra_scopes=mvfilter(NOT match(approved_scopes, scope))
| where mvcount(extra_scopes)>0
| table client_id, scope, approved_scopes, extra_scopes
```

Understanding this SPL

**OAuth Scope Creep Detection** — Applications accumulating scopes over time violate least privilege; comparing current vs approved scopes finds drift.

Documented **Data sources**: OAuth scope grants per `client_id`, approved scope lookup CSV. **App/TA** (typical add-on context): Graph API inventory, Okta `app.oauth2.*` events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: oauth; **sourcetype**: oauth:scope_inventory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=oauth, sourcetype="oauth:scope_inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **extra_scopes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where mvcount(extra_scopes)>0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **OAuth Scope Creep Detection**): table client_id, scope, approved_scopes, extra_scopes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (scope drift), Bar chart (apps with extra scopes), Timeline.

## SPL

```spl
index=oauth sourcetype="oauth:scope_inventory"
| lookup oauth_scope_approved client_id OUTPUT approved_scopes
| eval extra_scopes=mvfilter(NOT match(approved_scopes, scope))
| where mvcount(extra_scopes)>0
| table client_id, scope, approved_scopes, extra_scopes
```

## Visualization

Table (scope drift), Bar chart (apps with extra scopes), Timeline.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
