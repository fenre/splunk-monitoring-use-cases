---
id: "5.13.68"
title: "Catalyst Center + ISE Authentication Correlation"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.68 · Catalyst Center + ISE Authentication Correlation

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

Prerequisites
• UC-5.13.21 and UC-5.13.40 complete; `index=catalyst` `cisco:dnac:issue` and `index=ise` `cisco:ise:*` (or equivalent) with overlapping time coverage.
• Field alignment: `managementIpAddress` on Catalyst Center issues must match the NAS or access device address ISE reports as `nas_ip_address` (rename in subsearch to `managementIpAddress` for the join).

Step 1 — TA 7538 accounts
- Configure **Catalyst Center** per UC-5.13.1 (Intent API polling for Assurance/issues).
- Add an **ISE** account in the same TA to your ISE admin/API endpoint; enable ISE data types required for your auth visibility (e.g. admin API streams per TA documentation).
- Optional: forward ISE RADIUS/syslog to Splunk and parse as `cisco:ise:syslog` for pass/fail granularity if API fields are insufficient.

Step 2 — Baseline SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding" | join type=left managementIpAddress [search index=ise sourcetype="cisco:ise:*" | stats count as auth_failures by nas_ip_address | rename nas_ip_address as managementIpAddress] | where isnotnull(auth_failures) | stats count as correlated_issues sum(auth_failures) as total_auth_failures by deviceName, managementIpAddress | sort -total_auth_failures
```

Step 3 — Tuning
- Tighten `category` to your onboarding/triage taxonomy if it differs from `Onboarding`.
- If `managementIpAddress` is missing on issues, use `coalesce(managementIpAddress,deviceIp,host)` on the left after verifying field names in your data.
- For volume, consider `tstats` summaries or a **lookup** of latest ISE auth failures by NAS IP to replace the subsearch in production.

Step 4 — Runbook
- **High total_auth_failures** with correlated issues: investigate ISE policy, RADIUS shared secret, and endpoint identity.
- **Correlated issues without ISE signal:** confirm ISE input health and that `nas_ip_address` truly maps to the same device IP you see in Catalyst Center.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" category="Onboarding" | join type=left managementIpAddress [search index=ise sourcetype="cisco:ise:*" | stats count as auth_failures by nas_ip_address | rename nas_ip_address as managementIpAddress] | where isnotnull(auth_failures) | stats count as correlated_issues sum(auth_failures) as total_auth_failures by deviceName, managementIpAddress | sort -total_auth_failures
```

## Visualization

Sorted table: deviceName, managementIpAddress, correlated_issues, total_auth_failures; optional column chart of top access layers by total_auth_failures.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ISE + Splunk integration](https://developer.cisco.com/docs/identity-services-engine/)
