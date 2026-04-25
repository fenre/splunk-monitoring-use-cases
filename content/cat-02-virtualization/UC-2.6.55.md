<!-- AUTO-GENERATED from UC-2.6.55.json — DO NOT EDIT -->

---
id: "2.6.55"
title: "GPU Driver Version and License Status (NVIDIA GRID / vGPU)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.55 · GPU Driver Version and License Status (NVIDIA GRID / vGPU)

## Description

NVIDIA vGPU and GRID licensing tie guest driver versions, hypervisor, and a license service together. A guest can boot but fall back to a restricted mode, lose hardware encode, or see session failures if the license server is unreachable, the wrong `driverVersion` is paired with a host driver, or ECC errors pass a threshold. Citrix 3D workloads, Teams optimization, and browser video offload all depend on a healthy, licensed GPU path. This use case unifies uberAgent (or an equivalent) GPU performance and license state with optional Citrix VDA hardware health. Treat driver skew across a catalog as an image problem; treat isolated license loss as a network or license server problem.

## Value

NVIDIA vGPU and GRID licensing tie guest driver versions, hypervisor, and a license service together. A guest can boot but fall back to a restricted mode, lose hardware encode, or see session failures if the license server is unreachable, the wrong `driverVersion` is paired with a host driver, or ECC errors pass a threshold. Citrix 3D workloads, Teams optimization, and browser video offload all depend on a healthy, licensed GPU path. This use case unifies uberAgent (or an equivalent) GPU performance and license state with optional Citrix VDA hardware health. Treat driver skew across a catalog as an image problem; treat isolated license loss as a network or license server problem.

## Implementation

Enable the GPU-related uberAgent options that match your hypervisor. Confirm `index=uberagent` has one row per host per minute at minimum. Build a `lookup` of approved `driverVersion` for each vGPU type and image generation. Alert when `licenseState` is not `Licensed` for more than 15 minutes, or when `driverVersion` is not in the approved list, or when fatal GPU errors increment. Excluded dedicated physical GPUs from vGPU license logic if you run mixed modes. For Citrix, tag hosts that run HDX 3D Pro policies so the alert is routed to the DaaS and NVIDIA contact points.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent with GPU, NVIDIA vGPU in supported configuration; optional VDA service events; Windows forwarder for System events from the NVIDIA service.
• Ensure the following data sources are available: `index=uberagent` GPU sourcetypes; `index=xd` optional; consistent `host` keys.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map vendor fields to a shared schema. If two hosts on the same hypervisor show different `driverVersion`, investigate template drift. If `licenseState` flaps, capture license server and DNS tickets.

Step 2 — Create the search and alert
Simplify the primary SPL for day one: run only the `index=uberagent` arm until the append path is vetted. Example:

```spl
index=uberagent sourcetype="uberAgent:GPU:NVIDIA"
| eval lic=coalesce(licenseState, "unknown")
| where lic!="Licensed" OR like(lower(lic), "%fail%")
| table _time, host, driverVersion, licenseState, vgpuType
```

**GPU Driver Version and License Status (NVIDIA GRID / vGPU)** — Once stable, reintroduce the `append` to `index=xd` and deduplicate on `host_name`.

Step 3 — Validate
In a pre-production cluster, block license port traffic briefly, confirm the alert, restore, and assert recovery. Test driver roll-forward in a canary group.

Step 4 — Operationalize
Own jointly between virtualization and Citrix teams. Re-evaluate on every new NVIDIA and Citrix LTSR combination because driver pairs change.

## SPL

```spl
index=uberagent (sourcetype="uberAgent:GPU:NVIDIA" OR sourcetype="uberAgent:GPU:Performance")
| eval host_name=coalesce(host, dest_host, machine)
| eval driver=coalesce(driverVersion, driver_version, nvidia_driver_version, "unknown")
| eval lic=lower(coalesce(licenseState, license_state, vgpu_license_state, "unknown"))
| eval vgpu_name=coalesce(vgpuType, vgpu_type, vgpu, "Unknown")
| eval errs=tonumber(coalesce(fatal_count, 0)) + tonumber(coalesce(uncorrectable_ecc, 0))
| where (lic!="licensed" AND lic!="ok" AND lic!="n/a" AND lic!="active") OR like(lic, "%unlic%") OR like(lic, "%fail%") OR errs>0
| stats latest(driver) as driver_version, max(lic) as license_state, latest(vgpu_name) as vgpu, max(errs) as err_signals by host_name
| table host_name, driver_version, vgpu, license_state, err_signals
```

## Visualization

Table of hosts with `driverVersion`, vGPU type, and license; heatmap of license problems over time; line chart of GPU utilization for affected hosts, linked to a Citrix app session panel.

## References

- [NVIDIA vGPU software documentation](https://docs.nvidia.com/grid/index.html)
- [HDX 3D Pro — Citrix (context for GPU use)](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/hdx-3d-pro.html)
