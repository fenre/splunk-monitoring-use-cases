---
id: "9.1.24"
title: "Stale Computer Account Cleanup"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.1.24 · Stale Computer Account Cleanup

## Description

Stale computer objects enable rogue domain joins and clutter access reviews. Tracking supports automated disable/delete workflows.

## Value

Stale computer objects enable rogue domain joins and clutter access reviews. Tracking supports automated disable/delete workflows.

## Implementation

Export computer inventory weekly. Join with DHCP/DNS for false positives. Feed cleanup automation; exclude known appliance OUs via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input (PowerShell `Get-ADComputer`).
• Ensure the following data sources are available: AD computer attributes (`lastLogonTimestamp`, `pwdLastSet`, `whenCreated`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export computer inventory weekly. Join with DHCP/DNS for false positives. Feed cleanup automation; exclude known appliance OUs via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ad sourcetype="ad:computers"
| eval days_stale=round((now()-lastLogonTimestamp)/86400)
| where days_stale > 90 AND Enabled="True"
| table samAccountName, operatingSystem, days_stale, distinguishedName
| sort -days_stale
```

Understanding this SPL

**Stale Computer Account Cleanup** — Stale computer objects enable rogue domain joins and clutter access reviews. Tracking supports automated disable/delete workflows.

Documented **Data sources**: AD computer attributes (`lastLogonTimestamp`, `pwdLastSet`, `whenCreated`). **App/TA** (typical add-on context): Scripted input (PowerShell `Get-ADComputer`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ad; **sourcetype**: ad:computers. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ad, sourcetype="ad:computers". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_stale** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_stale > 90 AND Enabled="True"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Stale Computer Account Cleanup**): table samAccountName, operatingSystem, days_stale, distinguishedName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (stale computers), Bar chart (stale count by OU), Single value (candidates for cleanup).

## SPL

```spl
index=ad sourcetype="ad:computers"
| eval days_stale=round((now()-lastLogonTimestamp)/86400)
| where days_stale > 90 AND Enabled="True"
| table samAccountName, operatingSystem, days_stale, distinguishedName
| sort -days_stale
```

## Visualization

Table (stale computers), Bar chart (stale count by OU), Single value (candidates for cleanup).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
