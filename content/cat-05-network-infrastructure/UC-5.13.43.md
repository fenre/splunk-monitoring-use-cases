<!-- AUTO-GENERATED from UC-5.13.43.json — DO NOT EDIT -->

---
id: "5.13.43"
title: "Client Connection Failure Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.43 · Client Connection Failure Analysis

## Description

Analyzes client connection failures by reason, connection type, and SSID to identify the root cause of connectivity problems.

## Value

Connection failures frustrate users and generate helpdesk tickets. Categorizing failures by reason (auth, DHCP, association) points directly to the failing infrastructure component.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `connectionStatus`, `onboardingStatus`, `failureReason`, `connectionType`, `ssid`, `macAddress`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with `cisco:dnac:client` including `connectionStatus`, `onboardingStatus`, and `failureReason` in failed-path events.
• Enumerate the exact values your controller uses (FAILED vs `Failure` or numeric codes) so the `OR` block does not miss rows.
• `docs/implementation-guide.md`.

Step 1 — Configure data collection
• MAC-level client feed is PII; scope dashboards to NOC/Wireless teams.

Step 2 — Failure counts by reason and segment
```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED") | stats count as failure_count by failureReason, connectionType, ssid | sort -failure_count
```

Understanding this SPL (dominant failure class)
**Client Connection Failure Analysis** — Surfaces the top **failureReason** strings and whether they are wired or wireless, and which **SSID** is implicated, so you can hand off to the right team (RADIUS, DHCP, RF).

**Pipeline walkthrough**
• `FAILED` on connection or onboarding → `stats` by `failureReason`, `connectionType`, `ssid` → `sort` by count.

Step 3 — Validate
• Sample top `failureReason` in Splunk, then locate the same reason class in the Catalyst **Clients** or **Troubleshooting** UI for a known bad session.
• If `failureReason` is null, the TA or Catalyst may map errors elsewhere—`fieldsummary failureReason` and inspect raw JSON.

Step 4 — Operationalize
• Alert on new failure signature in the last 24h (add `| rare failureReason` in a second panel) to catch a fresh radius misconfiguration before ticket volume explodes. Include `connectionType` and `ssid` in the alert payload for context.

Step 5 — Troubleshooting
• All failures missing: status field names differ in your version—broaden to `*fail*` on raw `_raw` in lab only, then add proper `props`.
• Mass failures during controller upgrade: suppress alerts during that window; correlate to change records.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" (connectionStatus="FAILED" OR onboardingStatus="FAILED") | stats count as failure_count by failureReason, connectionType, ssid | sort -failure_count
```

## Visualization

Table (failureReason, connectionType, ssid, failure_count), bar chart of top failure reasons, alert when new dominant failure class appears.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
