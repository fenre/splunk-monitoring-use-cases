---
id: "2.2.12"
title: "VM Generation and Secure Boot Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.2.12 · VM Generation and Secure Boot Compliance

## Description

Generation 1 VMs use legacy BIOS and cannot support Secure Boot, vTPM, or UEFI features required by modern security policies. Generation 2 VMs with Secure Boot enabled prevent rootkits and bootkits from loading unauthorized firmware or OS loaders.

## Value

Generation 1 VMs use legacy BIOS and cannot support Secure Boot, vTPM, or UEFI features required by modern security policies. Generation 2 VMs with Secure Boot enabled prevent rootkits and bootkits from loading unauthorized firmware or OS loaders.

## Implementation

Create scripted input: `Get-VM | Select Name, Generation, @{N='SecureBoot';E={(Get-VMFirmware $_).SecureBoot}}`. Run daily. Define compliance policy — all new VMs should be Gen 2 with Secure Boot enabled. Generate weekly compliance reports. Note: Gen 1 → Gen 2 migration requires VM rebuild.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V), custom scripted input.
• Ensure the following data sources are available: PowerShell scripted input (`Get-VM`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input: `Get-VM | Select Name, Generation, @{N='SecureBoot';E={(Get-VMFirmware $_).SecureBoot}}`. Run daily. Define compliance policy — all new VMs should be Gen 2 with Secure Boot enabled. Generate weekly compliance reports. Note: Gen 1 → Gen 2 migration requires VM rebuild.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hyperv sourcetype="hyperv_vm_config"
| stats latest(generation) as gen, latest(secure_boot) as secure_boot by vm_name, host
| eval compliant=if(gen=2 AND secure_boot="On", "Yes", "No")
| where compliant="No"
| table vm_name, host, gen, secure_boot, compliant
| sort gen
```

Understanding this SPL

**VM Generation and Secure Boot Compliance** — Generation 1 VMs use legacy BIOS and cannot support Secure Boot, vTPM, or UEFI features required by modern security policies. Generation 2 VMs with Secure Boot enabled prevent rootkits and bootkits from loading unauthorized firmware or OS loaders.

Documented **Data sources**: PowerShell scripted input (`Get-VM`). **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V), custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hyperv; **sourcetype**: hyperv_vm_config. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hyperv, sourcetype="hyperv_vm_config". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where compliant="No"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **VM Generation and Secure Boot Compliance**): table vm_name, host, gen, secure_boot, compliant
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (Gen 1 vs Gen 2), Table (non-compliant VMs), Bar chart (by host).

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
index=hyperv sourcetype="hyperv_vm_config"
| stats latest(generation) as gen, latest(secure_boot) as secure_boot by vm_name, host
| eval compliant=if(gen=2 AND secure_boot="On", "Yes", "No")
| where compliant="No"
| table vm_name, host, gen, secure_boot, compliant
| sort gen
```

## Visualization

Pie chart (Gen 1 vs Gen 2), Table (non-compliant VMs), Bar chart (by host).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
