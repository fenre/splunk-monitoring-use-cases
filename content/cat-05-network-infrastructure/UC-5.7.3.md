<!-- AUTO-GENERATED from UC-5.7.3.json — DO NOT EDIT -->

---
id: "5.7.3"
title: "Bandwidth by Application"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.3 · Bandwidth by Application

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We help you see which apps are eating the most bandwidth so you can pick what to protect with quality-of-service and what to upgrade on the link.*

---

## Description

Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.

## Value

Network operations and capacity planners understand bandwidth consumption by application, detect unauthorized applications, and identify application mix shifts that require infrastructure adjustments.

## Implementation

Enable NBAR (Network-Based Application Recognition) on Cisco routers to export application-tagged NetFlow. Ingest in Splunk.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with port-level fields: `dest_port` (destination port number), `protocol` (TCP=6, UDP=17, ICMP=1), `bytes`, `packets`. The destination port is the primary indicator for application identification in flow data.
- Build an application mapping lookup `port_to_app.csv` mapping common ports to application names: 80/443=HTTP/HTTPS, 22=SSH, 3389=RDP, 53=DNS, 3306=MySQL, 5432=PostgreSQL, 1433=MSSQL, 8080=HTTP-alt, 8443=HTTPS-alt, etc. Include your organization's custom application ports.
- For deeper application identification, consider NBAR (Network-Based Application Recognition) data from Cisco devices, which classifies traffic by application rather than just port. NBAR data can be exported via NetFlow Flexible Records (application_id field).
- CIM: the Network_Traffic data model includes `All_Traffic.dest_port` and `All_Traffic.app` for application-level analysis.

### Step 1 — Configure data collection
Verify port-level data extraction:
```spl
index=netflow earliest=-15m
| stats count dc(dest_port) as unique_ports sum(bytes) as total_bytes
```
You should see hundreds to thousands of unique ports. If `dest_port` is null, the NetFlow template may not include port fields — check the exporter's flow record template configuration.

Upload the `port_to_app.csv` lookup with your application mapping.

### Step 2 — Create the search and alert

**Primary search — Bandwidth by application (hourly report):**
```spl
index=netflow earliest=-1h
| lookup port_to_app.csv dest_port OUTPUT app_name app_category
| eval application=if(isnotnull(app_name), app_name, "Port-".dest_port)
| stats sum(bytes) as total_bytes sum(packets) as total_pkts dc(src) as unique_sources by application, app_category
| eval total_GB=round(total_bytes/1073741824, 2)
| sort -total_bytes
| head 30
```

#### Understanding this SPL: We map destination ports to application names using the lookup, then aggregate bandwidth per application. `dc(src)` shows how many hosts use each application — an application used by 1 host vs. 1000 hosts has very different capacity implications. The `app_category` grouping (Web, Database, File Transfer, Remote Access, etc.) provides executive-level summaries.

**Application mix trending — shift detection over 7 days:**
```spl
index=netflow earliest=-7d
| lookup port_to_app.csv dest_port OUTPUT app_name app_category
| eval application=coalesce(app_name, "Other")
| bin _time span=1h
| stats sum(bytes) as bytes by _time, app_category
| timechart span=1h sum(bytes) by app_category
```

#### Understanding this SPL: Shows how the application mix changes over time. A sudden increase in "Remote Access" (SSH, RDP) could indicate a VPN outage driving users to direct connections. A steady increase in "Web" traffic may require WAN or proxy capacity expansion.

**Unauthorized application detection — unexpected ports with significant traffic:**
```spl
index=netflow earliest=-1h
| lookup port_to_app.csv dest_port OUTPUT app_name app_category risk_level
| where isnull(app_name) AND dest_port > 1024
| stats sum(bytes) as bytes dc(src) as sources dc(dest) as destinations by dest_port, protocol
| eval bytes_MB=round(bytes/1048576, 1)
| where bytes_MB > 50 OR sources > 10
| sort -bytes_MB
```

#### Understanding this SPL: Finds high-volume traffic on unrecognized ports. Known applications are in the lookup; unrecognized ports with significant traffic could be: unauthorized P2P (BitTorrent), tunneling (VPN bypass), C2 communication, or legitimate applications not yet in the lookup. The `sources > 10` condition catches ports used by multiple hosts (likely a shared service).

Schedule as Alert: unauthorized application search runs hourly. Trigger on any unrecognized port with > 1 GB or > 50 sources.

### Step 3 — Validate
(a) Compare the application bandwidth breakdown to your firewall or proxy's application report for the same hour. The proportions should be similar even if absolute numbers differ (due to NetFlow sampling).
(b) Verify the port-to-app mapping: check that the top 10 applications by volume are correctly named.
(c) Test unauthorized application detection: generate traffic on an unusual port (e.g. TCP/9999) and verify it appears in the results.

### Step 4 — Operationalize
Dashboard ("Network — Application Bandwidth"):
- Row 1 — Pie chart: bandwidth distribution by app_category.
- Row 2 — Timechart: application bandwidth over 7 days (stacked area by category).
- Row 3 — Top 30 applications table: application, category, total_GB, unique_sources, total_pkts.
- Row 4 — Unauthorized applications table: port, protocol, bytes, sources, destinations.

Alerting:
- Capacity (any single application > 50% of total bandwidth): notify capacity planning.
- Security (unrecognized port with > 1 GB in 1 hour): alert security for investigation.

Runbook:
1. **Unexpected application dominating bandwidth**: Identify the top sources using that application. If it's a backup job or software distribution, schedule it for off-peak hours. If unauthorized, block at the firewall.
2. **New high-volume port detected**: Investigate the port using online databases (IANA port registry, SpeedGuide). If it's a known application, add it to the lookup. If unknown, investigate the source hosts for potential compromise.

### Step 5 — Troubleshooting

- **Most traffic shows as "Other" / "Unknown"** — The port-to-app lookup is incomplete. Add entries for your top unrecognized ports. For deeper analysis, use NBAR data from Cisco devices or DPI from Splunk Stream.

- **Port 443 dominates everything** — Modern web applications (SaaS, cloud, APIs) all use HTTPS. Port-based analysis cannot distinguish between them. For HTTPS traffic breakdown, use TLS SNI (Server Name Indication) data from Splunk Stream or firewall SSL inspection logs.

- **NetFlow shows different application mix than the firewall** — The firewall may use DPI (Deep Packet Inspection) for application identification, while NetFlow relies on ports. DPI is more accurate for modern encrypted applications.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=netflow
| stats sum(bytes) as total_bytes by application
| sort -total_bytes | head 20 | eval GB=round(total_bytes/1073741824,2)
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.app span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
| head 20
```

## Visualization

Pie chart (bandwidth by app), Bar chart, Table.

## Known False Positives

Traffic spikes during backup jobs, large file transfers, or video streaming events can make one app dominate without a fault; NBAR and exporter labels can also shift after firmware or app updates.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
