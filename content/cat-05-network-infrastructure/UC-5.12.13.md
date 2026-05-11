<!-- AUTO-GENERATED from UC-5.12.13.json — DO NOT EDIT -->

---
id: "5.12.13"
title: "Voicemail System Health Monitoring (Unity, Exchange UM)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.12.13 · Voicemail System Health Monitoring (Unity, Exchange UM)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the machines that store voice messages and blink your message light so if they get sick or full, someone fixes them before people wonder why nobody got their voicemail.*

---

## Description

Surfaces voicemail platform faults—Unity Connection stack errors, Exchange UM worker crashes, MWI signaling delays, and mailbox database latency—so greeting playback and message waiting lamps stay dependable.

## Value

Unified communications teams restore voicemail services quickly when UM processes wedge or storage thresholds trip, preventing silent subscriber failures where calls roll to generic recordings without generating tickets.

## Implementation

Normalize Unity and Exchange timestamps to UTC; tag UM role hosts; alert on error burst deltas vs. seven-day baseline; pair with synthetic deposit tests weekly.

## Detailed Implementation

### Prerequisites
- Diagnostic logging enabled on Cisco Unity Connection (Connection Administration → Logs) forwarded via syslog/HEC.
- Exchange UM servers forwarding Application/System logs or SCOM-exported CSV.
- Inventory CSV linking `host`, `UM_role`, `voicemail_domain`, `storage_group`.

### Step 1 — Onboard logs
Route Unity Connection diagnostics into dedicated index with UTF-8 preservation for multilingual prompts metadata.

### Step 2 — Field extraction
Extract error codes, LDAP correlation IDs, and mailbox identifiers using vendor regex packs; mask subscriber PIN data—never index secrets.

### Step 3 — Baseline noise
Compute hourly error counts per component; alert when five-minute counts exceed three times rolling median excluding patch Tuesdays.

### Step 4 — Dashboard
Tiles for Unity vs Exchange UM error rates; timeline of MWI SIP NOTIFY failures; storage quota nearing-full indicators.

### Step 5 — Operational response
Restart UM worker under change window after validating DAG replication healthy; for Unity disk alarms purge orphaned prompts only per vendor KB.

Extended troubleshooting
MWI storms after bulk mailbox migrations mimic outages—correlate with migration batches. Hybrid UM retirements may shift traffic unexpectedly; validate hunt pilot overflow remains configured.

## SPL

```spl
(index=voicemail OR index=msexchange OR index=windows)
(sourcetype="cisco:unity:diag" OR sourcetype="MSExchangeUM*" OR sourcetype="WinEventLog:Application")
(error OR fail OR timeout OR MWI OR "storage")
| rex field=_raw max_match=1 "(?i)(?<vm_component>Unity|UMWorkerProcess|MSExchangeUM)"
| stats count by vm_component, host
| where count > 20
| sort -count
```

## Visualization

Split comparison chart Unity vs Exchange UM errors; table of top mailbox_ids impacted; single-value MWI failure percentage.

## Known False Positives

Scheduled antivirus scans spike disk latency alarms; benign LDAP constraint violations during AD tidy scripts resemble auth failures; UM language-pack updates emit benign INFO parsed as error when regex too broad; transient replication backlog after reboot clears without user impact.

## References

- [Cisco Unity Connection Administration Guide — Diagnostics](https://www.cisco.com/c/en/us/)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
