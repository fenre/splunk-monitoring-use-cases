<!-- AUTO-GENERATED from UC-9.1.22.json — DO NOT EDIT -->

---
id: "9.1.22"
title: "GPO Tampering Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.22 · GPO Tampering Detection

## Description

Tampering via SYSVOL (file-level) may bypass 5136-only monitoring. File integrity on GPO paths catches unauthorized edits.

## Value

Tampering via SYSVOL (file-level) may bypass 5136-only monitoring. File integrity on GPO paths catches unauthorized edits.

## Implementation

Deploy FIM on DCs or SYSVOL replica members. Alert on new/modified GPO files outside change windows. Correlate with 5136 and DFS-R 4412/5004 events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, FIM TA (e.g., Splunk FIM or OSSEC).
• Ensure the following data sources are available: GPO change events (5136), SYSVOL file integrity events, DFS-R replication errors for SYSVOL.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy FIM on DCs or SYSVOL replica members. Alert on new/modified GPO files outside change windows. Correlate with 5136 and DFS-R 4412/5004 events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ossec sourcetype="ossec:fim" OR index=fim sourcetype="fim:change"
| search path="*\\SYSVOL\\*\\Policies\\*"
| stats count by path, user, action
| sort -count
```

Understanding this SPL

**GPO Tampering Detection** — Tampering via SYSVOL (file-level) may bypass 5136-only monitoring. File integrity on GPO paths catches unauthorized edits.

Documented **Data sources**: GPO change events (5136), SYSVOL file integrity events, DFS-R replication errors for SYSVOL. **App/TA** (typical add-on context): `Splunk_TA_windows`, FIM TA (e.g., Splunk FIM or OSSEC). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ossec, fim; **sourcetype**: ossec:fim, fim:change. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ossec, index=fim, sourcetype="ossec:fim". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by path, user, action** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action | sort - count
```

Understanding this CIM / accelerated SPL

**GPO Tampering Detection** — Tampering via SYSVOL (file-level) may bypass 5136-only monitoring. File integrity on GPO paths catches unauthorized edits.

Documented **Data sources**: GPO change events (5136), SYSVOL file integrity events, DFS-R replication errors for SYSVOL. **App/TA** (typical add-on context): `Splunk_TA_windows`, FIM TA (e.g., Splunk FIM or OSSEC). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare results with the authoritative identity source (directory, IdP, or PAM) for the same time range and with known change or maintenance tickets.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (file paths changed), Timeline, Bar chart (changes by DC).

## SPL

```spl
index=ossec sourcetype="ossec:fim" OR index=fim sourcetype="fim:change"
| search path="*\\SYSVOL\\*\\Policies\\*"
| stats count by path, user, action
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action | sort - count
```

## Visualization

Table (file paths changed), Timeline, Bar chart (changes by DC).

## References

- [GPO change events](https://splunkbase.splunk.com/app/5136)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
