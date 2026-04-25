<!-- AUTO-GENERATED from UC-7.1.74.json — DO NOT EDIT -->

---
id: "7.1.74"
title: "Snowflake Warehouse Auto-Suspend and Auto-Resume Event Frequency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.74 · Snowflake Warehouse Auto-Suspend and Auto-Resume Event Frequency

## Description

Chronic auto-resume thrash burns credits and hides real workload signals, while a sudden drop in suspend/resume activity can mean policies were widened and spend is drifting. Tracking event frequency per warehouse makes finance and platform conversations data-driven.

## Value

Controls Snowflake runaway spend and catches misconfigured auto-suspend intervals before invoices spike.

## Implementation

Enable the warehouse events input in the add-on’s `inputs.conf` (respect ACCOUNT_USAGE latency). Normalize `EVENT_NAME` casing. Build a 30-day median baseline per warehouse. Exclude dev sandboxes via lookup. Alert on thrash (high count) and on zero events for 24h on warehouses expected to idle.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:warehouse_events"
| eval ev=upper(coalesce(EVENT_NAME, event_name))
| where match(ev,"SUSPEND") OR match(ev,"RESUME")
| bin _time span=1h
| stats count as events dc(ev) as event_types by WAREHOUSE_NAME, _time
| eventstats median(events) as med_events by WAREHOUSE_NAME
| where events > med_events*3 AND events > 20
```

## Visualization

Line chart (events by warehouse), Histogram (hour-of-day thrash).

## References

- [Snowflake WAREHOUSE_EVENTS_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_events_history)
- [Splunk Add-on for Snowflake](https://splunkbase.splunk.com/app/5390)
