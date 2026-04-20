---
id: "2.6.11"
title: "Citrix License Server Utilization and Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.11 · Citrix License Server Utilization and Compliance

## Description

Citrix licensing is capacity-based — concurrent user/device licenses or per-user/per-device named licenses. Approaching license limits during peak hours causes session launch failures with "no licenses available" errors. While Citrix provides a grace period, operating within grace period indicates a compliance gap. Trending license utilization supports procurement planning and ensures continuous service availability.

## Value

Citrix licensing is capacity-based — concurrent user/device licenses or per-user/per-device named licenses. Approaching license limits during peak hours causes session launch failures with "no licenses available" errors. While Citrix provides a grace period, operating within grace period indicates a compliance gap. Trending license utilization supports procurement planning and ensures continuous service availability.

## Implementation

Create a PowerShell scripted input on the Citrix License Server that queries license usage via `Get-LicInventory` and `Get-LicUsage` cmdlets or the Citrix Licensing WMI provider. Collect total licenses, in-use count, available count, grace period status, and license expiration dates. Run every 15 minutes. Alert at 80% utilization (capacity planning), 90% (operational warning), and immediately if grace period becomes active. Also alert 90 days before license expiration. Track peak utilization by hour and day of week for procurement planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on License Server, PowerShell scripted input.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:licensing"` fields `license_type`, `in_use`, `total`, `available`, `grace_period_active`, `expiration_date`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a PowerShell scripted input on the Citrix License Server that queries license usage via `Get-LicInventory` and `Get-LicUsage` cmdlets or the Citrix Licensing WMI provider. Collect total licenses, in-use count, available count, grace period status, and license expiration dates. Run every 15 minutes. Alert at 80% utilization (capacity planning), 90% (operational warning), and immediately if grace period becomes active. Also alert 90 days before license expiration. Track peak utilization by …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:licensing"
| stats latest(in_use) as used, latest(total) as total, latest(available) as available, latest(grace_period_active) as grace, latest(expiration_date) as expiry by license_type
| eval utilization_pct=round(used/total*100,1)
| eval days_to_expiry=round((strptime(expiry, "%Y-%m-%d")-now())/86400,0)
| where utilization_pct > 80 OR grace="true" OR days_to_expiry < 90
| table license_type, used, total, available, utilization_pct, grace, days_to_expiry
```

Understanding this SPL

**Citrix License Server Utilization and Compliance** — Citrix licensing is capacity-based — concurrent user/device licenses or per-user/per-device named licenses. Approaching license limits during peak hours causes session launch failures with "no licenses available" errors. While Citrix provides a grace period, operating within grace period indicates a compliance gap. Trending license utilization supports procurement planning and ensures continuous service availability.

Documented **Data sources**: `index=xd` `sourcetype="citrix:licensing"` fields `license_type`, `in_use`, `total`, `available`, `grace_period_active`, `expiration_date`. **App/TA** (typical add-on context): Splunk Universal Forwarder on License Server, PowerShell scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:licensing. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:licensing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by license_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **utilization_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **days_to_expiry** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where utilization_pct > 80 OR grace="true" OR days_to_expiry < 90` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix License Server Utilization and Compliance**): table license_type, used, total, available, utilization_pct, grace, days_to_expiry


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (license utilization %), Timechart (license usage over time), Table (license types with expiry dates).

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
index=xd sourcetype="citrix:licensing"
| stats latest(in_use) as used, latest(total) as total, latest(available) as available, latest(grace_period_active) as grace, latest(expiration_date) as expiry by license_type
| eval utilization_pct=round(used/total*100,1)
| eval days_to_expiry=round((strptime(expiry, "%Y-%m-%d")-now())/86400,0)
| where utilization_pct > 80 OR grace="true" OR days_to_expiry < 90
| table license_type, used, total, available, utilization_pct, grace, days_to_expiry
```

## Visualization

Gauge (license utilization %), Timechart (license usage over time), Table (license types with expiry dates).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
