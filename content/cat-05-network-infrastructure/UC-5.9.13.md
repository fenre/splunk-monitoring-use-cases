<!-- AUTO-GENERATED from UC-5.9.13.json — DO NOT EDIT -->

---
id: "5.9.13"
title: "DNS Availability Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.13 · DNS Availability Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check whether our domain names can still be found on the internet — because if people can't look up our address, they can't reach us at all, even if everything else is working perfectly.*

---

## Description

Flags DNS Server tests where resolution availability dropped below 100% — meaning at least one query from an agent to a specific DNS server for a specific domain name failed. DNS is the first step in every network connection; if DNS fails, users see "site not found" errors even when the actual service is running perfectly.

## Value

DNS is the single most critical dependency for internet-facing services — every HTTPS connection, API call, email delivery, and CDN fetch starts with a DNS lookup. A DNS outage that takes 5 minutes to detect and 10 minutes to mitigate costs orders of magnitude more than a web server restart, because the blast radius is everything: web, API, email, CDN, VPN. Monitoring DNS availability from multiple ThousandEyes agents lets the NOC detect failures from the user's perspective (not just the DNS server's health metrics), distinguish between "the server is down" and "the server is up but not answering queries for this domain" (zone loading failure, corrupted zone file, expired DNSSEC keys), and pinpoint which DNS server or domain is affected before the cascade reaches application monitoring.

## Implementation

Create DNS Server tests in ThousandEyes: **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNS Server**. Enter the domain name to query (e.g., `www.example.com`) and the DNS server address (e.g., `8.8.8.8` or your internal resolver IP). Create separate tests for each critical domain × DNS server combination. The Tests Stream — Metrics input delivers DNS metrics alongside network metrics in the same OTel stream.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **DNS Server tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNS Server**. Key settings:
  - **Domain:** The domain name to query (e.g., `www.example.com`, `api.example.com`). Monitor every domain that serves production traffic.
  - **DNS Server:** The IP address of the DNS server to query. For external monitoring, use your authoritative DNS server IPs (not resolvers). For internal monitoring, use your corporate recursive resolvers.
  - **Record Type:** A, AAAA, CNAME, MX, etc. Default is A. Match the record type your applications use.
  - **Agents:** Select Cloud Agents for external DNS monitoring ("how do internet users see our DNS?") and Enterprise Agents for internal DNS monitoring ("how do our employees see our internal DNS?").
  - **Interval:** 1 minute for critical domains, 5 minutes for less critical ones.
- **ThousandEyes account tier:** DNS Server tests are available on all tiers (Essentials, Advantage, Premier).
- **DNS server addresses:** Document which DNS servers serve each domain. For authoritative DNS, query your NS records: `dig NS example.com`. For corporate resolvers, get the IPs from your DHCP/DNS team.

### Step 1 — Configure data collection
DNS test metrics flow through the same Tests Stream — Metrics OTel input as network and BGP metrics. If the stream is already enabled and not filtered by test type, DNS data is included automatically.

Verify DNS data:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="dns-server" earliest=-30m
| stats count by dns.question.name, server.address
```
You should see one row per domain-server combination with active DNS Server tests.

**DNS test types in ThousandEyes — understanding the differences:**
- `dns-server` (this UC) — queries a SPECIFIC DNS server. Tests that server's ability to resolve the domain. Use for monitoring YOUR DNS infrastructure.
- `dns-trace` (UC-5.9.17) — follows the FULL delegation chain from root servers. Tests the entire DNS hierarchy. Use for detecting delegation issues.
- `dns-dnssec` (UC-5.9.15) — validates the DNSSEC chain of trust. Tests cryptographic integrity. Use for DNSSEC-signed domains.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.availability) as avg_availability min(dns.lookup.availability) as min_availability by dns.question.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```

**Understanding this SPL**

`thousandeyes.test.type="dns-server"` — filters to DNS Server tests. Other DNS test types (`dns-trace`, `dns-dnssec`) use different test type values.

`dns.question.name` — the domain being queried. This is the primary dimension for DNS monitoring.

`server.address` — the DNS server being queried. Splitting by this lets you distinguish "server A is down" from "server B is down" when you have multiple DNS servers for the same domain.

`avg(dns.lookup.availability)` — average availability over the search window. 100% means every query succeeded. 50% means half the queries failed. 0% means every query failed.

`min(dns.lookup.availability)` — the worst single reading. Useful for distinguishing sustained outages (min and avg both 0%) from brief blips (min = 0% but avg = 95%).

`where avg_availability < 100` — ANY DNS failure is significant. Unlike network latency where you might accept minor variations, DNS availability should be 100%. Even a single failed query means a user saw a "site not found" error. For extremely high-traffic domains, you may need to relax to `< 99` to avoid alerting on isolated agent-side issues.

