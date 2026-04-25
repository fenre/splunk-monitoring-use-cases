<!-- AUTO-GENERATED from UC-2.7.6.json — DO NOT EDIT -->

---
id: "2.7.6"
title: "Proxmox VE Hypervisor Firewall Deny Hotspots by Guest and Rule"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.7.6 · Proxmox VE Hypervisor Firewall Deny Hotspots by Guest and Rule

## Description

Hypervisor-level denies show east-west segmentation issues, compromised guests, or misapplied templates. Aggregating denies by guest and rule focuses policy fixes and incident triage without drowning in single-flow noise.

## Value

Improves zero-trust posture inside the virtualization tier and reduces mean time to containment.

## Implementation

Log selected deny chains with prefixes. Roll up hourly. Maintain a lookup of approved scanners. Alert when new vmid/rule combinations spike above a 30-day baseline.

## SPL

```spl
index=pve sourcetype="proxmox:firewall" earliest=-24h
| eval ac=lower(coalesce(action, verdict))
| where ac="drop" OR ac="reject"
| eval rk=coalesce(chain, rule, ruleid, log_prefix)
| stats count as hits, dc(src) as uniq_src, values(dport) as ports by vmid, rk, dst
| sort -hits
| head 50
```

## Visualization

Bar chart top deny rules; pie by vmid; drilldown raw events.

## References

- [Proxmox VE Firewall](https://pve.proxmox.com/pve-docs/chapter-pve-firewall.html)
