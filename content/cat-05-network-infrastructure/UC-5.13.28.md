<!-- AUTO-GENERATED from UC-5.13.28.json — DO NOT EDIT -->

---
id: "5.13.28"
title: "Device Compliance Status Overview"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.28 · Device Compliance Status Overview

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Compliance, Configuration &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check whether every network device's settings match the approved standards your organisation has defined. When a device drifts out of compliance, we flag it immediately — and we keep a running history that proves to auditors your standards are enforced continuously, not just on the day of the audit.*

---

## Description

Shows the compliance posture of every managed network device against Catalyst Center's golden-template policies — COMPLIANT, NON_COMPLIANT, ERROR, IN_PROGRESS — broken down by percentage, so security and compliance teams can see at a glance whether the fleet meets baseline configuration standards.

## Value

Auditors ask for two things: point-in-time compliance snapshots and evidence of continuous monitoring. This UC delivers both. A NON_COMPLIANT percentage above 5% during business hours means devices are running configurations that deviate from the approved golden template — introducing security vulnerabilities, operational inconsistencies, or regulatory violations. Catching drift here first means you can remediate before the next PCI assessment or NIST audit cycle, rather than discovering it during evidence collection. Over quarters, the compliance trend line becomes your strongest proof to assessors that configuration baseline enforcement is a continuous process, not a one-time project.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538) on the Search Head and Heavy Forwarder. Configure a Catalyst Center account and enable the `compliance` input (Inputs → Create → Compliance: account `catcenter-prod`, index `catalyst`, interval `3600`). Schedule a daily compliance snapshot report for the GRC evidence store. Alert when NON_COMPLIANT exceeds 10% of total devices.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads (for CIM tags and knowledge objects) AND the Heavy Forwarder / single-instance running inputs.
- Catalyst Center **2.3.5+** with compliance policies configured — at minimum, assign a golden running-config template to your device families in **Catalyst Center > Design > Network Settings > Template Editor**. Without assigned templates, all devices return NOT_APPLICABLE.
- Service account with **NETWORK-ADMIN-ROLE** (minimum for compliance data). Some compliance detail endpoints may require **SUPER-ADMIN-ROLE** — test with your account before going live.
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Splunk role: users need `srchIndexesAllowed = catalyst`. For compliance evidence exports, the scheduling user needs `schedule_search` capability.
- License headroom: `cisco:dnac:compliance` generates 1 event/device/poll × ~400 bytes. At 3600s interval: **500 devices ≈ 4.7 MB/day, 2,000 devices ≈ 19 MB/day, 10,000 devices ≈ 94 MB/day**. Budget accordingly.
- **Evidence retention**: align `catalyst` index retention with your compliance framework requirements. NIST 800-53 AU-11 recommends retaining audit records for the period required by the organisation's records retention policy — typically **1–3 years** for CM-6 evidence. PCI DSS 10.7 requires at least **12 months** of audit trail history. Set `frozenTimePeriodInSecs` in `indexes.conf` accordingly.
- CIM mapping: this sourcetype maps to the **Change** data model. The TA's `eventtypes.conf` and `tags.conf` should tag compliance events with `change` and `audit` tags. Verify with `| search eventtype=cisco_dnac_compliance tag=change` after installation.

### Step 1 — Configure data collection
In the TA on the Heavy Forwarder: Inputs → Create New Input → Compliance.

| Setting | Value |
|---------|-------|
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `3600` (1 hour — compliance status changes slowly; more frequent polling adds API load without significant benefit) |

The TA authenticates to `POST /dna/system/api/v1/auth/token`, then polls `GET /dna/intent/api/v1/compliance` (or v2 in newer TA releases). Each poll returns one event per device per compliance type (RUNNING_CONFIG, IMAGE, PSIRT, EOX, NETWORK_SETTINGS). A device may produce 1–5 events per poll depending on how many compliance types are configured.

