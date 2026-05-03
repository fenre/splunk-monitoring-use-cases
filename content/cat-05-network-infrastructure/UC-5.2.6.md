<!-- AUTO-GENERATED from UC-5.2.6.json — DO NOT EDIT -->

---
id: "5.2.6"
title: "Geo-IP Anomaly Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.6 · Geo-IP Anomaly Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly

*We help you notice odd geography on outbound traffic so mistakes, theft, and misrouted data are easier to spot.*

---

## Description

Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.

## Value

Security teams detect firewall-allowed traffic to/from geographically blocked or high-risk countries, identifying policy violations and potential data exfiltration paths.

## Implementation

Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.

## Detailed Implementation

### Prerequisites
* Firewall traffic logs with geographic IP information. Key fields: `src_ip`, `dest_ip`, `src_country`/`dest_country` (from GeoIP lookup), `action`, `bytes`. Most TAs include built-in GeoIP lookups, or use Splunk's `iplocation` command.
* Create `geo_policy.csv` lookup: `country_code`, `country_name`, `policy` (allowed/blocked/monitored), `risk_level`.

### Step 1 — - Configure data collection
Verify GeoIP enrichment:
```spl
index=firewall (action=allowed OR action=allow) earliest=-4h
| eval src=coalesce(src_ip, src)
| eval dst=coalesce(dest_ip, dest)
| iplocation src prefix=src_
| iplocation dst prefix=dest_
| stats count by src_Country, dest_Country
| sort -count | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- Geographic anomaly detection:**
```spl
index=firewall (action=allowed OR action=allow OR action=pass) earliest=-4h
| eval src=coalesce(src_ip, src, srcaddr)
| eval dst=coalesce(dest_ip, dest, dstaddr)
| iplocation src prefix=src_
| iplocation dst prefix=dest_
| where isnotnull(src_Country) OR isnotnull(dest_Country)
| lookup geo_policy.csv country_code AS src_Country OUTPUT policy AS src_policy, risk_level AS src_risk
| lookup geo_policy.csv country_code AS dest_Country OUTPUT policy AS dest_policy, risk_level AS dest_risk
| eval anomaly=case(src_policy="blocked", "BLOCKED_COUNTRY_SOURCE -- traffic from ".src_Country, dest_policy="blocked", "BLOCKED_COUNTRY_DEST -- traffic to ".dest_Country, src_risk="high" OR dest_risk="high", "HIGH_RISK_GEO -- ".coalesce(src_Country, "?")." -> ".coalesce(dest_Country, "?"), 1==1, null())
| where isnotnull(anomaly)
| stats count as connections dc(src) as unique_sources dc(dst) as unique_targets sum(bytes_out) as total_bytes by anomaly, src_Country, dest_Country
| eval severity=case(match(anomaly, "BLOCKED_COUNTRY"), "CRITICAL -- traffic to/from blocked country", match(anomaly, "HIGH_RISK"), "WARNING -- high-risk geography", 1==1, "INFO")
| sort severity, -connections
```

### Step 3 — - Validate
(a) Verify GeoIP database is current: `| iplocation "8.8.8.8" | table Country, City` should return "United States".
(b) Cross-reference with threat intelligence feeds for high-risk country lists.
(c) Confirm firewall geo-blocking rules match the `geo_policy.csv` lookup.

### Step 4 — - Operationalize
Dashboard ("Firewall -- Geo-IP Analysis"):
* Row 1 -- Single-value: "Blocked country connections", "High-risk geo connections", "Unique source countries".
* Row 2 -- Geographic anomaly table.
* Row 3 -- Geo map visualization of traffic flows.

Alerting:
* Critical (traffic from/to blocked country): policy violation.
* Warning (high-risk geography with high volume): investigate data exfiltration risk.

### Step 5 — - Troubleshooting

* **Legitimate traffic from blocked country** -- CDN or cloud provider may have IPs registered in unexpected countries. Check: (1) reverse DNS for the IP, (2) ASN ownership, (3) consider whitelisting specific IP ranges for known cloud providers.

* **GeoIP lookup returning null** -- IP may be private (RFC1918), reserved, or not in the GeoIP database. Filter private IPs before the `iplocation` command.

* **False positives from VPN exit nodes** -- Users on commercial VPNs may exit in unexpected countries. Correlate with VPN session logs to identify legitimate users.

## SPL

```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src, Country | sort -data_sent
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

Choropleth map, Table, Bar chart by country.

## Known False Positives

Cloud egress, anycast, or carrier address pools can look "wrong" for geography until you enrich with your own allowlists.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
