---
id: "9.4.1"
title: "Privileged Session Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.1 · Privileged Session Audit

## Description

Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.

## Value

Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.

## Implementation

Install vendor PAM TA. Forward PAM vault/session logs to Splunk. Track all privileged sessions with full metadata. Alert on sessions outside business hours or to unexpected targets. Retain logs per compliance requirements.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_cyberark, BeyondTrust TA for Splunk.
• Ensure the following data sources are available: PAM session logs (session start/end, target system, user, protocol).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install vendor PAM TA. Forward PAM vault/session logs to Splunk. Track all privileged sessions with full metadata. Alert on sessions outside business hours or to unexpected targets. Retain logs per compliance requirements.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:session"
| table _time, user, target_host, target_account, protocol, duration_min, session_id
| sort -_time
```

Understanding this SPL

**Privileged Session Audit** — Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.

Documented **Data sources**: PAM session logs (session start/end, target system, user, protocol). **App/TA** (typical add-on context): Splunk_TA_cyberark, BeyondTrust TA for Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:session. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:session". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Privileged Session Audit**): table _time, user, target_host, target_account, protocol, duration_min, session_id
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.app, "(?i)pam|cyberark|beyondtrust|delinea")
  by Authentication.user Authentication.dest Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Privileged Session Audit** — Complete audit trail of privileged sessions is required for compliance (SOX, PCI, HIPAA) and security investigation.

Documented **Data sources**: PAM session logs (session start/end, target system, user, protocol). **App/TA** (typical add-on context): Splunk_TA_cyberark, BeyondTrust TA for Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (session history), Bar chart (sessions by user), Timeline (privileged access events), Heatmap (user × time of day).

## SPL

```spl
index=pam sourcetype="cyberark:session"
| table _time, user, target_host, target_account, protocol, duration_min, session_id
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.app, "(?i)pam|cyberark|beyondtrust|delinea")
  by Authentication.user Authentication.dest Authentication.src span=1h
| sort -count
```

## Visualization

Table (session history), Bar chart (sessions by user), Timeline (privileged access events), Heatmap (user × time of day).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
