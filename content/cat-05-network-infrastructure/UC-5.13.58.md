---
id: "5.13.58"
title: "SWIM Upgrade Failure Alerting"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.58 · SWIM Upgrade Failure Alerting

## Description

Alerts when firmware upgrade operations fail, with the failure reason and affected device details for immediate troubleshooting.

## Value

Failed upgrades may leave devices in an inconsistent state. Immediate alerting ensures recovery actions (rollback, retry, manual intervention) start promptly.

## Implementation

Extend the SWIM collector so each failed upgrade produces at least: `deviceName`, `deviceFamily`, `runningVersion`, `targetVersion`, `upgradeStatus=FAILED`, and `failureReason` (from API fields such as `failureReason`, `message`, or nested error objects in `GET /dna/intent/api/v1/network-device-image-updates` responses). Authenticate with `POST /dna/system/api/v1/auth/token`.

**Scripted input** (short interval during change windows, for example 300 s):

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 300
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

**Event notifications (optional):** If your Catalyst Center can push SWIM failure events, configure a Platform webhook to Splunk HEC with `sourcetype=cisco:dnac:swim` and merge failure payloads into the same index for correlation. Ensure deduplication if both poll and webhook are active (use a stable `event_id` in the script/HEC payload).

## Detailed Implementation

Prerequisites
• UC-5.13.55 and SWIM data with `upgradeStatus` and `failureReason` (or mappable error fields) populated.

Step 1 — Field extraction
From `GET /dna/intent/api/v1/network-device-image-updates` (or device-specific update detail endpoints in your API version), map API error or status text into a single `failureReason` string for Splunk. If the body is JSON with nested `failure` objects, use `| spath` or index-time `KV_MODE=json` in props if you emit raw JSON.

Token lifecycle: `POST /dna/system/api/v1/auth/token` before each run or on 401; never embed secrets in the script file.

Step 2 — Alert SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED" | stats count as failure_count values(failureReason) as reasons by deviceName, deviceFamily, runningVersion, targetVersion | sort -failure_count
```

Step 3 — HEC (optional real-time)
In Catalyst Center, add a webhook destination to `https://<splunk-hec>:8088/services/collector/event` with `Authorization: Splunk <token>`; subscribe to SWIM/firmware failure categories if available; assign `sourcetype=cisco:dnac:swim` in HEC or override via HEC `metadata` in the event wrapper.

Step 4 — Validate
Induce a controlled failure in lab or use historical failure events; confirm alert rows match Catalyst Center.

Step 5 — Operationalize
Set alert throttling to avoid flapping, attach runbook (retry, check reachability, rollback).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED" | stats count as failure_count values(failureReason) as reasons by deviceName, deviceFamily, runningVersion, targetVersion | sort -failure_count
```

## Visualization

Table (deviceName, failureReason, runningVersion, targetVersion), top failure reasons, trend of failure_count over time during upgrade windows.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
