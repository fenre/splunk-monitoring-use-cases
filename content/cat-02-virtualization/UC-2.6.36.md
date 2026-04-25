<!-- AUTO-GENERATED from UC-2.6.36.json — DO NOT EDIT -->

---
id: "2.6.36"
title: "Session Reliability and Auto Client Reconnect"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.36 · Session Reliability and Auto Client Reconnect

## Description

Session Reliability and Auto Client Reconnect mask brief network blips, but a rising ratio of full disconnects to successful reconnects indicates unstable paths, bad Wi-Fi, or gateway issues. VDA and broker events that mention WCF, keep-alives, reliability channels, and EDT/TCP flips, correlated with network-side syslogs, separate client-side noise from data-center incidents.

## Value

Session Reliability and Auto Client Reconnect mask brief network blips, but a rising ratio of full disconnects to successful reconnects indicates unstable paths, bad Wi-Fi, or gateway issues. VDA and broker events that mention WCF, keep-alives, reliability channels, and EDT/TCP flips, correlated with network-side syslogs, separate client-side noise from data-center incidents.

## Implementation

Normalize VDA and broker time zones. For Citrix Cloud or hybrid, ensure universal forwarders label site id. Add optional `append` to NetScaler `citrix:netscaler:syslog` for the same time window. Compute reconnect success ratio: `reconnect` counts vs `disrupt` counts per 5m per delivery group, alert when disrupt exceeds baseline by 2x for 3 intervals.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), optional NetScaler syslog TA, uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="citrix:vda:events"`, `sourcetype="citrix:broker:events"`, optional `sourcetype="citrix:netscaler:syslog"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Index VDA and broker together or use event breaking that preserves each line. If Message text varies by VDA build, add a `macros.conf` for flexible regex. Forward gateway logs into the same search head with `site` or `location` context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; test regex against sample _raw data):

```spl
index=xd (sourcetype="citrix:vda:events" OR sourcetype="citrix:broker:events") match(_raw, "(?i)session reliability|reconnect|WCF|keep.?alive|auto.?client|ACR|ICA.*reset|edt|tcp.*(drop|reset)|udp")
| eval evt=if(match(_raw, "(?i)reconnect|re.?establish|re.?connected|back online"), "reconnect", if(match(_raw, "(?i)disconnect|drop|reset|fail|unreachable"), "disrupt", "other"))
| where evt!="other"
| eval user=coalesce(user, UserName, ClientName)
| bin _time span=5m
| stats count, dc(user) as users by _time, evt, host, delivery_group
| sort -_time, count
```

Step 3 — Validate
Induce a short network flap on a test client and assert disrupt/reconnect events appear. Compare with Help Desk ticket volume.

Step 4 — Operationalize
Route alerts to the network and EUC teams with delivery group context. Add weekly trends to executive readouts for remote-work quality.

## SPL

```spl
index=xd (sourcetype="citrix:vda:events" OR sourcetype="citrix:broker:events") match(_raw, "(?i)session reliability|reconnect|WCF|keep.?alive|auto.?client|ACR|ICA.*reset|edt|tcp.*(drop|reset)|udp")
| eval evt=if(match(_raw, "(?i)reconnect|re.?establish|re.?connected|back online"), "reconnect", if(match(_raw, "(?i)disconnect|drop|reset|fail|unreachable"), "disrupt", "other"))
| where evt!="other"
| eval user=coalesce(user, UserName, ClientName)
| bin _time span=5m
| stats count, dc(user) as users by _time, evt, host, delivery_group
| sort -_time, count
```

## Visualization

Multi-series line (disrupt vs reconnect), Timeline (outages), Map or table of affected delivery groups per site.

## References

- [Session Reliability in CVAD / HDX](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/hdx/session-reliability.html)
