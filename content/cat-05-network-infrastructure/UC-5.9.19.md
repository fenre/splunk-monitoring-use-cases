<!-- AUTO-GENERATED from UC-5.9.19.json — DO NOT EDIT -->

---
id: "5.9.19"
title: "ISP Performance Degradation Alerts"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.19 · ISP Performance Degradation Alerts

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We funnel all the network alarms from ThousandEyes into the same place where we see all our other alerts, so the team on call never misses a warning about an internet provider going down.*

---

## Description

Ingests ThousandEyes alert notifications into Splunk in near-real-time via webhook, providing a centralized view of ISP and network performance threshold violations alongside your other Splunk alerts. This bridges the gap between ThousandEyes' native alerting (which lives in the ThousandEyes UI) and your unified NOC monitoring in Splunk.

## Value

Most NOC teams monitor a single pane of glass — Splunk. If ThousandEyes alerts only fire in the ThousandEyes UI, they're invisible to the on-call team until someone manually checks. By streaming ThousandEyes alerts into Splunk, they appear alongside server alerts, application alerts, and infrastructure alerts in the same dashboard, the same alert queue, and the same PagerDuty integration. This eliminates the "nobody was watching ThousandEyes" failure mode. It also enables time-correlation: when a Splunk alert fires for application latency, the NOC can immediately see whether a ThousandEyes alert fired at the same time for the underlying network path — resolving the "is it the app or the network?" question in seconds.

## Implementation

Configure the Alerts Stream input: **Inputs → Alerts Stream → Create new input**. Select the ThousandEyes alert rules to receive. The app automatically creates a webhook integration in ThousandEyes and associates it with the selected alert rules. Alerts flow in real-time via HEC to `thousandeyes_alerts`.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured).
- **Alerts Stream input configured.** This is SEPARATE from the Tests Stream — Metrics input (UC-5.9.1) and the Events input (UC-5.9.18). Navigate to **Inputs → Alerts Stream → Create new input**.
  - The app lists all configured ThousandEyes alert rules.
  - Select which alert rules to stream to Splunk (select all, or choose critical ones).
  - The app automatically creates a webhook integration in ThousandEyes and associates it with the selected rules.
  - Alerts flow via HEC to the configured index.
- **Alert rule quality.** Before streaming to Splunk, ensure ThousandEyes alert rules are well-tuned: appropriate thresholds, sufficient rounds-of-violation, and reasonable suppression windows. Poorly tuned rules will flood Splunk with noise.
- **Index configuration:** Alerts go to `thousandeyes_alerts` (sourcetype `cisco:thousandeyes:alerts`). The macro used depends on the app version — some use `stream_index` with sourcetype filter, others use a dedicated alerts macro. Verify which pattern your deployment uses.

### Step 1 — Configure data collection
1. Navigate to **Inputs → Alerts Stream → Create new input**.
2. Select alert rules to receive. Start with critical rules (latency > threshold, loss > threshold, availability < 100%) and expand later.
3. The app creates a webhook in ThousandEyes automatically. Verify by checking **ThousandEyes → Alerts → Alert Rules → Notifications** — you should see a Splunk webhook listed.
4. Set the destination index to `thousandeyes_alerts`.
5. Save.

Verify:
```spl
index=thousandeyes_alerts sourcetype="cisco:thousandeyes:alerts" earliest=-24h
| stats count by alert.rule.name, severity
```
Note: alerts only appear when threshold violations occur. If no alerts fire in 24 hours, the network is healthy (or the alert rules are too relaxed). To test, temporarily lower a threshold in ThousandEyes to trigger an alert and verify it appears in Splunk.

### Step 2 — Create the search and alert
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" severity="critical" OR severity="warning"
| stats count earliest(_time) as first_fired latest(_time) as last_fired values(state) as states by alert.rule.name, alert.test.name, severity
| sort -count
```

**Understanding this SPL**

`sourcetype="cisco:thousandeyes:alerts"` — filters to alert data. Note: the `stream_index` macro may point to the same index as metrics (if all data goes to `thousandeyes_metrics`) or a different index (if alerts have their own index). The sourcetype filter ensures you only get alerts.

`severity="critical" OR severity="warning"` — filters to actionable alert levels. Info-level alerts are available for trending but shouldn't page anyone.

`values(state)` — shows the alert lifecycle: `active` means it's still firing; `cleared` means the threshold violation ended. If both `active` and `cleared` appear for the same rule in the search window, the alert fired and then cleared — a transient event.

**Active alert view** (for NOC real-time monitoring):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" state="active" earliest=-1h
| dedup alert.rule.name, alert.test.name
| table _time, alert.rule.name, alert.test.name, severity, thousandeyes.permalink
| sort -severity, -_time
```

**Alert noise analysis** (for tuning):
```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" earliest=-7d
| stats count as total_alerts dc(alert.test.name) as affected_tests by alert.rule.name
| eval alerts_per_day = round(total_alerts / 7, 1)
| sort -alerts_per_day
```
Rules firing > 10 times per day are candidates for threshold tuning.

