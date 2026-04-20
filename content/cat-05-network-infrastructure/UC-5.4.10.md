---
id: "5.4.10"
title: "Wireless IDS/IPS Events"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.10 · Wireless IDS/IPS Events

## Description

Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.

## Value

Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.

## Implementation

Enable wireless IDS on the WLC/AP. Forward alerts to Splunk. Alert on deauth floods, rogue AP impersonation, and client spoofing events. Correlate with rogue AP detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Cisco WLC syslog, Meraki API.
• Ensure the following data sources are available: `sourcetype=cisco:wlc`, `sourcetype=meraki:ids`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable wireless IDS on the WLC/AP. Forward alerts to Splunk. Alert on deauth floods, rogue AP impersonation, and client spoofing events. Correlate with rogue AP detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:wlc" "IDS Signature" OR "wIPS"
| rex "Signature (?<sig_id>\d+).*?(?<sig_name>[^,]+).*?MAC (?<attacker_mac>[0-9a-f:]+)"
| stats count by sig_name, attacker_mac | sort -count
```

Understanding this SPL

**Wireless IDS/IPS Events** — Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.

Documented **Data sources**: `sourcetype=cisco:wlc`, `sourcetype=meraki:ids`. **App/TA** (typical add-on context): Cisco WLC syslog, Meraki API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:wlc. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:wlc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by sig_name, attacker_mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (signature, attacker MAC, count), Timeline, Single value (alerts today).

## SPL

```spl
index=network sourcetype="cisco:wlc" "IDS Signature" OR "wIPS"
| rex "Signature (?<sig_id>\d+).*?(?<sig_name>[^,]+).*?MAC (?<attacker_mac>[0-9a-f:]+)"
| stats count by sig_name, attacker_mac | sort -count
```

## Visualization

Table (signature, attacker MAC, count), Timeline, Single value (alerts today).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
