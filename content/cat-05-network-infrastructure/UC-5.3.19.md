<!-- AUTO-GENERATED from UC-5.3.19.json — DO NOT EDIT -->

---
id: "5.3.19"
title: "Citrix ADC Content Switching Policy Hit Rate (NetScaler)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.19 · Citrix ADC Content Switching Policy Hit Rate (NetScaler)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Configuration

*We see how content switching rules are used so rewrites, new paths, and test rules do not sit unused while people blame the network.*

---

## Description

Content switching vServers route HTTP/HTTPS requests to different load-balancing vServers based on URL patterns, headers, cookies, or other request attributes. Misconfigured content switching policies result in traffic hitting the default (catch-all) policy or being routed to the wrong back-end. Monitoring policy hit rates validates that routing rules are working as intended and identifies policies that are never triggered (candidate for cleanup or misconfiguration).

## Value

Application delivery teams validate Citrix ADC content switching policy hit rates against expected baselines, detecting misconfigured or zero-hit policies that indicate incorrect traffic routing.

## Implementation

Poll the NITRO API `csvserver_cspolicy_binding` to get bound policies with hit counts. Alternatively, enable AppFlow on content switching vServers to capture per-request routing decisions. Run the scripted input every 15 minutes. Flag: policies with zero hits over 7 days (never triggered — misconfigured or obsolete), the default policy receiving more than 20% of traffic (indicates missing specific rules), and sudden shifts in policy hit distribution (routing change after configuration update). Content switching is critical for multi-tenant environments where different applications share a single VIP.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC content switching (CS) logs in `index=netscaler`. Key fields: `cs_vserver`, `cs_policy`, `target_lb_vserver`, `url`, `host_header`, `hit_count`.
* Content switching routes traffic to different lb vservers based on HTTP headers, URL, or expressions. Policy hits confirm traffic is being routed as intended. Low or zero hits on expected policies indicate misconfiguration or traffic pattern changes.

### Step 1 — - Configure data collection
Verify CS data:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("content switching" OR "cs_" OR "cspolicy" OR "CS_VSERVER") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Content switching policy hit analysis:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("content switching" OR "cs_" OR "cspolicy") earliest=-4h
| eval cs_vs=coalesce(cs_vserver, csvserver)
| eval policy=coalesce(cs_policy, cspolicy, policyname)
| eval target=coalesce(target_lb_vserver, targetlbvserver, target)
| eval hits=coalesce(hit_count, hits, totalhits)
| stats sum(hits) as total_hits latest(hits) as current_hits by host, cs_vs, policy, target
| lookup citrix_cs_policies.csv cs_vs, policy OUTPUT expected_hits_per_hour, application
| eval hit_rate=if(isnotnull(expected_hits_per_hour), round(100*total_hits/expected_hits_per_hour, 1), null())
| eval status=case(total_hits=0, "NO_HITS -- policy not matching", isnotnull(hit_rate) AND hit_rate < 20, "LOW -- significantly below expected", 1==1, "OK")
| where status != "OK"
| sort status, -total_hits
```

### Step 3 — - Validate
(a) On ADC CLI: `show cs vserver <vs>` -- check bound policies and hit counts.
(b) Send a request matching a specific CS policy and verify the hit counter increments.
(c) Verify that traffic is reaching the expected target lb vserver.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Content Switching"):
* Row 1 -- Single-value: "CS vservers", "Policies with zero hits", "Total policy hits".
* Row 2 -- Policy hit analysis table with expected vs actual.

Alerting:
* Warning (expected policy with zero hits for > 1 hour): traffic not being routed as intended.

### Step 5 — - Troubleshooting

* **Policy has zero hits** -- Check: (1) policy expression syntax: `show cs policy <policy>`, (2) policy priority (lower number = higher priority -- a higher-priority policy may be matching first), (3) traffic actually reaching the CS vserver.

* **Traffic going to wrong target** -- CS policies are evaluated in priority order. The first matching policy wins. Check priority: `show cs vserver <vs> -bindings`.

* **Policy hits decreased after config change** -- New or modified policies may have changed the matching order. Review the change log.

## SPL

```spl
index=network sourcetype="citrix:netscaler:cs"
| stats latest(hits) as total_hits, latest(target_lbvserver) as target, latest(priority) as priority by cs_vserver, policy_name, host
| eventstats sum(total_hits) as vserver_total_hits by cs_vserver
| eval hit_pct=if(vserver_total_hits>0, round(total_hits/vserver_total_hits*100,1), 0)
| sort cs_vserver, priority
| table cs_vserver, policy_name, priority, target, total_hits, hit_pct
```

## Visualization

Bar chart (hit rate by policy), Table (policies with hit counts), Timechart (default policy hit rate trending).

## Known False Positives

Rule reorder, content-switch tests, and new paths can change hit mix without a misconfiguration.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
