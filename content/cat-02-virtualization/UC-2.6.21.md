<!-- AUTO-GENERATED from UC-2.6.21.json — DO NOT EDIT -->

---
id: "2.6.21"
title: "Machine Boot and Shutdown Duration Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.21 · Machine Boot and Shutdown Duration Analysis

## Description

VDA boot time directly impacts how quickly machines become available after power-on events triggered by Citrix power management schedules. Slow boots delay session availability for early-morning users. uberAgent decomposes boot duration into phases (BIOS/firmware, kernel, drivers, services, boot processes) to identify bottlenecks — antivirus scans at boot, slow driver initialisation, or disk contention during mass power-on.

## Value

VDA boot time directly impacts how quickly machines become available after power-on events triggered by Citrix power management schedules. Slow boots delay session availability for early-morning users. uberAgent decomposes boot duration into phases (BIOS/firmware, kernel, drivers, services, boot processes) to identify bottlenecks — antivirus scans at boot, slow driver initialisation, or disk contention during mass power-on.

## Implementation

uberAgent captures boot duration automatically on all endpoints. Correlate boot times with Citrix power management schedules (UC-2.6.6) to validate machines are ready when users arrive. Alert on VDAs with p95 boot time exceeding 2 minutes. Use boot process detail data to identify specific services or drivers causing delays.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgent:OnOffTransition:BootDetail2"`, `sourcetype="uberAgent:OnOffTransition:BootProcessDetail"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent captures boot duration automatically on all endpoints. Correlate boot times with Citrix power management schedules (UC-2.6.6) to validate machines are ready when users arrive. Alert on VDAs with p95 boot time exceeding 2 minutes. Use boot process detail data to identify specific services or drivers causing delays.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:OnOffTransition:BootDetail2" earliest=-7d
| stats avg(TotalBootTimeMs) as avg_boot_ms perc95(TotalBootTimeMs) as p95_boot_ms count as boots by Host
| eval avg_boot_sec=round(avg_boot_ms/1000,1), p95_boot_sec=round(p95_boot_ms/1000,1)
| where p95_boot_sec > 120
| sort -p95_boot_sec
| table Host, boots, avg_boot_sec, p95_boot_sec
```

Understanding this SPL

**Machine Boot and Shutdown Duration Analysis** — VDA boot time directly impacts how quickly machines become available after power-on events triggered by Citrix power management schedules. Slow boots delay session availability for early-morning users. uberAgent decomposes boot duration into phases (BIOS/firmware, kernel, drivers, services, boot processes) to identify bottlenecks — antivirus scans at boot, slow driver initialisation, or disk contention during mass power-on.

Documented **Data sources**: `sourcetype="uberAgent:OnOffTransition:BootDetail2"`, `sourcetype="uberAgent:OnOffTransition:BootProcessDetail"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:OnOffTransition:BootDetail2. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:OnOffTransition:BootDetail2", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_boot_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where p95_boot_sec > 120` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Machine Boot and Shutdown Duration Analysis**): table Host, boots, avg_boot_sec, p95_boot_sec

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (boot time by VDA), Stacked bar (boot phases), Line chart (boot time trending).

## SPL

```spl
index=uberagent sourcetype="uberAgent:OnOffTransition:BootDetail2" earliest=-7d
| stats avg(TotalBootTimeMs) as avg_boot_ms perc95(TotalBootTimeMs) as p95_boot_ms count as boots by Host
| eval avg_boot_sec=round(avg_boot_ms/1000,1), p95_boot_sec=round(p95_boot_ms/1000,1)
| where p95_boot_sec > 120
| sort -p95_boot_sec
| table Host, boots, avg_boot_sec, p95_boot_sec
```

## Visualization

Bar chart (boot time by VDA), Stacked bar (boot phases), Line chart (boot time trending).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
