<!-- AUTO-GENERATED from UC-5.8.21.json — DO NOT EDIT -->

---
id: "5.8.21"
title: "Webhook Delivery Failure Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.21 · Webhook Delivery Failure Tracking (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you see when webhooks from Meraki fail, so automations and tickets still fire when something important happens.*

---

## Description

Ensures webhook notifications reach integrations and alerts don't get lost.

## Value

Network operations teams monitor Meraki webhook delivery health to Splunk, detecting failed deliveries that create gaps in real-time alerting and diagnosing HEC endpoint or authentication issues.

## Implementation

Log webhook delivery attempts. Alert on sustained failures.

## Detailed Implementation

### Prerequisites
- Meraki webhooks configured to send alerts to Splunk HEC. Webhooks provide near-real-time notification of events (device offline, VPN down, etc.). Data in `index=meraki` with `sourcetype=meraki:webhook`. Key fields: `alertType`, `networkName`, `deviceSerial`, `alertData`, `sentAt`.
- Webhook delivery failures occur when: (1) the Splunk HEC endpoint is unreachable, (2) HEC returns errors (token invalid, index disabled), (3) network issues between Meraki cloud and Splunk. Meraki retries failed webhooks but eventually drops them.
- Additionally, monitor the Meraki webhook logs via the Dashboard API: `GET /organizations/{orgId}/webhooks/logs`.

### Step 1 — Configure data collection
Verify webhook data:
```spl
index=meraki sourcetype="meraki:webhook" earliest=-24h
| stats count by alertType, networkName
```
If empty: webhooks may not be configured, or they're failing to deliver.

### Step 2 — Create the search and alert

**Primary search — Webhook delivery health:**
```spl
index=meraki sourcetype="meraki:webhooklogs:api" earliest=-24h
| eval delivery_status=if(responseCode >= 200 AND responseCode < 300, "SUCCESS", "FAILED")
| stats count as total count(eval(delivery_status="SUCCESS")) as success count(eval(delivery_status="FAILED")) as failed by url, networkName
| eval success_rate=round(100*success/total, 1)
| where failed > 0
| sort -failed
```

#### Understanding this SPL: Webhook failures mean real-time alerts aren't reaching Splunk. If the webhook to Splunk HEC fails, critical events (site down, VPN failure) are only detected during the next API poll cycle — potentially 5-15 minutes later. For time-sensitive incidents, this delay can be significant.

**Webhook gap detection (expected vs. actual):**
```spl
index=meraki sourcetype="meraki:webhook" earliest=-24h
| bin _time span=1h
| stats count as webhooks by _time
| eventstats avg(webhooks) as avg_hourly
| eval gap=if(webhooks < avg_hourly * 0.3, "POSSIBLE_GAP", "OK")
| where gap="POSSIBLE_GAP"
```

**Failed delivery error analysis:**
```spl
index=meraki sourcetype="meraki:webhooklogs:api" responseCode >= 400 earliest=-24h
| stats count by responseCode, url
| eval error_type=case(responseCode=401, "Auth failure", responseCode=403, "Forbidden", responseCode=404, "Endpoint not found", responseCode=429, "Rate limited", responseCode >= 500, "Server error", 1==1, "Other")
| sort -count
```

### Step 3 — Validate
(a) Trigger a webhook event (e.g., disconnect a device) and verify it arrives in Splunk within seconds.
(b) Temporarily misconfigure the webhook URL and verify the failure is logged.
(c) Compare webhook logs from Meraki Dashboard with Splunk data to identify any missed events.

### Step 4 — Operationalize
Dashboard ("Meraki Webhook Health"):
- Row 1 — Single-value tiles: "Webhooks received (24h)", "Failed deliveries", "Success rate %", "Webhook gaps".
- Row 2 — Delivery failure table: URL, network, failed count, response code, error type.
- Row 3 — Webhook volume trending with gap detection.

Alerting:
- Critical (webhook success rate < 80%): real-time alerting is broken.
- Warning (any failed webhook delivery): investigate HEC endpoint health.

### Step 5 — Troubleshooting

- **No webhook data at all** — Check Meraki Dashboard: Network > Alerts > Webhooks. Verify the webhook URL points to your Splunk HEC endpoint with the correct token.

- **401/403 errors** — HEC token is invalid or the index specified in the token is disabled. Verify the HEC token and index configuration.

- **Webhook data arrives but is unparsed** — The sourcetype may not be set correctly. Configure props.conf for `meraki:webhook` to handle the JSON payload.

## SPL

```spl
index=meraki sourcetype="meraki:webhook" (status="failure" OR status="error")
| stats count as failure_count, latest(error_message) as last_error by webhook_id, organization
| where failure_count > 5
```

## Visualization

Webhook failure timeline; failure cause breakdown; affected org list.

## Known False Positives

Meraki and your receiver can retry webhooks; dedup by `id` and avoid paging on the first single failure without context.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
