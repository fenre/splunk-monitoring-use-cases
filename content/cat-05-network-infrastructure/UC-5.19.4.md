<!-- AUTO-GENERATED from UC-5.19.4.json — DO NOT EDIT -->

---
id: "5.19.4"
title: "Configuration Deployment Drift (Post-Automation Validation)"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.19.4 · Configuration Deployment Drift (Post-Automation Validation)

> **Criticality:** High &middot; **Difficulty:** Expert &middot; **Pillar:** Platform &middot; **Type:** Configuration, Compliance, Operations &middot; **Wave:** Run &middot; **Status:** Verified

*After our robots push settings, we double-check that each machine still matches the approved blueprint using several checker tools. When something disagrees, we see one clear list of mismatches instead of hunting through separate reports.*

---

## Description

Splunk unifies Terraform apply outcomes, Ansible convergence artifacts, Batfish reachability/policy checks, and Nornir/NAPALM diff snapshots so post-change validation failures roll into one prioritized drift backlog instead of siloed CI emails.

## Value

Architecture teams enforce intent fidelity across hybrid nets because hazardous ACL omissions, BGP knob regressions, or Terraform policy denies are detected in the same operational timeline as live automation rather than weeks later during audits.

## Implementation

Instrument each toolchain to emit compact JSON verdict lines (pass/fail plus resource identifiers); agree on shared `host` keys; nightly Batfish snapshot ingest; alert on any drift=1 per device per day unless suppressed.

## Detailed Implementation

### Prerequisites
- Golden sources of truth documented (Terraform remote state workspace IDs, Ansible inventory groups, Batfish snapshot naming).
- Secrets scrubbing rules applied before HEC.

### Step 1 — Emit validation events
Configure Terraform Cloud notifications or runners to POST summary JSON; schedule Batfish `bfq` checks after merges; have Nornir push per-device diff hashes.

### Step 2 — Normalize schema
Use transforms to map differing vendor keys into `host`, `intent_layer`, `drift_reason`; stash large diffs in lookup-backed KV references rather than huge `_raw`.

### Step 3 — Saved search
Save `network_automation_post_validate_drift`; alert on first occurrence per host daily or cumulative count≥3 per layer weekly.

### Step 4 — Validate
Introduce controlled deliberate drift in lab; verify each subsystem surfaces drift=1 within SLA.

### Step 5 — Operationalize
Dashboard: Sankey from toolchain source to affected hosts; annotate owners via CMDB lookup; integrate ticketing webhook on drilldown.

## SPL

```spl
index IN ("iac","config_audit","network_audit") earliest=-24h@h latest=now
| eval src=lower(coalesce(sourcetype,_sourcetype,""))
| eval lr=lower(_raw)
| eval drift=case(match(src,"batfish") AND match(lr,"fail|violated|undefined\\sreference|inconsistent"),1,match(src,"terraform|tfc|hcp") AND match(lr,"apply.*error|policy.*denied|drift"),1,match(src,"ansible|napalm|nornir") AND match(lr,"\\bfail\\b|\\bdiff\\b|configuration drift"),1,match(lr,"drift|golden.*mismatch|hash.*diff"),1,0)
| eval hn=coalesce(host,device,d_hostname,network_device,"unknown")
| eval layer=coalesce(intent_layer,resource_type,"unspecified")
| where drift=1
| stats count earliest(_time) as first_seen latest(_time) as last_seen values(layer) as layers by hn src
| where count>=1
| sort -count
```

## Visualization

Dashboard Studio: KPI count of hosts with drift signals; treemap by toolchain source; detail table (`hn`,`src`,`layers`,`count`,`first_seen`,`last_seen`) with link-out to stored diffs.

## Known False Positives

**Benign drift:** emergency hotfixes outside Terraform/Ansible flagged until reconciled.**Batfish modeling gaps:** missing interfaces appear as false inconsistencies.**Timing skew:** snapshot older than live device state.**Parallel pipelines:** duplicate detections from Ansible and NAPALM unless deduped on hash.**Large churn:** mass VLAN adds spike counts during migrations.

## References

- [Batfish documentation — Network validation](https://batfish.readthedocs.io/)
- [HashiCorp Terraform — Audit logging](https://developer.hashicorp.com/terraform/cloud-docs/)
- [NAPALM documentation — Cross-vendor network automation](https://napalm.readthedocs.io/)
