<!-- AUTO-GENERATED from UC-8.2.36.json — DO NOT EDIT -->

---
id: "8.2.36"
title: "RabbitMQ Disk Free Watermark Breach"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.36 · RabbitMQ Disk Free Watermark Breach

## Description

`disk_alarm` and comparing `disk_free` to the effective `disk_free_limit` predict publisher block and cluster instability before the filesystem is completely exhausted.

## Value

Protects message durability and cluster continuity by catching disk watermark violations that trigger broker flow control.

## Implementation

Poll `/api/nodes` every minute. Treat `disk_free` and `disk_free_limit` as the same units (bytes) from one snapshot. Alert immediately on `disk_alarm=true`. Warn when `disk_free` is still above the limit but within 25% of it (`disk_free < 1.25*disk_free_limit`). Include host filesystem metrics for root cause.

## SPL

```spl
index=messaging sourcetype="rabbitmq:node"
| where disk_alarm==true OR (isnotnull(disk_free) AND isnotnull(disk_free_limit) AND disk_free_limit>0 AND disk_free < disk_free_limit*1.25)
| table _time, name, disk_free, disk_free_limit, disk_alarm
```

## Visualization

Gauge (disk_free vs limit), Line chart (disk_free trend), Table (nodes breaching threshold).

## References

- [RabbitMQ — Disk Alarms](https://www.rabbitmq.com/docs/alarms#disk-alarm)
- [RabbitMQ — Disk Space](https://www.rabbitmq.com/docs/disk-space)
