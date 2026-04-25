<!-- AUTO-GENERATED from UC-2.6.59.json — DO NOT EDIT -->

---
id: "2.6.59"
title: "Citrix Analytics for Security Risk Indicators"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.59 · Citrix Analytics for Security Risk Indicators

## Description

Citrix Analytics for Security aggregates behavioral signals on access to virtual apps and data: anomalous authentication patterns, data-exfiltration heuristics, and composite insider-threat style scores. Forwarding these indicators into a security operations index lets analysts create high-fidelity detections, hunt across users and risk types, and tune response playbooks (step-up, session recording review, or account disable) without only relying on raw gateway noise. The goal is to surface the risk-ranked narrative Microsoft and Citrix already compute, enriched with your corporate identity context in downstream workflows.

## Value

Citrix Analytics for Security aggregates behavioral signals on access to virtual apps and data: anomalous authentication patterns, data-exfiltration heuristics, and composite insider-threat style scores. Forwarding these indicators into a security operations index lets analysts create high-fidelity detections, hunt across users and risk types, and tune response playbooks (step-up, session recording review, or account disable) without only relying on raw gateway noise. The goal is to surface the risk-ranked narrative Microsoft and Citrix already compute, enriched with your corporate identity context in downstream workflows.

## Implementation

Enable the Security data export in Citrix Cloud and connect Splunkbase 6280 with least-privilege API credentials. Classify `risk_type` into SOC tiers: authentication anomalies versus exfiltration signals versus insider risk. Send critical scores (for example 85 plus) to your incident queue with a direct link to Citrix Cloud investigation. Deduplicate on `user_principal` and five-minute windows to control noise. Add identity context from your directory or HR feed via lookup. Comply with privacy review before storing raw risk text in long retention.

## Detailed Implementation

Prerequisites
• Entitlements for Citrix Security Analytics; export job healthy in Citrix Cloud; 6280 app configured; dedicated index for sensitive signals with restricted roles.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map vendor fields, mask where required, and test volume. Align clock across Citrix and identity systems for correlation.

Step 2 — Create the search and alert
Start with a daily digest, then add real-time only for the highest decile. Wire response actions per your playbooks; avoid duplicate alerts for the same person from parallel products without correlation rules.

Step 3 — Validate
Reconcile sample events in Splunk with the Citrix console for the same user and time window; document any delay between cloud scoring and index arrival.

Step 4 — Operationalize
Train shifts on disambiguation between false job travel and true credential theft, and run quarterly false-positive reviews.

## SPL

```spl
index=citrix sourcetype="citrix:analytics:security"
| eval risk=tonumber(coalesce(risk_score, score, 0))
| eval rtype=lower(coalesce(risk_type, event_subtype, category, "unknown"))
| where risk>=70 OR like(rtype, "%exfil%") OR like(rtype, "%anomal%auth%") OR like(rtype, "%insider%")
| stats latest(risk) as max_risk, values(threat_vector) as vectors, count as event_count by user_principal, rtype
| sort - max_risk
| head 200
```

## Visualization

Stacked bar of risk events by type; top risky users table; Sankey or sequence chart from sign-in to risk event when fields allow.

## References

- [Citrix Analytics Add-on for Splunk (Splunkbase 6280)](https://splunkbase.splunk.com/app/6280)
- [Citrix Analytics for Security](https://docs.citrix.com/en-us/citrix-analytics/security-analytics.html)
