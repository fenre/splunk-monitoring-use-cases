<!-- AUTO-GENERATED from UC-5.2.17.json — DO NOT EDIT -->

---
id: "5.2.17"
title: "Firewall Rule Hit Count Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.17 · Firewall Rule Hit Count Analysis

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We show which rules see the most use so you can clean dead access, find shadow IT, and tune noisy policies with facts.*

---

## Description

Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.

## Value

Security teams analyze firewall rule hit counts to identify unused rules for cleanup, overly permissive catchall rules, and shadow rules that never match traffic.

## Implementation

Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.

## Detailed Implementation

### Prerequisites
* Firewall traffic logs with rule/policy identification. Key fields: `rule` (PA: rule name), `policyid` (Fortinet: policy ID), `policy_name`, `action`, traffic counts. Data in `index=firewall`.
* Rule hit count analysis identifies: (1) unused rules (zero hits) that should be removed, (2) overly permissive "any-any" rules handling most traffic, (3) shadow rules (rules that never match because a higher-priority rule catches all traffic), (4) rules generating the most denials.

### Step 1 — - Configure data collection
Verify rule identification:
```spl
index=firewall earliest=-7d
| eval rule=coalesce(rule, policy_name, policyid, rule_name)
| stats count by rule, action | sort -count | head 30
```

### Step 2 — - Create the search and alert

**Primary search -- Rule hit count analysis:**
```spl
index=firewall earliest=-7d
| eval rule=coalesce(rule, policy_name, policyid, rule_name, acl_name)
| eval act=lower(coalesce(action, policy_action))
| eval is_allow=if(match(act, "(?i)allow|pass|accept|permit"), 1, 0)
| eval is_deny=if(match(act, "(?i)deny|block|drop|reject"), 1, 0)
| stats count as total_hits sum(is_allow) as allows sum(is_deny) as denials dc(coalesce(src_ip, src)) as unique_sources dc(coalesce(dest_ip, dest)) as unique_targets by rule, host
| eval allow_pct=round(100*allows/total_hits, 1)
| eval deny_pct=round(100*denials/total_hits, 1)
| eval concern=case(total_hits=0, "UNUSED -- remove rule", total_hits > 1000000 AND match(rule, "(?i)any|default|catch"), "OVERLY_PERMISSIVE -- catchall rule handling ".total_hits." hits", denials > allows AND total_hits > 1000, "HIGH_DENY -- mostly denying traffic (".deny_pct."%)", unique_sources > 10000 AND unique_targets > 10000, "BROAD -- very wide scope", 1==1, null())
| where isnotnull(concern)
| sort concern, -total_hits
```

### Step 3 — - Validate
(a) Palo Alto: Policies > Security > Hit Count column -- compare with Splunk.
(b) Fortinet: `diagnose firewall policy-hit-count` -- shows per-policy hit counts.
(c) Check for shadow rules by reviewing rule ordering vs hit counts.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Rule Analysis"):
* Row 1 -- Single-value: "Unused rules", "Overly permissive rules", "High-deny rules".
* Row 2 -- Rule hit count table with concern flags.

Alerting:
* Warning (unused rules > 10): rule cleanup needed.
* Info (monthly report): rule hygiene review.

### Step 5 — - Troubleshooting

* **Unused rules** -- May be backup/legacy rules. Document and remove after confirming with stakeholders. Set a review period (30-90 days with logging).

* **Overly permissive rules** -- Break down into specific source/destination/service rules. Use firewall rule recommendation features: PA "Rule Usage" or "Expedition" tool.

* **Shadow rules** -- A rule that never matches because a prior rule is more general. Reorder rules or remove the shadowed rule. PA: Security Policy Optimizer identifies shadows.

## SPL

```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src) as unique_sources dc(dest) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).

## Known False Positives

Backup jobs, software updates, and seasonality change which rules see the most hits; expect drift over time.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
