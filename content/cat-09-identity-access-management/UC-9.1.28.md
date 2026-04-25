<!-- AUTO-GENERATED from UC-9.1.28.json — DO NOT EDIT -->

---
id: "9.1.28"
title: "AD Certificate Services (ADCS) Anomalies"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.28 · AD Certificate Services (ADCS) Anomalies

## Description

ADCS misconfigurations enable privilege escalation (ESC1-ESC8 attacks). Monitoring certificate requests catches unauthorized certificate enrollment for domain admin impersonation.

## Value

ADCS misconfigurations enable privilege escalation (ESC1-ESC8 attacks). Monitoring certificate requests catches unauthorized certificate enrollment for domain admin impersonation.

## Implementation

Enable Certificate Services auditing on CA servers. EventCode 4887=certificate issued — track who requested which template. Alert on certificates with Subject Alternative Names (SANs) containing admin usernames (ESC1 attack). Monitor for certificate requests from non-standard templates. Track enrollment agent certificates (ESC3). Audit CA configuration for overly permissive templates with `certutil -v -template`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Certificate Services auditing on CA servers. EventCode 4887=certificate issued — track who requested which template. Alert on certificates with Subject Alternative Names (SANs) containing admin usernames (ESC1 attack). Monitor for certificate requests from non-standard templates. Track enrollment agent certificates (ESC3). Audit CA configuration for overly permissive templates with `certutil -v -template`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4886, 4887, 4888)
| eval action=case(EventCode=4886,"Request received",EventCode=4887,"Certificate issued",EventCode=4888,"Certificate denied")
| stats count by Requester, CertificateTemplate, SubjectName, action
| where CertificateTemplate IN ("User","SmartcardLogon","Machine") AND NOT match(Requester, "(?i)(SYSTEM|machine\\$)")
| sort -count
```

Understanding this SPL

**AD Certificate Services (ADCS) Anomalies** — ADCS misconfigurations enable privilege escalation (ESC1-ESC8 attacks). Monitoring certificate requests catches unauthorized certificate enrollment for domain admin impersonation.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4886, 4887, 4888). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by Requester, CertificateTemplate, SubjectName, action** so each row reflects one combination of those dimensions.
• Filters the current rows with `where CertificateTemplate IN ("User","SmartcardLogon","Machine") AND NOT match(Requester, "(?i)(SYSTEM|machine\\$)")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (certificate issuances), Bar chart (requests by template), Timeline, Alert on SAN mismatches.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4886, 4887, 4888)
| eval action=case(EventCode=4886,"Request received",EventCode=4887,"Certificate issued",EventCode=4888,"Certificate denied")
| stats count by Requester, CertificateTemplate, SubjectName, action
| where CertificateTemplate IN ("User","SmartcardLogon","Machine") AND NOT match(Requester, "(?i)(SYSTEM|machine\\$)")
| sort -count
```

## Visualization

Table (certificate issuances), Bar chart (requests by template), Timeline, Alert on SAN mismatches.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
