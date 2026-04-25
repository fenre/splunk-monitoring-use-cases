<!-- AUTO-GENERATED from UC-2.6.52.json — DO NOT EDIT -->

---
id: "2.6.52"
title: "VDA Software and OS Version Lifecycle Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.52 · VDA Software and OS Version Lifecycle Tracking

## Description

Citrix releases new VDA builds regularly. Microsoft retires Windows 10/11 builds on a predictable schedule. Running an inventory of `vda_version` and `os_build` per session host supports compliance with internal standard images, tells you which catalogs are still on long-term servicing versus current channel, and highlights stragglers before support tickets or Citrix Cloud health checks flag them. Feed the same list into patch windows, upgrade rings, and golden-image promotion. A simple scheduled report that lists any host not on the approved pair is enough for many organizations; add lookups for end-of-life dates you maintain in a CSV.

## Value

Citrix releases new VDA builds regularly. Microsoft retires Windows 10/11 builds on a predictable schedule. Running an inventory of `vda_version` and `os_build` per session host supports compliance with internal standard images, tells you which catalogs are still on long-term servicing versus current channel, and highlights stragglers before support tickets or Citrix Cloud health checks flag them. Feed the same list into patch windows, upgrade rings, and golden-image promotion. A simple scheduled report that lists any host not on the approved pair is enough for many organizations; add lookups for end-of-life dates you maintain in a CSV.

## Implementation

Emit a heartbeat or registration event at least daily that includes VDA and OS build. Create `lookup citrix_supported_vda.csv` with columns `vda_version`, `supported`, `eol_date`. Version the lookup with change control. Schedule the report weekly; alert only for rows on the critical path (for example, Internet-facing or regulated worker pools). Combine with your configuration management database to auto-close when a host is decommissioned.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-XD7-VDA` or equivalent log path; optional uberAgent for OS fields.
• Ensure the following data sources are available: `citrix:vda:events` with version fields; optional Windows Application log for installs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize `vda_version` to `major.minor.build` strings. If multiple events per day exist, take `latest` by machine. Store the supported-version lookup in `lookups/citrix_supported_vda.csv` and reference it in `transforms.conf`.

Step 2 — Create the search and alert
If you have not yet built the lookup, start with a simple distribution report:

```spl
index=xd sourcetype="citrix:vda:events"
| eval vda_ver=coalesce(vda_version, agent_version, "unknown")
| stats count by vda_ver
| sort - count
```

**VDA Software and OS Version Lifecycle Tracking** — Add the `lookup` and `where` clauses from the primary SPL once the CSV exists. Do not alert on lab or test indexes in production schedules.

Step 3 — Validate
Compare counts to the Citrix admin console machine list. Reconcile differences with powered-off or maintenance machines.

Step 4 — Operationalize
Attach the report to monthly CAB. When a new LTSR is adopted, update the lookup first, then sweep machines in ring order.

## SPL

```spl
index=xd sourcetype="citrix:vda:events" (event_type="AgentInfo" OR event_type="Registration" OR event_type="Heartbeat")
| eval vda_ver=coalesce(vda_version, agent_version, VdaVersion, "unknown")
| eval os_b=coalesce(os_build, windows_build, OSBuild, "unknown")
| eval machine=coalesce(machine_name, host, "Unknown")
| where vda_ver!="unknown"
| stats dc(machine) as host_count, max(_time) as last_seen by vda_ver, os_b
| rename vda_ver as vda_version, os_b as os_build_value
| sort vda_version, os_build_value
| table vda_version, os_build_value, host_count, last_seen
```

## Visualization

Bar chart of hosts by VDA version, table of unsupported rows, treemap by catalog if you join a lookup from machine to catalog.

## References

- [Citrix Virtual Apps and Desktops — product matrix and lifecycle](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/product-lifecycle.html)
- [Current release VDA requirements](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/system-requirements.html)
