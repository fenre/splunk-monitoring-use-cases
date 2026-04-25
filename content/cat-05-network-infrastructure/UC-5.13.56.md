<!-- AUTO-GENERATED from UC-5.13.56.json — DO NOT EDIT -->

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

Step 1 — Data fields (Catalyst Center SWIM / compliance)
The base Cisco Catalyst TA may not cover every field; a scripted input must call:
- `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` (normalize the API’s compliance strings to `imageCompliance` in Splunk)
- `GET /dna/intent/api/v1/network-device-image-updates` (running and target or golden assignment)
Authenticate with `POST /dna/system/api/v1/auth/token` and pass `X-Auth-Token` on subsequent calls.

Store credentials in Splunk’s credential store; set `sourcetype=cisco:dnac:swim` and `index=catalyst` in `inputs.conf` for the poller.

Step 2 — Search / alert

```spl
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT" | stats count as non_compliant_count by deviceFamily, runningVersion, targetVersion | eval version_gap=if(isnotnull(runningVersion) AND isnotnull(targetVersion), tostring(runningVersion)." → ".tostring(targetVersion), null()) | sort -non_compliant_count
```

If your environment uses a different field name than `imageCompliance`, adjust the filter to the strings your poller normalizes (for example `COMPLIANT` / `NON_COMPLIANT`).

Step 3 — Validate
• Compare a sample to **Catalyst Center > SWIM** and **Compliance** for the same device set; a mismatch usually means a lagging poll or a different golden assignment scope (site vs global).

Step 4 — Operationalize
• Page **SecOps and change** on sustained non-compliance; attach **Device 360** from Catalyst for remediation.

Step 5 — Troubleshooting
• **Zero results when the UI shows drift:** the API user may not see all sites in your virtual domain, or the compliance endpoint returned empty — broaden scope in Catalyst first.
• **Noise during upgrade waves:** add a **summary** of `upgradeStatus` or exclude maintenance **tags/lookups** for known canary groups.
• **All devices non-compliant after golden change:** expect a **burst** until the next SWIM run completes — widen the alert time window, not the blast radius, before tuning thresholds.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT" | stats count as non_compliant_count by deviceFamily, runningVersion, targetVersion | eval version_gap=if(isnotnull(runningVersion) AND isnotnull(targetVersion), tostring(runningVersion)." → ".tostring(targetVersion), null()) | sort -non_compliant_count
```

## Visualization

Table (deviceFamily, runningVersion, targetVersion, version_gap, non_compliant_count), single value (non-compliant device total), bar chart by deviceFamily.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
