---
id: "2.1.33"
title: "ESXi Host Lockdown Mode Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.1.33 · ESXi Host Lockdown Mode Compliance

## Description

Lockdown mode restricts direct ESXi access, forcing all management through vCenter. Hosts not in lockdown mode can be accessed directly via SSH or the DCUI, bypassing vCenter audit trails and RBAC. Required by security frameworks like CIS, DISA STIG, and PCI DSS.

## Value

Lockdown mode restricts direct ESXi access, forcing all management through vCenter. Hosts not in lockdown mode can be accessed directly via SSH or the DCUI, bypassing vCenter audit trails and RBAC. Required by security frameworks like CIS, DISA STIG, and PCI DSS.

## Implementation

Collect host inventory via Splunk_TA_vmware. Define expected lockdown mode per cluster (lockdownNormal or lockdownStrict). Alert when any production host has lockdown disabled or SSH enabled outside a maintenance window. Generate weekly compliance reports for security audits.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:hostsystem`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect host inventory via Splunk_TA_vmware. Define expected lockdown mode per cluster (lockdownNormal or lockdownStrict). Alert when any production host has lockdown disabled or SSH enabled outside a maintenance window. Generate weekly compliance reports for security audits.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(lockdownMode) as lockdown, latest(sshEnabled) as ssh by host, cluster
| where lockdown!="lockdownNormal" OR ssh="true"
| table host, cluster, lockdown, ssh
```

Understanding this SPL

**ESXi Host Lockdown Mode Compliance** — Lockdown mode restricts direct ESXi access, forcing all management through vCenter. Hosts not in lockdown mode can be accessed directly via SSH or the DCUI, bypassing vCenter audit trails and RBAC. Required by security frameworks like CIS, DISA STIG, and PCI DSS.

Documented **Data sources**: `sourcetype=vmware:inv:hostsystem`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:hostsystem. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:hostsystem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cluster** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where lockdown!="lockdownNormal" OR ssh="true"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ESXi Host Lockdown Mode Compliance**): table host, cluster, lockdown, ssh


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (lockdown compliance), Table (non-compliant hosts), Pie chart (compliance rate).

## SPL

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(lockdownMode) as lockdown, latest(sshEnabled) as ssh by host, cluster
| where lockdown!="lockdownNormal" OR ssh="true"
| table host, cluster, lockdown, ssh
```

## Visualization

Status grid (lockdown compliance), Table (non-compliant hosts), Pie chart (compliance rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
