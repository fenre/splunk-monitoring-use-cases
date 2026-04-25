<!-- AUTO-GENERATED from UC-2.1.36.json — DO NOT EDIT -->

---
id: "2.1.36"
title: "VM Encryption and vTPM Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.1.36 · VM Encryption and vTPM Compliance

## Description

VM encryption protects data at rest on shared storage. vTPM enables Credential Guard, BitLocker, and measured boot inside VMs. Compliance frameworks increasingly require encryption for workloads handling sensitive data. Tracking which VMs are encrypted vs. which should be ensures policy adherence.

## Value

VM encryption protects data at rest on shared storage. vTPM enables Credential Guard, BitLocker, and measured boot inside VMs. Compliance frameworks increasingly require encryption for workloads handling sensitive data. Tracking which VMs are encrypted vs. which should be ensures policy adherence.

## Implementation

Collect VM inventory via Splunk_TA_vmware. Maintain a lookup defining which VMs require encryption (based on data classification). Cross-reference inventory with the requirements lookup. Alert when a VM that should be encrypted is not. Generate quarterly compliance reports for audit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect VM inventory via Splunk_TA_vmware. Maintain a lookup defining which VMs require encryption (based on data classification). Cross-reference inventory with the requirements lookup. Alert when a VM that should be encrypted is not. Generate quarterly compliance reports for audit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(cryptoState) as encryption, latest(vtpm_present) as vtpm by vm_name, host, guest_os
| eval encrypted=if(encryption="encrypted", "Yes", "No")
| eval has_vtpm=if(vtpm_present="true", "Yes", "No")
| table vm_name, host, guest_os, encrypted, has_vtpm
| sort encrypted, has_vtpm
```

Understanding this SPL

**VM Encryption and vTPM Compliance** — VM encryption protects data at rest on shared storage. vTPM enables Credential Guard, BitLocker, and measured boot inside VMs. Compliance frameworks increasingly require encryption for workloads handling sensitive data. Tracking which VMs are encrypted vs. which should be ensures policy adherence.

Documented **Data sources**: `sourcetype=vmware:inv:vm`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host, guest_os** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **encrypted** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **has_vtpm** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **VM Encryption and vTPM Compliance**): table vm_name, host, guest_os, encrypted, has_vtpm
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM encryption status), Pie chart (encrypted vs not), Bar chart (compliance by department).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| stats latest(cryptoState) as encryption, latest(vtpm_present) as vtpm by vm_name, host, guest_os
| eval encrypted=if(encryption="encrypted", "Yes", "No")
| eval has_vtpm=if(vtpm_present="true", "Yes", "No")
| table vm_name, host, guest_os, encrypted, has_vtpm
| sort encrypted, has_vtpm
```

## Visualization

Table (VM encryption status), Pie chart (encrypted vs not), Bar chart (compliance by department).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
