<!-- AUTO-GENERATED from UC-5.13.32.json — DO NOT EDIT -->

---
id: "5.13.32"
title: "Compliance Drift Detection (Was Compliant, Now Not)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.32 · Compliance Drift Detection (Was Compliant, Now Not)

## Description

Detects devices that were previously compliant but have drifted to non-compliant status, indicating unauthorized changes or configuration drift.

## Value

Compliance drift means something changed — either an unauthorized modification, a failed change, or a new policy that existing configs do not meet. Catching drift early prevents audit findings.

## Implementation

Enable the `compliance` input. Use a time range that includes at least two polling cycles per device. Pair with change records to distinguish policy updates from unauthorized edits.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (7538) with **compliance** → `cisco:dnac:compliance` in `index=catalyst`.
• Agreement on **string values** for `complianceStatus` in your build (`COMPLIANT` / `NON_COMPLIANT` vs other spellings). Confirm in a **raw** event.
• This SPL uses **earliest** vs **latest** in the *selected time range*; pick a range spanning **at least two** TA poll cycles, or the transition may be **invisible**.
• `docs/implementation-guide.md` for input enablement, credentials, and secure outbound HTTPS to Catalyst Center.

Step 1 — Configure data collection
• **TA input:** **compliance**; verify interval and index. Ensure **Catalyst** inventory and **Assurance/Compliance** features are **licensed** and **in scope** for the sites you monitor.
• **Stability of keys:** the search keys on `deviceName` + `complianceType`—if hostnames or policy IDs change in inventory sync, a **false** “new” non-compliance can appear. Add **serial** or **deviceId** to the `by` clause if your feed includes stable identifiers.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats latest(complianceStatus) as current_status earliest(complianceStatus) as previous_status by deviceName, complianceType | where current_status="NON_COMPLIANT" AND previous_status="COMPLIANT" | table deviceName complianceType current_status previous_status
```

Understanding this SPL (drift vs noise)
**Compliance Drift (was compliant, now not)** — Answers “who **regressed** in this window,” not “who is worst overall.”
• **Caveat:** `earliest`/`latest` in a **short** window is fragile when polling is hourly—use **7d** and **alert throttling** for production, or a **state-tracking** summary index for consecutive bad polls.
• Pair results with your **CAB/ITSM** feed: a spike after an **image upgrade** or **SDA** change may be **expected** non-compliance during convergence.

**Pipeline walkthrough**
• One row per `deviceName, complianceType` with **oldest** and **newest** status in range → keep only `COMPLIANT`→`NON_COMPLIANT` paths → `table` for triage.

Step 3 — Validate
• Reproduce a **known** policy change in **lab** and watch one device flip from `COMPLIANT` to `NON_COMPLIANT` in Splunk in the same window the **Catalyst** UI shows the regression.
• Compare row count to **Catalyst** filtered views for changed compliance state (wording by release).
• Add `| where _time>...` in a test to avoid mixing **historical** backfill re-ingest with true drift.

Step 4 — Operationalize (alerting)
• **Schedule** during business hours for **policy** teams first; tune to **per-site** throttles. Include **Catalyst** deep link and **complianceType** in the ticket body.
• For **regulatory** use, store **export** of each firing with the Splunk time range and the **Catalyst** screenshot as one evidence bundle.

Step 5 — Troubleshooting
• **Zero results always:** one poll in the window, or all devices **steady** `NON_COMPLIANT` (no `COMPLIANT` in range)—widen the range or add a `COMPLIANT` history lookup.
• **Too many results after upgrade:** a **Catalyst** server upgrade can **re-evaluate** all policies—**suppress** for 24h or correlate with the change record.
• **Mismatched device list vs UI:** virtual-domain scope, RMA, or **duplicate** `deviceName` in multi-cluster designs—tighten the `by` clause with a unique id field.
• **Sourcetype missing:** re-check **compliance** input, **Token** refresh, and **API** throttling in `splunkd.log`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | stats latest(complianceStatus) as current_status earliest(complianceStatus) as previous_status by deviceName, complianceType | where current_status="NON_COMPLIANT" AND previous_status="COMPLIANT" | table deviceName complianceType current_status previous_status
```

## Visualization

Table (deviceName, complianceType, current_status, previous_status), alert list for drift events.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
