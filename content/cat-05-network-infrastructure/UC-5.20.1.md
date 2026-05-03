<!-- AUTO-GENERATED from UC-5.20.1.json — DO NOT EDIT -->

---
id: "5.20.1"
title: "IPv6 vs IPv4 Traffic Ratio Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.20.1 · IPv6 vs IPv4 Traffic Ratio Trending

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity, Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch how much of your network traffic uses the new internet addressing system (IPv6) compared to the old one (IPv4), so you can see whether your upgrade is making progress and catch any sudden setbacks before they become problems.*

---

## Description

Measures the ratio of IPv6 to IPv4 traffic across the network using flow data (NetFlow v9, IPFIX, or firewall logs), trended over time. This is the foundational adoption metric — without it, you cannot answer 'how much of our traffic is IPv6?' or track whether a dual-stack rollout is progressing. The search classifies flows by IP version using the presence of a colon in the source or destination address, then computes hourly percentages by both flow count and byte volume.

## Value

IPv6 adoption is a board-level metric for organisations subject to OMB M-21-07 (US federal: 80% IPv6-only by FY2025), and a planning input for every enterprise running dual-stack. Without a traffic ratio baseline, you cannot measure rollout progress, detect regression (e.g., a firewall change that blocks IPv6 and forces fallback), or identify subnets where IPv6 was deployed but nobody is using it. The byte-weighted ratio also reveals whether IPv6 is carrying real application traffic or just NDP and link-local noise — an IPv6 flow percentage of 15% but byte percentage of 2% means your biggest applications are still IPv4-only.

## Implementation

Deploy NetFlow v9 or IPFIX on routers and switches — NetFlow v5 cannot export IPv6 flows and will produce a false 0% reading. Point exporters at the Splunk NetFlow collector (Heavy Forwarder with the NetFlow TA). Alternatively, use firewall traffic logs from Palo Alto or Cisco ASA, which log both IPv4 and IPv6 sessions natively. Schedule the search as a report (daily, over the last 7 days, sliding window) and save to a summary index for long-term trending.

## Detailed Implementation

### Prerequisites
- NetFlow v9 or IPFIX must be configured on routers/switches exporting flows. NetFlow v5 is IPv4-only — it structurally cannot carry IPv6 flow records. If your infrastructure only supports v5, the first action item is upgrading exporters. On Cisco IOS-XE: `flow record v9-ipv6` with `match ipv6 source address` and `match ipv6 destination address`. On Juniper Junos: `services flow-monitoring version-ipfix template ipv6-template`.
- Splunk Add-on for NetFlow (`splunk-add-on-for-netflow`, Splunkbase 1658) installed on the Heavy Forwarder that receives flow data (UDP typically on port 2055 or 9996). Install the same TA on Search Heads for field extractions.
- Alternative data source: Palo Alto NGFW traffic logs (`sourcetype=pan:traffic`) or Cisco ASA syslog (`sourcetype=cisco:asa`) both log the IP version natively. If using PAN logs, the field `ip_version` is already populated.
- Index: `netflow` (flow data) or `firewall` (firewall logs). Ensure the index is created and the data is arriving.
- Role permissions: `srchIndexesAllowed` must include the relevant index.
- License headroom: NetFlow/IPFIX volume varies enormously by flow export rate and network size. A 500-router campus at 1:100 sampling rate typically generates 2–10 GB/day of flow data. Plan accordingly.

### Step 1 — Configure data collection

Option A — NetFlow v9/IPFIX (preferred for comprehensive measurement):

On Cisco IOS-XE router:
```
flow record NETFLOW-V9-IPV6
 match ipv6 source address
 match ipv6 destination address
 match transport source-port
 match transport destination-port
 match interface input
 collect counter bytes long
 collect counter packets long
 collect timestamp sys-uptime first
 collect timestamp sys-uptime last

flow exporter SPLUNK-EXPORTER
 destination <splunk-hf-ip>
 transport udp 9996
 export-protocol netflow-v9
 template data timeout 300

flow monitor IPV6-MONITOR
 record NETFLOW-V9-IPV6
 exporter SPLUNK-EXPORTER

interface GigabitEthernet0/0/0
 ipv6 flow monitor IPV6-MONITOR input
 ipv6 flow monitor IPV6-MONITOR output
```

