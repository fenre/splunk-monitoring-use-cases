<!-- AUTO-GENERATED from UC-5.13.31.json — DO NOT EDIT -->

---
id: "5.13.31"
title: "Compliance by Rule/Policy Category"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.13.31 · Compliance by Rule/Policy Category

## Description

Breaks down non-compliance by policy rule category to identify which compliance areas (running config, image, PSIRT, etc.) have the most violations.

## Value

Not all compliance violations are equal. Breaking down by rule category reveals whether the problem is configuration drift, outdated images, or unpatched vulnerabilities.

## Implementation

Enable the `compliance` input. If `complianceType` is nested, use `spath` or field aliases from the TA so category names appear consistently.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538) with the **compliance** modular input writing sourcetype `cisco:dnac:compliance` to `index=catalyst`.
• Service account: **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** (or the roles your Cisco TA documents for compliance Intent API read access); verify the controller virtual domain/scope includes the sites you expect.
• Field names and nesting for `complianceType` and `complianceStatus` can vary by Catalyst Center release—sample one **raw** JSON event and confirm the TA extraction before building dashboards.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md` for install paths, index sizing, and credential handling.

Step 1 — Configure data collection
• **Intent API (typical):** device compliance results as exposed in your TA version; the add-on normalises to `cisco:dnac:compliance`.
• **TA input:** **compliance**; confirm the destination **index** and **sourcetype** match this UC (`cisco:dnac:compliance`).
• **Poll interval:** follow the Cisco TA default (often 15–60 minutes); tighter intervals mean fresher `NON_COMPLIANT` counts but more API load.
• **Key fields to validate in Search:** `complianceType`, `complianceStatus` (`COMPLIANT` / `NON_COMPLIANT` or your build’s values), `deviceName`.
• If `complianceType` is nested in JSON, add **field extractions** or `spath` in your knowledge objects so category names are stable in panels.

Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violations dc(deviceName) as affected_devices by complianceType | sort -violations
```

Understanding this SPL (what the alert condition really is)
**Compliance by Rule/Policy Category** — Ranks *which classes* of policy fail most, not *which* single device to fix first (use `UC-5.13.33` for row-level detail).
• The filter on `complianceStatus="NON_COMPLIANT"` is intentional: passing devices are excluded so the bar chart is actionable.
• `dc(deviceName)` is an **approximate** count of impacted devices; if the TA emits multiple rows per device per poll, deduplicate in a stricter panel (`latest` by key) before trusting exact headcount.
• Sort `-violations` orders the noisiest **complianceType** first for program-level prioritisation (image/PSIRT/config families).

**Pipeline walkthrough**
• Non-compliant rows only → `stats` of violation **events** and **distinct** hostnames by category → **sort** for executive or engineering review.

Step 3 — Validate (completeness vs Catalyst Center)
• In Catalyst **Network Assurance / Compliance** (wording varies by version), open the same site scope and compare the top **categories** to this chart within one poll window.
• In Splunk: `| tstats count WHERE index=catalyst sourcetype="cisco:dnac:compliance" by complianceType` to confirm all expected **types** (running-config, image, etc.) appear.
• `| timechart count` on the sourcetype to catch silent **ingest gaps** (zero events across hours).

Step 4 — Operationalize
• **Dashboard:** bar of **violations** by `complianceType` with a drilldown to a **detail** search (`deviceName` list) and link to the Catalyst **device** or **compliance** view.
• **Change correlation:** add a `notes` or **ITSM** lookup for scheduled policy pushes; spike the panel after approved changes to avoid false escalations from expected waves of `NON_COMPLIANT` results.
• **Access:** `deviceName` and policy text can be sensitive—restrict the app or dashboard to **NetEng / SecOps** roles.

Step 5 — Troubleshooting
• **No `cisco:dnac:compliance` data:** re-enable the **compliance** input, verify the **Catalyst** base URL, credentials, and **role**; scan `splunkd.log` for REST **403/5xx** from the input worker.
• **Empty or odd `complianceType`:** inspect **raw** JSON; add **EXTRACT** or `spath` until `by complianceType` is populated.
• **Count explosion:** duplicate **poll** rows—use `| stats ... by complianceType, deviceName` in a stricter view or add **dedup** keyed on a TA-provided `lastUpdated` field if present.
• **Mismatch vs UI:** check **Catalyst** site/scope, **RMA** renames, and **stale** inventory; Splunk can only reflect what the **Intent API** returned on the last successful poll.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violations dc(deviceName) as affected_devices by complianceType | sort -violations
```

## Visualization

Bar chart (violations by complianceType), table with affected device counts.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
