<!-- AUTO-GENERATED from UC-2.6.39.json — DO NOT EDIT -->

---
id: "2.6.39"
title: "USB and Peripheral Redirection Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.39 · USB and Peripheral Redirection Failures

## Description

USB, scanner, and smart card redirection, plus client drive mapping and clipboard, depend on VDA services, client versions, and Citrix/Windows policies. Failures are often per-device or per-user but can spike when a new policy, endpoint agent, or firmware change blocks channels. VDA and Application logs capture the denial reason, while optional uberAgent peripheral metrics confirm drop-off in hardware attach success rates.

## Value

USB, scanner, and smart card redirection, plus client drive mapping and clipboard, depend on VDA services, client versions, and Citrix/Windows policies. Failures are often per-device or per-user but can spike when a new policy, endpoint agent, or firmware change blocks channels. VDA and Application logs capture the denial reason, while optional uberAgent peripheral metrics confirm drop-off in hardware attach success rates.

## Implementation

Ingest a broad slice of VDA logs with USB/TWAIN categories enabled. Add policy lookup by AD group. Separate Help Desk false positives (unsupported devices) with `NOT match(device_class,"(legacy)")` style filters where fields exist. Correlate with NetScaler/ADC app flow only if the channel is not negotiated locally. Alert on new denial strings in a 24h compare.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), Splunk Add-on for Microsoft Windows, optional uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="citrix:vda:events"`, `sourcetype="WinEventLog:Application"`, optional `index=uberagent` peripheral data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable detailed VDA logging for HDX device redirection per Citrix doc for your LTSR/CR build. If logs are very verbose, route to a dedicated index with shorter retention. Map `user` and `ClientName` fields consistently.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; limit `index=uberagent` to your deployment):

```spl
(index=xd sourcetype="citrix:vda:events" OR (index=windows (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events")) OR (index=uberagent sourcetype="uberAgent:Peripheral*"))
| search match(_raw, "(?i)USB|TWAIN|WIA|redirect|peripheral|smart.?card|scard|clipboard|mapped drive|clpb|device.*(fail|deny|block|stop|stall)")
| eval channel=if(match(_raw, "(?i)twain|wia|scan"), "imaging", if(match(_raw, "(?i)clipboard|clip"), "clipboard", if(match(_raw, "(?i)drive|mapped"), "drives", "usb_usb")))
| where match(_raw, "(?i)fail|error|block|deny|policy|restric|not supported|time.?out|stall")
| stats count, values(Message) as sample, earliest(_time) as first_t, latest(_time) as last_t, dc(user) as users by host, channel, user
| sort - count
```

Step 3 — Validate
Unplug/attach a test USB in lab; confirm a failure path logs if you block via policy. Verify sampling does not include benign detach messages.

Step 4 — Operationalize
Share weekly Top 10 error strings with endpoint engineering. For regulated sites, add privacy guardrails to mask serial numbers in Message.

## SPL

```spl
(index=xd sourcetype="citrix:vda:events" OR (index=windows (sourcetype="WinEventLog:Application" OR sourcetype="citrix:vda:events")) OR (index=uberagent sourcetype="uberAgent:Peripheral*"))
| search match(_raw, "(?i)USB|TWAIN|WIA|redirect|peripheral|smart.?card|scard|clipboard|mapped drive|clpb|device.*(fail|deny|block|stop|stall)")
| eval channel=if(match(_raw, "(?i)twain|wia|scan"), "imaging", if(match(_raw, "(?i)clipboard|clip"), "clipboard", if(match(_raw, "(?i)drive|mapped"), "drives", "usb_usb")))
| where match(_raw, "(?i)fail|error|block|deny|policy|restric|not supported|time.?out|stall")
| stats count, values(Message) as sample, earliest(_time) as first_t, latest(_time) as last_t, dc(user) as users by host, channel, user
| sort - count
```

## Visualization

Table (users and channels with sample errors), Pareto chart (error text top 10), Bar chart (failed channel by delivery group if joined).

## References

- [HDX features - USB, TWAIN, drives](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-2112/hdx/hdx-features-2112.html)
