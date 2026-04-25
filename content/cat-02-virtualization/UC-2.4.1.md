<!-- AUTO-GENERATED from UC-2.4.1.json — DO NOT EDIT -->

---
id: "2.4.1"
title: "Guest OS End-of-Life Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.4.1 · Guest OS End-of-Life Tracking

## Description

VMs running end-of-life operating systems no longer receive security patches, creating unmitigated vulnerabilities. Tracking guest OS versions across all hypervisors against vendor EOL dates enables proactive migration planning before support ends. Required for PCI DSS, HIPAA, and SOC 2 compliance.

## Value

VMs running end-of-life operating systems no longer receive security patches, creating unmitigated vulnerabilities. Tracking guest OS versions across all hypervisors against vendor EOL dates enables proactive migration planning before support ends. Required for PCI DSS, HIPAA, and SOC 2 compliance.

## Implementation

Collect guest OS information from all hypervisor platforms. Maintain a lookup table (`os_eol_dates.csv`) mapping OS names to vendor EOL dates (Microsoft, Red Hat, Canonical, etc.). Alert at 180 days before EOL (planning), 90 days (action required), and on any VM running an already-EOL OS. Generate quarterly reports for management.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, `Splunk_TA_windows`, custom OS inventory.
• Ensure the following data sources are available: VM inventory from all hypervisors, OS EOL lookup table.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect guest OS information from all hypervisor platforms. Maintain a lookup table (`os_eol_dates.csv`) mapping OS names to vendor EOL dates (Microsoft, Red Hat, Canonical, etc.). Alert at 180 days before EOL (planning), 90 days (action required), and on any VM running an already-EOL OS. Generate quarterly reports for management.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(guest_os) as os_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" | stats latest(os_name) as os_name by vm_name]
| append [search index=virtualization sourcetype=kvm_guest_agent | stats latest(os_name) as os_name by vm_name]
| lookup os_eol_dates os_name OUTPUT eol_date, eol_status
| eval days_to_eol=round((strptime(eol_date, "%Y-%m-%d") - now()) / 86400, 0)
| where days_to_eol < 180 OR eol_status="EOL"
| sort days_to_eol
| table vm_name, os_name, eol_date, days_to_eol, eol_status
```

Understanding this SPL

**Guest OS End-of-Life Tracking** — VMs running end-of-life operating systems no longer receive security patches, creating unmitigated vulnerabilities. Tracking guest OS versions across all hypervisors against vendor EOL dates enables proactive migration planning before support ends. Required for PCI DSS, HIPAA, and SOC 2 compliance.

Documented **Data sources**: VM inventory from all hypervisors, OS EOL lookup table. **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`, custom OS inventory. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name** so each row reflects one combination of those dimensions.
• Appends rows from a subsearch with `append`.
• Appends rows from a subsearch with `append`.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **days_to_eol** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_eol < 180 OR eol_status="EOL"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Guest OS End-of-Life Tracking**): table vm_name, os_name, eol_date, days_to_eol, eol_status

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, OS, EOL date), Bar chart (VMs by EOL status), Timeline (upcoming EOL dates).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(guest_os) as os_name by vm_name
| append [search index=hyperv sourcetype="hyperv_vm_config" | stats latest(os_name) as os_name by vm_name]
| append [search index=virtualization sourcetype=kvm_guest_agent | stats latest(os_name) as os_name by vm_name]
| lookup os_eol_dates os_name OUTPUT eol_date, eol_status
| eval days_to_eol=round((strptime(eol_date, "%Y-%m-%d") - now()) / 86400, 0)
| where days_to_eol < 180 OR eol_status="EOL"
| sort days_to_eol
| table vm_name, os_name, eol_date, days_to_eol, eol_status
```

## Visualization

Table (VM, OS, EOL date), Bar chart (VMs by EOL status), Timeline (upcoming EOL dates).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
