<!-- AUTO-GENERATED from UC-5.13.41.json — DO NOT EDIT -->

---
id: "5.13.41"
title: "Client Distribution by Type (Wired/Wireless/Guest)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.41 · Client Distribution by Type (Wired/Wireless/Guest)

## Description

Breaks down the client population by connection type (wired, wireless 2.4GHz, wireless 5GHz, wireless 6GHz) and SSID for capacity planning.

## Value

Knowing how clients distribute across SSIDs and connection types helps identify overloaded access points and plan wireless capacity.

## Implementation

Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `location`, `healthScore`.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538) with the **client** input writing sourcetype `cisco:dnac:client` to `index=catalyst`.
• The TA typically calls the Catalyst **client-detail** style Intent API; confirm interval (often 3600s) in the add-on’s Inputs page.
• Client visibility may require the appropriate Assurance or Wireless capabilities on Catalyst; otherwise fields can be empty.
• `docs/implementation-guide.md` and `docs/guides/catalyst-center.md`.

Step 1 — Configure data collection
• Validate `macAddress`, `hostType`, `connectionType`, `ssid`, and `vlanId` in raw events. Treat MAC and host data as PII: restrict index and dashboard access.

Step 2 — Top SSID and connection-type mix
```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as client_count by connectionType, ssid | sort -client_count | head 20
```

Understanding this SPL
**Client Distribution (Wired/Wireless/Guest)** — Surfaces the busiest `connectionType` and `ssid` pairs for capacity work (RF design, DHCP scopes, and guest portal sizing). The `head 20` cap focuses the chart; remove or increase for “full estate” views.

**Pipeline walkthrough**
• Distinct MACs per `connectionType` and `ssid`, sorted by volume, then trim to the top 20.

Step 3 — Validate
• Compare order-of-magnitude to Catalyst’s client views for the same site scope; exact counts may differ from Splunk de-duplication and poll timing.
• Spot-check a single high-volume SSID in both UIs in the same hour.

Step 4 — Operationalize
• Use as a capacity panel: pair with per-AP or RF health from Assurance as a second row. For site-specific views, add `where` on site or building fields if the TA or a join provides them.

Step 5 — Troubleshooting
• Blank `ssid` for wired is expected—add `where isnotnull(ssid) OR connectionType="WIRED"` as needed. If `client_count` is inflated, dedup `macAddress` per poll per TA documentation before `stats`.
• No events: client input disabled, API 403, or index mismatch—check `splunkd.log` and the Catalyst service account’s wireless/client read permissions.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as client_count by connectionType, ssid | sort -client_count | head 20
```

## Visualization

Bar or column chart (client_count by connectionType and ssid), table of top SSIDs, single value for total wireless clients if post-processed.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
