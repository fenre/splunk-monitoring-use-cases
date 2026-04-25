<!-- AUTO-GENERATED from UC-6.4.27.json — DO NOT EDIT -->

---
id: "6.4.27"
title: "Commvault client agent version compliance and unsupported endpoint audit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.4.27 · Commvault client agent version compliance and unsupported endpoint audit

## Description

Out-of-date agents miss features, hotfixes, and security patches; they also complicate vendor support during restore incidents.

## Value

Reduces Sev1 restore time by ensuring the fleet is on supported combinations before audits or ransomware events.

## Implementation

Maintain `commvault_supported_agents.csv` with `min_supported` per product line. Refresh client inventory daily. Feed results to CMDB patch team.

## SPL

```spl
index=backup sourcetype="commvault:client" earliest=-24h
| eval ver=coalesce(agent_version, client_version)
| lookup commvault_supported_agents product OUTPUT min_supported
| where isnull(min_supported) OR ver < min_supported
| stats values(hostname) as hosts dc(hostname) as host_count by ver, client_group
| sort host_count
```

## Visualization

Pie chart (supported vs not), table (version, host count).

## References

- [Commvault Documentation — Splunk integration](https://documentation.commvault.com/)
