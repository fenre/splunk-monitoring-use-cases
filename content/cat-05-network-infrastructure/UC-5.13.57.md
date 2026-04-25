<!-- AUTO-GENERATED from UC-5.13.57.json — DO NOT EDIT -->

---
id: "5.13.57"
title: "Image Distribution and Upgrade Progress Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.57 · Image Distribution and Upgrade Progress Tracking

## Description

Tracks the progress of firmware distribution and upgrade operations across the managed device fleet, showing success, in-progress, scheduled, and failed states.

## Value

Large-scale firmware upgrades are high-risk operations. Real-time progress tracking ensures failures are caught immediately and upgrade windows are respected.

## Implementation

Ingest `upgradeStatus` (and related metadata) from Catalyst Center SWIM into `sourcetype=cisco:dnac:swim` using the same poller as UC-5.13.55. Primary Intent API: `GET /dna/intent/api/v1/network-device-image-updates` (often returns schedule, state, and device identifiers; field names may include versions of SUCCESS, IN_PROGRESS, FAILED, etc.). Re-authenticate on each run or cache the token with expiry handling via `POST /dna/system/api/v1/auth/token`.

**Scripted input example** (`interval` aligned to your change window, for example 300–900 seconds during upgrades):

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 300
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

**HEC / event notifications (optional):** For faster state transitions, register Catalyst Center event notifications (if your release exposes SWIM task events) to Splunk HEC and merge into the same sourcetype or a secondary `cisco:dnac:swim:event` that you `union` in dashboards.

## Detailed Implementation

Prerequisites
• UC-5.13.55 live with SWIM data in `index=catalyst`, `sourcetype=cisco:dnac:swim` including `upgradeStatus` and `deviceFamily` (from your poller or HEC path).

Step 1 — API and fields (Catalyst Center)
• Poll `GET /dna/intent/api/v1/network-device-image-updates` after `POST /dna/system/api/v1/auth/token`. Normalize the API’s state strings into `upgradeStatus` (for example `SUCCESS`, `IN_PROGRESS`, `SCHEDULED`, `FAILED`) for consistent SPL. Include `deviceFamily` in each event; flatten nested task lists in the script if the JSON is not one row per device.
• Optional **push path:** HEC to `cisco:dnac:swim` (or a parallel sourcetype) and `| union` in dashboard base searches; dedupe on device + task id if poll and event both run.

Step 2 — Search (progress view)

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=* | stats count by upgradeStatus, deviceFamily | eval status_order=case(upgradeStatus="SUCCESS",1,upgradeStatus="IN_PROGRESS",2,upgradeStatus="SCHEDULED",3,upgradeStatus="FAILED",4,1==1,5) | sort status_order -count
```

Step 3 — Validate
• Run a small lab upgrade; confirm that counts move from SCHEDULED/IN_PROGRESS to SUCCESS and that FAILED matches **Catalyst Center > SWIM** job details.

Step 4 — Operationalize
• During **change windows**, schedule a short refresh (1–5 minutes) on a dashboard; alert when `FAILED` increases against a **baseline** or when `IN_PROGRESS` exceeds an SLA (for example 4 hours) with no SUCCESS.

Step 5 — Troubleshooting
• **Flat or missing `upgradeStatus`:** poller not mapping API fields, or the script runs outside the change window; confirm `cisco:dnac:swim` events include `upgradeStatus` in raw data.
• **Inflated IN_PROGRESS after restart:** the API may re-emit a task; use `dc(deviceName)` in a time-bounded `stats` to avoid double-counting duplicate lines.
• **HEC 401/404:** HEC token or URL wrong; Catalyst Center may still have healthy SWIM while Splunk is quiet — see UC-5.13.64 for the notification pipeline when you combine push and pull data.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=* | stats count by upgradeStatus, deviceFamily | eval status_order=case(upgradeStatus="SUCCESS",1,upgradeStatus="IN_PROGRESS",2,upgradeStatus="SCHEDULED",3,upgradeStatus="FAILED",4,1==1,5) | sort status_order -count
```

## Visualization

Stacked bar or column chart of count by `upgradeStatus` and `deviceFamily`, single values for in-progress and failed, timeline if `_time` from event notifications is used.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
