<!-- AUTO-GENERATED from UC-5.2.24.json — DO NOT EDIT -->

---
id: "5.2.24"
title: "Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.24 · Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at how traffic is shaped and marked so the team can see whether important apps still get a fair share when the link is full.*

---

## Description

Measures the impact of traffic shaping policies on bandwidth distribution and priority.

## Value

Operations teams evaluate Meraki MX traffic shaping effectiveness by application category, identifying over-shaped critical applications and under-shaped bandwidth hogs.

## Implementation

1. Configure SC4S for MX syslog (Flows category enabled in Meraki Dashboard). 2. Use rex to extract src/dst/protocol/port. 3. Enable the Summary Top Clients by Usage input for the org-wide top 10. 4. For genuine QoS health monitoring use Meraki Dashboard -> Security & SD-WAN -> Traffic shaping -> [rule] usage graphs (UI only); the Dashboard API does not expose per-rule shaped/dropped byte counters.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for L3 firewall flows from the MX, plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input (sourcetype=meraki:summarytopclientsbyusage) for top-talker context. NOTE: Meraki MX traffic-shaping uses a token-bucket algorithm and does NOT emit per-queue drop counters; QoS effectiveness can only be inferred indirectly from flow distribution and top-talker usage..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog (Flows category enabled in Meraki Dashboard). 2. Use rex to extract src/dst/protocol/port. 3. Enable the Summary Top Clients by Usage input for the org-wide top 10. 4. For genuine QoS health monitoring use Meraki Dashboard -> Security & SD-WAN -> Traffic shaping -> [rule] usage graphs (UI only); the Dashboard API does not expose per-rule shaped/dropped byte counters.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "protocol=(?<proto>\S+)"
| rex "(?:dport|sport)=(?<port>\d+)"
| stats count as flow_count by proto, port
| sort - flow_count
| head 20
| append [
    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h
    | stats latest(usage.total) as total_kb,
            latest(usage.upstream) as upstream_kb,
            latest(usage.downstream) as downstream_kb
             by clientId, name, mac
    | sort - total_kb
    | head 10
  ]
```

#### Understanding this SPL

**Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)** — Operations teams evaluate Meraki MX traffic shaping effectiveness by application category, identifying over-shaped critical applications and under-shaped bandwidth hogs.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for L3 firewall flows from the MX, plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input (sourcetype=meraki:summarytopclientsbyusage) for top-talker context. NOTE: Meraki MX traffic-shaping uses a token-bucket algorithm and does NOT emit per-queue drop counters; QoS effectiveness can only be inferred indirectly from flow distribution and top-talker usage. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by proto, port** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "protocol=(?<proto>\S+)"
| rex "(?:dport|sport)=(?<port>\d+)"
| stats count as flow_count by proto, port
| sort - flow_count
| head 20
| append [
    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h
    | stats latest(usage.total) as total_kb,
            latest(usage.upstream) as upstream_kb,
            latest(usage.downstream) as downstream_kb
             by clientId, name, mac
    | sort - total_kb
    | head 10
  ]
```

## Visualization

Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.

## Known False Positives

Overnight jobs, large downloads, and guest traffic can shift which queues look busy; compare to known workloads.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
