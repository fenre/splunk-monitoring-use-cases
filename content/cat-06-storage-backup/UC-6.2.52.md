<!-- AUTO-GENERATED from UC-6.2.52.json — DO NOT EDIT -->

---
id: "6.2.52"
title: "TrueNAS UI and service TLS certificate expiration monitoring"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.2.52 · TrueNAS UI and service TLS certificate expiration monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance, Security &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Expired certificates break HTTPS admin, replication auth, and some cloud sync providers—often during holiday change freezes.

## Value

Avoids preventable outages on admin and API integrations relied on by automation.

## Implementation

Store `notAfter` in epoch; compute days in SPL or at ingest. Integrate with ITSM for auto-tickets at 30/14/7 days.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-7d
| search certificate OR x509 OR TLS OR SSL
| eval days_left=coalesce(days_until_expiry, cert_days_remaining)
| where days_left < 30
| stats min(days_left) as min_days by hostname, cn, service
```

## Visualization

Table (CN, days left), timeline.

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
