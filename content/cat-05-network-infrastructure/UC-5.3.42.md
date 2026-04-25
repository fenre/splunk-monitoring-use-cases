<!-- AUTO-GENERATED from UC-5.3.42.json — DO NOT EDIT -->

---
id: "5.3.42"
title: "Citrix SD-WAN Orchestrator Config Push Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.42 · Citrix SD-WAN Orchestrator Config Push Failures

## Description

The SD-WAN Orchestrator (or center) applies policies and feature templates across the fleet. When pushes fail, sites can drift or stay on stale rules. Primary reachability problems and job-level errors show risk at scale, not one box at a time. A single bad change set that fails in many sites needs rollback attention fast.

## Value

The SD-WAN Orchestrator (or center) applies policies and feature templates across the fleet. When pushes fail, sites can drift or stay on stale rules. Primary reachability problems and job-level errors show risk at scale, not one box at a time. A single bad change set that fails in many sites needs rollback attention fast.

## Implementation

Ingest job completion and management heartbeat logs. Tag each job with a change ticket. Alert on any push failure, growing count of `target_appliance` in error, or management-plane unreachability. For fleet-wide failure, start rollback of the `change_set` in the product and notify change owner. For chronic single appliance failure, look at time sync, cert expiry, and last-seen in inventory.

## Detailed Implementation

Prerequisites: Orchestrator lines include change_set and result; change ticket data in lookup change_ticket_map.csv. Step 1: Configure data collection — Forward orchestrator and mgmt reachability; keep INFO that marks job end; props [citrix:sdwan:orchestrator] for target_appliance, error_code, change_set, result. Step 2: Create the search and alert — Sev-1 when fail count maps to more than half of appliances for one change_set; sev-2 for production template failure; include reach_fails>0. Step 3: Validate — Re-run a harmless template after hours and confirm `index=sdwan (sourcetype="citrix:sdwan:orchestrator" OR sourcetype="citrix:sdwan:mgmt") earliest=-1h | stats count by result, change_set` shows success. Step 4: Operationalize — Attach Splunk link to change reviews; repeated push failures with broad blast radius go to the Citrix SD-WAN Orchestrator support team and change owner; if failures persist per appliance, check clock and certificate expiry.

## SPL

```spl
index=sdwan (sourcetype="citrix:sdwan:orchestrator" OR sourcetype="citrix:sdwan:mgmt") earliest=-24h
| eval ok=if(match(lower(result),"(?i)success|ok|applied"),1,0), fail=if(match(lower(result),"(?i)fail|error|timeout|denied|partial"),1,0), nreach=if(match(lower(error_code),"(?i)unreach|no route|refused|tls|auth|503"),1,0)
| bin _time span=15m
| stats count as jobs, sum(ok) as okc, sum(fail) as failc, sum(nreach) as reach_fails, dc(target_appliance) as appliances by _time, change_set
| where failc>0 OR reach_fails>0
| table _time, change_set, jobs, okc, failc, reach_fails, appliances
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

## Visualization

Timechart: failed jobs per 15m; table: `change_set` with failure rates; list: top appliances by failed attempts; health tile: orchestrator reachability.

## References

- [Citrix — SD-WAN Orchestrator administration](https://docs.citrix.com/en-us/citrix-sd-wan-orchestrator/)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
