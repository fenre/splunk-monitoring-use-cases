<!-- AUTO-GENERATED from UC-2.6.35.json — DO NOT EDIT -->

---
id: "2.6.35"
title: "Pre-Launch and Lingering Session Management"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.35 · Pre-Launch and Lingering Session Management

## Description

Pre-launched and lingering sessions keep apps warm and retain user context, but they consume memory, session licenses, and power-managed capacity. Misconfigured idle timers, excessive pre-launch, or sessions stuck in disconnected state can exhaust pools and look like a capacity outage. Tuning visibility from broker and VDA events shows where session lifecycle policy diverges from design.

## Value

Pre-launched and lingering sessions keep apps warm and retain user context, but they consume memory, session licenses, and power-managed capacity. Misconfigured idle timers, excessive pre-launch, or sessions stuck in disconnected state can exhaust pools and look like a capacity outage. Tuning visibility from broker and VDA events shows where session lifecycle policy diverges from design.

## Implementation

Map published app and user fields. For ghost capacity, also pull uberAgent session or host CPU to correlate pre-launch with sustained resource use. Compare counts against GPO- or policy-driven idle and disconnect timers. Alert when pre-launch or linger counts exceed rolling baselines, or when idle sessions outnumber active sessions in a business hour window.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448), Template for Citrix XenDesktop 7 (TA-XD7-Broker).
• Ensure the following data sources are available: `sourcetype="citrix:broker:events"`, `sourcetype="citrix:vda:events"`, `index=uberagent` optional.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure session-related broker events are indexed with consistent `event_type` and user fields. If event names differ by version, centralize a macro with OR clauses. Ingest VDA `CtxSession` or equivalent event ids as needed for idle/linger details.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; extend `event_type` list to your build):

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)pre[\s-]*launch|lingering|ghost|idle|disc") OR event_type IN ("SessionDisconnect", "SessionInfo") OR match(event_type, "(?i)SessionPreLaunch"))
| eval session_type=if(match(_raw, "(?i)pre[\s-]*launch|prelaunch"), "prelaunch", if(match(_raw, "(?i)linger|disconnected|idle"), "idle_linger", "other"))
| where session_type!="other"
| bin _time span=1h
| stats count, dc(user) as users, values(session_id) as sample_sessions by _time, session_type, delivery_group, published_app
| table _time, session_type, delivery_group, published_app, count, users, sample_sessions
```

Step 3 — Validate
For a published app with known pre-launch, compare hourly counts. Spot-check a linger-heavy user against the Citrix session list.

Step 4 — Operationalize
Pair with the desktop policy team. Track improvements after GPO and Citrix policy changes.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)pre[\s-]*launch|lingering|ghost|idle|disc") OR event_type IN ("SessionDisconnect", "SessionInfo") OR match(event_type, "(?i)SessionPreLaunch"))
| eval session_type=if(match(_raw, "(?i)pre[\s-]*launch|prelaunch"), "prelaunch", if(match(_raw, "(?i)linger|disconnected|idle"), "idle_linger", "other"))
| where session_type!="other"
| bin _time span=1h
| stats count, dc(user) as users, values(session_id) as sample_sessions by _time, session_type, delivery_group, published_app
| table _time, session_type, delivery_group, published_app, count, users, sample_sessions
```

## Visualization

Area chart (prelaunch vs idle_linger by group), Table (top published apps with linger), Donut (session type mix).

## References

- [uberAgent UXM for Citrix](https://splunkbase.splunk.com/app/1448)
