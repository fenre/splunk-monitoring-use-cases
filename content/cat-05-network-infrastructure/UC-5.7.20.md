<!-- AUTO-GENERATED from UC-5.7.20.json — DO NOT EDIT -->

---
id: "5.7.20"
title: "NetFlow v5 vs v9/IPFIX Template Coverage Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.7.20 · NetFlow v5 vs v9/IPFIX Template Coverage Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Data Quality, Governance, Operations &middot; **Wave:** Walk &middot; **Status:** Verified

*We check whether our traffic summaries arrive in the older fixed form or the newer flexible form and whether each sender shares enough variety of templates. That tells planners who still owes an upgrade so fields do not quietly vanish.*

---

## Description

Aggregates observed NetFlow protocol generations, template identifiers, and byte volumes per exporter so engineers can spot outdated fixed-schema collectors, missing flexible templates, or parsers stuck on unknown versions.

## Value

Platform owners accelerate migrations toward Internet Protocol Flow Information Export-capable exporters, justify firewall rule updates for template traffic, and produce audit trails proving sensitive fields remain populated after upgrades.

## Implementation

Schedule daily audit; reconcile against configuration management intended versions; gate hardware refresh milestones on healthy template diversity; alert when legacy version five dominates critical sites.

## Detailed Implementation

### Prerequisites
- Inventory of mandated information elements such as application identifiers and interface indices.
- Lab packet captures validating Splunk’s decoded `version` field naming.
- Capacity planning numbers for template-record overhead.

### Step 1 — Configure data collection
Enable debug-template logging temporarily during migrations; capture exporter clocks and observation domain identifiers for multi-tenant collectors.

### Step 2 — Create the search
Extend with `| where coverage_flag="LOW_TEMPLATE_DIVERSITY" AND gb>10` for prioritized remediation. Push outputs into a metrics index for trending.

### Step 3 — Validate
Compare Splunk metrics to `show flow exporter statistics` on Cisco devices during cutover weekends.

### Step 4 — Operationalize
Executive PDF summarizes percentage of bytes still on version five; automation opens firewall-change tasks when new template ports appear.

### Step 5 — Troubleshooting
Parsing UNKNOWN versions usually indicates fragmented datagrams—increase maximum transmission unit checks on forwarding paths. Duplicate template IDs across domains require composite keys—append observation domain to stats grouping.

## SPL

```spl
index=netflow earliest=-24h
| eval nf_ver=coalesce(version, nf_version, netflow_version, "UNKNOWN")
| eval tmpl=coalesce(template_id, flowset_id, "NONE")
| eval exporter=coalesce(exporter_ip, agent, "UNSPECIFIED")
| stats count dc(tmpl) as distinct_templates values(tmpl) as template_list dc(sourcetype) as sourcetypes sum(bytes) as bytes
  by nf_ver exporter host
| eval gb=round(bytes/1073741824, 3)
| eval coverage_flag=case(
    nf_ver="5" OR nf_ver="v5" OR nf_ver="V5", "LEGACY_FIXED_SCHEMA",
    nf_ver="9" OR nf_ver="v9" OR nf_ver="V9" OR nf_ver="10" OR nf_ver="IPFIX" OR nf_ver="ipfix", if(distinct_templates>=3, "TEMPLATE_HEALTHY", "LOW_TEMPLATE_DIVERSITY"),
    true(), "VERSION_PARSE_REVIEW"
)
| sort nf_ver -count
| head 200
```

## Visualization

Pie chart of bytes by nf_ver; heatmap exporters × distinct_templates; timeline of LOW_TEMPLATE_DIVERSITY incidents.

## Known False Positives

Maintenance windows briefly collapse template diversity while exporters reload. Multi-slot routers export independent streams that appear redundant until folded by observation domain. Synthetic replay labs skew distributions.

## References

- [RFC 3954 — Cisco Systems NetFlow Services Export Version 9](https://www.rfc-editor.org/rfc/rfc3954)
- [RFC 7011 — Specification for IP Flow Information Export (IPFIX)](https://www.rfc-editor.org/rfc/rfc7011)
