---
id: "2.5.7"
title: "IGEL Device Resource Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.5.7 · IGEL Device Resource Utilization

## Description

IGEL thin clients have constrained hardware resources (CPU, memory, flash storage). Monitoring resource utilization across the fleet identifies devices that are under-provisioned for their workload, approaching flash storage capacity, or experiencing performance issues that degrade the VDI user experience. Proactive capacity trending prevents user complaints and supports hardware refresh planning.

## Value

IGEL thin clients have constrained hardware resources (CPU, memory, flash storage). Monitoring resource utilization across the fleet identifies devices that are under-provisioned for their workload, approaching flash storage capacity, or experiencing performance issues that degrade the VDI user experience. Proactive capacity trending prevents user complaints and supports hardware refresh planning.

## Implementation

Poll `GET /v3/thinclients?facets=details` to retrieve hardware specifications for each device. The API returns CPU speed, memory size, flash storage, battery level (mobile devices), and network speed. Index these as inventory events with the device `unitID` as a unique key. Build a fleet hardware profile to identify under-provisioned devices. Alert when battery level drops below 20% on mobile IGEL devices. Use trending to forecast flash storage exhaustion. Cross-reference hardware specs against minimum requirements for the VDI workload (e.g., Citrix Workspace App, VMware Horizon Client).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`).
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `cpu_speed_mhz`, `mem_size_mb`, `flash_size_mb`, `battery_level`, `network_speed`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET /v3/thinclients?facets=details` to retrieve hardware specifications for each device. The API returns CPU speed, memory size, flash storage, battery level (mobile devices), and network speed. Index these as inventory events with the device `unitID` as a unique key. Build a fleet hardware profile to identify under-provisioned devices. Alert when battery level drops below 20% on mobile IGEL devices. Use trending to forecast flash storage exhaustion. Cross-reference hardware specs against …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(cpu_speed_mhz) as cpu_mhz, latest(mem_size_mb) as mem_mb, latest(flash_size_mb) as flash_mb, latest(battery_level) as battery, latest(device_name) as device_name by unit_id
| eval mem_tier=case(mem_mb<2048, "Under 2GB", mem_mb<4096, "2-4GB", mem_mb<8192, "4-8GB", 1=1, "8GB+")
| eval flash_tier=case(flash_mb<4096, "Under 4GB", flash_mb<8192, "4-8GB", 1=1, "8GB+")
| stats count as device_count by mem_tier, flash_tier
| sort mem_tier, flash_tier
| table mem_tier, flash_tier, device_count
```

Understanding this SPL

**IGEL Device Resource Utilization** — IGEL thin clients have constrained hardware resources (CPU, memory, flash storage). Monitoring resource utilization across the fleet identifies devices that are under-provisioned for their workload, approaching flash storage capacity, or experiencing performance issues that degrade the VDI user experience. Proactive capacity trending prevents user complaints and supports hardware refresh planning.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `cpu_speed_mhz`, `mem_size_mb`, `flash_size_mb`, `battery_level`, `network_speed`. **App/TA** (typical add-on context): Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:inventory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by unit_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **mem_tier** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **flash_tier** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by mem_tier, flash_tier** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **IGEL Device Resource Utilization**): table mem_tier, flash_tier, device_count


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (memory tier x flash tier), Bar chart (devices by hardware class), Table (devices below minimum specs).

## SPL

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(cpu_speed_mhz) as cpu_mhz, latest(mem_size_mb) as mem_mb, latest(flash_size_mb) as flash_mb, latest(battery_level) as battery, latest(device_name) as device_name by unit_id
| eval mem_tier=case(mem_mb<2048, "Under 2GB", mem_mb<4096, "2-4GB", mem_mb<8192, "4-8GB", 1=1, "8GB+")
| eval flash_tier=case(flash_mb<4096, "Under 4GB", flash_mb<8192, "4-8GB", 1=1, "8GB+")
| stats count as device_count by mem_tier, flash_tier
| sort mem_tier, flash_tier
| table mem_tier, flash_tier, device_count
```

## Visualization

Heatmap (memory tier x flash tier), Bar chart (devices by hardware class), Table (devices below minimum specs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
