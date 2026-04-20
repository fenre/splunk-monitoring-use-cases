---
id: "9.4.5"
title: "Suspicious Session Commands"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.5 · Suspicious Session Commands

## Description

Detecting dangerous commands during privileged sessions enables real-time intervention before damage occurs.

## Value

Detecting dangerous commands during privileged sessions enables real-time intervention before damage occurs.

## Implementation

Enable PAM session recording and command logging. Parse keystroke transcripts. Alert immediately on high-risk commands (rm -rf, format, DROP DATABASE, etc.). Integrate with SOAR for automated session termination on critical detections.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: CyberArk PSM, BeyondTrust session monitoring.
• Ensure the following data sources are available: PAM session recordings/keystroke logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable PAM session recording and command logging. Parse keystroke transcripts. Alert immediately on high-risk commands (rm -rf, format, DROP DATABASE, etc.). Integrate with SOAR for automated session termination on critical detections.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=pam sourcetype="cyberark:psm_transcript"
| search command IN ("rm -rf","format","del /s","DROP DATABASE","shutdown","halt","init 0")
| table _time, user, target_host, command, session_id
```

Understanding this SPL

**Suspicious Session Commands** — Detecting dangerous commands during privileged sessions enables real-time intervention before damage occurs.

Documented **Data sources**: PAM session recordings/keystroke logs. **App/TA** (typical add-on context): CyberArk PSM, BeyondTrust session monitoring. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: pam; **sourcetype**: cyberark:psm_transcript. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=pam, sourcetype="cyberark:psm_transcript". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Suspicious Session Commands**): table _time, user, target_host, command, session_id


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious commands), Timeline (command events), Single value (high-risk commands today).

## SPL

```spl
index=pam sourcetype="cyberark:psm_transcript"
| search command IN ("rm -rf","format","del /s","DROP DATABASE","shutdown","halt","init 0")
| table _time, user, target_host, command, session_id
```

## Visualization

Table (suspicious commands), Timeline (command events), Single value (high-risk commands today).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
