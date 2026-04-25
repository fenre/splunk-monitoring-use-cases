<!-- AUTO-GENERATED from UC-2.6.50.json — DO NOT EDIT -->

---
id: "2.6.50"
title: "VDA BSOD and Machine Stability Tracking"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.50 · VDA BSOD and Machine Stability Tracking

## Description

Blue screens, hard hangs, and unexpected reboots on session hosts are disproportionately disruptive: many users and published apps can fail in one incident. A single bugcheck may be a driver or GPU edge case; a cluster of the same stop code in one catalog points to a bad image, firmware, or policy rollout. You need a unified stream that captures bugcheck parameters from the System log, correlates with Citrix VDA and agent state when available, and enriches with uberAgent reboot analytics so you can trend stability per catalog, per hardware generation, and after every monthly patch. Treat recurring hosts as a candidate for maintenance mode and root-cause with vendor tools.

## Value

Blue screens, hard hangs, and unexpected reboots on session hosts are disproportionately disruptive: many users and published apps can fail in one incident. A single bugcheck may be a driver or GPU edge case; a cluster of the same stop code in one catalog points to a bad image, firmware, or policy rollout. You need a unified stream that captures bugcheck parameters from the System log, correlates with Citrix VDA and agent state when available, and enriches with uberAgent reboot analytics so you can trend stability per catalog, per hardware generation, and after every monthly patch. Treat recurring hosts as a candidate for maintenance mode and root-cause with vendor tools.

## Implementation

Ingest the full System channel from all session hosts. For bugcheck 1001, parse `Message` to extract the stop code. Join `host` to a CMDB or lookup that supplies `catalog_name` and `delivery_group`. In uberAgent, confirm unexpected reboots flow with the same `host` key. Alert when any host has more than one bugcheck in seven days, or when a new stop code appears in more than 10% of a catalog in a week. Exclude planned reboot windows via a change lookup. For GPU images, add NVIDIA or AMD field extractions in a child search.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows on all session hosts; uberAgent; optional VDA log feed.
• Ensure the following data sources are available: `WinEventLog:System` with 1001, 41, 6008, and 1074 where applicable; `index=uberagent` boot and stability; optional `index=xd` `citrix:vda:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Standardize time zones. Map `host` to asset inventory. Truncate or mask kernel dumps paths in `Message` if sensitive. If `append` is heavy, materialize a summary index on a 15-minute schedule instead of real-time for wide fleets.

Step 2 — Create the search and alert
Simplify the primary SPL in production — the example is illustrative. A typical pattern is:

```spl
index=windows sourcetype="WinEventLog:System" EventCode=1001
| eval stop_code=if(match(_raw, "(0x[A-Fa-f0-9]{8})"), mvindex( match(_raw, "(0x[A-Fa-f0-9]{8})" ),1), null())
| stats count by host, stop_code
| where count>0
```

**VDA BSOD and Machine Stability Tracking** — Union with `index=uberagent` unexpected reboots on `host` in a `join` or `append` and deduplicate the same second.

Step 3 — Validate
Induce a controlled bugcheck in a non-production pool if policy allows, or use historical data from a known patch regression. Check that 41 and 1001 do not double count the same event.

Step 4 — Operationalize
Send weekly top-stop-code review to the desktop engineering team, attach to image lifecycle gates, and block promotion when stability KPIs regress.

## SPL

```spl
index=windows sourcetype="WinEventLog:System" (EventCode=1001 OR EventCode=41 OR EventCode=6008)
| rex field=Message max_match=0 "(?<bugcheck>0x[0-9A-Fa-f]+)"
| append [ search index=uberagent sourcetype="uberAgent:Machine:Boot" unexpected_reboot=1 | eval EventCode=9999 | eval host=coalesce(host, dest_host) ]
| bin _time span=1d
| stats count as instabilities, values(EventCode) as event_codes, values(bugcheck) as stop_codes by host, _time
| where instabilities>0
| sort - instabilities
| table _time, host, instabilities, event_codes, stop_codes
```

## Visualization

Choropleth of stability rate by data center, bar chart of top stop codes, timeline of restarts, table of worst hosts with catalog and patch level.

## References

- [Windows bug check reference (Microsoft Learn)](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2)
- [uberAgent unexpected reboots](https://docs.uberagent.com/)
