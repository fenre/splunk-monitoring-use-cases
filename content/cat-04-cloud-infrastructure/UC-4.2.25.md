<!-- AUTO-GENERATED from UC-4.2.25.json — DO NOT EDIT -->

---
id: "4.2.25"
title: "Entra ID Conditional Access Blocked Sign-Ins"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.25 · Entra ID Conditional Access Blocked Sign-Ins

## Description

Blocked sign-ins by Conditional Access indicate policy enforcement. Tracking blocks helps tune policies and detect bypass attempts.

## Value

Blocked sign-ins by Conditional Access indicate policy enforcement. Tracking blocks helps tune policies and detect bypass attempts.

## Implementation

Forward sign-in logs. Filter for resultType or status indicating block (e.g. conditional access block). Alert on spike in blocks or blocks for sensitive apps. Correlate with risk and device compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Entra ID sign-in logs (resultType=0 for success; filter for blocks).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward sign-in logs. Filter for resultType or status indicating block (e.g. conditional access block). Alert on spike in blocks or blocks for sensitive apps. Correlate with risk and device compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:signinlog" status.errorCode!="0"
| stats count by userPrincipalName appDisplayName status.errorCode location
| sort -count
```

Understanding this SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement. Tracking blocks helps tune policies and detect bypass attempts.

Documented **Data sources**: Entra ID sign-in logs (resultType=0 for success; filter for blocks). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:signinlog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:signinlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userPrincipalName appDisplayName status.errorCode location** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model `Authentication.Authentication` — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Authentication` data model (`Authentication` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Authentication` data model (`Authentication` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Authentication` data model (`Authentication` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Conditional Access Blocked Sign-Ins** — Blocked sign-ins by Conditional Access indicate policy enforcement.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Authentication` data model (`Authentication` dataset)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, app, error, location), Bar chart (blocks by reason), Timeline.

## SPL

```spl
index=azure sourcetype="mscs:azure:signinlog" status.errorCode!="0"
| stats count by userPrincipalName appDisplayName status.errorCode location
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.action Authentication.src span=1h
| sort -count
```

## Visualization

Table (user, app, error, location), Bar chart (blocks by reason), Timeline.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
