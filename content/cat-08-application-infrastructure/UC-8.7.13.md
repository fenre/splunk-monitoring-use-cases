<!-- AUTO-GENERATED from UC-8.7.13.json — DO NOT EDIT -->

---
id: "8.7.13"
title: "RabbitMQ Administrative User Lifecycle Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.7.13 · RabbitMQ Administrative User Lifecycle Audit

## Description

Captures creation, deletion, and permission mutations for RabbitMQ identities—required evidence for access-governance programs.

## Value

Demonstrates that only approved admins changed messaging credentials and speeds investigations when new privileged tags appear.

## Implementation

Enable verbose management logging where safe. Ship logs to a restricted index. Join against ITSM tickets for automated compliance dashboards.

## SPL

```spl
index=messaging sourcetype="rabbitmq:log"
| search ("Adding user" OR "Deleting user" OR "user '" OR "Setting permissions" OR "Clearing permissions" OR "administrator")
| table _time, host, _raw
```

## Visualization

Table (admin actions), Timeline (user lifecycle), Single value (changes per week).

## References

- [RabbitMQ — Access Control](https://www.rabbitmq.com/docs/access-control)
- [RabbitMQ — Logging](https://www.rabbitmq.com/docs/logging)
