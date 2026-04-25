<!-- AUTO-GENERATED from UC-1.3.6.json — DO NOT EDIT -->

---
id: "1.3.6"
title: "macOS Gatekeeper and XProtect Status"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.3.6 · macOS Gatekeeper and XProtect Status

## Description

Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.

## Value

Old malware definitions and turned-off download checks leave users exposed to the same class of file-based threats your policy assumes are blocked; this use case makes that gap visible in one place.

## Implementation

Create a scripted input that runs `spctl --status` (expect "assessments enabled" for Gatekeeper on). For XProtect, run `system_profiler SPInstallHistoryDataType` and parse XProtect/XProtect Remediator entries, or check `/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/version.plist`. Run daily. Alert when Gatekeeper is disabled; alert when XProtect definitions are older than 30 days.

## Detailed Implementation

Prerequisites
• Install the Universal Forwarder on the Mac; place scripts in an app or `deployment-apps` as you do for other custom inputs.
• Data sources: `spctl --status`, and XProtect version/date from `system_profiler` or the XProtect `version.plist` (your parser must set `xprotect_date` in the format the search expects).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs `spctl --status` and collects XProtect metadata. The sample search expects fields `xprotect_date`, and optionally `xprotect_ver` for the table. Run daily. Do not rely on Windows or Linux performance counters (no Perfmon, no `/proc` load) — this is macOS-only.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust the 30-day window as needed):

```spl
index=os sourcetype=macos_gatekeeper host=*
| eval xprotect_age_days = now() - strptime(xprotect_date, "%Y-%m-%d")
| where xprotect_age_days > 30
| table host xprotect_ver xprotect_date xprotect_age_days
```

Add a second alert for Gatekeeper if you parse `spctl` into the same or a companion sourcetype.

Understanding this SPL

**macOS Gatekeeper and XProtect Status** — Verify Gatekeeper and XProtect are enabled and definitions are current. Disabled or outdated security controls increase malware risk.

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_gatekeeper`.
• `eval` turns `xprotect_date` into `xprotect_age_days`.
• `where` flags definitions older than 30 days; `table` shows detail for remediation.


Step 3 — Validate
Compare `xprotect_date` in Search to `system_profiler` and Apple’s current release notes for your build. For full details, see the Implementation guide: docs/implementation-guide.md

Step 4 — Operationalize
Document how often Apple ships definition updates in your environment and tune the 30-day threshold. Consider visualizations: Table (host, status, XProtect version), count of non-compliant hosts.

## SPL

```spl
index=os sourcetype=macos_gatekeeper host=*
| eval xprotect_age_days = now() - strptime(xprotect_date, "%Y-%m-%d")
| where xprotect_age_days > 30
| table host xprotect_ver xprotect_date xprotect_age_days
```

## CIM SPL

```spl
N/A — XProtect and Gatekeeper state are not CIM data model fields; the add-on for Unix and Linux is commonly used for Linux host metrics, but this Apple-specific inventory remains a custom sourcetype unless you build your own mapping.
```

## Visualization

Table (host, Gatekeeper status, XProtect version), Single value (non-compliant count), Pie chart (enabled vs. disabled).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