**Aggregate view variant** (overall availability per domain across all servers and agents):
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.availability) as global_availability dc(server.address) as servers_tested dc(thousandeyes.source.agent.name) as agents by dns.question.name
| where global_availability < 100
| sort global_availability
```

**Scheduling:** cron `*/5 * * * *`, time range `-15m to now`. DNS failures are critical — use a 5-minute schedule, not 15-minute. Throttle by `dns.question.name` + `server.address` for 1 hour.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → DNS Server** and select the same domain and time window. The UI shows availability and resolution time per agent.

(b) **Manual DNS query.** From a machine with network access: `dig @<server.address> <dns.question.name>`. If it returns `NOERROR` with answer records, availability should be 100%. If it returns `SERVFAIL` or times out, availability should be 0%. Compare with what Splunk shows.

(c) **Expected record validation.** ThousandEyes DNS Server tests can validate that the DNS response contains expected records (e.g., a specific IP or CNAME). If the validation fails, availability drops to 0% even though the server responded. Check the test configuration for expected response validation.

(d) **Multi-server comparison.** For a domain served by multiple DNS servers, all servers should show similar availability. If one server consistently shows lower availability, it has a problem independent of the others.

### Step 4 — Operationalize
**Dashboard** ("DNS Health" — designed for NOC and DNS team):
- Row 1 — Single value tiles: per critical domain showing availability %. Red if < 100%. This is the "everything works" indicator.
- Row 2 — Timechart: availability per domain over 24 hours at 5-minute granularity. Drops are immediately visible.
- Row 3 — Table: domain | server | agent | availability % | min availability | avg resolution time (ms) — sorted worst-first.
- Row 4 — Combined with UC-5.9.14 resolution time for a complete DNS quality view.

**Alerting:**
- Availability < 100% for ANY critical domain → immediate page (PagerDuty high-urgency). DNS outages have the widest blast radius of any infrastructure failure.
- Include: domain name, DNS server, affected agents, and ThousandEyes permalink.

**Runbook** (owner: DNS team / NOC):
1. **Triage.** Which domain? Which DNS server? Which agents are affected?
2. **All agents, one server:** The DNS server is down or not serving that zone. Check server health (BIND status, Windows DNS event logs, cloud DNS provider dashboard).
3. **All agents, all servers for one domain:** The zone itself is broken (expired SOA, corrupted zone file, failed zone transfer). Check zone status on all authoritative servers.
4. **One agent, one server:** Network path issue between that agent and that server. Check UC-5.9.1/2 for that agent-server path.
5. **All agents, all servers, all domains:** Catastrophic DNS infrastructure failure or a network-wide issue preventing UDP 53 traffic. Escalate immediately.
6. **Check DNSSEC:** If the domain is DNSSEC-signed, a validation failure looks like an availability failure from validating resolvers. Check UC-5.9.15.

### Step 5 — Troubleshooting

- **No DNS test data at all** — DNS Server tests may not be configured in ThousandEyes, or the test type may be filtered out of the OTel stream. Check ThousandEyes test settings.

- **Availability always 0% even though DNS works** — The test may have an expected response validation that's failing (e.g., expecting a specific IP that has changed). Check the test configuration in ThousandEyes for "Expected IP" or "Verify Response" settings.

- **`dns.lookup.availability` field missing** — In v1 OTel, the field may be `dns.metrics.availability`. Check `| fieldsummary | search field=dns*` to find the correct field name.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, and role permissions.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.availability) as avg_availability min(dns.lookup.availability) as min_availability by dns.question.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```

## Visualization

(1) Single value tile: DNS availability % across all tests (red if < 100%). (2) Table: domain, DNS server, agent, availability %, min availability — sorted worst-first, colour-coded: green 100%, red < 100%. (3) Timechart: `| timechart span=5m avg(dns.lookup.availability) by dns.question.name` showing availability over time per domain. (4) Combined panel: DNS availability alongside DNS resolution time (UC-5.9.14) to distinguish between outages (availability drop) and slowdowns (duration increase). (5) The ThousandEyes Splunk app includes a built-in "DNS Availability (%)" line chart with drilldown to ThousandEyes.

## Known False Positives

**DNS server rolling restart/maintenance.** When a DNS server reboots (e.g., BIND reload, Infoblox Grid maintenance), queries during the restart window fail. If the test interval is 1 minute and the restart takes 30 seconds, you'll see 1–2 rounds of 0% availability followed by full recovery. Distinguish by checking whether the failure is brief (< 5 minutes) and affects only one server address while other servers for the same domain remain at 100%. Suppress planned restarts with a `dns_maintenance_windows` lookup.

**Transient network issues between agent and DNS server.** If the network path between a specific agent and the DNS server experiences packet loss, the DNS query may time out even though the DNS server is healthy. Distinguish by checking whether other agents querying the same DNS server show 100% availability. If only one agent shows failures, the problem is the network path, not the DNS server — correlate with UC-5.9.1/2 for that agent.

**Anycast DNS server pool rotation.** DNS providers using anycast (Cloudflare 1.1.1.1, Google 8.8.8.8) route queries to different physical servers. If one anycast PoP is down, some agents may experience failures while others don't. This is a real DNS availability issue from the user's perspective (users near that PoP are affected), but it may resolve quickly as BGP routes withdraw the failing PoP.

**Negative caching / NXDOMAIN for intentional test domains.** If the ThousandEyes test queries a domain that legitimately doesn't exist (misconfiguration in test setup), availability will always read 0%. Verify the `dns.question.name` is a real, resolvable domain.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes DNS Server Test Configuration](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/dns-tests/)
- [ThousandEyes OTel v2 Data Model — DNS metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
