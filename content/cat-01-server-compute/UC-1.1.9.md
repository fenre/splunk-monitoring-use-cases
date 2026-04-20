---
id: "1.1.9"
title: "Unauthorized Sudo Usage"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.9 · Unauthorized Sudo Usage

## Description

Repeated failed `sudo` attempts indicate attacker probing after account compromise; unexpected `sudo` success with destructive commands (e.g. `rm -rf`, `chmod 777`) may signal insider misuse or stolen credentials. Pair detection with IR steps: disable the account, revoke SSH keys, and review command history for lateral movement.

## Value

Repeated failed `sudo` attempts indicate attacker probing after account compromise; unexpected `sudo` success with destructive commands (e.g. `rm -rf`, `chmod 777`) may signal insider misuse or stolen credentials. Pair detection with IR steps: disable the account, revoke SSH keys, and review command history for lateral movement.

## Implementation

Forward auth logs. Alert immediately on `NOT in sudoers` events. For successful sudo, create audit dashboard showing who ran what with root privileges.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=linux_secure`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward auth logs. Alert immediately on `NOT in sudoers` events. For successful sudo, create audit dashboard showing who ran what with root privileges.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_secure "sudo:" ("NOT in sudoers" OR "authentication failure" OR "incorrect password")
| rex "user (?<sudo_user>\w+)"
| rex "COMMAND=(?<command>.+)"
| stats count by host, sudo_user, command
| sort -count
```

Understanding this SPL

**Unauthorized Sudo Usage** — Repeated failed `sudo` attempts indicate attacker probing after account compromise; unexpected `sudo` success with destructive commands (e.g. `rm -rf`, `chmod 777`) may signal insider misuse or stolen credentials. Pair detection with IR steps: disable the account, revoke SSH keys, and review command history for lateral movement.

Documented **Data sources**: `sourcetype=linux_secure`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, sudo_user, command** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

Understanding this CIM / accelerated SPL

**Unauthorized Sudo Usage** — Repeated failed `sudo` attempts indicate attacker probing after account compromise; unexpected `sudo` success with destructive commands (e.g. `rm -rf`, `chmod 777`) may signal insider misuse or stolen credentials. Pair detection with IR steps: disable the account, revoke SSH keys, and review command history for lateral movement.

Documented **Data sources**: `sourcetype=linux_secure`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, host, command, count), Bar chart of sudo failures by user, Events list for investigation.

## SPL

```spl
index=os sourcetype=linux_secure "sudo:" ("NOT in sudoers" OR "authentication failure" OR "incorrect password")
| rex "user (?<sudo_user>\w+)"
| rex "COMMAND=(?<command>.+)"
| stats count by host, sudo_user, command
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

## Visualization

Table (user, host, command, count), Bar chart of sudo failures by user, Events list for investigation.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
