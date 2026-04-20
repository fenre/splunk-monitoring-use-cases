---
id: "2.1.37"
title: "VM Template Inventory and Staleness"
criticality: "low"
splunkPillar: "Observability"
---

# UC-2.1.37 · VM Template Inventory and Staleness

## Description

Stale VM templates with outdated OS patches, expired certificates, or old application versions get deployed into production and immediately become vulnerable. Tracking template age and last update ensures new VMs start from a secure, current baseline.

## Value

Stale VM templates with outdated OS patches, expired certificates, or old application versions get deployed into production and immediately become vulnerable. Tracking template age and last update ensures new VMs start from a secure, current baseline.

## Implementation

Collect VM inventory via Splunk_TA_vmware (templates appear as VMs with isTemplate=true). Flag templates older than 30 days as needing refresh. Alert on templates older than 90 days. Track deployment frequency per template to identify popular templates that should be prioritized for updates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm` (templates are VMs with isTemplate=true).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect VM inventory via Splunk_TA_vmware (templates appear as VMs with isTemplate=true). Flag templates older than 30 days as needing refresh. Alert on templates older than 90 days. Track deployment frequency per template to identify popular templates that should be prioritized for updates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" isTemplate="true"
| eval age_days=round((now() - strptime(modifiedTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| sort -age_days
| table vm_name, guest_os, hw_version, age_days, modifiedTime
```

Understanding this SPL

**VM Template Inventory and Staleness** — Stale VM templates with outdated OS patches, expired certificates, or old application versions get deployed into production and immediately become vulnerable. Tracking template age and last update ensures new VMs start from a secure, current baseline.

Documented **Data sources**: `sourcetype=vmware:inv:vm` (templates are VMs with isTemplate=true). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Template Inventory and Staleness**): table vm_name, guest_os, hw_version, age_days, modifiedTime


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (template, OS, age), Bar chart (templates by age bucket), Single value (templates >90 days).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" isTemplate="true"
| eval age_days=round((now() - strptime(modifiedTime, "%Y-%m-%dT%H:%M:%S")) / 86400, 0)
| sort -age_days
| table vm_name, guest_os, hw_version, age_days, modifiedTime
```

## Visualization

Table (template, OS, age), Bar chart (templates by age bucket), Single value (templates >90 days).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
