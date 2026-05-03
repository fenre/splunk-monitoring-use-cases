<!-- AUTO-GENERATED from UC-5.9.17.json — DO NOT EDIT -->

---
id: "5.9.17"
title: "DNS Trace Delegation Chain Monitoring"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.17 · DNS Trace Delegation Chain Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We follow the full chain of internet address books — from the master list all the way down to the one that has our address — to make sure every link in that chain is correct, because if one link breaks while the old answer is still remembered, nobody notices until it's suddenly too late.*

---

## Description

Monitors the full DNS delegation chain from root to authoritative server for critical domains, detecting delegation failures (broken NS records, lame delegations, missing glue records) that DNS Server tests might not catch because they query a specific resolver that may have cached the correct answer. A DNS Trace test bypasses all caches and walks the chain fresh every round — catching problems that will surface when caches expire.

## Value

DNS delegation issues are the most insidious DNS failures because they're invisible until caches expire. A broken NS record at the TLD level, a lame delegation (NS record points to a server that doesn't serve the zone), or missing glue records won't cause any immediate impact — resolver caches continue serving the domain for hours. But when the TTL expires and resolvers walk the delegation chain again, they hit the broken link and resolution fails for all users simultaneously. DNS Trace tests catch these problems during the cache window, giving the DNS team hours of warning to fix the delegation before the cache-cliff outage hits.

## Implementation

Create DNS Trace tests in ThousandEyes: **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNS Trace**. Enter the domain name to trace. Unlike DNS Server tests, no server address is needed — the test starts at root servers and follows NS delegations. Use Cloud Agents for best global coverage. Schedule at 5–15 minute intervals.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **DNS Trace tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNS Trace**. Enter the domain name. No DNS server address is needed.
- **Understanding DNS Trace vs DNS Server:** A DNS Server test is like asking a librarian (the resolver) for a book — you get the answer but don't see how they found it. A DNS Trace test is like going to the library yourself, starting at the catalogue (root servers), following the references (TLD servers), and finding the book on the shelf (authoritative servers). If the catalogue reference is wrong (lame delegation), the DNS Trace test catches it even though the librarian (resolver cache) still remembers where the book was last time.
- **ThousandEyes account tier:** DNS Trace tests are available on all tiers.

### Step 1 — Configure data collection
DNS Trace test metrics flow through the same Tests Stream — Metrics OTel input.

Verify:
```spl
index=thousandeyes_metrics thousandeyes.test.type="dns-trace" earliest=-30m
| stats count by dns.question.name
```

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="dns-trace"
| stats avg(dns.lookup.availability) as avg_availability avg(dns.lookup.duration) as avg_duration_s by dns.question.name, thousandeyes.source.agent.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| where avg_availability < 100 OR avg_duration_ms > 500
| sort avg_availability, -avg_duration_ms
```

**Understanding this SPL**

`thousandeyes.test.type="dns-trace"` — filters to DNS Trace tests specifically.

`avg_availability < 100` — delegation chain failure. The trace couldn't walk from root to authoritative successfully.

`avg_duration_ms > 500` — even if the chain is valid, a total trace time > 500 ms indicates a slow authoritative server or a very deep delegation chain. Normal DNS Trace duration: 100–300 ms (root + TLD + authoritative). > 500 ms suggests an overloaded authoritative server or an unusually long chain.

**Cache-masked issue detection** (the high-value variant):
```spl
`stream_index` thousandeyes.test.type="dns-trace" OR thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.availability) as avg_availability by thousandeyes.test.type, dns.question.name
| xyseries dns.question.name, thousandeyes.test.type, avg_availability
| eval cache_masked_issue = if("dns-server" >= 99 AND "dns-trace" < 99, "YES — resolver cache hiding a delegation problem", "No")
| where cache_masked_issue = "YES — resolver cache hiding a delegation problem"
```
This is the killer query: it finds domains where the resolver (DNS Server test) shows 100% availability but the delegation chain (DNS Trace test) shows failures. This means the resolver is serving cached answers and the delegation is broken — when the cache expires, the domain will fail for everyone.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`. Throttle by `dns.question.name` for 4 hours.

### Step 3 — Validate
(a) **Manual delegation check.** Use `dig +trace <domain>` from a machine with direct internet access. This performs the same delegation walk that ThousandEyes does. Compare the results with what Splunk shows.

(b) **Known-good domain.** A well-established domain with healthy delegation (e.g., `google.com`) should always show 100% availability and < 300 ms duration from DNS Trace tests.

