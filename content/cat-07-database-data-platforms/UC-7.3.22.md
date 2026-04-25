<!-- AUTO-GENERATED from UC-7.3.22.json — DO NOT EDIT -->

---
id: "7.3.22"
title: "Redis ACL and AUTH Denial Events"
criticality: "medium"
splunkPillar: "Security"
---

# UC-7.3.22 · Redis ACL and AUTH Denial Events

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

## References

- [Redis ACL LOG](https://redis.io/docs/latest/commands/acl-log/)
