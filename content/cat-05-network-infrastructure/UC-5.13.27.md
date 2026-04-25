<!-- AUTO-GENERATED from UC-5.13.27.json — DO NOT EDIT -->

---
id: "5.13.27"
title: "Issue Volume Anomaly Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.27 · Issue Volume Anomaly Detection

## Description

Detects statistically unusual spikes in assurance issue volume that may indicate a network event, failed change, or emerging attack.

## Value

A sudden surge in issues often correlates with a failed change, configuration push, or emerging infrastructure problem. Anomaly detection catches these faster than fixed thresholds.

## Implementation

Enable the `issue` input. Run over a time window with enough 4h buckets to estimate a stable baseline; tune the `2*stdev` multiplier for sensitivity. Use alongside change calendars for triage context.

## Detailed Implementation

Prerequisites
• **issue** data flowing (`cisco:dnac:issue`); **UC-5.13.22** to sanity-check a normal **4h** **timechart** before **stats**-based **anomaly** work.
• **Same-window** **eventstats** baseline as **UC-5.13.20** (network health): **changing** the **time** picker **changes** the **baseline**—set **lookback** policy in the runbook (**14d** or **30d** typical).
• **Dedup wisdom:** if each poll re-sends **all** open issues, **raw** **count** is meaningless—**fix** **ingest** first or **pre-aggregate** **`| bin ... | stats dc(issueId) as issue_count by _time`** in a v2 **macro**.
• `docs/implementation-guide.md` for **search** **cost** ( **eventstats** over long windows).

Step 1 — Configure data collection
• **Input:** **issue**; **interval** aligned with NOC’s comfort on **stale** **issues**.
• **Key:** stable **`issueId`** in raw events for any future **dedup** design.

Step 2 — Create the search or alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" | bin _time span=4h | stats count as issue_count by _time | eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues | where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0 | eval deviation=round((issue_count-baseline)/stdev_issues,1) | sort -deviation
```

Understanding this SPL (2-sigma on bucket counts)
• **Over-dispersed** data (many **zeros**, rare **huge** hours) can break **Gaussian** intuition—treat as **sensitivity** **triage**, not proof of a sev-1 on its own.
• For chatty networks, require (baseline + 3 × stdev_issues) instead of 2 × stdev, or lengthen the time window to stabilize stdev.
• **Parallel** `| timechart count` to see **genuine** **bursts** vs **ingest** **drop/restart** **artifacts**.

**Pipeline walkthrough**
• **4h** **buckets** align with **UC-5.13.22** for story consistency with leadership.

Step 3 — Validate
• **Change** **calendar** overlay: a **known** **bad** **Saturday** **cut** should show **rows**; if **not**, **sensitivity** is too low or **count** is **wrong** (dedup problem).
• **Compare** to **Catalyst** **UI** **issue** **counts** in the same **4h** **UTC** **window**.

Step 4 — Operationalize
• **Alert** to a Slack/Teams **investigate** channel with a **Catalyst Assurance** link; page only when paired with **device** or **client** health drops (see **UC-5.13.1**, **3**, **5**, and **9** in this set).
• **Table** **panel** of **deviation** for **postmortem** **Appendix**.

Step 5 — Troubleshooting
• **Hundreds of buckets:** **stdev** too small; **lengthen** lookback or **increase** **span** to **1d** for **strategic** **noise** **reduction**.
• **No buckets:** **count** is **0** in **all** **bins**—**ingest** **failure**; check **sourcetype** **first**.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | bin _time span=4h | stats count as issue_count by _time | eventstats avg(issue_count) as baseline stdev(issue_count) as stdev_issues | where issue_count > (baseline + 2*stdev_issues) AND stdev_issues > 0 | eval deviation=round((issue_count-baseline)/stdev_issues,1) | sort -deviation
```

## Visualization

Timechart of issue_count with reference lines, table of anomalous buckets with deviation score.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
