<!-- AUTO-GENERATED from UC-4.4.10.json — DO NOT EDIT -->

---
id: "4.4.10"
title: "Cloud API Rate Limit and Throttling (429) Trends"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.4.10 · Cloud API Rate Limit and Throttling (429) Trends

## Description

429 (Too Many Requests) from cloud APIs indicate client or provider throttling. Tracking trends supports quota increase and architecture changes.

## Value

429 (Too Many Requests) from cloud APIs indicate client or provider throttling. Tracking trends supports quota increase and architecture changes.

## Implementation

Search audit logs for throttling errors (AWS ThrottlingException, Azure 429, GCP RESOURCE_EXHAUSTED). Dashboard by API and principal. Request quota increase when sustained. Consider exponential backoff and request batching in applications.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk TAs for each cloud (CloudTrail, Activity Log, GCP audit).
• Ensure the following data sources are available: CloudTrail (errorCode=ThrottlingException), Azure Activity Log (status=Throttled), GCP audit (status 429).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Search audit logs for throttling errors (AWS ThrottlingException, Azure 429, GCP RESOURCE_EXHAUSTED). Dashboard by API and principal. Request quota increase when sustained. Consider exponential backoff and request batching in applications.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudtrail" errorCode="ThrottlingException"
| stats count by eventName userIdentity.principalId
| sort -count
```

Understanding this SPL

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling. Tracking trends supports quota increase and architecture changes.

Documented **Data sources**: CloudTrail (errorCode=ThrottlingException), Azure Activity Log (status=Throttled), GCP audit (status 429). **App/TA** (typical add-on context): Splunk TAs for each cloud (CloudTrail, Activity Log, GCP audit). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudtrail. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudtrail". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by eventName userIdentity.principalId** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling.

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

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling.

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

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling.

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

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling.

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

**Cloud API Rate Limit and Throttling (429) Trends** — 429 (Too Many Requests) from cloud APIs indicate client or provider throttling.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (API, principal, 429 count), Line chart (429 over time), Bar chart (top throttled APIs).

## SPL

```spl
index=aws sourcetype="aws:cloudtrail" errorCode="ThrottlingException"
| stats count by eventName userIdentity.principalId
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

Table (API, principal, 429 count), Line chart (429 over time), Bar chart (top throttled APIs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