On the Splunk Heavy Forwarder, inputs.conf:
```
[udp://9996]
connection_host = ip
sourcetype = netflow
index = netflow
```

Option B — Palo Alto firewall traffic logs (alternative):
Traffic logs already contain both IPv4 and IPv6 sessions. No special configuration needed beyond ensuring the TA is installed and traffic logging is enabled. The `src` and `dst` fields contain the IP addresses.

Verification (wait 15 minutes for flow data to arrive):
```spl
index=netflow sourcetype=netflow earliest=-30m
| eval has_ipv6=if(match(src_ip, ":") OR match(dest_ip, ":"), 1, 0)
| stats count as total_flows sum(has_ipv6) as ipv6_flows
| eval ipv6_pct=round(ipv6_flows/total_flows*100, 2)
```

Expected result: `ipv6_pct` should be non-zero if any IPv6 traffic exists on the network. If zero, verify exporters support v9/IPFIX (`show flow monitor` on Cisco, `show services flow-monitoring` on Juniper) and that the IPv6 flow record includes source/destination address matches.

### Step 2 — Create the search and alert

**Primary search — IPv6 vs IPv4 traffic ratio trending:**
```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix
| eval ip_version=case(
    match(src_ip, ":"), "IPv6",
    match(dest_ip, ":"), "IPv6",
    isnotnull(sourceIPv6Address), "IPv6",
    1==1, "IPv4")
| timechart span=1h count as flows sum(bytes) as total_bytes by ip_version
| eval ipv6_pct_flows=round(('IPv6' / ('IPv4' + 'IPv6')) * 100, 2)
| eval ipv6_pct_bytes=round(('IPv6' / ('IPv4' + 'IPv6')) * 100, 2)
```

**Understanding this SPL:**
- `match(src_ip, ":")` — IPv6 addresses always contain colons; IPv4 never does. This is the simplest and most reliable classifier across all sourcetypes.
- `isnotnull(sourceIPv6Address)` — fallback for IPFIX exports where the TA extracts separate IPv4/IPv6 address fields from IPFIX Information Elements 27/28.
- `timechart span=1h` — hourly granularity balances visibility and performance. For capacity planning, use `span=1d`. For incident investigation, `span=5m`.
- Dual metrics (flows vs bytes): flow count shows session frequency; byte volume shows actual bandwidth. An IPv6 flow percentage of 30% but byte percentage of 5% means IPv6 is only used for small transactions (DNS, NDP) while bulk data (file transfers, backups, video) remains IPv4.

**Variant — exclude NDP/link-local noise for application-only ratio:**
```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix
| where NOT match(src_ip, "^fe80:") AND NOT match(dest_ip, "^ff02:")
| eval ip_version=if(match(src_ip, ":") OR match(dest_ip, ":"), "IPv6", "IPv4")
| timechart span=1h count by ip_version
```

**Alert — IPv6 adoption regression:**
Schedule daily at 06:00, time range `-7d to now`:
```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix earliest=-7d
| eval ip_version=if(match(src_ip, ":") OR match(dest_ip, ":"), "IPv6", "IPv4")
| bin _time span=1d
| stats count by _time, ip_version
| chart sum(count) over _time by ip_version
| eval ipv6_pct=round(IPv6/(IPv4+IPv6)*100, 2)
| sort _time
| streamstats window=2 current=f last(ipv6_pct) as prev_pct
| eval drop_pct=prev_pct - ipv6_pct
| where drop_pct > 5
```
Trigger: any day where IPv6 percentage drops > 5 percentage points from the prior day. This catches firewall misconfigurations, routing changes, or DNS failures that silently disable IPv6.

