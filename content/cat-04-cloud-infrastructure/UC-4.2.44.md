---
id: "4.2.44"
title: "Azure Resource Lock Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.44 · Azure Resource Lock Changes

## Description

Locks prevent accidental deletes; removing a lock before maintenance is high risk and must be audited.

## Value

Locks prevent accidental deletes; removing a lock before maintenance is high risk and must be audited.

## Implementation

Alert on Delete or write operations against lock resources. Require change ticket in comments where possible. Correlate with subsequent delete operations on parent resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:audit` (Microsoft.Authorization/locks).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Alert on Delete or write operations against lock resources. Require change ticket in comments where possible. Correlate with subsequent delete operations on parent resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*providers/Microsoft.Authorization/locks*"
| stats count by operationName.value, identity.claims.name, resourceGroupName
| sort -count
```

Understanding this SPL

**Azure Resource Lock Changes** — Locks prevent accidental deletes; removing a lock before maintenance is high risk and must be audited.

Documented **Data sources**: `sourcetype=mscs:azure:audit` (Microsoft.Authorization/locks). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by operationName.value, identity.claims.name, resourceGroupName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Azure Resource Lock Changes** — Locks prevent accidental deletes; removing a lock before maintenance is high risk and must be audited.

Documented **Data sources**: `sourcetype=mscs:azure:audit` (Microsoft.Authorization/locks). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (operation, user, resource group), Timeline (lock changes).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*providers/Microsoft.Authorization/locks*"
| stats count by operationName.value, identity.claims.name, resourceGroupName
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (operation, user, resource group), Timeline (lock changes).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
