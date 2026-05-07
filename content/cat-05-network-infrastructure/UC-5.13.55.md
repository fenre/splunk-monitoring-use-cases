<!-- AUTO-GENERATED from UC-5.13.55.json — DO NOT EDIT -->

---
id: "5.13.55"
title: "Software Image Inventory and Version Summary"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.55 · Software Image Inventory and Version Summary

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Inventory, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep track of which software version every network device is running — like knowing which phones have the latest update and which are behind. This tells your team which devices need to be upgraded and how many different versions are out there, because the more versions you have, the harder it is to keep everything secure and working properly.*

---

## Description

Provides a complete inventory of firmware versions running across the managed device fleet, grouped by hardware platform — the starting point for firmware compliance assessment, upgrade planning, and vulnerability exposure analysis that feeds UC-5.13.56 (Firmware Non-Compliance) and UC-5.13.34–39 (PSIRT advisories).

## Value

You cannot plan a firmware campaign without knowing what's running today. This UC answers: 'How many device families do we have? What versions are they running? How fragmented is our firmware landscape?' A fleet running 15 different IOS-XE versions across 5 platform families is a maintenance nightmare — each version needs separate testing, different PSIRTs apply, and troubleshooting varies by version. Consolidating toward 2–3 standardised versions per platform reduces operational complexity, narrows the PSIRT exposure surface, and simplifies TAC support. The inventory also feeds UC-5.13.59 (End-of-Life Detection) by showing which versions are approaching or past their support lifecycle.

## Implementation

Enable the `device` inventory input (Inputs → Create → Device Inventory: account `catcenter-prod`, index `catalyst`, interval `3600`). The `softwareVersion` and `platformId` fields are in every device event. Schedule weekly for the firmware management review.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) installed on Search Heads AND Heavy Forwarder.
- The `device` inventory input provides firmware version data. This is separate from the `devicehealth` input (UC-5.13.1) — it polls a different API endpoint that returns detailed device metadata including `softwareVersion`.
- Service account with **NETWORK-ADMIN-ROLE** for device inventory access.

### Step 1 — Configure data collection
Enable the `device` inventory input:

| Setting | Value |
|---------|-------|
| Input type | Device Inventory |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `3600` (hourly — device metadata changes slowly) |

