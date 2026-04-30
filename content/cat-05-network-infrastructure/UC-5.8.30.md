<!-- AUTO-GENERATED from UC-5.8.30.json — DO NOT EDIT -->

---
id: "5.8.30"
title: "Infoblox Grid Member DNS Service Restarts and Critical Audit Events"
status: "draft"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.8.30 · Infoblox Grid Member DNS Service Restarts and Critical Audit Events

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Audit &middot; **Status:** Draft

*We help you know when a DNS service on the grid restarts or throws serious audit events, so core name resolution is not left blind.*

---

## Description

Unexpected DNS service restarts or member-level failures on the Infoblox Grid often precede partial outages or indicate administrative mistakes and potential unauthorised changes. The audit sourcetype is the authoritative record for who changed what on the platform.

## Value

Improves resilience of a critical Internet-facing control plane by correlating service impact with auditable configuration actions.

## Implementation

Enable comprehensive audit logging on Grid Manager and forward to Splunk. Refine the keyword search to match your NIOS audit message vocabulary. Require change tickets for matched events during business hours; after hours, route to on-call DNS and security.

## SPL

```spl
index=dns sourcetype="infoblox:audit" earliest=-24h
| search restart OR stopped OR failed OR "Named" OR "DNS Service" OR critical
| stats count values(action) as actions latest(_time) as last by host, admin, object
| where count>=1
| sort -last
```

## Visualization

Timeline (audit spikes), Table (admin, object, actions), Notable list for unplanned restarts.

## Known False Positives

Planned restarts, upgrades, and grid join operations can restart member services; tag maintenance windows in your alert logic.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
