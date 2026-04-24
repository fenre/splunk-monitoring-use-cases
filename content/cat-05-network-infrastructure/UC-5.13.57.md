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
• UC-5.13.55 live with SWIM data in `index=catalyst`, `sourcetype=cisco:dnac:swim`.

Step 1 — API and fields
Poll `GET /dna/intent/api/v1/network-device-image-updates` after `POST /dna/system/api/v1/auth/token`. Normalize the API’s state strings into a field `upgradeStatus` (for example map Catalyst Center’s enumeration to `SUCCESS`, `IN_PROGRESS`, `SCHEDULED`, `FAILED` for consistent SPL). Include `deviceFamily` in each event. If the API returns nested tasks, either flatten in the script or index one event per (device, task).

Step 2 — Real-time path
If you enable Platform event notifications to HEC, set the HEC `sourcetype` to `cisco:dnac:swim` or a parallel sourcetype and add an `| union` in dashboards, or use `collect` in an alert to a summary index for trending.

Step 3 — Search

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=* | stats count by upgradeStatus, deviceFamily | eval status_order=case(upgradeStatus="SUCCESS",1,upgradeStatus="IN_PROGRESS",2,upgradeStatus="SCHEDULED",3,upgradeStatus="FAILED",4,1==1,5) | sort status_order -count
```

Step 4 — Validate
Trigger a test upgrade in a lab and confirm `upgradeStatus` transitions and counts match Catalyst Center SWIM job UI.

Step 5 — Operationalize
Use during change windows: dashboard refresh 1–5 min, optional alerts on rising `FAILED` or stalled `IN_PROGRESS` beyond an SLA window.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=* | stats count by upgradeStatus, deviceFamily | eval status_order=case(upgradeStatus="SUCCESS",1,upgradeStatus="IN_PROGRESS",2,upgradeStatus="SCHEDULED",3,upgradeStatus="FAILED",4,1==1,5) | sort status_order -count
```

## Visualization

Stacked bar or column chart of count by `upgradeStatus` and `deviceFamily`, single values for in-progress and failed, timeline if `_time` from event notifications is used.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
