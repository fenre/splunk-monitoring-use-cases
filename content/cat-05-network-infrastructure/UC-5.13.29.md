<!-- AUTO-GENERATED from UC-5.13.29.json — DO NOT EDIT -->

---
id: "5.13.29"
title: "Non-Compliant Device Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.29 · Non-Compliant Device Alerting

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Compliance, Configuration &middot; **Wave:** Crawl &middot; **Status:** Verified

*We set up an alarm that goes off the moment any network device's settings drift from the approved standards. This is especially important for devices that handle sensitive data — the alarm ensures your team fixes the drift before it becomes a security hole or an audit failure.*

---

## Description

Fires an alert when any managed device falls out of compliance with Catalyst Center's golden-template policies, providing the device name, IP, violation type, and duration of non-compliance — so the security and operations teams can remediate configuration drift before it becomes a security vulnerability or audit finding.

## Value

UC-5.13.28 shows the compliance posture. This UC *pages you* when it degrades. A device that drifts from the golden template is running an unapproved configuration — which could mean a missing ACL, a disabled security feature, or an outdated protocol setting. Every hour that config drift goes undetected is an hour of elevated risk. For PCI-scoped devices, non-compliance triggers a potential assessment finding. For NIST CM-6, it's a control failure that must be documented and remediated. This alert closes the gap between Catalyst Center detecting the drift and your team fixing it.

## Implementation

Same `compliance` input as UC-5.13.28. Schedule as alert: cron `*/30 * * * *`, time range `-1h to now`, trigger on any results. Throttle by `deviceName` for 4 hours (to handle bulk template pushes gracefully). Route to the change management or security operations team.

## Detailed Implementation

### Prerequisites
- UC-5.13.28 (Compliance Status Overview) must be operational — same `compliance` data feed.
- Verify that `complianceStatus="NON_COMPLIANT"` is the correct string for your TA version. Run `| stats values(complianceStatus)` to confirm. Common variants: `NON_COMPLIANT`, `Non-Compliant`, `non_compliant`.
- Decide on alert routing: configuration drift alerts should go to the change management / security operations team, NOT the NOC. The NOC handles incidents; compliance drift is a change management issue.
- For PCI-scoped environments: document which devices are in the Cardholder Data Environment (CDE). Consider adding a `pci_in_scope` lookup so the alert can flag CDE devices separately with higher urgency.

### Step 1 — Configure data collection
Same `compliance` input as UC-5.13.28. No additional configuration.

Confirm non-compliant devices exist in the data:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" earliest=-24h
| stats dc(deviceName) as noncompliant_devices
```
If 0, either all devices are compliant (ideal) or no golden templates are assigned (see UC-5.13.28 Prerequisites).

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| stats latest(complianceType) as violation_type latest(_time) as last_seen by deviceName, managementIpAddress
| eval hours_noncompliant=round((now()-last_seen)/3600,1)
| sort -hours_noncompliant
```

Why `latest(complianceType)` per device: a device may have multiple compliance type violations (RUNNING_CONFIG and IMAGE simultaneously). `latest()` shows the most recently detected type. For all types per device, use `values(complianceType) as violation_types`.

Why `hours_noncompliant`: provides urgency context. A device non-compliant for 2 hours may be in the middle of a config push (acceptable). A device non-compliant for 72 hours has a genuine drift problem (needs remediation).

Why `by deviceName, managementIpAddress`: both are included so the ticket/alert body gives the responder everything needed to connect to the device without a lookup.

Schedule as Alert:
- Cron: `*/30 * * * *` (every 30 minutes — compliance drift is not as time-sensitive as P1 issues)
- Time range: `-2h to now` (covers 2 compliance poll cycles at 1h interval)
- Trigger: "Number of results > 0"
- Throttle: by `deviceName` for `4h` (prevents alert storms during bulk template pushes)

For PCI-scoped devices with higher urgency:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| stats latest(complianceType) as violation_type by deviceName, managementIpAddress
| lookup pci_in_scope deviceName OUTPUT in_cde
| where in_cde="yes"
| eval urgency="PCI-CRITICAL: CDE device non-compliant"
```
Schedule this variant every 15 minutes with no throttle.

### Step 3 — Validate
(a) If you have a device currently showing NON_COMPLIANT in **Catalyst Center > Compliance**, verify it appears in the Splunk alert results with matching `deviceName` and `complianceType`.

(b) Intentional test: in a lab, make a manual CLI change to a device that violates the golden template (e.g., add an unauthorised ACL). Within the next compliance poll cycle (1 hour), the device should appear in the alert results.

(c) Throttle test: trigger the alert twice within 4 hours for the same device. Only one notification should arrive.

(d) Cross-reference with UC-5.13.28 (Compliance Overview): the count of non-compliant devices in the alert should match or be a subset of the NON_COMPLIANT count in the overview.

(e) For PCI environments: verify CDE devices are correctly tagged by the `pci_in_scope` lookup.

### Step 4 — Operationalize
Alerting:
- **Change Management / Security Ops**: primary recipient. Include deviceName, managementIpAddress, violation_type, hours_noncompliant, and a link to UC-5.13.33 (Violation Detail) for remediation actions.
- **Slack/Teams**: `#compliance-alerts` for visibility.
- **ServiceNow**: auto-create a change request for remediation, categorised under "Configuration Management."

