---
id: "8.6.11"
title: "HashiCorp Vault Seal Status and Token Count"
criticality: "critical"
splunkPillar: "Security"
---

# UC-8.6.11 · HashiCorp Vault Seal Status and Token Count

## Description

Vault health, auto-unseal events, and token creation rate indicate secrets management availability. Sealed Vault blocks all secret access; token anomalies may indicate abuse.

## Value

Vault health, auto-unseal events, and token creation rate indicate secrets management availability. Sealed Vault blocks all secret access; token anomalies may indicate abuse.

## Implementation

Poll Vault `/v1/sys/health` via scripted input every minute. Parse sealed, standby, version, replication_performance_mode. Forward to Splunk via HEC. Enable Vault audit log; forward audit events for token creation and auth attempts. Alert immediately when sealed==true. Track token creation rate; alert on anomalies. Correlate unseal events with operator actions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (Vault API, audit log).
• Ensure the following data sources are available: Vault `/v1/sys/health`, `/v1/sys/audit`, audit log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll Vault `/v1/sys/health` via scripted input every minute. Parse sealed, standby, version, replication_performance_mode. Forward to Splunk via HEC. Enable Vault audit log; forward audit events for token creation and auth attempts. Alert immediately when sealed==true. Track token creation rate; alert on anomalies. Correlate unseal events with operator actions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vault sourcetype="vault:health"
| where sealed==true
| table _time, host, sealed, standby, version
```

Understanding this SPL

**HashiCorp Vault Seal Status and Token Count** — Vault health, auto-unseal events, and token creation rate indicate secrets management availability. Sealed Vault blocks all secret access; token anomalies may indicate abuse.

Documented **Data sources**: Vault `/v1/sys/health`, `/v1/sys/audit`, audit log. **App/TA** (typical add-on context): Custom (Vault API, audit log). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vault; **sourcetype**: vault:health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vault, sourcetype="vault:health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where sealed==true` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **HashiCorp Vault Seal Status and Token Count**): table _time, host, sealed, standby, version


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (sealed status — target: false), Table (Vault cluster health), Line chart (token creation rate), Timeline (unseal events).

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
index=vault sourcetype="vault:health"
| where sealed==true
| table _time, host, sealed, standby, version
```

## Visualization

Single value (sealed status — target: false), Table (Vault cluster health), Line chart (token creation rate), Timeline (unseal events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
