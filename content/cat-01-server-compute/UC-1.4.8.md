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

PCIe links that downgrade (e.g. x16→x8) indicate slot or cable issues. Affects GPU, NVMe, and HBA performance and can precede full failure.

## Implementation

Parse `lspci -vv` for "LnkCap" and "LnkSta" or read sysfs. Run daily. Maintain lookup of expected width/speed per host and slot. Alert on downgrade.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`lspci -vv` or Windows PCI query).
• Ensure the following data sources are available: `lspci -vv`, `/sys/bus/pci/devices/*/current_link_width_speed`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse `lspci -vv` for "LnkCap" and "LnkSta" or read sysfs. Run daily. Maintain lookup of expected width/speed per host and slot. Alert on downgrade.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=pcie_link host=*
| stats latest(link_width) as width, latest(link_speed) as speed by host, slot
| lookup pcie_expected host slot OUTPUT expected_width expected_speed
| where width < expected_width OR speed < expected_speed
| table host slot width speed expected_width expected_speed
```

Understanding this SPL

**PCIe Link Width and Speed Degradation** — PCIe links that downgrade (e.g. x16→x8) indicate slot or cable issues. Affects GPU, NVMe, and HBA performance and can precede full failure.

Documented **Data sources**: `lspci -vv`, `/sys/bus/pci/devices/*/current_link_width_speed`. **App/TA** (typical add-on context): Custom scripted input (`lspci -vv` or Windows PCI query). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: pcie_link. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=pcie_link. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, slot** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where width < expected_width OR speed < expected_speed` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **PCIe Link Width and Speed Degradation**): table host slot width speed expected_width expected_speed


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, slot, current vs. expected), Bar chart of link widths.

## SPL

```spl
index=hardware sourcetype=pcie_link host=*
| stats latest(link_width) as width, latest(link_speed) as speed by host, slot
| lookup pcie_expected host slot OUTPUT expected_width expected_speed
| where width < expected_width OR speed < expected_speed
| table host slot width speed expected_width expected_speed
```

## Visualization

Table (host, slot, current vs. expected), Bar chart of link widths.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
