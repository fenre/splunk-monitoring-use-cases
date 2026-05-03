<!-- AUTO-GENERATED from UC-5.7.14.json — DO NOT EDIT -->

---
id: "5.7.14"
title: "Geo-IP Flow Enrichment and Unexpected Country Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.14 · Geo-IP Flow Enrichment and Unexpected Country Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Risk &middot; **Wave:** Walk &middot; **Status:** Verified

*We tag outside destinations with where in the world they sit and compare that to the places we normally do business. When something lands outside that familiar list, we look closer without reading every line ourselves.*

---

## Description

Adds geography to destination addresses on flows leaving private space and highlights destinations whose country is absent from an approved-country lookup so investigators focus on unfamiliar regions quickly.

## Value

Security operations reduces dwell time for jurisdictional policy breaches, supports data-residency attestations with evidence of unexpected regions, and prioritizes incident tickets using geographic context without waiting on firewall logs.

## Implementation

Schedule recurring geography database updates; maintain `expected_peer_countries.csv`; filter RFC1918 and carrier-grade Network Address Translation ranges; tune byte and host-count floors.

## Detailed Implementation

### Prerequisites
- Legal-approved list of countries permitted for routine business traffic; separate lists for sensitive subnets.
- Accurate MaxMind or equivalent database mapped through `transforms.conf` as automatic lookups or invoked explicitly.
- Consensus whether to evaluate source geography for inbound denial-of-service contexts—this UC focuses on outbound discovery.

### Step 1 — Configure data collection
Prefer indexer-time enrichment for volume efficiency; if search-time `iplocation` is used, restrict summaries with transforms or summaries-only accelerated searches.

### Step 2 — Create the search
Extend SPL with `| lookup sensitive_src_segments.csv src OUTPUT tier` and multiply thresholds when tier equals restricted. Add threat-intelligence joins sparingly to avoid cartesian explosion.

### Step 3 — Validate
Pick three known Software-as-a-Service endpoints across approved regions and confirm absence from alerts. Synthetic tests via authorized cloud shells should appear once then be allowlisted.

### Step 4 — Operationalize
Dashboard tabs split by business unit using asset lookups; automated ticketing includes geo_city and autonomous-system summaries when available.

### Step 5 — Troubleshooting
Carrier proxies and virtual private network egress nodes skew geography—maintain `vpn_exit_ips.csv`. Satellite offices may route through unexpected countries legitimately; annotate lookups with effective dates.

## SPL

```spl
index=netflow earliest=-4h NOT (cidrmatch("10.0.0.0/8", dest) OR cidrmatch("192.168.0.0/16", dest) OR cidrmatch("172.16.0.0/12", dest))
| iplocation prefix=geo_ dest
| lookup expected_peer_countries.csv country AS geo_Country OUTPUT allowed
| where isnull(allowed)
| stats sum(bytes) as bytes dc(src) as internal_hosts dc(dest) as external_ips values(geo_Country) as countries values(geo_City) as cities
  by dest
| eval mb=round(bytes/1048576,2)
| sort -bytes
| head 50
```

## Visualization

Map visualization of weighted points; table of country, bytes, internal_hosts; pie chart of bytes by continent.

## Known False Positives

Content delivery networks rotate countries for the same hostname. Browser privacy relays appear as unfamiliar regions. Mis-geolocated mobile carrier ranges trigger benign spikes.

## References

- [Splunk Documentation — iplocation command](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Iplocation)
- [MaxMind GeoIP documentation](https://dev.maxmind.com/geoip/docs/databases)
