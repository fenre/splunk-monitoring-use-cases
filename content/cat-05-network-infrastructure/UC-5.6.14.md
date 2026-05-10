<!-- AUTO-GENERATED from UC-5.6.14.json — DO NOT EDIT -->

---
id: "5.6.14"
title: "DNS Resolution Performance and Failures (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.14 · DNS Resolution Performance and Failures (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.

## Value

Network operations teams monitoring Meraki-managed sites detect DNS resolution failures and upstream resolver health issues per site, enabling rapid failover to backup resolvers before users experience connectivity problems.

## Implementation

1. Choose a DNS source you actually operate: Infoblox (sourcetype=infoblox:dns:query), BIND (sourcetype=bind, query log enabled), Microsoft DNS (sourcetype=msad:nt6:dns), or Splunk Stream (sourcetype=stream:dns). 2. resolution_time_ms / response_time_ms / duration_ms are typical field names depending on source. 3. For wire-data deployment, install Splunk Stream or use Cisco Cyber Vision -> Splunk for OT-side DNS visibility. 4. Pair with Meraki MX flow logs (type=flows dport=53) for client-IP context.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: DNS server logs from your authoritative / recursive resolver (Infoblox, BIND, Microsoft DNS) or DNS wire data (Splunk Stream sourcetype=stream:dns). NOTE: Meraki does NOT log DNS resolution time. Meraki MX syslog only records the DHCP lease (which references the offered DNS server), not actual DNS query performance. This UC has been pivoted to the customer's actual DNS infrastructure..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Choose a DNS source you actually operate: Infoblox (sourcetype=infoblox:dns:query), BIND (sourcetype=bind, query log enabled), Microsoft DNS (sourcetype=msad:nt6:dns), or Splunk Stream (sourcetype=stream:dns). 2. resolution_time_ms / response_time_ms / duration_ms are typical field names depending on source. 3. For wire-data deployment, install Splunk Stream or use Cisco Cyber Vision -> Splunk for OT-side DNS visibility. 4. Pair with Meraki MX flow logs (type=flows dport=53) for client-IP con…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dns sourcetype IN ("infoblox:dns:query","bind","stream:dns","dns")
    earliest=-24h
| eval resolution_ms = coalesce(resolution_time_ms, response_time_ms, duration_ms)
| where isnum(resolution_ms)
| stats avg(resolution_ms) as avg_dns_ms,
        max(resolution_ms) as max_dns_ms,
        count
         by src, dest
| where avg_dns_ms > 100
| sort - avg_dns_ms
```

#### Understanding this SPL

**DNS Resolution Performance and Failures (Meraki)** — Network operations teams monitoring Meraki-managed sites detect DNS resolution failures and upstream resolver health issues per site, enabling rapid failover to backup resolvers before users experience connectivity problems.

Documented **Data sources**: DNS server logs from your authoritative / recursive resolver (Infoblox, BIND, Microsoft DNS) or DNS wire data (Splunk Stream sourcetype=stream:dns). NOTE: Meraki does NOT log DNS resolution time. Meraki MX syslog only records the DHCP lease (which references the offered DNS server), not actual DNS query performance. This UC has been pivoted to the customer's actual DNS infrastructure. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dns.

**Pipeline walkthrough**

- Scopes the data: index=dns, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `eval` defines or adjusts **resolution_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnum(resolution_ms)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by src, dest** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where avg_dns_ms > 100` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

**DNS Resolution Performance and Failures (Meraki)** — Network operations teams monitoring Meraki-managed sites detect DNS resolution failures and upstream resolver health issues per site, enabling rapid failover to backup resolvers before users experience connectivity problems.

Documented **Data sources**: DNS server logs from your authoritative / recursive resolver (Infoblox, BIND, Microsoft DNS) or DNS wire data (Splunk Stream sourcetype=stream:dns). NOTE: Meraki does NOT log DNS resolution time. Meraki MX syslog only records the DHCP lease (which references the offered DNS server), not actual DNS query performance. This UC has been pivoted to the customer's actual DNS infrastructure. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Resolution.DNS` — enable acceleration for that model.
- Filters the current rows with `where count>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge showing average DNS time; histogram of query times; slow query detail table.

## SPL

```spl
index=dns sourcetype IN ("infoblox:dns:query","bind","stream:dns","dns")
    earliest=-24h
| eval resolution_ms = coalesce(resolution_time_ms, response_time_ms, duration_ms)
| where isnum(resolution_ms)
| stats avg(resolution_ms) as avg_dns_ms,
        max(resolution_ms) as max_dns_ms,
        count
         by src, dest
| where avg_dns_ms > 100
| sort - avg_dns_ms
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

## Visualization

Gauge showing average DNS time; histogram of query times; slow query detail table.

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
