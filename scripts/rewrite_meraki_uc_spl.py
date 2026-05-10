#!/usr/bin/env python3
"""Hand-rewrite SPL for Meraki UCs that the mass substitution couldn't fix.

For each UC, we replace the `spl`, `dataSources`, and the embedded SPL
fence in `detailedImplementation`. The SPL targets the real sourcetypes
shipped by `Splunk_TA_cisco_meraki` (app 5580) — see the canonical
inventory at ~/.cursor/skills/cisco-meraki-ta-setup/reference.md.

Run:
    python3 scripts/rewrite_meraki_uc_spl.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


# ---------------------------------------------------------------------------
# Canonical rewrites
# ---------------------------------------------------------------------------
# Each entry: relative path -> {dataSources, spl, app?, implementation?, ...}
# All rewrites target sourcetypes that actually exist in Splunk_TA_cisco_meraki.
# Sensor data: sourcetype=meraki:sensorreadingshistory, metric/value pairs are
# nested in JSON sub-objects (e.g. temperature.celsius, humidity.relativePercentage,
# co2.concentration, water.present, door.open, noise.ambient.level, battery.percentage).
# We use `rename "metric.subfield" as alias` to handle the JSON-extracted dot-paths.
# ---------------------------------------------------------------------------

REWRITES: dict[str, dict[str, str]] = {
    # ----- Cat 14 — Meraki MT environmental sensors --------------------------
    "content/cat-14-iot-operational-technology-ot/UC-14.1.15.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"temperature\"` from the `cisco_meraki_sensor_readings_history` modular input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Default poll: 86400s. Key fields: `serial`, `network.id`, `network.name`, `metric`, `temperature.celsius`, `temperature.fahrenheit`, `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"temperature\"\n| rename \"temperature.celsius\" as temp_c\n| stats latest(temp_c) as current_temp_c, min(temp_c) as min_temp_c, max(temp_c) as max_temp_c by serial, \"network.name\"\n| where current_temp_c > 30 OR current_temp_c < 5\n| sort - current_temp_c",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` in `Splunk_TA_cisco_meraki` (Splunkbase 5580) to poll `GET /organizations/{orgId}/sensor/readings/history` for MT temperature readings. Filter on `metric=\"temperature\"`. Alert when sensors report temperatures outside the safe range (5-30°C by default — adjust per equipment class).",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.16.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric IN (\"humidity\",\"temperature\")` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `humidity.relativePercentage`, `temperature.celsius`, `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" (metric=\"humidity\" OR metric=\"temperature\")\n| rename \"humidity.relativePercentage\" as humidity_pct, \"temperature.celsius\" as temp_c\n| stats latest(humidity_pct) as humidity_pct, latest(temp_c) as temp_c by serial, \"network.name\"\n| where isnotnull(humidity_pct) AND isnotnull(temp_c)\n| eval a=17.625, b=243.04\n| eval alpha=ln(humidity_pct/100) + (a*temp_c)/(b+temp_c)\n| eval dew_point_c=round((b*alpha)/(a-alpha), 1)\n| eval comfort=case(humidity_pct < 30, \"Too dry\", humidity_pct > 60, \"Too humid\", true(), \"Comfortable\")",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` to collect both temperature and humidity readings from MT sensors. The Magnus-Tetens approximation derives dew point from temperature (°C) and relative humidity (%). Alert when dew point approaches the surface temperature (condensation risk).",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.17.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"door\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `door.open` (boolean), `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"door\"\n| rename \"door.open\" as door_open\n| eval action=if(door_open=\"true\" OR door_open=1, \"open\", \"closed\")\n| stats count as door_events, latest(_time) as last_event_time by serial, \"network.name\", action\n| eval last_event=strftime(last_event_time, \"%Y-%m-%d %H:%M:%S\")\n| sort - last_event_time",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` to collect MT door sensor data. The `door.open` boolean toggles on each open/close transition. Tag specific sensors as restricted-area or after-hours to drive RBAC-aware alerting.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.18.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"water\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `water.present` (boolean), `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"water\"\n| rename \"water.present\" as water_present\n| where water_present=\"true\" OR water_present=1\n| stats count as leak_events, latest(_time) as last_detection_time by serial, \"network.name\"\n| eval last_detection=strftime(last_detection_time, \"%Y-%m-%d %H:%M:%S\")\n| where leak_events > 0\n| sort - last_detection_time",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` to poll for MT10/MT11/MT12 water sensors. Any event with `water.present=true` indicates a leak — alert immediately and dispatch facilities. Persistent positives may indicate a stuck sensor.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.19.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"realPower\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `realPower.draw` (watts), `voltage.level`, `current.draw`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"realPower\"\n| rename \"realPower.draw\" as power_w\n| stats avg(power_w) as avg_power_w, max(power_w) as peak_power_w by serial, \"network.name\"\n| eval power_capacity_pct=round(peak_power_w*100/15000, 2)\n| sort - peak_power_w",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` for MT40 power monitor sensors. `realPower.draw` is in watts; the 15000 W denominator above is a standard 15A/120V circuit headroom — adjust to match the rated capacity of the monitored circuit.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.20.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"co2\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `co2.concentration` (ppm), `ts`. For broader IAQ also consider `metric=\"tvoc\"`, `metric=\"pm25\"`, and `metric=\"indoorAirQuality\"`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"co2\"\n| rename \"co2.concentration\" as co2_ppm\n| stats latest(co2_ppm) as current_co2_ppm, avg(co2_ppm) as avg_co2_ppm by serial, \"network.name\"\n| where current_co2_ppm > 1000\n| sort - current_co2_ppm",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` for MT15 (IAQ) sensors. ASHRAE recommends keeping CO₂ below 1000 ppm in occupied spaces; values above 1500 ppm correlate with reduced cognitive performance. For full IAQ, combine with TVOC, PM2.5, and the composite `indoorAirQuality.score`.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.21.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"noise\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `noise.ambient.level` (dBA), `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"noise\"\n| rename \"noise.ambient.level\" as noise_db\n| timechart span=15m avg(noise_db) as avg_noise_db, max(noise_db) as peak_noise_db by serial limit=10",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` for MT15/MT20 sensors that include the ambient noise mic. Use `timechart` for trend visualisation. WHO recommends keeping office ambient noise below 55 dBA.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.22.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric IN (\"temperature\",\"humidity\")` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `temperature.celsius`, `humidity.relativePercentage`, `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" (metric=\"temperature\" OR metric=\"humidity\")\n| rename \"temperature.celsius\" as temp_c, \"humidity.relativePercentage\" as humidity_pct\n| eval value=coalesce(temp_c, humidity_pct)\n| timechart span=1h avg(value) by metric",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` to collect both temperature and humidity from MT sensors. Trend by location to identify HVAC drift, weekend setback opportunities, or zones consistently outside the comfort band.",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.23.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory metric=\"battery\"` from the `cisco_meraki_sensor_readings_history` input in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `network.name`, `metric`, `battery.percentage`, `ts`.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\" metric=\"battery\"\n| rename \"battery.percentage\" as battery_pct\n| stats latest(battery_pct) as battery_pct by serial, \"network.name\"\n| where battery_pct < 20\n| sort battery_pct",
        "implementation": "Configure `cisco_meraki_sensor_readings_history` to capture MT sensor battery levels. Pre-stage replacement batteries before sensors fall below 20%. The `battery` metric only fires periodically; a missing battery reading for >7 days suggests the sensor itself is offline (see UC-14.1.24).",
    },
    "content/cat-14-iot-operational-technology-ot/UC-14.1.24.json": {
        "dataSources": "`index=meraki sourcetype=meraki:sensorreadingshistory` from the `cisco_meraki_sensor_readings_history` input plus `index=meraki sourcetype=meraki:devicesavailabilities` from `cisco_meraki_devices_availabilities` in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Used to detect sensors that have stopped reporting.",
        "spl": "index=meraki sourcetype=\"meraki:sensorreadingshistory\"\n| stats latest(_time) as last_reading by serial, \"network.name\"\n| eval hours_since_reading=round((now()-last_reading)/3600, 1)\n| where hours_since_reading > 2\n| eval last_reading_human=strftime(last_reading, \"%Y-%m-%d %H:%M:%S\")\n| sort - hours_since_reading",
        "implementation": "Track when each MT sensor last reported. Sensors transmit periodically (every few minutes for live metrics, hourly for slow-change ones); >2 hours without any reading typically means the sensor has disconnected, lost LoRa coverage, or the gateway (MR/MV) is offline. Cross-reference with `meraki:devicesavailabilities` for the parent gateway state.",
    },
    # ----- Cat 15.3 — Meraki MV cameras --------------------------------------
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.22.json": {
        "dataSources": "`index=meraki sourcetype=meraki:devicesavailabilities productType=\"camera\"` from the `cisco_meraki_devices_availabilities` and `cisco_meraki_devices` inputs in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `model`, `network.name`, `productType` (camera/wireless/switch/appliance/sensor/cellularGateway), `status` (online/offline/alerting/dormant).",
        "spl": "index=meraki sourcetype=\"meraki:devicesavailabilities\" productType=\"camera\"\n| stats latest(status) as camera_status, latest(_time) as last_seen by serial, \"network.name\", model\n| eval offline_min=round((now()-last_seen)/60, 0)\n| where camera_status=\"offline\"\n| sort - offline_min",
        "implementation": "Configure `cisco_meraki_devices_availabilities` to poll `GET /organizations/{orgId}/devices/availabilities` (default 1h). Filter on `productType=\"camera\"` to scope to MV cameras only. Alert when any MV reports `status=\"offline\"` for more than 15 minutes; sustained offline cameras break recorded coverage and create compliance gaps.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.23.json": {
        "dataSources": "`index=meraki sourcetype=meraki:audit` from `cisco_meraki_audit` in `Splunk_TA_cisco_meraki` (Splunkbase 5580). The TA does not expose actual cloud-archive utilisation; this UC tracks retention-policy changes via the audit log. For real-time storage alerts, configure the Meraki Dashboard webhook receiver (`sourcetype=meraki:webhook`) and subscribe to `Camera storage` alerts.",
        "spl": "index=meraki sourcetype=\"meraki:audit\"\n| where like(page, \"%camera%\") OR like(label, \"%qualityAndRetention%\") OR like(label, \"%retention%\") OR like(label, \"%schedule%\")\n| stats count as changes, latest(_time) as last_change by adminEmail, networkName, page, label\n| eval last_change_human=strftime(last_change, \"%Y-%m-%d %H:%M:%S\")\n| sort - last_change",
        "implementation": "The Meraki TA does not poll camera storage utilisation directly. Two practical paths: (1) audit-based — track admin changes to `qualityAndRetention` settings (this SPL); (2) webhook-based — configure `cisco_meraki_webhook` HEC input and subscribe to `Camera storage` alerts in the Meraki Dashboard. For day-to-day storage planning, use the Dashboard UI under Cameras > Cameras > Settings > Quality & retention.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.24.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` from `cisco_meraki_webhook` (HEC, real-time) OR `index=meraki sourcetype=meraki:webhooklogs:api` from `cisco_meraki_webhook_logs` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Motion-detection events are delivered via Meraki Dashboard webhooks (Network-wide > Alerts); they are NOT in the polled device-API surface. Subscribe to `Camera motion alerts` in the alert profile.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertType=\"motionAlert\" OR alertTypeId=\"motion_alert\")\n| spath\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| timechart span=1h count as motion_events by device_name limit=10",
        "implementation": "Motion detection alerts are NOT in the polled device-API surface of `Splunk_TA_cisco_meraki`. Two paths: (1) `cisco_meraki_webhook` HEC input (real-time, sourcetype `meraki:webhook`) — requires HEC token and a webhook URL configured in the Meraki Dashboard; (2) `cisco_meraki_webhook_logs` polled input (sourcetype `meraki:webhooklogs:api`) — simpler to set up but capped to the Meraki webhook-logs retention window. This SPL queries both. Subscribe to `Motion alert` alert types per camera or zone in the Dashboard.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.25.json": {
        "dataSources": "`index=meraki sourcetype=meraki:devicesavailabilities productType=\"camera\"` plus `index=meraki sourcetype=meraki:devicesuplinkslossandlatency` from `Splunk_TA_cisco_meraki` (Splunkbase 5580). The TA does not expose a per-camera `quality_score`; this UC infers stream health from camera availability + uplink loss/latency to the cloud archive.",
        "spl": "index=meraki sourcetype=\"meraki:devicesuplinkslossandlatency\"\n| stats avg(lossPercent) as avg_loss_pct, avg(latencyMs) as avg_latency_ms, max(latencyMs) as peak_latency_ms by serial, \"network.name\"\n| where avg_loss_pct > 1 OR avg_latency_ms > 100\n| eval stream_health=case(avg_loss_pct > 5 OR avg_latency_ms > 250, \"POOR\", avg_loss_pct > 1 OR avg_latency_ms > 100, \"FAIR\", true(), \"GOOD\")\n| sort - avg_loss_pct",
        "implementation": "The Splunk_TA_cisco_meraki TA does not expose a per-camera quality score. The most reliable proxy for cloud-archive stream health is the camera's uplink loss and latency, polled via `cisco_meraki_devices_uplinks_loss_and_latency`. Loss > 1% or latency > 100ms generally degrades cloud video continuity. For deeper quality metrics, configure webhook integration and subscribe to `Camera offline` and `Camera unable to upload to cloud` alerts.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.26.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` from `cisco_meraki_webhook` (HEC, real-time) OR `index=meraki sourcetype=meraki:webhooklogs:api` from `cisco_meraki_webhook_logs` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Cloud-archive failure events are delivered via webhooks; the polling device API does not expose archive status.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertType=\"cameraOfflineAlert\" OR alertTypeId=\"camera_unable_to_upload_to_cloud\")\n| spath\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| stats count as failures, latest(_time) as last_failure by device_name, networkName, alertType\n| eval last_failure_human=strftime(last_failure, \"%Y-%m-%d %H:%M:%S\")\n| sort - last_failure",
        "implementation": "Configure either `cisco_meraki_webhook` (HEC, real-time, sourcetype `meraki:webhook`) or `cisco_meraki_webhook_logs` (polled, sourcetype `meraki:webhooklogs:api`). In the Meraki Dashboard, add a webhook URL and subscribe to `Camera unable to upload to cloud` and `Camera offline` alert types. The polling device API does NOT expose individual archive success/failure events — webhook is the only first-class source.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.27.json": {
        "dataSources": "`index=meraki sourcetype=meraki:assurancealerts` from `cisco_meraki_assurance_alerts` plus `index=meraki sourcetype=meraki:webhook` from `cisco_meraki_webhook` in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Stream-quality issues surface as assurance alerts; specific connection errors come via webhook.",
        "spl": "index=meraki (sourcetype=\"meraki:assurancealerts\" OR sourcetype=\"meraki:webhook\")\n| where like(deviceTypes, \"%camera%\") OR like(deviceType, \"%camera%\") OR productType=\"camera\"\n| stats count as alert_count, latest(_time) as last_alert by deviceName, alertType, severity\n| where alert_count > 1\n| sort - alert_count",
        "implementation": "Use `cisco_meraki_assurance_alerts` (default 1h poll) for camera-related assurance alerts (stream connection issues, RTSP failures, NVR communication errors). For real-time per-event alerts also configure `cisco_meraki_webhook` and subscribe to camera alert types in the Dashboard.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.28.json": {
        "dataSources": "`index=meraki sourcetype=meraki:devices productType=\"camera\"` plus `index=meraki sourcetype=meraki:firmwareupgrades` from `Splunk_TA_cisco_meraki` (Splunkbase 5580). Key fields: `serial`, `model`, `firmware`, `productType`, `status`.",
        "spl": "index=meraki sourcetype=\"meraki:devices\" productType=\"camera\"\n| stats latest(firmware) as current_fw, dc(serial) as camera_count by model\n| lookup recommended_camera_fw.csv camera_model AS model OUTPUTNEW recommended_version\n| where isnotnull(recommended_version) AND current_fw != recommended_version",
        "implementation": "Use `cisco_meraki_devices` (1d poll) to read camera firmware versions. Maintain `recommended_camera_fw.csv` with `camera_model,recommended_version` columns aligned to your firmware-baseline policy. Cross-reference with `cisco_meraki_firmware_upgrades` for in-flight upgrade campaigns.",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.29.json": {
        "dataSources": "`index=meraki sourcetype=meraki:audit` from `cisco_meraki_audit` plus `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) from `Splunk_TA_cisco_meraki` (Splunkbase 5580). Camera night-mode quality is not exposed in the TA; this UC uses motion-alert volume per hour-of-day as a proxy.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertType=\"motionAlert\" OR alertTypeId=\"motion_alert\")\n| spath\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| eval hour=tonumber(strftime(_time, \"%H\"))\n| eval period=case(hour>=22 OR hour<6, \"Night (22-06)\", hour>=18 AND hour<22, \"Evening (18-22)\", hour>=6 AND hour<10, \"Morning (06-10)\", true(), \"Day (10-18)\")\n| stats count as motion_alerts by device_name, period\n| sort device_name, period",
        "implementation": "The Splunk_TA_cisco_meraki TA does not expose per-camera quality scores or night-mode effectiveness directly. Two practical paths: (1) audit-based — track admin changes to camera quality settings via `meraki:audit`; (2) webhook-based (this SPL) — bucket motion alerts by hour-of-day to spot cameras whose night-mode behaviour is anomalous (e.g. far more or far fewer motion alerts than peers during 22:00-06:00).",
    },
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.30.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC, real-time) or `meraki:webhooklogs:api` (polled) from `Splunk_TA_cisco_meraki` (Splunkbase 5580). Camera people-counting analytics are delivered via the Meraki MV Sense webhook; they are NOT in the polled device-API surface.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"people_counting\" OR like(alertType, \"%people%\"))\n| spath\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| eval people_count=coalesce('alertData.peopleCount', 'data.peopleCount', peopleCount)\n| where isnotnull(people_count)\n| timechart span=15m avg(people_count) as avg_occupancy by device_name limit=10",
        "implementation": "Configure either `cisco_meraki_webhook` (HEC, real-time) or `cisco_meraki_webhook_logs` (polled) input in the TA, plus a Meraki MV Sense webhook in the Dashboard (Cameras > MV Sense > Webhooks). Each MV12/MV22/MV32/MV52/MV72 camera with people-counting enabled will POST `peopleCount` payloads. For higher-fidelity analytics, also use the Meraki MV Sense REST API directly (not in the TA).",
    },
    # ----- Cat 9.6 — Meraki Systems Manager (MDM) ----------------------------
    # The Splunk_TA_cisco_meraki TA does NOT poll Meraki Systems Manager (SM)
    # endpoints. Real SM data comes from webhooks or direct API integration.
    # We rewrite each UC to use whatever's actually available + honest notes.
    "content/cat-09-identity-access-management/UC-9.6.1.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). The polled device inputs do NOT cover Meraki Systems Manager (SM/MDM); compliance status arrives via SM webhook events. For richer SM detail, write a custom modular input that polls `GET /networks/{networkId}/sm/devices`.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_device_compliance\" OR like(alertType, \"%compliance%\") OR like(alertType, \"%mdm%\"))\n| spath\n| eval compliance_status=coalesce('alertData.complianceStatus', 'data.complianceStatus', complianceStatus)\n| eval os_type=coalesce('alertData.osName', 'data.osName', osName, \"unknown\")\n| stats count as total_devices, count(eval(compliance_status IN (\"noncompliant\",\"unknown\"))) as noncompliant_count by os_type\n| eval compliance_pct=round((total_devices-noncompliant_count)*100/total_devices, 2)\n| where noncompliant_count > 0\n| sort - noncompliant_count",
        "implementation": "Meraki Systems Manager (SM) data is NOT polled by the standard `Splunk_TA_cisco_meraki` device modular inputs. To monitor SM device compliance: (1) configure `cisco_meraki_webhook` (HEC, real-time, sourcetype `meraki:webhook`) OR `cisco_meraki_webhook_logs` (polled, sourcetype `meraki:webhooklogs:api`) and subscribe to SM compliance alerts in the Meraki Dashboard, OR (2) write a custom modular input that polls `GET /networks/{networkId}/sm/devices` and `GET /networks/{networkId}/sm/devices/{deviceId}/securityCenters` and writes results to `index=meraki sourcetype=meraki:sm:devices`. This UC uses the webhook path (works with either input).",
    },
    "content/cat-09-identity-access-management/UC-9.6.2.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM enrollment / un-enrollment webhook events.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_enrollment\" OR like(alertType, \"%enrollment%\") OR like(alertType, \"%sm_device_added%\") OR like(alertType, \"%sm_device_removed%\"))\n| spath\n| eval action=case(like(alertType, \"%added%\") OR like(alertType, \"%enroll%\"), \"enrolled\", like(alertType, \"%removed%\") OR like(alertType, \"%unenroll%\"), \"unenrolled\", true(), alertType)\n| stats count as events, latest(_time) as last_event by networkName, action, alertType\n| eval last_event_human=strftime(last_event, \"%Y-%m-%d %H:%M:%S\")\n| sort - events",
        "implementation": "Meraki SM enrollment events are delivered via Meraki Dashboard webhooks. Configure either `cisco_meraki_webhook` (HEC, real-time) or `cisco_meraki_webhook_logs` (polled) input in `Splunk_TA_cisco_meraki` and add a webhook URL in the Dashboard. Subscribe to SM device enrollment alerts. Track unexpected un-enrollment as a potential MDM-evasion signal.",
    },
    "content/cat-09-identity-access-management/UC-9.6.3.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM jailbreak / root / security-state alerts.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_jailbreak\" OR alertTypeId=\"sm_rooted\" OR like(alertType, \"%jailbreak%\") OR like(alertType, \"%rooted%\") OR like(alertType, \"%security%\"))\n| spath\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| eval os_type=coalesce('alertData.osName', 'data.osName', osName)\n| eval issue=case(like(alertType, \"%jailbreak%\"), \"jailbroken\", like(alertType, \"%root%\"), \"rooted\", true(), alertType)\n| stats count as detections, latest(_time) as last_detection by device_name, os_type, issue, networkName\n| eval last_detection_human=strftime(last_detection, \"%Y-%m-%d %H:%M:%S\")\n| sort - last_detection",
        "implementation": "Meraki SM detects jailbroken iOS and rooted Android devices and posts alerts via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM security alerts in the Dashboard. Treat any detection as a high-severity finding — the device should be quarantined and re-imaged before being allowed back on corporate Wi-Fi.",
    },
    "content/cat-09-identity-access-management/UC-9.6.4.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-installation / uninstall / unauthorized-app webhook events.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_app_install\" OR alertTypeId=\"sm_unauthorized_app\" OR like(alertType, \"%app%\"))\n| spath\n| eval app_name=coalesce('alertData.appName', 'data.appName', appName)\n| eval action=case(like(alertType, \"%install%\"), \"installed\", like(alertType, \"%uninstall%\"), \"uninstalled\", like(alertType, \"%unauthorized%\"), \"unauthorized\", true(), alertType)\n| where isnotnull(app_name)\n| stats count as events by app_name, action, networkName\n| sort - events",
        "implementation": "Meraki SM exposes app-inventory changes via webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app alerts. Maintain an app allow-list lookup (`approved_mobile_apps.csv`) and join here to flag installations of unapproved apps.",
    },
    "content/cat-09-identity-access-management/UC-9.6.5.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM remote-action webhook events (lock, wipe, retire).",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_remote_action\" OR like(alertType, \"%lock%\") OR like(alertType, \"%wipe%\") OR like(alertType, \"%retire%\"))\n| spath\n| eval action=case(like(alertType, \"%wipe%\"), \"wiped\", like(alertType, \"%lock%\"), \"locked\", like(alertType, \"%retire%\"), \"retired\", true(), alertType)\n| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)\n| eval admin=coalesce('alertData.adminName', 'data.adminName', adminName)\n| stats count as actions, latest(_time) as last_action by admin, action, device_name\n| eval last_action_human=strftime(last_action, \"%Y-%m-%d %H:%M:%S\")\n| sort - last_action",
        "implementation": "All Meraki SM remote actions (lock, wipe, retire) are admin-initiated and emit webhook events. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe in the Dashboard. Cross-reference with `meraki:audit` (admin login source/IP) for full attribution. A burst of wipes from a single admin is a strong account-compromise signal.",
    },
    "content/cat-09-identity-access-management/UC-9.6.6.json": {
        "dataSources": "`index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM app-deployment webhook events.",
        "spl": "index=meraki sourcetype IN (\"meraki:webhook\",\"meraki:webhooklogs:api\") (alertTypeId=\"sm_app_deployment\" OR like(alertType, \"%deploy%\") OR like(alertType, \"%app_install%\"))\n| spath\n| eval app_name=coalesce('alertData.appName', 'data.appName', appName)\n| eval status=coalesce('alertData.status', 'data.status', status)\n| stats count as deployments, count(eval(status=\"success\" OR status=\"installed\")) as success_count, count(eval(status=\"failed\" OR status=\"error\")) as failed_count by app_name\n| eval success_rate=round(success_count*100/deployments, 2)\n| where success_rate < 95 OR failed_count > 0\n| sort success_rate",
        "implementation": "Meraki SM app-deployment outcomes are delivered via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM app-deployment alerts in the Dashboard. A success_rate below 95% on a given app usually means a payload/profile/dependency issue — re-test deployment in a pilot ring before re-pushing org-wide.",
    },
}


def replace_spl_fence(text: str, new_spl: str) -> str:
    """Replace the first ```spl ... ``` fence in `text` with the new SPL.

    Operates on the raw JSON-escaped string (so `\\n` is literal in the file).
    The new_spl is provided as a real Python string (with newlines) and we
    escape it for JSON before substitution.
    """
    if "```spl" not in text:
        return text
    # The new_spl is a Python string with real newlines. We need to JSON-escape
    # it to embed inside the JSON string value of `detailedImplementation`.
    # That means: `\n` -> `\\n`, `"` -> `\\"`.
    json_escaped = (
        new_spl.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    pattern = re.compile(r"```spl\\n(.*?)\\n```", re.DOTALL)
    return pattern.sub(lambda m: f"```spl\\n{json_escaped}\\n```", text, count=1)


def update_field(text: str, field: str, new_value: str) -> str:
    """Replace a JSON string field's value with a new value.

    Conservatively handles only the simple case: `"field": "value"`. The new
    value must already be JSON-string-safe (we escape it here).
    """
    json_escaped = (
        new_value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    # Match: "field": "...." accounting for escaped quotes and newlines inside
    pattern = re.compile(
        r'("' + re.escape(field) + r'"\s*:\s*)"((?:\\.|[^"\\])*)"',
        re.DOTALL,
    )

    def _sub(m: re.Match[str]) -> str:
        return f'{m.group(1)}"{json_escaped}"'

    new_text, n = pattern.subn(_sub, text, count=1)
    if n == 0:
        # Field not present — append before the last `}`. Conservative guard:
        # only append if the text ends with `}` and is valid JSON.
        return text
    return new_text


def main() -> int:
    changed = 0
    failed = 0
    for rel_path, fields in REWRITES.items():
        path = REPO / rel_path
        if not path.exists():
            print(f"  MISS: {rel_path} not found")
            failed += 1
            continue
        text = path.read_text(encoding="utf-8")
        new_text = text
        for field, value in fields.items():
            new_text = update_field(new_text, field, value)
        # Refresh the SPL fence in detailedImplementation to match `spl`
        if "spl" in fields:
            new_text = replace_spl_fence(new_text, fields["spl"])

        # Validate JSON
        try:
            json.loads(new_text)
        except json.JSONDecodeError as exc:
            print(f"  ERROR: invalid JSON after rewrite for {rel_path}: {exc}")
            failed += 1
            continue
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"  OK: {rel_path}")
    print()
    print(f"Rewrote {changed} files; {failed} errors")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
