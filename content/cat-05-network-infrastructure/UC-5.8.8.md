<!-- AUTO-GENERATED from UC-5.8.8.json — DO NOT EDIT -->

---
id: "5.8.8"
title: "SNMP Polling Gap Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.8 · SNMP Polling Gap Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We notice when regular SNMP checks stop showing up, which usually means a password, path, or agent problem before the graphs go blank in a real incident.*

---

## Description

Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.

## Value

Network operations teams detect SNMP polling gaps that create silent monitoring blind spots, ensuring continuous visibility into all monitored network devices and identifying polling infrastructure failures.

## Implementation

Track SNMP data arrival per device using `tstats`. Compare expected vs. actual poll count. Alert when gap exceeds 20%. Investigate SNMP community/credential issues.

## Detailed Implementation

### Prerequisites
- SNMP polling infrastructure sending device metrics to Splunk at regular intervals. Common approaches: (1) SC4SNMP polling OIDs and sending via HEC, (2) Telegraf SNMP plugin → Splunk HEC, (3) custom scripts polling via pysnmp and forwarding to Splunk. Data in `index=snmp` (or `index=network`) with `sourcetype=sc4snmp:metrics` or `sourcetype=snmp:poll`.
- Key fields: `host` (polled device), `oid` (polled OID), `value`, `poll_time`, `community`/`context_name`. Expected polling interval: typically 5 minutes (300s) for most OIDs, 1 minute for critical metrics.
- SNMP polling gaps indicate: (1) the polled device is unreachable (down, network issue), (2) the polling infrastructure itself has a problem (SC4SNMP down, credential issue), (3) SNMP timeout (device overloaded, slow response). Gaps in polling = gaps in monitoring visibility.

### Step 1 — Configure data collection
Verify polling data:
```spl
index=snmp (sourcetype="sc4snmp:metrics" OR sourcetype="snmp:poll") earliest=-15m
| stats count by host
| sort -count
```
Each host should show a consistent count proportional to the polling interval and number of OIDs.

### Step 2 — Create the search and alert

**Primary search — Polling gap detection:**
```spl
index=snmp (sourcetype="sc4snmp:metrics" OR sourcetype="snmp:poll") earliest=-2h
| bin _time span=5m
| stats count as polls dc(oid) as oids_polled by _time, host
| streamstats window=2 current=t range(polls) as poll_variance by host
| eventstats avg(polls) as avg_polls by host
| eval expected_polls=avg_polls
| eval gap_detected=if(polls < expected_polls * 0.3, 1, 0)
| where gap_detected=1
| lookup snmp_device_inventory.csv src as host OUTPUT hostname device_type location tier
| eval device_label=coalesce(hostname, host)
| table _time, device_label, device_type, location, tier, polls, expected_polls
| sort tier, -_time
```

#### Understanding this SPL: SNMP polling gaps are silent failures — if the poller can't reach a device, no alert fires (unlike traps which are device-initiated). This creates a dangerous monitoring blind spot. The search establishes a per-device polling baseline and flags any 5-minute window where actual polls drop below 30% of expected. A complete gap (polls=0) means total loss of visibility for that device.

**Polling infrastructure health:**
```spl
index=snmp (sourcetype="sc4snmp:metrics" OR sourcetype="snmp:poll") earliest=-1h
| bin _time span=5m
| stats dc(host) as devices_polled count as total_polls by _time
| eventstats avg(devices_polled) as avg_devices
| eval device_coverage_pct=round(100*devices_polled/avg_devices, 1)
| where device_coverage_pct < 90
```

**SNMP timeout tracking:**
```spl
index=_internal sourcetype=splunkd "snmp" ("timeout" OR "error" OR "unreachable") earliest=-4h
| stats count by host, log_level, message
| sort -count
```

### Step 3 — Validate
(a) Shut down SNMP on a test device (`no snmp-server`) and verify a polling gap appears in Splunk within 2 polling intervals.
(b) Verify polling baseline: for a device polled every 5 minutes with 10 OIDs, you should see ~10 events per 5-minute window.
(c) Cross-check with the SNMP polling tool's own health metrics (SC4SNMP stats endpoint, Telegraf internal metrics).

### Step 4 — Operationalize
Dashboard ("SNMP Polling Health"):
- Row 1 — Single-value tiles: "Devices polled (15m)", "Polling gaps detected", "Device coverage %", "SNMP timeouts".
- Row 2 — Polling gap table: device, type, location, tier, last poll time, gap duration.
- Row 3 — Polling coverage trending: devices polled per 5-minute window over 24h.
- Row 4 — SNMP timeout tracking from internal logs.

Alerting:
- Critical (Tier1 device polling gap > 15 minutes): loss of monitoring visibility for critical device.
- High (device coverage drops below 80%): polling infrastructure issue.
- Warning (any polling gap > 10 minutes): investigate device or network reachability.

### Step 5 — Troubleshooting

- **All devices show polling gaps simultaneously** — The polling infrastructure itself is down (SC4SNMP container crashed, Telegraf stopped). Check the poller's own health first.

- **Single device has gaps but is pingable** — SNMP may be disabled or the community string changed on the device. Verify with: `snmpwalk -v 2c -c <community> <device_ip> sysDescr`.

- **Intermittent gaps correlating with time of day** — The polling infrastructure may be overloaded during peak hours (too many OIDs to poll within the interval). Reduce OID count or add polling capacity.

## SPL

```spl
| tstats count where index=network sourcetype="snmp:*" by host, sourcetype, _time span=10m
| stats range(_time) as time_range, count as poll_count by host, sourcetype
| eval expected_polls=round(time_range/300,0)
| eval gap_pct=round((1-poll_count/expected_polls)*100,1)
| where gap_pct > 20 | sort -gap_pct
```

## Visualization

Table (device, expected, actual, gap %), Single value (devices with gaps), Heatmap.

## Known False Positives

Maintenance silences, discovery pauses, and metric-store lag can under-count expected polls; verify the poller, not just Splunk, when gaps appear.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
