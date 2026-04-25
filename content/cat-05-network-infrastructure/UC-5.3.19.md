<!-- AUTO-GENERATED from UC-5.3.19.json — DO NOT EDIT -->

---
id: "5.3.19"
title: "Citrix ADC Content Switching Policy Hit Rate (NetScaler)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.19 · Citrix ADC Content Switching Policy Hit Rate (NetScaler)

## Description

Content switching vServers route HTTP/HTTPS requests to different load-balancing vServers based on URL patterns, headers, cookies, or other request attributes. Misconfigured content switching policies result in traffic hitting the default (catch-all) policy or being routed to the wrong back-end. Monitoring policy hit rates validates that routing rules are working as intended and identifies policies that are never triggered (candidate for cleanup or misconfiguration).

## Value

Content switching vServers route HTTP/HTTPS requests to different load-balancing vServers based on URL patterns, headers, cookies, or other request attributes. Misconfigured content switching policies result in traffic hitting the default (catch-all) policy or being routed to the wrong back-end. Monitoring policy hit rates validates that routing rules are working as intended and identifies policies that are never triggered (candidate for cleanup or misconfiguration).

## Implementation

Poll the NITRO API `csvserver_cspolicy_binding` to get bound policies with hit counts. Alternatively, enable AppFlow on content switching vServers to capture per-request routing decisions. Run the scripted input every 15 minutes. Flag: policies with zero hits over 7 days (never triggered — misconfigured or obsolete), the default policy receiving more than 20% of traffic (indicates missing specific rules), and sudden shifts in policy hit distribution (routing change after configuration update). Content switching is critical for multi-tenant environments where different applications share a single VIP.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling Citrix ADC NITRO API.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:cs"` fields `cs_vserver`, `policy_name`, `hits`, `target_lbvserver`, `priority`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the NITRO API `csvserver_cspolicy_binding` to get bound policies with hit counts. Alternatively, enable AppFlow on content switching vServers to capture per-request routing decisions. Run the scripted input every 15 minutes. Flag: policies with zero hits over 7 days (never triggered — misconfigured or obsolete), the default policy receiving more than 20% of traffic (indicates missing specific rules), and sudden shifts in policy hit distribution (routing change after configuration update). C…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:cs"
| stats latest(hits) as total_hits, latest(target_lbvserver) as target, latest(priority) as priority by cs_vserver, policy_name, host
| eventstats sum(total_hits) as vserver_total_hits by cs_vserver
| eval hit_pct=if(vserver_total_hits>0, round(total_hits/vserver_total_hits*100,1), 0)
| sort cs_vserver, priority
| table cs_vserver, policy_name, priority, target, total_hits, hit_pct
```

Understanding this SPL

**Citrix ADC Content Switching Policy Hit Rate (NetScaler)** — Content switching vServers route HTTP/HTTPS requests to different load-balancing vServers based on URL patterns, headers, cookies, or other request attributes. Misconfigured content switching policies result in traffic hitting the default (catch-all) policy or being routed to the wrong back-end. Monitoring policy hit rates validates that routing rules are working as intended and identifies policies that are never triggered (candidate for cleanup or misconfiguration).

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:cs"` fields `cs_vserver`, `policy_name`, `hits`, `target_lbvserver`, `priority`. **App/TA** (typical add-on context): Custom scripted input polling Citrix ADC NITRO API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:cs. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:cs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cs_vserver, policy_name, host** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by cs_vserver** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hit_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix ADC Content Switching Policy Hit Rate (NetScaler)**): table cs_vserver, policy_name, priority, target, total_hits, hit_pct

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (hit rate by policy), Table (policies with hit counts), Timechart (default policy hit rate trending).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=network sourcetype="citrix:netscaler:cs"
| stats latest(hits) as total_hits, latest(target_lbvserver) as target, latest(priority) as priority by cs_vserver, policy_name, host
| eventstats sum(total_hits) as vserver_total_hits by cs_vserver
| eval hit_pct=if(vserver_total_hits>0, round(total_hits/vserver_total_hits*100,1), 0)
| sort cs_vserver, priority
| table cs_vserver, policy_name, priority, target, total_hits, hit_pct
```

## Visualization

Bar chart (hit rate by policy), Table (policies with hit counts), Timechart (default policy hit rate trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
