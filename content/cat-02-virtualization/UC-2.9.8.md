<!-- AUTO-GENERATED from UC-2.9.8.json — DO NOT EDIT -->

---
id: "2.9.8"
title: "OpenStack Neutron Floating IP Pool Exhaustion per Project"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-2.9.8 · OpenStack Neutron Floating IP Pool Exhaustion per Project

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Capacity, Risk &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Exhausted floating IPs block new public services during incidents. Per-project utilization forecasts runout before the next change window.

## Value

Prevents last-mile connectivity failures during scaling and DR tests.

## Implementation

Ingest quota metrics hourly. Alert at 85%. Automate cleanup suggestions for stale FIPs via lookup of aged associations.

## SPL

```spl
index=openstack sourcetype="openstack:neutron" earliest=-1h
| eval pct=100*tonumber(fip_used)/tonumber(fip_total)
| where pct>=85
| stats latest(pct) as util by project_id, external_network_id
```

## Visualization

Gauge per project; table external nets; trend forecast.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Neutron Floating IPs](https://docs.openstack.org/neutron/latest/admin/config-fip.html)
