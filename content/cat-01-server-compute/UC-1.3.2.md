<!-- AUTO-GENERATED from UC-1.3.2.json — DO NOT EDIT -->

---
id: "1.3.2"
title: "FileVault Encryption Status"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.3.2 · FileVault Encryption Status

## Description

Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).

## Value

Finding laptops that are not using full-disk encryption lets you close a gap before a lost device turns into a reportable data exposure rather than a hardware replacement.

## Implementation

Create a scripted input: `fdesetup status`. Run daily. Alert on any endpoint where FileVault is not enabled. Feed into compliance dashboard.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`fdesetup status`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
On each Mac, run `fdesetup status` on a schedule and forward a single line or key=value event per host. Map the `status` field to what your **where** clause expects (the example assumes the literal `FileVault is On.` for compliant).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_filevault host=*
| stats latest(status) as fv_status by host
| where fv_status!="FileVault is On."
```

Understanding this SPL

**FileVault Encryption Status** — Unencrypted endpoints are a data breach risk if lost or stolen. Compliance requirement for most security frameworks (SOC2, ISO27001, PCI).

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_filevault`.
• `stats` keeps the latest `fv_status` per **host**.
• `where` flags hosts that are not in the “on” state for your string match.


Step 3 — Validate
On a test Mac, run `fdesetup status` and compare the indexed `status` to the event. Verify index permissions and that compliance dashboards use the same string.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Document exceptions (for example kiosks) in your runbook. Consider visualizations: Pie chart (encrypted vs. not), Table of non-compliant hosts, Single value (compliance %).

For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=macos_filevault host=*
| stats latest(status) as fv_status by host
| where fv_status!="FileVault is On."
```

## CIM SPL

```spl
N/A — full-disk encryption status is not a standard Common Information Model field; use a custom inventory or compliance sourcetype (for example from `fdesetup status`).
```

## Visualization

Pie chart (encrypted vs. not), Table of non-compliant hosts, Single value (compliance %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
