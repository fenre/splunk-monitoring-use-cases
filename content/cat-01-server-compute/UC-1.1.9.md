<!-- AUTO-GENERATED from UC-1.1.9.json — DO NOT EDIT -->

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
• `stats` rolls up events into metrics; results are split **by host, sudo_user, command** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

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

## Visualization

Table (user, host, command, count), Bar chart of sudo failures by user, Events list for investigation.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
