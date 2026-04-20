---
id: "4.2.54"
title: "Azure Bastion Session Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.54 · Azure Bastion Session Audit

## Description

Bastion provides secure, auditable VM access without public IPs. Monitoring session activity ensures compliance with access policies and detects unauthorized connection attempts.

## Value

Bastion provides secure, auditable VM access without public IPs. Monitoring session activity ensures compliance with access policies and detects unauthorized connection attempts.

## Implementation

Enable diagnostic logging on Azure Bastion to send audit logs via Event Hub. Track user sessions by `userName`, `targetVMIPAddress`, `protocol` (SSH/RDP), and `duration`. Alert on connections to unexpected VMs, connections from unusual IP addresses, and failed authentication attempts. Correlate with Entra ID sign-in logs for identity context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:diagnostics` (BastionAuditLogs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostic logging on Azure Bastion to send audit logs via Event Hub. Track user sessions by `userName`, `targetVMIPAddress`, `protocol` (SSH/RDP), and `duration`. Alert on connections to unexpected VMs, connections from unusual IP addresses, and failed authentication attempts. Correlate with Entra ID sign-in logs for identity context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="BastionAuditLogs"
| stats count as sessions, dc(targetVMIPAddress) as unique_targets by userName, clientIpAddress
| sort -sessions
```

Understanding this SPL

**Azure Bastion Session Audit** — Bastion provides secure, auditable VM access without public IPs. Monitoring session activity ensures compliance with access policies and detects unauthorized connection attempts.

Documented **Data sources**: `sourcetype=azure:diagnostics` (BastionAuditLogs). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by userName, clientIpAddress** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

Understanding this CIM / accelerated SPL

**Azure Bastion Session Audit** — Bastion provides secure, auditable VM access without public IPs. Monitoring session activity ensures compliance with access policies and detects unauthorized connection attempts.

Documented **Data sources**: `sourcetype=azure:diagnostics` (BastionAuditLogs). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (sessions by user and target), Bar chart (sessions by protocol), Line chart (session count over time).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="BastionAuditLogs"
| stats count as sessions, dc(targetVMIPAddress) as unique_targets by userName, clientIpAddress
| sort -sessions
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

## Visualization

Table (sessions by user and target), Bar chart (sessions by protocol), Line chart (session count over time).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
