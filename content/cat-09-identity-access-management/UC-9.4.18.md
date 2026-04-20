---
id: "9.4.18"
title: "Emergency Break-Glass Account Usage"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.18 · Emergency Break-Glass Account Usage

## Description

Real-time paging for emergency-only vault accounts beyond standard break-glass (UC-9.4.3)—includes usage from non-SOC networks.

## Value

Real-time paging for emergency-only vault accounts beyond standard break-glass (UC-9.4.3)—includes usage from non-SOC networks.

## Implementation

Define emergency accounts in PAM and AD. Alert on any checkout or interactive logon; require post-incident report within SLA. Correlate with major incident tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk TA for CyberArk, AD Security logs.
• Ensure the following data sources are available: PAM checkout for accounts tagged `emergency_only`, 4624 for same sAMAccountName.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define emergency accounts in PAM and AD. Alert on any checkout or interactive logon; require post-incident report within SLA. Correlate with major incident tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:vault" account_tag="emergency_only"
| lookup soc_networks subnet OUTPUT network_name
| where isnull(network_name)
| table _time, user, account, client_ip, action
| sort -_time
```

Understanding this SPL

**Emergency Break-Glass Account Usage** — Real-time paging for emergency-only vault accounts beyond standard break-glass (UC-9.4.3)—includes usage from non-SOC networks.

Documented **Data sources**: PAM checkout for accounts tagged `emergency_only`, 4624 for same sAMAccountName. **App/TA** (typical add-on context): Splunk TA for CyberArk, AD Security logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:vault. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:vault". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where isnull(network_name)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Emergency Break-Glass Account Usage**): table _time, user, account, client_ip, action
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Emergency Break-Glass Account Usage** — Real-time paging for emergency-only vault accounts beyond standard break-glass (UC-9.4.3)—includes usage from non-SOC networks.

Documented **Data sources**: PAM checkout for accounts tagged `emergency_only`, 4624 for same sAMAccountName. **App/TA** (typical add-on context): Splunk TA for CyberArk, AD Security logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (emergency usage), Table (detail), Single value (events outside SOC net).

## SPL

```spl
index=pam sourcetype="cyberark:vault" account_tag="emergency_only"
| lookup soc_networks subnet OUTPUT network_name
| where isnull(network_name)
| table _time, user, account, client_ip, action
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Timeline (emergency usage), Table (detail), Single value (events outside SOC net).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
