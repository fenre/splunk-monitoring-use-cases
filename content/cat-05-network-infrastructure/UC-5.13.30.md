<!-- AUTO-GENERATED from UC-5.13.30.json — DO NOT EDIT -->

---
id: "5.13.30"
title: "Compliance Status Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.30 · Compliance Status Trending

## Description

Tracks compliance status over time to measure remediation progress, detect compliance drift, and demonstrate continuous compliance for auditors.

## Value

Auditors want to see continuous compliance, not point-in-time snapshots. Trending demonstrates that compliance is maintained and that violations are remediated promptly.

## Implementation

Enable the `compliance` input. Use a 30-90d window for the timechart. If divisor is zero, handle nulls in a wrapper query or add a guard eval for empty days.

## Detailed Implementation

Prerequisites
• **compliance** modular input in the Cisco Catalyst Add-on (7538) writing `cisco:dnac:compliance` to `index=catalyst`.
• Complete **UC-5.13.28** first so you have validated `complianceStatus` and `complianceType` in raw events; this report uses the same `GET /dna/intent/api/v2/compliance/detail` feed.
• Default **30–90 day** time range for a credible trend; shorter windows are fine after a change freeze to prove recovery.
• `docs/implementation-guide.md` for GRC export paths and `catalyst` index retention for audit evidence.

Step 1 — Configure data collection
• **TA input** name: **compliance**; default poll **900 seconds**; assigned sourcetype `cisco:dnac:compliance`.
• **Event shape:** the TA can emit **multiple** rows per device and per `complianceType` each poll. This SPL **counts event rows** per day, not “unique devices.” For a true **per-device** daily score, pre-dedup in a subsearch or summary to **one row per device per day** (by policy family if you split dashboards).

Step 2 — Create the report
```spl
index=catalyst sourcetype="cisco:dnac:compliance" | timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant | eval compliance_pct=round(compliant*100/(compliant+non_compliant),1)
```

Understanding this SPL (ratio, empty days, policy scope)
• **Guard** division by zero: when `compliant+non_compliant=0` for a day, append `| eval compliance_pct=if((compliant+non_compliant)=0, null(), ...)` (or a small conditional `eval`) so charts do not show a fake zero percent.
• To trend **one** policy family, add a leading filter such as `complianceType="RUNNING_CONFIG"` to the base search—mixing **IMAGE** checks with **config** checks in one ratio can mislead executives without a shared denominator story.

**Pipeline walkthrough**
• `timechart span=1d` counts how many **COMPLIANT** vs **NON_COMPLIANT** **evaluations** occurred in each calendar day (Splunk’s **span** uses the search time zone unless you set `tz`).
• `compliance_pct` is the passing share of those two counted buckets for that day—document that **IN_PROGRESS** and **ERROR** are excluded unless you extend the `eval` list.

Step 3 — Validate
• Compare a given day’s **compliant** and **non_compliant** split to **Catalyst Center > Compliance** for the same **UTC** date; one-day skew often traces to **midnight** boundary or **double rows** per type.
• Run `| timechart count` without splits to catch long **flat zero** days that really mean **ingest** or **scoping** problems, not “perfect compliance.”

Step 4 — Operationalize (evidence)
• **Dashboard:** stacked area of `compliant` vs `non_compliant` with a line panel for `compliance_pct`; annotate known **CAB** or **upgrade** windows on the time axis for auditor narrative.
• **Evidence:** schedule **weekly** CSV or PDF to your GRC store; the **NIST/PCI** references in this UC’s `compliance` array describe how assessors use the artefact—keep the export path in your control matrix.

Step 5 — Troubleshooting
• **Flat 100%** while operators see red in Catalyst: `complianceStatus` **case** or **props** change after a TA upgrade—`fieldsummary complianceStatus` and compare a raw event to the UI.
• **Large step** in the line after a **device onboarding** wave: the **count** denominator jumped; split by `siteId` (if extracted) or add narrative to QBR slides.
• **Null** `compliance_pct` for weeks: the feed may be **IN_PROGRESS/ERROR** only; follow **UC-5.13.28** Step 5 to confirm on-controller jobs and API health.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" | timechart span=1d count(eval(complianceStatus="COMPLIANT")) as compliant count(eval(complianceStatus="NON_COMPLIANT")) as non_compliant | eval compliance_pct=round(compliant*100/(compliant+non_compliant),1)
```

## Visualization

Stacked area (compliant vs non_compliant), line chart of compliance_pct, annotations for change freezes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
