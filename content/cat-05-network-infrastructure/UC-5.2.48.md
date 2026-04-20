---
id: "5.2.48"
title: "Check Point Policy Install and Publish Tracking (Check Point)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.48 · Check Point Policy Install and Publish Tracking (Check Point)

## Description

Policy install pushes new rulebase and object changes from the management server (SmartConsole/Smart-1 Cloud) to enforcement gateways. A failed install leaves old policy active; a successful install with errors may silently break specific rules. Tracking install timestamps, success/failure, and who published enables change management correlation and root-cause analysis when traffic patterns shift unexpectedly after a policy push.

## Value

Policy install pushes new rulebase and object changes from the management server (SmartConsole/Smart-1 Cloud) to enforcement gateways. A failed install leaves old policy active; a successful install with errors may silently break specific rules. Tracking install timestamps, success/failure, and who published enables change management correlation and root-cause analysis when traffic patterns shift unexpectedly after a policy push.

## Implementation

Forward management audit logs via Log Exporter. Track policy install duration (publish → install complete). Alert on install failures or partial installs (some gateways succeeded, others failed). Require ITSM ticket IDs in SmartConsole session descriptions for audit correlation. Report on policy change frequency by admin and gateway.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259).
• Ensure the following data sources are available: `sourcetype=cp_log` (audit/admin logs), SmartConsole audit trail.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward management audit logs via Log Exporter. Track policy install duration (publish → install complete). Alert on install failures or partial installs (some gateways succeeded, others failed). Require ITSM ticket IDs in SmartConsole session descriptions for audit correlation. Report on policy change frequency by admin and gateway.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)smartconsole|smartcenter|management") AND match(lower(operation),"(?i)install|publish|verify")
| stats count earliest(_time) as first latest(_time) as last values(operation) as ops by administrator, target_gateway
| sort -last
```

Understanding this SPL

**Check Point Policy Install and Publish Tracking (Check Point)** — Policy install pushes new rulebase and object changes from the management server (SmartConsole/Smart-1 Cloud) to enforcement gateways. A failed install leaves old policy active; a successful install with errors may silently break specific rules. Tracking install timestamps, success/failure, and who published enables change management correlation and root-cause analysis when traffic patterns shift unexpectedly after a policy push.

Documented **Data sources**: `sourcetype=cp_log` (audit/admin logs), SmartConsole audit trail. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: checkpoint; **sourcetype**: cp_log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=checkpoint, sourcetype="cp_log", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(lower(product),"(?i)smartconsole|smartcenter|management") AND match(lower(operation),"(?i)install|publish|verify")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by administrator, target_gateway** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object span=1d
```

Understanding this CIM / accelerated SPL

**Check Point Policy Install and Publish Tracking (Check Point)** — Policy install pushes new rulebase and object changes from the management server (SmartConsole/Smart-1 Cloud) to enforcement gateways. A failed install leaves old policy active; a successful install with errors may silently break specific rules. Tracking install timestamps, success/failure, and who published enables change management correlation and root-cause analysis when traffic patterns shift unexpectedly after a policy push.

Documented **Data sources**: `sourcetype=cp_log` (audit/admin logs), SmartConsole audit trail. **App/TA** (typical add-on context): `Splunk_TA_checkpoint` (Splunkbase 5402), Check Point App for Splunk (Splunkbase 4293), CCX Add-on for Checkpoint Smart-1 Cloud (Splunkbase 7259). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (recent policy installs), Timeline (publish/install events), Bar chart (installs by admin), Single value (failed installs this week).

## SPL

```spl
index=checkpoint sourcetype="cp_log" earliest=-30d
| where match(lower(product),"(?i)smartconsole|smartcenter|management") AND match(lower(operation),"(?i)install|publish|verify")
| stats count earliest(_time) as first latest(_time) as last values(operation) as ops by administrator, target_gateway
| sort -last
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object span=1d
```

## Visualization

Table (recent policy installs), Timeline (publish/install events), Bar chart (installs by admin), Single value (failed installs this week).

## References

- [Check Point App for Splunk](https://splunkbase.splunk.com/app/4293)
- [CCX Add-on for Checkpoint Smart-1 Cloud](https://splunkbase.splunk.com/app/7259)
- [Splunkbase app 5402](https://splunkbase.splunk.com/app/5402)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
