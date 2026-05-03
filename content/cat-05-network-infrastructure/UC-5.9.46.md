<!-- AUTO-GENERATED from UC-5.9.46.json — DO NOT EDIT -->

---
id: "5.9.46"
title: "ThousandEyes Alert Severity Distribution"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.46 · ThousandEyes Alert Severity Distribution

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Anomaly &middot; **Wave:** Walk &middot; **Status:** Verified

*We count and sort all our network alerts to find the ones that cry wolf too often, so we can fix them and make sure the real emergencies get noticed.*

---

## Description

Analyzes the distribution of ThousandEyes alerts by severity and rule name over a 7-day window. Identifies the noisiest alert rules (alert fatigue candidates), severity imbalances, and tuning opportunities. This is an operational health check for your ThousandEyes alerting configuration.

## Value

Alert fatigue is the #1 killer of monitoring effectiveness. If a single alert rule fires 500 times per week, operators stop paying attention to ALL alerts — including the critical ones. This UC surfaces the noisiest rules so they can be tuned (raise thresholds, increase rounds-of-violation, add suppression windows). It also reveals severity distribution: if 90% of alerts are "info" level, the alerting strategy may be too permissive. Conversely, if 90% are "critical," everything is over-prioritized and nothing stands out.

## Implementation

Uses the Alerts Stream input from UC-5.9.19. Analyze alert volume and distribution over time.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.19 apply — the Alerts Stream input must be configured (webhook → HEC push), delivering real-time alert notifications to `thousandeyes_alerts`.
- **At least 7 days of alert data.** This UC analyses a 7-day window. If the Alerts Stream was recently enabled, wait until enough data accumulates.
- **ThousandEyes alert rules configured.** Navigate to ThousandEyes → **Alerts → Alert Rules** and verify you have active rules. Each rule has a severity (`info`, `minor`, `major`, `critical`), a condition (metric threshold + rounds of violation), and target tests/agents. Understanding the rule configuration is essential for interpreting the distribution data in this UC.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_alerts` (or the index the `stream_index` macro resolves to for alerts).

### Step 1 — Configure data collection
The Alerts Stream input is configured in UC-5.9.19. No additional configuration is needed.

Verify alert data is present and spans 7 days:
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count earliest(_time) as first latest(_time) as last dc(alert.rule.name) as unique_rules
| eval first=strftime(first, "%Y-%m-%d %H:%M"), last=strftime(last, "%Y-%m-%d %H:%M")
```
If `unique_rules` is 0 or `count` is very low, either no alerts fired in 7 days (healthy environment or alerts not configured) or the Alerts Stream is not delivering data.

**Understanding alert data fields:**
- `alert.rule.name` — the name of the ThousandEyes alert rule (e.g., "High Latency - Production Servers").
- `alert.test.name` — the test that triggered the alert.
- `severity` — the severity assigned in the alert rule: `info`, `minor`, `major`, `critical`.
- `state` — alert state: `active` (alert firing), `cleared` (alert resolved).
- Each rule firing from each agent creates a separate alert event. A single rule firing across 10 agents generates 10 events. This inflates raw counts — use `dc()` (distinct count) to count unique incidents vs raw events.

### Step 2 — Create the search and report
**Alert severity distribution by rule (primary view):**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count as alert_count dc(alert.test.name) as affected_tests by alert.rule.name, severity
| eval alerts_per_day=round(alert_count/7,1)
| sort -alert_count
```

**Understanding this SPL**

`sourcetype="cisco:thousandeyes:alerts"` — essential filter. The `stream_index` macro returns both metrics and alerts, so the sourcetype filter isolates alert data.

`stats count as alert_count dc(alert.test.name) as affected_tests by alert.rule.name, severity` — for each rule + severity combination: `alert_count` is the total number of alert events (inflated by multi-agent rules), and `affected_tests` is how many distinct tests triggered this rule (a rule that fires for 20 tests is more concerning than one that fires for 1 test).

`alerts_per_day=round(alert_count/7,1)` — normalizes to a daily rate. Rules firing > 10 times per day are noise candidates. Rules firing < 1 time per day are either well-tuned or too insensitive.

`sort -alert_count` — noisiest rules first, so the team focuses on the biggest offenders.

**Noisy rule identification** (top candidates for tuning):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count dc(alert.test.name) as tests dc(thousandeyes.source.agent.name) as agents by alert.rule.name, severity
| eval per_day=round(count/7,1)
| eval agent_amplification=round(count/(tests*7),1)
| where per_day > 10
| sort -per_day
```
The `agent_amplification` metric shows how many alerts per test per day — a rule that fires from 20 agents for 1 test produces 20 events for a single incident. If `agent_amplification` is high, consider aggregating the rule to fire per-test (not per-agent).

**Severity distribution summary** (overall health of alerting strategy):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count by severity
| eventstats sum(count) as total
| eval pct=round(count/total*100,1)
| table severity, count, pct
```
Healthy distribution: ~60% info/minor (noise, background), ~30% major (investigation-worthy), ~10% critical (requires immediate action). If >50% are critical, everything is "top priority" and nothing stands out.

**Rule-to-noise ratio:**
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count as total_events dc(alert.rule.name) as unique_rules
| eval events_per_rule=round(total_events/unique_rules,1)
```
If `events_per_rule` > 50, a few rules are generating most of the noise. If `events_per_rule` < 5, alerting is well-tuned.

