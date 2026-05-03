<!-- AUTO-GENERATED from UC-5.10.5.json — DO NOT EDIT -->

---
id: "5.10.5"
title: "SIP Registration Storm Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.10.5 · SIP Registration Storm Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Availability, Security

*We watch for floods of phone check-in messages to the call server so a bad app or handsets in a loop do not knock the platform over before you see a spike on a chart.*

---

## Description

Detects sudden spikes in SIP REGISTER messages that can overwhelm IMS/SBC infrastructure — caused by mass device reboots, network flaps, or DDoS attacks. Early detection prevents cascading core failures.

## Value

NOC teams detect registration storms within minutes of onset and distinguish mass device re-registration (self-limiting) from device loops and DDoS attacks (requiring intervention), preventing cascading IMS core failures.

## Implementation

Configure Splunk App for Stream to capture SIP REGISTER traffic on the IMS/SBC interfaces. Use a 5-minute time bucket for aggregation. Calculate a rolling baseline using `eventstats` and flag any bucket where REGISTER volume exceeds 3 standard deviations above the mean. The `dc(src)` field helps distinguish between a mass re-registration event (many unique sources) vs. a single device stuck in a registration loop (few unique sources, high count). Alert the NOC immediately as registration storms can cascade into full core outages within minutes.

## Detailed Implementation

### Prerequisites
- Splunk App for Stream (Splunkbase 1809) v8.0+ with the Stream Forwarder deployed on a mirror/tap that sees SIP signaling on the IMS core or SBC registrar-facing interfaces. SIP REGISTER typically uses UDP 5060 or TCP 5060/5061.
- Understand SIP registration mechanics: each SIP endpoint (phone, softclient, IoT device) periodically sends a REGISTER message to maintain its registration with the registrar/P-CSCF. Normal registration interval is 3600 seconds (1 hour) by default, though some devices use shorter intervals (300–600 seconds). A registration storm occurs when a large number of devices simultaneously send REGISTER messages — this can happen after a network outage recovery (all devices re-register at once), a software/firmware update push (mass reboot), an SBC restart, or a malicious registration flood (VoIP DDoS).
- Know your normal registration baseline: for a platform with 100,000 registered endpoints at 1-hour registration intervals, the expected steady-state REGISTER rate is ~28 per second (100K / 3600). During a storm, this can spike to 10,000+ per second, overwhelming the registrar, HSS lookup capacity, and SBC CPU.
- The distinction between a storm from many unique devices (mass re-registration) vs. a single device in a registration loop is critical for triage — the `dc(src)` (distinct source IPs) field provides this.
- Index: use the same `index=telecom_sip` from UC-5.10.4 or create a separate stream filtered to REGISTER only.

### Step 1 — Configure data collection
Reuse the SIP stream from UC-5.10.4, or create a dedicated REGISTER-focused stream for higher fidelity:

| Setting | Value |
|---------|-------|
| Protocol | SIP |
| Name | `sip_register_monitoring` |
| Filter | `method == "REGISTER"` |
| Fields | `method`, `reply_code`, `src`, `dest`, `caller`, `call_id`, `user_agent`, `expires` |
| Sourcetype | `stream:sip` |
| Index | `telecom_sip` |

Verify REGISTER data is arriving:
```spl
index=telecom_sip sourcetype="stream:sip" method="REGISTER" earliest=-15m
| stats count dc(src) as unique_sources
```
The `count` divided by 900 (seconds in 15 minutes) gives you the average REGISTER rate per second. For 100K endpoints with 1-hour intervals, expect ~28/sec baseline. If the count is zero, verify the mirror is capturing REGISTER traffic (it may be on a different SBC interface than INVITE traffic).

Establish the baseline:
```spl
index=telecom_sip sourcetype="stream:sip" method="REGISTER" earliest=-7d
| bin _time span=5m
| stats count as register_count by _time
| stats avg(register_count) as avg_5min stdev(register_count) as stdev_5min
```
Record these baseline values — they inform your threshold configuration. A typical 5-minute bucket should contain a predictable number of registrations based on your subscriber count and registration interval.

### Step 2 — Create the search and alert

