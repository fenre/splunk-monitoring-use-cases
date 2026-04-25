<!-- AUTO-GENERATED from UC-1.1.88.json — DO NOT EDIT -->

---
id: "1.1.88"
title: "Container Escape Attempt Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.1.88 · Container Escape Attempt Detection

## Description

Counts combined **AppArmor**/**SELinux** style denials whose text also references a **container** id or the word **container**, and pages when a **host**+**container** pair crosses a small floor.

## Value

These log lines are rare in healthy microservice estates; even a handful can be the first hint of a breakout tool hitting **policy** before it succeeds.

## Implementation

If `container_id` is not extracted, start with `by host` only and add **REX** for **k8s** **namespace**/**pod** once you standardize logging. Raise `>5` in **dev** clusters that are always noisy.

## Detailed Implementation

Prerequisites
• **Runtime** logs ( **containerd** / **cri-o** ) may be a better primary in some orgs—pair this UC with those sourcetypes in a **join** during triage.

**CIM** — **N/A** for the **syslog** keyword pass; use **Authentication**/**Change** only after you model **container** policy into CIM.


Step 3 — Validate
`crictl inspect` / **docker** **inspect** for the **id**; **dmesg** **seccomp** lines on the node the same minute.

Step 4 — Operationalize
Page both **platform** and **product** security when a **container** image name in the log matches a customer **tenant**.



## SPL

```spl
index=os sourcetype=syslog ("AppArmor" OR "SELinux") "container" ("denied" OR "DENIED")
| stats count by host, container_id
| where count>5
```

## Visualization

Alert, Table

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
