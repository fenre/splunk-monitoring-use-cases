<!-- AUTO-GENERATED from UC-2.6.46.json — DO NOT EDIT -->

---
id: "2.6.46"
title: "Citrix Monitor OData Load Index Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.46 · Citrix Monitor OData Load Index Trending

## Description

The Citrix load evaluator reports a load index (0 to 10,000) that combines session count, application load, and other factors per machine. Trending that index at the machine and delivery group level shows who is overassigned before new sessions fail, validates load-balancing policy effectiveness, and helps capacity planning. Spikes in average or peak load index that persist across hours point to too few hosts, heavy users, or runaway published applications, not one-off blips. Pair this with session counts to separate genuine saturation from a broken load metric source.

## Value

The Citrix load evaluator reports a load index (0 to 10,000) that combines session count, application load, and other factors per machine. Trending that index at the machine and delivery group level shows who is overassigned before new sessions fail, validates load-balancing policy effectiveness, and helps capacity planning. Spikes in average or peak load index that persist across hours point to too few hosts, heavy users, or runaway published applications, not one-off blips. Pair this with session counts to separate genuine saturation from a broken load metric source.

## Implementation

Stand up a scheduled OData poll with authentication to the on-premises Monitor service and persist JSON into `citrix:monitor:odata` with a stable `odata_resource` field. Map OData property names to lowercase Splunk fields for `LoadIndex` and `MachineName`. Create hourly or fifteen-minute baselines. Alert when peak load index exceeds 5,000 (tunable) for any machine for more than two consecutive samples, or when the delivery group average crosses your internal green/yellow line. Onboard a dashboard of top ten machines by load index with drilldowns to process and session data.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: A Citrix Monitor OData poller (scripted or third-party) that writes to `index=xd` with `sourcetype="citrix:monitor:odata"`.
• Ensure the following data sources are available: OData `Machines` and optionally `Sessions` for joins; service account with least privilege.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule polls at least every five minutes. Use incremental queries if the API supports it. Add credentials in `password.conf` and reference a modular or scripted input. Normalize field names. Log HTTP failures from the poller to a separate index so you can alert on collector outages separately from high load index.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; fix `coalesce` field list to the names your poller actually emits):

```spl
index=xd sourcetype="citrix:monitor:odata" odata_resource="Machines"
| eval li=tonumber(coalesce(load_index, LoadIndex, 0))
| eval machine=coalesce(machine_name, MachineName, host)
| eval dg=coalesce(delivery_group, DesktopGroupName, "Unknown")
| bin _time span=1h
| stats latest(li) as load_index, max(li) as peak_li by machine, dg, _time
| where peak_li > 5000
```

**Citrix Monitor OData Load Index Trending** — The `5,000` cut is a starting point: busy single-session physical hosts may be lower. For multi-session, lower thresholds are common. Add `streamstats` to require sustained elevation before alerting.

Step 3 — Validate
Compare a known busy host’s on-console load index in Citrix against the poll. If deltas appear, check clock skew, poll interval, and whether you are using cached OData responses.

Step 4 — Operationalize
Tie the alert to capacity reviews: new hardware, more instances, or session limits per user. Revisit delivery group power management so hosts come online before load index pegs at shift start.

## SPL

```spl
index=xd sourcetype="citrix:monitor:odata" odata_resource="Machines"
| eval li=tonumber(coalesce(load_index, LoadIndex, 0))
| eval machine=coalesce(machine_name, MachineName, host)
| eval dg=coalesce(delivery_group, DesktopGroupName, "Unknown")
| where li >= 0
| bin _time span=1h
| stats latest(li) as load_index, max(li) as peak_li by machine, dg, _time
| where peak_li > 5000
| timechart max(peak_li) by dg
```

## Visualization

Line chart of max load index by delivery group, heatmap of machines over time, table of current worst offenders with load index and session count if joined.

## References

- [Monitor Service and OData in CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/monitor-service.html)
- [Citrix — load management overview](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-load-balancing.html)
