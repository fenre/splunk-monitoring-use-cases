---
id: "2.4.5"
title: "Virtualization License Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.4.5 · Virtualization License Compliance

## Description

VMware licenses are per-CPU, Hyper-V licenses are per-core, and Windows Server Datacenter vs Standard determines VM rights. Running more physical CPUs or cores than licensed risks audit penalties. Tracking socket/core counts against entitlements prevents costly true-up surprises.

## Value

VMware licenses are per-CPU, Hyper-V licenses are per-core, and Windows Server Datacenter vs Standard determines VM rights. Running more physical CPUs or cores than licensed risks audit penalties. Tracking socket/core counts against entitlements prevents costly true-up surprises.

## Implementation

Collect host hardware inventory (socket count, core count) from all hypervisors. Maintain a lookup table of license entitlements per cluster/site. Compare actual vs entitled. Alert when actual exceeds entitled. Generate monthly compliance reports. Track license utilization ratio — under-utilized licenses may be reassignable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, `Splunk_TA_windows`, license lookup.
• Ensure the following data sources are available: Host inventory from all hypervisors, license entitlement lookup.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect host hardware inventory (socket count, core count) from all hypervisors. Maintain a lookup table of license entitlements per cluster/site. Compare actual vs entitled. Alert when actual exceeds entitled. Generate monthly compliance reports. Track license utilization ratio — under-utilized licenses may be reassignable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(numCpuPkgs) as sockets, latest(numCpuCores) as cores, latest(version) as esxi_version by host, cluster
| eval license_units=sockets
| stats sum(license_units) as total_sockets, sum(cores) as total_cores, dc(host) as host_count by cluster
| lookup license_entitlements cluster OUTPUT licensed_sockets, license_edition
| eval compliant=if(total_sockets<=licensed_sockets, "Yes", "No")
| table cluster, host_count, total_sockets, total_cores, licensed_sockets, license_edition, compliant
```

Understanding this SPL

**Virtualization License Compliance** — VMware licenses are per-CPU, Hyper-V licenses are per-core, and Windows Server Datacenter vs Standard determines VM rights. Running more physical CPUs or cores than licensed risks audit penalties. Tracking socket/core counts against entitlements prevents costly true-up surprises.

Documented **Data sources**: Host inventory from all hypervisors, license entitlement lookup. **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`, license lookup. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:hostsystem. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:hostsystem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, cluster** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **license_units** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by cluster** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Virtualization License Compliance**): table cluster, host_count, total_sockets, total_cores, licensed_sockets, license_edition, compliant


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cluster, sockets, entitled, compliant), Gauge (license utilization), Bar chart (compliance by cluster).

## SPL

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(numCpuPkgs) as sockets, latest(numCpuCores) as cores, latest(version) as esxi_version by host, cluster
| eval license_units=sockets
| stats sum(license_units) as total_sockets, sum(cores) as total_cores, dc(host) as host_count by cluster
| lookup license_entitlements cluster OUTPUT licensed_sockets, license_edition
| eval compliant=if(total_sockets<=licensed_sockets, "Yes", "No")
| table cluster, host_count, total_sockets, total_cores, licensed_sockets, license_edition, compliant
```

## Visualization

Table (cluster, sockets, entitled, compliant), Gauge (license utilization), Bar chart (compliance by cluster).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
