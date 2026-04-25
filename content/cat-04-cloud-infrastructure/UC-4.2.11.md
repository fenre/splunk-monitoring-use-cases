<!-- AUTO-GENERATED from UC-4.2.11.json — DO NOT EDIT -->

---
id: "4.2.11"
title: "Resource Health Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.11 · Resource Health Events

## Description

Azure service health impacts your resources directly. Knowing when Azure itself is having problems prevents wasted troubleshooting time.

## Value

Azure service health impacts your resources directly. Knowing when Azure itself is having problems prevents wasted troubleshooting time.

## Implementation

Resource Health events flow through the Activity Log. Monitor for Unavailable and Degraded statuses. Correlate with your application health metrics to distinguish Azure platform issues from your own problems.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Resource Health via Activity Log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Resource Health events flow through the Activity Log. Monitor for Unavailable and Degraded statuses. Correlate with your application health metrics to distinguish Azure platform issues from your own problems.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" category.value="ResourceHealth"
| table _time resourceGroupName resourceType status.value properties.cause properties.currentHealthStatus
| sort -_time
```

Understanding this SPL

**Resource Health Events** — Azure service health impacts your resources directly. Knowing when Azure itself is having problems prevents wasted troubleshooting time.

Documented **Data sources**: Azure Resource Health via Activity Log. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Resource Health Events**): table _time resourceGroupName resourceType status.value properties.cause properties.currentHealthStatus
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Resource Health Events** — Azure service health impacts your resources directly.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model `Change.All_Changes` — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Resource Health Events** — Azure service health impacts your resources directly.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Resource Health Events** — Azure service health impacts your resources directly.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Resource Health Events** — Azure service health impacts your resources directly.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Resource Health Events** — Azure service health impacts your resources directly.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel per resource type, Table, Timeline.

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" category.value="ResourceHealth"
| table _time resourceGroupName resourceType status.value properties.cause properties.currentHealthStatus
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Status panel per resource type, Table, Timeline.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
