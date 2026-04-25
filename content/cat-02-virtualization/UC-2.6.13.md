<!-- AUTO-GENERATED from UC-2.6.13.json — DO NOT EDIT -->

---
id: "2.6.13"
title: "Citrix Federated Authentication Service (FAS) Certificate Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.13 · Citrix Federated Authentication Service (FAS) Certificate Health

## Description

Citrix FAS dynamically issues short-lived certificates that allow users to log on to VDA sessions as if they had a smart card — enabling passwordless SSO from StoreFront via SAML or other federated identity providers. If FAS cannot reach the Certificate Authority or certificate signing takes too long, user authentication fails entirely. FAS is a privileged component with access to private keys, making its security monitoring equally critical.

## Value

Citrix FAS dynamically issues short-lived certificates that allow users to log on to VDA sessions as if they had a smart card — enabling passwordless SSO from StoreFront via SAML or other federated identity providers. If FAS cannot reach the Certificate Authority or certificate signing takes too long, user authentication fails entirely. FAS is a privileged component with access to private keys, making its security monitoring equally critical.

## Implementation

Deploy a Splunk Universal Forwarder on FAS servers and collect the Citrix FAS application event log. FAS logs certificate issuance attempts, CA connectivity status, and certificate signing operations. Monitor for: certificate issuance failures (CA unreachable, template misconfigured), slow certificate signing (>2 seconds impacts logon), RA certificate expiration (FAS's own registration authority certificate), and unauthorized certificate requests. FAS PowerShell cmdlets (`Get-FasRaCertificateMonitor`, `Test-FasUserCertificateCrypto`) can be used via scripted inputs for proactive health checks. Alert immediately on any certificate issuance failure as it blocks user authentication.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder on FAS servers.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:fas:events"` fields `event_type`, `user`, `certificate_status`, `signing_time_ms`, `ca_server`, `error_message`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy a Splunk Universal Forwarder on FAS servers and collect the Citrix FAS application event log. FAS logs certificate issuance attempts, CA connectivity status, and certificate signing operations. Monitor for: certificate issuance failures (CA unreachable, template misconfigured), slow certificate signing (>2 seconds impacts logon), RA certificate expiration (FAS's own registration authority certificate), and unauthorized certificate requests. FAS PowerShell cmdlets (`Get-FasRaCertificateMon…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:fas:events"
| bin _time span=15m
| stats sum(eval(if(certificate_status="Issued", 1, 0))) as issued,
  sum(eval(if(certificate_status="Failed", 1, 0))) as failed,
  avg(signing_time_ms) as avg_sign_ms, max(signing_time_ms) as max_sign_ms by ca_server, _time
| eval fail_pct=if((issued+failed)>0, round(failed/(issued+failed)*100,1), 0)
| where failed > 0 OR avg_sign_ms > 2000
| table _time, ca_server, issued, failed, fail_pct, avg_sign_ms, max_sign_ms
```

Understanding this SPL

**Citrix Federated Authentication Service (FAS) Certificate Health** — Citrix FAS dynamically issues short-lived certificates that allow users to log on to VDA sessions as if they had a smart card — enabling passwordless SSO from StoreFront via SAML or other federated identity providers. If FAS cannot reach the Certificate Authority or certificate signing takes too long, user authentication fails entirely. FAS is a privileged component with access to private keys, making its security monitoring equally critical.

Documented **Data sources**: `index=xd` `sourcetype="citrix:fas:events"` fields `event_type`, `user`, `certificate_status`, `signing_time_ms`, `ca_server`, `error_message`. **App/TA** (typical add-on context): Splunk Universal Forwarder on FAS servers. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:fas:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:fas:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by ca_server, _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **fail_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where failed > 0 OR avg_sign_ms > 2000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Citrix Federated Authentication Service (FAS) Certificate Health**): table _time, ca_server, issued, failed, fail_pct, avg_sign_ms, max_sign_ms

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - count
```

Understanding this CIM / accelerated SPL

**Citrix Federated Authentication Service (FAS) Certificate Health** — Citrix FAS dynamically issues short-lived certificates that allow users to log on to VDA sessions as if they had a smart card — enabling passwordless SSO from StoreFront via SAML or other federated identity providers. If FAS cannot reach the Certificate Authority or certificate signing takes too long, user authentication fails entirely. FAS is a privileged component with access to private keys, making its security monitoring equally critical.

Documented **Data sources**: `index=xd` `sourcetype="citrix:fas:events"` fields `event_type`, `user`, `certificate_status`, `signing_time_ms`, `ca_server`, `error_message`. **App/TA** (typical add-on context): Splunk Universal Forwarder on FAS servers. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (certificate issuance success vs failure), Single value (current CA reachability), Table (failed certificate requests with error details).

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
index=xd sourcetype="citrix:fas:events"
| bin _time span=15m
| stats sum(eval(if(certificate_status="Issued", 1, 0))) as issued,
  sum(eval(if(certificate_status="Failed", 1, 0))) as failed,
  avg(signing_time_ms) as avg_sign_ms, max(signing_time_ms) as max_sign_ms by ca_server, _time
| eval fail_pct=if((issued+failed)>0, round(failed/(issued+failed)*100,1), 0)
| where failed > 0 OR avg_sign_ms > 2000
| table _time, ca_server, issued, failed, fail_pct, avg_sign_ms, max_sign_ms
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src span=15m | sort - count
```

## Visualization

Timechart (certificate issuance success vs failure), Single value (current CA reachability), Table (failed certificate requests with error details).

## References

- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
