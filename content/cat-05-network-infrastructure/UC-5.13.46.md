<!-- AUTO-GENERATED from UC-5.13.46.json — DO NOT EDIT -->

---
id: "5.13.46"
title: "Configuration Change Audit Trail"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.46 · Configuration Change Audit Trail

## Description

Tracks all configuration changes made through Catalyst Center, including template deployments, provisioning actions, and policy changes.

## Value

Configuration changes are the leading cause of network outages. A complete audit trail enables rapid rollback and root-cause identification.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **audit_logs** → `cisco:dnac:audit:logs` in `index=catalyst` (typically `GET /dna/intent/api/v1/audit/logs`, 300s default poll in many releases).
• Wildcard filters on `auditRequestType` must be tuned: `PROVISION` can match more than you expect, and a Catalyst upgrade can add new type strings. Validate against `| stats count by auditRequestType` in a 24h window before locking into SOX or CM-3 evidence.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• Service account: must read the audit stream; confirm the TA documents which RBAC is required. Treat `auditUserName` and `auditIpAddress` as sensitive.

Step 2 — Config / provision / template activity
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="CONFIG*" OR auditRequestType="*PROVISION*" OR auditRequestType="*TEMPLATE*") | stats count as change_count values(auditDescription) as actions by auditUserName, auditIpAddress | sort -change_count
```

Understanding this SPL (change control evidence)
**Configuration Change Trail** — Who changed **what class** of Catalyst-originated work, from which **source** IP, with sample **descriptions** for CAB correlation.

**Pipeline walkthrough**
• Wildcard match on `auditRequestType` → `stats` by user and IP with **values** of `auditDescription` (may truncate) → sort by volume.

Step 3 — Validate
• For one high `change_count` row, expand raw events in the same user+IP+hour and compare to a known **approved** change. Map `values(auditDescription)` to ITSM tickets; expect multiline text to appear as separate multivalue entries.

Step 4 — Operationalize
• **SOX/CM-3:** export the table monthly with the Splunk time window noted in the workpaper. Add drilldown: `| search auditUserName="$row$"` to raw for auditors.

Step 5 — Troubleshooting
• **Empty** results: audit input disabled, wrong index, or API role missing read access to audit; check `splunkd.log` and Catalyst RBAC.
• **Wildcards** no longer match: `auditRequestType` values can change in an upgrade; run `| stats count by auditRequestType` and adjust the OR clauses.
• **Flood of noise** from a known service account: add a documented `where` exclusion for that principal or route automation to a second panel.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" (auditRequestType="CONFIG*" OR auditRequestType="*PROVISION*" OR auditRequestType="*TEMPLATE*") | stats count as change_count values(auditDescription) as actions by auditUserName, auditIpAddress | sort -change_count
```

## Visualization

Table (auditUserName, auditIpAddress, change_count, actions), timechart of config-related events, drilldown to raw events for ticket correlation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
