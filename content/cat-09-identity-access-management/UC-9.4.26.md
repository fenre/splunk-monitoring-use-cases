<!-- AUTO-GENERATED from UC-9.4.26.json — DO NOT EDIT -->

---
id: "9.4.26"
title: "BeyondTrust Privileged Command Channel High-Risk Keywords"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.4.26 · BeyondTrust Privileged Command Channel High-Risk Keywords

## Description

Command-line patterns associated with credential dumping, shadow copy destruction, or destructive disk operations during a BeyondTrust session warrant immediate response.

## Value

Compresses hours of session video review into a narrow Splunk alert aligned with common ransomware and lateral movement TTPs.

## Implementation

Maintain a lookup of regex patterns approved by your IR team instead of hard-coding in SPL long term. Ensure command logging complies with privacy and works council agreements. Integrate with SOAR to terminate sessions automatically only after legal review.

## Detailed Implementation

Prerequisites
• Install and configure: BeyondTrust PAM telemetry with Splunk parsing (org TA).
• Data sources: `sourcetype=beyondtrust:command` keystroke or command transcripts.

Step 1 — Configure data collection
Maintain a lookup of regex patterns approved by your IR team instead of hard-coding in SPL long term. Ensure command logging complies with privacy and works council agreements. Integrate with SOAR to terminate sessions automatically only after legal review.

Step 2 — Create the search and alert

```spl
index=pam sourcetype="beyondtrust:command" earliest=-4h
| eval cmd=coalesce(command, Command, CommandLine, _raw)
| where match(lower(cmd), "(?i)net user|invoke-mimikatz|sekurlsa|vssadmin.*delete shadows|bcdedit.*recoveryenabled no|format\s|diskpart")
| eval user=coalesce(user, UserName, "")
| eval target=coalesce(target_host, TargetHost, dest, "")
| stats count values(cmd) as commands by user, target
| sort -count
```

Step 3 — Validate
Compare with BeyondTrust session replay or command detail in the PAM console for the same user, target, and session time range.

Step 4 — Operationalize
Add to a dashboard or alert; document the owner. Table (user × target × commands), timeline, single value (distinct sessions).

## SPL

```spl
index=pam sourcetype="beyondtrust:command" earliest=-4h
| eval cmd=coalesce(command, Command, CommandLine, _raw)
| where match(lower(cmd), "(?i)net user|invoke-mimikatz|sekurlsa|vssadmin.*delete shadows|bcdedit.*recoveryenabled no|format\s|diskpart")
| eval user=coalesce(user, UserName, "")
| eval target=coalesce(target_host, TargetHost, dest, "")
| stats count values(cmd) as commands by user, target
| sort -count
```

## Visualization

Table (user × target × commands), timeline, single value (distinct sessions).

## References

- [BeyondTrust Password Safe / Cloud Dashboard for Splunk](https://splunkbase.splunk.com/app/5574)
- [MITRE ATT&CK — Impact / Credential Access](https://attack.mitre.org/)
