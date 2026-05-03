<!-- AUTO-GENERATED from UC-5.20.8.json — DO NOT EDIT -->

---
id: "5.20.8"
title: "IPv6 Prefix Plan Compliance Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.20.8 · IPv6 Prefix Plan Compliance Audit

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We compare the addresses actually being used on the network against the approved address plan, the same way a city planner checks that street addresses match the official zoning map. If someone builds on an unapproved lot, we catch it.*

---

## Description

Compares IPv6 prefixes observed in routing tables or traffic against the authoritative IPv6 prefix plan (IPAM), identifying three categories: compliant prefixes (in the plan and active), violations (deprecated prefixes still being routed), and unauthorized prefixes (observed on the network but not in the plan at all). NIST SP 800-119 §5.2 explicitly requires organisations to maintain an IPv6 addressing plan and periodically audit actual usage against it. This UC automates that audit.

## Value

Without prefix plan compliance auditing, IPv6 address space sprawls uncontrolled — departments self-assign /64s from the organisation's /32 allocation, rogue SLAAC prefixes appear on unauthorised VLANs, and deprecated prefixes persist in routing tables long after their associated services are decommissioned. Each unauthorized prefix is a blind spot: no firewall rules cover it, no monitoring watches it, and no documentation explains it. This UC turns the IPAM plan from a static document into an enforced policy. For regulated environments, the compliance percentage is an auditable metric for NIST SP 800-119 and DISA STIG conformance.

## Implementation

Export your IPv6 prefix plan from IPAM (Infoblox, NetBox, or spreadsheet) into a Splunk CSV lookup. Collect IPv6 routing tables from all Layer 3 devices via scripted CLI (`show ipv6 route summary` or full route table), SNMP polling (inetCidrRouteTable), or passive prefix observation from NetFlow/IPFIX. The search joins observed prefixes against the plan and flags deviations. Schedule weekly for compliance reporting.

## Detailed Implementation

### Prerequisites
- An authoritative IPv6 prefix plan in CSV format, loadable as a Splunk lookup. This is the most critical prerequisite — without it, the UC cannot function. The CSV must contain at minimum: `prefix` (e.g., `2001:db8:abcd:100::/64`), `status` (active, reserved, deprecated). Additional useful fields: `site`, `vlan_id`, `description`, `owner`, `last_updated`.
- Example `ipv6_prefix_plan.csv`:
```csv
prefix,prefix_length,site,vlan_id,description,status
2001:db8:abcd:100::/64,64,HQ,100,HQ User VLAN,active
2001:db8:abcd:200::/64,64,HQ,200,HQ Server VLAN,active
2001:db8:abcd:300::/64,64,Branch1,300,Branch1 User VLAN,active
2001:db8:abcd:f00::/64,64,HQ,N/A,Old test network,deprecated
```
- IPv6 routing table collection from all Layer 3 devices. Options:
  - **Scripted CLI:** SSH to each router, run `show ipv6 route`, forward output to Splunk via syslog or file monitoring.
  - **SNMP:** Poll `inetCidrRouteTable` (RFC 4292, OID 1.3.6.1.2.1.4.24.7) with SC4SNMP or Telegraf.
  - **gNMI:** Subscribe to OpenConfig `openconfig-network-instance:network-instances/network-instance/afts/ipv6-unicast` for real-time route table streaming (see subcategory 5.11).
  - **Passive:** Aggregate NetFlow/IPFIX source addresses to /64 boundaries to discover actively-used prefixes without polling routers directly.

### Step 1 — Configure data collection

**Create the prefix plan lookup:**
1. Export your IPv6 prefix plan from IPAM (Infoblox: Grid Manager → IPAM → IPv6 → export CSV, or NetBox: IPAM → Prefixes → export).
2. Upload as `ipv6_prefix_plan.csv` to `$SPLUNK_HOME/etc/apps/<your_app>/lookups/`.
3. Create the lookup definition in transforms.conf:
```
[ipv6_prefix_plan]
filename = ipv6_prefix_plan.csv
match_type = CIDR(prefix)
```
Note: Splunk's CIDR match for lookups works with IPv6 prefixes. The lookup will match an observed /64 against a planned /48 if the /64 falls within the /48's range.

**Collect routing tables:**
Option A — scripted input (simplest):
```bash
#!/bin/bash
# collect_ipv6_routes.sh
for router in $(cat /opt/splunk/etc/apps/myapp/lookups/router_list.txt); do
  ssh -o StrictHostKeyChecking=no splunk-svc@$router "show ipv6 route" 2>/dev/null
done
```
```
# inputs.conf
[script://./bin/collect_ipv6_routes.sh]
interval = 86400
sourcetype = cisco:ios
index = network
```
Run daily — routing tables don't change frequently in stable networks.

