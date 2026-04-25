<!-- AUTO-GENERATED from UC-5.3.24.json — DO NOT EDIT -->

---
id: "5.3.24"
title: "Citrix ADC Web Application Firewall (WAF) Violations"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.3.24 · Citrix ADC Web Application Firewall (WAF) Violations

## Description

Citrix ADC Web Application Firewall inspects HTTP traffic for common attacks (SQL injection, cross-site scripting, JSON/XML threats) and policy violations. Spikes in violations, or critical signatures firing in enforcement mode, indicate active attacks or misconfigured applications. Distinguishing learning mode noise from enforcement blocks, and monitoring geographic blocks, keeps incident response focused and reduces false positives.

## Value

Citrix ADC Web Application Firewall inspects HTTP traffic for common attacks (SQL injection, cross-site scripting, JSON/XML threats) and policy violations. Spikes in violations, or critical signatures firing in enforcement mode, indicate active attacks or misconfigured applications. Distinguishing learning mode noise from enforcement blocks, and monitoring geographic blocks, keeps incident response focused and reduces false positives.

## Implementation

Send WAF log profile output to syslog and index as `citrix:netscaler:syslog`. Parse violation type, action (block, learn, log), and policy. Build correlation searches for attack categories (SQL, XSS, JSON injection) and for geo-IP block actions if logged. Tune thresholds by application: public APIs may legitimately spike; internal apps should not. Use lookups for known scanner IPs and pen-test windows.

## Detailed Implementation

Prerequisites
• Splunk_TA_citrix-netscaler with WAF-relevant syslog in `index=netscaler`.
• WAF log profile bound to vservers; consistent timestamp and severity.
• Field extractions for violation and policy names (or rely on `rex` in the search for first rollout).

Step 1 — Configure data collection
On the ADC, enable logging for the WAF profile: violations, learn vs block decisions, and geo policy hits if used. Forward to Splunk. Avoid logging full request bodies in production if policy forbids; hash or truncate as required.

Step 2 — Create the search and alert
Run the SPL. Alert on sustained elevation above baseline, or on any critical OWASP category in enforcement from sensitive apps. Add suppressions for learning-only noise where appropriate. Integrate with your incident queue for critical spikes.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Dashboard for SecOps, weekly digest for App owners, and runbook steps for false positive tuning ( relax rule, add exception, or fix application).

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:syslog" (WAF OR "Application Firewall" OR APPFW)
| rex field=_raw "(?i)(?<violation>SQL|XSS|JSON|XML|CSRF|OWASP)"
| eval is_learning=if(match(_raw, "(?i)learning"), 1, 0)
| where NOT (is_learning=1 AND match(_raw, "(?i)info"))
| bin _time span=15m
| stats count as hits, values(violation) as violation_types, dc(url) as unique_urls, latest(host) as adc by policy_name, _time
| where hits > 0
| sort - hits
| table _time, adc, policy_name, violation_types, unique_urls, hits
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Stacked column chart of violations by type over time, treemap of policies, drilldown to sample URLs (sanitized).

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
- [Citrix ADC — Web App Firewall](https://docs.citrix.com/en-us/citrix-adc/current-release/application-firewall.html)
