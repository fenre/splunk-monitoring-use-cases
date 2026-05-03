<!-- AUTO-GENERATED from UC-5.2.30.json — DO NOT EDIT -->

---
id: "5.2.30"
title: "Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.30 · Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We group blocked requests by country so data-location rules and blocked regions are easy to show to auditors in plain language.*

---

## Description

Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.

## Value

Security teams track Meraki MX geo-blocking enforcement by country and direction, validating geographic access policy effectiveness and identifying legitimate traffic requiring exceptions.

## Implementation

Ingest URL logs with GeoIP enrichment. Track blocks by geography.

## Detailed Implementation

### Prerequisites
* Meraki MX geo-blocking events. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `country`, `action` (block), `src_ip`, `dest_ip`.
* Meraki geo-blocking: MX can block inbound and outbound traffic based on source/destination country. Configured in Dashboard > Security & SD-WAN > Firewall > Layer 3. Uses Meraki's GeoIP database for classification.

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Firewall
# Add geo-based L3 rules blocking specific countries
# Syslog > Roles: Flows
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(_raw, "(?i)geo.*block|country.*block|country.*deny")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Geo-blocking event tracking:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| where match(pattern, "(?i)deny") OR match(action, "(?i)block|deny")
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip, dst)
| iplocation src prefix=src_
| iplocation dst prefix=dest_
| where isnotnull(src_Country) OR isnotnull(dest_Country)
| eval geo_direction=case(match(src, "^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)"), "OUTBOUND to ".dest_Country, 1==1, "INBOUND from ".src_Country)
| stats count as blocks dc(src) as unique_sources dc(dst) as unique_targets by geo_direction, src_Country, dest_Country
| sort -blocks | head 20
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Firewall -- check geo-based rules.
(b) Test with a VPN to a blocked country and verify block event.
(c) Compare with Meraki Dashboard event log.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Geo-Blocking"):
* Row 1 -- Single-value: "Geo blocks (4h)", "Blocked countries", "Unique blocked sources".
* Row 2 -- Geo-blocking by country.

### Step 5 — - Troubleshooting

* **Legitimate traffic blocked by geo-policy** -- CDN endpoints may be in blocked countries. Whitelist specific IPs or CIDR ranges while keeping country block active.

* **Geo-blocking not effective** -- Traffic may bypass via VPN/proxy. Combine with URL filtering to block proxy/VPN categories.

* **GeoIP misclassification** -- Some IPs may be classified in the wrong country. Check with external GeoIP databases (MaxMind, IP2Location).

## SPL

```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```

## Visualization

Geo-block map; country block count chart; policy compliance dashboard.

## Known False Positives

CDNs, VPN exit points, and roaming users can make geo policy blocks spike without a data breach.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
