<!-- AUTO-GENERATED from UC-7.2.28.json — DO NOT EDIT -->

---
id: "7.2.28"
title: "MySQL Group Replication Member Not ONLINE"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.28 · MySQL Group Replication Member Not ONLINE

## Description

Group Replication requires members to reach ONLINE state for write certification. MEMBER_STATE in ERROR, RECOVERING, or OFFLINE is a standard failover and incident trigger.

## Value

Prevents split writes and certification failures by catching group members that have left the quorum or stopped applying the relay log.

## Implementation

Schedule a DB Connect query to replication_group_members on each instance. Include MEMBER_ROLE to distinguish PRIMARY/SECONDARY. Alert on any non-ONLINE state outside maintenance. Correlate with network and disk on the affected host.

## SPL

```spl
index=database sourcetype="mysql:gr_member"
| where MEMBER_STATE!="ONLINE"
| stats latest(MEMBER_STATE) as state latest(MEMBER_HOST) as member_host by CHANNEL_NAME, GROUP_NAME, host
| sort state
```

## Visualization

Table (group, member, state, role), Timeline (state transitions), Single value (bad members).

## References

- [MySQL Group Replication — Group Member States](https://dev.mysql.com/doc/refman/8.0/en/group-replication-group-members.html)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
