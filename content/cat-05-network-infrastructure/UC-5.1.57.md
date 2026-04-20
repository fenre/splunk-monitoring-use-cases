---
id: "5.1.57"
title: "Junos Commit History and Configuration Rollback Audit (Juniper)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.57 · Junos Commit History and Configuration Rollback Audit (Juniper)

## Description

Junos treats configuration as a sequence of commits, so every change is tied to a user, time, and optional comment—ideal for audit and rollback to any of the last stored revisions. Without central logging, you lose the evidence needed to prove who changed routing, security zones, or interfaces during an incident. Correlating commits with change tickets catches unapproved changes and commits outside maintenance windows before they propagate through routing or firewall policy.

## Value

Junos treats configuration as a sequence of commits, so every change is tied to a user, time, and optional comment—ideal for audit and rollback to any of the last stored revisions. Without central logging, you lose the evidence needed to prove who changed routing, security zones, or interfaces during an incident. Correlating commits with change tickets catches unapproved changes and commits outside maintenance windows before they propagate through routing or firewall policy.

## Implementation

Ensure `interactive-commands` (or equivalent) is logged to the host that forwards to Splunk. Parse `UI_COMMIT` / `UI_COMMIT_COMPLETED` lines; if the TA already extracts `user`, prefer that field over `rex`. Alert on commits from break-glass accounts or when `_time` is outside approved windows (lookup). Join to change-management lookup by ticket ID when comments include ticket numbers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper`, syslog.
• Ensure the following data sources are available: `sourcetype=juniper:junos:structured`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure `interactive-commands` (or equivalent) is logged to the host that forwards to Splunk. Parse `UI_COMMIT` / `UI_COMMIT_COMPLETED` lines; if the TA already extracts `user`, prefer that field over `rex`. Alert on commits from break-glass accounts or when `_time` is outside approved windows (lookup). Join to change-management lookup by ticket ID when comments include ticket numbers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="juniper:junos:structured"
| search UI_COMMIT OR UI_COMMIT_COMPLETED OR "UI_COMMIT_EVENT"
| rex field=_raw "(?i)user\s+['\"]?(?<commit_user>[^\s'\"]+)"
| rex field=_raw "(?i)comment\s*[:=]\s*['\"]?(?<commit_comment>[^'\"\n]+)"
| rex field=_raw "configuration committed by (?<commit_user2>\S+)"
| eval operator=coalesce(commit_user, commit_user2, user)
| stats earliest(_time) as first_seen, latest(_time) as last_seen, count as commits, latest(commit_comment) as last_comment by host, operator
| sort -last_seen
```

Understanding this SPL

**Junos Commit History and Configuration Rollback Audit (Juniper)** — Junos treats configuration as a sequence of commits, so every change is tied to a user, time, and optional comment—ideal for audit and rollback to any of the last stored revisions. Without central logging, you lose the evidence needed to prove who changed routing, security zones, or interfaces during an incident. Correlating commits with change tickets catches unapproved changes and commits outside maintenance windows before they propagate through routing or firewall policy.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:structured. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **operator** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, operator** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t latest(All_Changes.status) as agg_value from datamodel=Change.All_Changes by All_Changes.dest | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Junos Commit History and Configuration Rollback Audit (Juniper)** — Junos treats configuration as a sequence of commits, so every change is tied to a user, time, and optional comment—ideal for audit and rollback to any of the last stored revisions. Without central logging, you lose the evidence needed to prove who changed routing, security zones, or interfaces during an incident. Correlating commits with change tickets catches unapproved changes and commits outside maintenance windows before they propagate through routing or firewall policy.

Documented **Data sources**: `sourcetype=juniper:junos:structured`. **App/TA** (typical add-on context): `Splunk_TA_juniper`, syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Commit timeline by device; table of last commit per host with user and comment; compliance panel for commits without matching change record.

## SPL

```spl
index=network sourcetype="juniper:junos:structured"
| search UI_COMMIT OR UI_COMMIT_COMPLETED OR "UI_COMMIT_EVENT"
| rex field=_raw "(?i)user\s+['\"]?(?<commit_user>[^\s'\"]+)"
| rex field=_raw "(?i)comment\s*[:=]\s*['\"]?(?<commit_comment>[^'\"\n]+)"
| rex field=_raw "configuration committed by (?<commit_user2>\S+)"
| eval operator=coalesce(commit_user, commit_user2, user)
| stats earliest(_time) as first_seen, latest(_time) as last_seen, count as commits, latest(commit_comment) as last_comment by host, operator
| sort -last_seen
```

## CIM SPL

```spl
| tstats summariesonly=t latest(All_Changes.status) as agg_value from datamodel=Change.All_Changes by All_Changes.dest | sort - agg_value
```

## Visualization

Commit timeline by device; table of last commit per host with user and comment; compliance panel for commits without matching change record.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