(c) **Cross-reference with DNS Server tests.** If DNS Trace shows failures but DNS Server shows 100%, a cache-masked issue exists (see the cache-masked variant above). This is the most valuable validation scenario.

### Step 4 — Operationalize
**Dashboard** (add as a row in the UC-5.9.13 "DNS Health" dashboard):
- Table: domain | DNS Trace availability % | DNS Server availability % | status ("Healthy", "Trace failing — cache masking issue", "Both failing — active outage").
- Timechart: DNS Trace duration per domain.

**Runbook** (owner: DNS team):
1. **DNS Trace failing, DNS Server OK:** Cache-masked delegation issue. You have a window of time (equal to the remaining TTL) before the cached answers expire and the outage becomes visible. Urgent fix required.
  a. Check NS records: `dig NS <domain>`. Verify all listed nameservers actually serve the zone: `dig @<ns-server> <domain> SOA`. If a nameserver returns REFUSED or SERVFAIL, it's a lame delegation.
  b. Check glue records: `dig +norec NS <domain> @<tld-server>`. Verify glue A records point to the correct IPs.
  c. Fix the delegation at your registrar or parent zone operator.
2. **DNS Trace failing, DNS Server also failing:** Active delegation outage. All caches have expired. Follow UC-5.9.13 runbook for immediate response.
3. **DNS Trace slow but available:** Authoritative server is overloaded or geographically distant from the testing agents. Check authoritative server health and capacity.

### Step 5 — Troubleshooting

- **DNS Trace always fails from Enterprise Agents behind corporate firewalls** — Corporate firewalls may block outbound DNS (UDP/TCP 53) to root and TLD servers, only allowing queries to approved resolvers. DNS Trace tests require direct access to root servers. Use Cloud Agents for DNS Trace tests if Enterprise Agents are firewalled.

- **DNS Trace duration is very high (> 2000 ms) but availability is 100%** — The authoritative server is slow. Check server-side query logs and CPU utilization. Also check whether the domain has an unusually deep CNAME chain that the trace must follow.

- **All common troubleshooting** — See UC-5.9.13 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-trace"
| stats avg(dns.lookup.availability) as avg_availability avg(dns.lookup.duration) as avg_duration_s by dns.question.name, thousandeyes.source.agent.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| where avg_availability < 100 OR avg_duration_ms > 500
| sort avg_availability, -avg_duration_ms
```

## Visualization

(1) Table: domain, agent, availability %, resolution time (ms) — sorted by availability ascending (failures first), then by duration descending (slowest traces). (2) Timechart: availability and duration per domain over 24 hours. (3) Single value: count of domains with delegation chain failures (red ≥ 1). (4) Combined with UC-5.9.13 (DNS Server availability) — if DNS Server shows 100% but DNS Trace shows failures, a cache-masked delegation issue exists.

## Known False Positives

**TLD server maintenance.** TLD operators (e.g., Verisign for .com, AFNIC for .fr) occasionally perform maintenance on individual TLD name servers, which may cause DNS Trace tests to fail when they hit the maintained server during the delegation walk. Distinguish by checking whether the failure is brief (< 1 hour) and whether it correlates with TLD operator maintenance notices. The domain should still resolve via other TLD servers — DNS Trace tests that hit a different TLD server in the next round will succeed.

**Root server unreachability from specific agents.** If an Enterprise Agent can't reach certain root servers (e.g., firewall blocking outbound UDP 53 to root server IPs), the DNS Trace test may fail or take a very long time as it tries alternate root servers. Distinguish by checking whether the failure is consistent from one agent while other agents show 100%.

**Registrar DNS record propagation.** After changing NS records at your registrar, TLD servers propagate the update on their own schedule (typically 15 minutes to 48 hours depending on the TLD). During propagation, some DNS Trace tests may follow the old delegation and fail if the old nameservers have been decommissioned. This is a real window of vulnerability, not a false positive, but it's expected during migrations.

**Slow authoritative DNS response.** DNS Trace tests walk the full chain, so the total `dns.lookup.duration` includes the response time of every server in the chain (root + TLD + authoritative). If your authoritative server is slow (overloaded, geographically distant), the trace duration will be high even though the delegation is correct. Distinguish this from a delegation issue by checking whether availability is 100% (delegation is fine, just slow) vs < 100% (delegation is broken).

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes DNS Trace Test Configuration](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/dns-tests/dns-trace-test)
- [Lame Delegations — Understanding broken NS records (ICANN)](https://www.icann.org/resources/pages/lame-delegation-2013-05-01-en)
