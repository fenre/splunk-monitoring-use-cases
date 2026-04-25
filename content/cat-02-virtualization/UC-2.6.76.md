<!-- AUTO-GENERATED from UC-2.6.76.json — DO NOT EDIT -->

---
id: "2.6.76"
title: "Citrix Client Ecosystem and Platform Distribution"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.76 · Citrix Client Ecosystem and Platform Distribution

## Description

Supported, patched clients are a common compliance and support requirement. A live distribution of Workspace app versions, client operating systems, thin-client firmware, and device classes gives IT and security teams a single place to see drift, plan upgrades, and retire unsupported platforms before they become an audit finding or a break-fix incident.

## Value

Supported, patched clients are a common compliance and support requirement. A live distribution of Workspace app versions, client operating systems, thin-client firmware, and device classes gives IT and security teams a single place to see drift, plan upgrades, and retire unsupported platforms before they become an audit finding or a break-fix incident.

## Implementation

Pull version fields on every new session or daily heartbeat, depending on the feed. Add lookups for LTS/allowed builds. Schedule monthly compliance PDF or CSV. Partner with end-user computing to nudge or block at the gateway for builds below a floor. For BYOD, show OS mix separately from corporate-managed endpoints.

## Detailed Implementation

Prerequisites
• `index=xd`; NTP on forwarders. In `props.conf` use `FIELDALIAS-` per sourcetype so `client_os`/`app_version`/`device_type` line up with the SPL. CSV lookup `approved_citrix_clients` with `os,min_build` for compliance joins.

Step 1 — Configure data collection
Lab: one Windows, macOS, thin client—document field names. If versions sit in `_raw`, add `REPORT-` in `transforms.conf` and wire from `props`. Extract firmware for Wyse/IGEL if present.

Step 2 — Create the search and report
Monthly saved search; add `| lookup approved_citrix_clients` and `eval noncom=if(ver<min_build,1,0)`. Panels: pie OS, bar top `ver`, table noncompliance by `os`. Optional alert: new `ver` in 7d.

Step 3 — Validate
Reconcile session totals to Director; `rare ver` to catch bad parsing; sample 5 hosts vs UEM.

Step 4 — Operationalize
Export to asset mgmt; enforce min client at NetScaler/Store at policy threshold. L2 if noncompliance > SLO; Security for audit. Re-tune after CWA LTS changes.

## SPL

```spl
index=xd (sourcetype="citrix:workspace:client" OR sourcetype="citrix:hdx:connect" OR sourcetype="citrix:broker:session") earliest=-7d
| eval os=coalesce(client_os, device_os, platform, "unknown"), ver=coalesce(workspace_version, app_version, client_version, "unknown"), dev=coalesce(device_type, endpoint_type, "unknown")
| bin _time span=1d
| stats count as sessions by _time, os, ver, dev
| sort -sessions
| head 200
```

## Visualization

Pie: OS; bar: Workspace app version; treemap: device class; line: unsupported share over time after campaigns.

## References

- [Citrix Workspace app — Lifecycle milestones](https://docs.citrix.com/en-us/citrix-workspace-app-for-windows/technical-overview-lifecycle-milestones.html)