### Step 3 — Validate
(a) **Compare to router CLI:** On a core router, run `show ipv6 traffic` (Cisco) or `show ipv6 statistics` (Juniper). Compare the IPv6 packet count ratio to Splunk's flow-based ratio. They won't be identical (router counts all packets; Splunk counts sampled flows) but the percentage should be within 5 points.

(b) **Cross-reference with DNS:** Query DNS logs for AAAA vs A query ratios (see UC-5.20.89). If DNS shows 40% AAAA queries but flow data shows 5% IPv6 traffic, many AAAA queries are failing or falling back to IPv4 — investigate Happy Eyeballs behavior (UC-5.20.103).

(c) **Spot-check a known dual-stack service:** Pick a server with a known AAAA record (e.g., your internal web portal). Filter flows to that destination: `index=netflow dest_ip=2001:db8::web:1 | stats count`. If zero flows but the DNS record exists, clients are not using IPv6 to reach it.

(d) **Check for v5-only exporters:** `index=netflow | stats values(sourcetype) dc(src_ip) as flow_sources by exporter_ip | where sourcetype="netflow" AND NOT sourcetype="ipfix"`. Any exporter producing only v5 data needs upgrade.

### Step 4 — Operationalize

**Dashboard** ("IPv6 Adoption — Traffic Ratio"):
- Row 1 — Single-value tiles: "IPv6 Traffic %" (last 24h, trend arrow), "IPv6 Byte %" (last 24h), "Flow Exporters with IPv6" (count of exporters producing IPv6 flows vs total exporters).
- Row 2 — Timechart: dual-axis with IPv6 flow percentage (line, left axis 0–100%) and total flow volume (area, right axis). 30-day view for executive reporting.
- Row 3 — Table: top 10 subnets/sites by IPv6 percentage, drillable to per-device detail.
- Row 4 — Stacked area: IPv4 vs IPv6 byte volumes over 90 days for capacity planning.

**Scheduling:** Run the trending report daily at 02:00 over `-24h`, output to `summary` index for long-term retention. IPv6 adoption data from 12+ months ago is valuable for year-over-year comparisons.

**Audiences:**
- Network engineering: weekly review of per-subnet adoption rates during dual-stack rollout
- CISO/compliance: monthly executive metric for OMB M-21-07 or internal IPv6 strategy
- Capacity planning: quarterly byte-volume analysis to forecast IPv6 infrastructure needs

**Runbook** (owner: Network Architecture):
1. If IPv6 percentage drops > 5 points day-over-day, check: recent firewall rule changes (UC-5.20.53), routing table changes (UC-5.20.49), DNS AAAA record issues (UC-5.20.89).
2. If IPv6 percentage is flat at < 5% despite dual-stack deployment, investigate: Happy Eyeballs fallback (UC-5.20.103), PMTUD failures causing IPv6 TCP hangs (UC-5.20.38), applications hardcoded to IPv4.
3. For compliance reporting: export the daily IPv6 percentage to a CSV lookup for quarterly FISMA reporting or internal IPv6 strategy reviews.

### Step 5 — Troubleshooting

- **IPv6 percentage is 0% despite dual-stack deployment** — Most likely cause: all flow exporters are running NetFlow v5, which cannot carry IPv6 flows. Verify: `index=netflow | head 1000 | stats count by sourcetype`. If only `netflow` (v5) appears and no `ipfix`, upgrade exporters. On Cisco IOS-XE: change from `ip flow-export version 5` to `flow exporter ... export-protocol netflow-v9`. Second cause: the IPv6 flow record is configured but not applied to interfaces — check `show flow interface` on each router.

- **IPv6 percentage is very high (> 90%) in a mixed environment** — Most likely cause: link-local NDP traffic (RA, NS, NA) is being exported and counted. NDP is multicast-based and generates constant background traffic on every VLAN. Filter with `| where NOT match(src_ip, "^fe80:") AND NOT match(dest_ip, "^ff02:")` to exclude it.

