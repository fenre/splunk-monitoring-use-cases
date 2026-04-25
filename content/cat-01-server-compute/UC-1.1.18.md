<!-- AUTO-GENERATED from UC-1.1.18.json — DO NOT EDIT -->

---
id: "1.1.18"
title: "User Account Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.18 · User Account Changes

## Description

Detects unauthorized user creation or modification. Key for security auditing and compliance (SOX, PCI, HIPAA).

## Value

Detects unauthorized user creation or modification. Key for security auditing and compliance (SOX, PCI, HIPAA).

## Implementation

Forward auth logs. Enable auditd rules for user management commands. Alert on any user creation/deletion events. Consider correlating with change management tickets.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=linux_secure`, `sourcetype=linux_audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward auth logs. Enable auditd rules for user management commands. Alert on any user creation/deletion events. Consider correlating with change management tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=linux_secure ("useradd" OR "userdel" OR "usermod" OR "groupadd" OR "passwd")
| rex "by (?<admin_user>\w+)"
| table _time host admin_user _raw
| sort -_time
```

Understanding this SPL

**User Account Changes** — Detects unauthorized user creation or modification. Key for security auditing and compliance (SOX, PCI, HIPAA).

Documented **Data sources**: `sourcetype=linux_secure`, `sourcetype=linux_audit`. **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: linux_secure. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=linux_secure. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **User Account Changes**): table _time host admin_user _raw
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events timeline, Table of account changes with who/what/when.

## SPL

```spl
index=os sourcetype=linux_secure ("useradd" OR "userdel" OR "usermod" OR "groupadd" OR "passwd")
| rex "by (?<admin_user>\w+)"
| table _time host admin_user _raw
| sort -_time
```

## Visualization

Events timeline, Table of account changes with who/what/when.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
