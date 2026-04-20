---
id: "9.1.20"
title: "AD Replication Topology Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.20 · AD Replication Topology Changes

## Description

New connections, site link, or bridgehead changes can indicate persistence or misconfiguration affecting auth paths.

## Value

New connections, site link, or bridgehead changes can indicate persistence or misconfiguration affecting auth paths.

## Implementation

Enable KCC and replication diagnostics. Ingest periodic topology snapshots. Alert on new unexpected replication partners or disabled site links outside change windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, `repadmin` / scripted input.
• Ensure the following data sources are available: Directory Service events (KCC topology), scripted `repadmin /showconn` / `nltest`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable KCC and replication diagnostics. Ingest periodic topology snapshots. Alert on new unexpected replication partners or disabled site links outside change windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog (sourcetype="WinEventLog:Directory Service" EventCode IN (1308,1311,1394)) OR sourcetype="ad:topology"
| table _time, host, EventCode, Message, connection_from, connection_to
| sort -_time
```

Understanding this SPL

**AD Replication Topology Changes** — New connections, site link, or bridgehead changes can indicate persistence or misconfiguration affecting auth paths.

Documented **Data sources**: Directory Service events (KCC topology), scripted `repadmin /showconn` / `nltest`. **App/TA** (typical add-on context): `Splunk_TA_windows`, `repadmin` / scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Directory Service, ad:topology. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Directory Service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **AD Replication Topology Changes**): table _time, host, EventCode, Message, connection_from, connection_to
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (topology events), Table (connection changes), Diagram export (optional via lookup).

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
index=wineventlog (sourcetype="WinEventLog:Directory Service" EventCode IN (1308,1311,1394)) OR sourcetype="ad:topology"
| table _time, host, EventCode, Message, connection_from, connection_to
| sort -_time
```

## Visualization

Timeline (topology events), Table (connection changes), Diagram export (optional via lookup).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
