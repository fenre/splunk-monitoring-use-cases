<!-- AUTO-GENERATED from UC-5.13.49.json — DO NOT EDIT -->

---
id: "5.13.49"
title: "After-Hours Administrative Activity"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.49 · After-Hours Administrative Activity

## Description

Identifies administrative actions performed outside normal business hours (before 6am, after 10pm, or on weekends), which may indicate unauthorized access.

## Value

After-hours admin activity is a common indicator of insider threats, compromised accounts, or unauthorized maintenance. Flagging it enables rapid investigation.

## Implementation

Enable the `audit_logs` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls audit log data from the Catalyst Center Intent API `/dna/intent/api/v1/audit/logs` every 5 minutes. Key fields: `auditRequestType`, `auditDescription`, `auditUserName`, `auditTimestamp`, `auditIpAddress`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with `cisco:dnac:audit:logs` (Intent `GET /dna/intent/api/v1/audit/logs`; typical 300s poll).
• `strftime` uses the timezone context of the search (Splunk user TZ or equivalent); align with your **written** off-hours policy. Fix NTP on the Catalyst and Splunk tiers before trusting hour-of-day for evidence—bad clocks shift the 6/22 cutoffs.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Define policy
• Adjust `hour<6 OR hour>22` and the weekend `where` to match *your* on-call and regional reality. For multi-continent orgs, enrich events with a site timezone from Catalyst or a lookup and evaluate hour in local time, not the search head only.

Step 2 — After-hours report
```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | eval hour=strftime(_time, "%H") | eval day=strftime(_time, "%a") | where (hour<6 OR hour>22) OR (day="Sat" OR day="Sun") | stats count as after_hours_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -after_hours_actions
```

Understanding this SPL (detective, not prescriptive)
**After-Hours Admin Activity** — All audit events whose `_time` falls outside the sample window, rolled up by `auditUserName` and `auditIpAddress`. It does **not** know intent; it is a triage list for the identity team, not a standalone breach detection.

**Pipeline walkthrough**
• `eval` of hour and day from `_time` → `where` for late night, early morning, or weekend → `stats` of counts and `values(auditRequestType)` per user+IP → sort by volume.

Step 3 — Validate
• Correlates each top row to ITSM: if the weekend window has a **tracked** **change** or on-call, treat as true negative for escalation and keep for attestation only.

Step 4 — Operationalize
• **SOC** optional alert: new `auditIpAddress` for a user who normally never appears off-hours, using a 30d baseline `lookup` (separate). Otherwise run as a weekly report to security governance.

Step 5 — Troubleshooting
• **Everyone** in the report: the whole team works nights—tighten `where` or add allowlists. **No one** in the report: UTC vs local, or all audit `_time` wrong—`fieldformat` a test with `strptime` on `auditTimestamp` if present in raw. **Catalyst** clock drift: fix in **Catalyst** first for legal defensibility, not a Splunk `eval` override alone.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:audit:logs" | eval hour=strftime(_time, "%H") | eval day=strftime(_time, "%a") | where (hour<6 OR hour>22) OR (day="Sat" OR day="Sun") | stats count as after_hours_actions values(auditRequestType) as action_types by auditUserName, auditIpAddress | sort -after_hours_actions
```

## Visualization

Table (auditUserName, auditIpAddress, after_hours_actions, action_types), timeline panel for manual review, optional alert to SOC when a known admin baseline changes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
