<!-- AUTO-GENERATED from UC-5.13.59.json — DO NOT EDIT -->

---
id: "5.13.59"
title: "End-of-Life / End-of-Support Software Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.59 · End-of-Life / End-of-Support Software Detection

## Description

Identifies devices running software versions that have reached or are approaching end-of-life or end-of-support status, using Catalyst Center lifecycle data.

## Value

EoL/EoS software no longer receives security patches. Identifying affected devices enables proactive upgrade planning before vulnerabilities emerge.

## Implementation

Combine **SWIM inventory** (`GET /dna/intent/api/v1/network-device-image-updates` and `GET /dna/intent/api/v1/image/importation`) with **lifecycle** fields exposed for your Catalyst Center version (Cisco has published lifecycle/EoL context in product APIs; consult the current Intent API reference for the exact EoL endpoint in your release — for example endpoints under software/lifecycle that return `eolStatus`, `eolDate` tied to `runningVersion` / platform). Your poller for `sourcetype=cisco:dnac:swim` should output normalized fields: `eolStatus` (for example `END_OF_LIFE`, `END_OF_SUPPORT`, `END_OF_SW_MAINTENANCE`), `eolDate`, `deviceFamily`, `runningVersion`, `deviceName`.

**Scripted input:**

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 86400
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

Run daily (or weekly) to reduce API load; for critical fleets, add a more frequent EoL-only pass if the API supports a lightweight lifecycle query. Store credentials in Splunk’s credential store; use `POST /dna/system/api/v1/auth/token` for authentication.

## Detailed Implementation

Prerequisites
• UC-5.13.55 complete so SWIM inventory (versions per device) is in Splunk.

Step 1 — API strategy (Catalyst Center and lifecycle data)
• **Inventory:** `GET /dna/intent/api/v1/network-device-image-updates` (and device detail as needed) to resolve `deviceFamily` and `runningVersion`.
• **EoL attributes:** In your software train, use the published lifecycle/EOX-style Intent or documentation paths that return end dates for a product and image; merge in your script on (`deviceFamily` or PIDs) and `runningVersion`.
• **Auth:** `POST /dna/system/api/v1/auth/token` for each run or on token refresh. Emit normalized fields: `eolStatus`, `eolDate`, `deviceFamily`, `runningVersion`, `deviceName` into `cisco:dnac:swim` (or a dedicated `cisco:dnac:license`-style index if you split concerns).

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/collect_swim.py]
interval = 86400
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

Step 2 — Search

```spl
index=catalyst sourcetype="cisco:dnac:swim" (eolStatus="END_OF_LIFE" OR eolStatus="END_OF_SUPPORT" OR eolStatus="END_OF_SW_MAINTENANCE") | stats count as affected_devices values(runningVersion) as versions by deviceFamily, eolStatus, eolDate | sort eolDate
```

Step 3 — Validate
Compare a few rows to **Cisco.com** and **Catalyst Center** lifecycle or SWIM details for the same platform and version; drift usually means a stale merge table or a field rename after an API upgrade.

Step 4 — Operationalize
• Feed **capacity and refresh** backlogs; pair with **change** for upgrade waves. NIST-800-53 **SA-22** use: treat the list as candidates for replacement or upgrade, not an automatic sev-1 without business context.

Step 5 — Troubleshooting
• **Over-counts:** one device with multiple PIDs in the API may duplicate rows — dedupe on `deviceName`+`serialNumber` in the poller if available.
• **Under-counts:** script only daily — add a one-off run after a major EoL announcement. **No `eolStatus` in raw:** your merge step failed; log API responses in a dev forwarder and fix JSON paths.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" (eolStatus="END_OF_LIFE" OR eolStatus="END_OF_SUPPORT" OR eolStatus="END_OF_SW_MAINTENANCE") | stats count as affected_devices values(runningVersion) as versions by deviceFamily, eolStatus, eolDate | sort eolDate
```

## Visualization

Table (deviceFamily, eolStatus, eolDate, versions, affected_devices), timeline of upcoming EoL dates, single value of affected device count.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
