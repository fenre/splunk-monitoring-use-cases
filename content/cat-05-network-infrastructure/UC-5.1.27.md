<!-- AUTO-GENERATED from UC-5.1.27.json — DO NOT EDIT -->

---
id: "5.1.27"
title: "Interface Error Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.27 · Interface Error Rate Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault

*We help you know early when something looks wrong with interface error rate trending so the team can act before it grows into a bigger outage.*

---

## Description

CRC, runts, giants, input/output errors as rate over time.

## Value

Network engineers analyze 30-day interface error rate trends to detect gradually degrading links and schedule proactive cable or optic replacement before complete failure.

## Implementation

Poll IF-MIB (ifInErrors, ifOutErrors) and EtherLike-MIB (dot3StatsFCSErrors) every 300s. Use streamstats for delta calculation. Alert when error rate exceeds threshold (e.g., >1/min on uplinks). Exclude admin-down interfaces.

## Detailed Implementation

### Prerequisites
* Interface error rate trending data from SNMP. Data in `index=network` with SNMP counter data. Extends UC-5.1.2 with long-term trending and predictive analysis.
* Error rate trending: tracks error counter growth over days/weeks to identify slowly degrading links before they fail. A cable or SFP developing marginal performance may show gradually increasing error rates.

### Step 1 — - Configure data collection
```
# Same SNMP polling as UC-5.1.2
# Ensure historical data retention > 30 days for trending
# Summary indexing recommended for long-term analysis
```
Verify:
```spl
index=network earliest=-30d
| eval in_errors=tonumber(coalesce(ifInErrors, input_errors))
| where isnotnull(in_errors)
| stats latest(in_errors) by host, ifName
```

### Step 2 — - Create the search and alert

**Primary search -- Error rate trend analysis (30-day):**
```spl
index=network earliest=-30d
| eval in_errors=tonumber(coalesce(ifInErrors, input_errors, in_errors))
| eval out_errors=tonumber(coalesce(ifOutErrors, output_errors, out_errors))
| eval interface=coalesce(ifName, interface, port)
| eval device=coalesce(host, device_name)
| where isnotnull(in_errors) OR isnotnull(out_errors)
| bin _time span=1d
| stats latest(in_errors) as daily_in_err latest(out_errors) as daily_out_err by _time, device, interface
| sort device, interface, _time
| streamstats current=f last(daily_in_err) as prev_in last(daily_out_err) as prev_out by device, interface
| eval delta_in=daily_in_err - prev_in
| eval delta_out=daily_out_err - prev_out
| eval daily_total=max(delta_in, 0) + max(delta_out, 0)
| where daily_total > 0
| stats sum(daily_total) as total_errors avg(daily_total) as avg_daily_errors max(daily_total) as peak_daily_errors count as days_with_errors by device, interface
| eval trend=case(
    days_with_errors > 20 AND avg_daily_errors > 10, "DEGRADING -- consistent daily errors",
    peak_daily_errors > 1000, "SPIKE -- single day with >1000 errors",
    total_errors > 5000, "ACCUMULATED -- high total error count",
    1==1, "STABLE")
| where trend != "STABLE"
| eval severity=case(
    trend="DEGRADING", "WARNING -- link is degrading, plan replacement",
    trend="SPIKE", "INFO -- investigate spike cause",
    trend="ACCUMULATED", "INFO -- high cumulative errors",
    1==1, "INFO")
| sort severity, -total_errors
```

### Step 3 — - Validate
(a) CLI: `show interface <intf>` -- check current error counters.
(b) CLI: `show interface transceiver` -- check optic power level trends.
(c) Correlate with CRC error trending (UC-5.1.21).

### Step 4 — - Operationalize
Dashboard ("Network -- Error Rate Trends"):
* Row 1 -- Single-value: "Degrading links", "Interfaces with errors (30d)".
* Row 2 -- Error rate trend timechart.

Alert: Warning (consistent daily errors for >20 days): schedule cable/optic replacement.

### Step 5 — - Troubleshooting

* **Gradually increasing errors** -- Physical layer degradation in progress. Schedule cable/optic replacement during next maintenance window. Don't wait for failure.

* **Error spikes correlating with time of day** -- May indicate congestion-related discards (not physical). Correlate with interface utilization (UC-5.1.3).

* **Errors on multiple interfaces same device** -- May indicate device hardware issue (linecard, backplane) rather than individual port/cable. Investigate chassis health.

## SPL

```spl
index=network sourcetype=snmp:interface
| streamstats current=f last(ifInErrors) as prev_in, last(ifOutErrors) as prev_out, last(_time) as prev_time by host, ifDescr
| eval delta_in=ifInErrors-coalesce(prev_in,0), delta_out=ifOutErrors-coalesce(prev_out,0)
| eval interval_sec=_time-prev_time | where interval_sec>0 AND interval_sec<900
| eval in_err_rate=round(delta_in/interval_sec*60,2), out_err_rate=round(delta_out/interval_sec*60,2)
| where in_err_rate>0 OR out_err_rate>0
| timechart span=5m avg(in_err_rate) as in_errors_per_min, avg(out_err_rate) as out_errors_per_min by host
```

## Visualization

Line chart (error rate over time), Table (host, interface, rate), Heatmap.

## Known False Positives

Brief error increments during transceiver replacement, software upgrades, or known-noisy access segments can look like a fault. Baseline by interface role before paging.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
