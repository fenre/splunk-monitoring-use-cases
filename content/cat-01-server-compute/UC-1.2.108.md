---
id: "1.2.108"
title: "Kerberos Constrained Delegation Abuse"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.108 · Kerberos Constrained Delegation Abuse

## Description

Kerberos delegation allows services to impersonate users. Misconfigured or compromised delegation targets enable privilege escalation to domain admin.

## Value

Kerberos delegation allows services to impersonate users. Misconfigured or compromised delegation targets enable privilege escalation to domain admin.

## Implementation

Monitor TGS requests (4769) where TransitionedServices is populated (indicates S4U2Proxy delegation). Alert on delegation to sensitive services (krbtgt, LDAP, CIFS on DCs). Track AD object modifications (5136) that change msDS-AllowedToDelegateTo attribute — indicates delegation configuration changes. Detect resource-based constrained delegation attacks by monitoring msDS-AllowedToActOnBehalfOfOtherIdentity attribute changes. MITRE ATT&CK T1550.003.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4769, 5136).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor TGS requests (4769) where TransitionedServices is populated (indicates S4U2Proxy delegation). Alert on delegation to sensitive services (krbtgt, LDAP, CIFS on DCs). Track AD object modifications (5136) that change msDS-AllowedToDelegateTo attribute — indicates delegation configuration changes. Detect resource-based constrained delegation attacks by monitoring msDS-AllowedToActOnBehalfOfOtherIdentity attribute changes. MITRE ATT&CK T1550.003.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=4769 TransitionedServices!=""
| eval is_suspicious=if(match(ServiceName, "(?i)(krbtgt|ldap/)"), "High_Risk", "Normal")
| stats count by ServiceName, TargetUserName, IpAddress, TransitionedServices, is_suspicious
| where is_suspicious="High_Risk" OR count>50
| sort -count
```

Understanding this SPL

**Kerberos Constrained Delegation Abuse** — Kerberos delegation allows services to impersonate users. Misconfigured or compromised delegation targets enable privilege escalation to domain admin.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4769, 5136). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **is_suspicious** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by ServiceName, TargetUserName, IpAddress, TransitionedServices, is_suspicious** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where is_suspicious="High_Risk" OR count>50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Understanding this CIM / accelerated SPL

**Kerberos Constrained Delegation Abuse** — Kerberos delegation allows services to impersonate users. Misconfigured or compromised delegation targets enable privilege escalation to domain admin.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4769, 5136). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (delegation events), Alert on sensitive service delegation, Network diagram (delegation paths).

## SPL

```spl
index=wineventlog EventCode=4769 TransitionedServices!=""
| eval is_suspicious=if(match(ServiceName, "(?i)(krbtgt|ldap/)"), "High_Risk", "Normal")
| stats count by ServiceName, TargetUserName, IpAddress, TransitionedServices, is_suspicious
| where is_suspicious="High_Risk" OR count>50
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

## Visualization

Table (delegation events), Alert on sensitive service delegation, Network diagram (delegation paths).

## References

- [Track AD object modifications](https://splunkbase.splunk.com/app/5136)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
