<!-- AUTO-GENERATED from UC-4.4.26.json — DO NOT EDIT -->

---
id: "4.4.26"
title: "Cross-Cloud Resource Tagging Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.26 · Cross-Cloud Resource Tagging Compliance

## Description

A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

## Value

A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

## Implementation

Normalize required tag keys (for example Environment, Owner, CostCenter) in a lookup. Weekly trend of non-compliant count per provider. Alert when any provider’s gap exceeds SLA threshold.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure Policy exports, GCP Asset Inventory.
• Ensure the following data sources are available: `sourcetype=aws:config:notification`, Azure Policy compliance events, `sourcetype=google:gcp:pubsub:message` (asset exports).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize required tag keys (for example Environment, Owner, CostCenter) in a lookup. Weekly trend of non-compliant count per provider. Alert when any provider’s gap exceeds SLA threshold.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=aws sourcetype="aws:config:notification" configRuleName="*tag*" complianceType="NON_COMPLIANT")
 OR (index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant" operationName.value="*policy*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "missingLabelKeys")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"other")
| stats count by provider, resourceType, resourceGroup
| sort -count
```

Understanding this SPL

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

Documented **Data sources**: `sourcetype=aws:config:notification`, Azure Policy compliance events, `sourcetype=google:gcp:pubsub:message` (asset exports). **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure Policy exports, GCP Asset Inventory. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws, azure, gcp; **sourcetype**: aws:config:notification, mscs:azure:audit, google:gcp:pubsub:message. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, index=azure, index=gcp, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **provider** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by provider, resourceType, resourceGroup** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

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

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

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

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

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

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

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

**Cross-Cloud Resource Tagging Compliance** — A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar (non-compliant by provider over time), Table (resource, missing tags), Single value (compliance %).

## SPL

```spl
(index=aws sourcetype="aws:config:notification" configRuleName="*tag*" complianceType="NON_COMPLIANT")
 OR (index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant" operationName.value="*policy*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "missingLabelKeys")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"other")
| stats count by provider, resourceType, resourceGroup
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

Stacked bar (non-compliant by provider over time), Table (resource, missing tags), Single value (compliance %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
