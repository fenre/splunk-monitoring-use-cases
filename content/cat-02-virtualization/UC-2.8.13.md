<!-- AUTO-GENERATED from UC-2.8.13.json — DO NOT EDIT -->

---
id: "2.8.13"
title: "oVirt ISO Domain Mount and Image Provisioning Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.8.13 · oVirt ISO Domain Mount and Image Provisioning Events

## Description

ISO domains power installs and rescue media. Mount failures delay builds and can mask NFS permission regressions.

## Value

Keeps build pipelines and operator runbooks unblocked.

## Implementation

Monitor ISO domain health separately from data domains. Alert on failed mounts. Correlate with NAS audit logs.

## SPL

```spl
index=ovirt sourcetype="ovirt:storagedomain" earliest=-7d
| eval dt=lower(coalesce(domain_type, type))
| where dt="iso"
| eval ms=lower(mount_status)
| where ms!="active" OR match(lower(_raw), "(?i)unmount|nfs.*fail|permission")
| table _time, domain_name, ms, last_scan, message
```

## Visualization

Timeline mount state; table domains; NFS error keywords.

## References

- [oVirt ISO Storage Domains](https://www.ovirt.org/documentation/administration_guide/#ISO_domain)
