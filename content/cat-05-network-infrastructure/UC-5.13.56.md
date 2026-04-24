---
id: "5.13.56"
title: "Firmware Non-Compliance Detection (Running vs Golden Image)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.56 · Firmware Non-Compliance Detection (Running vs Golden Image)

## Description

Identifies devices running software versions that do not match the Catalyst Center golden image assignment, indicating firmware non-compliance.

## Value

Devices running non-golden images may have known vulnerabilities, missing features, or untested configurations. Firmware compliance is a key security control.

## Implementation

Use the same SWIM scripted input as UC-5.13.55 (`sourcetype=cisco:dnac:swim`), ensuring the collector merges **image compliance** with **running** and **target** version fields. Poll at minimum: `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` and `GET /dna/intent/api/v1/network-device-image-updates` so each event can carry `imageCompliance`, `runningVersion`, and `targetVersion` (golden). Authenticate with `POST /dna/system/api/v1/auth/token`. Map Catalyst Center’s compliance status values so `imageCompliance=NON_COMPLIANT` (or your deployment’s equivalent string) is normalized in Splunk. Optional: enrich with HEC if you emit compliance-change events in real time.

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 3600
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

## Detailed Implementation

Prerequisites
• Complete UC-5.13.55 so `cisco:dnac:swim` events exist with `imageCompliance`, `runningVersion`, and `targetVersion`.

Step 1 — Data fields
The TA does not populate golden-image compliance alone. The scripted input must call:
- `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` (per-device or bulk response depending on API version — normalize in the script)
- `GET /dna/intent/api/v1/network-device-image-updates` (running and target build)
Token: `POST /dna/system/api/v1/auth/token`.

Store credentials in Splunk’s credential store; set `sourcetype=cisco:dnac:swim` and `index=catalyst` in `inputs.conf` for the poller.

Step 2 — Search / alert

```spl
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT" | stats count as non_compliant_count by deviceFamily, runningVersion, targetVersion | eval version_gap=runningVersion." → ".targetVersion | sort -non_compliant_count
```

If your environment uses a different field name than `imageCompliance`, adjust the filter to match the normalized value for non-golden (for example `COMPLIANT` / `NON_COMPLIANT` strings from the API after mapping).

Step 3 — Validate
Compare a sample of non-compliant results to Catalyst Center SWIM/Compliance views for the same site or device list.

Step 4 — Operationalize
Schedule the search and route to SecOps/change management. Visualizations: table of gaps by family and versions, count of non-compliant devices, bar chart by `deviceFamily`.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT" | stats count as non_compliant_count by deviceFamily, runningVersion, targetVersion | eval version_gap=runningVersion." → ".targetVersion | sort -non_compliant_count
```

## Visualization

Table (deviceFamily, runningVersion, targetVersion, version_gap, non_compliant_count), single value (non-compliant device total), bar chart by deviceFamily.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
