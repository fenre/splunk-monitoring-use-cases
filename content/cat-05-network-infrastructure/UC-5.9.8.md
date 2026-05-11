<!-- AUTO-GENERATED from UC-5.9.8.json — DO NOT EDIT -->

---
id: "5.9.8"
title: "BGP Reachability Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.8 · BGP Reachability Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We check whether the addresses that point to our company can be found by routers around the world. If our address disappears from the internet's directory in some region, we catch it immediately — because until it's back, people in that region simply cannot reach us at all.*

---

## Description

Monitors whether your BGP-advertised IP prefixes are visible in the global routing table from ThousandEyes' worldwide network of BGP route monitors. A prefix dropping below 100% reachability means some ISPs' routers no longer have a route to your addresses — users behind those ISPs cannot reach your services, even though your infrastructure is up and running.

## Value

A BGP reachability drop is the most severe network event possible for an internet-facing business — if your prefix is unreachable from a region, no amount of server capacity or CDN caching matters because packets cannot find a route to your network. Unlike latency or loss (which degrade performance), a reachability drop means total blackout for affected users. The business impact scales with the number of monitors showing the prefix as unreachable: a drop from 100% to 95% means ~15 ISPs have lost the route (potentially millions of users in those ISPs' footprints). Catching it in Splunk within minutes — rather than waiting for customer complaints — lets the NOC immediately check whether it's your announcement (misconfiguration), your upstream ISP (peering issue), or a BGP hijack (security incident) and take the appropriate action.

## Implementation

Create BGP tests in ThousandEyes for each critical prefix your organization announces. Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Routing → BGP**. Enter the prefix (e.g., `203.0.113.0/24`) and optionally specify the expected origin ASN. ThousandEyes selects monitors automatically but you can add/remove specific ones. Enable the Tests Stream — Metrics input if not already enabled — BGP metrics flow through the same OTel stream as Agent-to-Server metrics.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **BGP tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Routing → BGP**. Enter each critical prefix your organization announces. Key settings:
  - **Prefix:** Your advertised prefix (e.g., `203.0.113.0/24`). Monitor every prefix that serves production traffic.
  - **Include Covered Prefixes:** Enable if you want to track sub-prefixes within the monitored prefix.
  - **Alert on Prefix Hijack:** Enable this to get ThousandEyes alerts when an unexpected ASN originates your prefix.
- **ThousandEyes account tier:** BGP Route Monitoring is available on all ThousandEyes tiers (Essentials, Advantage, Premier). No Enterprise Agent is required — BGP tests use ThousandEyes' global network of BGP route monitors.
- **Know your expected origin ASN.** Document which ASN(s) should be originating each prefix. This is critical for distinguishing legitimate routing changes from hijacks (UC-5.9.11).
- **RPKI:** If your organization uses RPKI (Resource Public Key Infrastructure), ensure your ROAs (Route Origin Authorizations) are current and match your actual announcements. Expired or misconfigured ROAs cause legitimate reachability drops from ISPs that enforce RPKI.

### Step 1 — Configure data collection
BGP test metrics flow through the same Tests Stream — Metrics OTel input as Agent-to-Server and Agent-to-Agent metrics. If the stream is already enabled, BGP data is included automatically (the stream covers all test types unless filtered).

Verify BGP data is flowing:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="bgp" earliest=-30m
| stats count by network.prefix, thousandeyes.monitor.name
| stats dc(thousandeyes.monitor.name) as monitor_count by network.prefix
```
You should see your monitored prefix(es) with `monitor_count` close to the number of BGP monitors ThousandEyes assigned to the test (typically 250–350 for global coverage). If `monitor_count` is 0, the BGP test may not be included in the stream scope, or the test hasn't completed its first round yet (BGP tests default to 15-minute intervals).

**BGP vs Agent tests — key differences:**
- BGP tests are **passive** — they observe routing tables, not send probes. No Enterprise Agent needed.
- BGP data appears at **15-minute intervals** (default), not 60-second intervals like Agent-to-Server.
- BGP metrics use `thousandeyes.monitor.name` and `thousandeyes.monitor.location`, not `thousandeyes.source.agent.name`.
- BGP-specific metrics: `bgp.reachability`, `bgp.path_changes.count`, `bgp.updates.count`. Network metrics (`network.latency`, `network.loss`) are NOT present in BGP test data.

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability min(bgp.reachability) as min_reachability by thousandeyes.monitor.name, network.prefix
| where avg_reachability < 100
| sort avg_reachability
```

**Understanding this SPL**

`thousandeyes.test.type="bgp"` — filters to BGP tests only. This is essential because the `stream_index` macro returns all test types.

`avg(bgp.reachability)` — the average reachability across the search window for each monitor-prefix pair. A value of 100 means the monitor saw the prefix as reachable in every polling round. A value of 80 means the prefix was reachable in 80% of rounds (unreachable 20% of the time).

`min(bgp.reachability)` — the worst single reachability reading. Useful for distinguishing sustained drops (min and avg both low) from brief flaps (min low but avg near 100 — meaning the prefix recovered quickly).

`where avg_reachability < 100` — fires when any monitor shows any reachability degradation. For noisy environments, relax to `< 98` or `< 95`. For critical prefixes carrying production traffic, keep at `< 100` — any drop deserves investigation.

**Aggregate view variant** (overall reachability per prefix across ALL monitors):
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as global_reachability dc(thousandeyes.monitor.name) as total_monitors by network.prefix
| eval unreachable_monitors = round(total_monitors * (100 - global_reachability) / 100, 0)
| where global_reachability < 100
| sort global_reachability
```
This gives a fleet-level view: "prefix X is 97% reachable globally, unreachable from ~9 of 300 monitors."

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now` (two BGP collection rounds). Trigger on "Number of results > 0". For critical prefixes, throttle by `network.prefix` for 1 hour (reachability drops are urgent — don't suppress for 4 hours like latency alerts). For non-critical prefixes, throttle for 4 hours.

### Step 3 — Validate
(a) **Cross-reference ThousandEyes UI.** Navigate to **Cloud & Enterprise Agents → Views → BGP Route Visualization** and select the same prefix and time window. The UI shows a map of monitors colour-coded by reachability. Compare the numbers in Splunk to the ThousandEyes UI.

(b) **Known-good prefix.** For a prefix that is stable and well-announced, reachability should be 100% across all monitors. If any monitor shows < 100%, investigate that specific monitor — it may have its own peering issues.

(c) **Verify prefix match.** `| stats dc(network.prefix) as prefix_count values(network.prefix) as prefixes` — confirm the prefixes in the data match the prefixes you configured in ThousandEyes. Typos in prefix configuration are common (e.g., `/24` vs `/23`).

(d) **Check monitor coverage.** For critical prefixes, verify you have sufficient geographic monitor diversity: `| stats dc(thousandeyes.monitor.location) as locations by network.prefix`. You want monitors in all regions where you have users.

### Step 4 — Operationalize
**Dashboard** ("BGP Prefix Health" — designed for NOC wall display):
- Row 1 — Single value tiles: one per critical prefix showing current reachability %. Red if < 100%. This should be the most prominent element on the NOC wall — a red prefix tile demands immediate attention.
- Row 2 — World map: ThousandEyes includes a built-in BGP map panel in the Splunk app. Alternatively, build one using Splunk Maps: plot each monitor location with colour-coded reachability.
- Row 3 — Table: prefix | global reachability % | monitors showing unreachable | worst monitor name + location — sorted by reachability ascending.
- Row 4 — Timechart: reachability per prefix over 24 hours. This shows the timeline of any drops and how long they lasted.

**Alerting:**
- < 100% reachability for any critical prefix → immediate page (PagerDuty high-urgency). Include the prefix, reachability %, number of affected monitors, and the ThousandEyes permalink.
- < 95% reachability → escalate to NOC manager and ISP contacts simultaneously.
- 0% reachability → major incident, all-hands escalation.

**Runbook** (owner: Network Engineering / NOC / ISP Relations):
1. **Triage:** Open the alert. Note the prefix, reachability %, and which monitors are affected.
2. **Determine scope:** Is reachability down from specific regions (regional ISP issue) or globally (your announcement is withdrawn or hijacked)?
3. **Check your own announcement:** On your border router, verify the prefix is being announced: `show ip bgp summary` / `show ip bgp <prefix>`. If the prefix is not in your local BGP table, it's a misconfiguration on your side.
4. **Check for BGP hijack:** If the prefix IS being announced from your side but ThousandEyes shows a different origin ASN (visible in UC-5.9.11), this may be a BGP hijack. Escalate to security and ISP immediately.
5. **Check upstream ISP:** If your announcement is correct but monitors in specific ISPs show unreachable, your upstream ISP may have a peering issue. Contact the ISP with the ThousandEyes evidence (permalink showing which ISP's monitors lost visibility).
6. **Check RPKI:** If you have ROAs deployed, verify they haven't expired: check rpki-validator.ripe.net for your prefix. Expired ROAs cause ISPs with RPKI enforcement to reject your announcement.
7. **Monitor recovery:** After taking corrective action, watch the reachability timechart for recovery. BGP convergence typically takes 2–15 minutes globally.

### Step 5 — Troubleshooting

- **No BGP data at all** — BGP tests may not be configured in ThousandEyes, or the test type may be filtered out of the OTel stream. Check ThousandEyes test settings and the stream input scope.

- **`bgp.reachability` field is missing but BGP data arrives** — The field name may differ between v1 and v2 OTel models. In v1, the field may be `bgp.metrics.reachability`. Check `| fieldsummary | search field=bgp*` to find the correct field name.

- **Reachability is always exactly 100% even when ThousandEyes UI shows drops** — The search time window may not overlap with the actual drop. BGP tests default to 15-minute intervals, so use `-30m to now` minimum. Also check whether the `stream_index` macro filters out BGP data (some deployments use a separate index for BGP).

- **All common troubleshooting** — See UC-5.9.1 Step 5 for HEC connectivity, OAuth refresh, macro configuration, and general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability min(bgp.reachability) as min_reachability by thousandeyes.monitor.name, network.prefix
| where avg_reachability < 100
| sort avg_reachability
```

## Visualization

(1) World map: BGP reachability by monitor location — green dots for 100%, red dots for < 100%, size proportional to reachability drop. The ThousandEyes Splunk App includes a built-in BGP Reachability map panel. (2) Single value tile: overall reachability % across all monitors and prefixes (red threshold < 100%). (3) Table: monitor name, monitor location, prefix, reachability % — sorted worst-first. (4) Timechart: reachability over time per prefix showing drops and recovery events.

## Known False Positives

**Planned prefix withdrawal for maintenance.** When your network team intentionally withdraws a prefix for maintenance (e.g., renumbering, migrating to a new upstream), reachability drops to 0% as expected. Distinguish by cross-referencing with your change management system. Suppress with a `bgp_maintenance_windows` lookup keyed on `network.prefix`.

**Monitor-specific reachability dips.** Individual BGP monitors may temporarily lose visibility of a prefix due to their own peering issues — an ISP's route server rebooting, a peering session flapping at the IXP. If only 1–2 monitors out of 300 lose reachability while the rest show 100%, the prefix is fine and the monitor is the problem. Distinguish by checking `min_reachability` vs `avg_reachability` — if avg is 99.5% and min is 95%, it's isolated monitor issues.

**Sub-prefix vs aggregate prefix routing.** If you announce both a /24 and a covering /22, some monitors may prefer the aggregate and not track the sub-prefix. Reachability for the sub-prefix may fluctuate even though the aggregate is 100% reachable. Verify by monitoring both the sub-prefix and the aggregate.

**RPKI ROA validation rejecting your announcement.** If your prefix's RPKI ROA (Route Origin Authorization) is expired, misconfigured, or doesn't match your origin ASN, ISPs that enforce RPKI validation will reject your announcement, causing reachability to drop from those ISPs. This is not a false positive per se — it's a real configuration issue — but it's not an attack or outage. Check your RPKI ROA status at rpki-validator.ripe.net.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes BGP Route Monitoring — Understanding BGP tests](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/)
- [ThousandEyes OTel v2 Data Model — BGP metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics/data-model-migration-v1-to-v2)
- [BGP Hijacking — NIST RPKI reference](https://www.nist.gov/publications/)
