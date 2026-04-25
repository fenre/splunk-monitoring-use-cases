<!-- AUTO-GENERATED from UC-2.10.3.json — DO NOT EDIT -->

---
id: "2.10.3"
title: "VxRail Manager Support Bundle Collection and Upload Status"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.10.3 · VxRail Manager Support Bundle Collection and Upload Status

## Description

Stalled support bundles delay Dell/GSS engagement during sev-1s. Tracking upload phases ensures diagnostics arrive before bridge calls stall.

## Value

Shortens vendor-assisted recovery timelines and improves audit evidence for escalations.

## Implementation

Ingest bundle job JSON. Alert if collection stuck >2 hours. Retry automation with least-privilege service account.

## SPL

```spl
index=vxrail sourcetype="vxrail:support_gateway" earliest=-7d
| eval pct=tonumber(percent_complete)
| eval ph=lower(phase)
| where pct<100 AND now()-_time>7200 OR match(lower(coalesce(error, _raw)), "(?i)fail|timeout")
| stats latest(pct) as progress, latest(error) as err by bundle_id, cluster_id
```

## Visualization

Progress bars per bundle; table errors; cluster facet.

## References

- [Collect VxRail support logs](https://www.dell.com/support/kbdoc/en-us/000201573/how-to-collect-logs-from-dell-vxrail-products-vxrecover)
