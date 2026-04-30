<!-- AUTO-GENERATED from UC-2.9.12.json — DO NOT EDIT -->

---
id: "2.9.12"
title: "OpenStack Keystone Federation IdP Login and Mapping Failures"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.9.12 · OpenStack Keystone Federation IdP Login and Mapping Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Federation regressions lock out enterprise users without touching local passwords. Mapping failures after IdP cert rotations are common.

## Value

Reduces enterprise SSO outages and speeds joint debugging with identity teams.

## Implementation

Tag IdP id on events. Alert on failure bursts. Maintain mapping version control links in tickets.

## SPL

```spl
index=openstack sourcetype="openstack:keystone" earliest=-24h
| search match(lower(_raw), "(?i)federat|saml|oidc|mapped")
| eval hs=tonumber(http_status)
| where hs>=401 OR match(lower(_raw), "(?i)mapping.*fail|assertion")
| stats count as fed_fails by idp_id, protocol
```

## Visualization

Timechart federation failures; breakdown by IdP; sample assertions redacted.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [Keystone Federation](https://docs.openstack.org/keystone/latest/admin/federation/)
