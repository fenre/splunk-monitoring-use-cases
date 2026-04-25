<!-- AUTO-GENERATED from UC-2.5.6.json — DO NOT EDIT -->

---
id: "2.5.6"
title: "IGEL UMS Security Audit Log Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.5.6 · IGEL UMS Security Audit Log Monitoring

## Description

IGEL UMS security audit logs capture critical administrative actions: user logins, failed authentication, password changes, device policy assignments, configuration modifications, and administrator account lifecycle events. Monitoring these events is essential for detecting unauthorized administrative access, policy tampering, and insider threats targeting the endpoint management plane.

## Value

IGEL UMS security audit logs capture critical administrative actions: user logins, failed authentication, password changes, device policy assignments, configuration modifications, and administrator account lifecycle events. Monitoring these events is essential for detecting unauthorized administrative access, policy tampering, and insider threats targeting the endpoint management plane.

## Implementation

Deploy a Splunk Universal Forwarder on the UMS server (Windows or Linux). Monitor the security log files: `ums-server-security.log`, `ums-admin-security.log`, `wums-app-security.log`. Enable remote security logging in UMS Administration > Global Configuration > Logging. Parse events using source tags (`UMS-Server`, `ICG`, `IMI`, `UMS-Webapp`). Alert on: failed login attempts exceeding 5 within 10 minutes, administrator account creation/deletion, device factory reset commands, and off-hours policy modifications.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder monitoring UMS security log files.
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `result`, `detail`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on the UMS server (Windows or Linux). Monitor the security log files: `ums-server-security.log`, `ums-admin-security.log`, `wums-app-security.log`. Enable remote security logging in UMS Administration > Global Configuration > Logging. Parse events using source tags (`UMS-Server`, `ICG`, `IMI`, `UMS-Webapp`). Alert on: failed login attempts exceeding 5 within 10 minutes, administrator account creation/deletion, device factory reset commands, and off-hours polic…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:security"
| eval event_category=case(
    match(event_type, "(?i)logon|login|logoff|authentication"), "Authentication",
    match(event_type, "(?i)password"), "Password Change",
    match(event_type, "(?i)assignment|profile|policy"), "Policy Change",
    match(event_type, "(?i)account|user.*creat|user.*delet"), "Account Lifecycle",
    match(event_type, "(?i)shutdown|restart"), "Service Lifecycle",
    1=1, "Other"
  )
| stats count by event_category, source_tag, result
| sort -count
| table event_category, source_tag, result, count
```

Understanding this SPL

**IGEL UMS Security Audit Log Monitoring** — IGEL UMS security audit logs capture critical administrative actions: user logins, failed authentication, password changes, device policy assignments, configuration modifications, and administrator account lifecycle events. Monitoring these events is essential for detecting unauthorized administrative access, policy tampering, and insider threats targeting the endpoint management plane.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `result`, `detail`. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring UMS security log files. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **event_category** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by event_category, source_tag, result** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **IGEL UMS Security Audit Log Monitoring**): table event_category, source_tag, result, count

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**IGEL UMS Security Audit Log Monitoring** — IGEL UMS security audit logs capture critical administrative actions: user logins, failed authentication, password changes, device policy assignments, configuration modifications, and administrator account lifecycle events. Monitoring these events is essential for detecting unauthorized administrative access, policy tampering, and insider threats targeting the endpoint management plane.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:security"` fields `source_tag`, `event_type`, `user`, `target`, `result`, `detail`. **App/TA** (typical add-on context): Splunk Universal Forwarder monitoring UMS security log files. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (events by category), Timeline (authentication events), Table (failed logins by user and source IP).

## SPL

```spl
index=endpoint sourcetype="igel:ums:security"
| eval event_category=case(
    match(event_type, "(?i)logon|login|logoff|authentication"), "Authentication",
    match(event_type, "(?i)password"), "Password Change",
    match(event_type, "(?i)assignment|profile|policy"), "Policy Change",
    match(event_type, "(?i)account|user.*creat|user.*delet"), "Account Lifecycle",
    match(event_type, "(?i)shutdown|restart"), "Service Lifecycle",
    1=1, "Other"
  )
| stats count by event_category, source_tag, result
| sort -count
| table event_category, source_tag, result, count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Bar chart (events by category), Timeline (authentication events), Table (failed logins by user and source IP).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
