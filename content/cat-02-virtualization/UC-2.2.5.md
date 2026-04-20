---
id: "2.2.5"
title: "Integration Services Version"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.2.5 · Integration Services Version

## Description

Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.

## Value

Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.

## Implementation

Replace `"latest"` in the SPL with the actual expected integration services version. Create a PowerShell scripted input on Hyper-V hosts: `Get-VM | Get-VMIntegrationService | Select VMName, Name, Enabled, PrimaryOperationalStatus`. Run daily.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V), custom scripted input.
• Ensure the following data sources are available: PowerShell scripted input (`Get-VMIntegrationService`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Replace `"latest"` in the SPL with the actual expected integration services version. Create a PowerShell scripted input on Hyper-V hosts: `Get-VM | Get-VMIntegrationService | Select VMName, Name, Enabled, PrimaryOperationalStatus`. Run daily.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hyperv sourcetype=integration_services
| stats latest(version) as ic_version by vm_name, host
| where ic_version != "latest"
```

Understanding this SPL

**Integration Services Version** — Outdated integration services cause performance issues and prevent features like time sync, heartbeat, and data exchange from working correctly.

Documented **Data sources**: PowerShell scripted input (`Get-VMIntegrationService`). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V), custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hyperv; **sourcetype**: integration_services. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hyperv, sourcetype=integration_services. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ic_version != "latest"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, version, status), Pie chart (current vs. outdated).

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
index=hyperv sourcetype=integration_services
| stats latest(version) as ic_version by vm_name, host
| where ic_version != "latest"
```

## Visualization

Table (VM, version, status), Pie chart (current vs. outdated).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
