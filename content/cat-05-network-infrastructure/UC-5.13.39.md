<!-- AUTO-GENERATED from UC-5.13.39.json — DO NOT EDIT -->

---
id: "5.13.39"
title: "Advisory Severity Distribution and Risk Scoring"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.39 · Advisory Severity Distribution and Risk Scoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability &middot; **Wave:** Walk &middot; **Status:** Verified

*We calculate a single risk number that tells your security leadership how exposed the network is to known vulnerabilities right now. A high number means there are serious weaknesses that need fixing urgently. A declining number over time means your patching efforts are reducing the risk.*

---

## Description

Analyses the severity distribution of active security advisories and computes a weighted risk score across the fleet, giving the security team a single metric for overall vulnerability exposure and enabling risk-based prioritisation of firmware upgrade campaigns.

## Value

Not all advisory counts are equal. 20 MEDIUM advisories is less urgent than 3 CRITICAL ones. This UC provides a weighted risk score (CRITICAL=10, HIGH=5, MEDIUM=2, LOW=1) that collapses the multi-severity landscape into a single number the CISO can track. The distribution view also reveals whether your exposure is concentrated (a few CRITICAL PSIRTs on many devices) or diffused (many LOW advisories on few devices) — which determines whether you need an emergency firmware campaign or a steady-state upgrade cadence.

## Implementation

Same `securityadvisory` input as UC-5.13.34. Compute risk score with `eval` weighting. Schedule weekly.

## Detailed Implementation

### Prerequisites
- UC-5.13.34 (PSIRT Overview) must be operational — same `securityadvisory` data feed.
- Agree with the security team on the risk weighting formula: the default uses CRITICAL=10, HIGH=5, MEDIUM=2, LOW=1. This produces a single composite risk score that collapses the multi-severity advisory landscape into a trackable number. Adjust weights based on your organisation's risk appetite — some organisations prefer CVSS base scores, others use internal risk ratings.
- This UC is designed for the CISO dashboard — a single number that answers 'what is our vulnerability exposure right now?' and trends over quarters.

### Step 1 — Configure data collection
Same `securityadvisory` input as UC-5.13.34. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| stats dc(advisoryId) as advisories sum(deviceCount) as affected by severity
| eval weight=case(severity="CRITICAL",10,severity="HIGH",5,severity="MEDIUM",2,severity="LOW",1,1==1,0)
| eval risk_score=advisories * weight
| eventstats sum(risk_score) as total_risk
| table severity, advisories, affected, weight, risk_score, total_risk
| sort -weight
```

Why weighted risk score: not all advisory counts are equal. 20 MEDIUM advisories represent less risk than 3 CRITICAL advisories. The weighted score collapses the multi-severity landscape into a single number. A declining `total_risk` means remediation is outpacing new advisory publications. A growing `total_risk` means exposure is increasing — the firmware upgrade cadence needs to be accelerated.

Why `advisories * weight` not `affected * weight`: the risk score is per-advisory, not per-device. An advisory affecting 200 devices is one vulnerability that needs one firmware fix — the device count affects the remediation *effort* but not the number of distinct *risks*. Use `sum(affected * weight)` for an effort-weighted variant that prioritises high-blast-radius advisories.

Why `where deviceCount > 0`: excludes advisories that don't affect your fleet. Their weight should not inflate the risk score.

For risk score trending (CISO dashboard KPI):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| eval weight=case(severity="CRITICAL",10,severity="HIGH",5,severity="MEDIUM",2,severity="LOW",1,1==1,0)
| timechart span=1w sum(eval(weight)) as weekly_risk
| trendline sma4(weekly_risk) as four_week_avg
```
A declining `weekly_risk` with a downward `four_week_avg` trend is the strongest evidence that vulnerability management investment is reducing exposure.

