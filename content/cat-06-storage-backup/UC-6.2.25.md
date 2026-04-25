<!-- AUTO-GENERATED from UC-6.2.25.json — DO NOT EDIT -->

---
id: "6.2.25"
title: "Ceph CRUSH rule and failure domain consistency verification"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.25 · Ceph CRUSH rule and failure domain consistency verification

## Description

Pools whose CRUSH rules do not enforce distinct failure domains risk simultaneous data loss when a rack or chassis fails. Automated diffing catches human error after hardware refreshes.

## Value

Supports data durability commitments and audit evidence for regulated object stores.

## Implementation

Nightly JSON snapshot; use `diff` saved to Splunk via scripted alert or store hash in KV for drift detection. Document allowed exceptions in a lookup.

## SPL

```spl
index=storage sourcetype="ceph:status" earliest=-24h
| search crush OR rule
| eval rule=coalesce(crush_rule_name, rule_name)
| eval domain=coalesce(failure_domain, device_class, host_bucket)
| stats values(domain) as domains dc(domain) as domain_count by rule, cluster_name
| where domain_count < 2 AND match(rule, "replicated|erasure")
| table cluster_name, rule, domains
```

## Visualization

Table (rule, domains), single value (violations).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
