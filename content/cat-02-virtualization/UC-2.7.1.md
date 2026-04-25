<!-- AUTO-GENERATED from UC-2.7.1.json — DO NOT EDIT -->

---
id: "2.7.1"
title: "Proxmox VE HA Manager Fencing and Live Migration Events"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.7.1 · Proxmox VE HA Manager Fencing and Live Migration Events

## Description

HA fencing and forced migrations are the last resort for guest availability on Proxmox clusters. When these events cluster in time or correlate with lost quorum, operators risk split-brain, repeated restarts, or guests left unmanaged during node failure.

## Value

Surfaces imminent or ongoing cluster partition scenarios so you can validate votes, qdevice, and storage before tenants see rolling outages.

## Implementation

Forward HA manager logs from every cluster member with a consistent sourcetype. Use FIELDALIAS to normalize `action` and `quorate`. Create a correlation search for fence bursts per node and for `quorate=false` transitions. Tie alerts to your hardware management channel when STONITH is involved.

## SPL

```spl
index=pve sourcetype="proxmox:ha" earliest=-24h
| eval act=lower(coalesce(action, ha_action, op))
| where match(act, "(?i)fence|stonith|migrate|relocate") OR match(lower(_raw), "(?i)lost quorum|not quorate|fence")
| rex field=_raw "(?i)VM\s+(?<vmid_num>\d+)"
| eval vmid=coalesce(vmid, vmid_num)
| stats count as ev, values(act) as actions, latest(quorate) as last_quorate by node, vmid
| sort - ev
```

## Visualization

Single value (active HA incidents), timechart of fence/migrate rate, table by node and vmid.

## References

- [Proxmox VE HA Manager](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html)
