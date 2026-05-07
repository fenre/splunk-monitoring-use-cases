<!-- AUTO-GENERATED from UC-5.13.33.json — DO NOT EDIT -->

---
id: "5.13.33"
title: "Compliance Violation Detail Drill-Down"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.33 · Compliance Violation Detail Drill-Down

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We give your team the exact details of what is wrong with each non-compliant device and what to do to fix it — not just 'this device has a problem' but 'this device is missing this specific setting, and here is how to add it.' That way fixes happen faster because nobody has to look up the instructions separately.*

---

## Description

Provides the specific violation-level detail for each non-compliant device — the exact rule that failed, the failure message, and the recommended remediation action — transforming a generic 'non-compliant' status into an actionable fix instruction that an engineer can execute without opening the Catalyst Center GUI.

## Value

UC-5.13.28 tells you *how many* devices are non-compliant. UC-5.13.31 tells you *what type* of compliance failed. This UC tells you *exactly what is wrong and how to fix it*. The `remediationAction` field from the Catalyst Center API provides the specific configuration change needed — 'Apply template X to interface Y' or 'Upgrade to version Z.' This closes the loop from detection to remediation by giving the engineer the fix instruction directly in the Splunk ticket or CSV export, without requiring them to navigate through multiple Catalyst Center GUI screens to find the same information. For NIST CM-6 evidence, the violation detail demonstrates not just that you detected drift but that you know the specific delta and have a documented remediation path for each finding.

## Implementation

Same `compliance` input as UC-5.13.28. The nested `violations{}` array requires `spath | mvexpand | spath` to extract per-violation fields. Use as a drilldown from UC-5.13.28 or UC-5.13.31, filtered to specific devices or compliance types. Export as CSV for ITSM ticket bulk creation.

## Detailed Implementation

### Prerequisites
- UC-5.13.28 (Compliance Status Overview) must be operational — same `compliance` data feed.
- Confirm that the compliance API returns violation detail (nested `violations{}` array). Not all compliance types include detail — RUNNING_CONFIG typically does (shows the specific configuration lines that differ from the golden template), but IMAGE compliance may only show the version mismatch without a `violations` array. EOX typically has no violations array.
- The `spath | mvexpand | spath` pattern is required because violation data is double-nested JSON — direct field references like `violations{}.violationType` won't work reliably across TA versions. This is the same reliable extraction pattern used in UC-5.13.9 (Client Health) for nested score data.
- This UC is a **drill-down** view, not a standalone dashboard. It's typically launched from UC-5.13.28 (click a non-compliant device) or UC-5.13.31 (click a compliance type) and filtered to the specific context.

### Step 1 — Configure data collection
Same `compliance` input as UC-5.13.28. No additional configuration.

Confirm violation detail is available in the events:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" earliest=-24h
| spath output=violations path=violations{}
| where isnotnull(violations)
| stats count as events_with_violations
```
If `events_with_violations > 0`, violation detail is present. If 0, your Catalyst Center version may not include the `violations{}` array — check the raw event structure with `| head 1 | spath`.

Identify the actual JSON path for violations:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" earliest=-24h
| head 1
| spath
| fieldsummary
| search field="violations*"
```
This shows all fields matching the `violations*` pattern, revealing the correct nesting path for your TA version.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| spath output=violations path=violations{}
| mvexpand violations
| spath input=violations
| table deviceName, complianceType, violationType, violationMessage, remediationAction
| sort deviceName, complianceType
```

Why `spath output=violations path=violations{}` + `mvexpand` + `spath input=violations`: this three-stage extraction flattens the nested JSON array. Each violation becomes its own row with `violationType`, `violationMessage`, and `remediationAction` as separate fields. Stage 1 (`spath output=`) extracts the array into a multivalue field. Stage 2 (`mvexpand`) creates one row per array element. Stage 3 (`spath input=`) extracts the fields from each element. This pattern is resilient to TA version changes because it doesn't hardcode the nesting path beyond the first level.

Why `table` not `stats`: this is a detail view, not an aggregation. Each row is one specific violation on one device. The output is designed for direct consumption: remediation engineers read it row-by-row, or it's exported to CSV for ITSM ticket creation.

Why include `remediationAction`: this is the most valuable field in the entire compliance UC family. It tells the engineer exactly what to do — 'Enable `ip source-route` on interface Gi1/0/1' or 'Update NTP server to 10.1.1.1.' Without it, the engineer must open the Catalyst Center GUI, navigate to the device, find the compliance detail, and read the recommendation. With it, the fix instruction is in the ticket body.

For bulk ITSM ticket creation:
```spl
<base search above>
| eval ticket_summary=deviceName." — ".complianceType.": ".violationType
| eval ticket_description="Violation: ".violationMessage." | Fix: ".remediationAction
| table ticket_summary, ticket_description, deviceName, complianceType, violationType
| outputcsv compliance_violations.csv
```
Upload the CSV to your ITSM (ServiceNow, Jira) for bulk ticket creation. Each row becomes one remediation task.

For filtered drill-down from UC-5.13.28 (specific device — token-driven):
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" deviceName="$selected_device$"
| spath output=violations path=violations{}
| mvexpand violations
| spath input=violations
| table complianceType, violationType, violationMessage, remediationAction
```