Sample event:
```json
{
  "deviceName": "dist-sw-02.branch.example.com",
  "complianceStatus": "NON_COMPLIANT",
  "complianceType": "RUNNING_CONFIG",
  "lastUpdateTime": 1714060200000,
  "deviceUuid": "device-uuid-xyz789",
  "managementIpAddress": "10.2.1.1"
}
```

Verification: wait one poll interval (1 hour, or restart the input for immediate poll), then run:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" earliest=-2h
| stats count by complianceStatus
```
You should see rows for COMPLIANT and likely NON_COMPLIANT or NOT_APPLICABLE. If the only status is NOT_APPLICABLE, no golden templates are assigned in Catalyst Center — see Prerequisites.

If no events arrive, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors. Common failures: `401 Unauthorized` (credentials), `403 Forbidden` (insufficient RBAC role for compliance endpoint), `Connection refused` (URL/firewall).

Expected event volume: `device_count × compliance_types_per_device × 24 polls/day × 400 bytes`. A 500-device campus with 3 compliance types averages ~1,500 events/poll ≈ 36,000 events/day ≈ 14 MB/day.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| stats latest(complianceStatus) as status by deviceName, complianceType
| stats count by status
| eventstats sum(count) as _total
| eval pct=round(100*count/_total,1)
| table status, count, pct
| sort status
```

Why `latest(complianceStatus) by deviceName, complianceType` first: the TA may emit multiple events per device per poll (one per compliance type) AND the same device appears in every hourly poll. Without deduplication, `stats count by complianceStatus` on raw events would count each status once per poll cycle, inflating the numbers. Taking `latest()` per device per type first gives you the current-state snapshot, then the outer `stats count by status` gives an accurate compliance posture.

Why not filter `NOT_APPLICABLE` and `IN_PROGRESS`: keep them visible in the overview so stakeholders can see the full picture. For alerting and evidence exports, filter them out: `| where status IN ("COMPLIANT", "NON_COMPLIANT", "ERROR")`.

CIM mapping note: if the Change data model is accelerated, you can use `| tstats count from datamodel=Change where All_Changes.action=* by All_Changes.action`. However, compliance status is a state snapshot, not a discrete change event — the CIM mapping is useful for audit log compliance (UC-5.13.45–50) but less natural for this UC. Use the raw SPL above for the compliance overview.

Schedule as Report: cron `0 6 * * *` (6 AM daily), time range `-24h to now`, output to PDF → GRC evidence folder. Also schedule as CSV → `compliance_daily_snapshot.csv` for assessor evidence packs.

Schedule as Alert: cron `0 */4 * * *` (every 4 hours), trigger when `NON_COMPLIANT pct > 10%`, throttle for `24h`. This catches config drift promptly without alert fatigue.

### Step 3 — Validate
(a) In Catalyst Center, navigate to **Provision > Inventory > Compliance** (or **Assurance > Compliance** depending on version). Note the count of COMPLIANT, NON_COMPLIANT, ERROR devices. In Splunk, run the Step 2 search over the same time window. Counts should match within one poll cycle.

(b) Pick two specific devices — one COMPLIANT and one NON_COMPLIANT. In Splunk: `index=catalyst sourcetype="cisco:dnac:compliance" deviceName="<device>" | head 1 | table _time complianceStatus complianceType`. Confirm the status matches what Catalyst Center shows for that device.

(c) Verify all compliance types are present: `index=catalyst sourcetype="cisco:dnac:compliance" | stats dc(complianceType) as types, values(complianceType) as type_list`. Compare with the compliance policies configured in Catalyst Center. If only RUNNING_CONFIG appears but you expect IMAGE and PSIRT too, the TA may not be pulling all compliance types — check the input configuration.

(d) Confirm CIM tagging: `index=catalyst sourcetype="cisco:dnac:compliance" | head 1 | eval _tag_check=if(searchmatch("tag=change"), "tagged", "MISSING — check TA tags.conf on SH")`. If missing, the TA's knowledge objects are not installed on the Search Head.