Option B — SNMP (for large-scale automation):
```yaml
# SC4SNMP profiles.yaml
profile_ipv6_routes:
  frequency: 86400
  varBinds:
    - ['1.3.6.1.2.1.4.24.7']  # inetCidrRouteTable
```

Verification:
```spl
index=network sourcetype=cisco:ios "show ipv6 route" earliest=-48h
| rex "(?<prefix>[0-9a-fA-F:]+/\d+)"
| stats dc(prefix) as unique_prefixes dc(host) as routers_reporting
```

### Step 2 — Create the search and alert

**Primary search — prefix plan compliance audit:**
```spl
index=network sourcetype="cisco:ios" "show ipv6 route" earliest=-24h
| rex "(?<route_type>[CSLBOD])\s+(?<prefix>[0-9a-fA-F:]+/\d+).*?(?:via\s+(?<next_hop>[0-9a-fA-F:]+|[A-Za-z0-9/]+))?"
| where isnotnull(prefix) AND NOT match(prefix, "^fe80:") AND NOT match(prefix, "^ff") AND prefix != "::/0"
| stats latest(route_type) as type latest(next_hop) as next_hop values(host) as routers_with_route by prefix
| lookup ipv6_prefix_plan prefix OUTPUT site, description, status as plan_status
| eval compliance=case(
    isnotnull(plan_status) AND plan_status="active", "COMPLIANT",
    isnotnull(plan_status) AND plan_status="reserved", "INFO - reserved prefix in use (verify timing)",
    isnotnull(plan_status) AND plan_status="deprecated", "VIOLATION - deprecated prefix still routed",
    isnull(plan_status), "UNAUTHORIZED - prefix not in plan")
| stats count by compliance
| eventstats sum(count) as total
| eval pct=round(count/total*100, 1)
```

**Understanding this SPL:**
- The regex captures route type (C=connected, S=static, L=local, B=BGP, O=OSPF, D=EIGRP) and the prefix with its mask length.
- Filters exclude link-local (fe80::), multicast (ff::), and the default route (::/0) — these are always present and not part of the IPAM plan.
- The CIDR-aware lookup matches observed prefixes against the plan, handling hierarchical matching (/64 within /48 within /32).
- Four compliance states: COMPLIANT, INFO (reserved prefix in active use — may be intentional during migration), VIOLATION (should have been removed), UNAUTHORIZED (never approved).

**Alert — unauthorized prefix detected:**
```spl
index=network sourcetype="cisco:ios" "show ipv6 route" earliest=-24h
| rex "(?<prefix>[0-9a-fA-F:]+/\d+)"
| where isnotnull(prefix) AND NOT match(prefix, "^fe80:") AND NOT match(prefix, "^ff") AND prefix != "::/0"
| lookup ipv6_prefix_plan prefix OUTPUT status as plan_status
| where isnull(plan_status)
| stats dc(prefix) as unauthorized_prefixes values(prefix) as prefixes by host
```
Trigger: any router advertising prefixes not in the IPAM plan.

**Variant — passive prefix discovery from flow data:**
```spl
index=netflow sourcetype=ipfix earliest=-7d
| where match(src_ip, ":")
| rex field=src_ip "(?<prefix_48>[0-9a-fA-F:]{1,19})::[0-9a-fA-F:]*$"
| eval prefix_48=prefix_48 . "::/48"
| stats dc(src_ip) as unique_addresses count as flows by prefix_48
| lookup ipv6_prefix_plan prefix as prefix_48 OUTPUT status
| where isnull(status)
| sort -flows
```

### Step 3 — Validate
(a) **Manual spot-check:** On a core router, run `show ipv6 route summary`. Count the number of /64 prefixes. Compare to the IPAM plan — the COMPLIANT count plus known exceptions (link-local, multicast, default) should approximately match.

(b) **Known-bad test:** Add a test prefix (e.g., `2001:db8:ffff::/48`) to a router's routing table as a static route. Run the search — it should appear as UNAUTHORIZED. Remove the test route afterward.

(c) **Deprecated prefix check:** If your IPAM has deprecated entries, verify at least one appears as VIOLATION in the search results (proving the join works correctly).

(d) **CIDR match validation:** Add a /64 prefix to a router that falls within a /48 in the IPAM plan. Verify the lookup matches it as COMPLIANT (hierarchical CIDR matching).

### Step 4 — Operationalize

