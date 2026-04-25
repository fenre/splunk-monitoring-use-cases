<!-- AUTO-GENERATED from UC-2.6.8.json — DO NOT EDIT -->

---
id: "2.6.8"
title: "Citrix Provisioning Services (PVS) vDisk Streaming Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.8 · Citrix Provisioning Services (PVS) vDisk Streaming Health

## Description

In PVS-provisioned environments, target devices boot and run entirely from vDisk images streamed over the network. If PVS streaming degrades — due to network congestion, PVS server overload, or storage bottlenecks — target devices experience slow boot times, application hangs, and blue screens. Monitoring PVS streaming health ensures the foundation of the VDI environment remains solid. Write cache exhaustion on target devices is particularly dangerous as it causes immediate device failure.

## Value

In PVS-provisioned environments, target devices boot and run entirely from vDisk images streamed over the network. If PVS streaming degrades — due to network congestion, PVS server overload, or storage bottlenecks — target devices experience slow boot times, application hangs, and blue screens. Monitoring PVS streaming health ensures the foundation of the VDI environment remains solid. Write cache exhaustion on target devices is particularly dangerous as it causes immediate device failure.

## Implementation

Deploy a Splunk Universal Forwarder on PVS servers and collect Stream Service event logs (enable event logging on each PVS server's Stream Service). Additionally, create a PowerShell scripted input using PVS MCLI commands (`Mcli-Get Device`, `Mcli-Get DiskVersion`) to collect target device status, boot times, retry counts, and write cache utilization. Alert on: boot times exceeding 120 seconds, stream retry counts above 50 (network/disk issues), write cache utilization above 80% (imminent exhaustion), or target devices dropping to inactive status. Monitor vDisk lock status to detect orphan locks preventing updates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on PVS servers, PowerShell scripted input via PVS MCLI.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:pvs:stream"` fields `pvs_server`, `target_device`, `vdisk_name`, `boot_time_sec`, `retries`, `cache_used_pct`, `cache_type`, `status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on PVS servers and collect Stream Service event logs (enable event logging on each PVS server's Stream Service). Additionally, create a PowerShell scripted input using PVS MCLI commands (`Mcli-Get Device`, `Mcli-Get DiskVersion`) to collect target device status, boot times, retry counts, and write cache utilization. Alert on: boot times exceeding 120 seconds, stream retry counts above 50 (network/disk issues), write cache utilization above 80% (imminent exhaus…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:pvs:stream"
| stats latest(status) as device_status, latest(boot_time_sec) as boot_sec, latest(retries) as retries, latest(cache_used_pct) as cache_pct by target_device, pvs_server, vdisk_name
| where device_status!="Active" OR boot_sec > 120 OR retries > 50 OR cache_pct > 80
| eval risk=case(cache_pct>90, "Critical-CacheExhaustion", device_status!="Active", "Offline", boot_sec>120, "SlowBoot", retries>50, "HighRetries", 1=1, "Warning")
| sort -cache_pct
| table target_device, pvs_server, vdisk_name, device_status, boot_sec, retries, cache_pct, risk
```

Understanding this SPL

**Citrix Provisioning Services (PVS) vDisk Streaming Health** — In PVS-provisioned environments, target devices boot and run entirely from vDisk images streamed over the network. If PVS streaming degrades — due to network congestion, PVS server overload, or storage bottlenecks — target devices experience slow boot times, application hangs, and blue screens. Monitoring PVS streaming health ensures the foundation of the VDI environment remains solid. Write cache exhaustion on target devices is particularly dangerous as it causes immediate…

Documented **Data sources**: `index=xd` `sourcetype="citrix:pvs:stream"` fields `pvs_server`, `target_device`, `vdisk_name`, `boot_time_sec`, `retries`, `cache_used_pct`, `cache_type`, `status`. **App/TA** (typical add-on context): Splunk Universal Forwarder on PVS servers, PowerShell scripted input via PVS MCLI. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:pvs:stream. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:pvs:stream". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by target_device, pvs_server, vdisk_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where device_status!="Active" OR boot_sec > 120 OR retries > 50 OR cache_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **risk** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix Provisioning Services (PVS) vDisk Streaming Health**): table target_device, pvs_server, vdisk_name, device_status, boot_sec, retries, cache_pct, risk

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (target devices with health metrics), Gauge (write cache utilization), Bar chart (boot times by PVS server).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=xd sourcetype="citrix:pvs:stream"
| stats latest(status) as device_status, latest(boot_time_sec) as boot_sec, latest(retries) as retries, latest(cache_used_pct) as cache_pct by target_device, pvs_server, vdisk_name
| where device_status!="Active" OR boot_sec > 120 OR retries > 50 OR cache_pct > 80
| eval risk=case(cache_pct>90, "Critical-CacheExhaustion", device_status!="Active", "Offline", boot_sec>120, "SlowBoot", retries>50, "HighRetries", 1=1, "Warning")
| sort -cache_pct
| table target_device, pvs_server, vdisk_name, device_status, boot_sec, retries, cache_pct, risk
```

## Visualization

Table (target devices with health metrics), Gauge (write cache utilization), Bar chart (boot times by PVS server).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
