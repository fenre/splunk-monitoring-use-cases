<!-- AUTO-GENERATED from UC-7.3.22.json — DO NOT EDIT -->

---
id: "7.3.22"
title: "Redis ACL and AUTH Denial Events"
status: "draft"
criticality: "medium"
splunkPillar: "Security"
---

# UC-7.3.22 · Redis ACL and AUTH Denial Events

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Status:** Draft

*We watch for repeated or suspicious sign-in activity on our databases so we can catch brute-force and misconfiguration before they become account takeovers.*

---

## Description

ACL denials and failed authentications surface privilege misuse, broken automation, or password-guessing against Redis—especially after enabling ACL users in production.

## Value

Closes the gap between open Redis instances and least-privilege enforcement by making denials visible in Splunk.

## Implementation

Enable ACL LOG on each primary; ship JSON lines with username, reason, client info. If only file logs exist, use sourcetype redis:log with transforms. Redact key names where sensitive.

## SPL

```spl
index=middleware sourcetype="redis:acl_log"
| where reason IN ("auth","deny-command","key") OR match(_raw,"denied")
| bin _time span=1h
| stats count as events dc(username) as users dc(client_info) as clients by host, _time
| where events > 10
```

## Visualization

Table (user, reason, count), Timeline (denials), Top (client_info).

## Known False Positives

Planned access reviews, recertification, break-glass accounts, and vendor maintenance can emit privilege- or access-change events that match the rule but are already approved; require a change ticket for context.

## References

- [Redis ACL LOG](https://redis.io/docs/latest/commands/acl-log/)
