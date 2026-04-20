---
id: "8.6.18"
title: "TFTP Unauthorized Access"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.6.18 · TFTP Unauthorized Access

## Description

TFTP should be rare in enterprise networks. Any RRQ/WRQ outside PXE scope may indicate data exfil or firmware abuse.

## Value

TFTP should be rare in enterprise networks. Any RRQ/WRQ outside PXE scope may indicate data exfil or firmware abuse.

## Implementation

Maintain allowlist for PXE subnets. Alert on any other TFTP read/write. Block TFTP at firewall unless required.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Firewall logs, `atftpd`/`tftpd` syslog.
• Ensure the following data sources are available: `tftp:syslog` `filename`, `op`, `src`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain allowlist for PXE subnets. Alert on any other TFTP read/write. Block TFTP at firewall unless required.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="tftp:log" OR sourcetype="syslog" process=tftpd
| search RRQ OR WRQ
| lookup tftp_allowed_subnets src OUTPUT allowed
| where allowed!=1 OR isnull(allowed)
| table _time, src, filename, op
```

Understanding this SPL

**TFTP Unauthorized Access** — TFTP should be rare in enterprise networks. Any RRQ/WRQ outside PXE scope may indicate data exfil or firmware abuse.

Documented **Data sources**: `tftp:syslog` `filename`, `op`, `src`. **App/TA** (typical add-on context): Firewall logs, `atftpd`/`tftpd` syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: tftp:log, syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="tftp:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where allowed!=1 OR isnull(allowed)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **TFTP Unauthorized Access**): table _time, src, filename, op


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (TFTP events), Table (unauthorized attempts), Single value (blocked attempts).

## SPL

```spl
index=network sourcetype="tftp:log" OR sourcetype="syslog" process=tftpd
| search RRQ OR WRQ
| lookup tftp_allowed_subnets src OUTPUT allowed
| where allowed!=1 OR isnull(allowed)
| table _time, src, filename, op
```

## Visualization

Timeline (TFTP events), Table (unauthorized attempts), Single value (blocked attempts).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