For per-device risk scoring (which devices carry the most risk):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| eval weight=case(severity="CRITICAL",10,severity="HIGH",5,severity="MEDIUM",2,severity="LOW",1,1==1,0)
| stats sum(weight) as device_risk dc(advisoryId) as advisory_count by deviceId
| lookup catalyst_device_lookup deviceId OUTPUT deviceName, platformId
| sort -device_risk
| head 20
```
The top devices by `device_risk` are the priority firmware upgrade targets.

Schedule: monthly (cron `0 7 1 * *`), output to the CISO dashboard. Weekly for the security operations team.

### Step 3 — Validate
(a) Sum `advisories` across all severities. Should match UC-5.13.34's total advisory count (with `deviceCount > 0` filter).

(b) The `total_risk` should be dominated by CRITICAL advisories if any exist — verify that a single CRITICAL advisory with weight=10 contributes more than multiple LOW advisories.

(c) Compare risk score month-over-month: is it going up or down? The direction should align with your firmware campaign activity.

(d) Check the per-device risk variant: the top-risk device should be running the oldest firmware (most advisory exposure). Verify with `show version` on the device.

(e) Vendor UI parity: no direct equivalent in Catalyst Center — this is a Splunk-native analytics layer on top of the Catalyst Center data.

### Step 4 — Operationalize
- CISO dashboard: single-value tile of `total_risk` with month-over-month trend arrow (green ↓, red ↑).
- Quarterly security review: risk score trend over 90 days with firmware campaign annotations showing cause and effect.
- Remediation ROI: each firmware campaign should produce a measurable risk score decrease. If a campaign upgraded 200 devices and reduced `total_risk` by 40 points, the ROI is documented.
- SLA tracking: define a target risk score ceiling (e.g., `total_risk < 50`). Track compliance against the ceiling monthly.

Runbook (owner: CISO / Security Operations Manager):
1. Monthly: review risk score. If increasing, identify which severity is driving the increase.
2. CRITICAL component growing: there are unpatched critical vulnerabilities — escalate to emergency firmware campaign.
3. HIGH component growing: planned upgrades are falling behind — increase firmware campaign frequency.
4. MEDIUM/LOW growing: normal advisory publication cadence — include in next quarterly upgrade cycle.
5. Overall risk score declining: good — document the improvement for the board.

### Step 5 — Troubleshooting

- **Risk score is 0** — no advisories with affected devices. This is the ideal state. Continue monitoring monthly.

- **Risk score jumps suddenly** — a new CRITICAL advisory was published. Check UC-5.13.35 for the alert.

- **Risk score doesn't decrease after patching** — new advisories may be offsetting the remediation. Check the trend by severity to isolate which component is growing.

- **Weight values feel wrong** — adjust the `case()` weights to match your organisation's risk tolerance. Some organisations use CVSS base scores: `| eval weight=round(cvss_score,0)` if CVSS is available in the advisory data.

- **Severity values unexpected** — check `| stats values(severity)` for the actual strings. Adjust the `case()` accordingly.

- **Want device-level risk** — use the per-device variant from Step 2.

- **Missing INFORMATIONAL severity** — some TA versions include INFORMATIONAL advisories. Weight them at 0 to exclude from risk scoring.

- **Risk score trend is volatile week-to-week** — smooth with `| trendline sma4(weekly_risk)` for a 4-week moving average. Short-term volatility from advisory publication batches is normal; the SMA shows the structural trend.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| where deviceCount > 0
| stats dc(advisoryId) as advisories sum(deviceCount) as affected by severity
| eval weight=case(severity="CRITICAL",10,severity="HIGH",5,severity="MEDIUM",2,severity="LOW",1,1==1,0)
| eval risk_score=advisories * weight
| eventstats sum(risk_score) as total_risk
| table severity, advisories, affected, weight, risk_score, total_risk
| sort -weight
```

## Visualization

(1) Pie/donut: advisory count by severity. (2) Single value: weighted risk score. (3) Table: severity, advisory_count, total_affected_devices, weighted_score. (4) Trend: risk score over time from `| timechart span=1w` to show whether overall risk is declining.

## Known False Positives

**Risk score calculation skewed by a few CRITICAL advisories affecting many devices.** The risk scoring formula that weights severity times affected devices may produce a disproportionately high score if one CRITICAL advisory affects 100+ devices. Distinguish by breaking down the risk score by advisory to identify which single advisory is driving the score. Do not suppress — the score is mathematically correct, but provide context on which advisory contributes most.

**INFORMATIONAL advisories included in the severity distribution.** INFORMATIONAL advisories (vendor recommendations, configuration best practices) may be included in the severity distribution chart without representing actual vulnerabilities. Distinguish by checking whether `severity=INFORMATIONAL` entries have `deviceCount=0`. Suppress by filtering `| where severity!="INFORMATIONAL"` for vulnerability dashboards.

**Advisory severity assessment changing between Catalyst Center versions.** Catalyst Center may apply different severity assessment methodologies across versions, causing the severity distribution to shift after an upgrade. Distinguish by checking whether the severity distribution changed coincident with a Catalyst Center upgrade. No suppression needed — re-baseline the distribution after the upgrade.

**Duplicate advisory entries for the same CVE under different advisory IDs.** Some CVEs may be referenced by multiple Cisco advisory IDs (e.g., a combined advisory and a per-component advisory). Distinguish by checking `| stats dc(advisoryId) by cveId | where count>1`. Suppress by deduplicating on `cveId` when computing vulnerability counts.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
