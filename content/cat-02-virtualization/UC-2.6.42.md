<!-- AUTO-GENERATED from UC-2.6.42.json — DO NOT EDIT -->

---
id: "2.6.42"
title: "Citrix Configuration Change Audit Trail"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.42 · Citrix Configuration Change Audit Trail

## Description

Unplanned or unauthorized changes to published resources, machine catalogs, entitlements, and policies are high-impact in VDI. Collecting a tamper-resistant trail from Windows process creation and Citrix admin audit events, plus any broker-side configuration events you expose, gives security and change teams evidence for investigations and attestation, not only for ITIL tickets.

## Value

Unplanned or unauthorized changes to published resources, machine catalogs, entitlements, and policies are high-impact in VDI. Collecting a tamper-resistant trail from Windows process creation and Citrix admin audit events, plus any broker-side configuration events you expose, gives security and change teams evidence for investigations and attestation, not only for ITIL tickets.

## Implementation

Send Security logs from admin jump hosts and all Delivery Controllers. Enable command-line process auditing (4688) per Microsoft guidance. Harden: lock down who can run `BrokerPowerShell`. Enrich with asset identity for admin accounts. For Citrix DaaS, pipe Cloud Director API audit to Splunk. Retention: align to your compliance schedule (e.g. 1 year online).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows, Template for Citrix XenDesktop 7 (TA-XD7-Broker), optional Splunk Enterprise Security.
• Ensure the following data sources are available: `sourcetype="WinEventLog:Security"` for admin hosts and controllers, `sourcetype="citrix:broker:events"` for broker audit.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable 4688 with command line collection on all admin entry points. Ingest `citrix:broker:events` with admin/audit subtypes. Create a `privileged_admins.csv` to separate service accounts. For Cloud, export Director or logging API to HEC with signing metadata if required by policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; field names for Security 4688 may vary with TA version):

```spl
index=windows sourcetype="WinEventLog:Security" (EventCode=4688 OR EventCode=4702)
| search match(_raw, "(?i)BrokerPowerShell|CVAD|XD.*Catalog|XenDesktop|Studio|Publish|Delivery.?Group|Machine.?Catalog|GPO|Broker\\bin|Get-Broker|Set-Broker|New-Broker|Remove-Broker")
| eval account=coalesce(Security_ID, user, src_user, Account_Name)
| eval process=New_Process_Name
| table _time, host, account, process, EventCode, CommandLine
| append [search index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)admin|audit|publish|unpublish|add.?desktop|change.?entitlement|polic|Studio")]
| sort - _time
```

Step 3 — Validate
Run a test change in lower environment; verify both the PowerShell and broker legs appear. Tune regex to include `Web Studio` browser paths if your team uses the web UI.

Step 4 — Operationalize
Send daily digest to the SOC for unusual off-hours `Remove-Broker` or mass publish events. Add Correlation Searches in ES if available. Map to your change tool via ticket number in a shared lookup where operators paste the incident id into the work notes field.

## SPL

```spl
index=windows sourcetype="WinEventLog:Security" (EventCode=4688 OR EventCode=4702)
| search match(_raw, "(?i)BrokerPowerShell|CVAD|XD.*Catalog|XenDesktop|Studio|Publish|Delivery.?Group|Machine.?Catalog|GPO|Broker\\bin|Get-Broker|Set-Broker|New-Broker|Remove-Broker")
| eval account=coalesce(Security_ID, user, src_user, Account_Name)
| eval process=New_Process_Name
| table _time, host, account, process, EventCode, CommandLine
| append [search index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)admin|audit|publish|unpublish|add.?desktop|change.?entitlement|polic|Studio")]
| sort - _time
```

## Visualization

Timeline (change events by admin), Table (raw command line), Bar chart (changes per day by team via lookup).

## References

- [Citrix audit logging and reporting](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/operations/audit/audit-logging.html)
