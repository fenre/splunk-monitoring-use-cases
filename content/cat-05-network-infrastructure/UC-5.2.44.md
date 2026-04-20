---
id: "5.2.44"
title: "FortiGate Security Fabric Health Monitoring (Fortinet)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.44 · FortiGate Security Fabric Health Monitoring (Fortinet)

## Description

Security Fabric ties FortiGate to FortiManager, FortiAnalyzer, FortiSandbox, EMS, and downstream FortiGates for synchronized policy, logging, and threat intelligence. When fabric connectivity or authorization breaks, you lose centralized management, shared object updates, and automated sandbox verdict workflows—often silently until someone notices missing logs or stale objects. Monitoring root and downstream fabric membership, heartbeat, and authorization errors gives early warning before operations and compliance gaps widen.

## Value

Security Fabric ties FortiGate to FortiManager, FortiAnalyzer, FortiSandbox, EMS, and downstream FortiGates for synchronized policy, logging, and threat intelligence. When fabric connectivity or authorization breaks, you lose centralized management, shared object updates, and automated sandbox verdict workflows—often silently until someone notices missing logs or stale objects. Monitoring root and downstream fabric membership, heartbeat, and authorization errors gives early warning before operations and compliance gaps widen.

## Implementation

Ensure FortiOS event logging includes system and fabric-related categories (varies by version). Install `TA-fortinet_fortigate` and send logs via syslog or reliable forwarding. Create alerts for authorization failures, certificate issues, or loss of FortiManager reachability strings in `logdesc`/`msg`. Validate FortiManager/Analyzer versions and time sync. Test by temporarily blocking management paths in a lab to confirm detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-fortinet_fortigate` (Splunkbase 2846).
• Ensure the following data sources are available: `sourcetype=fgt_event`, `sourcetype=fortinet_fortios_event`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure FortiOS event logging includes system and fabric-related categories (varies by version). Install `TA-fortinet_fortigate` and send logs via syslog or reliable forwarding. Create alerts for authorization failures, certificate issues, or loss of FortiManager reachability strings in `logdesc`/`msg`. Validate FortiManager/Analyzer versions and time sync. Test by temporarily blocking management paths in a lab to confirm detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event")
  (lower(_raw) LIKE "%fabric%" OR lower(logdesc) LIKE "%fabric%" OR lower(msg) LIKE "%fabric%"
   OR match(_raw, "(?i)FortiManager|FortiAnalyzer|authorization failed|certificate.*fabric"))
| eval device=coalesce(devname, dvc, host)
| stats count by device type subtype logdesc msg level
| sort -count
```

Understanding this SPL

**FortiGate Security Fabric Health Monitoring (Fortinet)** — Security Fabric ties FortiGate to FortiManager, FortiAnalyzer, FortiSandbox, EMS, and downstream FortiGates for synchronized policy, logging, and threat intelligence. When fabric connectivity or authorization breaks, you lose centralized management, shared object updates, and automated sandbox verdict workflows—often silently until someone notices missing logs or stale objects. Monitoring root and downstream fabric membership, heartbeat, and authorization errors gives early…

Documented **Data sources**: `sourcetype=fgt_event`, `sourcetype=fortinet_fortios_event`. **App/TA** (typical add-on context): `TA-fortinet_fortigate` (Splunkbase 2846). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **device** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by device type subtype logdesc msg level** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, subtype, message), Timeline (fabric errors), Status grid (root vs leaf FortiGate health).

## SPL

```spl
index=firewall sourcetype IN ("fgt_event","fortinet_fortios_event")
  (lower(_raw) LIKE "%fabric%" OR lower(logdesc) LIKE "%fabric%" OR lower(msg) LIKE "%fabric%"
   OR match(_raw, "(?i)FortiManager|FortiAnalyzer|authorization failed|certificate.*fabric"))
| eval device=coalesce(devname, dvc, host)
| stats count by device type subtype logdesc msg level
| sort -count
```

## Visualization

Table (device, subtype, message), Timeline (fabric errors), Status grid (root vs leaf FortiGate health).

## References

- [Splunkbase app 2846](https://splunkbase.splunk.com/app/2846)
