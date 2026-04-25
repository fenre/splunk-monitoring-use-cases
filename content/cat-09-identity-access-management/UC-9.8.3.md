<!-- AUTO-GENERATED from UC-9.8.3.json — DO NOT EDIT -->

---
id: "9.8.3"
title: "BeyondTrust Jump Client Offline Status and Connectivity Loss"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-9.8.3 · BeyondTrust Jump Client Offline Status and Connectivity Loss

## Description

Jump Clients extend PRA into segmented networks; when they go dark, support and incident responders lose path diversity. Clustered offline signals may indicate maintenance—or targeted disruption.

## Value

Improves operational resilience of remote access and helps distinguish planned outages from potential security events affecting OT or DMZ enclaves.

## Implementation

(1) Classify Jump Clients by criticality in a lookup. (2) Correlate with network change windows. (3) Alert when more than N clients in a site drop within minutes. (4) Integrate with NMS ICMP where available. (5) Track MTTR for reconnect.

## SPL

```spl
index=pam sourcetype="beyondtrust:audit" earliest=-24h
| eval jc=coalesce(jump_client, JumpClient, client_name, host, "")
| eval msg=coalesce(message, Message, event, Event, _raw)
| where match(lower(msg), "(?i)offline|unreachable|disconnect|tunnel.*down|heartbeat.*miss|agent.*stop")
| eval site=coalesce(site_name, Site, location, "")
| stats latest(_time) as last_event count by jc site
| eval mins_ago=round((now()-last_event)/60,1)
| sort -count
```

## Visualization

Map or site-based status panel, table (Jump Client, last event age), single-value (offline count).

## References

- [BeyondTrust — Jump Technology overview](https://www.beyondtrust.com/resources/videos/jump-technology-overview)
- [Splunk Lantern](https://lantern.splunk.com/)
