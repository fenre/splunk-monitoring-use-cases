<!-- AUTO-GENERATED from UC-9.8.1.json — DO NOT EDIT -->

---
id: "9.8.1"
title: "BeyondTrust Privileged Session Recording and Playback Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.8.1 · BeyondTrust Privileged Session Recording and Playback Audit

## Description

Regulators and insurers increasingly expect replayable evidence for privileged access. Sessions without a recording artifact break the chain of custody for investigations and SOX-style ITGC reviews.

## Value

Ensures BeyondTrust deployments actually capture sessions that should be recorded and triggers rapid correction of misconfiguration or agent faults.

## Implementation

(1) Confirm recording IDs populate for all PRA session types in scope. (2) Allow-list break-glass jump boxes via lookup if policy permits no recording. (3) Alert SecOps on missing recordings within 15 minutes of session end. (4) Correlate with storage quotas on recording servers.

## SPL

```spl
index=pam sourcetype="beyondtrust:session" earliest=-7d
| eval rec=coalesce(recording_id, RecordingId, session_recording, "")
| eval user=coalesce(user, UserName, admin_user, "")
| eval target=coalesce(target_host, TargetHost, dest, "")
| eval outcome=coalesce(session_status, outcome, "")
| where isnull(rec) OR rec="" OR match(lower(outcome), "(?i)no.record|recording.failed|missing")
| stats count values(outcome) as status_samples by user target
| sort -count
```

## Visualization

Table (user, target, missing count), pie (sessions with vs without recording), timeline.

## References

- [BeyondTrust — Privileged Remote Access documentation](https://www.beyondtrust.com/privileged-remote-access)
- [Splunk Docs — stats](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Stats)
