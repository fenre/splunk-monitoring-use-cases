<!-- AUTO-GENERATED from UC-9.4.20.json — DO NOT EDIT -->

---
id: "9.4.20"
title: "PAM Agent Health Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.20 · PAM Agent Health Monitoring

## Description

CPM, PSM, and PVWA agents offline block rotation and session capture; distinct from vault binary health (UC-9.4.6).

## Value

CPM, PSM, and PVWA agents offline block rotation and session capture; distinct from vault binary health (UC-9.4.6).

## Implementation

Agents send heartbeat every 60s. Alert if no heartbeat >5 minutes. Auto-ticket remediation for PSM in production zones.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CyberArk component monitoring, SNMP/HEARTBEAT logs.
• Ensure the following data sources are available: Agent heartbeat, service status, `Get-PMPServerHealth`-style scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Agents send heartbeat every 60s. Alert if no heartbeat >5 minutes. Auto-ticket remediation for PSM in production zones.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:agent_heartbeat"
| stats latest(_time) as last_hb by agent_type, hostname
| eval secs_since=now()-last_hb
| where secs_since > 300
| table agent_type, hostname, secs_since
```

Understanding this SPL

**PAM Agent Health Monitoring** — CPM, PSM, and PVWA agents offline block rotation and session capture; distinct from vault binary health (UC-9.4.6).

Documented **Data sources**: Agent heartbeat, service status, `Get-PMPServerHealth`-style scripted input. **App/TA** (typical add-on context): CyberArk component monitoring, SNMP/HEARTBEAT logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:agent_heartbeat. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:agent_heartbeat". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by agent_type, hostname** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **secs_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where secs_since > 300` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **PAM Agent Health Monitoring**): table agent_type, hostname, secs_since


Step 3 — Validate
Compare with CyberArk PrivateArk/Password Vault Web Access (or BeyondTrust / vendor console) for the same sessions, vault activity, and alerts.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (agent × host), Single value (unhealthy agents), Line chart (heartbeat age).

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
index=pam sourcetype="cyberark:agent_heartbeat"
| stats latest(_time) as last_hb by agent_type, hostname
| eval secs_since=now()-last_hb
| where secs_since > 300
| table agent_type, hostname, secs_since
```

## Visualization

Status grid (agent × host), Single value (unhealthy agents), Line chart (heartbeat age).

## References

- [Cisco Security Cloud](https://splunkbase.splunk.com/app/7404)
