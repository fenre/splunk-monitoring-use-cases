<!-- AUTO-GENERATED from UC-5.20.69.json — DO NOT EDIT -->

---
id: "5.20.69"
title: "IPv6 Geographic Flow Analysis and Unexpected Country Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.69 · IPv6 Geographic Flow Analysis and Unexpected Country Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We have a list of countries we don't accept visitors from. We check every visitor's passport (IP address) to see where they're from. But with the new system (IPv6), some visitors don't have their passport checked — they come through a different entrance that doesn't have the country list posted. We watch for visitors from blocked countries sneaking in through the IPv6 entrance.*

---

## Description

Analyses IPv6 flow data for geographic anomalies — traffic from or to countries that should be blocked by policy, or traffic from unexpected geographic origins. IPv6 geo-blocking is frequently overlooked when IPv4 geo-blocking is in place, creating a bypass path for attackers from sanctioned or high-risk countries who route traffic over IPv6 to avoid the IPv4-only geo-block.

## Value

Organisations that implement geographic access restrictions for IPv4 often fail to apply the same restrictions to IPv6. An attacker from a blocked country who routes traffic over IPv6 bypasses the geo-block entirely. This analysis detects IPv6 traffic from countries that should be blocked, identifies the geo-blocking parity gap, and monitors for geographic shifts in IPv6 traffic patterns that may indicate compromised infrastructure or proxy usage.

## Implementation

Apply iplocation to IPv6 source addresses from flow data. Compare against geographic access policy. Alert on traffic from blocked countries. Track geographic distribution changes over time.

## Detailed Implementation

### Prerequisites
- IPv6 flow data in Splunk with source and destination addresses.
- Splunk's iplocation command with a geo-IP database that supports IPv6 (MaxMind GeoLite2 or GeoIP2).
- Geographic access policy defining allowed and blocked countries.

### Step 1 — Configure data collection

**Geo-IP database update:**
Splunk uses MaxMind GeoLite2 for iplocation. Ensure the database supports IPv6:
```
# Verify IPv6 geo-IP resolution works
| makeresults
| eval ip="2001:4860:4860::8888"
| iplocation ip
| table ip, Country, City, Region
```
Expected: Google's IPv6 DNS resolver geolocates to US.

**Create geographic access policy lookup:**
```csv
country,allowed,risk_level
United States,yes,low
United Kingdom,yes,low
Germany,yes,low
Norway,yes,low
Russia,no,high
China,no,high
North Korea,no,critical
Iran,no,critical
```
Upload as `geo_policy.csv`.

**Verification:**
```spl
index=network (sourcetype="netflow" OR sourcetype="pan:traffic") earliest=-1h
| eval src_ip=coalesce(sourceIPv6Address, src)
| where match(src_ip, ":")
| iplocation src_ip
| stats count by Country
| head 20
```

### Step 2 — Create the search and alert

**Blocked country IPv6 traffic alert:**
```spl
index=network (sourcetype="netflow" OR sourcetype="pan:traffic") earliest=-1h
| eval src_ip=coalesce(sourceIPv6Address, src)
| where match(src_ip, ":")
| iplocation src_ip
| rename Country as src_country
| lookup geo_policy.csv country as src_country OUTPUT allowed, risk_level
| where allowed="no"
| stats count as flows dc(src_ip) as sources first(risk_level) as risk by src_country
| eval alert=src_country . " (" . risk . " risk): " . sources . " IPv6 sources, " . flows . " flows"
| sort -flows
```

**IPv4 vs IPv6 geo-policy parity check:**
```spl
index=network (sourcetype="pan:traffic") action="allowed" earliest=-24h
| eval ip_ver=if(match(src, ":"), "IPv6", "IPv4")
| iplocation src
| rename Country as src_country
| lookup geo_policy.csv country as src_country OUTPUT allowed
| where allowed="no"
| stats count as permitted_from_blocked by ip_ver, src_country
| eval parity_issue="Traffic from blocked country " . src_country . " PERMITTED via " . ip_ver . " (" . permitted_from_blocked . " flows)"
```
If blocked-country traffic is permitted via IPv6 but not IPv4, the geo-blocking policy has a parity gap.