**Scheduling:** For the active alert view: real-time or 1-minute scheduled search. For the summary view: cron `*/15 * * * *`, time range `-1h to now`.

### Step 3 — Validate
(a) **Trigger a test alert.** In ThousandEyes, temporarily lower a latency threshold to 1 ms for a test (guaranteed to fire). Verify the alert appears in Splunk within 60 seconds. Reset the threshold afterwards.

(b) **Cross-reference with ThousandEyes UI.** Navigate to **Alerts → Alert History** and compare with Splunk. Alert counts, timing, and severity should match.

(c) **Verify webhook connectivity.** If alerts don't appear in Splunk, check:
  - ThousandEyes → Alerts → Alert Rules → Notifications — is the Splunk webhook listed and active?
  - Is HEC reachable from ThousandEyes? The webhook sends to your HEC endpoint.
  - Check `index=_internal "HEC" "thousandeyes"` for HEC receipt confirmation.

### Step 4 — Operationalize
**Dashboard** ("ThousandEyes Alerts" or add to a unified NOC dashboard):
- Active alerts table: deduped, sorted by severity.
- Alert timeline: `| timechart span=15m count by severity` over 24 hours.
- Noisy rule analysis: top 10 rules by frequency for tuning.

**Integration with existing Splunk alerting:**
- Forward critical ThousandEyes alerts to PagerDuty/On-Call using Splunk alert actions.
- Enrich internal Splunk alerts with ThousandEyes context: when an application latency alert fires, a correlated ThousandEyes network alert provides immediate root cause.

**Runbook** (owner: NOC):
1. Critical ThousandEyes alert received. Open the `thousandeyes.permalink` to see the specific test and metric that violated the threshold.
2. Determine whether the alert represents an ISP issue (affect multiple tests/agents) or a target issue (affects tests to one target).
3. Cross-reference with UC-5.9.18 events — if an Internet Insights event exists for the same time/ISP, it's a confirmed ISP outage.
4. Take action based on root cause (ISP escalation, SD-WAN reroute, or internal investigation).

### Step 5 — Troubleshooting

- **No alerts in Splunk despite active alerts in ThousandEyes UI** — The Alerts Stream input may not be configured, or the webhook may be broken. Check the webhook status in ThousandEyes and HEC connectivity.

- **Alerts arriving but with empty/missing fields** — The sourcetype may not be parsing correctly. Check `index=thousandeyes_alerts | head 5 | fieldsummary` to see which fields are populated.

- **Too many alerts — alert fatigue** — Tune ThousandEyes alert rules: increase rounds-of-violation, add suppression windows, raise thresholds. Focus on critical/warning only in Splunk.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth, and general app troubleshooting.

## SPL

```spl
`stream_index` sourcetype="cisco:thousandeyes:alerts" severity="critical" OR severity="warning"
| stats count earliest(_time) as first_fired latest(_time) as last_fired values(state) as states by alert.rule.name, alert.test.name, severity
| sort -count
```

## Visualization

(1) Events timeline: alerts over 24 hours, colour-coded by severity. (2) Table: alert rule, test name, severity, state, count, first fired, last fired. (3) Pie chart: alerts by severity distribution. (4) Bar chart: top 10 alert rules by frequency — identifies the noisiest rules for tuning. (5) Combined panel: ThousandEyes alerts alongside internal Splunk alerts for the same time window.

## Known False Positives

**Flapping alert rules with aggressive thresholds.** If a ThousandEyes alert rule has a tight threshold (e.g., latency > 50 ms) without sufficient rounds-of-violation or suppression, the alert fires and clears repeatedly as the metric oscillates around the threshold. This floods Splunk with alert noise. Fix by tuning the ThousandEyes alert rule: increase the "number of rounds" requirement (e.g., 3 consecutive violations) or add ThousandEyes-side suppression.

**Alerts for test maintenance windows.** When agents are taken offline for maintenance or tests are temporarily disabled, threshold violations may fire during the transition. Distinguish by checking whether the alert corresponds to a known maintenance window.

**Duplicate alerts from multiple agents.** A single network issue may trigger alerts from multiple agents testing the same path. This is by design (confirms the issue is real, not agent-specific) but can look noisy. Group alerts by `alert.test.name` and time window to de-duplicate.

**Alerts for paths your users don't traverse.** If you have tests monitoring ISP paths "just in case," alerts from those tests may not represent actual user impact. Tag tests as "critical" or "informational" in ThousandEyes and filter Splunk alerts accordingly.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Alert Rules Configuration](https://docs.thousandeyes.com/product-documentation/alerts)
- [ThousandEyes Splunk App — Alerts Stream input](https://docs.thousandeyes.com/product-documentation/integration-guides/custom-built-integrations/splunk-app/inputs)
