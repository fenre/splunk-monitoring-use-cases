<!-- AUTO-GENERATED from UC-4.2.27.json — DO NOT EDIT -->

---
id: "4.2.27"
title: "Azure Policy Compliance and Non-Compliant Resources"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.27 · Azure Policy Compliance and Non-Compliant Resources

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance

*Azure Policy enforces governance.*

---

## Description

Azure Policy enforces governance. Non-compliant resources increase risk and compliance gaps. Tracking compliance supports remediation.

## Value

Azure Policy enforces governance. Non-compliant resources increase risk and compliance gaps. Tracking compliance supports remediation.

## Implementation

Use Azure Policy compliance API or export policy states to storage/Event Hub. Ingest in Splunk. Dashboard compliance % by policy and resource group. Alert when critical policy becomes non-compliant.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
- Ensure the following data sources are available: Policy state change events, Azure Monitor (policy compliance API or diagnostic).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Use Azure Policy compliance API or export policy states to storage/Event Hub. Ingest in Splunk. Dashboard compliance % by policy and resource group. Alert when critical policy becomes non-compliant.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" resourceId=*Microsoft.Authorization/policyAssignments*
| search complianceState="NonCompliant"
| stats count by policyDefinitionId resourceType
| sort -count
```

#### Understanding this SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance. Non-compliant resources increase risk and compliance gaps. Tracking compliance supports remediation.

Documented **Data sources**: Policy state change events, Azure Monitor (policy compliance API or diagnostic). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Applies an explicit `search` filter to narrow the current result set.
- `stats` rolls up events into metrics; results are split **by policyDefinitionId resourceType** so each row reflects one combination of those dimensions.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on accelerated data model `Change.All_Changes` — enable that model in Data Models and CIM add-ons, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Azure Policy Compliance and Non-Compliant Resources** — Azure Policy enforces governance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

- Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

- Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (policy, resource, state), Pie chart (compliant %), Bar chart (non-compliant by type).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" resourceId=*Microsoft.Authorization/policyAssignments*
| search complianceState="NonCompliant"
| stats count by policyDefinitionId resourceType
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Table (policy, resource, state), Pie chart (compliant %), Bar chart (non-compliant by type).

## Known False Positives

Our own break-glass and automation accounts show up the same as anyone else, and a delete or write during a change window is expected. We allowlist the roles that do routine maintenance and we link alerts to approved changes before we call an incident.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
