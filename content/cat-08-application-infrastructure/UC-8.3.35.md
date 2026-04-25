<!-- AUTO-GENERATED from UC-8.3.35.json — DO NOT EDIT -->

---
id: "8.3.35"
title: "ActiveMQ JAAS Authentication Failure Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.35 · ActiveMQ JAAS Authentication Failure Monitoring

## Description

JAAS and simple authentication failures indicate stolen credentials rolling, LDAP outages, or clients pinned to the wrong broker user.

## Value

Surfaces authentication outages that manifest as mysterious client disconnects and supports security investigations into credential abuse.

## Implementation

Ensure `login.config` failures are logged at WARN/ERROR. Mask passwords in raw events. Correlate spikes with LDAP/Kerberos incidents. Page SecOps when counts exceed baseline during business hours.

## SPL

```spl
index=messaging sourcetype="activemq:log"
| search "SecurityException" OR "authentication failed" OR ("User name" AND "invalid")
| rex field=_raw "user\s+(?<amq_user>\S+)"
| timechart span=15m count by host
```

## Visualization

Line chart (failures by broker), Table (sample events), Single value (failure count).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
- [Apache ActiveMQ — Security](https://activemq.apache.org/components/classic/documentation/security)
- [Apache ActiveMQ — Broker Configuration](https://activemq.apache.org/components/classic/documentation/broker-configuration)
