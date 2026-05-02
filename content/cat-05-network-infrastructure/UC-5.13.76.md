<!-- AUTO-GENERATED from UC-5.13.76.json — DO NOT EDIT -->

---
id: "5.13.76"
title: "Catalyst Center Alert to Splunk On-Call/SOAR Routing"
status: "verified"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-5.13.76 · Catalyst Center Alert to Splunk On-Call/SOAR Routing

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Operations &middot; **Wave:** Run &middot; **Status:** Verified

*We connect the network monitoring alerts to automated response systems — so when a critical problem is detected, the system automatically investigates, creates a ticket, and pages the right person, instead of relying on someone to notice the alert and manually do all those steps. This cuts the response time from hours to minutes.*

---

## Description

Routes critical Catalyst Center alerts (P1/P2 issues and severity 1-2 events) to Splunk On-Call (VictorOps) or Splunk SOAR for automated incident creation and on-call escalation.

## Value

Manual alert triage introduces delay. Automated routing to On-Call/SOAR ensures critical network issues reach the right engineer within seconds.

## Implementation

Save the SPL as an alert with the following alert actions:

**For Splunk On-Call (VictorOps):**
1. Install the Splunk On-Call (VictorOps) app for Splunk
2. Configure the alert action to create an incident with:
   - Routing key: `network-ops`
   - Message type: `CRITICAL` for P1/severity-1, `WARNING` for P2/severity-2
   - Entity ID: `catalyst-center-$deviceName$`

**For Splunk SOAR:**
1. Configure the HEC connection from Splunk to SOAR
2. Set the alert to trigger a SOAR playbook that:
   - Creates a ServiceNow incident
   - Pages the network on-call team
   - Runs initial diagnostics (ping, show commands via Catalyst Center Command Runner API)

Schedule the alert to run every 5 minutes with a 5-minute window.

## Detailed Implementation

### Prerequisites
- Splunk SOAR (formerly Phantom) must be deployed and connected to this Splunk instance, OR Splunk On-Call (formerly VictorOps) must be configured for alert routing. This UC covers both platforms.
- The Catalyst Center alerting UCs must be operational: UC-5.13.3 (Unhealthy Device), UC-5.13.23 (P1/P2 Issues), UC-5.13.29 (Non-Compliance), UC-5.13.35 (Critical PSIRT). These are the alert sources that feed into SOAR/On-Call.
- For SOAR playbooks: network connectivity from SOAR to Catalyst Center API (HTTPS 443) for automated investigation and remediation actions.
- For On-Call: PagerDuty or Splunk On-Call routing policies configured with escalation tiers for network operations.

### Step 1 — Configure alert-to-SOAR pipeline
Each Catalyst Center alerting UC generates Splunk alerts. Configure these alerts to trigger SOAR playbooks or On-Call pages:

**Option A — Splunk SOAR integration:**
In each alerting UC's alert actions, add "Run Playbook" with the corresponding playbook name:
| Alert UC | SOAR Playbook | Trigger |
|----------|--------------|---------|
| UC-5.13.3 (Unhealthy Device) | `catalyst_device_triage` | `health_score < 50` |
| UC-5.13.6 (Unreachable Device) | `catalyst_unreachable_triage` | `reachability = Unreachable` |
| UC-5.13.23 (P1/P2 Issue) | `catalyst_p1_response` | `priority IN (P1, P2)` |
| UC-5.13.29 (Non-Compliance) | `catalyst_compliance_remediate` | `complianceStatus = NON_COMPLIANT` |
| UC-5.13.35 (Critical PSIRT) | `catalyst_psirt_response` | `severity = CRITICAL` |
| UC-5.13.61 (Rogue AP) | `catalyst_rogue_containment` | `category = Security AND name = *rogue*` |

**Option B — Splunk On-Call / PagerDuty:**
In each alerting UC's alert actions, add "Send to PagerDuty" with routing based on severity:
| Severity | Routing | Urgency |
|----------|---------|---------|
| Critical (P1, unreachable, CRITICAL PSIRT) | Network Operations Lead | High |
| High (P2, non-compliance, rogue AP) | On-call Engineer | Low |
| Medium (health < 50, issue trending) | Slack notification only | N/A |

### Step 2 — Build SOAR playbooks
Playbook 1: `catalyst_unreachable_triage` (UC-5.13.6 trigger)
```
1. RECEIVE alert (deviceName, managementIpAddress, siteId)
2. PING device from SOAR (verify Splunk isn't the only one seeing the issue)
   ├── If PING succeeds → CLOSE as transient; add note
   └── If PING fails → CONTINUE
3. CHECK interface status on upstream device via Catalyst Center API
   GET /dna/intent/api/v1/interface?deviceId={upstream_device_id}
4. CHECK recent changes in audit log
   SPL: index=catalyst sourcetype="cisco:dnac:audit:logs"
        auditDescription="*{deviceName}*" earliest=-4h
5. CREATE ServiceNow incident (priority based on device role)
6. NOTIFY on-call engineer
7. UPDATE Splunk notable event with triage results
```

Playbook 2: `catalyst_psirt_response` (UC-5.13.35 trigger)
```
1. RECEIVE alert (advisoryId, severity, cveId, affected_devices)
2. LOOKUP advisory details from Cisco PSIRT API
3. ENUMERATE affected devices from UC-5.13.37
4. CHECK SWIM compliance for affected devices
5. CREATE change request for firmware upgrade
6. NOTIFY security team with advisory summary
7. SCHEDULE follow-up check in 7 days
```

