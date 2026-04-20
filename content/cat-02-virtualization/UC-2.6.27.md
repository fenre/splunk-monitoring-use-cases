---
id: "2.6.27"
title: "Endpoint Security Analytics (ESA) Threat Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-2.6.27 · Endpoint Security Analytics (ESA) Threat Detection

## Description

uberAgent ESA provides endpoint-level threat detection within Citrix sessions using Sigma rules, LOLBAS detection, process tampering monitoring, and file system activity analysis. In multi-user CVAD environments, a compromised session can laterally move to shared resources. ESA detects threats inside the session that network-based security tools cannot see.

## Value

uberAgent ESA provides endpoint-level threat detection within Citrix sessions using Sigma rules, LOLBAS detection, process tampering monitoring, and file system activity analysis. In multi-user CVAD environments, a compromised session can laterally move to shared resources. ESA detects threats inside the session that network-based security tools cannot see.

## Implementation

Enable uberAgent ESA with default Sigma rule pack. Customise rules for Citrix-specific threats (e.g., lateral movement via published apps, credential dumping in shared sessions). Forward ESA events to Splunk Enterprise Security as notable events. The MITRE ATT&CK integration maps detections to tactics and techniques for SOC workflows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent ESA (included with uberAgent UXM, Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging"`, `sourcetype="uberAgent:Process:ProcessStartup"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable uberAgent ESA with default Sigma rule pack. Customise rules for Citrix-specific threats (e.g., lateral movement via published apps, credential dumping in shared sessions). Forward ESA events to Splunk Enterprise Security as notable events. The MITRE ATT&CK integration maps detections to tactics and techniques for SOC workflows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging" earliest=-24h
| stats count by RuleName, RuleSeverity, User, Host, ProcessName
| where RuleSeverity IN ("critical","high")
| sort -RuleSeverity, -count
| table Host, User, ProcessName, RuleName, RuleSeverity, count
```

Understanding this SPL

**Endpoint Security Analytics (ESA) Threat Detection** — uberAgent ESA provides endpoint-level threat detection within Citrix sessions using Sigma rules, LOLBAS detection, process tampering monitoring, and file system activity analysis. In multi-user CVAD environments, a compromised session can laterally move to shared resources. ESA detects threats inside the session that network-based security tools cannot see.

Documented **Data sources**: `sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging"`, `sourcetype="uberAgent:Process:ProcessStartup"`. **App/TA** (typical add-on context): uberAgent ESA (included with uberAgent UXM, Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgentESA:ActivityMonitoring:ProcessTagging. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by RuleName, RuleSeverity, User, Host, ProcessName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where RuleSeverity IN ("critical","high")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Endpoint Security Analytics (ESA) Threat Detection**): table Host, User, ProcessName, RuleName, RuleSeverity, count

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.dest | sort - count
```

Understanding this CIM / accelerated SPL

**Endpoint Security Analytics (ESA) Threat Detection** — uberAgent ESA provides endpoint-level threat detection within Citrix sessions using Sigma rules, LOLBAS detection, process tampering monitoring, and file system activity analysis. In multi-user CVAD environments, a compromised session can laterally move to shared resources. ESA detects threats inside the session that network-based security tools cannot see.

Documented **Data sources**: `sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging"`, `sourcetype="uberAgent:Process:ProcessStartup"`. **App/TA** (typical add-on context): uberAgent ESA (included with uberAgent UXM, Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (threat detections), Bar chart (by MITRE tactic), Timeline (detection events), Single value (critical alerts).

## SPL

```spl
index=uberagent sourcetype="uberAgentESA:ActivityMonitoring:ProcessTagging" earliest=-24h
| stats count by RuleName, RuleSeverity, User, Host, ProcessName
| where RuleSeverity IN ("critical","high")
| sort -RuleSeverity, -count
| table Host, User, ProcessName, RuleName, RuleSeverity, count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.dest | sort - count
```

## Visualization

Table (threat detections), Bar chart (by MITRE tactic), Timeline (detection events), Single value (critical alerts).

## References

- [Splunkbase app 1448](https://splunkbase.splunk.com/app/1448)
- [Splunk Enterprise Security](https://splunkbase.splunk.com/app/263)
- [CIM: Intrusion Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
