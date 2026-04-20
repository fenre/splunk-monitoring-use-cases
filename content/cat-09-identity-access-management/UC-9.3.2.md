---
id: "9.3.2"
title: "Impossible Travel Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.3.2 · Impossible Travel Detection

## Description

Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.

## Value

Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.

## Implementation

Ingest IdP sign-in logs. Enrich with GeoIP. Calculate distance and time between consecutive logins per user. Alert when distance/time ratio is impossible (>500km in <2 hours). Whitelist VPN exit IPs and known travel patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`, custom correlation.
• Ensure the following data sources are available: IdP sign-in logs with IP geolocation.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest IdP sign-in logs. Enrich with GeoIP. Calculate distance and time between consecutive logins per user. Alert when distance/time ratio is impossible (>500km in <2 hours). Whitelist VPN exit IPs and known travel patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.session.start"
| iplocation client.ipAddress
| sort actor.alternateId, _time
| streamstats window=2 earliest(_time) as prev_time, earliest(lat) as prev_lat, earliest(lon) as prev_lon by actor.alternateId
| eval distance_km=round(6371*2*asin(sqrt(pow(sin((lat-prev_lat)*pi()/360),2)+cos(lat*pi()/180)*cos(prev_lat*pi()/180)*pow(sin((lon-prev_lon)*pi()/360),2))),0) , time_diff_hr=((_time-prev_time)/3600)
| where distance_km > 500 AND time_diff_hr < 2
```

Understanding this SPL

**Impossible Travel Detection** — Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.

Documented **Data sources**: IdP sign-in logs with IP geolocation. **App/TA** (typical add-on context): `Splunk_TA_okta`, custom correlation. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Impossible Travel Detection**): iplocation client.ipAddress
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `streamstats` rolls up events into metrics; results are split **by actor.alternateId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **distance_km** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where distance_km > 500 AND time_diff_hr < 2` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user span=1h
| where src_count > 2
```

Understanding this CIM / accelerated SPL

**Impossible Travel Detection** — Authentication from two geographically distant locations within an impossibly short timeframe strongly indicates credential compromise.

Documented **Data sources**: IdP sign-in logs with IP geolocation. **App/TA** (typical add-on context): `Splunk_TA_okta`, custom correlation. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where src_count > 2` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Geo map (sign-in locations with lines), Table (impossible travel events), Timeline (flagged events).

## SPL

```spl
index=okta sourcetype="OktaIM2:log" eventType="user.session.start"
| iplocation client.ipAddress
| sort actor.alternateId, _time
| streamstats window=2 earliest(_time) as prev_time, earliest(lat) as prev_lat, earliest(lon) as prev_lon by actor.alternateId
| eval distance_km=round(6371*2*asin(sqrt(pow(sin((lat-prev_lat)*pi()/360),2)+cos(lat*pi()/180)*cos(prev_lat*pi()/180)*pow(sin((lon-prev_lon)*pi()/360),2))),0) , time_diff_hr=((_time-prev_time)/3600)
| where distance_km > 500 AND time_diff_hr < 2
```

## CIM SPL

```spl
| tstats `summariesonly` count dc(Authentication.src) as src_count
  from datamodel=Authentication.Authentication
  where Authentication.action="success"
  by Authentication.user span=1h
| where src_count > 2
```

## Visualization

Geo map (sign-in locations with lines), Table (impossible travel events), Timeline (flagged events).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
