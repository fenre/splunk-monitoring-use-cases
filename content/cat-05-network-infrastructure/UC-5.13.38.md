<!-- AUTO-GENERATED from UC-5.13.38.json — DO NOT EDIT -->

---
id: "5.13.38"
title: "Advisory Remediation Progress Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.38 · Advisory Remediation Progress Tracking

## Description

Tracks the remediation progress of security advisories over time by comparing current affected device counts against historical baselines.

## Value

Vulnerability remediation is a process, not a one-time event. Tracking progress demonstrates active management and identifies stalled remediation efforts.

## Implementation

Enable the `securityadvisory` input. `appendcols` requires aligned `advisoryId` order between the two `stats` outputs; for production, consider a `join` on `advisoryId` or `lookup` of precomputed baselines. Validate that subsearch time bounds cover representative weeks.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with `cisco:dnac:securityadvisory` in `index=catalyst`.
• For production, prefer `| join type=left advisoryId` (or a KVStore baseline from two scheduled searches) instead of `appendcols`, because `appendcols` only lines up by **row number** and can pair the wrong `advisoryId` with the wrong `previous_affected` when sort order differs.
• “Current” uses the user’s time range; the inline subsearch uses a fixed **baseline** of `earliest=-30d latest=-7d`—tune to your change cadence.
• `docs/implementation-guide.md`.

Step 1 — Prototype in lab
• Run the main and baseline `stats` alone; confirm both return the **same** `advisoryId` set and order before trusting `appendcols`.

Step 2 — Remediation % (stalled work)
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(deviceId) as current_affected by advisoryId, severity, advisoryTitle | appendcols [search index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-30d latest=-7d | stats dc(deviceId) as previous_affected by advisoryId] | eval remediation_pct=if(previous_affected>0, round((previous_affected-current_affected)*100/previous_affected,1), "N/A") | where current_affected > 0 | sort severity -current_affected
```

Understanding this SPL
**Advisory Remediation Progress** — Percent change in distinct affected `deviceId` between windows. Inventory shrink (RMA, decommission, site removed from Catalyst) can reduce `current_affected` without a single IOS upgrade, so do not use this as proof of patch alone; pair with change tickets and SWIM or fixed-version fields from Cisco where available.

**Pipeline walkthrough**
• `stats` for current `dc(deviceId)` by `advisoryId` + baseline subsearch for `previous_affected` → `remediation_pct` → keep rows still open (`current_affected > 0`).

Step 3 — Validate
• For one `advisoryId`, hand-check current vs previous counts; if the percentage does not match simple arithmetic, switch to an explicit `join` on `advisoryId`.
• Reconcile to Catalyst’s PSIRT view of remaining affected where the UI exposes it.

Step 4 — Operationalize
• Export monthly for GRC; flag advisories with low `remediation_pct` for multiple consecutive months as “stalled” in the vulnerability queue.

Step 5 — Troubleshooting
• **N/A** for `remediation_pct`: new advisory in current window (no `previous_affected` in baseline) or baseline subsearch had no data—widen the baseline or accept N/A for brand-new items.
• **Optimistic % after inventory cleanup:** document on the dashboard that `deviceId` count drops can reflect **scope** change, not only patching.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(deviceId) as current_affected by advisoryId, severity, advisoryTitle | appendcols [search index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-30d latest=-7d | stats dc(deviceId) as previous_affected by advisoryId] | eval remediation_pct=if(previous_affected>0, round((previous_affected-current_affected)*100/previous_affected,1), "N/A") | where current_affected > 0 | sort severity -current_affected
```

## Visualization

Table (advisoryId, severity, current_affected, previous_affected, remediation_pct), column chart of remediation_pct.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
