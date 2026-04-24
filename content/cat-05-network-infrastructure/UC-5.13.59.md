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

Step 1 — API strategy
- Base inventory: `GET /dna/intent/api/v1/network-device-image-updates` and related device detail if needed to resolve `deviceFamily` and `runningVersion`.
- EoL attributes: In your API release, use the published lifecycle/EOX Intent paths that return end-of-life and support end dates for a given product/software combination; merge results in the script on (`deviceFamily` or PIDs) and `runningVersion`.
- Auth: `POST /dna/system/api/v1/auth/token` for every job or on token refresh.

The script should emit a consistent `eolStatus` vocabulary matching your SPL: `END_OF_LIFE`, `END_OF_SUPPORT`, or `END_OF_SW_MAINTENANCE` (or map Cisco’s values to these).

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
Compare a few rows to Cisco.com / Catalyst Center lifecycle information for the same product version.

Step 4 — Operationalize
Feed capacity planning; pair with change management for upgrade waves. NIST-800-53 SA-22 alignment: treat results as a backlog of unsupported components until remediated.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" (eolStatus="END_OF_LIFE" OR eolStatus="END_OF_SUPPORT" OR eolStatus="END_OF_SW_MAINTENANCE") | stats count as affected_devices values(runningVersion) as versions by deviceFamily, eolStatus, eolDate | sort eolDate
```

## Visualization

Table (deviceFamily, eolStatus, eolDate, versions, affected_devices), timeline of upcoming EoL dates, single value of affected device count.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
