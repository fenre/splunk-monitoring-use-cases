<!-- AUTO-GENERATED from UC-2.6.65.json — DO NOT EDIT -->

---
id: "2.6.65"
title: "Citrix Endpoint Management MDM/MAM Policy Compliance"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.65 · Citrix Endpoint Management MDM/MAM Policy Compliance

## Description

MDM and MAM policies express your minimum security bar: no jailbreak or root, current OS patch bands, a real passcode, and no disallowed applications. CEM can emit compliance state per device and per policy package. A rising non-compliant population after an OS release, or a sudden bloom of blacklisted app hits, is often your first sign of shadow IT or stolen devices on the same fleet as your regulated data. This use case drives executive-friendly compliance rate charts and high-severity security alerts in one place.

## Value

MDM and MAM policies express your minimum security bar: no jailbreak or root, current OS patch bands, a real passcode, and no disallowed applications. CEM can emit compliance state per device and per policy package. A rising non-compliant population after an OS release, or a sudden bloom of blacklisted app hits, is often your first sign of shadow IT or stolen devices on the same fleet as your regulated data. This use case drives executive-friendly compliance rate charts and high-severity security alerts in one place.

## Implementation

Ingest a daily (or more frequent) compliance snapshot, not only raw real-time if volume is high. Map vendor booleans to consistent integer flags. Create an overall `compliance_percent` for managed devices. Alert on any jailbreak or root true, any blacklisted app install on a corporate-owned tag, and sustained passcode false on more than five percent of a business unit. Pair with asset ownership lookups. For regulated industries, route evidence exports to your GRC archive with retention that matches policy. Reconcile counts with the CEM admin console during rollout.

## Detailed Implementation

Prerequisites
• CEM entitlements; secure index with role-based access; data classification for device identifiers.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prefer normalized JSON. If only CSV, use `index-time` and `sourcetype` consistently. Document label meanings for `compliance_state` per OS.

Step 2 — Create the search and alert
Tier-1: jailbreak or root. Tier-2: passcode and blacklist trends. Add change-window suppressions for known app-block pushes.

Step 3 — Validate
In test, run a disallowed app and a policy without passcode, confirm the events. Remove test devices promptly.

Step 4 — Operationalize
Monthly business review: compliance by department; tie to conditional access in identity systems where applicable.

## SPL

```spl
index=xd sourcetype="citrix:endpoint:compliance"
| eval jf=if(match(lower(coalesce(jailbreak_flag, jailbroken, is_compromised, "no")), "(1|true|yes)"), 1, 0)
| eval rf=if(match(lower(coalesce(root_flag, rooted, "no")), "(1|true|yes)"), 1, 0)
| eval pc=if(match(lower(coalesce(passcode_compliant, has_pin, "yes")), "(0|false|no)"), 0, 1)
| eval bad_app=if(tonumber(coalesce(blacklisted_app_hit, blocked_app, 0))>0, 1, 0)
| where jf=1 OR rf=1 OR pc=0 OR bad_app=1 OR lower(coalesce(compliance_state, ""))!="compliant"
| eval reason=case(jf=1, "jailbreak", rf=1, "root", pc=0, "passcode", bad_app=1, "blacklist_app", true(), "other")
| stats values(device_id) as sample_devices, latest(os_patch_level) as patch_level, count as events by user_id, reason
| sort - events
```

## Visualization

Donut: compliant versus not; bar: reasons for failure; line: compliance percent by OS major version across months.

## References

- [Compliance policies in Citrix Endpoint Management](https://docs.citrix.com/en-us/citrix-endpoint-management/citrix-endpoint-mdm-mam.html)