Playbook 3: `catalyst_rogue_containment` (UC-5.13.61 trigger)
```
1. RECEIVE alert (deviceName, siteId, alert type, rogue MAC)
2. CORRELATE with ISE for known/unknown device check
3. LOCATE AP using Catalyst Center floor map API
4. DECISION: containment
   ├── Sensitive area → AUTO-CONTAIN + ALERT SecOps
   └── Common area → ALERT SecOps for manual decision
5. CREATE security incident
6. LOG all actions for audit trail
```

### Step 3 — Validate
(a) Trigger each alert manually (temporarily lower thresholds) and verify the SOAR playbook or On-Call page fires correctly.
(b) For SOAR: verify the playbook executes each step successfully. Check SOAR's action history for the test run.
(c) For On-Call: verify the page reaches the correct on-call engineer within the expected timeframe.
(d) Test the Catalyst Center API connectivity from SOAR: the triage playbooks need to call `GET /dna/intent/api/v1/...` endpoints.
(e) Test the ServiceNow incident creation: verify the ticket is created with the correct category, priority, and assignment group.

### Step 4 — Operationalize
- SOAR dashboard: track playbook execution counts, success/failure rates, and average triage time.
- On-Call reports: track MTTA (mean time to acknowledge) and MTTR (mean time to resolve) per alert type.
- Monthly review: which playbooks fire most often? Are they reducing manual triage time?
- Quarterly: measure the MTTR improvement since SOAR deployment — this is the automation ROI.

Runbook (owner: Automation Engineering):
1. Monthly: review playbook execution statistics. Playbooks with > 50% failure rate need debugging.
2. Quarterly: identify manual triage steps that could be automated in existing playbooks.
3. Annually: assess whether new Catalyst Center UCs should have SOAR playbooks.

### Step 5 — Troubleshooting

- **Playbook doesn't trigger** — the alert action "Run Playbook" is not configured. Check the alert's actions in Settings → Alerts.

- **Playbook triggers but fails at Catalyst Center API call** — connectivity issue from SOAR to Catalyst Center. Check firewall rules (HTTPS 443) and API credentials configured in SOAR.

- **PagerDuty page goes to wrong engineer** — routing policy misconfigured. Check the escalation policy in PagerDuty/On-Call.

- **Too many pages** — alert throttling not configured. Set throttle by `deviceName` for 4 hours on each alerting UC.

- **SOAR can't create ServiceNow ticket** — ServiceNow integration credentials expired or the incident template is misconfigured. Check SOAR → Apps → ServiceNow.

- **Rogue containment playbook causes issues** — auto-containment sends deauth frames that can affect legitimate devices. Ensure the MAC-check step correctly identifies rogues vs neighbours. Test in a lab before enabling auto-containment in production.

- **Want to add Webex notification** — add a Webex Teams action step to any playbook. SOAR has a native Webex connector.

- **Playbook takes too long** — check each step's execution time. API calls to Catalyst Center should return in < 5 seconds. If > 30 seconds, check Catalyst Center API health.

## SPL

```spl
index=catalyst ((sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED") OR (sourcetype="cisco:dnac:event:notification" eventSeverity<=2)) | eval alert_source=case(sourcetype="cisco:dnac:issue","Assurance Issue: ".name, sourcetype="cisco:dnac:event:notification","Event: ".description, 1==1,"Unknown") | eval severity=case(priority="P1" OR eventSeverity=1,"critical", priority="P2" OR eventSeverity=2,"high", 1==1,"medium") | table _time alert_source severity deviceName siteId
```

## Visualization

Alert-driven: no primary chart; optional supporting table in a runbook dashboard showing last 20 routed events with dedup key on deviceName+issueId.

## Known False Positives

**Lab or test device P1/P2 issue routed to the production on-call team.** A lab device generating a P1/P2 issue or severity 1-2 event notification triggers the SOAR/on-call routing, paging the production team unnecessarily. Distinguish by checking whether `deviceName` matches a lab naming convention or is in a non-production `siteId`. Suppress by maintaining a `catalyst_excluded_devices` lookup and filtering lab devices from the routing logic.

**Planned maintenance P1/P2 issue triggering SOAR playbook.** A device reload during a maintenance window generates a P1/P2 issue that triggers the automated response. Distinguish by correlating with ITSM change records. Suppress by integrating the `catalyst_maintenance_windows` lookup into the SOAR routing logic — suppress routing when the alert falls within an approved maintenance window.

**Duplicate routing from both issue and event notification matching the same incident.** The SPL matches both `cisco:dnac:issue` and `cisco:dnac:event:notification` sources. A single network event may trigger two SOAR actions. Distinguish by checking whether the `deviceName` and timestamp match across both sourcetypes. Suppress by deduplicating: group by `deviceName` and use a 15-minute deduplication window.

**SOAR playbook failing on enrichment step due to missing Catalyst Center API access.** The SOAR playbook may attempt to query the Catalyst Center API for enrichment and fail if the SOAR platform does not have API credentials configured. Distinguish by checking SOAR playbook execution logs for API errors. This is not a false positive — fix the SOAR-to-Catalyst Center connectivity.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Issues API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!issues)