The TA polls `GET /dna/intent/api/v1/network-device`. Each managed device produces one JSON event with detailed metadata including `softwareVersion`, `platformId`, `hostname`, `managementIpAddress`, `deviceFamily`, `upTime`, and more.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:device" earliest=-2h
| stats dc(hostname) as devices, dc(softwareVersion) as versions, dc(platformId) as platforms
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:device"
| stats dc(hostname) as device_count by platformId, softwareVersion
| sort platformId, softwareVersion
```

Why `by platformId, softwareVersion`: groups devices by hardware platform AND firmware version. This produces the firmware matrix that operations and security teams need for upgrade planning.

Why `dc(hostname)` not `count`: deduplicates across poll cycles.

For a firmware fragmentation metric:
```spl
index=catalyst sourcetype="cisco:dnac:device"
| stats dc(softwareVersion) as version_count by platformId
| eval fragmentation=case(version_count=1, "Standardised", version_count<=3, "Managed", 1==1, "Fragmented (".version_count." versions)")
| sort -version_count
```

For firmware change tracking (detect upgrades):
```spl
index=catalyst sourcetype="cisco:dnac:device" earliest=-7d
| stats earliest(softwareVersion) as old_version latest(softwareVersion) as new_version by hostname
| where old_version != new_version
| table hostname, old_version, new_version
```

Schedule: weekly (cron `0 7 * * 1`), output to PDF for the firmware management review.

### Step 3 — Validate
(a) Compare total device count with UC-5.13.1. They should match (same device fleet, different sourcetype).
(b) Pick a specific device and verify its `softwareVersion` matches `show version` on the device CLI.
(c) Compare the firmware matrix with **Catalyst Center > Provision > Inventory** sorted by platform and version.
(d) Check for version string normalisation issues: `| stats dc(softwareVersion) | where dc > 20`. If > 20 unique versions, some may be formatting variants.
(e) Vendor UI parity: compare the platform/version distribution with **Catalyst Center > SWIM > Image Summary**.

### Step 4 — Operationalize
- Firmware management dashboard: firmware matrix as the lead panel.
- Fragmentation metric: target ≤ 3 versions per platform family.
- Upgrade planning: identify the largest device_count rows running old versions as the priority targets.
- Track firmware changes week-over-week to monitor upgrade campaign progress.
- Cross-reference with UC-5.13.34–39 (PSIRT) to identify which versions are affected by active advisories.

Runbook (owner: Network Engineering / Firmware Management):
1. Review the weekly firmware matrix.
2. For each platform with > 3 active versions: plan a consolidation campaign.
3. Identify the golden image version per platform in **Catalyst Center > SWIM > Golden Image**.
4. Count devices NOT on the golden image (UC-5.13.56).
5. Schedule upgrade campaigns for the largest non-compliant populations first.

### Step 5 — Troubleshooting

- **No `cisco:dnac:device` events** — the `device` inventory input is not enabled. Check TA → Inputs. This is a separate input from `devicehealth`.

- **`softwareVersion` is null** — some device types (older models, third-party) may not report firmware version via the API. Check `| stats count(eval(isnull(softwareVersion))) as null_version, count as total`.

- **Version strings have inconsistent formatting** — normalise with regex: `| rex field=softwareVersion "(?P<normalized>\d+\.\d+\.\d+)"`.

- **AP firmware not matching WLC firmware** — expected. APs and WLCs have independent firmware lifecycles.

- **Device count per version doesn't sum to total fleet** — some devices may have null version (excluded from the `by softwareVersion` grouping). Add `| eval softwareVersion=coalesce(softwareVersion, "UNKNOWN")`.

- **Firmware change detection shows false positives** — the `earliest`/`latest` approach may compare across data gaps. Use `streamstats` for more precise version-change detection.

- **Too many versions for meaningful analysis** — focus on the top platforms by device count first. Fragmented niche platforms with 2–3 devices are lower priority.

- **Want to map versions to PSIRT exposure** — join with UC-5.13.37 (Devices Affected by Advisory) to see which advisory exposure correlates with which version.

Additional operational context for Software Image Inventory and Version Summary:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:device"
| stats dc(hostname) as device_count by platformId, softwareVersion
| sort platformId, softwareVersion
```

## Visualization

(1) Table: platformId, softwareVersion, device_count — sorted by platform for a consolidated firmware matrix. (2) Bar chart: device_count by softwareVersion within each platform family. (3) Single values: total unique firmware versions (fragmentation metric), total platforms. (4) Pie: version distribution per platform family (trellis by platformId).

## Known False Positives

**Same firmware version reported with different formatting.** Some devices report `17.9.4a` while others report `17.09.04a` or `Amsterdam-17.9.4a`. These are the same version but appear as separate rows. Distinguish by normalising version strings: `| rex field=softwareVersion "(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)"`. Suppress by using the normalised version for grouping.

**Devices running custom or engineering images.** Lab devices or early-adopter devices running engineering builds have non-standard version strings. Distinguish by checking the version format. Present these separately from production versions.

**Firmware version changes after upgrade but before inventory refresh.** After a firmware upgrade, the device reports the new version immediately, but the Catalyst Center inventory may take one poll cycle (1 hour) to reflect the change. During this window, the old and new versions may both appear for the same device. Suppress by using `latest(softwareVersion)` per device.

**AP firmware versions differing from WLC version.** APs run their own firmware that may differ from the WLC firmware. The device inventory shows the AP firmware, not the WLC firmware. This is expected — AP and WLC firmware are managed independently.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Network Device endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-device-list)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco IOS-XE Release Notes and Lifecycle](https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-17/products-release-notes-list.html)