**Primary search — Registration storm detection (5-min real-time):**
```spl
index=telecom_sip sourcetype="stream:sip" method="REGISTER" earliest=-24h
| bin _time span=5m
| stats count as register_count dc(src) as unique_sources by _time
| eventstats avg(register_count) as baseline stdev(register_count) as stdev_reg
| eval threshold=baseline + (3 * stdev_reg)
| eval threshold=if(threshold < baseline*2, baseline*2, threshold)
| where register_count > threshold
| eval spike_factor=round(register_count/baseline, 1)
| eval storm_type=case(unique_sources > baseline*0.5, "Mass Re-Registration (many devices)", unique_sources < 10, "Registration Loop (few devices, high rate)", 1==1, "Moderate Spike")
| table _time, register_count, unique_sources, baseline, threshold, spike_factor, storm_type
| sort -spike_factor
```

#### Understanding this SPL: We aggregate REGISTER messages into 5-minute buckets and compare each bucket to the 24-hour rolling average using `eventstats`. The threshold is set at 3 standard deviations above the mean, with a floor of 2x the baseline to prevent false positives in very stable environments (where stdev is near zero). The `storm_type` classification is critical for triage: "Mass Re-Registration" (many unique sources) typically follows a network event and may be self-resolving but needs monitoring; "Registration Loop" (few sources, high count) indicates a broken device or attack and needs immediate action to prevent registrar overload.

**Source analysis — identify the storm origin:**
```spl
index=telecom_sip sourcetype="stream:sip" method="REGISTER" earliest=-15m
| stats count as reg_count latest(reply_code) as last_reply latest(user_agent) as device_type by src
| sort -reg_count
| head 50
| eval reg_per_min=round(reg_count/15, 1)
| eval is_loop=if(reg_per_min > 10, "YES — possible loop", "normal")
```

#### Understanding this SPL: During an active storm, this drill-down identifies the top registering sources. A device sending >10 REGISTER/minute is likely in a loop — normal is 1 per hour (0.017/min). The `user_agent` field identifies the device type (Cisco IP Phone, Obi, Polycom, etc.) and firmware version, which helps determine if a firmware bug is causing the loop. The `last_reply` shows the registrar's response — repeated 401 (Unauthorized) suggests authentication failure triggering retry loops; 200 (OK) followed by immediate re-register suggests the device is not caching its registration.

**Response code analysis during storm:**
```spl
index=telecom_sip sourcetype="stream:sip" method="REGISTER" earliest=-15m
| stats count by reply_code
| eval code_meaning=case(reply_code==200, "OK (success)", reply_code==401, "Unauthorized (auth challenge)", reply_code==403, "Forbidden (rejected)", reply_code==408, "Timeout (registrar overloaded)", reply_code==429, "Too Many Requests (rate limited)", reply_code==500, "Internal Error", reply_code==503, "Service Unavailable", isnull(reply_code), "No response captured", 1==1, "Code-".reply_code)
| sort -count
```

#### Understanding this SPL: During a registration storm, the registrar's response pattern reveals impact severity. If most responses are 200 OK, the registrar is handling the load. If 408 Timeout or 503 Service Unavailable dominate, the registrar is overloaded and legitimate registrations are failing — this means subscriber impact (phones going offline). A high 401 count suggests an authentication backend failure triggering mass retry.

Schedule as Alert: run the primary storm detection search every 5 minutes over a 24-hour window. Trigger when `spike_factor > 3`. Severity: Critical if `spike_factor > 10` or `storm_type="Registration Loop"`. Throttle for 30 minutes (storms can last minutes to hours).

### Step 3 — Validate
(a) During normal operations, run the storm detection search over 7 days and verify it returns zero or very few results. If it fires frequently, the baseline may be unstable — increase the lookback window or raise the threshold multiplier to 4 sigma.

(b) Simulate a controlled storm: if you have a test environment, reboot a batch of 50+ SIP endpoints simultaneously and verify the search detects the spike. Confirm the `storm_type` correctly classifies it as "Mass Re-Registration" (many unique sources).

(c) Simulate a registration loop: configure a test device with incorrect credentials. It should retry REGISTER rapidly, generating a concentration from one `src`. Verify the search detects this and classifies it as "Registration Loop".

(d) Compare the baseline values to your expected registration rate: subscriber_count / registration_interval × 300 (seconds per 5-min bucket) should approximate `avg(register_count)`. If Splunk shows significantly more, devices may have shorter-than-expected registration intervals.

