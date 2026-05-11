<!-- AUTO-GENERATED from UC-5.1.49.json — DO NOT EDIT -->

---
id: "5.1.49"
title: "Port Access Control List (ACL) Hits and Block Events (Meraki MS)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.1.49 · Port Access Control List (ACL) Hits and Block Events (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with port access control list so the team can act before it grows into a bigger outage.*

---

## Description

Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.

## Value

Security teams analyze Meraki MS ACL deny events to validate access control policy effectiveness and detect scanning or unauthorized access attempts blocked at the switch layer.

## Implementation

1. Configure SC4S for Meraki MX syslog. 2. In Meraki Dashboard enable Flows syslog category (Network-wide -> General -> Reporting). 3. Filter pattern=deny* to surface blocked flows. 4. The pattern field comes from the Meraki message body 'pattern: allow all' or 'pattern: deny <rule_name>'. 5. To map blocked traffic back to specific firewall rules, name your rules descriptively in Meraki Dashboard -> Security & SD-WAN -> Firewall.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX appliance flow logs (type=flows pre MX18.101, type=firewall MX18.101+). Each event carries src=, dst=, mac=, protocol=, sport=, dport=, pattern=allow/deny. NOTE: Meraki MS switch ACLs do NOT emit per-rule hit counters to syslog; this UC tracks denied flows at the MX boundary instead. For switch-side ACL visibility use Meraki Dashboard -> Switch -> Switch ACL hit counters (UI only)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for Meraki MX syslog. 2. In Meraki Dashboard enable Flows syslog category (Network-wide -> General -> Reporting). 3. Filter pattern=deny* to surface blocked flows. 4. The pattern field comes from the Meraki message body 'pattern: allow all' or 'pattern: deny <rule_name>'. 5. To map blocked traffic back to specific firewall rules, name your rules descriptively in Meraki Dashboard -> Security & SD-WAN -> Firewall.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    pattern="deny*"
    earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"
| stats count as block_count by host, src_ip, dst_ip, src_mac
| sort - block_count
| head 50
```

#### Understanding this SPL

**Port Access Control List (ACL) Hits and Block Events (Meraki MS)** — Security teams analyze Meraki MS ACL deny events to validate access control policy effectiveness and detect scanning or unauthorized access attempts blocked at the switch layer.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX appliance flow logs (type=flows pre MX18.101, type=firewall MX18.101+). Each event carries src=, dst=, mac=, protocol=, sport=, dport=, pattern=allow/deny. NOTE: Meraki MS switch ACLs do NOT emit per-rule hit counters to syslog; this UC tracks denied flows at the MX boundary instead. For switch-side ACL visibility use Meraki Dashboard -> Switch -> Switch ACL hit counters (UI only). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host, src_ip, dst_ip, src_mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall)
    pattern="deny*"
    earliest=-24h
| rex "src=(?<src_ip>[\d\.]+)"
| rex "dst=(?<dst_ip>[\d\.]+)"
| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"
| stats count as block_count by host, src_ip, dst_ip, src_mac
| sort - block_count
| head 50
```

## Visualization

Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.

## Known False Positives

New security baselines, pen tests, and mis-pointed app VIPs can spike denies. Weed out scanners and approved tests via subnet lookup.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
