<!-- AUTO-GENERATED from UC-5.9.25.json — DO NOT EDIT -->

---
id: "5.9.25"
title: "Remote Worker Connectivity Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.25 · Remote Worker Connectivity Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep an eye on how good each remote worker's home internet connection is, so when they call IT saying 'everything is slow,' we can immediately tell them whether it's their internet provider, their Wi-Fi, or something on our end.*

---

## Description

Monitors gateway connectivity health for remote and hybrid workers by analyzing Endpoint Agent Local Network metrics, grouped by ISP and connection type. Identifies remote workers whose home or mobile network is causing poor digital experience — enabling IT to provide targeted support (e.g., "your ISP is dropping packets") rather than generic troubleshooting.

## Value

In a hybrid workforce, 30–60% of connectivity issues originate in the employee's home network — not in the corporate infrastructure the IT team controls. Without endpoint visibility, the help desk has no data to distinguish "our VPN is slow" from "your Wi-Fi router needs rebooting." This UC gives the service desk concrete evidence: "Your ISP [Comcast] is showing 3% packet loss to your gateway — that's causing your Teams call drops. Try connecting via Ethernet or contact your ISP." This eliminates the circular escalation loop (service desk → network team → cloud team → back to service desk) that wastes hours per ticket. It also enables proactive outreach: when multiple remote workers on the same ISP in the same region show degraded scores simultaneously, IT can send a mass communication before the tickets flood in.

## Implementation

Uses the same Endpoint Agent data stream as UC-5.9.24. Filter by `target.type="gateway"` to focus on the first network hop from the user's device. Group by ISP attributes to identify ISP-level patterns.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.24 apply — Endpoint Agents deployed, endpoint data streaming to Splunk.
- **Sufficient endpoint coverage.** For meaningful remote worker analysis, Endpoint Agents should be deployed on at least a representative sample of remote workers' devices. Full deployment across the remote workforce is ideal.

### Step 1 — Configure data collection
Same as UC-5.9.24. No additional configuration needed.

Verify remote worker data:
```spl
index=thousandeyes_metrics thousandeyes.test.domain="endpoint" target.type="gateway"
| stats dc(thousandeyes.source.agent.name) as agents count by thousandeyes.source.agent.network.org
| sort -agents
```
This shows which ISPs your endpoints are using. Residential ISPs (Comcast, AT&T, BT, Telenor, etc.) indicate remote workers.

### Step 2 — Create the search
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, thousandeyes.source.agent.network.org, thousandeyes.source.agent.connection.type, thousandeyes.source.agent.geo.country.iso_code
| eval avg_latency_ms=round(avg_latency*1000,1)
| where avg_score < 0.7
| sort avg_score
```

**ISP-level aggregation** (identifies ISP-wide issues):
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-4h
| stats avg(network.score) as avg_score dc(thousandeyes.source.agent.name) as affected_agents avg(network.loss) as avg_loss by thousandeyes.source.agent.network.org
| where avg_score < 0.7 AND affected_agents > 3
| sort avg_score
```
If > 3 users on the same ISP show degraded scores simultaneously, it's likely an ISP-level issue.

**Connection type comparison:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-24h
| timechart span=1h avg(network.score) by thousandeyes.source.agent.connection.type
```
Expected: Ethernet scores consistently higher than Wireless.

**Scheduling:** cron `*/15 * * * *`, time range `-1h to now`.

### Step 3 — Validate
(a) Compare ISP names with your known employee population. Are the expected residential ISPs showing up?
(b) Cross-reference with the ThousandEyes UI: **Endpoint Agents → Views → Network Access → filter by Agent**.
(c) Ask a remote worker to run a speed test while checking their Endpoint Agent score in Splunk. The scores should correlate.

### Step 4 — Operationalize
**Dashboard** ("Remote Worker Health"):
- ISP health scoreboard: average network score per ISP.
- Worst-performing endpoints table.
- Connection type comparison chart.
- Geographic distribution map.

**Runbook** (owner: service desk):
1. User reports connectivity issues. Look up their endpoint in the dashboard.
2. If `network.score` is low and ISP shows degradation → advise user: "Your ISP [X] is experiencing issues. Try connecting via Ethernet if on Wi-Fi, or contact your ISP."
3. If `network.score` is low and connection type is Wireless → advise user: "Your Wi-Fi signal may be weak. Try moving closer to your router or connecting via Ethernet."
4. If `network.score` is fine but application is slow → the issue is beyond the local network (VPN, cloud, application). Escalate with the endpoint data as evidence.
5. If multiple users on the same ISP are affected → proactive communication: "We're aware of connectivity issues affecting users on [ISP] in [region]. The issue is with the ISP, not our systems."

### Step 5 — Troubleshooting
- **`thousandeyes.source.agent.network.org` shows "Unknown"** — The agent couldn't determine the ISP via reverse DNS/whois. This may happen on certain cellular connections or tunneled traffic.

- **All endpoints show the same ISP** — If all endpoints show your corporate ISP, the Endpoint Agents may be on-prem (not remote) or always-on VPN is masking the actual ISP. Check `target.type="vpn"` data to see if VPN is active.

- See UC-5.9.24 Step 5 for general endpoint data troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, thousandeyes.source.agent.network.org, thousandeyes.source.agent.connection.type, thousandeyes.source.agent.geo.country.iso_code
| eval avg_latency_ms=round(avg_latency*1000,1)
| where avg_score < 0.7
| sort avg_score
```

## Visualization

(1) Table: remote workers sorted by network score (worst first), showing ISP, connection type, country. (2) Bar chart: average network score by ISP — identifies problematic ISPs. (3) Map: endpoints plotted by location, colour-coded by score. (4) Pie chart: connection type distribution (Wireless vs Ethernet). (5) Timechart: average gateway latency by ISP over 24 hours.

## Known False Positives

**Home router reboots.** A brief connectivity loss when a home router restarts (ISP firmware update, power blip) causes a spike in loss and latency. These are typically < 5 minutes and self-resolve. Filter by duration to exclude transient blips.

**Shared home bandwidth.** A remote worker's family member streaming 4K video or downloading a game can saturate the home internet connection, degrading the worker's network metrics. This is a real experience issue but not an IT-fixable problem — advise the user on bandwidth management.

**Coffee shop / mobile hotspot connections.** Remote workers on public Wi-Fi or mobile hotspots inherently have worse connectivity than home broadband. These are expected to show lower scores. Segment by `thousandeyes.source.agent.connection.type` and treat Wireless connections differently from Ethernet.

**ISP maintenance windows.** Regional ISP maintenance (typically 1–5 AM local time) may degrade metrics for workers in that region. Check ISP status pages and maintenance calendars.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes Endpoint Agent — Local Network testing](https://docs.thousandeyes.com/product-documentation/endpoint-agent)
- [ThousandEyes OTel v2 — Endpoint Experience Local Network attributes](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
