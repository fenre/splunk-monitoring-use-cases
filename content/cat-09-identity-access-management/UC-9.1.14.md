<!-- AUTO-GENERATED from UC-9.1.14.json — DO NOT EDIT -->

---
id: "9.1.14"
title: "Service Account Password Age"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.1.14 · Service Account Password Age

## Description

Service accounts with passwords older than policy permits increase risk exposure.

## Value

Service accounts with passwords older than policy permits increase risk exposure.

## Implementation

Run PowerShell or ldapsearch script querying AD for service accounts (filter by naming convention or OU). Export pwdLastSet and convert to days. Ingest via scripted input. Alert on accounts exceeding policy (e.g., >90 days). Maintain lookup of accounts with approved exceptions. Report for quarterly access reviews.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (AD inventory), SA-ldapsearch.
• Ensure the following data sources are available: AD attribute pwdLastSet on service accounts.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run PowerShell or ldapsearch script querying AD for service accounts (filter by naming convention or OU). Export pwdLastSet and convert to days. Ingest via scripted input. Alert on accounts exceeding policy (e.g., >90 days). Maintain lookup of accounts with approved exceptions. Report for quarterly access reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ad sourcetype="ad:accounts"
| search objectClass=serviceAccount OR samAccountName=svc_* OR samAccountName=*_svc
| eval days_since_pwd=round((now()-(pwdLastSet/10000000-11644473600))/86400)
| where days_since_pwd > 90 AND enabled="True"
| table samAccountName, displayName, days_since_pwd, ou
| sort -days_since_pwd
```

Understanding this SPL

**Service Account Password Age** — Service accounts with passwords older than policy permits increase risk exposure.

Documented **Data sources**: AD attribute pwdLastSet on service accounts. **App/TA** (typical add-on context): `Splunk_TA_windows` (AD inventory), SA-ldapsearch. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ad; **sourcetype**: ad:accounts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ad, sourcetype="ad:accounts". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `eval` defines or adjusts **days_since_pwd** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since_pwd > 90 AND enabled="True"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Service Account Password Age**): table samAccountName, displayName, days_since_pwd, ou
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (overdue service accounts), Bar chart (password age by OU), Single value (accounts over policy limit), Gauge (compliance %).

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
| search objectClass=serviceAccount OR samAccountName=svc_* OR samAccountName=*_svc
| eval days_since_pwd=round((now()-(pwdLastSet/10000000-11644473600))/86400)
| where days_since_pwd > 90 AND enabled="True"
| table samAccountName, displayName, days_since_pwd, ou
| sort -days_since_pwd
```

## Visualization

Table (overdue service accounts), Bar chart (password age by OU), Single value (accounts over policy limit), Gauge (compliance %).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
