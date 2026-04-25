<!-- AUTO-GENERATED from UC-1.1.54.json — DO NOT EDIT -->

---
id: "1.1.54"
title: "Network Namespace Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.54 · Network Namespace Monitoring

## Description

Counts how many distinct network namespace names appear per host in the collection window; unusually high counts can mean container sprawl or unexpected new namespaces worth reviewing.

## Value

Unexpected growth in namespaces often lines up with orchestration drift, manual experiments, or activity you want your security or platform team to confirm, before isolation assumptions break.

## Implementation

Run a periodic script that lists netns names (or IDs) and ships one row per namespace. Adjust the `where count > 10` threshold to your container density; very dense worker nodes may need per–node group baselines instead of a global number.

## Detailed Implementation

Prerequisites
• Install `Splunk_TA_nix` and a script with permission to read `/var/run/netns` or run `ip netns list` under **sudo** via a secured forwarder.

Step 1 — Configure data collection
Emit `host`, `netns_name`, and optional creation metadata if you track it outside the default search.

Step 2 — Create the search and alert

```spl
index=os sourcetype=custom:netns host=*
| stats dc(netns_name) as netns_count by host
| where netns_count > 10
```

Prefer `dc()` if your script sends one event per namespace per poll; if you already aggregate, keep the original `stats count` pattern. Set the threshold per environment.

**Understanding this SPL** — Highlights hosts with more distinct namespaces than you expect for a steady-state profile.


Step 3 — Validate
On-box, run `ip netns` or `ls /var/run/netns` and compare counts to the latest forwarder event; check orchestration layer for expected churn.

Step 4 — Operationalize
Integrate with change records and container inventory; route unexpected growth to security for review on sensitive segments.



## SPL

```spl
index=os sourcetype=custom:netns host=*
| stats dc(netns_name) as netns_count by host
| where netns_count > 10
```

## Visualization

Table, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
