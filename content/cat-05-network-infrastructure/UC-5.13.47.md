<!-- AUTO-GENERATED from UC-5.13.47.json — DO NOT EDIT -->

---
id: "5.13.47"
title: "Privileged User Activity Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.47 · Privileged User Activity Monitoring

## Description

Monitors activity from privileged accounts (admins, super-admins) and user/role management actions to detect potential abuse or compromised credentials.

## Value

Privileged accounts can cause maximum damage. Monitoring their activity detects unauthorized use, credential compromise, and insider threats.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **audit_logs** writing `cisco:dnac:audit:logs` to `index=catalyst` (Intent `GET` audit log API; typical 300s poll).
• Tuning is mandatory: wildcards such as `*USER*` can over-match; add a lookup of allowed `auditRequestType` values in production, or list explicit request types for SOX/PCI evidence.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• Baseline your jump-box and VPN `auditIpAddress` values before any spike alert; a hot IP can be “normal” for 24/7 NOC work.

Step 2 — Privileged-activity view
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditUserName="admin" OR auditRequestType="*USER*" OR auditRequestType="*ROLE*" OR auditRequestType="*PERMISSION*") | stats count as action_count dc(auditRequestType) as unique_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -action_count
```

Understanding this SPL (identity and RBAC on Catalyst)
**Privileged user monitoring** — Ranks the loudest `auditUserName`+`auditIpAddress` pairs for identity-related `auditRequestType` strings, with a separate branch for a literal `admin` username. Replace the literal and wildcards to match your tenant and naming standard.

**Pipeline walkthrough**
• Filter to likely high-privilege work → `stats` for volume, `dc` of type, and `values` of type strings → `sort` by `action_count`.

Step 3 — Validate
• Cross-check the top 10 with your IdP: confirm whether each `auditUserName` is expected in that window (break-glass, TAC, or service principal). HR-driven bulk user sync can legitimately run up counts.

Step 4 — Operationalize
• Optional alert: a **new** `auditIpAddress` for a **known** admin account, implemented with a `lookup` of historical pairs; throttle and route to the identity team, not a generic on-call.

Step 5 — Troubleshooting
• After a Catalyst or TA upgrade, re-run `| stats count by auditRequestType` to refresh the wildcard list. No rows: filter too tight or the audit user never uses those strings. Time skew: align `auditTimestamp` with Splunk `_time` for PAM cross-checks—fix NTP on Catalyst, not in SPL alone, for evidential use.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditUserName="admin" OR auditRequestType="*USER*" OR auditRequestType="*ROLE*" OR auditRequestType="*PERMISSION*") | stats count as action_count dc(auditRequestType) as unique_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -action_count
```

## Visualization

Table (auditUserName, auditIpAddress, action_count, unique_actions, action_types), alert on spikes or new admin sources.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
