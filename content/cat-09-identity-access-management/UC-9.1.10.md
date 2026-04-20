---
id: "9.1.10"
title: "Stale Account Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.1.10 · Stale Account Detection

## Description

Stale accounts are an attack surface — unused accounts may be compromised without detection. Regular cleanup reduces risk.

## Value

Stale accounts are an attack surface — unused accounts may be compromised without detection. Regular cleanup reduces risk.

## Implementation

Run PowerShell script querying AD for lastLogonTimestamp weekly. Export to CSV/JSON and ingest. Flag accounts inactive >90 days. Cross-reference with HR systems for departed employees. Report for access review.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input (PowerShell AD query).
• Ensure the following data sources are available: AD attributes (lastLogonTimestamp, pwdLastSet) via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run PowerShell script querying AD for lastLogonTimestamp weekly. Export to CSV/JSON and ingest. Flag accounts inactive >90 days. Cross-reference with HR systems for departed employees. Report for access review.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ad sourcetype="ad:accounts"
| eval days_inactive=round((now()-lastLogon)/86400)
| where days_inactive > 90 AND enabled="True"
| table samAccountName, displayName, days_inactive, ou, lastLogon
| sort -days_inactive
```

Understanding this SPL

**Stale Account Detection** — Stale accounts are an attack surface — unused accounts may be compromised without detection. Regular cleanup reduces risk.

Documented **Data sources**: AD attributes (lastLogonTimestamp, pwdLastSet) via scripted input. **App/TA** (typical add-on context): Scripted input (PowerShell AD query). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ad; **sourcetype**: ad:accounts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ad, sourcetype="ad:accounts". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_inactive** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_inactive > 90 AND enabled="True"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Stale Account Detection**): table samAccountName, displayName, days_inactive, ou, lastLogon
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (stale accounts), Bar chart (stale accounts by OU), Single value (total stale accounts), Pie chart (by account type).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=ad sourcetype="ad:accounts"
| eval days_inactive=round((now()-lastLogon)/86400)
| where days_inactive > 90 AND enabled="True"
| table samAccountName, displayName, days_inactive, ou, lastLogon
| sort -days_inactive
```

## Visualization

Table (stale accounts), Bar chart (stale accounts by OU), Single value (total stale accounts), Pie chart (by account type).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