Runbook (owner: Change Management):
1. Open the alert. Note `deviceName` and `violation_type`.
2. For **RUNNING_CONFIG** non-compliance:
   - Compare the device's running-config to the golden template in **Catalyst Center > Design > Template Editor**.
   - Identify the specific configuration delta. Common causes: manual CLI change, partial template push, SNMP community string modification.
   - If the delta is authorised (approved change not yet templated): update the golden template to match.
   - If the delta is unauthorised: remediate by pushing the golden template from Catalyst Center.
3. For **IMAGE** non-compliance: the device is not running the designated golden firmware image. See UC-5.13.56 for firmware compliance remediation.
4. For **PSIRT** non-compliance: the device is affected by an unpatched security advisory. See UC-5.13.34–39 for PSIRT handling.
5. After remediation: verify the device returns to COMPLIANT in the next poll cycle (1 hour).
6. Document the remediation in the `catalyst_compliance_exceptions` lookup if an exception is approved.

Compliance evidence (NIST CM-6 / PCI 1.1.1):
- Archive alert history to a restricted index for assessor review.
- Track the time from non-compliance detection to remediation — this is the CM-6 "response time" metric.
- Include in monthly compliance reports alongside UC-5.13.28 (posture overview) and UC-5.13.30 (trending).

### Step 5 — Troubleshooting

- **Alert fires for hundreds of devices simultaneously** — a golden template was just updated. Check `index=catalyst sourcetype="cisco:dnac:audit:logs"` for template changes. This is expected after a template update — allow 24 hours for configuration pushes to complete.

- **Alert never fires but non-compliant devices exist in Catalyst Center** — check the `complianceStatus` string. Case sensitivity matters: `NON_COMPLIANT` ≠ `Non-Compliant`. Run `| stats values(complianceStatus)` to verify.

- **Alert fires during every maintenance window** — add a `catalyst_maintenance_windows` lookup and filter.

- **Same device re-alerts every 4 hours** — the device is genuinely non-compliant and hasn't been remediated. The throttle resets after 4 hours. This is working as designed — the device needs to be fixed.

- **Alert fires for lab devices** — add lab devices to `catalyst_compliance_exceptions` lookup and filter.

- **Compliance type doesn't match expectations** — not all compliance types are applicable to all device families. APs may not support RUNNING_CONFIG compliance. Check **Catalyst Center > Compliance** for the device to see which types are evaluated.

- **`managementIpAddress` is null** — some TA versions don't extract this field. Fall back to `deviceUuid` and resolve the IP from a `catalyst_device_lookup`.

- **PCI-scoped variant shows no results** — the `pci_in_scope` lookup is empty or has incorrect `deviceName` values. Verify the lookup contents match the actual device names in the compliance data.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| stats latest(complianceType) as violation_type latest(_time) as last_seen by deviceName, managementIpAddress
| eval hours_noncompliant=round((now()-last_seen)/3600,1)
| sort -hours_noncompliant
```

## Visualization

(1) Alert results table: deviceName, managementIpAddress, violation_type, hours_noncompliant — sorted by duration. (2) Single value: count of non-compliant devices (red ≥ 1). (3) Context: drilldown to UC-5.13.28 (compliance posture) and UC-5.13.33 (violation detail) for remediation guidance.

## Known False Positives

**Golden template update causing a wave of non-compliance alerts.** When the golden template is updated in Catalyst Center, all devices are re-evaluated against the new template. Devices that were compliant under the old template may now be non-compliant. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:audit:logs"` for template changes. Suppress by allowing 24 hours after a template change before triggering non-compliance alerts.

**Device in the middle of a configuration push showing temporary non-compliance.** During a staged configuration deployment, devices transition through a non-compliant state. Distinguish by checking whether `complianceStatus` changes to COMPLIANT on the next poll. Suppress by requiring non-compliance to persist across 2+ consecutive polls.

**Lab or pilot device running non-standard configuration.** Test equipment may intentionally deviate from the golden template. Distinguish by checking `deviceName` against lab naming conventions. Suppress with a `catalyst_compliance_exceptions` lookup.

**Compliance check failure due to API timeout on large configurations.** Devices with very large running configurations may cause the compliance check to time out, returning ERROR instead of a valid status. Distinguish by checking `index=_internal` for timeout errors. Suppress by treating ERROR separately from NON_COMPLIANT.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-6 Configuration Settings](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-6)
