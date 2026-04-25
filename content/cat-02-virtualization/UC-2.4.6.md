<!-- AUTO-GENERATED from UC-2.4.6.json — DO NOT EDIT -->

---
id: "2.4.6"
title: "Multi-Hypervisor Fleet Inventory"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.4.6 · Multi-Hypervisor Fleet Inventory

## Description

Organizations running multiple hypervisors need a unified view of all VMs regardless of platform. A consolidated inventory enables accurate capacity planning, consistent policy enforcement, and complete asset tracking. Without it, VMs on different platforms become silos with inconsistent governance.

## Value

Organizations running multiple hypervisors need a unified view of all VMs regardless of platform. A consolidated inventory enables accurate capacity planning, consistent policy enforcement, and complete asset tracking. Without it, VMs on different platforms become silos with inconsistent governance.

## Implementation

Normalize VM inventory fields across all hypervisor platforms into a common schema (vm_name, platform, host, vcpus, mem_gb, power_state, guest_os). Use a scheduled search to populate a summary index or KV store for fast lookups. Enrich with CMDB data (owner, department, environment) via lookup. Generate weekly fleet reports showing total VM count, resource allocation, and platform distribution.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, `Splunk_TA_windows`, custom KVM inputs.
• Ensure the following data sources are available: VM inventory from VMware, Hyper-V, KVM/Proxmox.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize VM inventory fields across all hypervisor platforms into a common schema (vm_name, platform, host, vcpus, mem_gb, power_state, guest_os). Use a scheduled search to populate a summary index or KV store for fast lookups. Enrich with CMDB data (owner, department, environment) via lookup. Generate weekly fleet reports showing total VM count, resource allocation, and platform distribution.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm"
| eval platform="VMware", vcpus=numCpu, mem_gb=round(memoryMB/1024,0)
| table vm_name, platform, host, vcpus, mem_gb, power_state, guest_os
| append [search index=hyperv sourcetype="hyperv_vm_config" | eval platform="Hyper-V", mem_gb=round(memory_mb/1024,0) | table vm_name, platform, host, vcpus, mem_gb, state, os_name | rename state as power_state, os_name as guest_os]
| append [search index=virtualization sourcetype=kvm_capacity | eval platform="KVM", mem_gb=round(vm_memory_mb/1024,0) | table vm_name, platform, host, vm_vcpus, mem_gb, power_state, guest_os | rename vm_vcpus as vcpus]
| stats latest(platform) as platform, latest(host) as host, latest(vcpus) as vcpus, latest(mem_gb) as mem_gb, latest(power_state) as state, latest(guest_os) as os by vm_name
| sort platform, vm_name
| table vm_name, platform, host, vcpus, mem_gb, state, os
```

Understanding this SPL

**Multi-Hypervisor Fleet Inventory** — Organizations running multiple hypervisors need a unified view of all VMs regardless of platform. A consolidated inventory enables accurate capacity planning, consistent policy enforcement, and complete asset tracking. Without it, VMs on different platforms become silos with inconsistent governance.

Documented **Data sources**: VM inventory from VMware, Hyper-V, KVM/Proxmox. **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`, custom KVM inputs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **platform** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Multi-Hypervisor Fleet Inventory**): table vm_name, platform, host, vcpus, mem_gb, power_state, guest_os
• Appends rows from a subsearch with `append`.
• Appends rows from a subsearch with `append`.
• `stats` rolls up events into metrics; results are split **by vm_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Multi-Hypervisor Fleet Inventory**): table vm_name, platform, host, vcpus, mem_gb, state, os

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Compute_Inventory.Hypervisor by Hypervisor.dest, Hypervisor.status | sort - count
```

Understanding this CIM / accelerated SPL

**Multi-Hypervisor Fleet Inventory** — Organizations running multiple hypervisors need a unified view of all VMs regardless of platform. A consolidated inventory enables accurate capacity planning, consistent policy enforcement, and complete asset tracking. Without it, VMs on different platforms become silos with inconsistent governance.

Documented **Data sources**: VM inventory from VMware, Hyper-V, KVM/Proxmox. **App/TA** (typical add-on context): `Splunk_TA_vmware`, `Splunk_TA_windows`, custom KVM inputs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Compute_Inventory.Hypervisor` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (unified VM inventory), Pie chart (VMs by platform), Bar chart (resource allocation by platform), Treemap (VMs by department and platform).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm"
| eval platform="VMware", vcpus=numCpu, mem_gb=round(memoryMB/1024,0)
| table vm_name, platform, host, vcpus, mem_gb, power_state, guest_os
| append [search index=hyperv sourcetype="hyperv_vm_config" | eval platform="Hyper-V", mem_gb=round(memory_mb/1024,0) | table vm_name, platform, host, vcpus, mem_gb, state, os_name | rename state as power_state, os_name as guest_os]
| append [search index=virtualization sourcetype=kvm_capacity | eval platform="KVM", mem_gb=round(vm_memory_mb/1024,0) | table vm_name, platform, host, vm_vcpus, mem_gb, power_state, guest_os | rename vm_vcpus as vcpus]
| stats latest(platform) as platform, latest(host) as host, latest(vcpus) as vcpus, latest(mem_gb) as mem_gb, latest(power_state) as state, latest(guest_os) as os by vm_name
| sort platform, vm_name
| table vm_name, platform, host, vcpus, mem_gb, state, os
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Compute_Inventory.Hypervisor by Hypervisor.dest, Hypervisor.status | sort - count
```

## Visualization

Table (unified VM inventory), Pie chart (VMs by platform), Bar chart (resource allocation by platform), Treemap (VMs by department and platform).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Compute_Inventory](https://docs.splunk.com/Documentation/CIM/latest/User/Compute_Inventory)
