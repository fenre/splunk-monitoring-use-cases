<!-- AUTO-GENERATED from UC-2.6.64.json — DO NOT EDIT -->

---
id: "2.6.64"
title: "Citrix Endpoint Management Device Enrollment Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.64 · Citrix Endpoint Management Device Enrollment Failures

## Description

Citrix Endpoint Management (CEM) enrollments that fail by Azure AD, identity-provider, or gateway-based flows strand devices without the policies and secure channels you expect. A rising failure rate in one method (for example AAD) often foreshadows certificate or conditional-access changes rather than a bad device. Tracking failures by method and MDM versus MAM split, with hourly trends, helps operations separate widespread identity drift from a flaky Wi-Fi at one site, and it pairs naturally with the certificate and compliance use cases in the same runbooks.

## Value

Citrix Endpoint Management (CEM) enrollments that fail by Azure AD, identity-provider, or gateway-based flows strand devices without the policies and secure channels you expect. A rising failure rate in one method (for example AAD) often foreshadows certificate or conditional-access changes rather than a bad device. Tracking failures by method and MDM versus MAM split, with hourly trends, helps operations separate widespread identity drift from a flaky Wi-Fi at one site, and it pairs naturally with the certificate and compliance use cases in the same runbooks.

## Implementation

Stream enrollment transactions from the CEM service or appliance into a dedicated index and sourcetype. Normalize `outcome` to lower case. Add a small lookup of acceptable error rates per platform. Alert when hourly non-success events exceed a rolling four-hour baseline by 300 percent, or any single error code appears more than 50 times in an hour. Provide a dashboard by enrollment method and region. Separate corporate-owned and BYOD cohorts if your data model supports it. Coordinate with the identity team when AAD- or IdP-tagged failures lead the chart.

## Detailed Implementation

Prerequisites
• CEM or XenMobile at a supported build; read-only API or file export for enrollments; correct time zone and NTP to correlate with directory logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm field list with one failed lab enrollment. Retain a hashed device identifier, not full IMEI, where privacy policy requires it.

Step 2 — Create the search and alert
Phase one: a daily report. Phase two: dynamic thresholds. Suppress during announced OS upgrades where enrollment spikes are expected.

Step 3 — Validate
Replay a known AAD test failure, confirm a row. Fix the trust and assert recovery in the same chart.

Step 4 — Operationalize
Add a single owner from EUC and one from identity for AAD-tagged error spikes; document escalation paths in the runbook.

## SPL

```spl
index=xd sourcetype="citrix:endpoint:enrollment" outcome!="success"
| eval method=upper(coalesce(enrollment_method, channel, "UNKNOWN"))
| eval mode=coalesce(mdms_scope, mdm_mam, enrollment_mode, "unknown")
| eval platform=coalesce(device_platform, os_type, "unknown")
| bin _time span=1h
| stats count as failures, dc(error_code) as unique_errors by _time, method, mode, platform
| where failures>=5
| sort - _time, failures
```

## Visualization

Time chart: enrollment failures by method; bar chart: MDM versus MAM failure share; drill table with top error_code and last device sample IDs (masked).

## References

- [Citrix Endpoint Management product documentation](https://docs.citrix.com/en-us/citrix-endpoint-management.html)
