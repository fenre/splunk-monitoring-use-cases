<!-- AUTO-GENERATED from UC-5.13.68.json — DO NOT EDIT -->

---
id: "5.13.68"
title: "Catalyst Center + ISE Authentication Correlation"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.68 · Catalyst Center + ISE Authentication Correlation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We connect the dots between network problems and login system problems to quickly figure out whether it is the network or the authentication server that is causing people to fail to connect. This helps your team act on facts instead of guesses.*

---

## Description

Correlates Catalyst Center client onboarding issues with ISE authentication failure events to determine whether client connectivity problems are caused by network infrastructure (Catalyst Center) or identity services (ISE).

## Value

When users cannot connect, the root cause could be the network or the authentication server. Cross-correlating Catalyst Center and ISE data isolates the failing component in minutes instead of hours.

## Implementation

Both Catalyst Center and ISE data are ingested via the same Cisco Catalyst Add-on (7538). Ensure both account types are configured:

1. **Catalyst Center account:** Configure as per UC-5.13.1 setup
2. **ISE account:** In the TA, add an ISE account pointing to your ISE PAN node
3. **Enable ISE inputs:** Enable the ISE administrative input with data types `security_group_tags,authz_policy_hit,ise_tacacs_rule_hit`
4. **ISE index:** ISE data goes to `index=ise` by default
5. **Correlation key:** Match on device IP address — Catalyst Center `managementIpAddress` maps to ISE `nas_ip_address`

For ISE authentication logs (RADIUS), you may also need syslog ingestion from ISE to Splunk (sourcetype `cisco:ise:syslog`) for detailed auth pass/fail events.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (Splunkbase 7538) with `issue` or `devicehealth` inputs enabled to `index=catalyst`.
- Cisco ISE data available in Splunk — typically via syslog to `index=ise`, sourcetype `cisco:ise:syslog` or `cisco:ise:*`.
- Both data sources must be collecting concurrently for the same time windows.
- Network path between ISE and the Catalyst Center-managed infrastructure must exist (ISE authenticating users/devices on Catalyst Center-managed switches/APs).
- Understand the join key: `managementIpAddress` (Catalyst Center) ↔ `nas_ip_address` (ISE). If devices use different IPs for management and RADIUS, create a `catalyst_ise_ip_map` lookup.

### Step 1 — Configure data collection
This UC correlates Catalyst Center infrastructure health with ISE authentication events:
- **Catalyst Center side:** `sourcetype=cisco:dnac:issue` or `cisco:dnac:devicehealth` — polled at 900s intervals. Provides device health, reachability, and Assurance issues.
- **ISE side:** `sourcetype=cisco:ise:syslog` — arrives via syslog in real-time. Provides authentication attempts, failures, and policy decisions.

Key fields for correlation:
- Catalyst Center: `managementIpAddress`, `deviceName`, `overallHealth`, `reachabilityHealth`.
- ISE: `nas_ip_address` (Network Access Server — the switch/AP authenticating the user), `username`, `ise_auth_result` (SUCCESS/FAILURE), `ise_auth_failure_reason`, `endpoint_mac`.
- Correlation key: `managementIpAddress` ↔ `nas_ip_address`.

