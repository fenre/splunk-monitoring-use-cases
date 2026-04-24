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
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:client (Catalyst Center client data; fields macAddress, connectionType, ssid).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `client` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls client detail data from the Catalyst Center Intent API every 60 minutes. Key fields: `macAddress`, `hostType`, `connectionType`, `ssid`, `vlanId`, `location`, `healthScore`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as client_count by connectionType, ssid | sort -client_count | head 20
```

Understanding this SPL

**Client Distribution by Type (Wired/Wireless/Guest)** — Knowing how clients distribute across SSIDs and connection types helps identify overloaded access points and plan wireless capacity.

**Pipeline walkthrough**

• Filters to Catalyst client events in the `catalyst` index for `cisco:dnac:client`.
• `stats dc(macAddress) as client_count by connectionType, ssid` counts unique clients per connection method and SSID.
• `sort -client_count` and `head 20` surface the busiest SSID and connection-type combinations.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Bar or column chart (client_count by connectionType and ssid), table of top SSIDs, single value for total wireless clients if post-processed.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" | stats dc(macAddress) as client_count by connectionType, ssid | sort -client_count | head 20
```

## Visualization

Bar or column chart (client_count by connectionType and ssid), table of top SSIDs, single value for total wireless clients if post-processed.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