**Scheduling:** Weekly report: cron `0 9 * * 1` (Monday 9 AM), time range `-7d to now`. Generate a scheduled report (PDF) and email to the network operations manager for the weekly alerting hygiene review. For dashboard use, no scheduled alert — the dashboard runs on-demand.

### Step 3 — Validate
(a) **Cross-reference with ThousandEyes UI.** Navigate to **Alerts → Alert History** and compare the alert count for a specific rule with what Splunk shows. Counts may differ if the ThousandEyes UI deduplicates across agents while Splunk counts raw events.

(b) **Verify severity mapping.** Check that the `severity` values in Splunk match the severity configured in each ThousandEyes alert rule. Navigate to ThousandEyes → Alerts → Alert Rules → [select rule] and note the severity. Compare with `| stats values(severity) by alert.rule.name | head 5`.

(c) **Spot-check noisy rules.** For the noisiest rule, investigate whether the alerts represent real issues or false positives. If the rule fires 100 times/day but the underlying metric only briefly crosses the threshold before recovering, the rule needs a higher "rounds of violation" setting (e.g., require 3 consecutive violations instead of 1).

(d) **Check for missing rules.** Compare the alert rules in ThousandEyes with what appears in Splunk. If a rule exists in ThousandEyes but never appears in Splunk, either: (a) the rule hasn't fired in 7 days (good), or (b) the rule is not included in the Alerts Stream scope.

### Step 4 — Operationalize
**Dashboard** ("Alert Hygiene Report" — designed for weekly operations review):
- Row 1 — Single value tiles: "Total alerts this week" (with WoW trend arrow), "Unique alert rules that fired", "Noisiest rule" (name + count).
- Row 2 — Pie chart: severity distribution (info/minor/major/critical). If the pie is dominated by one colour, the severity assignments need rebalancing.
- Row 3 — Bar chart: top 10 noisiest rules, colour-coded by severity. This is the actionable view — each bar is a tuning candidate.
- Row 4 — Table: all rules with columns: rule name | severity | alert count | alerts/day | affected tests | agent amplification factor — sorted by alert count descending. Include a drill-down to the rule's specific alert timeline.

**Alerting (meta-alert):**
- A single rule fires > 50 times in 24 hours → email notification to network ops manager. This is an "alert about alerts" — a single noisy rule is drowning out everything else.

**Weekly alert hygiene review process** (owner: Network Operations Manager):
1. **Top 5 noisiest rules.** For each:
   (a) Is the underlying issue real and recurring? → Fix the root cause (capacity, misconfiguration, circuit degradation).
   (b) Is the threshold too sensitive for this metric? → Raise the threshold in ThousandEyes (e.g., latency threshold from 50 ms to 75 ms for non-critical paths).
   (c) Is the "rounds of violation" too low? → Increase from 1 to 3 (requires 3 consecutive violations before firing). This eliminates transient spike alerts.
   (d) Is the rule hitting too many agents? → Consider agent-specific suppression or aggregating alerts per-test instead of per-agent.
2. **Severity distribution.** If >70% of alerts are `info` level → consider removing info-level alert forwarding to Splunk (configure the Alerts Stream to only push `minor`+). If >50% are `critical` → everything is over-prioritized; downgrade rules for non-production tests to `major`.
3. **Rules with 0 fires.** Rules that haven't fired in 30 days may be unnecessary or have thresholds set too high. Review and either adjust or remove.
4. **New rules added.** Check UC-5.9.48 (Activity Log) for newly created rules. New rules should be monitored for their first week to validate the threshold.

### Step 5 — Troubleshooting

- **No alert data in Splunk** — The Alerts Stream input may not be configured, or the webhook/HEC endpoint is unreachable. See UC-5.9.19 Step 5 for Alerts Stream troubleshooting.

- **Alert counts seem inflated** — Multiple agents firing the same rule create multiple events. This is expected. Use `dc(alert.test.name)` to count unique incidents instead of raw events. Consider adding `| dedup alert.rule.name, alert.test.name, _time span=5m` to collapse multi-agent alerts.

- **Missing `alert.rule.name` field** — Check `| fieldsummary | search field=alert*`. The field name may vary between ThousandEyes versions. Also check `alertRuleName` (camelCase) as a possible alternative.

- **Severity field has unexpected values** — ThousandEyes uses `info`, `minor`, `major`, `critical`. If you see different values, the alert data may be coming from a non-ThousandEyes source that also uses the `stream_index` macro. Add `sourcetype="cisco:thousandeyes:alerts"` to filter precisely.

- **All common troubleshooting** — See UC-5.9.19 Step 5 for HEC webhook connectivity, OAuth token refresh, and general alert stream troubleshooting.

## SPL

```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count as alert_count dc(alert.test.name) as affected_tests by alert.rule.name, severity
| eval alerts_per_day=round(alert_count/7,1)
| sort -alert_count
```

## Visualization

(1) Pie chart: alert severity distribution. (2) Bar chart: top 10 noisiest alert rules. (3) Table: alert rules with count, severity, affected tests, alerts/day. (4) Timechart: alert volume trending by severity.

## Known False Positives

This is a meta-analysis UC — it analyzes alerting patterns, not network issues. No false positives in the traditional sense. However, alert counts may be inflated by test configuration (more agents per test = more alert instances per incident).

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes alert rule best practices](https://docs.thousandeyes.com/product-documentation/alerts)
