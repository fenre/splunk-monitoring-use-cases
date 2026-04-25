<!-- AUTO-GENERATED from UC-6.1.39.json — DO NOT EDIT -->

---
id: "6.1.39"
title: "NetApp ONTAP SVM Administrative State Not Running"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.39 · NetApp ONTAP SVM Administrative State Not Running

## Description

A storage virtual machine that is stopped or mis-administered drops all hosted NFS, SMB, and SAN endpoints for its tenants—often during DR tests or automation mistakes.

## Value

Detects accidental `vserver stop` operations or failed migrations before helpdesk volume explodes with "share unavailable" tickets.

## Implementation

Ensure Hydra inventory jobs collect vserver objects. If field names differ between cluster-mode releases, add `FIELDALIAS` in `props.conf`. Exclude template SVMs used for cloning via a lookup. Page on any production-tagged SVM not `running` for more than one poll interval.

## SPL

```spl
index=ontap OR index=storage sourcetype="ontap:vserver"
| eval state=lower(coalesce(administrative_state, state, vserver_admin_state))
| eval svm=coalesce(vserver, vserver_name, name)
| where state!="running" AND isnotnull(svm)
| stats latest(state) as admin_state latest(type) as svm_type by cluster_name svm
| sort cluster_name svm
```

## Visualization

Table (cluster, SVM, state), map or icon panel by datacenter.

## References

- [Splunk Add-on for NetApp Data ONTAP (Splunkbase)](https://splunkbase.splunk.com/app/3418)
- [Splunk Docs — NetApp add-on sourcetypes](https://docs.splunk.com/Documentation/AddOns/released/NetApp/Sourcetypes)
