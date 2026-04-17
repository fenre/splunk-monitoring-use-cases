# 1. Example Category

## 1.1 Example Subcategory

### UC-1.1.1 · Failed login spike
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Value:** Catches credential-stuffing before the attacker pivots.
- **Data Sources:** auth logs
- **Query:** see below

```
sourcetype=auth
| stats count by user
| where count > 10
```

- **Implementation:** deploy as a saved search with a 5-minute schedule.
- **Visualization:** table.

---

### UC-1.1.2 · Disk usage nearing capacity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Value:** Pre-emptive capacity alert on filesystems that routinely fill overnight.
- **Data Sources:** host metrics
- **Query:** see below

```
metric_name=system.disk.used_pct
| stats avg(_value) by host
| where avg > 85
```

- **Implementation:** metric alert at warning (85 %) and critical (95 %).
- **Visualization:** single value with threshold.