(e) Evidence export test: run the scheduled search manually and verify the PDF/CSV output contains all expected columns (deviceName, complianceType, status, percentage). Present a sample to the compliance team for format approval before going live.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Catalyst Center — Compliance Posture"):
- Row 1 — Single value tile: "Compliant %" as a large number (green ≥ 95%, yellow 90–95%, red < 90%). Next to it: donut chart of count by status (COMPLIANT green, NON_COMPLIANT red, ERROR orange, NOT_APPLICABLE grey).
- Row 2 — Sortable table: deviceName | complianceType | status — filtered to NON_COMPLIANT and ERROR only. This is the remediation triage list. Drilldown: click a device → open UC-5.13.33 (Compliance Violation Detail) filtered to that device.
- Row 3 — Stacked area timechart from UC-5.13.30 (Compliance Trending): COMPLIANT vs NON_COMPLIANT counts over 30 days. Annotate with change windows from `catalyst_maintenance_windows` lookup so assessors can see that dips correspond to planned template pushes, not uncontrolled drift.
- Row 4 — Compliance by policy type: `| stats count by complianceType, status | xyseries complianceType status count`. This shows whether the non-compliance is concentrated in RUNNING_CONFIG (template drift) or IMAGE (firmware non-compliance — addressed in UC-5.13.56).
- Time-picker presets: "Last 24 hours" (daily review), "Last 30 days" (audit evidence), "Last 90 days" (quarterly compliance report).

Evidence workflow (NIST CM-6 / PCI 1.1.1):
- **Daily snapshot**: scheduled CSV export of the Step 2 search, stored in your GRC system or SharePoint evidence folder with date-stamped filename (`compliance_snapshot_YYYY-MM-DD.csv`).
- **Monthly PDF**: formatted compliance posture report including the donut chart, trending timechart, and exception list. Deliver to the compliance officer.
- **On-demand**: assessors can query the Splunk dashboard directly during audits. Create a read-only role `compliance_auditor` with `srchIndexesAllowed = catalyst` and a search filter scoped to `sourcetype="cisco:dnac:compliance"`.

Runbook (owner: Network Security / Compliance team):
1. Open the Compliance Posture dashboard. Check the "Compliant %" tile. If < 95%, investigate.
2. Filter the table to NON_COMPLIANT. Sort by `deviceName`. Identify the affected devices.
3. For RUNNING_CONFIG non-compliance: compare the device's running config to the golden template in **Catalyst Center > Design > Network Settings > Template Editor**. Common causes: manual CLI changes that bypassed Catalyst Center's template system, or a template update that hasn't been pushed yet.
4. For IMAGE non-compliance: the device is running firmware that doesn't match the designated golden image. See UC-5.13.56 (Firmware Non-Compliance) for remediation.
5. For ERROR status: the device is unreachable or the compliance engine cannot assess it. Correlate with UC-5.13.1 (device health) for reachability. If the device is reachable but compliance errors persist, open a Cisco TAC case.
6. Document each exception in the `catalyst_compliance_exceptions` lookup with justification and review date. Exceptions must be re-approved quarterly.
7. After remediation, verify the status changed in the next poll cycle: `index=catalyst sourcetype="cisco:dnac:compliance" deviceName="<device>" earliest=-2h | head 1 | table complianceStatus`.

### Step 5 — Troubleshooting

- **No events at all** — `compliance` input not enabled, or TA not on the Heavy Forwarder. Check: TA → Inputs → confirm Compliance is present and enabled. CLI: `$SPLUNK_HOME/bin/splunk btool inputs list --debug | grep -i compliance`. Check `splunkd.log` for `ExecProcessor` entries.

- **All devices show NOT_APPLICABLE** — no golden templates are assigned in Catalyst Center. Compliance checks cannot evaluate without a reference template. Configure templates in **Catalyst Center > Design > Network Settings > Template Editor** and assign them to device families.

- **403 Forbidden on the compliance endpoint** — the service account lacks permission for compliance data. Some Catalyst Center deployments require **SUPER-ADMIN-ROLE** for compliance detail endpoints, not just **NETWORK-ADMIN-ROLE**. Escalate the account role or create a separate compliance-specific service account.

