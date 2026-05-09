<!-- AUTO-GENERATED from UC-5.4.40.json — DO NOT EDIT -->

---
id: "5.4.40"
title: "Cisco C9800 RF Performance and Channel Assignment"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.40 · Cisco C9800 RF Performance and Channel Assignment

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Community

*We watch how often the office Wi-Fi gear automatically switches the radio channel it is using to avoid interference. A little switching is healthy; lots of switching means it is fighting with something — another network, a microwave, a faulty radio — and users will complain about laggy video calls.*

---

## Description

Tracks the Radio Resource Management (RRM) channel-change decisions emitted by Cisco Catalyst 9800 controllers. Counts how many times each AP radio (per slot) has rolled to a new 2.4 GHz / 5 GHz / 6 GHz channel and surfaces APs that have flapped more than three times in the search window — the threshold that typically distinguishes legitimate RRM optimisation from co-channel interference or a misbehaving neighbour.

## Value

RRM is a black-box optimisation engine — it picks channels and transmit power without the wireless team's involvement. Most of the time that is fine; sometimes RRM gets stuck in a feedback loop where two APs keep stealing each other's channel, both clients drop, both APs back off, and both APs flap channels again. Without monitoring you discover this after the third help-desk ticket reports laggy video calls in a particular conference room. With the channel-change rate visible in Splunk, the wireless team can spot the pathology in the first hour and either nail the channel down manually or investigate the rogue source (microwave oven, non-Wi-Fi 5 GHz radar, neighbouring tenant's AP).

## Implementation

Enable RRM and DOT11 syslog messages on the C9800 controller. Forward to Splunk via `TA-cisco_ios`. Alert on excessive channel changes (count > 3 within 1 hour) per AP-slot — this is a stronger signal than absolute rate because it adapts to fleet size. For 6 GHz deployments, also correlate channel changes with `AFC-6-CHANNEL_DENIED` events.

## SPL

```spl
index=network sourcetype="cisco:ios" host="c9800*" "%RRM-6-CHANNEL_CHANGE"
| rex "AP (?<ap_name>\S+).*slot (?<slot>\d+).*channel (?<old_channel>\d+) to (?<new_channel>\d+)"
| stats count by ap_name, slot, old_channel, new_channel
| where count > 3
| sort - count
```

## Visualization

Table (top channel-changing APs, sorted by count), Bar chart (channel changes per hour, faceted by AP), Heatmap (AP floor-plan with channel utilisation; requires Catalyst Center geolocation data).

## Known False Positives

**Newly deployed APs settling.** A freshly installed AP performs an initial RF scan and may channel-change three or four times in the first hour. Suppress alerts for AP names that have been in the inventory for less than 24 hours.

**Adjacent-channel scheduled non-Wi-Fi sources.** Microwave ovens and radar systems run on schedules; the AP next to a cafeteria microwave will flap channels every time someone heats lunch. Document these AP-name patterns and correlate with the time of day.

**6 GHz client onboarding waves.** Wi-Fi 6E client deployment surges can cause RRM to redistribute channels as new 6 GHz radios start populating PSC channels. Use a 30-day rolling baseline rather than absolute thresholds during a deployment ramp.

## References

- [Cisco RRM (Radio Resource Management) best-practices white paper](https://www.cisco.com/c/en/us/td/docs/wireless/controller/technotes/8-6/b_RRM_White_Paper.html)
- [Catalyst 9800 RRM tuning](https://www.cisco.com/c/en/us/support/docs/wireless/catalyst-9800-series-wireless-controllers/216330-rrm-on-catalyst-9800.html)
