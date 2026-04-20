---
id: "5.6.11"
title: "DHCP Lease Duration Analysis"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.6.11 · DHCP Lease Duration Analysis

## Description

Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.

## Value

Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.

## Implementation

Collect DHCP server logs. Analyze lease durations per scope. Identify scopes with unusually short leases (frequent renewals) or extremely long leases. Adjust based on network type (guest vs. corporate).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_infoblox, Windows DHCP logs.
• Ensure the following data sources are available: `sourcetype=infoblox:dhcp`, `sourcetype=DhcpSrvLog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect DHCP server logs. Analyze lease durations per scope. Identify scopes with unusually short leases (frequent renewals) or extremely long leases. Adjust based on network type (guest vs. corporate).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="infoblox:dhcp" "DHCPACK"
| rex "lease (?<lease_ip>\d+\.\d+\.\d+\.\d+).*?(?<lease_duration>\d+)"
| stats avg(lease_duration) as avg_lease, count as renewals by subnet
| eval avg_hours=round(avg_lease/3600,1) | sort -renewals
```

Understanding this SPL

**DHCP Lease Duration Analysis** — Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.

Documented **Data sources**: `sourcetype=infoblox:dhcp`, `sourcetype=DhcpSrvLog`. **App/TA** (typical add-on context): Splunk_TA_infoblox, Windows DHCP logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: infoblox:dhcp. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="infoblox:dhcp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by subnet** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (scope, avg lease, renewal count), Bar chart (renewals by scope).

## SPL

```spl
index=network sourcetype="infoblox:dhcp" "DHCPACK"
| rex "lease (?<lease_ip>\d+\.\d+\.\d+\.\d+).*?(?<lease_duration>\d+)"
| stats avg(lease_duration) as avg_lease, count as renewals by subnet
| eval avg_hours=round(avg_lease/3600,1) | sort -renewals
```

## Visualization

Table (scope, avg lease, renewal count), Bar chart (renewals by scope).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