- **IPv6 percentage fluctuates wildly between hours** — Could indicate sampling rate differences between IPv4 and IPv6 flow records, or that IPv6 traffic is bursty (e.g., a backup job that runs hourly over IPv6). Check `| timechart span=5m count by ip_version` for patterns. If the IPv6 spikes are periodic, correlate with scheduled jobs.

- **Byte ratio much lower than flow ratio** — IPv6 is carrying small transactions (DNS, NDP, control plane) but not bulk data. This is expected in early dual-stack deployments. The byte ratio is the more meaningful metric for adoption maturity.

- **Different ratios across subnets** — Expected during phased rollout. Use `| stats count by ip_version, subnet` to identify subnets where IPv6 is deployed but unused, or where IPv6 adoption is blocked by a local issue (e.g., a switch with RA Guard misconfiguration blocking SLAAC).

- **No data from specific exporter** — Check `index=netflow | stats latest(_time) as last_seen by exporter_ip | eval age_min=round((now()-last_seen)/60) | where age_min > 30`. Stale exporters may have lost UDP connectivity to the collector (firewall rule, routing change) or the flow monitor may have been removed during a config change.

## SPL

```spl
index=netflow sourcetype=netflow OR sourcetype=ipfix
| eval ip_version=case(
    match(src_ip, ":"), "IPv6",
    match(dest_ip, ":"), "IPv6",
    isnotnull(sourceIPv6Address), "IPv6",
    1==1, "IPv4")
| timechart span=1h count as flows sum(bytes) as total_bytes by ip_version
| eval ipv6_pct_flows=round(('IPv6' / ('IPv4' + 'IPv6')) * 100, 2)
| eval ipv6_pct_bytes=round(('IPv6' / ('IPv4' + 'IPv6')) * 100, 2)
```

## Visualization

(1) Dual-axis timechart: line for IPv6 flow percentage (left axis, 0–100%) overlaid with area chart for total flows (right axis). (2) Single-value tile: current IPv6 traffic percentage (last 24h), with trend arrow showing week-over-week change. Green ≥ target (e.g., 50%), yellow 20–49%, red < 20%. (3) Stacked area chart: IPv4 vs IPv6 byte volumes over 30 days for executive reporting. (4) Table: top 10 subnets by IPv6 flow percentage to identify adoption leaders and laggards.

## Known False Positives

**Link-local NDP inflates IPv6 flow count.** Neighbor Discovery Protocol (NDP) generates IPv6 multicast traffic (ff02::1, ff02::2, ff02::1:ff00::/104) on every VLAN, even where no application uses IPv6. This inflates the IPv6 flow percentage without representing real user traffic. Distinguish by filtering out link-local source addresses (`| where NOT match(src_ip, "^fe80:")`) and well-known multicast destinations. The byte-weighted metric is less affected because NDP packets are small (72–128 bytes each).

**NetFlow v5 exporters produce false 0% IPv6.** NetFlow v5 is structurally incapable of exporting IPv6 flows. If some routers export v5 and others export v9/IPFIX, the blended ratio understates IPv6 adoption. Identify v5-only exporters with `index=netflow | stats values(sourcetype) by exporter_ip` and upgrade them to v9/IPFIX or exclude them from the ratio calculation.

**Firewall NAT64 translation masks IPv6 origin.** If a NAT64 gateway translates IPv6-originated traffic to IPv4 before the flow exporter, the resulting flow appears as IPv4. This understates IPv6 adoption. Measure upstream of the translator, or separately track NAT64 state table volume (see UC-5.20.71).

## References

- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.2 — Traffic monitoring)](https://www.rfc-editor.org/rfc/rfc9099)
- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§5.1 — Transition planning metrics)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [OMB M-21-07 — Completing the Transition to Internet Protocol Version 6 (IPv6)](https://whitehouse.gov/wp-content/uploads/2020/11/M-21-07.pdf)
- [Splunk Add-on for NetFlow (Splunkbase 1658)](https://splunkbase.splunk.com/app/1658)
