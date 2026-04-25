<!-- AUTO-GENERATED from UC-1.3.4.json — DO NOT EDIT -->

---
id: "1.3.4"
title: "Software Update Compliance"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.3.4 · Software Update Compliance

## Description

Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.

## Value

A single view of which Macs are on an approved (or too-old) build makes patch and vulnerability work measurable instead of guessing from occasional spot checks.

## Implementation

Scripted input for `sw_vers` (weekly) and `softwareupdate -l` (daily). Track OS versions and pending updates. Alert when critical security updates are pending >7 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (`softwareupdate -l`, `sw_vers`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted input for `sw_vers` (weekly) and `softwareupdate -l` (daily). Track OS versions and pending updates. Alert when critical security updates are pending longer than your policy allows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_sw_vers host=*
| stats latest(ProductVersion) as os_version by host
| eval is_current = if(os_version >= "14.3", "Yes", "No")
| stats count by is_current
```

Replace the `14.3` string with a lookup or a field from your own policy. Use `| inputlookup` for approved versions per model if the fleet is mixed.

Understanding this SPL

**Software Update Compliance** — Unpatched macOS endpoints are vulnerable. Tracking update levels across the fleet supports vulnerability management.

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_sw_vers`.
• `stats` takes the latest `os_version` per **host**.
• `eval` labels current vs. not against your example threshold.
• Final `stats` gives fleet counts for reporting (not a per-host alert as written—split into a per-host form if alerting).


Step 3 — Validate
On a test Mac, compare `sw_vers -productVersion` to the indexed `ProductVersion`. Verify index permissions and time zones for daily rollups.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Document your minimum supported version. Consider visualizations: Table (host, OS version, pending updates), Pie chart (version distribution). See the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=macos_sw_vers host=*
| stats latest(ProductVersion) as os_version by host
| eval is_current = if(os_version >= "14.3", "Yes", "No")
| stats count by is_current
```

## CIM SPL

```spl
N/A — macOS `ProductVersion` from inventory is not a CIM Performance field; use MDM, custom `sw_vers` data, or your own policy lookup for approved builds.
```

## Visualization

Table (host, OS version, pending updates), Pie chart (version distribution).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
