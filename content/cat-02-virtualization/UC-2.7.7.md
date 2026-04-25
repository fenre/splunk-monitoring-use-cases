<!-- AUTO-GENERATED from UC-2.7.7.json — DO NOT EDIT -->

---
id: "2.7.7"
title: "Proxmox VE QEMU Guest Agent API Failures and Timeouts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.7.7 · Proxmox VE QEMU Guest Agent API Failures and Timeouts

## Description

Guest-agent RPC failures break clean quiescing for backups, IP reporting, and orchestration playbooks. A rising failure ratio often tracks QEMU upgrades, virtio-serial issues, or agents disabled inside guests.

## Value

Preserves automation reliability and avoids surprise manual console work during maintenance.

## Implementation

Parse proxy logs with method, path, and status. Alert on sustained failure percentage. Join `vmid` to CMDB. Automate tickets to owners to reinstall or enable the agent.

## SPL

```spl
index=pve sourcetype="proxmox:pveproxy" earliest=-4h
| eval cmd=lower(coalesce(command, api_cmd, uri_path))
| where match(cmd, "(?i)agent|qemu.*guest|guest-ping|guest-info|guest-exec")
| eval hs=tonumber(replace(coalesce(http_status, status_code), "[^0-9]", ""))
| eval fail=if(hs>=400 OR match(lower(coalesce(result, _raw)), "(?i)timeout|error|no guest agent"), 1, 0)
| stats count as calls, sum(fail) as fails, dc(vmid) as guests by user
| eval fail_pct=round(100*fails/calls,2)
| where fails>0 AND fail_pct>5
```

## Visualization

Timechart of failure rate; table of users and affected guests.

## References

- [QEMU Guest Agent on Proxmox](https://pve.proxmox.com/wiki/Qemu-guest-agent)
