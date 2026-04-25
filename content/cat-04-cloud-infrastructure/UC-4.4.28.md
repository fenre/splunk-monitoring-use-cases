<!-- AUTO-GENERATED from UC-4.4.28.json — DO NOT EDIT -->

---
id: "4.4.28"
title: "Hybrid Identity Synchronization Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.28 · Hybrid Identity Synchronization Health

## Description

AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

## Value

AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

## Implementation

Ingest connector health JSON or Event Hub stream. Correlate with password hash sync errors and object export failures. Alert on any failed sync window or rising error count.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Windows/Entra diagnostics, GCP Identity logs.
• Ensure the following data sources are available: `sourcetype=mscs:azure:audit` / AD Connect health, `sourcetype=WinEventLog:Security` (on-prem), `sourcetype=google:gcp:pubsub:message` (identity sync).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest connector health JSON or Event Hub stream. Correlate with password hash sync errors and object export failures. Alert on any failed sync window or rising error count.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=azure sourcetype="mscs:azure:audit" (operationName.value="*AADConnect*" OR activityDisplayName="*sync*") activityStatus!="Success")
 OR (index=identity sourcetype="adconnect:health" status!="success")
| eval connector_name=coalesce(connector_name, resourceGroupName, "aadconnect")
| stats count by sourcetype, connector_name, bin(_time, 1h)
```

Understanding this SPL

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

Documented **Data sources**: `sourcetype=mscs:azure:audit` / AD Connect health, `sourcetype=WinEventLog:Security` (on-prem), `sourcetype=google:gcp:pubsub:message` (identity sync). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Windows/Entra diagnostics, GCP Identity logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure, identity; **sourcetype**: mscs:azure:audit, adconnect:health. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, index=identity, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **connector_name** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by sourcetype, connector_name, bin(_time, 1h)** so each row reflects one combination of those dimensions.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

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

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

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

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

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

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

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

**Hybrid Identity Synchronization Health** — AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Change` data model (`All_Changes` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (sync status), Table (connector, error), Single value (last successful sync age in minutes).

## SPL

```spl
(index=azure sourcetype="mscs:azure:audit" (operationName.value="*AADConnect*" OR activityDisplayName="*sync*") activityStatus!="Success")
 OR (index=identity sourcetype="adconnect:health" status!="success")
| eval connector_name=coalesce(connector_name, resourceGroupName, "aadconnect")
| stats count by sourcetype, connector_name, bin(_time, 1h)
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Timeline (sync status), Table (connector, error), Single value (last successful sync age in minutes).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
