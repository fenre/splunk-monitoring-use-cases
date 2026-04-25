<!-- AUTO-GENERATED from UC-1.4.8.json — DO NOT EDIT -->

---
id: "1.4.8"
title: "PCIe Link Width and Speed Degradation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.4.8 · PCIe Link Width and Speed Degradation

## Description

PCIe links that downgrade (e.g. x16→x8) indicate slot or cable issues. Affects GPU, NVMe, and HBA performance and can precede full failure.

## Value

A slot that trained narrower or slower than designed hurts throughput for GPUs, NVMe, and HBAs, and is often a sign of a bad connection long before a device disappears entirely.

## Implementation

Parse `lspci -vv` for "LnkCap" and "LnkSta" or read sysfs. Run daily. Maintain lookup of expected width/speed per host and slot. Alert on downgrade.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`lspci -vv` and sysfs on Linux; vendor inventory scripts elsewhere).
• Ensure the following data sources are available: `lspci -vv`, `/sys/bus/pci/devices/*/current_link_width_speed` (Linux typical).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On Linux, parse `lspci -vv` for LnkCap/LnkSta and/or read sysfs for current link width and speed per device. On non-Linux hosts, use the vendor’s PCI reporting tool to emit the same `link_width` and `link_speed` fields. Populate the `pcie_expected` lookup with per-host, per-slot expectations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust as needed):

```spl
index=hardware sourcetype=pcie_link host=*
| stats latest(link_width) as width, latest(link_speed) as speed by host, slot
| lookup pcie_expected host slot OUTPUT expected_width expected_speed
| where width < expected_width OR speed < expected_speed
| table host slot width speed expected_width expected_speed
```

Understanding this SPL

**PCIe Link Width and Speed Degradation** — PCIe links that downgrade (e.g. x16→x8) indicate slot or cable issues. Affects GPU, NVMe, and HBA performance and can precede full failure.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=pcie_link`.
• `stats` and `lookup` compare current width/speed to `expected_*` from policy.


Step 3 — Validate
On a test host, compare `lspci -vv` to indexed fields. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=pcie_link host=*
| stats latest(link_width) as width, latest(link_speed) as speed by host, slot
| lookup pcie_expected host slot OUTPUT expected_width expected_speed
| where width < expected_width OR speed < expected_speed
| table host slot width speed expected_width expected_speed
```

## CIM SPL

```spl
N/A — PCIe link training width/speed is not a CIM data model; use Linux `lspci`/`sysfs` output or vendor-specific inventory in a custom sourcetype.
```

## Visualization

Table (host, slot, current vs. expected), Bar chart of link widths.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
