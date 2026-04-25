<!-- AUTO-GENERATED from UC-2.6.16.json — DO NOT EDIT -->

---
id: "2.6.16"
title: "Citrix Cloud Connector Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.16 · Citrix Cloud Connector Health

## Description

For Citrix DaaS (cloud-managed) deployments, Cloud Connectors are the link between on-premises resources and Citrix Cloud. If all Cloud Connectors in a resource location fail, the site enters Local Host Cache (LHC) mode with limited functionality — no new machine registrations, no power management, and no access to cloud-hosted services. Monitoring connector health ensures continuous cloud management connectivity.

## Value

For Citrix DaaS (cloud-managed) deployments, Cloud Connectors are the link between on-premises resources and Citrix Cloud. If all Cloud Connectors in a resource location fail, the site enters Local Host Cache (LHC) mode with limited functionality — no new machine registrations, no power management, and no access to cloud-hosted services. Monitoring connector health ensures continuous cloud management connectivity.

## Implementation

Deploy a Splunk Universal Forwarder on Cloud Connector hosts and monitor Windows Event Logs for Citrix Cloud Connector events. Also run the Cloud Health Check utility via scheduled PowerShell scripted input to validate connectivity to Citrix Cloud services. Track connectivity status (Connected, Disconnected), service health, and last successful cloud contact time. Alert when: any connector loses cloud connectivity for more than 15 minutes, all connectors in a resource location become disconnected (LHC mode imminent), or Cloud Connector services stop. Ensure at least 2 connectors per resource location for redundancy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on Cloud Connector hosts.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:cloudconnector"` fields `connector_host`, `connectivity_status`, `last_contact`, `service_status`, `resource_location`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on Cloud Connector hosts and monitor Windows Event Logs for Citrix Cloud Connector events. Also run the Cloud Health Check utility via scheduled PowerShell scripted input to validate connectivity to Citrix Cloud services. Track connectivity status (Connected, Disconnected), service health, and last successful cloud contact time. Alert when: any connector loses cloud connectivity for more than 15 minutes, all connectors in a resource location become disconnecte…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:cloudconnector"
| stats latest(connectivity_status) as cloud_status, latest(service_status) as svc_status, latest(_time) as last_seen by connector_host, resource_location
| eval hours_since_contact=round((now()-last_seen)/3600, 1)
| where cloud_status!="Connected" OR svc_status!="Running" OR hours_since_contact > 1
| table connector_host, resource_location, cloud_status, svc_status, hours_since_contact
```

Understanding this SPL

**Citrix Cloud Connector Health** — For Citrix DaaS (cloud-managed) deployments, Cloud Connectors are the link between on-premises resources and Citrix Cloud. If all Cloud Connectors in a resource location fail, the site enters Local Host Cache (LHC) mode with limited functionality — no new machine registrations, no power management, and no access to cloud-hosted services. Monitoring connector health ensures continuous cloud management connectivity.

Documented **Data sources**: `index=xd` `sourcetype="citrix:cloudconnector"` fields `connector_host`, `connectivity_status`, `last_contact`, `service_status`, `resource_location`. **App/TA** (typical add-on context): Splunk Universal Forwarder on Cloud Connector hosts. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:cloudconnector. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:cloudconnector". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by connector_host, resource_location** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hours_since_contact** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cloud_status!="Connected" OR svc_status!="Running" OR hours_since_contact > 1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Cloud Connector Health**): table connector_host, resource_location, cloud_status, svc_status, hours_since_contact

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (connector x resource location), Timeline (connectivity events), Single value (connected connectors count).

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
index=xd sourcetype="citrix:cloudconnector"
| stats latest(connectivity_status) as cloud_status, latest(service_status) as svc_status, latest(_time) as last_seen by connector_host, resource_location
| eval hours_since_contact=round((now()-last_seen)/3600, 1)
| where cloud_status!="Connected" OR svc_status!="Running" OR hours_since_contact > 1
| table connector_host, resource_location, cloud_status, svc_status, hours_since_contact
```

## Visualization

Status grid (connector x resource location), Timeline (connectivity events), Single value (connected connectors count).

## References

- [uberAgent indexer app](https://splunkbase.splunk.com/app/2998)
- [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448)