- **Only RUNNING_CONFIG compliance type appears, missing IMAGE/PSIRT/EOX** — the TA version or input configuration may only poll the basic compliance endpoint. Check whether the TA supports v2 compliance detail (`GET /dna/intent/api/v2/compliance/detail`) and whether additional compliance types require separate inputs.

- **Compliance status flips between COMPLIANT and NON_COMPLIANT on alternating polls** — the golden template or policy may be in flux (e.g., template is being edited). Check `index=catalyst sourcetype="cisco:dnac:audit:logs"` for recent template edits. Freeze the template before relying on compliance data for audit evidence.

- **Large spike of NON_COMPLIANT after a template update** — this is expected behaviour. When you update a golden template, all devices become non-compliant until their running config is pushed to match. Annotate the compliance trend chart with the template change date. Allow 2–4 hours for template re-push and re-check.

- **`lastUpdateTime` is very old (days or weeks ago)** — the compliance engine may be stalled on that device. In Catalyst Center, navigate to the device's compliance page and trigger a manual re-check. If re-check fails, the device may have a connectivity issue with the Catalyst Center cluster.

- **CIM Change data model shows no compliance events** — the TA's `tags.conf` may not include the `change` tag for compliance events. Check `index=catalyst sourcetype="cisco:dnac:compliance" | head 1 | tags` to see which tags are applied. If `change` is missing, add it to `$SPLUNK_HOME/etc/apps/TA_cisco_catalyst/local/tags.conf`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| stats latest(complianceStatus) as status by deviceName, complianceType
| stats count by status
| eventstats sum(count) as _total
| eval pct=round(100*count/_total,1)
| table status, count, pct
| sort status
```

## Visualization

(1) Donut or pie: count by `complianceStatus` with COMPLIANT green, NON_COMPLIANT red, ERROR orange, IN_PROGRESS grey, NOT_APPLICABLE muted. (2) Single value tile: compliant percentage as a large number (green ≥ 95%, yellow 90–95%, red < 90%). (3) Sortable table: deviceName, complianceType, status — filtered to NON_COMPLIANT only, for remediation triage. (4) Stacked area timechart from UC-5.13.30 showing COMPLIANT vs NON_COMPLIANT counts over 30 days for the audit trend narrative.

## Known False Positives

**Active configuration push marking devices temporarily non-compliant.** During a Catalyst Center template deployment, devices receive new configurations in stages. Between the push and the next compliance check, devices may show as NON_COMPLIANT because the running config does not yet match the golden template. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for recent template deployment activity. Suppress by excluding `complianceStatus=IN_PROGRESS` from non-compliance counts and allowing 2 poll cycles after a configuration push before alerting.

**Lab or pilot devices intentionally deviating from the golden template.** Lab switches or proof-of-concept equipment may run non-standard configurations that fail compliance checks by design. Distinguish by checking whether `deviceName` matches a lab naming convention. Suppress by maintaining a `catalyst_compliance_exceptions` lookup with `deviceName` and justification, and filtering excepted devices from compliance alerting.

**Compliance check returning ERROR due to device unreachability.** If Catalyst Center cannot reach a device to check its configuration, the compliance status may show ERROR rather than COMPLIANT or NON_COMPLIANT. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:devicehealth"` for `reachabilityHealth=Unreachable` on the same device. Suppress by treating ERROR as a separate condition from NON_COMPLIANT — alert on reachability, not compliance.

**NOT_APPLICABLE compliance status for devices that do not support the compliance type.** Some compliance types (e.g., IMAGE compliance for APs, EOX for virtual appliances) return NOT_APPLICABLE for unsupported device families. Distinguish by checking whether `complianceType` is appropriate for the device's platform. Suppress by filtering `| where complianceStatus NOT IN ("NOT_APPLICABLE","IN_PROGRESS")` for compliance violation dashboards.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-6 Configuration Settings](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-6)
