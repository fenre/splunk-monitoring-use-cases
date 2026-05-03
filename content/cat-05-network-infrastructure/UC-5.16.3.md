<!-- AUTO-GENERATED from UC-5.16.3.json — DO NOT EDIT -->

---
id: "5.16.3"
title: "Optimization Bypass Events (Pass-Through Traffic)"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-5.16.3 · Optimization Bypass Events (Pass-Through Traffic)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Operations, Security, Analytics &middot; **Wave:** Walk &middot; **Status:** Verified

*Sometimes traffic is supposed to skip the shortcut box on purpose, but sudden spikes in skipping can hide mistakes or attacks. We list what skipped the shortcut, where it went, and why so teams can fix rules calmly.*

---

## Description

Splunk aggregates appliance-reported pass-through decisions—whether driven by policy, encryption incompatibilities, or health fails—so unexpected bypass storms surface alongside destinations and applications responsible.

## Value

Engineering teams reconcile governance versus performance by proving which subnets ignore optimization while security reviewers confirm sensitive flows intentionally bypass interception without silently widening blind spots.

## Implementation

Normalize bypass syslog signatures per vendor revision, maintain exclusion CSV for approved maintenance bypass classes, alert when hourly bypass count exceeds rolling median by configurable sigma.

## Detailed Implementation

### Prerequisites
- Regex regression tests stored alongside TA because vendors rename tokens quarterly.
- Network CMDB linking `dst` to business owners for automated ticketing.
- Approval catalog describing compliant versus suspicious bypass reasons.

### Step 1 — Configure data collection
Ensure informational severity bypass logs are not filtered upstream; increase UDP buffers if bursts occur.

### Step 2 — Create the search and alert
Deploy SPL as `wanopt_bypass_top_talkers`; derivative alert uses `eventstats median(count) as med by vendor` then filters `count>3*med`.

### Step 3 — Validate
Replay anonymized PCAP slices matching bypass intervals and verify Splunk counts align with appliance CLI session dumps.

### Step 4 — Operationalize
Dashboard Sankey from vendor→application→reason; integrate with CMDB lookups for contact overlays.

### Step 5 — Troubleshooting
**Log floods:** throttle via summary indexing.**Ambiguous regex:** tighten with vendor TAC guidance.**Dual appliance pairs:** dedupe using `serial` fields to avoid double counting mirrored syslog.

## SPL

```spl
index=wanop OR index=network earliest=-24h
| eval v=lower(sourcetype)
| eval vendor=case(match(v,"riverbed|steelhead"),"Riverbed SteelHead",match(v,"silverpeak|edgeconnect"),"Silver Peak EdgeConnect",match(v,"citrix"),"Citrix SD-WAN WANOP",match(v,"zdx|zscaler"),"Zscaler Digital Experience","other")
| where vendor!="other"
| eval reason=coalesce(bypass_reason,rule_action,pass_through_reason,opt_action)
| eval bypass_flag=case(match(lower(coalesce(reason,"")),"bypass|pass[- ]?through|passthrough|non[- ]opt"),1,match(_raw,"(?i)(optimization bypass|passthrough|pass-through|ineligible|blacklisted flow)"),1,0)
| where bypass_flag=1
| eval dst=coalesce(dest_ip,destination,dst_subnet,"unknown")
| eval app=coalesce(application,app_name,service,"unknown")
| stats count by vendor host app dst reason
| sort - count
| head 200
```

## Visualization

Stacked bar bypass counts by reason; linked search table with drilldown to `_time` raw slices.

## Known False Positives

**Certificate pinning apps:** permanent intentional bypass.**Quarterly pen-tests:** red-team TLS probes mimic attacks.**Inline upgrades:** vendor-guided bypass windows.**Multicast replication:** protocols unsupported yet benign.

## References

- [Splunk Documentation — Rex command overview](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Rex)
- [Zscaler Help — Digital Experience (ZDX)](https://help.zscaler.com/zdx)