For filtered drill-down from UC-5.13.31 (specific compliance type — token-driven):
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" complianceType="$selected_type$"
| spath output=violations path=violations{}
| mvexpand violations
| spath input=violations
| table deviceName, violationType, violationMessage, remediationAction
| sort deviceName
```

For violation pattern analysis (which violation types are most common fleet-wide):
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| spath output=violations path=violations{}
| mvexpand violations
| spath input=violations
| stats dc(deviceName) as affected_devices by violationType, complianceType
| sort -affected_devices
| head 20
```
The top violation types are the most impactful remediation targets — fixing a single `violationType` across 50 devices is more efficient than fixing 50 different violations on one device.

### Step 3 — Validate
(a) Pick a non-compliant device. Open **Catalyst Center > Compliance > [device] > Violation Detail** (or the equivalent compliance detail page for your version). Compare the violation types, messages, and remediation actions with the Splunk output. They should match exactly.

(b) Confirm `spath` produces the expected fields: `| head 1 | spath output=violations path=violations{} | mvexpand violations | spath input=violations | fieldsummary`. The three fields (`violationType`, `violationMessage`, `remediationAction`) should all appear with non-zero count.

(c) For RUNNING_CONFIG violations: the `violationMessage` should contain the specific configuration delta — what's different between the running config and the golden template. If it's generic ('Device is non-compliant'), the compliance API may not be providing diff-level detail for your Catalyst Center version.

(d) For IMAGE violations: `violationType` should indicate the firmware mismatch. If the `violations{}` array is empty for IMAGE type, the API provides version info at the event level, not in the nested array — use `| table deviceName, complianceType, softwareVersion, targetVersion` instead.

(e) Check row count per device: `| stats count by deviceName | sort -count`. A device with 50+ violations has a very strict golden template or a very drifted configuration. Both are worth investigating.

(f) Vendor UI parity: compare the violation detail table with **Catalyst Center > Compliance > [device]** violation list for the same device.

### Step 4 — Operationalize
Dashboard placement:
- As a **drill-down panel** on the Compliance Posture dashboard. Hidden by default; appears when a user clicks a non-compliant device in UC-5.13.28 or a compliance type in UC-5.13.31.
- Token-driven: `deviceName=$selected_device$` and/or `complianceType=$selected_type$` from the parent panel's drilldown.

Remediation workflow:
1. Operations team reviews the violation table for a specific device or compliance type.
2. For each violation: the `remediationAction` provides the fix instruction.
3. Export as CSV for bulk ITSM ticket creation — one ticket per device (or per unique `violationType` across devices for fleet-level fixes).
4. The engineer applies the fix (push golden template, modify configuration, upgrade firmware).
5. After remediation: verify the violation clears in the next compliance poll (1 hour).
6. Close the ticket and archive the before/after compliance states for audit evidence.

