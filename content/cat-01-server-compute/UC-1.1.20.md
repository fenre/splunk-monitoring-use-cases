<!-- AUTO-GENERATED from UC-1.1.20.json — DO NOT EDIT -->

---
id: "1.1.20"
title: "Reboot Detection (Linux)"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.20 · Reboot Detection (Linux)

## Description

Unexpected reboots may indicate kernel panics, hardware failure, or unauthorized changes. Distinguishing planned vs. unplanned reboots is key.

## Value

Unexpected reboots may indicate kernel panics, hardware failure, or unauthorized changes. Distinguishing planned vs. unplanned reboots is key.

## Implementation

Forward syslog. Detect boot-up log patterns. Cross-reference boot times with maintenance window lookups to flag unplanned reboots. Alert on any reboot outside approved windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, Syslog.
• Ensure the following data sources are available: `sourcetype=syslog`, `sourcetype=who` (wtmp).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward syslog. Detect boot-up log patterns. Cross-reference boot times with maintenance window lookups to flag unplanned reboots. Alert on any reboot outside approved windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog ("Initializing cgroup subsys" OR "Linux version" OR "Command line:" OR "systemd.*Started" OR "Booting Linux")
| stats latest(_time) as last_boot by host
| eval hours_since_boot = round((now() - last_boot) / 3600, 1)
| join max=1 host [| inputlookup maintenance_windows.csv | where status="approved"]
| sort hours_since_boot
```

Understanding this SPL

**Reboot Detection (Linux)** — Unexpected reboots may indicate kernel panics, hardware failure, or unauthorized changes. Distinguishing planned vs. unplanned reboots is key.

Documented **Data sources**: `sourcetype=syslog`, `sourcetype=who` (wtmp). **App/TA** (typical add-on context): `Splunk_TA_nix`, Syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hours_since_boot** — often to normalize units, derive a ratio, or prepare for thresholds.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, last boot, planned/unplanned), Timeline of reboots, Single value panel (unexpected reboots last 7d).

## SPL

```spl
index=os sourcetype=syslog ("Initializing cgroup subsys" OR "Linux version" OR "Command line:" OR "systemd.*Started" OR "Booting Linux")
| stats latest(_time) as last_boot by host
| eval hours_since_boot = round((now() - last_boot) / 3600, 1)
| join max=1 host [| inputlookup maintenance_windows.csv | where status="approved"]
| sort hours_since_boot
```

## Visualization

Table (host, last boot, planned/unplanned), Timeline of reboots, Single value panel (unexpected reboots last 7d).

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
