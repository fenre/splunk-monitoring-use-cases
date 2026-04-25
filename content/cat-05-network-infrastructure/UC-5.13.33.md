<!-- AUTO-GENERATED from UC-5.13.33.json — DO NOT EDIT -->

---
id: "5.13.33"
title: "Compliance Violation Detail Drill-Down"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.33 · Compliance Violation Detail Drill-Down

## Description

Provides detailed violation-level information for non-compliant devices, including the specific rule violated, the violation message, and suggested remediation actions.

## Value

Operations teams need actionable detail to remediate violations. This drill-down provides the specific violation and recommended fix for each non-compliant device.

## Implementation

Enable the `compliance` input. Confirm the TA normalises `violations` (JSON or multivalue) as expected. Adjust `spath` paths if the payload structure differs in your version.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with **compliance** → `cisco:dnac:compliance` in `index=catalyst`.
• One **raw** `NON_COMPLIANT` event in hand: confirm the JSON path to **`violations`** (array of objects, depth, and field names for `violationType` / `remediationAction`).
• **Performance:** `mvexpand` can be heavy at scale—**limit** the time range or pre-filter to a **site** or **complianceType** in busy estates.
• `docs/implementation-guide.md` for app layout and any performance notes on the compliance input.

Step 1 — Configure data collection
• If the built-in `spath` in this sample does not match your payload, replace `path=violations{}` with the correct `spath` or **KV** extraction; keep **field** names **consistent** in `props` so dashboards do not break on upgrade.

Step 2 — Create the search and table
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | spath output=violations path=violations{} | mvexpand violations | spath input=violations | table deviceName complianceType violationType violationMessage remediationAction | sort deviceName complianceType
```

Understanding this SPL (operator drilldown)
**Violation detail** — This is a **row-per-finding** view for **remediation** tickets, not a **fleet health** score (see `UC-5.13.31` for roll-ups).
• If `violationType` is empty, your inner `spath` may need a different sub-path—use **Job Inspector** in Search on one **mvexpand**d row to debug.

**Pipeline walkthrough**
• `NON_COMPLIANT` only → `spath` **violations** array → `mvexpand` to individual findings → `spath` inner fields → **table** for export to **Excel** or **ITSM**.

Step 3 — Validate
• Pick a device in **Catalyst** **Compliance** detail and line up **message** and **remediation** text to one Splunk **row**.
• `| where isnotnull(violationMessage) | head 1` in **Verbose** to confirm multiline text is not truncated by **LINE_BREAKER** settings.

Step 4 — Operationalize
• **Dashboard:** two-step drill—start from **bar** by `complianceType` (`UC-5.13.31`), token drill to this **detail** search filtered on `complianceType` and **site**.
• **Export:** `outputcsv` for bulk ticket creation; **redact** hostnames for **untrusted** tickets.

Step 5 — Troubleshooting
• **Empty table after mvexpand:** the **violations** path is wrong, or the TA flattened violations into **separate** events already—simplify the SPL to `| table violations` first.
• **Exploding row counts:** one API row per rule **per** rule check—**dedup** on `deviceName+violationType+_time` if the TA re-sends the same string every **poll**.
• **No data:** follow **compliance** input and **Catalyst** **role** steps from `UC-5.13.31` troubleshooting.
• **Catalyst** shows a finding Splunk does not: **time range** and **virtual domain** do not include that site, or the device **left** inventory mid-window.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | spath output=violations path=violations{} | mvexpand violations | spath input=violations | table deviceName complianceType violationType violationMessage remediationAction | sort deviceName complianceType
```

## Visualization

Table (deviceName, complianceType, violationType, violationMessage, remediationAction) with drilldowns.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
