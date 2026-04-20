---
id: "9.3.6"
title: "Phishing-Resistant MFA Adoption"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.3.6 · Phishing-Resistant MFA Adoption

## Description

Tracks migration from phishable factors (SMS, phone) to phishing-resistant factors (FIDO2, WebAuthn). Supports zero-trust maturity goals.

## Value

Tracks migration from phishable factors (SMS, phone) to phishing-resistant factors (FIDO2, WebAuthn). Supports zero-trust maturity goals.

## Implementation

Track MFA factor types used in authentication events. Classify as phishing-resistant (FIDO2, WebAuthn) vs phishable (SMS, voice, email). Report adoption percentages. Set organizational targets for phishing-resistant adoption.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, IdP MFA enrollment data.
• Ensure the following data sources are available: IdP MFA enrollment logs, factor type metadata.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track MFA factor types used in authentication events. Classify as phishing-resistant (FIDO2, WebAuthn) vs phishable (SMS, voice, email). Report adoption percentages. Set organizational targets for phishing-resistant adoption.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count by debugContext.debugData.factor
| eval factor_type=case(match(factor,"FIDO"),"phishing_resistant", match(factor,"push"),"medium", 1=1,"phishable")
| stats sum(count) as total by factor_type
```

Understanding this SPL

**Phishing-Resistant MFA Adoption** — Tracks migration from phishable factors (SMS, phone) to phishing-resistant factors (FIDO2, WebAuthn). Supports zero-trust maturity goals.

Documented **Data sources**: IdP MFA enrollment logs, factor type metadata. **App/TA** (typical add-on context): `Splunk_TA_okta`, IdP MFA enrollment data. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by debugContext.debugData.factor** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **factor_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by factor_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (factor type distribution), Line chart (phishing-resistant adoption trend), Table (users still on SMS).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.authentication.auth_via_mfa"
| stats count by debugContext.debugData.factor
| eval factor_type=case(match(factor,"FIDO"),"phishing_resistant", match(factor,"push"),"medium", 1=1,"phishable")
| stats sum(count) as total by factor_type
```

## Visualization

Pie chart (factor type distribution), Line chart (phishing-resistant adoption trend), Table (users still on SMS).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
