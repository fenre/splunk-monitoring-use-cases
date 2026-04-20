---
id: "1.1.17"
title: "Service Availability Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.1.17 · Service Availability Monitoring

## Description

Detects stopped services before users notice. Essential for any SLA-bound service where uptime matters.

## Value

Detects stopped services before users notice. Essential for any SLA-bound service where uptime matters.

## Implementation

Create a scripted input that checks key service statuses: `systemctl is-active httpd sshd mysqld | paste - - -`. Run every 60 seconds. Alert immediately when critical services stop. Maintain a lookup of expected services per host role.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`systemctl is-active <service>`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that checks key service statuses: `systemctl is-active httpd sshd mysqld | paste - - -`. Run every 60 seconds. Alert immediately when critical services stop. Maintain a lookup of expected services per host role.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=service_status host=*
| stats latest(status) as status by host, service_name
| where status != "active"
| table host service_name status
```

Understanding this SPL

**Service Availability Monitoring** — Detects stopped services before users notice. Essential for any SLA-bound service where uptime matters.

Documented **Data sources**: Custom scripted input (`systemctl is-active <service>`). **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: service_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=service_status. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where status != "active"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Service Availability Monitoring**): table host service_name status


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator panels (green/red per service), Table of down services, Icon grid.

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
index=os sourcetype=service_status host=*
| stats latest(status) as status by host, service_name
| where status != "active"
| table host service_name status
```

## Visualization

Status indicator panels (green/red per service), Table of down services, Icon grid.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
