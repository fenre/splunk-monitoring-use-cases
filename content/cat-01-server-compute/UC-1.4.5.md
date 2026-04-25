<!-- AUTO-GENERATED from UC-1.4.5.json — DO NOT EDIT -->

---
id: "1.4.5"
title: "Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.4.5 · Firmware Version Compliance

## Description

Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.

## Value

A single list of which boxes still run old system or out-of-band firmware makes patch and risk conversations concrete instead of sampling a few serial numbers by hand.

## Implementation

Create scripted input: `ipmitool mc info` or `dmidecode -t bios`. Run daily. Maintain a lookup table of expected firmware versions per server model. Dashboard showing compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`, `dmidecode`), vendor APIs.
• Ensure the following data sources are available: BMC/BIOS version data via scripted input.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux, run `ipmitool mc info` and `dmidecode -t bios` (or Redfish) on a schedule; parse `bios_version` and `bmc_version` and `model`. Populate `current_firmware` lookup with `expected_bios` and `expected_bmc` per `model`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust as needed):

```spl
index=hardware sourcetype=firmware_inventory
| stats latest(bios_version) as bios, latest(bmc_version) as bmc by host, model
| lookup current_firmware model OUTPUT expected_bios, expected_bmc
| eval bios_current = if(bios=expected_bios, "Yes", "No")
| where bios_current="No"
```

Extend with a similar `bmc` check if required.

Understanding this SPL

**Firmware Version Compliance** — Outdated firmware may have security vulnerabilities or known bugs. Fleet-wide firmware tracking supports patch management.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=firmware_inventory`.
• `stats` and `lookup` join live versions to `expected_*` from policy.
• `where` shows hosts out of policy on BIOS in this example.


Step 3 — Validate
Hand-check a few hosts against the vendor or DCIM UI. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=firmware_inventory
| stats latest(bios_version) as bios, latest(bmc_version) as bmc by host, model
| lookup current_firmware model OUTPUT expected_bios, expected_bmc
| eval bios_current = if(bios=expected_bios, "Yes", "No")
| where bios_current="No"
```

## CIM SPL

```spl
N/A — BIOS and BMC version strings are not a standard CIM compliance view; use a lookup of approved firmware per `model` with your own inventory sourcetype.
```

## Visualization

Table (host, model, current vs. expected), Pie chart (compliant %), Bar chart by model.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
