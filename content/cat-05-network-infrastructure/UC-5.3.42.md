<!-- AUTO-GENERATED from UC-5.3.42.json — DO NOT EDIT -->

---
id: "5.3.42"
title: "Citrix SD-WAN Orchestrator Config Push Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.42 · Citrix SD-WAN Orchestrator Config Push Failures

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We look at orchestrator and remote push results so a failed template or a half-applied site is a clear lead before users only "feel something off."*

---

## Description

The SD-WAN Orchestrator (or center) applies policies and feature templates across the fleet. When pushes fail, sites can drift or stay on stale rules. Primary reachability problems and job-level errors show risk at scale, not one box at a time. A single bad change set that fails in many sites needs rollback attention fast.

## Value

Network operations teams track Citrix SD-WAN Orchestrator configuration push success rates and version consistency across sites, detecting deployment failures and config drift.

## Implementation

Ingest job completion and management heartbeat logs. Tag each job with a change ticket. Alert on any push failure, growing count of `target_appliance` in error, or management-plane unreachability. For fleet-wide failure, start rollback of the `change_set` in the product and notify change owner. For chronic single appliance failure, look at time sync, cert expiry, and last-seen in inventory.

## Detailed Implementation

### Prerequisites
* Citrix SD-WAN Orchestrator syslog or API data. Key fields: `config_push_status` (SUCCESS/FAILURE), `site_name`, `target_appliance`, `error_reason`, `config_version`, `staged_version`.
* Citrix SD-WAN Orchestrator: central management platform that pushes configurations to all SD-WAN appliances. Config push failures leave sites on old configurations, creating inconsistencies. This can cause: routing mismatches, application steering errors, QoS policy discrepancies.

### Step 1 — - Configure data collection
Verify Orchestrator events:
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:orch") ("config" OR "push" OR "deploy" OR "stage" OR "activate") earliest=-7d
| where match(_raw, "(?i)(fail|error|success|push|deploy|stage)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Config push failure analysis:**
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:orch") ("config" OR "push" OR "deploy") earliest=-24h
| eval site=coalesce(site_name, target_site)
| eval appliance=coalesce(target_appliance, device_name)
| eval status=coalesce(config_push_status, if(match(_raw, "(?i)success"), "SUCCESS", if(match(_raw, "(?i)fail|error"), "FAILURE", null())))
| eval reason=coalesce(error_reason, if(match(_raw, "(?i)timeout"), "Timeout", if(match(_raw, "(?i)connect|unreachable"), "Appliance unreachable", if(match(_raw, "(?i)conflict|mismatch"), "Config conflict", "Unknown"))))
| where status="FAILURE"
| stats count as failures latest(reason) as last_reason latest(_time) as last_attempt by site, appliance
| eval severity=case(failures > 3, "HIGH -- repeated failures", 1==1, "WARNING")
| sort severity, -failures
```

**Config version consistency:**
```spl
index=netscaler (sourcetype="citrix:sdwan:syslog" OR sourcetype="citrix:sdwan:orch") ("config" OR "version") earliest=-4h
| eval site=coalesce(site_name, site)
| eval version=coalesce(config_version, running_version)
| stats latest(version) as current_version by site
| eventstats dc(current_version) as version_count
| where version_count > 1
| eval concern="CONFIG DRIFT -- sites running different versions"
```

### Step 3 — - Validate
(a) Check Orchestrator: Administration > Config Push History -- compare with Splunk.
(b) Verify all sites are running the same config version.
(c) If a push failed, check the specific error in Orchestrator UI.

### Step 4 — - Operationalize
Dashboard ("Citrix SD-WAN -- Config Management"):
* Row 1 -- Single-value: "Config pushes (24h)", "Failures", "Sites with old config", "Config versions active".
* Row 2 -- Config push failure detail.
* Row 3 -- Config version consistency check.

Alerting:
* High (repeated config push failures to same site): site running outdated config.
* Warning (multiple config versions active across sites): config drift.

### Step 5 — - Troubleshooting

* **Timeout on push** -- Appliance may be unreachable. Check: (1) management network connectivity to the appliance, (2) appliance CPU (high CPU can delay config processing), (3) Orchestrator-to-appliance VPN tunnel.

* **Config conflict** -- The running config has manual changes that conflict with the Orchestrator version. Resolve: (1) export running config, (2) compare with Orchestrator version, (3) merge changes in Orchestrator and re-push.

* **Config drift across sites** -- Ensure all changes go through Orchestrator, not local CLI. Disable local config changes on appliances.

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

## Known False Positives

Network blips, auth expiry, and partial pushes can make orchestrator or appliance deploy logs look worse than the live config.

## References

- [Citrix — SD-WAN Orchestrator administration](https://docs.citrix.com/en-us/citrix-sd-wan-orchestrator/)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