Expected volume: ISE generates high-volume syslog (thousands of events/hour in enterprise environments). Pre-filter to failed authentications for the join to maintain search performance.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as cc_health latest(reachabilityHealth) as cc_reach by deviceName, managementIpAddress, siteId
| join managementIpAddress type=left [search index=ise sourcetype="cisco:ise:*" ise_auth_result="FAILURE" | stats count as auth_failures dc(username) as affected_users values(ise_auth_failure_reason) as failure_reasons by nas_ip_address | rename nas_ip_address as managementIpAddress]
| eval correlation=case(cc_reach="Unreachable" AND auth_failures>0, "Device Down + Auth Failures", cc_health<50 AND auth_failures>10, "Health Degraded + High Auth Failures", auth_failures>50, "Mass Auth Failure", isnotnull(auth_failures), "Auth Failures Present", 1==1, "No ISE Correlation")
| where correlation!="No ISE Correlation"
| sort correlation, -auth_failures
```

#### Understanding this SPL:
- **`ise_auth_result="FAILURE"`**: Pre-filters ISE data to failed authentications only. This dramatically reduces the subsearch volume for the join.
- **`join managementIpAddress type=left`**: Correlates Catalyst Center devices with ISE authentication failures occurring on the same network access device. Left join preserves Catalyst Center devices without ISE failures.
- **`dc(username) as affected_users`**: Counts distinct users affected by authentication failures on each device. High affected_users with a single device suggests a device-side issue; high failures for a single user suggests a user credential issue.
- **`values(ise_auth_failure_reason)`**: Shows the ISE failure reasons — "Wrong password", "User disabled", "Certificate validation failed", etc. This guides remediation.

### Step 3 — Validate
- **Cross-reference:** Select a Catalyst Center-managed switch. In ISE, check the RADIUS Live Log for that switch's IP. Compare the failure count and reasons with the Splunk join results.
- **Join key validation:** Run `| stats dc(managementIpAddress) as cc_ips` and `| stats dc(nas_ip_address) as ise_ips` separately. If the overlap is low, the join key may need a lookup translation.
- **Volume check:** If ISE generates >100,000 events/hour, the subsearch in the join may hit Splunk's subsearch limits (default 50,000 results). Consider pre-summarizing ISE data or using `| lookup` instead of `| join`.

### Step 4 — Operationalize
- **Dashboard:** Two-panel layout — Catalyst Center device health on the left, ISE authentication failure summary on the right, with a correlation column connecting them. Add a timechart showing authentication failure rate alongside device health score trends.
- **Alert:** Trigger when `correlation="Device Down + Auth Failures"` — this indicates a network device failure causing cascading authentication failures. Route to NOC for immediate attention.
- **Root cause workflow:** When correlation shows "Mass Auth Failure" without device health degradation, the root cause is likely in ISE (RADIUS server issue, certificate expiration, policy misconfiguration). Route to the IAM/security team.

### Step 5 — Troubleshoot
- **Join returns no ISE data:** The `managementIpAddress` in Catalyst Center may not match `nas_ip_address` in ISE. Many devices use a loopback or VLAN SVI IP for RADIUS rather than the management IP. Create a `catalyst_ise_ip_map` lookup: `| inputlookup catalyst_ise_ip_map | lookup ... OUTPUT managementIpAddress`.
- **ISE subsearch exceeds limits:** The default subsearch limit is 50,000 results. For high-volume ISE environments, either increase `max_subsearch_results` in `limits.conf` or restructure the search to use a summary index or lookup for ISE data.
- **Time scale mismatch:** ISE syslog arrives in real-time while Catalyst Center health is polled every 15 minutes. Use `| bin _time span=15m` on both sources to align time windows.
- **Credential-related failures dominating:** Most authentication failures are caused by expired passwords or locked accounts, not network issues. Pre-filter: `| where ise_auth_failure_reason!="Wrong password" AND ise_auth_failure_reason!="User disabled"` to focus on infrastructure-related failures.

Additional operational context for Catalyst Center + ISE Authentication Correlation:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding" | join type=left managementIpAddress [search index=ise sourcetype="cisco:ise:*" | stats count as auth_failures by nas_ip_address | rename nas_ip_address as managementIpAddress] | where isnotnull(auth_failures) | stats count as correlated_issues sum(auth_failures) as total_auth_failures by deviceName, managementIpAddress | sort -total_auth_failures
```

## Visualization

Sorted table: deviceName, managementIpAddress, correlated_issues, total_auth_failures; optional column chart of top access layers by total_auth_failures.

## Known False Positives

**ISE reporting authentication events for a different NAS than the Catalyst Center-managed device.** The join on `managementIpAddress` assumes the device's management IP in Catalyst Center matches the NAS IP in ISE. If the device uses a different IP for RADIUS (e.g., a loopback or VLAN SVI), the join will miss valid correlations. Distinguish by comparing the join key: check whether `managementIpAddress` in Catalyst Center matches `nas_ip_address` in ISE for the same device. Fix by using a `catalyst_ise_ip_map` lookup to translate between management IPs and NAS IPs.

**ISE authentication failures caused by user credential issues, not network problems.** The correlation may surface ISE authentication failures that coincide with Catalyst Center onboarding issues, but the root cause is an expired password or locked account, not a network fault. Distinguish by checking the ISE failure reason: `ise_auth_failure_reason` will indicate credential-related failures (e.g., "Wrong password", "User disabled"). Do not suppress — the correlation is valid, but the remediation path is IAM, not network operations.

**High-volume ISE authentication events overwhelming the join.** In large environments, ISE generates thousands of authentication events per hour. The join may be slow or incomplete if the ISE data volume exceeds the subsearch limits. Distinguish by checking whether the join returns incomplete results (missing devices known to have ISE events). Suppress by pre-filtering ISE data to failed authentications only: `| where ise_auth_result!="SUCCESS"` before the join.

**ISE and Catalyst Center data on different time scales.** ISE syslog events arrive in real-time while Catalyst Center issues are polled every 15 minutes. The time-based join may miss correlations where the ISE failure occurs between Catalyst Center poll cycles. Distinguish by widening the time window for the join using `| bin _time span=15m` on both data sources.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ISE + Splunk integration](https://developer.cisco.com/docs/identity-services-engine/)
- [Catalyst Center Issues API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!issues)
