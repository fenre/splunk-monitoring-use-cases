<!-- AUTO-GENERATED from UC-9.4.6.json — DO NOT EDIT -->

---
id: "9.4.6"
title: "Vault Health Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.6 · Vault Health Monitoring

## Description

PAM vault downtime prevents all privileged access, blocking critical operations. Health monitoring ensures continuous availability.

## Value

PAM vault downtime prevents all privileged access, blocking critical operations. Health monitoring ensures continuous availability.

## Implementation

Monitor PAM vault components (vault server, PVWA, PSM, CPM). Track service availability, replication between primary/DR vault, and component health. Alert on any component failure or replication lag >5 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: PAM infrastructure monitoring, SNMP.
• Ensure the following data sources are available: PAM vault system logs, component health APIs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor PAM vault components (vault server, PVWA, PSM, CPM). Track service availability, replication between primary/DR vault, and component health. Alert on any component failure or replication lag >5 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:vault_health"
| stats latest(status) as status, latest(replication_lag) as lag by vault_server, component
| where status!="Running" OR lag > 300
```

Understanding this SPL

**Vault Health Monitoring** — PAM vault downtime prevents all privileged access, blocking critical operations. Health monitoring ensures continuous availability.

Documented **Data sources**: PAM vault system logs, component health APIs. **App/TA** (typical add-on context): PAM infrastructure monitoring, SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:vault_health. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:vault_health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vault_server, component** so each row reflects one combination of those dimensions.
• Filters the current rows with `where status!="Running" OR lag > 300` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with CyberArk PrivateArk/Password Vault Web Access (or BeyondTrust / vendor console) for the same sessions, vault activity, and alerts.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (component × health), Single value (vault uptime %), Table (unhealthy components), Line chart (replication lag).

## SPL

```spl
index=pam sourcetype="cyberark:vault_health"
| stats latest(status) as status, latest(replication_lag) as lag by vault_server, component
| where status!="Running" OR lag > 300
```

## Visualization

Status grid (component × health), Single value (vault uptime %), Table (unhealthy components), Line chart (replication lag).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
