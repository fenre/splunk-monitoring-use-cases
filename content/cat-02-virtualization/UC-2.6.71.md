<!-- AUTO-GENERATED from UC-2.6.71.json — DO NOT EDIT -->

---
id: "2.6.71"
title: "Citrix ShareFile DLP Policy Violation Tracking"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.71 · Citrix ShareFile DLP Policy Violation Tracking

## Description

Data loss prevention in ShareFile surfaces policy hits, enforcements (block vs warn), and classification outcomes. Tracking hit volume, block and warn rates, trends that look like false positives, and file classification mismatches helps security and privacy teams prove control effectiveness, tune policies, and respond before regulated data leaves approved channels.

## Value

Data loss prevention in ShareFile surfaces policy hits, enforcements (block vs warn), and classification outcomes. Tracking hit volume, block and warn rates, trends that look like false positives, and file classification mismatches helps security and privacy teams prove control effectiveness, tune policies, and respond before regulated data leaves approved channels.

## Implementation

Ingest DLP or ShareFile security events with stable policy identifiers. Retain long enough for compliance reporting. Create hourly rollups and weekly anomaly review for `false_positive` spikes. For mismatches, join to label or sensitivity taxonomy in a lookup. Escalate sudden block-rate drops (possible policy bypass) and sustained warn-only surges (possible business friction).

## Detailed Implementation

Prerequisites
• DLP or ShareFile policy events in Splunk with `action`, `policy_id`, and user identity. Optional lookup for business unit and data owner per policy.

Step 1 — Configure data collection
Map vendor fields to `action` and a boolean for analyst-marked false positives if available. Enrich with group from identity if possible.

Step 2 — Create the search and alert
Build the base SPL, then add alerts: spike in `class_mismatches`, sudden drop in blocks with steady uploads, or false-positive count rising week over week for one policy (tuning needed).

Step 3 — Validate
Reconcile event counts to the admin console for a sample day. Test with a controlled warn-only policy in a lab if allowed.

Step 4 — Operationalize
Publish monthly compliance view of policy effectiveness; hand off tuning tasks to the data governance team with Splunk links.

## SPL

```spl
index=sharefile sourcetype="citrix:sharefile:dlp" earliest=-24h
| eval action=lower(coalesce(action, outcome, "unknown")), is_fp=if(match(lower(false_positive),"(?i)true|yes|1"),1,0), mismatch=if(match(lower(classification_mismatch),"(?i)true|yes|1"),1,0)
| bin _time span=1h
| stats count as hits, sum(eval(action="block")) as blocks, sum(eval(action="warn")) as warns, sum(is_fp) as fp_tags, sum(mismatch) as class_mismatches by _time, policy_id, user
| eval block_rate=round(100*blocks/hits,2), warn_rate=round(100*warns/hits,2)
| where blocks>0 OR warns>0 OR class_mismatches>0
| table _time, policy_id, user, hits, block_rate, warn_rate, fp_tags, class_mismatches
```

## Visualization

Stacked bar: block vs warn by policy; timechart: false-positive tagged rate; table: top users and policies by hits; line: classification mismatch count.

## References

- [Citrix — Data loss prevention for ShareFile](https://docs.citrix.com/en-us/citrix-content-collaboration/data-loss-prevention.html)
