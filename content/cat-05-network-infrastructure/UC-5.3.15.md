---
id: "5.3.15"
title: "Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.15 · Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)

## Description

SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.

## Value

SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.

## Implementation

Create a scripted input that polls the NITRO API `sslcertkey` resource on each ADC. The API returns `certkey` name, `subject`, `issuer`, `serial`, `clientcertnotbefore`, `clientcertnotafter`, `daystoexpiration`, and `expirymonitor` status. Also enable the built-in `expirymonitor` on the ADC with a `notificationperiod` (10–100 days). Run the scripted input daily. Alert at 90 days (plan renewal), 30 days (action required), 7 days (critical), and immediately when `daystoexpiration` reaches 0. Track all certificates bound to vServers — unbound certificates can be ignored or flagged for cleanup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling Citrix ADC NITRO API.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:ssl"` fields `certkey_name`, `days_to_expiry`, `subject`, `issuer`, `serial`, `bound_vserver`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that polls the NITRO API `sslcertkey` resource on each ADC. The API returns `certkey` name, `subject`, `issuer`, `serial`, `clientcertnotbefore`, `clientcertnotafter`, `daystoexpiration`, and `expirymonitor` status. Also enable the built-in `expirymonitor` on the ADC with a `notificationperiod` (10–100 days). Run the scripted input daily. Alert at 90 days (plan renewal), 30 days (action required), 7 days (critical), and immediately when `daystoexpiration` reaches 0. Track…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:ssl"
| stats latest(days_to_expiry) as days_left, latest(subject) as subject, latest(issuer) as issuer, values(bound_vserver) as bound_to by certkey_name, host
| where days_left < 90
| eval urgency=case(days_left<=7, "CRITICAL", days_left<=30, "HIGH", days_left<=90, "MEDIUM", 1=1, "LOW")
| sort days_left
| table certkey_name, days_left, urgency, subject, issuer, bound_to, host
```

Understanding this SPL

**Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)** — SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:ssl"` fields `certkey_name`, `days_to_expiry`, `subject`, `issuer`, `serial`, `bound_vserver`. **App/TA** (typical add-on context): Custom scripted input polling Citrix ADC NITRO API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:ssl. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:ssl". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by certkey_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where days_left < 90` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **urgency** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)**): table certkey_name, days_left, urgency, subject, issuer, bound_to, host

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Certificates.All_Certificates by All_Certificates.dest | sort - count
```

Understanding this CIM / accelerated SPL

**Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)** — SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:ssl"` fields `certkey_name`, `days_to_expiry`, `subject`, `issuer`, `serial`, `bound_vserver`. **App/TA** (typical add-on context): Custom scripted input polling Citrix ADC NITRO API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Certificates.All_Certificates` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (certificates sorted by expiry), Single value (certificates expiring within 30 days), Gauge (soonest expiry).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=network sourcetype="citrix:netscaler:ssl"
| stats latest(days_to_expiry) as days_left, latest(subject) as subject, latest(issuer) as issuer, values(bound_vserver) as bound_to by certkey_name, host
| where days_left < 90
| eval urgency=case(days_left<=7, "CRITICAL", days_left<=30, "HIGH", days_left<=90, "MEDIUM", 1=1, "LOW")
| sort days_left
| table certkey_name, days_left, urgency, subject, issuer, bound_to, host
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Certificates.All_Certificates by All_Certificates.dest | sort - count
```

## Visualization

Table (certificates sorted by expiry), Single value (certificates expiring within 30 days), Gauge (soonest expiry).

## References

- [CIM: Certificates](https://docs.splunk.com/Documentation/CIM/latest/User/Certificates)
