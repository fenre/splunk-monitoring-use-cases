<!-- AUTO-GENERATED from UC-5.4.26.json — DO NOT EDIT -->

---
id: "5.4.26"
title: "Top Talker Analysis and Bandwidth Hogs (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.26 · Top Talker Analysis and Bandwidth Hogs (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch top talker analysis and bandwidth hogs (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.

## Value

Network operations teams monitor Meraki wireless health scores across all sites, grading each network on connection success, throughput, and latency to prioritize sites needing wireless optimization.

## Implementation

1. Configure SC4S for MR syslog and enable the Summary Top Clients by Usage input in Splunk_TA_cisco_meraki. 2. Syslog gives flow-count / protocol-distribution per client_mac (extracted via rex from the mac= field). 3. The Top Clients input polls GET /organizations/{orgId}/summary/top/clients/byUsage and returns the top 10 with usage.{total,upstream,downstream} in kB. 4. For full per-client byte accounting beyond top-10, use the Meraki Dashboard -> Network-wide -> Clients page (UI) or scrape /networks/{networkId}/clients/{clientId}/usageHistory with a custom modular input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for syslog flow records (which give protocol/port granularity but not byte counters), plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input (sourcetype=meraki:summarytopclientsbyusage, daily) for the org's top 10 clients by data volume in kB. NOTE: per-flow byte counters are NOT in Meraki syslog..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MR syslog and enable the Summary Top Clients by Usage input in Splunk_TA_cisco_meraki. 2. Syslog gives flow-count / protocol-distribution per client_mac (extracted via rex from the mac= field). 3. The Top Clients input polls GET /organizations/{orgId}/summary/top/clients/byUsage and returns the top 10 with usage.{total,upstream,downstream} in kB. 4. For full per-client byte accounting beyond top-10, use the Meraki Dashboard -> Network-wide -> Clients page (UI) or scrape /ne…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "mac=(?<client_mac>[0-9A-Fa-f:]+)"
| rex "protocol=(?<proto>\S+)"
| rex "dport=(?<dst_port>\d+)"
| stats count as flow_count,
        values(proto) as protos,
        values(dst_port) as dst_ports
         by client_mac, src_ip
| sort - flow_count
| head 20
| append [
    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h
    | stats latest(usage.total) as total_kb,
            latest(usage.upstream) as upload_kb,
            latest(usage.downstream) as download_kb
             by clientId, name, mac
    | sort - total_kb
    | head 20
  ]
```

#### Understanding this SPL

**Top Talker Analysis and Bandwidth Hogs (Meraki MR)** — Network operations teams monitor Meraki wireless health scores across all sites, grading each network on connection success, throughput, and latency to prioritize sites needing wireless optimization.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for syslog flow records (which give protocol/port granularity but not byte counters), plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input (sourcetype=meraki:summarytopclientsbyusage, daily) for the org's top 10 clients by data volume in kB. NOTE: per-flow byte counters are NOT in Meraki syslog. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by client_mac, src_ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.
- Appends rows from a subsearch with `append`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| where bytes>0
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Top Talker Analysis and Bandwidth Hogs (Meraki MR)** — Network operations teams monitor Meraki wireless health scores across all sites, grading each network on connection success, throughput, and latency to prioritize sites needing wireless optimization.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for syslog flow records (which give protocol/port granularity but not byte counters), plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input (sourcetype=meraki:summarytopclientsbyusage, daily) for the org's top 10 clients by data volume in kB. NOTE: per-flow byte counters are NOT in Meraki syslog. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
- Filters the current rows with `where bytes>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "mac=(?<client_mac>[0-9A-Fa-f:]+)"
| rex "protocol=(?<proto>\S+)"
| rex "dport=(?<dst_port>\d+)"
| stats count as flow_count,
        values(proto) as protos,
        values(dst_port) as dst_ports
         by client_mac, src_ip
| sort - flow_count
| head 20
| append [
    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h
    | stats latest(usage.total) as total_kb,
            latest(usage.upstream) as upload_kb,
            latest(usage.downstream) as download_kb
             by clientId, name, mac
    | sort - total_kb
    | head 20
  ]
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

## Known False Positives

Backup jobs, imaging, and video can create heavy wireless flows; confirm with the app owner before assuming abuse or a misbehaving client.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
