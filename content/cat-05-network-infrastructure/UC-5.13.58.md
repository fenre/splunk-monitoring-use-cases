<!-- AUTO-GENERATED from UC-5.13.58.json — DO NOT EDIT -->

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
• UC-5.13.55 and SWIM data with `upgradeStatus` and `failureReason` (or mappable error fields) populated in `cisco:dnac:swim`.

Step 1 — Field extraction (Catalyst Center)
From `GET /dna/intent/api/v1/network-device-image-updates` (or the device image update detail in your API version), map API error or status text to a single `failureReason` in Splunk. If the body is JSON with nested `failure` objects, use `spath` in Search or set `KV_MODE=json` in **props** for the sourcetype. Authenticate with `POST /dna/system/api/v1/auth/token` and refresh the token on 401; keep secrets in Splunk’s credential store, not in the script file.

Step 2 — Alert SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED" | stats count as failure_count values(failureReason) as reasons by deviceName, deviceFamily, runningVersion, targetVersion | sort -failure_count
```

Step 3 — HEC (optional, faster than poll alone)
Point Catalyst **Platform** webhooks to Splunk HEC when your release supports SWIM or deployment failure events; set default **sourcetype** to `cisco:dnac:swim` (or merge into the same index with a dedup key if both poll and webhook run).

Step 4 — Validate
Reproduce a known failure in lab or compare samples to **Catalyst Center > SWIM** for the same device and time.

Step 5 — Operationalize and troubleshooting
• **Throttling:** dedupe on `deviceName` + `targetVersion` in a 15–30 minute window to avoid duplicate pages during API retries from the poller.
• **No failures in Splunk but UI shows one:** the script may map only a subset of error codes; expand the `failureReason` map and confirm `upgradeStatus=FAILED` is not normalized to a different string.
• **Noise from canary or lab devices:** add a `lookup` of excluded hostnames or site IDs. **Stuck FAILED after user recovery:** clear state in the controller or wait for the next full poll; some failures are marked FAILED until a successful retry completes.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED" | stats count as failure_count values(failureReason) as reasons by deviceName, deviceFamily, runningVersion, targetVersion | sort -failure_count
```

## Visualization

Table (deviceName, failureReason, runningVersion, targetVersion), top failure reasons, trend of failure_count over time during upgrade windows.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