**Dashboard** ("IPv6 Prefix Plan Compliance"):
- Row 1 — Pie chart: COMPLIANT / VIOLATION / UNAUTHORIZED / INFO distribution. Single-value: compliance percentage.
- Row 2 — Table: unauthorized prefixes with source router, route type, first observed — action items.
- Row 3 — Table: deprecated-but-routed prefixes — cleanup items.
- Row 4 — Timechart: compliance percentage over 90 days (should trend toward 100%).

**Scheduling:** Weekly (Monday 06:00). Monthly executive report for NIST SP 800-119 compliance.

**Runbook** (owner: Network Architecture / IPAM Team):
1. UNAUTHORIZED prefix: determine origin. Who configured it? Was it approved via change management? If approved, update the IPAM plan. If not, remove it from the routing table.
2. DEPRECATED prefix still routed: schedule removal during the next maintenance window. Check for dependencies — are any services still using this prefix?
3. Compliance < 95%: escalate to Network Architecture lead for a focused cleanup sprint.

### Step 5 — Troubleshooting

- **All prefixes show as UNAUTHORIZED** — The lookup CIDR match may not be working. Test: `| makeresults | eval prefix="2001:db8:abcd:100::/64" | lookup ipv6_prefix_plan prefix`. If no match, check: (a) the lookup file exists and is accessible, (b) the `match_type = CIDR(prefix)` is set in transforms.conf, (c) the prefix format in the CSV matches (colon-hex with /length).

- **Scripted input returns empty** — SSH authentication failure. Check: (a) the `splunk-svc` account has SSH key auth to all routers, (b) the account has `show ipv6 route` privilege, (c) no SSH rate limiting is blocking the script.

- **Too many prefixes to review** — A large enterprise may have hundreds of /64 prefixes. Focus on route types: B (BGP) and O (OSPF) learned routes are less concerning than C (connected) and S (static) routes, because dynamic routes are controlled by routing policy. Prioritise unauthorized C and S routes.

- **IPAM export format issues** — Ensure the CSV uses RFC 5952 canonical form for prefixes. Non-canonical prefixes (uppercase, leading zeros) won't match against canonical routing table output. Normalise before uploading to Splunk.

## SPL

```spl
index=network sourcetype="cisco:ios" "show ipv6 route" earliest=-24h
| rex "(?<route_type>[CSLBOD])\s+(?<prefix>[0-9a-fA-F:]+/\d+).*via\s+(?<next_hop>[0-9a-fA-F:]+|[A-Za-z0-9/]+)"
| where isnotnull(prefix)
| stats latest(route_type) as type latest(next_hop) as next_hop by host, prefix
| lookup ipv6_prefix_plan prefix OUTPUT site, description, status as plan_status
| eval compliance=case(
    isnotnull(plan_status) AND plan_status="active", "COMPLIANT - in plan",
    isnotnull(plan_status) AND plan_status="deprecated", "VIOLATION - deprecated prefix still routed",
    isnull(plan_status), "UNAUTHORIZED - not in prefix plan")
| stats count by compliance
| eventstats sum(count) as total
| eval pct=round(count/total*100, 1)
```

## Visualization

(1) Pie chart: Compliant / Violation / Unauthorized distribution. (2) Single-value: prefix plan compliance percentage (target: 100%). (3) Table: unauthorized prefixes with source router, next-hop, and first-seen timestamp — action items for the IPAM team. (4) Table: deprecated-but-still-routed prefixes — cleanup candidates.

## Known False Positives

**Link-local prefixes (fe80::/10) in routing table.** Connected routes for link-local interfaces always appear in the IPv6 routing table but are never in the IPAM plan because link-local addresses are self-assigned. Filter with `| where NOT match(prefix, "^fe80:")` to exclude them.

**Default route (::/0).** The default route is present in every routing table but won't match a specific prefix in the IPAM plan. Filter with `| where prefix != "::/0"`.

**Multicast routing entries (ff00::/8).** PIM/MLD multicast routing entries appear in some routing table outputs but are not address allocations. Filter with `| where NOT match(prefix, "^ff")`.

**Temporary sub-allocations.** During network changes or migrations, temporary prefixes may be used that haven't yet been added to the IPAM plan. These are correctly flagged as unauthorized — the remediation is to update the plan, not suppress the alert.

## References

- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6 (§5.2 — IPv6 address plan inventory)](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.2.2 — Device and prefix inventory)](https://www.rfc-editor.org/rfc/rfc9099)
- [RFC 4292 — IP Forwarding Table MIB (inetCidrRouteTable for SNMP-based route collection)](https://www.rfc-editor.org/rfc/rfc4292)
