<!-- AUTO-GENERATED from UC-9.2.4.json — DO NOT EDIT -->

---
id: "9.2.4"
title: "Replication Health Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.4 · Replication Health Monitoring

## Description

LDAP replication failures cause authentication inconsistencies and stale directory data across sites.

## Value

LDAP replication failures cause authentication inconsistencies and stale directory data across sites.

## Implementation

Monitor LDAP replication status via scripted input querying contextCSN or replication agreements. Forward syncrepl logs. Alert on replication failures or increasing lag between providers and consumers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Scripted input, LDAP server logs.
• Ensure the following data sources are available: LDAP replication logs, `ldapsearch` monitoring attributes (contextCSN).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor LDAP replication status via scripted input querying contextCSN or replication agreements. Forward syncrepl logs. Alert on replication failures or increasing lag between providers and consumers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ldap sourcetype="openldap:syncrepl"
| search "syncrepl" ("ERROR" OR "RETRY" OR "failed")
| stats count by host, provider
| where count > 0
```

Understanding this SPL

**Replication Health Monitoring** — LDAP replication failures cause authentication inconsistencies and stale directory data across sites.

Documented **Data sources**: LDAP replication logs, `ldapsearch` monitoring attributes (contextCSN). **App/TA** (typical add-on context): Scripted input, LDAP server logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ldap; **sourcetype**: openldap:syncrepl. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ldap, sourcetype="openldap:syncrepl". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by host, provider** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the directory server’s admin or audit view (bind DNs, result codes) for the same time range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (provider × consumer health), Table (replication status), Timeline (failure events).

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
index=ldap sourcetype="openldap:syncrepl"
| search "syncrepl" ("ERROR" OR "RETRY" OR "failed")
| stats count by host, provider
| where count > 0
```

## Visualization

Status grid (provider × consumer health), Table (replication status), Timeline (failure events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
