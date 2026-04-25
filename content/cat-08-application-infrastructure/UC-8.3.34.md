<!-- AUTO-GENERATED from UC-8.3.34.json — DO NOT EDIT -->

---
id: "8.3.34"
title: "RabbitMQ Management Login and Access Denied Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.3.34 · RabbitMQ Management Login and Access Denied Events

## Description

Failed management logins and HTTP access denials expose credential stuffing, misconfigured monitoring accounts, or accidental exposure of the management port.

## Value

Provides an auditable trail for authentication abuse investigations and catches broken automation before it locks production accounts.

## Implementation

Forward `rabbit@*.log` from each cluster node. Extract `user` when present. Suppress known scanner subnets via a lookup. Alert on burst counts per 15 minutes; lower thresholds for management-tier hosts.

## SPL

```spl
index=messaging sourcetype="rabbitmq:log"
| search "access denied" OR "LOGIN refused" OR "failed to authenticate" OR "HTTP access denied"
| stats count by host, user
| where count >= 5
```

## Visualization

Timeline (failed logins), Table (host, user, count), Single value (failed attempts).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [RabbitMQ — Logging](https://www.rabbitmq.com/docs/logging)
- [RabbitMQ — Management Plugin](https://www.rabbitmq.com/docs/management)
