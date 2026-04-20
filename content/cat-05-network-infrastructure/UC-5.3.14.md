---
id: "5.3.14"
title: "Citrix ADC Service Group Member Health (NetScaler)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.14 · Citrix ADC Service Group Member Health (NetScaler)

## Description

Behind each Citrix ADC vServer, service group members represent individual back-end servers. When health monitors detect a service group member as DOWN, the ADC stops sending traffic to that server. A single member going down may be routine (maintenance), but multiple simultaneous failures indicate a systemic issue — network partition, shared dependency failure, or deployment problem. Monitoring service group member health identifies back-end server failures faster than application-level monitoring.

## Value

Behind each Citrix ADC vServer, service group members represent individual back-end servers. When health monitors detect a service group member as DOWN, the ADC stops sending traffic to that server. A single member going down may be routine (maintenance), but multiple simultaneous failures indicate a systemic issue — network partition, shared dependency failure, or deployment problem. Monitoring service group member health identifies back-end server failures faster than application-level monitoring.

## Implementation

The ADC logs service state transitions via syslog. For richer data, poll the NITRO API `servicegroup_servicegroupmember_binding` to enumerate all members and their states. Track `svrstate` (UP, DOWN, OUT OF SERVICE) and monitor response times. Alert when: more than 2 service group members go DOWN simultaneously (systemic issue), a critical service group drops below minimum capacity threshold, or a member remains DOWN for more than 15 minutes (stale failure). Correlate member health with application error rates for impact assessment.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`).
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `service_name`, `service_ip`, `service_port`, `service_state`, `monitor_name`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The ADC logs service state transitions via syslog. For richer data, poll the NITRO API `servicegroup_servicegroupmember_binding` to enumerate all members and their states. Track `svrstate` (UP, DOWN, OUT OF SERVICE) and monitor response times. Alert when: more than 2 service group members go DOWN simultaneously (systemic issue), a critical service group drops below minimum capacity threshold, or a member remains DOWN for more than 15 minutes (stale failure). Correlate member health with applicat…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:syslog" "monitor" ("DOWN" OR "UP") "servicegroup"
| rex "servicegroup member (?<sg_name>\S+)\((?<member_ip>[^)]+)\) - State (?<state>\w+)"
| where state="DOWN"
| stats count as transitions, latest(_time) as last_seen, latest(state) as current_state by sg_name, member_ip, host
| eval last_seen_fmt=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| sort -last_seen
| table sg_name, member_ip, current_state, transitions, last_seen_fmt, host
```

Understanding this SPL

**Citrix ADC Service Group Member Health (NetScaler)** — Behind each Citrix ADC vServer, service group members represent individual back-end servers. When health monitors detect a service group member as DOWN, the ADC stops sending traffic to that server. A single member going down may be routine (maintenance), but multiple simultaneous failures indicate a systemic issue — network partition, shared dependency failure, or deployment problem. Monitoring service group member health identifies back-end server failures faster than…

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:syslog"` fields `service_name`, `service_ip`, `service_port`, `service_state`, `monitor_name`. **App/TA** (typical add-on context): Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where state="DOWN"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by sg_name, member_ip, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **last_seen_fmt** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix ADC Service Group Member Health (NetScaler)**): table sg_name, member_ip, current_state, transitions, last_seen_fmt, host


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (service groups with DOWN members), Bar chart (DOWN members by service group), Timeline (member state changes).

## SPL

```spl
index=network sourcetype="citrix:netscaler:syslog" "monitor" ("DOWN" OR "UP") "servicegroup"
| rex "servicegroup member (?<sg_name>\S+)\((?<member_ip>[^)]+)\) - State (?<state>\w+)"
| where state="DOWN"
| stats count as transitions, latest(_time) as last_seen, latest(state) as current_state by sg_name, member_ip, host
| eval last_seen_fmt=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| sort -last_seen
| table sg_name, member_ip, current_state, transitions, last_seen_fmt, host
```

## Visualization

Table (service groups with DOWN members), Bar chart (DOWN members by service group), Timeline (member state changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
