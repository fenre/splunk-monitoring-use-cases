<!-- AUTO-GENERATED from UC-5.2.38.json — DO NOT EDIT -->

---
id: "5.2.38"
title: "Connection Rate Analysis and DOS Detection (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.38 · Connection Rate Analysis and DOS Detection (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We look at new connection rates on small office traffic so floods, scans, and misbehaving clients stand out from everyday browsing.*

---

## Description

Detects denial of service attacks by analyzing abnormal connection establishment rates.

## Value

SOC teams detect denial-of-service attacks against Meraki MX firewalls by analyzing connection rate anomalies and IDS/IPS threat events, enabling rapid incident response.

## Implementation

1. Configure SC4S for MX syslog with Flows category enabled in Meraki Dashboard. 2. Each flow event carries src=, dst=, mac=, protocol=, sport=, dport=, pattern. 3. Threshold > 1000 new TCP flows per minute per source is a strong DoS / scanning indicator. 4. For SYN-flag-aware detection deploy a Snort sensor and ingest its alerts via the existing IDS/IPS pipeline; Meraki MX flow logs do not carry TCP flag detail.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) receiving MX L3 firewall flow logs. NOTE: Meraki MX flow records do NOT expose individual TCP flag bits; only the protocol, src/dst, sport/dport, and pattern (allow/deny) are emitted. This UC monitors absolute new-connection rate per source IP as a DoS indicator..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog with Flows category enabled in Meraki Dashboard. 2. Each flow event carries src=, dst=, mac=, protocol=, sport=, dport=, pattern. 3. Threshold > 1000 new TCP flows per minute per source is a strong DoS / scanning indicator. 4. For SYN-flag-aware detection deploy a Snort sensor and ingest its alerts via the existing IDS/IPS pipeline; Meraki MX flow logs do not carry TCP flag detail.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    protocol="tcp"
    earliest=-1h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "dport=(?<dst_port>\d+)"
| timechart span=1m count as new_connections by src_ip useother=false limit=10
| where new_connections > 1000
```

#### Understanding this SPL

**Connection Rate Analysis and DOS Detection (Meraki MX)** — SOC teams detect denial-of-service attacks against Meraki MX firewalls by analyzing connection rate anomalies and IDS/IPS threat events, enabling rapid incident response.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) receiving MX L3 firewall flow logs. NOTE: Meraki MX flow records do NOT expose individual TCP flag bits; only the protocol, src/dst, sport/dport, and pattern (allow/deny) are emitted. This UC monitors absolute new-connection rate per source IP as a DoS indicator. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `timechart` plots the metric over time using **span=1m** buckets with a separate series **by src_ip useother=false limit=10** — ideal for trending and alerting on this use case.
- Filters the current rows with `where new_connections > 1000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

**Connection Rate Analysis and DOS Detection (Meraki MX)** — SOC teams detect denial-of-service attacks against Meraki MX firewalls by analyzing connection rate anomalies and IDS/IPS threat events, enabling rapid incident response.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) receiving MX L3 firewall flow logs. NOTE: Meraki MX flow records do NOT expose individual TCP flag bits; only the protocol, src/dst, sport/dport, and pattern (allow/deny) are emitted. This UC monitors absolute new-connection rate per source IP as a DoS indicator. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
- Filters the current rows with `where count>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Connection rate timeline; source IP detail table; DOS alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    protocol="tcp"
    earliest=-1h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "dport=(?<dst_port>\d+)"
| timechart span=1m count as new_connections by src_ip useother=false limit=10
| where new_connections > 1000
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action All_Traffic.dvc span=1h
| where count>0
| sort -count
```

## Visualization

Connection rate timeline; source IP detail table; DOS alert dashboard.

## Known False Positives

Scanners, new internet-facing apps, and broken clients can look like a SYN flood in raw statistics.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
