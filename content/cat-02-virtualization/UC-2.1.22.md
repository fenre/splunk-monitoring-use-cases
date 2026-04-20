---
id: "2.1.22"
title: "vCenter Service Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.1.22 · vCenter Service Health

## Description

vCenter is the management plane for the entire VMware environment. If VPXD, SSO, or the content library service fails, you lose visibility into your VMs and cannot perform management operations. Monitoring vCenter appliance health ensures the control plane is operational.

## Value

vCenter is the management plane for the entire VMware environment. If VPXD, SSO, or the content library service fails, you lose visibility into your VMs and cannot perform management operations. Monitoring vCenter appliance health ensures the control plane is operational.

## Implementation

Forward vCenter appliance syslog to Splunk. Monitor VPXD, STS (SSO), content library, and PostgreSQL logs. Also create a scripted input to poll the VAMI health API (`https://vcsa:5480/rest/applmgmt/health`). Alert when any service reports unhealthy status. Monitor vCenter disk space (database growth).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, vCenter syslog.
• Ensure the following data sources are available: `sourcetype=vmware:events`, vCenter VAMI health API, vCenter syslog (`/var/log/vmware/vpxd/vpxd.log`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward vCenter appliance syslog to Splunk. Monitor VPXD, STS (SSO), content library, and PostgreSQL logs. Also create a scripted input to poll the VAMI health API (`https://vcsa:5480/rest/applmgmt/health`). Alert when any service reports unhealthy status. Monitor vCenter disk space (database growth).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="syslog" source="/var/log/vmware/vpxd/*" ("ERROR" OR "CRITICAL" OR "FATAL")
| stats count as errors by host, source
| where errors > 10
| sort -errors
| table host, source, errors
```

Understanding this SPL

**vCenter Service Health** — vCenter is the management plane for the entire VMware environment. If VPXD, SSO, or the content library service fails, you lose visibility into your VMs and cannot perform management operations. Monitoring vCenter appliance health ensures the control plane is operational.

Documented **Data sources**: `sourcetype=vmware:events`, vCenter VAMI health API, vCenter syslog (`/var/log/vmware/vpxd/vpxd.log`). **App/TA** (typical add-on context): `Splunk_TA_vmware`, vCenter syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, source** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where errors > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **vCenter Service Health**): table host, source, errors


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (service health), Line chart (error rate over time), Table (recent errors).

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
index=vmware sourcetype="syslog" source="/var/log/vmware/vpxd/*" ("ERROR" OR "CRITICAL" OR "FATAL")
| stats count as errors by host, source
| where errors > 10
| sort -errors
| table host, source, errors
```

## Visualization

Status grid (service health), Line chart (error rate over time), Table (recent errors).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
