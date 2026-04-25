<!-- AUTO-GENERATED from UC-1.4.11.json — DO NOT EDIT -->

---
id: "1.4.11"
title: "Boot Order and UEFI/BIOS Configuration Drift"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.4.11 · Boot Order and UEFI/BIOS Configuration Drift

## Description

Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.

## Value

If someone or something changes which disk or network path the server boots from, you can catch it before the next reboot leaves a system stuck at a wrong image or a surprise installer.

## Implementation

Use vendor APIs or scripts to export boot order and Secure Boot state. Compare to a lookup of expected configuration. Alert on drift. Run after changes or daily.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (Redfish, iDRAC, iLO, or `dmidecode` where that is sufficient).
• Ensure the following data sources are available: `dmidecode -t bios` (Linux) and out-of-band boot-order exports from the BMC.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux, `dmidecode` can backfill basic firmware info, but out-of-band boot order and Secure Boot are usually from Redfish, racadm, or the vendor’s REST API. Ingest a single `boot_order` string per `host` and a `lookup` of `expected_order` and optional `expected_secure_boot`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; fix `inputlookup` pattern to your lookup shape):

```spl
index=hardware sourcetype=boot_config host=*
| stats latest(boot_order) as current_order, latest(secure_boot) as secure_boot by host
| inputlookup expected_boot_config append=t
| eval match=if('current_order'='expected_order', "Match", "Drift")
| where match="Drift"
| table host current_order expected_order secure_boot
```

Production use usually joins on `host` to the lookup with `| lookup` instead of a broad `append`—adjust to your data.

Understanding this SPL

**Boot Order and UEFI/BIOS Configuration Drift** — Unauthorized or accidental boot order changes can prevent systems from booting from the correct disk or PXE. Tracking supports change audit and recovery.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=boot_config`.
• `stats` keeps the latest `boot_order` and `secure_boot` per **host**.
• The lookup and `match` test detect drift; `table` lists offenders.


Step 3 — Validate
After a change window, read boot order in the out-of-band UI and align the lookup. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=boot_config host=*
| stats latest(boot_order) as current_order, latest(secure_boot) as secure_boot by host
| inputlookup expected_boot_config append=t
| eval match=if('current_order'='expected_order', "Match", "Drift")
| where match="Drift"
| table host current_order expected_order secure_boot
```

## CIM SPL

```spl
N/A — boot order and secure-boot state are not a CIM data model; use a custom `boot_config` sourcetype and a lookup of approved settings.
```

## Visualization

Table (host, current vs. expected boot order), Compliance percentage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
