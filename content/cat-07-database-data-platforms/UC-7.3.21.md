<!-- AUTO-GENERATED from UC-7.3.21.json — DO NOT EDIT -->

---
id: "7.3.21"
title: "MongoDB Authentication Failure Monitoring"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.3.21 · MongoDB Authentication Failure Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Draft

*We watch for repeated or suspicious sign-in activity on our databases so we can catch brute-force and misconfiguration before they become account takeovers.*

---

## Description

Failed authentication events in MongoDB audit logs indicate credential attacks or misconfigured clients. Teams monitor these alongside Atlas authentication alerts.

## Value

Improves detection of database credential abuse in self-managed and Atlas-backed MongoDB deployments ingested into Splunk.

## Implementation

Normalize audit schema (Atlas vs on-prem). Map result codes: success vs failure per vendor docs. Enrich addr with threat intel if permitted. Tune thresholds for CI/CD service accounts.

## SPL

```spl
index=database sourcetype="mongodb:audit"
| search "Authentication failed" OR result="fail" OR errCode=18
| bin _time span=1h
| stats count as failures dc(user) as users dc(ip) as sources by host, _time
| where failures > 30
```

## Visualization

Table (user, sources, count), Timeline (failures), Map (addr).

## Known False Positives

Planned access reviews, recertification, break-glass accounts, and vendor maintenance can emit privilege- or access-change events that match the rule but are already approved; require a change ticket for context.

## References

- [MongoDB Auditing](https://www.mongodb.com/docs/manual/administration/auditing/)