**Geographic shift detection:**
```spl
index=network (sourcetype="netflow" OR sourcetype="pan:traffic") earliest=-7d
| eval src_ip=coalesce(sourceIPv6Address, src)
| where match(src_ip, ":")
| iplocation src_ip
| rename Country as src_country
| bin _time span=1d
| stats count as daily_flows by src_country, _time
| eventstats avg(daily_flows) as avg_flows stdev(daily_flows) as stdev_flows by src_country
| where daily_flows > avg_flows + 3 * stdev_flows AND daily_flows > 100
| eval shift_alert=src_country . ": " . daily_flows . " flows vs avg " . round(avg_flows, 0) . " — geographic anomaly"
```

### Step 3 — Validate
(a) **Blocked country test.** Verify that known IPv6 addresses from blocked countries (use a geo-IP lookup tool) trigger the alert.

(b) **Parity check.** If IPv4 geo-blocking is in place, verify the parity check identifies the IPv6 gap.

(c) **Geo-IP accuracy.** Test iplocation with known IPv6 addresses (Google, Cloudflare, major ISPs) to verify accuracy.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Geographic Analysis"):
- Row 1 — Choropleth map: IPv6 traffic sources by country.
- Row 2 — Table: blocked-country IPv6 traffic (should be empty if policies are correctly applied).
- Row 3 — Parity comparison: IPv4 vs IPv6 geo-policy compliance.
- Row 4 — Timechart: top-5 IPv6 source countries over 30 days.

**Scheduling:** Blocked country alert every 15 minutes. Parity check daily. Geographic shift weekly.

**Runbook:**
1. Blocked-country IPv6 traffic permitted: URGENT — apply equivalent geo-blocking to IPv6 firewall rules.
2. Geographic shift: investigate the country. Could be legitimate (new partner, cloud migration) or suspicious (compromised infrastructure, proxy).
3. Persistent geo-IP inaccuracy: submit corrections to MaxMind; consider alternative geo-IP sources for IPv6.

### Step 5 — Troubleshooting

- **iplocation limitations** — Splunk's iplocation command relies on MaxMind GeoLite2. IPv6 coverage is approximately 85-90% accurate at the country level. For higher accuracy, consider GeoIP2 commercial databases.

- **Private/ULA addresses** — ULA (fc00::/7) and link-local (fe80::/10) addresses will not resolve to a geographic location. Filter these before analysis.

- **Anycast addresses** — IPv6 anycast services (DNS, CDN) geolocate to the anycast PoP, not the end user. Consider this when interpreting geographic data for well-known anycast prefixes.

## SPL

```spl
index=network (sourcetype="netflow" OR sourcetype="pan:traffic") earliest=-24h
| eval src_ip=coalesce(sourceIPv6Address, src)
| eval dest_ip=coalesce(destinationIPv6Address, dest)
| where match(src_ip, ":")
| iplocation src_ip
| rename Country as src_country, lat as src_lat, lon as src_lon
| stats count as flows sum(bytes) as total_bytes dc(src_ip) as unique_sources by src_country
| lookup geo_policy.csv country as src_country OUTPUT allowed
| where allowed="no" OR isnull(allowed)
| eval alert=src_country . ": " . unique_sources . " unique IPv6 sources, " . flows . " flows, " . round(total_bytes/1048576, 1) . " MB — BLOCKED COUNTRY via IPv6"
| sort -flows
```

## Visualization

(1) Geo-map: IPv6 traffic sources by country (choropleth). (2) Table: blocked-country IPv6 traffic sorted by volume. (3) Comparison: IPv4 vs IPv6 geographic distribution. (4) Timechart: IPv6 traffic from top-5 countries over 30 days.

## Known False Positives

**Geo-IP inaccuracy for IPv6.** IPv6 geolocation databases are less accurate than IPv4, especially for mobile networks and tunnel providers. Some IPv6 addresses may geolocate incorrectly.

**CDN and cloud provider addresses.** Major cloud providers (AWS, Azure, GCP) and CDNs (Cloudflare, Akamai) have IPv6 allocations that may geolocate to their infrastructure rather than the end user.

**IPv6 tunnel providers.** Addresses from tunnel brokers like Hurricane Electric may geolocate to the PoP location rather than the user's physical location.

**Legitimate VPN exit nodes.** VPN users may appear to originate from unexpected countries.

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.4 — filtering considerations)](https://www.rfc-editor.org/rfc/rfc9099)
