---
id: "5.13.29"
title: "Non-Compliant Device Alerting"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.29 · Non-Compliant Device Alerting

## Description

Alerts when devices fall out of compliance with Catalyst Center policies, identifying which devices have violations and what type of compliance failure occurred.

## Value

Non-compliant devices represent security and operational risk. Immediate alerting ensures violations are remediated before they lead to incidents or audit findings.

## Implementation

Enable the `compliance` input. Schedule the alert **every 30 minutes**; **throttle by deviceName** (for example **4 hours**) to limit noise during bulk config pushes. `GET /dna/intent/api/v2/compliance/detail` via the **compliance** TA input (see UC-5.13.28).

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (Splunkbase 7538); **compliance** data in `index=catalyst`, sourcetype `cisco:dnac:compliance`.
• Same **Intent API** context as the overview: `GET /dna/intent/api/v2/compliance/detail`; **TA input name** **compliance**; default **900s** poll (see **UC-5.13.28** for field definitions).
• API user can read **compliance** results for the managed device inventory; align **virtual domain / site** scope with what security reviews in the **Catalyst** UI.
• Runbook owner for **remediation** and for **Catalyst** policy ownership (change window coordination).

Step 1 — Configure data collection
• **API:** `GET /dna/intent/api/v2/compliance/detail` (device-level compliance detail; exact filtering may depend on **TA** version and modular input options).
• **TA input:** **compliance**; sourcetype `cisco:dnac:compliance`.
• **Key fields for alerts:** `complianceStatus`, **`deviceName`**, `managementIpAddress` (or IP field your TA maps), `complianceType` (**RUNNING_CONFIG**, **IMAGE**, **PSIRT**, **EOX**, **NETWORK_SETTINGS**).

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violation_count values(complianceType) as violation_types by deviceName, managementIpAddress | sort -violation_count
```

Understanding this SPL
• Focuses on **`NON_COMPLIANT`** only; **`violation_count`** can exceed **1** if multiple **policy evaluations** or **time buckets** are merged—tune with **`dedup`** or **`| stats latest() by deviceName, complianceType`** if your team counts **one row per device** for ticketing.
• **`values(complianceType)`** lists **which** policy families failed on that device; pair with the **Catalyst** Compliance page for the **exact** failing rule or diff.

**Pipeline walkthrough**
• Filters the compliance feed, aggregates **violations** and **types** by **device** identifiers, and sorts to put the **worst** systems first for **email/ITSM** payloads.

**Alerting recommendations**
• **Schedule:** run the alert on a **30-minute** cadence (balance between **MTTD** and **API/event noise**; faster than **15m** is rarely needed for **config drift** that is not security-PSIRT-critical).
• **Throttle / suppression:** **throttle by `deviceName` for 4 hours** (or use **per-result** throttling) to **avoid alert storms during bulk template pushes** when many devices flip **NON_COMPLIANT** and back to **COMPLIANT** in the same maintenance window. Combine with a **“maintenance”** time window token if you use **Splunk** scheduled maintenance.

Step 3 — Validate
• Compare the **set of `deviceName` values** and **`complianceType` failures** to **Catalyst Center > Compliance** for the same time—counts may differ if Splunk’s window spans **two** polls; use **“last 35 minutes”** to match a **30m** schedule.
• Confirm **`managementIpAddress`** (or your IP field) matches **Catalyst** inventory for **NOC** reachability in the **ticket** body.

Step 4 — Operationalize
• **Alert actions:** open **ticket** with top **5** devices from **`sort`**, include **`violation_types`**, link to **UC-5.13.28** **dashboard** for **% COMPLIANT** context.
• **P1** only for **IMAGE** or **PSIRT** non-compliance if your **policy** says so; **RUNNING_CONFIG** drift may be **P2** with a **4h** follow-up in many orgs—document the matrix in the runbook.

Step 5 — Troubleshooting
• **Spikes during change:** if **hundreds** of alerts fire, verify **throttle by device** and a **change record**; **pause** the alert for the **CAB** window if safe.
• **False negatives:** if **Catalyst** shows **NON_COMPLIANT** but Splunk is quiet, check **sourcetype** routing, **index-time** filter, and **Catalyst** **scope** (Splunk may be **global** while the engineer filtered **one site**).
• **Duplicate device names:** use **device serial** or **id** in **`stats by`** if the TA enriches it—naming collisions across sites exist.
• **PSIRT-specific failures:** follow **Cisco** advisory **remediation** in **Catalyst** first; Splunk is the **notifier**, not the **patch** engine.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as violation_count values(complianceType) as violation_types by deviceName, managementIpAddress | sort -violation_count
```

## Visualization

Table (violation_count, violation_types by device), list panel for email or ticket bodies.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
