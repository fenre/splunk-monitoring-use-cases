<!-- AUTO-GENERATED from UC-6.2.46.json — DO NOT EDIT -->

---
id: "6.2.46"
title: "TrueNAS SMB share access audit trail for sensitive datasets"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.46 · TrueNAS SMB share access audit trail for sensitive datasets

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Audit, Security &middot; **Status:** Draft

*We help you see when who can reach a file share changes, so permission drift does not quietly open a sensitive folder to the whole company.*

---

## Description

Share-level audit trails support insider-threat investigations and proves who touched regulated folders.

## Value

Strengthens governance for HIPAA/PCI file shares without third-party agents.

## Implementation

Enable granular SMB auditing in TrueNAS; set `props.conf` LINE_BREAKER for multi-line kerberos events. Restrict index ACLs to security team.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-24h
| search smb OR SMB OR "share access" OR "authentication failure"
| eval share=coalesce(share_name, smb_share)
| eval user=coalesce(username, user, account)
| stats count by share, user, client_ip
| sort - count
```

## Visualization

Top shares by events, table (user, client_ip).

## Known False Positives

Backup jobs, scanners, and legitimate mass access can resemble policy violations; narrow paths and service accounts using a lookup.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