For assessor walkthroughs:
- Show the assessor the violation detail for a sample of non-compliant devices.
- Demonstrate that each violation has a `remediationAction` — proving the monitoring system doesn't just detect drift but provides actionable fix instructions.
- Show closed tickets that correspond to remediated violations — proving the detection-to-remediation loop is closed.
- Export the 30-day violation history (UC-5.13.30 trend + this detail) as evidence for CM-6.

### Step 5 — Troubleshooting

- **`violations{}` is null for all events** — your Catalyst Center version may not include violation detail in the compliance API response. Check the API documentation for your version. Some versions only provide violation detail for RUNNING_CONFIG compliance, not IMAGE or PSIRT.

- **Empty table after `mvexpand`** — the `spath path=violations{}` is wrong for your JSON structure. Common variants: `violations`, `violationDetail`, `nonCompliantDetails{}`, `complianceDetail{}.violations{}`. Check `| head 1 | spath` on a raw non-compliant event to see the actual structure.

- **`remediationAction` is null for many violations** — not all violation types include a remediation suggestion. Catalyst Center provides remediation for RUNNING_CONFIG violations (golden template diff) but may not for custom compliance rules or NETWORK_SETTINGS checks. Handle with `| eval remediationAction=coalesce(remediationAction, "See Catalyst Center Compliance detail for this device")`.

- **Exploding row count** — one compliance API event per device per type per poll, and each can have multiple violations. At scale (2,000 devices × 3 violation types × 5 violations each = 30,000 rows), the table becomes unwieldy. Limit with `| head 100` or filter to specific devices/types via the drilldown tokens.

- **`violationType` strings are cryptic or internal** — Catalyst Center's internal rule names may not be human-readable (e.g., `COMPLIANCE_RULE_42` instead of a descriptive name). Create a `violation_type_labels` lookup to map internal names to friendly descriptions for the dashboard.

- **Violation detail differs from Catalyst Center GUI** — the GUI may show a rendered diff view (side-by-side configuration comparison) while the API provides raw text fields. The content should match; the presentation differs. For the full diff view, direct the engineer to Catalyst Center's compliance detail page.

- **CSV export for ticket creation is too large** — if a device has 50 violations, 50 tickets is too many. Deduplicate by device: `| stats values(violationType) as violations values(remediationAction) as fixes by deviceName, complianceType` to produce one row per device with all violations concatenated.

- **Performance concern** — `mvexpand` on large datasets (thousands of events × dozens of violations per event) is expensive. Narrow to `earliest=-2h` (one compliance poll cycle) for the current violation state. For historical violation analysis, use summary indexing.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| spath output=violations path=violations{}
| mvexpand violations
| spath input=violations
| table deviceName, complianceType, violationType, violationMessage, remediationAction
| sort deviceName, complianceType
```

## Visualization

(1) Table: deviceName, complianceType, violationType, violationMessage, remediationAction — sorted by device for remediation workflow. (2) Export: `| outputcsv` for ITSM ticket bulk creation. (3) Drilldown from UC-5.13.28 (click non-compliant device) or UC-5.13.31 (click compliance type). (4) Count: `| stats dc(violationType) as unique_violations by complianceType` for violation pattern analysis.

## Known False Positives

**Compliance violation detail showing expected configuration differences for lab devices.** Lab devices may have intentional deviations from the golden template. Distinguish by checking `deviceName` against lab naming conventions. Suppress with `catalyst_compliance_exceptions` lookup.

**Large number of violation entries for a single device due to template strictness.** A very detailed golden template with many checked elements may generate dozens of violations for a single device — each missing ACL entry, each non-standard banner line, each disabled feature is a separate violation. Distinguish by grouping violations by `deviceName` and counting unique types. Present as a summary count per device with drill-down to individual violations.

**Nested JSON violation structure requiring careful spath expansion.** The `violations{}` array structure may differ between Catalyst Center versions. Some nest violations inside `violations{}.violation` or use different field names. Distinguish by running `| head 1 | spath` on a non-compliant event to map the actual JSON path. Adjust `spath path=` accordingly.

**Violation details changing between polls due to partial compliance remediation.** A device may have some violations fixed between polls, causing the violation list to change. This is remediation in progress — the changing list reflects actual progress, not a data quality issue.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-6 Configuration Settings](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-6)