(e) Verify response code capture: during a test storm, confirm `reply_code` values are populated. If the registrar sends responses on a different IP than it receives registrations, the mirror may not capture responses.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Voice — SIP Registration Health"):
- Row 1 — Single-value tiles: "Current REGISTER rate (/min)" (with sparkline), "Baseline rate (/min)", "Spike factor (current/baseline)" (red if >3), "Unique registering sources (5m)".
- Row 2 — Timechart: REGISTER count per 5-minute bucket over 24h, with dynamic threshold line overlaid. Spike periods highlighted in red.
- Row 3 — During-storm drill-down: top 50 sources by registration rate, with device type and last response code. Color-code rows where `is_loop=YES`.
- Row 4 — Response code distribution pie chart (200 vs. 401 vs. 403 vs. 503 etc.) during the active period.

Alerting:
- Critical (spike_factor > 10 or registration loop detected): page NOC and IMS/voice core team immediately. Include spike_factor, unique_sources count, and storm_type. Registration storms can cascade to full IMS outage within minutes if the registrar or HSS becomes unresponsive.
- Warning (spike_factor > 3): notify voice engineering for monitoring. May be a transient event (small outage recovery) or the start of a larger storm.

Runbook (owner: IMS / Voice Core Engineering):
1. **Mass re-registration (many sources, post-outage)**: This is typically self-limiting — devices re-register over a few minutes as their registration timers are randomized. Monitor the registrar CPU and HSS query rate. If the registrar is overloaded (503 responses increasing), implement rate-limiting on the SBC: configure SIP REGISTER rate-limiting to 100 per second per source subnet. The storm should subside within 15–30 minutes as devices successfully re-register and resume normal intervals.
2. **Registration loop (few sources)**: Identify the looping device(s) from the source analysis search. Common causes: incorrect credentials (device retries every 1–5 seconds after 401), expired TLS certificate (device gets 403 and retries), firmware bug. Block the offending source IP(s) on the SBC immediately to protect the registrar. Contact the device owner to fix credentials or update firmware.
3. **DDoS registration flood**: If `dc(src)` is very high and sources are external/unknown, this is a VoIP DDoS attack. Activate SBC rate-limiting per-source and per-subnet. Enable REGISTER authentication challenge (401) if not already active — most botnets cannot complete SIP digest authentication. Engage your DDoS mitigation provider for upstream filtering.
4. **Registrar overloaded (503 responses dominating)**: If the registrar cannot keep up, temporarily increase the minimum REGISTER interval (Expires header) to 7200 seconds on the SBC to reduce re-registration frequency. Scale the registrar horizontally if possible. Prioritize re-registrations from known enterprise IP ranges over unknown sources.

### Step 5 — Troubleshooting

- **Storm detection never fires despite known events** — The 3-sigma threshold may be too high for your environment. If your registration rate is very stable, even a 2x spike may not exceed 3 sigma. Lower the threshold to 2 sigma, or add an absolute threshold floor (e.g. `register_count > 5000 AND register_count > threshold`).

- **Storm detection fires constantly (too many false positives)** — Your baseline may be unstable due to regular scheduled events (nightly firmware updates, daily office-hours registration bursts). Extend the lookback window to 7 days, or use `percentile95(register_count)` as the threshold instead of mean + 3*stdev.

- **`dc(src)` is always 1 (single source)** — The mirror may be capturing traffic after NAT, where all REGISTER messages appear to come from one IP (the NAT gateway). Move the mirror to before the NAT device, or use the SIP Contact header (which contains the device's private IP) instead of the IP layer `src`.

- **`user_agent` is null** — Not all SIP endpoints include a User-Agent header. This field is optional in RFC 3261. You can still identify the device type by the Contact header URI pattern or the SIP domain.

- **Response codes not visible during storms** — If the registrar becomes completely unresponsive, there may be no response events to analyze. The absence of responses is itself a critical signal — compare `register_count` (requests) to response count in the same window. A large gap means the registrar is dropping requests.

## SPL

```spl
sourcetype="stream:sip" method="REGISTER"
| bin _time span=5m
| stats count as register_count, dc(src) as unique_sources by _time
| eventstats avg(register_count) as baseline, stdev(register_count) as stdev_reg
| eval threshold=baseline+(3*stdev_reg)
| where register_count>threshold
| eval spike_factor=round(register_count/baseline, 1)
```

## Visualization

Line chart (REGISTER count over time with dynamic baseline threshold line), Single value (current spike factor vs. baseline), Table (time bucket, register_count, unique_sources, baseline, threshold — highlighting rows above threshold), Area chart (unique sources over time to correlate with storms).

## Known False Positives

SBC certificate rolls, number portability batches, and customer premise equipment reboots can spike SIP failures. Match trunk names to the carrier work queue.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
