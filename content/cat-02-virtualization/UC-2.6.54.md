<!-- AUTO-GENERATED from UC-2.6.54.json — DO NOT EDIT -->

---
id: "2.6.54"
title: "RDS Licensing Validation for Multi-Session Hosts"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.54 · RDS Licensing Validation for Multi-Session Hosts

## Description

Session hosts that offer multiple concurrent RDP and Citrix sessions need valid Remote Desktop Services client access licenses, healthy communication with the license server list, and clear visibility into per-device versus per-user mode and any grace period. A host in grace can appear healthy until a deadline passes and new sessions are refused. A broken license server list string — wrong DNS, firewall, or certificate — is a common misconfiguration. Collect license warnings from Application and the Remote Desktop service channels on each multi-session VDA, and aggregate the same on license servers. Pair with your Citrix per-user and Microsoft RDS-CAL entitlements in procurement, not in Splunk, but use Splunk to prove the runtime state matches policy.

## Value

Session hosts that offer multiple concurrent RDP and Citrix sessions need valid Remote Desktop Services client access licenses, healthy communication with the license server list, and clear visibility into per-device versus per-user mode and any grace period. A host in grace can appear healthy until a deadline passes and new sessions are refused. A broken license server list string — wrong DNS, firewall, or certificate — is a common misconfiguration. Collect license warnings from Application and the Remote Desktop service channels on each multi-session VDA, and aggregate the same on license servers. Pair with your Citrix per-user and Microsoft RDS-CAL entitlements in procurement, not in Splunk, but use Splunk to prove the runtime state matches policy.

## Implementation

Enable verbose Remote Desktop license logging in Windows where supported. Add a small scripted input to dump `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\RCM\Licensing` or PowerShell `Get-RDLicense` output daily on license servers. Alert on any `grace` or `0-day` grace start, any event that says license server is unreachable, and any 4105 with severity error. Deduplicate license servers. Document which Citrix and Microsoft agreements cover which host pools. Tune out duplicate Windows noise per build.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Windows add-on; reachability from forwarders to license servers; UDP/TCP 135 and RPC ranges documented.
• Ensure the following data sources are available: Application and RDS-specific event logs; optional dedicated license server in `index=windows` with its own `host` value.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Build a `lookup` of expected license server FQDNs per site. Ingest the license server farm first — it is the source of truth for issuance errors. Ingest all multi-session session hosts. Merge Citrix and Microsoft terms of use in a runbook; Splunk is evidence, not a license calculator.

Step 2 — Create the search and alert
Harden `EventCode` lists per your Windows build. A parallel search for unreachability:

```spl
index=windows "Remote Desktop License Servers" OR "The Remote Desktop license server is not available"
| table _time, host, EventCode, Message
```

**RDS Licensing Validation for Multi-Session Hosts** — Require two matching events in 15 minutes before a page, to reduce one-off flaps. Join `host` to a lookup that classifies the machine as `multi_session=true` to avoid false positives on single-session VDI where RDS CAL rules differ.

Step 3 — Validate
Stop the license service in a lab (not production) briefly and assert Splunk shows the follow-on events. Reconcile Event IDs to Microsoft’s table for your build.

Step 4 — Operationalize
Attach dashboards to the Windows license operations team, not only Citrix, because CAL issues are shared. Revisit when migrating license servers to new hardware or DNS aliases.

## SPL

```spl
index=windows (sourcetype="WinEventLog:Application" OR sourcetype="WinEventLog:RemoteDesktopServices*" OR source="*TerminalServices*")
| where EventCode IN (22, 23, 25, 28, 38, 4105) OR like(lower(_raw),"%license%") OR like(lower(_raw),"%grace%") OR like(lower(_raw),"%remote desktop%") OR like(lower(_raw),"%rd licen%")
| eval kind=if(like(lower(_raw),"%grace%"),"grace", if(like(lower(_raw),"%expir%"),"expiry","license_event"))
| eval server=coalesce(license_server, LicenseServer, host)
| bin _time span=1d
| stats count as daily_events, values(EventCode) as codes, values(kind) as kinds by server, _time
| where daily_events>0
| sort - daily_events
| table _time, server, daily_events, codes, kinds
```

## Visualization

Table of last license error per host, timechart of daily_events by server, single value of hosts in grace, network diagram optional with manual overlay.

## References

- [Remote Desktop Services and licensing (Microsoft Learn)](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/remote-desktop-services-terms)
- [Citrix — supported operating systems and RDS context](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/system-requirements.html)
