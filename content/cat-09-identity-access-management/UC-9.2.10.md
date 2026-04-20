---
id: "9.2.10"
title: "LDAPS Certificate Validation"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.10 · LDAPS Certificate Validation

## Description

LDAPS clients failing TLS handshakes or cert validation indicate expired CAs, hostname mismatches, or MITM attempts.

## Value

LDAPS clients failing TLS handshakes or cert validation indicate expired CAs, hostname mismatches, or MITM attempts.

## Implementation

Forward Schannel and LDAP server TLS logs. Map to cert renewal runbook. Alert on spike in handshake failures after cert rotation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Windows Schannel, OpenLDAP TLS logs.
• Ensure the following data sources are available: System log Schannel errors (36870, 36866), slapd TLS errors.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Schannel and LDAP server TLS logs. Map to cert renewal runbook. Alert on spike in handshake failures after cert rotation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName="Schannel" EventCode IN (36870,36866)
| stats count by ComputerName, EventCode, Message
| sort -count
```

Understanding this SPL

**LDAPS Certificate Validation** — LDAPS clients failing TLS handshakes or cert validation indicate expired CAs, hostname mismatches, or MITM attempts.

Documented **Data sources**: System log Schannel errors (36870, 36866), slapd TLS errors. **App/TA** (typical add-on context): Windows Schannel, OpenLDAP TLS logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ComputerName, EventCode, Message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (hosts with TLS errors), Timeline, Single value (LDAPS errors 24h).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName="Schannel" EventCode IN (36870,36866)
| stats count by ComputerName, EventCode, Message
| sort -count
```

## Visualization

Table (hosts with TLS errors), Timeline, Single value (LDAPS errors 24h).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
