---
id: "5.13.74"
title: "Catalyst Center Data Collection Health (Meta)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.74 · Catalyst Center Data Collection Health (Meta)

## Description

Monitors the health of the Catalyst Center data collection pipeline by checking event volume and freshness for each sourcetype, detecting collection failures or gaps.

## Value

All other Catalyst Center use cases depend on data flowing reliably. This meta-monitoring UC ensures the pipeline is healthy and catches collection failures early.

## Implementation

This UC uses existing TA inputs — no additional configuration needed beyond the standard TA setup. It monitors all `cisco:dnac:*` sourcetypes to verify:

1. **Event volume:** Each sourcetype should have events within the last 2 hours (based on TA polling intervals)
2. **Expected sourcetypes:** devicehealth, clienthealth, networkhealth, issue, compliance, securityadvisory, client, audit:logs, site:topology
3. **Freshness:** If any sourcetype's latest event is older than 2 hours, the TA input may have failed

Schedule this search as a daily health check and alert when any sourcetype shows 'Stale' status.

## Detailed Implementation

Prerequisites
• TA 7538 installed; `index=catalyst` receiving at least one `cisco:dnac:*` sourcetype from known-good inputs.

Step 1 — Expected coverage
- Cross-check **Inputs** in Splunk against the TA documentation for your version: each enabled input should map to a sourcetype under `cisco:dnac:*` (e.g. `cisco:dnac:devicehealth`, `cisco:dnac:issue`, `cisco:dnac:audit:logs`).
- HEC-based sourcetypes (e.g. event notifications) count as `cisco:dnac:*` if so named — include them in review.

Step 2 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:*" | stats count as event_count latest(_time) as last_event earliest(_time) as first_event by sourcetype | eval hours_since_last=round((now()-last_event)/3600,1) | eval status=if(hours_since_last>2,"Stale","Active") | sort -hours_since_last
```

Step 3 — Alerting
- Save as **scheduled** search (e.g. hourly) with `where status="Stale"` as a trigger; route to email/Slack/Ticket.
- Tune `2` hours per your slowest acceptable poll + buffer; never below the TA’s minimum interval for a given input.

Step 4 — Remediation
- **Stale:** restart the modular input, validate Catalyst Center API token, check network/DNS to DNAC, review `splunkd.log` and TA internal logs on the heavy forwarder.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:*" | stats count as event_count latest(_time) as last_event earliest(_time) as first_event by sourcetype | eval hours_since_last=round((now()-last_event)/3600,1) | eval status=if(hours_since_last>2,"Stale","Active") | sort -hours_since_last
```

## Visualization

Table: sourcetype, event_count, hours_since_last, status; heatmap for Stale vs Active; optional trend of event_count per sourcetype over 7 days.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
