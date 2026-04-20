---
id: "2.3.7"
title: "KVM Host CPU Model and Migration Compatibility"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.3.7 · KVM Host CPU Model and Migration Compatibility

## Description

Live migration fails or degrades when host CPU models differ. Tracking CPU compatibility avoids failed migrations and performance surprises.

## Value

Live migration fails or degrades when host CPU models differ. Tracking CPU compatibility avoids failed migrations and performance surprises.

## Implementation

Extract host CPU model from `virsh capabilities` and per-VM CPU from `virsh dumpxml`. Compare for migration compatibility. Document and alert when VMs use incompatible CPU.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`virsh capabilities`, `virsh dominfo`).
• Ensure the following data sources are available: Libvirt capabilities XML, VM CPU config.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract host CPU model from `virsh capabilities` and per-VM CPU from `virsh dumpxml`. Compare for migration compatibility. Document and alert when VMs use incompatible CPU.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=virtualization sourcetype=kvm_cpu_compat host=*
| stats latest(host_cpu_model) as host_model, values(vm_cpu_model) as vm_models by host
| eval compatible=if(match(vm_models, host_model), "Yes", "No")
| where compatible="No"
| table host host_model vm_models
```

Understanding this SPL

**KVM Host CPU Model and Migration Compatibility** — Live migration fails or degrades when host CPU models differ. Tracking CPU compatibility avoids failed migrations and performance surprises.

Documented **Data sources**: Libvirt capabilities XML, VM CPU config. **App/TA** (typical add-on context): Custom scripted input (`virsh capabilities`, `virsh dominfo`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: virtualization; **sourcetype**: kvm_cpu_compat. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=virtualization, sourcetype=kvm_cpu_compat. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **compatible** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where compatible="No"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **KVM Host CPU Model and Migration Compatibility**): table host host_model vm_models


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, VM, CPU model, compatible), Migration readiness matrix.

## SPL

```spl
index=virtualization sourcetype=kvm_cpu_compat host=*
| stats latest(host_cpu_model) as host_model, values(vm_cpu_model) as vm_models by host
| eval compatible=if(match(vm_models, host_model), "Yes", "No")
| where compatible="No"
| table host host_model vm_models
```

## Visualization

Table (host, VM, CPU model, compatible), Migration readiness matrix.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
