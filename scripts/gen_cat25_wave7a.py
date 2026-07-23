#!/usr/bin/env python3
"""Generate cat-25 wave7a UCs for subcategories 25.1-25.20."""
from __future__ import annotations

from pathlib import Path

from gen_cat25_common import Cat25Writer, R

SCRIPT_PATH = Path(__file__).resolve()
EXPECTED_PER_SUB = 15
TARGET_SUBS = [str(sub) for sub in range(1, 21)]


def S(
    title: str,
    crit: str,
    diff: str,
    mtypes: list[str],
    spl: str,
    desc: str,
    val: str,
    impl: str,
    viz: str,
    grandma_body: str,
) -> dict[str, object]:
    return {
        "title": title,
        "crit": crit,
        "diff": diff,
        "mtypes": mtypes,
        "spl": spl,
        "desc": desc,
        "val": val,
        "impl": impl,
        "viz": viz,
        "grandma_body": grandma_body,
    }


def SPL(*lines: str) -> str:
    return "\n".join(lines)


STYLE: dict[str, dict[str, object]] = {
    "1": {"crit": "low", "diff": "advanced", "mtypes": ["Performance", "Anomaly"], "cadence": "weekly"},
    "2": {"crit": "medium", "diff": "advanced", "mtypes": ["Analytics", "Risk"], "cadence": "daily"},
    "3": {"crit": "medium", "diff": "advanced", "mtypes": ["Cost", "Performance"], "cadence": "daily"},
    "4": {"crit": "low", "diff": "advanced", "mtypes": ["Availability", "Reliability"], "cadence": "hourly"},
    "5": {"crit": "low", "diff": "intermediate", "mtypes": ["Operations", "Fault"], "cadence": "daily"},
    "6": {"crit": "medium", "diff": "advanced", "mtypes": ["Cost", "Analytics"], "cadence": "daily"},
    "7": {"crit": "low", "diff": "intermediate", "mtypes": ["Performance", "Analytics"], "cadence": "daily"},
    "8": {"crit": "medium", "diff": "advanced", "mtypes": ["Availability", "Operations"], "cadence": "hourly"},
    "9": {"crit": "medium", "diff": "advanced", "mtypes": ["Availability", "Security"], "cadence": "hourly"},
    "10": {"crit": "low", "diff": "intermediate", "mtypes": ["Physical", "Anomaly"], "cadence": "daily"},
    "11": {"crit": "low", "diff": "intermediate", "mtypes": ["Physical", "Operations"], "cadence": "daily"},
    "12": {"crit": "medium", "diff": "intermediate", "mtypes": ["Cost", "Analytics"], "cadence": "daily"},
    "13": {"crit": "low", "diff": "intermediate", "mtypes": ["Analytics", "Operations"], "cadence": "daily"},
    "14": {"crit": "low", "diff": "advanced", "mtypes": ["Analytics", "Cost"], "cadence": "daily"},
    "15": {"crit": "low", "diff": "intermediate", "mtypes": ["Quality", "Performance"], "cadence": "daily"},
    "16": {"crit": "low", "diff": "advanced", "mtypes": ["Quality", "Performance"], "cadence": "daily"},
    "17": {"crit": "medium", "diff": "advanced", "mtypes": ["Operations", "Quality"], "cadence": "daily"},
    "18": {"crit": "medium", "diff": "advanced", "mtypes": ["Physical Security", "Availability"], "cadence": "hourly"},
    "19": {"crit": "medium", "diff": "intermediate", "mtypes": ["Physical", "Risk"], "cadence": "daily"},
    "20": {"crit": "medium", "diff": "advanced", "mtypes": ["Physical", "Analytics"], "cadence": "hourly"},
}


def G(
    sub: str,
    title: str,
    spl: str,
    product: str,
    focus: str,
    benefit: str,
    viz: str,
    *,
    crit: str | None = None,
    diff: str | None = None,
    mtypes: list[str] | None = None,
    cadence: str | None = None,
    impl_hint: str = "",
) -> dict[str, object]:
    style = STYLE[sub]
    crit = crit or str(style["crit"])
    diff = diff or str(style["diff"])
    mtypes = mtypes or list(style["mtypes"])
    cadence = cadence or str(style["cadence"])
    desc = f"Uses {product} telemetry to monitor {focus} in index=personal."
    val = (
        f"Splunk turns the feed into an operational check for {benefit}, "
        "so the signal does not stay buried inside separate consumer apps or exports."
    )
    impl = (
        f"Ingest {product} data through its real API, export, MQTT bridge, or open-source connector "
        f"into `index=personal`; preserve the fields referenced in the SPL and schedule the search on a {cadence} cadence."
    )
    if impl_hint:
        impl = f"{impl} {impl_hint}"
    grandma_body = f"{focus} so you can spot {benefit} before it becomes annoying."
    return S(title, crit, diff, mtypes, spl, desc, val, impl, viz, grandma_body)


DEFAULTS: dict[str, dict[str, object]] = {
    "1": {
        "app": (
            "COROS, Wahoo ELEMNT, TrainerRoad, Apple Fitness / HealthKit exports, Concept2 Logbook, "
            "Strava, Garmin Connect, and Zwift activity feeds via official APIs, FIT/CSV exports, and Splunk HEC."
        ),
        "ds": (
            "Endurance activities (`strava:activity`, `garmin:activity`, `coros:activity`, `wahoo:workout`, "
            "`trainerroad:workout`, `applefitness:workout`, `concept2:workout`, `zwift:activity`)."
        ),
        "refs": R(
            ("Strava - API reference", "https://developers.strava.com/docs/reference/"),
            ("COROS support", "https://support.coros.com/hc/en-us"),
            ("Wahoo support", "https://support.wahoofitness.com/hc/en-us"),
            ("TrainerRoad support", "https://support.trainerroad.com/hc/en-us"),
            ("Apple HealthKit", "https://developer.apple.com/documentation/healthkit"),
            ("Concept2 Logbook API", "https://log.concept2.com/developers/documentation"),
        ),
    },
    "2": {
        "app": (
            "Apple Health / Apple Watch exports, Oura, WHOOP, Dexcom, Levels, LibreView, Eight Sleep, "
            "Withings, and Garmin Body Battery feeds via vendor APIs, exports, Home Assistant bridges, and Splunk HEC."
        ),
        "ds": (
            "Recovery and biometrics (`apple:health`, `oura:daily`, `whoop:cycle`, `dexcom:egv`, `levels:glucose`, "
            "`libre:glucose`, `eightsleep:sleep`, `withings:measure`, `garmin:bodybattery`)."
        ),
        "refs": R(
            ("Apple HealthKit", "https://developer.apple.com/documentation/healthkit"),
            ("Oura API v2", "https://cloud.ouraring.com/v2/docs"),
            ("WHOOP developer platform", "https://developer.whoop.com/"),
            ("Dexcom developer portal", "https://developer.dexcom.com/"),
            ("Eight Sleep", "https://www.eightsleep.com/"),
            ("LibreView", "https://www.libreview.com/"),
            ("Levels", "https://www.levelshealth.com/"),
        ),
    },
    "3": {
        "app": (
            "Tesla Fleet API / TeslaMate, Rivian telemetry, ChargePoint session exports, PlugShare trip logs, "
            "Smartcar, and OBD-II / home-charger data via APIs, CSV exports, MQTT, and Splunk HEC."
        ),
        "ds": (
            "Personal EV and vehicle telemetry (`tesla:vehicle`, `tesla:charge`, `rivian:vehicle`, "
            "`chargepoint:session`, `plugshare:checkin`, `evcharger:session`, `obd:pid`, `smartcar:vehicle`)."
        ),
        "refs": R(
            ("Tesla Fleet API", "https://developer.tesla.com/docs/fleet-api"),
            ("TeslaMate documentation", "https://docs.teslamate.org/"),
            ("Rivian", "https://rivian.com/"),
            ("ChargePoint", "https://www.chargepoint.com/"),
            ("PlugShare", "https://www.plugshare.com/"),
            ("Smartcar API", "https://smartcar.com/docs/"),
            ("Open Charge Point Protocol", "https://www.openchargealliance.org/protocols/open-charge-point-protocol/"),
        ),
    },
    "4": {
        "app": (
            "Home Assistant, Matter and Thread border routers, Alexa routine logs, Google Home automations, "
            "Zigbee2MQTT bridges, SmartThings, Node-RED, and webhooks streamed to Splunk HEC."
        ),
        "ds": (
            "Home automation orchestration (`homeassistant:event`, `matter:event`, `thread:router`, `alexa:routine`, "
            "`googlehome:event`, `zigbee2mqtt:bridge`, `smartthings:event`, `nodered:event`)."
        ),
        "refs": R(
            ("Home Assistant", "https://www.home-assistant.io/docs/"),
            ("Home Assistant Matter integration", "https://www.home-assistant.io/integrations/matter/"),
            ("Home Assistant Thread integration", "https://www.home-assistant.io/integrations/thread/"),
            ("Alexa smart home docs", "https://developer.amazon.com/en-US/docs/alexa/smarthome/steps-to-build-a-smart-home-skill.html"),
            ("Google Home automations", "https://developers.home.google.com/automations"),
            ("Node-RED", "https://nodered.org/docs/"),
            ("Zigbee2MQTT", "https://www.zigbee2mqtt.io/"),
        ),
    },
    "5": {
        "app": (
            "Aqara, IKEA Tradfri, LIFX, Nanoleaf, Shelly, Zigbee2MQTT, Ecobee, and smart blind motors "
            "via vendor clouds, LAN APIs, MQTT bridges, and Splunk HEC."
        ),
        "ds": (
            "Device-state telemetry (`zigbee2mqtt:device`, `aqara:device`, `tradfri:device`, `lifx:state`, "
            "`nanoleaf:scene`, `blindmotor:state`, `shelly:status`, `ecobee:thermostat`)."
        ),
        "refs": R(
            ("Aqara", "https://www.aqara.com/en/"),
            ("IKEA smart home", "https://www.ikea.com/us/en/cat/smart-lighting-36812/"),
            ("LIFX support", "https://support.lifx.com/"),
            ("Nanoleaf integrations", "https://nanoleaf.me/en-US/integration/"),
            ("Shelly API documentation", "https://shelly-api-docs.shelly.cloud/"),
            ("ecobee developer API", "https://www.ecobee.com/home/developer/api/introduction/index.shtml"),
            ("Zigbee2MQTT", "https://www.zigbee2mqtt.io/"),
        ),
    },
    "6": {
        "app": (
            "Tesla Powerwall, Enphase IQ, SolarEdge, Sense, Emporia Vue, DSMR / P1 smart meters, and utility tariff "
            "exports collected via vendor APIs, Home Assistant, MQTT, and Splunk HEC."
        ),
        "ds": (
            "Home energy telemetry (`powerwall:aggregate`, `enphase:production`, `solaredge:power`, "
            "`sense:device`, `emporia:circuit`, `dsmr:telegram`, `utilityrate:tariff`)."
        ),
        "refs": R(
            ("Tesla Powerwall", "https://www.tesla.com/support/energy/powerwall"),
            ("Enphase API", "https://developer-v4.enphase.com/"),
            ("SolarEdge Monitoring API", "https://developers.solaredge.com/docs/monitoring-api/"),
            ("Home Assistant Sense integration", "https://www.home-assistant.io/integrations/sense/"),
            ("Emporia Vue integration", "https://github.com/magico13/ha-emporia-vue"),
            ("DSMR Reader docs", "https://dsmr-reader.readthedocs.io/"),
            ("Home Assistant utility meter", "https://www.home-assistant.io/integrations/utility_meter/"),
        ),
    },
    "7": {
        "app": (
            "Jellyfin, Emby, Steam, Steam Deck logs, Xbox and Nintendo exports, Tautulli, AntennaPod, RetroArch, "
            "and the *arr stack via official APIs, local databases, webhook payloads, and Splunk HEC."
        ),
        "ds": (
            "Media and gaming telemetry (`jellyfin:activity`, `emby:session`, `steam:player`, `steamdeck:session`, "
            "`xbox:activity`, `nintendo:play`, `tautulli:play`, `antennapod:episode`, `retroarch:session`, `sonarr:event`)."
        ),
        "refs": R(
            ("Jellyfin documentation", "https://jellyfin.org/docs/"),
            ("Emby support", "https://emby.media/support/"),
            ("Steam Web API", "https://developer.valvesoftware.com/wiki/Steam_Web_API"),
            ("Tautulli documentation", "https://docs.tautulli.com/"),
            ("AntennaPod", "https://github.com/AntennaPod/AntennaPod"),
            ("nxapi", "https://github.com/samuelthomas2774/nxapi"),
            ("RetroArch docs", "https://docs.libretro.com/"),
        ),
    },
    "8": {
        "app": (
            "Kubernetes homelab clusters, Proxmox, Vaultwarden, Paperless-ngx, Immich, AdGuard Home, Docker, "
            "TrueNAS, and NUT metrics via APIs, logs, Telegraf, and Splunk HEC."
        ),
        "ds": (
            "Homelab services (`kubernetes:pod`, `proxmox:metric`, `vaultwarden:event`, `paperless:document`, "
            "`immich:job`, `adguard:query`, `docker:stats`, `truenas:pool`, `nut:ups`, `uptime:probe`)."
        ),
        "refs": R(
            ("Kubernetes", "https://kubernetes.io/docs/"),
            ("Vaultwarden wiki", "https://github.com/dani-garcia/vaultwarden/wiki"),
            ("Paperless-ngx docs", "https://docs.paperless-ngx.com/"),
            ("Immich docs", "https://immich.app/docs/"),
            ("AdGuard Home overview", "https://adguard.com/kb/adguard-home/overview/"),
            ("Proxmox VE docs", "https://pve.proxmox.com/wiki/Main_Page"),
            ("TrueNAS docs", "https://www.truenas.com/docs/"),
        ),
    },
    "9": {
        "app": (
            "OpenWrt, UniFi, Pi-hole, AdGuard Home, Tailscale, Cloudflare Tunnel, DNS over HTTPS resolvers, "
            "and scheduled probes via syslog, APIs, and Splunk HEC."
        ),
        "ds": (
            "Personal network telemetry (`openwrt:syslog`, `unifi:event`, `pihole:query`, `adguard:query`, "
            "`tailscale:netmap`, `cloudflared:connector`, `doh:query`, `speedtest:result`, `uptime:probe`)."
        ),
        "refs": R(
            ("OpenWrt docs", "https://openwrt.org/docs/start"),
            ("Tailscale docs", "https://tailscale.com/kb"),
            ("Cloudflare Tunnel docs", "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"),
            ("Pi-hole docs", "https://docs.pi-hole.net/"),
            ("AdGuard Home overview", "https://adguard.com/kb/adguard-home/overview/"),
            ("Ookla Speedtest CLI", "https://www.speedtest.net/apps/cli"),
            ("UniFi Network docs", "https://help.ui.com/hc/en-us/categories/6583256751383"),
        ),
    },
    "10": {
        "app": (
            "WeatherFlow Tempest, Ecowitt, PurpleAir, AirGradient, ESPHome plant sensors, aquarium controllers, "
            "and pollen feeds streamed to Splunk HEC via MQTT and scripted inputs."
        ),
        "ds": (
            "Weather and garden telemetry (`weatherflow:obs`, `ecowitt:obs`, `purpleair:aqi`, `airgradient:sensor`, "
            "`plant:sensor`, `aquarium:sensor`, `ambee:pollen`)."
        ),
        "refs": R(
            ("Tempest API", "https://weatherflow.github.io/Tempest/api/"),
            ("Ecowitt support", "https://www.ecowitt.com/support.html"),
            ("PurpleAir API", "https://api2.purpleair.com/"),
            ("AirGradient documentation", "https://www.airgradient.com/documentation/"),
            ("ESPHome", "https://esphome.io/"),
            ("Ambee pollen API", "https://www.getambee.com/api/pollen"),
        ),
    },
    "11": {
        "app": (
            "Fi collar, Petkit, Tractive, Petlibro, Litter-Robot, pet cameras, and aquarium controllers "
            "via vendor exports, Home Assistant integrations, MQTT, and Splunk HEC."
        ),
        "ds": (
            "Pet telemetry (`fi:activity`, `petkit:status`, `tractive:location`, `petlibro:feeder`, "
            "`litterrobot:cycle`, `furbo:event`, `aquarium:sensor`)."
        ),
        "refs": R(
            ("Fi support", "https://support.tryfi.com/hc/en-us"),
            ("Petkit", "https://www.petkit.com/"),
            ("Tractive", "https://tractive.com/"),
            ("Petlibro", "https://petlibro.com/"),
            ("Litter-Robot", "https://www.litter-robot.com/"),
            ("ESPHome", "https://esphome.io/"),
        ),
    },
    "12": {
        "app": (
            "Monarch Money, Copilot Money, Plaid-connected accounts, Plaid investments, and brokerage CSV exports "
            "ingested into Splunk HEC via scripted inputs."
        ),
        "ds": (
            "Personal finance telemetry (`monarch:transaction`, `copilot:transaction`, `plaid:account`, "
            "`plaid:transaction`, `plaid:investment`)."
        ),
        "refs": R(
            ("Monarch Money help", "https://help.monarchmoney.com/"),
            ("Copilot Money help", "https://help.copilot.money/"),
            ("Plaid docs", "https://plaid.com/docs/"),
            ("Portfolio Performance", "https://www.portfolio-performance.info/en/"),
        ),
    },
    "13": {
        "app": (
            "Obsidian Sync, Todoist, Toggl Track, Google Calendar / iCloud calendar exports, and task metadata "
            "ingested into Splunk HEC."
        ),
        "ds": (
            "Personal productivity telemetry (`obsidian:sync`, `obsidian:note`, `todoist:task`, "
            "`toggl:timeentry`, `calendar:freebusy`, `calendar:event`)."
        ),
        "refs": R(
            ("Obsidian Sync", "https://help.obsidian.md/sync"),
            ("Todoist REST API", "https://developer.todoist.com/rest/v2/"),
            ("Toggl Track API", "https://engineering.toggl.com/docs/"),
            ("Google Calendar freeBusy", "https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query"),
        ),
    },
    "14": {
        "app": (
            "FlightAware, OpenSky, MarineTraffic, ADS-B receivers, ABRP trip plans, toll-tag exports, "
            "and EV charging receipts forwarded to Splunk HEC."
        ),
        "ds": (
            "Travel telemetry (`adsb:aircraft`, `flightaware:flight`, `marinetraffic:vessel`, `tolltag:trip`, "
            "`abrp:trip`, `evcharger:session`, `travel:document`, `commute:trip`)."
        ),
        "refs": R(
            ("FlightAware AeroAPI", "https://www.flightaware.com/aeroapi/portal/documentation"),
            ("OpenSky REST API", "https://opensky-network.org/apidoc/rest.html"),
            ("MarineTraffic API services", "https://www.marinetraffic.com/en/p/api-services"),
            ("readsb / tar1090", "https://github.com/wiedehopf/readsb"),
            ("A Better Routeplanner", "https://abetterrouteplanner.com/"),
            ("E-ZPass Interagency Group", "https://www.e-zpassiag.com/"),
        ),
    },
    "15": {
        "app": (
            "Meater probes, Anova Precision Cooker sessions, Instant Pot logs, wine-fridge sensors, "
            "ESPHome kitchen sensors, and pantry inventory feeds via MQTT and Splunk HEC."
        ),
        "ds": (
            "Kitchen telemetry (`meater:cook`, `anova:session`, `instantpot:cook`, `kitchen:appliance`, "
            "`bbq:probe`, `pantry:item`)."
        ),
        "refs": R(
            ("MEATER", "https://meater.com/"),
            ("Anova support", "https://support.anovaculinary.com/"),
            ("Instant Pot", "https://instantpot.com/"),
            ("ESPHome", "https://esphome.io/"),
            ("Home Assistant REST sensor", "https://www.home-assistant.io/integrations/rest/"),
        ),
    },
    "16": {
        "app": (
            "Brewfather batch exports, iSpindel and Tilt hydrometers, ESPHome mash probes, keg pressure sensors, "
            "brew-fridge telemetry, and cellar climate data via MQTT and Splunk HEC."
        ),
        "ds": (
            "Brewing telemetry (`brew:batch`, `brew:fermentation`, `brew:mash`, `tilt:hydrometer`, "
            "`ispindel:reading`, `kegerator:pressure`, `kegerator:pour`, `brewfridge:compressor`, "
            "`winecellar:reading`, `tapline:clean`)."
        ),
        "refs": R(
            ("Brewfather API", "https://api.brewfather.app/"),
            ("iSpindel docs", "https://www.ispindel.de/docs/README_en.html"),
            ("Tilt Hydrometer", "https://tilthydrometer.com/"),
            ("ESPHome", "https://esphome.io/"),
        ),
    },
    "17": {
        "app": (
            "Bambu Lab printers, Prusa Connect, OctoPrint, Moonraker, LaserWeb, CNC.js, drybox sensors, "
            "and workshop telemetry via MQTT and Splunk HEC."
        ),
        "ds": (
            "Maker telemetry (`bambulab:job`, `prusaconnect:printer`, `octoprint:job`, `klipper:telemetry`, "
            "`laserweb:job`, `cnc:job`, `cnc:coolant`, `filament:spool`, `workshop:air`)."
        ),
        "refs": R(
            ("Bambu Lab wiki", "https://wiki.bambulab.com/"),
            ("Prusa Connect", "https://connect.prusa3d.com/"),
            ("OctoPrint API", "https://docs.octoprint.org/en/master/api/index.html"),
            ("Moonraker API", "https://moonraker.readthedocs.io/en/latest/web_api/"),
            ("LaserWeb", "https://github.com/LaserWeb/LaserWeb4"),
            ("CNC.js", "https://cnc.js.org/"),
        ),
    },
    "18": {
        "app": (
            "Reolink, UniFi Protect, Ring, Nest Protect, Frigate, and Home Assistant security integrations "
            "streamed to Splunk HEC via MQTT, webhooks, and vendor APIs."
        ),
        "ds": (
            "Home security telemetry (`reolink:event`, `unifiprotect:event`, `ring:event`, `nestprotect:event`, "
            "`frigate:event`, `camera:health`, `alarm:event`, `doorbell:event`)."
        ),
        "refs": R(
            ("Reolink Home Assistant integration", "https://www.home-assistant.io/integrations/reolink/"),
            ("UniFi Protect integration", "https://www.home-assistant.io/integrations/unifiprotect/"),
            ("Ring integration", "https://www.home-assistant.io/integrations/ring/"),
            ("Nest integration", "https://www.home-assistant.io/integrations/nest/"),
            ("Frigate docs", "https://docs.frigate.video/"),
        ),
    },
    "19": {
        "app": (
            "Flo by Moen, Rachio, Flume, Maytronics Dolphin, pool sensors, water softener sensors, "
            "and irrigation controllers via vendor APIs, MQTT, and Splunk HEC."
        ),
        "ds": (
            "Water telemetry (`watermeter:flow`, `flo:event`, `rachio:zone`, `maytronics:robot`, "
            "`watersoftener:status`, `pool:chemistry`, `irrigation:zone`, `waterpressure:reading`)."
        ),
        "refs": R(
            ("Flo by Moen", "https://shop.moen.com/pages/flo-smart-water-monitor-and-shutoff"),
            ("Rachio API", "https://rachio.readme.io/docs"),
            ("Flume personal API", "https://help.flumewater.com/en/articles/3457857-flume-personal-api"),
            ("Maytronics", "https://www.maytronics.com/en-us/"),
            ("OpenSprinkler API", "https://openthings.freshdesk.com/support/solutions/articles/5000821298-opensprinkler-api"),
        ),
    },
    "20": {
        "app": (
            "Raspberry Shake, Safecast, Blitzortung-compatible lightning sensors, AirGradient CO2 sensors, "
            "radon monitors, allsky cameras, and magnetometers streamed to Splunk HEC."
        ),
        "ds": (
            "Citizen-science telemetry (`seismo:reading`, `geiger:cpm`, `lightning:strike`, `airgradient:sensor`, "
            "`radon:reading`, `allsky:capture`, `magnetometer:reading`, `weatherstation:reading`)."
        ),
        "refs": R(
            ("Raspberry Shake", "https://raspberryshake.org/"),
            ("Safecast", "https://safecast.org/"),
            ("Blitzortung", "https://www.blitzortung.org/"),
            ("AirGradient documentation", "https://www.airgradient.com/documentation/"),
            ("Allsky", "https://github.com/AllSkyCamera/allsky"),
            ("RadonEye", "https://radonftlab.com/"),
        ),
    },
}


SPECS: dict[str, list[dict[str, object]]] = {
    "1": [
        G("1", "COROS Training Load Ramp Above Baseline", SPL(
            "index=personal sourcetype=coros:activity",
            "| bin _time span=1w",
            "| stats sum(training_load) as load, sum(distance_km) as distance_km by athlete _time",
            "| streamstats window=4 current=f avg(load) as baseline by athlete",
            "| where baseline>0 AND load>baseline*1.25 AND distance_km>20",
            "| sort - load",
        ), "COROS activity exports", "weekly training load against the recent COROS baseline", "overshoot weeks that often precede fatigue", "Weekly load bar chart by athlete."),
        G("1", "Wahoo Sensor Dropout by Ride", SPL(
            "index=personal sourcetype=wahoo:workout",
            "| stats sum(cadence_dropouts) as cadence_dropouts, sum(hr_dropouts) as hr_dropouts, avg(duration_min) as duration_min by workout_id head_unit",
            "| where cadence_dropouts>2 OR hr_dropouts>2",
            "| sort - cadence_dropouts - hr_dropouts",
        ), "Wahoo ELEMNT ride telemetry", "sensor stability during each recorded ride", "head units or sensors that are quietly losing data quality", "Table of rides with cadence and heart-rate dropouts."),
        G("1", "TrainerRoad Missed Workout Streak", SPL(
            "index=personal sourcetype=trainerroad:workout status!=completed",
            "| bin _time span=14d",
            "| stats count as missed_sessions by athlete _time",
            "| where missed_sessions>2",
            "| sort - missed_sessions",
        ), "TrainerRoad calendar exports", "missed-session accumulation over the last two weeks", "when a build block is slipping before fitness drops", "Two-week column chart of missed workouts per athlete."), 
        G("1", "Apple Fitness Ring Closure Dip After Travel", SPL(
            "index=personal sourcetype=applefitness:workout",
            "| bin _time span=1d",
            "| stats max(move_pct) as move_pct, max(exercise_min) as exercise_min, max(stand_pct) as stand_pct by athlete _time",
            "| where move_pct<70 OR exercise_min<20 OR stand_pct<80",
            "| sort - _time",
        ), "Apple Fitness exports", "daily ring closure after trips or disrupted routines", "travel weeks where baseline movement fell away", "Daily table of move, exercise, and stand percentages."),
        G("1", "Concept2 Interval Pace Fade", SPL(
            "index=personal sourcetype=concept2:workout piece_type=interval",
            "| stats first(avg_split_sec) as opening_split, last(avg_split_sec) as closing_split by workout_id athlete",
            "| eval fade_sec=closing_split-opening_split",
            "| where fade_sec>5",
            "| sort - fade_sec",
        ), "Concept2 Logbook workouts", "pace fade from the first interval to the final interval", "rowing sessions where endurance disappeared late", "Scatter plot of interval workouts ranked by pace fade."),
        G("1", "Open-Water Swim Pace Variability by Session", SPL(
            "index=personal sourcetype=strava:activity sport=swim",
            "| stats avg(moving_pace_sec_100m) as avg_pace, stdev(moving_pace_sec_100m) as pace_sd, max(distance_km) as distance_km by activity_id athlete",
            "| where distance_km>1 AND pace_sd>12",
            "| sort - pace_sd",
        ), "Strava swim activities", "pace stability during longer swim sessions", "days when open-water pacing became inconsistent", "Session table of swim distance, average pace, and pace deviation."),
        G("1", "Hike Elevation Gain per Moving Hour", SPL(
            "index=personal sourcetype=garmin:activity sport=hike",
            "| stats sum(elevation_gain_m) as climb_m, sum(moving_time_hr) as moving_time_hr by athlete",
            "| eval climb_per_hr=round(climb_m/moving_time_hr,1)",
            "| where moving_time_hr>0 AND climb_per_hr>500",
            "| sort - climb_per_hr",
        ), "Garmin hiking exports", "vertical climbing rate across hiking time", "exceptionally steep or overreaching hike days", "Ranked table of climb per moving hour."),
        G("1", "Ski Day Vertical Drop vs Lift Time", SPL(
            "index=personal sourcetype=garmin:activity sport=ski",
            "| bin _time span=1d",
            "| stats sum(vertical_drop_m) as vertical_drop_m, sum(lift_time_min) as lift_time_min by athlete resort _time",
            "| where vertical_drop_m>0",
            "| sort - vertical_drop_m",
        ), "Garmin ski activity exports", "how much vertical each ski day produced relative to lift time", "resort days with poor lift efficiency or standout volume", "Daily resort chart of vertical drop beside lift minutes."),
        G("1", "Rowing Stroke Rate Drift During Long Pieces", SPL(
            "index=personal sourcetype=concept2:workout distance_m>=5000",
            "| stats avg(stroke_rate_spm) as avg_spm, stdev(stroke_rate_spm) as spm_sd by workout_id athlete",
            "| where avg_spm>18 AND spm_sd>3",
            "| sort - spm_sd",
        ), "Concept2 long-piece sessions", "stroke-rate stability in rows long enough to expose pacing issues", "pieces where technique drifted under fatigue", "Table of long pieces with average stroke rate and deviation."),
        G("1", "TrainerRoad FTP Progression Stall After Build Block", SPL(
            "index=personal sourcetype=trainerroad:workout",
            "| bin _time span=8w",
            "| stats max(ftp_estimate_w) as ftp_estimate_w, count(eval(status=\"completed\")) as completed_sessions by athlete _time",
            "| streamstats current=f last(ftp_estimate_w) as previous_ftp by athlete",
            "| where completed_sessions>=10 AND previous_ftp>0 AND ftp_estimate_w<=previous_ftp",
            "| sort - _time",
        ), "TrainerRoad workout history", "FTP movement after solid blocks of completed training", "plateaus that deserve a plan change or recovery week", "Eight-week trend of completed sessions and estimated FTP."),
        G("1", "COROS Recovery Day Compliance Gap", SPL(
            "index=personal sourcetype=coros:activity",
            "| where recovery_status=\"low\" AND activity_load>0",
            "| bin _time span=1w",
            "| stats count as low_recovery_training_days by athlete _time",
            "| where low_recovery_training_days>2",
            "| sort - low_recovery_training_days",
        ), "COROS recovery guidance", "how often hard work happened on low-recovery days", "blocks where intensity ignored recovery signals", "Weekly count of low-recovery training days."),
        G("1", "Wahoo Indoor vs Outdoor Ride Mix Shift", SPL(
            "index=personal sourcetype=wahoo:workout",
            "| bin _time span=1mon",
            "| stats count(eval(environment=\"indoor\")) as indoor_sessions, count(eval(environment=\"outdoor\")) as outdoor_sessions by athlete _time",
            "| eval indoor_share=round(100*indoor_sessions/(indoor_sessions+outdoor_sessions),1)",
            "| where indoor_sessions+outdoor_sessions>=6",
            "| sort - _time",
        ), "Wahoo workout exports", "indoor versus outdoor riding balance each month", "seasonal shifts or trainer-heavy blocks that changed the mix", "Monthly stacked chart of indoor and outdoor sessions."),
        G("1", "Apple Fitness Workout-Type Diversity Drop", SPL(
            "index=personal sourcetype=applefitness:workout",
            "| bin _time span=1mon",
            "| stats dc(workout_type) as workout_types, count as sessions by athlete _time",
            "| where sessions>=10 AND workout_types<3",
            "| sort workout_types",
        ), "Apple Fitness workout exports", "variety across logged workout types", "months when routine diversity collapsed", "Monthly table of sessions versus distinct workout types."),
        G("1", "Concept2 Rest Interval Drift Beyond Plan", SPL(
            "index=personal sourcetype=concept2:workout piece_type=interval",
            "| stats avg(rest_interval_sec) as avg_rest_interval, avg(target_rest_sec) as target_rest_sec by workout_id athlete",
            "| where target_rest_sec>0 AND avg_rest_interval>target_rest_sec*1.2",
            "| sort - avg_rest_interval",
        ), "Concept2 interval sessions", "rest behavior versus the programmed recovery window", "sessions where recovery drifted away from the plan", "Comparison table of planned and actual rest intervals."),
        G("1", "Strava Segment PR Drought on Favorite Climb", SPL(
            "index=personal sourcetype=strava:activity",
            "| stats max(pr_count) as pr_count, max(days_since_last_pr) as days_since_last_pr by athlete segment_name",
            "| where pr_count=0 AND days_since_last_pr>90",
            "| sort - days_since_last_pr",
        ), "Strava segment data", "how long favorite segments have gone without a new personal record", "stale benchmarks that might signal a change in training focus", "Ranked segment list by days since the last PR."),
    ],
    "2": [
        G("2", "Eight Sleep Temperature Intervention Spike", SPL(
            "index=personal sourcetype=eightsleep:sleep",
            "| bin _time span=1d",
            "| stats sum(temp_adjustments) as temp_adjustments, avg(room_temp_c) as room_temp_c by sleeper _time",
            "| where temp_adjustments>6",
            "| sort - temp_adjustments",
        ), "Eight Sleep exports", "how often the bed had to correct temperature through the night", "sleep sessions fighting room conditions or recovery stress", "Daily chart of temperature adjustments and room temperature."), 
        G("2", "Levels Post-Meal Glucose Spike Frequency", SPL(
            "index=personal sourcetype=levels:glucose event_type=meal_window",
            "| bin _time span=1w",
            "| stats count(eval(glucose_rise_mgdl>30)) as spikes, count as meal_windows by person _time",
            "| eval spike_pct=round(100*spikes/meal_windows,1)",
            "| where meal_windows>=5 AND spike_pct>40",
            "| sort - spike_pct",
        ), "Levels CGM meal windows", "the share of meals that triggered a sharp glucose rise", "food patterns that keep creating large excursions", "Weekly spike-rate chart by person."),
        G("2", "Libre Overnight Low Glucose Window", SPL(
            "index=personal sourcetype=libre:glucose",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats min(glucose_mgdl) as overnight_low by person _time",
            "| where overnight_low<70",
            "| sort overnight_low",
        ), "Libre overnight readings", "lowest glucose values during sleeping hours", "nights with low glucose risk", "Daily overnight-low trend line."),
        G("2", "Overnight SpO2 Dip Cluster", SPL(
            "index=personal sourcetype=apple:health metric=spo2",
            "| bin _time span=1d",
            "| stats count(eval(value_pct<92)) as low_spo2_points by person _time",
            "| where low_spo2_points>3",
            "| sort - low_spo2_points",
        ), "Apple Health SpO2 exports", "clusters of oxygen-saturation dips during sleep", "repeated nighttime desaturation that warrants a closer look", "Daily count of low SpO2 readings."),
        G("2", "Garmin Body Battery Morning Floor", SPL(
            "index=personal sourcetype=garmin:bodybattery",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=5 AND hour<=9",
            "| bin _time span=1d",
            "| stats max(body_battery) as morning_body_battery by person _time",
            "| where morning_body_battery<35",
            "| sort morning_body_battery",
        ), "Garmin Body Battery exports", "how much recovery was available at the start of the day", "mornings that begin already depleted", "Daily morning body-battery table."),
        G("2", "WHOOP Recovery Mismatch With Sleep Score", SPL(
            "index=personal sourcetype=whoop:cycle",
            "| bin _time span=1d",
            "| stats avg(recovery_pct) as recovery_pct, avg(sleep_score) as sleep_score by athlete _time",
            "| where sleep_score>80 AND recovery_pct<40",
            "| sort recovery_pct",
        ), "WHOOP daily recovery", "days where sleep looked strong but recovery stayed poor", "hidden stress or illness signals that sleep duration alone missed", "Daily comparison of sleep score and recovery percentage."),
        G("2", "Dexcom Time-in-Range Below Target", SPL(
            "index=personal sourcetype=dexcom:egv",
            "| bin _time span=1d",
            "| stats count as samples, count(eval(glucose_value>=70 AND glucose_value<=180)) as in_range by person _time",
            "| eval tir_pct=round(100*in_range/samples,1)",
            "| where samples>0 AND tir_pct<70",
            "| sort tir_pct",
        ), "Dexcom CGM readings", "daily time-in-range performance", "days when glucose control slipped below target", "Daily time-in-range percentage chart."),
        G("2", "Oura Respiratory Rate Drift", SPL(
            "index=personal sourcetype=oura:daily",
            "| bin _time span=1d",
            "| stats avg(respiratory_rate) as respiratory_rate by person _time",
            "| eventstats avg(respiratory_rate) as baseline by person",
            "| where respiratory_rate>baseline+1.5",
            "| sort - respiratory_rate",
        ), "Oura daily readiness exports", "respiratory-rate movement against the longer baseline", "breathing changes that may precede illness or poor recovery", "Daily respiratory-rate line chart with baseline overlay."),
        G("2", "Long Nap Recovery Tradeoff", SPL(
            "index=personal sourcetype=apple:health metric=nap",
            "| bin _time span=1d",
            "| stats sum(nap_min) as nap_min, max(next_day_hrv) as next_day_hrv by person _time",
            "| where nap_min>90",
            "| sort - nap_min",
        ), "Apple Health nap exports", "very long daytime naps and the next-day recovery context", "patterns where long naps may be compensating for poor overnight rest", "Daily table of nap duration and next-day HRV."),
        G("2", "Eight Sleep Bed Exit Count", SPL(
            "index=personal sourcetype=eightsleep:sleep",
            "| bin _time span=1d",
            "| stats max(bed_exit_count) as bed_exit_count by sleeper _time",
            "| where bed_exit_count>3",
            "| sort - bed_exit_count",
        ), "Eight Sleep sleep summaries", "how often the bed session was interrupted", "restless nights with repeated bed exits", "Daily chart of bed exits per sleeper."),
        G("2", "Levels Late Meal Variability", SPL(
            "index=personal sourcetype=levels:glucose",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=20",
            "| bin _time span=1d",
            "| stats max(glucose_mgdl) as late_peak, min(glucose_mgdl) as late_low by person _time",
            "| eval spread=late_peak-late_low",
            "| where spread>50",
            "| sort - spread",
        ), "Levels glucose traces", "how volatile glucose became after late meals", "evening habits that create large swings", "Daily table of late-meal peak, low, and spread."),
        G("2", "Withings Weight and Body-Fat Divergence", SPL(
            "index=personal sourcetype=withings:measure metric=bodycomposition",
            "| bin _time span=30d",
            "| stats first(weight_kg) as start_weight, last(weight_kg) as end_weight, first(body_fat_pct) as start_bf, last(body_fat_pct) as end_bf by person _time",
            "| eval weight_delta=round(end_weight-start_weight,1), bf_delta=round(end_bf-start_bf,1)",
            "| where weight_delta<0 AND bf_delta>0",
            "| sort bf_delta",
        ), "Withings body-composition exports", "whether lower scale weight still came with higher body-fat percentage", "trend lines that need a closer quality check, not just scale optimism", "Monthly table of weight delta versus body-fat delta."),
        G("2", "Apple Resting HR and Walking Pace Divergence", SPL(
            "index=personal sourcetype=apple:health",
            "| bin _time span=1w",
            "| stats avg(resting_hr) as resting_hr, avg(walking_pace_sec_km) as walking_pace_sec_km by person _time",
            "| streamstats window=4 current=f avg(resting_hr) as baseline_rhr, avg(walking_pace_sec_km) as baseline_pace by person",
            "| where baseline_rhr>0 AND resting_hr>baseline_rhr+5 AND walking_pace_sec_km>baseline_pace+30",
            "| sort - _time",
        ), "Apple Health cardio metrics", "resting heart rate alongside easy walking pace", "fatigue patterns where both recovery and everyday speed worsened together", "Weekly trend of resting heart rate and walking pace."),
        G("2", "Libre Sensor Upload Gap Over Eight Hours", SPL(
            "index=personal sourcetype=libre:glucose",
            "| stats max(_time) as last_seen by sensor_id",
            "| eval hours_since=round((now()-last_seen)/3600,1)",
            "| where hours_since>8",
            "| sort - hours_since",
        ), "Libre CGM uploads", "time since each sensor last sent data", "wear or sync issues before you lose the day", "Sensor table ranked by hours since last upload."), 
        G("2", "Oura Temperature Deviation and Readiness Watch", SPL(
            "index=personal sourcetype=oura:daily",
            "| bin _time span=1d",
            "| stats avg(temp_deviation_c) as temp_deviation_c, avg(readiness_score) as readiness_score by person _time",
            "| where temp_deviation_c>0.5 AND readiness_score<70",
            "| sort - temp_deviation_c",
        ), "Oura daily readiness", "temperature deviation paired with lower readiness", "early warning days when recovery and body temperature both move the wrong way", "Daily scatter plot of temperature deviation and readiness."),
    ],
    "3": [
        G("3", "Rivian Overnight Vampire Drain at Home", SPL(
            "index=personal sourcetype=rivian:vehicle state=parked location_type=home",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats first(soc_pct) as start_soc, last(soc_pct) as end_soc by vin _time",
            "| eval overnight_loss=round(start_soc-end_soc,1)",
            "| where overnight_loss>3",
            "| sort - overnight_loss",
        ), "Rivian vehicle telemetry", "overnight battery drop while the vehicle sat parked at home", "phantom drain days before they become expensive habit", "Daily chart of overnight state-of-charge loss."),
        G("3", "ChargePoint Public Session Failure Rate", SPL(
            "index=personal sourcetype=chargepoint:session",
            "| bin _time span=1mon",
            "| stats count as sessions, count(eval(status!=\"completed\")) as failed_sessions by site_name _time",
            "| eval failed_pct=round(100*failed_sessions/sessions,1)",
            "| where sessions>=3 AND failed_pct>20",
            "| sort - failed_pct",
        ), "ChargePoint session exports", "monthly completion reliability by public charging site", "favorite chargers that keep failing in practice", "Monthly site table of completed versus failed sessions."), 
        G("3", "PlugShare Favorite Charger Rating Drop", SPL(
            "index=personal sourcetype=plugshare:checkin",
            "| stats latest(score) as current_score, earliest(score) as first_score, count as visits by station_name",
            "| eval score_delta=round(current_score-first_score,1)",
            "| where visits>=3 AND score_delta<-0.5",
            "| sort score_delta",
        ), "PlugShare station check-ins", "how favorite charging stops are trending over repeated visits", "stations whose real-world reliability has declined", "Ranked table of charger score change over time."),
        G("3", "Tire Rotation Mileage Overdue", SPL(
            "index=personal sourcetype=obd:pid metric=odometer",
            "| stats max(odometer_mi) as odometer_mi, latest(last_tire_rotation_mi) as last_tire_rotation_mi by vin",
            "| eval miles_since=round(odometer_mi-last_tire_rotation_mi,0)",
            "| where miles_since>6000",
            "| sort - miles_since",
        ), "OBD-II maintenance telemetry", "miles since the last recorded tire rotation", "vehicles drifting past a routine maintenance interval", "Table of miles since last tire rotation by VIN."),
        G("3", "Service Interval Countdown Under Five Hundred Miles", SPL(
            "index=personal sourcetype=smartcar:vehicle",
            "| stats latest(odometer_mi) as odometer_mi, latest(next_service_due_mi) as next_service_due_mi by vin",
            "| eval miles_left=round(next_service_due_mi-odometer_mi,0)",
            "| where miles_left>=0 AND miles_left<500",
            "| sort miles_left",
        ), "Smartcar vehicle data", "remaining distance before the next service interval", "cars that are about to need workshop time", "Mileage runway table to next service."),
        G("3", "Rivian Preconditioning Miss Before DC Fast Charge", SPL(
            "index=personal sourcetype=rivian:vehicle upcoming_charge_type=dc_fast",
            "| stats max(preconditioned) as preconditioned by trip_id vin",
            "| where preconditioned=0",
            "| sort trip_id",
        ), "Rivian route and charging telemetry", "whether DC fast-charge stops were reached without battery preconditioning", "road-trip sessions that left charging speed on the table", "Trip table of fast-charge stops missing preconditioning."),
        G("3", "ChargePoint Cost per kWh Outlier", SPL(
            "index=personal sourcetype=chargepoint:session",
            "| eval cost_per_kwh=round(session_cost_usd/kwh_added,2)",
            "| where kwh_added>5",
            "| eventstats avg(cost_per_kwh) as avg_cost by network_name",
            "| where cost_per_kwh>avg_cost*1.5",
            "| sort - cost_per_kwh",
        ), "ChargePoint session costs", "price paid per delivered kilowatt-hour", "expensive charging stops that distort trip budgets", "Cost-per-kWh comparison by charging network."),
        G("3", "PlugShare Low-Availability Stop Watch", SPL(
            "index=personal sourcetype=plugshare:checkin",
            "| stats avg(stalls_available) as avg_stalls_available, count as visits by station_name",
            "| where visits>=3 AND avg_stalls_available<1",
            "| sort avg_stalls_available",
        ), "PlugShare stop logs", "how often favored chargers actually had stalls available", "busy stops that rarely meet expectations", "Ranked table of average stalls available."),
        G("3", "Home and Public Charging Cost Gap", SPL(
            "index=personal sourcetype=evcharger:session",
            "| bin _time span=1mon",
            "| stats avg(eval(if(location_type=\"home\",cost_per_kwh,null()))) as home_cost_per_kwh, avg(eval(if(location_type=\"public\",cost_per_kwh,null()))) as public_cost_per_kwh by vin _time",
            "| eval cost_gap=round(public_cost_per_kwh-home_cost_per_kwh,2)",
            "| where isnotnull(home_cost_per_kwh) AND isnotnull(public_cost_per_kwh)",
            "| sort - cost_gap",
        ), "Home and public charging sessions", "the monthly spread between home and public charging prices", "how much road charging premium is really costing", "Monthly cost-gap trend by vehicle."),
        G("3", "OBD Tire Pressure Seasonal Delta", SPL(
            "index=personal sourcetype=obd:pid metric=tire_pressure",
            "| eval month=strftime(_time,\"%m\")",
            "| stats avg(front_left_psi) as fl, avg(front_right_psi) as fr, avg(rear_left_psi) as rl, avg(rear_right_psi) as rr by vin month",
            "| eval avg_psi=round((fl+fr+rl+rr)/4,1)",
            "| eventstats max(avg_psi) as peak_psi, min(avg_psi) as trough_psi by vin",
            "| eval seasonal_drop=round(peak_psi-trough_psi,1)",
            "| where seasonal_drop>5",
            "| sort - seasonal_drop",
        ), "OBD-II tire-pressure exports", "seasonal pressure spread across the year", "vehicles that need more seasonal tire attention", "Monthly tire-pressure spread by VIN."), 
        G("3", "Rivian OTA Install Duration Outlier", SPL(
            "index=personal sourcetype=rivian:vehicle event=ota_update",
            "| stats avg(duration_min) as avg_duration_min, max(duration_min) as max_duration_min by vin version",
            "| where avg_duration_min>90 OR max_duration_min>120",
            "| sort - avg_duration_min",
        ), "Rivian OTA events", "how long over-the-air installs take by version", "updates that consistently overrun normal install windows", "Version table of average and maximum OTA duration."),
        G("3", "Charge Session Dwell Time After Full", SPL(
            "index=personal sourcetype=evcharger:session",
            "| stats avg(post_charge_parked_min) as avg_dwell_min by site_name",
            "| where avg_dwell_min>30",
            "| sort - avg_dwell_min",
        ), "EV charging session exports", "how long the vehicle stayed parked after charge completion", "sites where charging etiquette or workflow is slipping", "Site ranking by post-charge dwell minutes."),
        G("3", "PlugShare Road Trip Stop Density", SPL(
            "index=personal sourcetype=plugshare:checkin trip_mode=road_trip",
            "| bin _time span=1d",
            "| stats count as charging_stops by trip_name _time",
            "| where charging_stops>4",
            "| sort - charging_stops",
        ), "PlugShare road-trip logs", "how many charging stops each road trip day required", "itineraries that were less efficient than expected", "Daily road-trip chart of charging stop count."),
        G("3", "12V Battery Voltage Sag During Wake", SPL(
            "index=personal sourcetype=obd:pid metric=12v_battery",
            "| bin _time span=1d",
            "| stats min(voltage_v) as min_voltage_v by vin _time",
            "| where min_voltage_v<12.0",
            "| sort min_voltage_v",
        ), "OBD-II 12V telemetry", "lowest auxiliary-battery voltage seen during daily wake cycles", "early hints that the low-voltage battery is weakening", "Daily minimum 12V voltage table."),
        G("3", "Departure Range Buffer Below Plan", SPL(
            "index=personal sourcetype=smartcar:vehicle",
            "| stats latest(est_range_mi) as est_range_mi, latest(planned_trip_mi) as planned_trip_mi by vin departure_id",
            "| eval range_buffer=round(est_range_mi-planned_trip_mi,0)",
            "| where range_buffer<20",
            "| sort range_buffer",
        ), "Smartcar departure planning exports", "range buffer between estimated range and the planned trip length", "days when departure planning ran too close to empty", "Departure table of planned miles versus range buffer."),
    ],
    "4": [
        G("4", "Matter Pairing Failure Rate", SPL(
            "index=personal sourcetype=matter:event event_type=commissioning",
            "| stats count as attempts, count(eval(result=\"success\")) as successes by fabric",
            "| eval success_pct=round(100*successes/attempts,1)",
            "| where attempts>=3 AND success_pct<90",
            "| sort success_pct",
        ), "Matter commissioning events", "success rate for device pairing and commissioning", "fabrics or devices that are painful to onboard", "Fabric table of Matter pairing attempts and success rate."), 
        G("4", "Thread Border Router Parent Churn", SPL(
            "index=personal sourcetype=thread:router",
            "| bin _time span=1d",
            "| stats dc(parent_id) as parent_count by endpoint _time",
            "| where parent_count>2",
            "| sort - parent_count",
        ), "Thread mesh telemetry", "how many different parents each endpoint used each day", "endpoints wandering too much around the mesh", "Daily table of parent-count churn by endpoint."),
        G("4", "Alexa Routine Execution Delay", SPL(
            "index=personal sourcetype=alexa:routine",
            "| stats avg(execution_delay_ms) as avg_delay_ms, max(execution_delay_ms) as max_delay_ms by routine_name",
            "| where avg_delay_ms>3000 OR max_delay_ms>10000",
            "| sort - avg_delay_ms",
        ), "Alexa routine logs", "delay between trigger and routine completion", "routines that feel slow or flaky in real life", "Routine table of average and peak execution delay."),
        G("4", "Google Home Action Failure Count", SPL(
            "index=personal sourcetype=googlehome:event result=error",
            "| stats count as failures by automation action_type",
            "| sort - failures",
        ), "Google Home automation events", "which actions fail most often in household automations", "voice or script actions that keep breaking", "Failure leaderboard by Google Home action type."), 
        G("4", "Matter Device Offline Flap After Firmware Update", SPL(
            "index=personal sourcetype=matter:event event_type=device_state",
            "| bin _time span=1d",
            "| stats count(eval(state=\"offline\")) as offline_events, values(firmware_version) as firmware_versions by device_id _time",
            "| where offline_events>3",
            "| sort - offline_events",
        ), "Matter device-state events", "offline flapping after firmware changes", "devices that became unstable after an update", "Daily device table of offline events and firmware version."),
        G("4", "Zigbee2MQTT Bridge Disconnect Burst", SPL(
            "index=personal sourcetype=zigbee2mqtt:bridge",
            "| bin _time span=1h",
            "| stats count(eval(event=\"disconnect\")) as disconnects by bridge_name _time",
            "| where disconnects>1",
            "| sort - disconnects",
        ), "Zigbee2MQTT bridge logs", "bridge disconnect bursts inside each hour", "backhaul or host issues affecting many devices at once", "Hourly chart of Zigbee2MQTT disconnects."),
        G("4", "Home Assistant Matter Command Retry Hotspot", SPL(
            "index=personal sourcetype=homeassistant:event integration=matter event_type=service_call",
            "| stats avg(retry_count) as avg_retry_count, count as commands by entity_id",
            "| where commands>=5 AND avg_retry_count>1",
            "| sort - avg_retry_count",
        ), "Home Assistant Matter service calls", "how often Matter commands had to be retried", "entities whose control path is degrading", "Entity table of command volume and average retries."),
        G("4", "Thread Battery Endpoint Silent for Twelve Hours", SPL(
            "index=personal sourcetype=thread:router",
            "| stats max(_time) as last_seen by endpoint",
            "| eval hours_since=round((now()-last_seen)/3600,1)",
            "| where hours_since>12",
            "| sort - hours_since",
        ), "Thread endpoint telemetry", "how long battery-powered endpoints have been silent", "devices that may have died or fallen off the mesh", "Endpoint table of hours since last update."),
        G("4", "Alexa Duplicate Routine Execution", SPL(
            "index=personal sourcetype=alexa:routine",
            "| bin _time span=5m",
            "| stats count as routine_runs by routine_name trigger_id _time",
            "| where routine_runs>1",
            "| sort - routine_runs",
        ), "Alexa routine triggers", "multiple executions from the same trigger window", "duplicate routine runs that annoy the household", "Five-minute bucket table of duplicate routine executions."),
        G("4", "Google Home Presence State Mismatch", SPL(
            "index=personal sourcetype=googlehome:event event_type=presence_sync",
            "| bin _time span=1d",
            "| stats dc(presence_state) as presence_states, count as updates by person _time",
            "| where updates>2 AND presence_states>1",
            "| sort - updates",
        ), "Google Home presence sync events", "days where household presence bounced between conflicting states", "presence automations that are likely to misfire", "Daily person table of updates and distinct states."),
        G("4", "Matter Firmware Lag Inventory", SPL(
            "index=personal sourcetype=matter:event",
            "| stats latest(firmware_version) as firmware_version by device_model device_id",
            "| eventstats dc(firmware_version) as firmware_variants by device_model",
            "| where firmware_variants>1",
            "| sort - firmware_variants",
        ), "Matter inventory events", "firmware skew inside the same device model", "households where upgrades did not land consistently", "Inventory table of firmware variants by model."),
        G("4", "Automation Trace Error Summary", SPL(
            "index=personal sourcetype=homeassistant:event event_type=automation_trace",
            "| where trace_result=\"error\"",
            "| stats count as trace_errors by automation",
            "| sort - trace_errors",
        ), "Home Assistant automation traces", "which automations are ending in trace errors", "flows that need debugging before they fail silently", "Automation error leaderboard from trace results."), 
        G("4", "Google Home Script Editor Latency", SPL(
            "index=personal sourcetype=googlehome:event source=script_editor",
            "| stats avg(latency_ms) as avg_latency_ms, perc95(latency_ms) as p95_latency_ms by household",
            "| where p95_latency_ms>5000",
            "| sort - p95_latency_ms",
        ), "Google Home script-editor runs", "household automation latency at the slow tail", "scripted actions that feel noticeably delayed", "Household table of average and p95 latency."),
        G("4", "Thread Border Router Packet Loss", SPL(
            "index=personal sourcetype=thread:router",
            "| stats avg(packet_loss_pct) as avg_packet_loss_pct, max(packet_loss_pct) as max_packet_loss_pct by border_router",
            "| where avg_packet_loss_pct>2 OR max_packet_loss_pct>5",
            "| sort - avg_packet_loss_pct",
        ), "Thread border-router telemetry", "mesh packet loss at the router edge", "routers that are introducing reliability problems", "Border-router table of average and max packet loss."),
        G("4", "Matter Command Round-Trip Outlier", SPL(
            "index=personal sourcetype=matter:event event_type=command",
            "| stats avg(round_trip_ms) as avg_round_trip_ms, max(round_trip_ms) as max_round_trip_ms by cluster command_name",
            "| where avg_round_trip_ms>1500 OR max_round_trip_ms>5000",
            "| sort - avg_round_trip_ms",
        ), "Matter command telemetry", "round-trip time by cluster and command", "commands that are much slower than users expect", "Cluster and command table of average round-trip latency."),
    ],
    "5": [
        G("5", "Aqara Leak Sensor Check-In Gap", SPL(
            "index=personal sourcetype=aqara:device device_class=leak",
            "| stats max(_time) as last_seen by device",
            "| eval hours_since=round((now()-last_seen)/3600,1)",
            "| where hours_since>24",
            "| sort - hours_since",
        ), "Aqara leak-sensor telemetry", "time since each leak sensor last checked in", "silent water sensors before they matter", "Leak-sensor table ranked by hours since last update."), 
        G("5", "IKEA Tradfri Remote Battery Drain", SPL(
            "index=personal sourcetype=tradfri:device device_class=remote",
            "| sort 0 device _time",
            "| streamstats current=f last(battery_pct) as prev_battery_pct by device",
            "| eval battery_drop=prev_battery_pct-battery_pct",
            "| stats sum(battery_drop) as total_battery_drop by device",
            "| where total_battery_drop>10",
            "| sort - total_battery_drop",
        ), "IKEA Tradfri remote reports", "which remotes are losing battery faster than expected", "controls that will become flaky sooner than they should", "Remote table of accumulated battery drop."),
        G("5", "LIFX Wi-Fi Reconnect Flap", SPL(
            "index=personal sourcetype=lifx:state event=wifi_reconnect",
            "| bin _time span=1d",
            "| stats count as reconnects by bulb _time",
            "| where reconnects>3",
            "| sort - reconnects",
        ), "LIFX connectivity events", "how often bulbs are dropping and rejoining Wi-Fi", "lighting devices that are unstable on the network", "Daily bulb chart of reconnect counts."),
        G("5", "Nanoleaf Scene Activation Latency", SPL(
            "index=personal sourcetype=nanoleaf:scene",
            "| stats avg(apply_ms) as avg_apply_ms, max(apply_ms) as max_apply_ms by scene",
            "| where avg_apply_ms>1500 OR max_apply_ms>4000",
            "| sort - avg_apply_ms",
        ), "Nanoleaf scene events", "how long scenes take to apply after activation", "visual routines that feel sluggish", "Scene table of average and maximum apply latency."),
        G("5", "Blind Motor Calibration Drift", SPL(
            "index=personal sourcetype=blindmotor:state",
            "| stats avg(position_error_pct) as avg_position_error_pct, max(position_error_pct) as max_position_error_pct by blind",
            "| where avg_position_error_pct>5 OR max_position_error_pct>10",
            "| sort - avg_position_error_pct",
        ), "Smart blind motor telemetry", "how far blind positions drift from their intended state", "motors that need recalibration before automations go wrong", "Blind table of average and worst position error."),
        G("5", "Aqara Vibration Sensor False-Trip Cluster", SPL(
            "index=personal sourcetype=aqara:device device_class=vibration",
            "| bin _time span=1h",
            "| stats count as vibration_events by device _time",
            "| where vibration_events>10",
            "| sort - vibration_events",
        ), "Aqara vibration sensors", "bursts of vibration events inside short windows", "false alarms or noisy placements that need cleanup", "Hourly table of vibration-event bursts."), 
        G("5", "IKEA Shortcut Button Unused for Thirty Days", SPL(
            "index=personal sourcetype=tradfri:device device_class=button",
            "| stats max(_time) as last_used by device",
            "| eval days_since=round((now()-last_used)/86400,1)",
            "| where days_since>30",
            "| sort - days_since",
        ), "IKEA button events", "how long shortcut buttons have gone unused", "devices or workflows that are no longer earning their keep", "Shortcut-button table by days since last use."),
        G("5", "LIFX Firmware Skew by Group", SPL(
            "index=personal sourcetype=lifx:state",
            "| stats latest(firmware_version) as firmware_version by group bulb",
            "| eventstats dc(firmware_version) as firmware_variants by group",
            "| where firmware_variants>1",
            "| sort - firmware_variants",
        ), "LIFX bulb state", "firmware skew inside each lighting group", "partial upgrades that complicate troubleshooting", "Group inventory of LIFX firmware variants."),
        G("5", "Nanoleaf Unreachable Panel Count", SPL(
            "index=personal sourcetype=nanoleaf:scene event=panel_status",
            "| stats count(eval(status!=\"online\")) as unreachable_reports by controller",
            "| where unreachable_reports>0",
            "| sort - unreachable_reports",
        ), "Nanoleaf panel health", "how often controllers report unreachable panels", "panel failures before a scene looks obviously broken", "Controller table of unreachable-panel reports."),
        G("5", "Blind Motor Sunset Automation Miss", SPL(
            "index=personal sourcetype=blindmotor:state",
            "| where automation_name=\"sunset_close\"",
            "| bin _time span=1d",
            "| stats count(eval(result=\"missed\")) as missed_closes by blind _time",
            "| where missed_closes>0",
            "| sort - missed_closes",
        ), "Blind sunset-close events", "whether sunset automations actually finished as planned", "missed shade closes that leave rooms exposed or hot", "Daily table of missed sunset-close automations."),
        G("5", "Aqara Door Sensor Overnight Open Alert", SPL(
            "index=personal sourcetype=aqara:device device_class=contact state=open",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=23 OR hour<5",
            "| bin _time span=1d",
            "| stats count as overnight_opens by device _time",
            "| where overnight_opens>0",
            "| sort - overnight_opens",
        ), "Aqara door-contact events", "door openings during overnight quiet hours", "unexpected night access or forgotten doors", "Daily overnight-open summary by sensor."), 
        G("5", "IKEA Tradfri Outlet Unexpected Overnight Load", SPL(
            "index=personal sourcetype=tradfri:device device_class=outlet",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<5",
            "| stats avg(power_w) as avg_power_w by outlet",
            "| where avg_power_w>40",
            "| sort - avg_power_w",
        ), "Tradfri outlet power telemetry", "overnight power draw on smart outlets that should be quiet", "devices silently chewing through power overnight", "Outlet table of average overnight load."),
        G("5", "LIFX Brightness Cap After Restore", SPL(
            "index=personal sourcetype=lifx:state event=power_restore",
            "| stats avg(brightness_pct) as avg_brightness_pct by bulb",
            "| where avg_brightness_pct<70",
            "| sort avg_brightness_pct",
        ), "LIFX power-restore events", "brightness level after power returns", "bulbs coming back dimmer than users expect", "Bulb table of average restore brightness."),
        G("5", "Nanoleaf Scene Usage Leaderboard by Week", SPL(
            "index=personal sourcetype=nanoleaf:scene event=scene_applied",
            "| bin _time span=1w",
            "| stats count as activations by scene _time",
            "| sort - activations",
        ), "Nanoleaf scene activations", "which scenes actually get used each week", "stale scenes that can probably be retired", "Weekly leaderboard of scene activations."),
        G("5", "Paired Shade Open-Close Asymmetry", SPL(
            "index=personal sourcetype=blindmotor:state",
            "| stats avg(travel_time_sec) as avg_travel_time_sec by pair_id blind",
            "| eventstats max(avg_travel_time_sec) as slowest_blind, min(avg_travel_time_sec) as fastest_blind by pair_id",
            "| eval travel_gap=round(slowest_blind-fastest_blind,1)",
            "| where travel_gap>4",
            "| sort - travel_gap",
        ), "Paired blind motor telemetry", "timing mismatch between shades that should move together", "paired blinds drifting far enough to be visually obvious", "Pair table of slowest and fastest travel times."),
    ],
    "6": [
        G("6", "Powerwall Backup-Test Reserve Shortfall", SPL(
            "index=personal sourcetype=powerwall:aggregate event=backup_test",
            "| stats min(battery_soc_pct) as min_battery_soc_pct by site_name test_id",
            "| where min_battery_soc_pct<30",
            "| sort min_battery_soc_pct",
        ), "Tesla Powerwall backup tests", "lowest battery reserve reached during backup exercises", "tests that fell closer to empty than planned", "Backup-test table of minimum battery reserve."),
        G("6", "Enphase Microinverter Offline Wave", SPL(
            "index=personal sourcetype=enphase:production",
            "| bin _time span=1h",
            "| stats dc(eval(if(status=\"offline\",inverter_serial,null()))) as offline_inverters by site _time",
            "| where offline_inverters>1",
            "| sort - offline_inverters",
        ), "Enphase production telemetry", "hours where multiple microinverters were offline together", "site-wide inverter issues before they turn into yield loss", "Hourly count of offline microinverters."),
        G("6", "Sense Always-On Jump", SPL(
            "index=personal sourcetype=sense:device",
            "| bin _time span=1w",
            "| stats avg(always_on_w) as always_on_w by home _time",
            "| streamstats window=4 current=f avg(always_on_w) as baseline_w by home",
            "| where baseline_w>0 AND always_on_w>baseline_w*1.15",
            "| sort - always_on_w",
        ), "Sense always-on metrics", "growth in the home's baseline power draw", "new hidden loads that permanently raised consumption", "Weekly always-on trend by home."),
        G("6", "Time-of-Use Import Cost by Tariff Window", SPL(
            "index=personal sourcetype=dsmr:telegram",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| eval tariff_window=case(hour>=16 AND hour<21,\"peak\",hour>=21 OR hour<7,\"offpeak\",true(),\"shoulder\")",
            "| bin _time span=1d",
            "| stats sum(import_kwh) as import_kwh by tariff_window _time",
            "| sort - _time tariff_window",
        ), "DSMR smart-meter telemetry", "daily import broken out by tariff window", "when expensive windows are carrying too much load", "Daily tariff-window chart of imported kWh."),
        G("6", "Solar Export Curtailment Day", SPL(
            "index=personal sourcetype=powerwall:aggregate",
            "| where export_limited=1",
            "| bin _time span=1d",
            "| stats sum(solar_kw) as limited_solar_kw by _time",
            "| where limited_solar_kw>0",
            "| sort - limited_solar_kw",
        ), "Powerwall site exports", "days where solar production was export-limited", "curtailment that left energy on the roof", "Daily chart of export-limited solar production."),
        G("6", "Powerwall Grid Charge Outside Cheap Window", SPL(
            "index=personal sourcetype=powerwall:aggregate",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where battery_from_grid_kwh>0 AND NOT (hour>=0 AND hour<7)",
            "| bin _time span=1d",
            "| stats sum(battery_from_grid_kwh) as off_window_grid_charge_kwh by _time",
            "| where off_window_grid_charge_kwh>0",
            "| sort - off_window_grid_charge_kwh",
        ), "Powerwall charging telemetry", "grid charging that happened outside the cheap window", "battery schedules that are costing too much", "Daily chart of off-window grid charge."),
        G("6", "Enphase Consumption CT Mismatch", SPL(
            "index=personal sourcetype=enphase:production",
            "| stats avg(consumption_ct_w) as ct_w, avg(home_consumption_w) as home_w by site",
            "| eval pct_diff=round(100*abs(ct_w-home_w)/home_w,1)",
            "| where home_w>0 AND pct_diff>10",
            "| sort - pct_diff",
        ), "Enphase site telemetry", "disagreement between CT-derived and reported home consumption", "sensor or wiring problems that warp downstream dashboards", "Site table of CT mismatch percentage."),
        G("6", "Sense Unassigned Load Growth", SPL(
            "index=personal sourcetype=sense:device device_name=\"Other\"",
            "| bin _time span=1w",
            "| stats avg(power_w) as other_power_w by home _time",
            "| streamstats window=4 current=f avg(other_power_w) as baseline_w by home",
            "| where baseline_w>0 AND other_power_w>baseline_w*1.2",
            "| sort - other_power_w",
        ), "Sense device detections", "the share of power still hidden in unassigned loads", "homes where device detection has drifted backwards", "Weekly trend of Sense Other load."),
        G("6", "DSMR Peak Demand Day Ranking", SPL(
            "index=personal sourcetype=dsmr:telegram",
            "| bin _time span=1d",
            "| stats max(import_kw) as peak_import_kw by _time",
            "| sort - peak_import_kw",
        ), "DSMR import telemetry", "which days hit the highest grid-demand peaks", "demand spikes that drive bills or future capacity issues", "Ranked daily peak-demand table."),
        G("6", "Emporia EV Circuit Overnight Load Share", SPL(
            "index=personal sourcetype=emporia:circuit",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats sum(eval(if(match(circuit,\"(?i)ev\"),kwh,0))) as ev_kwh, sum(kwh) as total_kwh by _time",
            "| eval ev_share_pct=round(100*ev_kwh/total_kwh,1)",
            "| where total_kwh>0",
            "| sort - _time",
        ), "Emporia circuit telemetry", "what share of overnight consumption is coming from EV charging", "homes where vehicle charging dominates night load", "Daily chart of EV share of overnight kWh."),
        G("6", "Powerwall Storm-Watch Early Exit", SPL(
            "index=personal sourcetype=powerwall:aggregate mode=storm_watch",
            "| sort 0 site_name _time",
            "| streamstats current=f last(mode) as prev_mode by site_name",
            "| eval exited=if(prev_mode=\"storm_watch\" AND mode!=\"storm_watch\",1,0)",
            "| stats count(eval(exited=1)) as storm_watch_exits by site_name",
            "| where storm_watch_exits>0",
            "| sort - storm_watch_exits",
        ), "Powerwall mode changes", "unexpected exits from storm-watch mode", "reserve behavior that may not match severe-weather expectations", "Site table of storm-watch exits."),
        G("6", "Enphase Phase Imbalance Alert", SPL(
            "index=personal sourcetype=enphase:production",
            "| stats avg(phase_a_w) as phase_a_w, avg(phase_b_w) as phase_b_w, avg(phase_c_w) as phase_c_w by site",
            "| eval spread_ab=abs(phase_a_w-phase_b_w), spread_bc=abs(phase_b_w-phase_c_w), spread_ac=abs(phase_a_w-phase_c_w)",
            "| eval phase_gap=round(if(spread_ab>spread_bc AND spread_ab>spread_ac,spread_ab,if(spread_bc>spread_ac,spread_bc,spread_ac)),1)",
            "| where phase_gap>500",
            "| sort - phase_gap",
        ), "Enphase multi-phase telemetry", "how far phase loads drift apart", "panel or wiring issues that leave one phase unusually heavy", "Site table of maximum phase gap."),
        G("6", "Utility Tariff Season Rollover Missing", SPL(
            "index=personal sourcetype=utilityrate:tariff",
            "| stats max(_time) as last_update by provider season_name",
            "| eval days_since=round((now()-last_update)/86400,1)",
            "| where days_since>45",
            "| sort - days_since",
        ), "Utility tariff exports", "whether seasonal tariff tables have been refreshed recently", "stale rate schedules before cost reporting drifts", "Provider table of days since tariff update."),
        G("6", "Sense Runtime Cost Leaderboard by Device", SPL(
            "index=personal sourcetype=sense:device",
            "| bin _time span=1mon",
            "| stats sum(kwh) as kwh by device_name _time",
            "| eval est_cost=round(kwh*0.30,2)",
            "| sort - est_cost",
        ), "Sense device energy data", "which appliances are costing the most to run each month", "top contributors to the power bill", "Monthly device leaderboard by estimated cost."),
        G("6", "Self-Powered Day by Month", SPL(
            "index=personal sourcetype=powerwall:aggregate",
            "| bin _time span=1d",
            "| stats sum(eval(if(grid_kw>0,grid_kw,0))) as import_kw by _time",
            "| eval self_powered_day=if(import_kw<15,1,0)",
            "| where self_powered_day=1",
            "| sort - _time",
        ), "Powerwall aggregate telemetry", "which days stayed almost entirely self-powered", "months that are quietly improving energy independence", "Daily table of near self-powered days."),
    ],
    "7": [
        G("7", "Jellyfin Transcode Hotspot by Client", SPL(
            "index=personal sourcetype=jellyfin:activity",
            "| stats count(eval(transcode=\"true\")) as transcodes, count as sessions by client",
            "| eval transcode_pct=round(100*transcodes/sessions,1)",
            "| where sessions>=5 AND transcode_pct>50",
            "| sort - transcode_pct",
        ), "Jellyfin playback activity", "how often each client forces a transcode", "devices creating unnecessary media-server load", "Client table of transcode rate."),
        G("7", "Emby Library Scan Failure Count", SPL(
            "index=personal sourcetype=emby:session event=library_scan",
            "| stats count(eval(result=\"error\")) as failures by library",
            "| where failures>0",
            "| sort - failures",
        ), "Emby library scans", "which libraries are failing to scan cleanly", "content sources that need repair before metadata goes stale", "Failure leaderboard by Emby library."), 
        G("7", "Xbox Game Pass Playtime Drift", SPL(
            "index=personal sourcetype=xbox:activity",
            "| bin _time span=1mon",
            "| stats sum(minutes_played) as minutes_played by title _time",
            "| streamstats current=f avg(minutes_played) as baseline_minutes by title",
            "| where baseline_minutes>0 AND minutes_played<baseline_minutes*0.5",
            "| sort minutes_played",
        ), "Xbox activity exports", "monthly playtime against the recent title baseline", "games that fell out of rotation after install", "Monthly title chart of playtime versus baseline."),
        G("7", "Nintendo Switch Docked Share by Month", SPL(
            "index=personal sourcetype=nintendo:play",
            "| bin _time span=1mon",
            "| stats count(eval(mode=\"docked\")) as docked_sessions, count as total_sessions by player _time",
            "| eval docked_share_pct=round(100*docked_sessions/total_sessions,1)",
            "| where total_sessions>=5",
            "| sort - _time",
        ), "Nintendo play exports", "how much of Switch time was docked versus handheld", "household play-style changes across the month", "Monthly docked-share chart by player."),
        G("7", "Steam Deck Offline Sync Gap", SPL(
            "index=personal sourcetype=steamdeck:session",
            "| stats max(_time) as last_sync by device",
            "| eval hours_since=round((now()-last_sync)/3600,1)",
            "| where hours_since>24",
            "| sort - hours_since",
        ), "Steam Deck session sync logs", "how long devices have gone without syncing sessions", "offline-play gaps before progress or telemetry goes missing", "Device table of hours since last sync."),
        G("7", "AntennaPod Unplayed Queue Growth", SPL(
            "index=personal sourcetype=antennapod:episode",
            "| bin _time span=1w",
            "| stats count(eval(state=\"unplayed\")) as unplayed_episodes by podcast _time",
            "| streamstats current=f avg(unplayed_episodes) as baseline_unplayed by podcast",
            "| where baseline_unplayed>0 AND unplayed_episodes>baseline_unplayed*1.5",
            "| sort - unplayed_episodes",
        ), "AntennaPod episode exports", "backlog growth in unplayed podcast episodes", "shows that are piling up faster than listening time allows", "Weekly podcast backlog chart."),
        G("7", "Jellyfin Remote Stream Buffering Spike", SPL(
            "index=personal sourcetype=jellyfin:activity",
            "| stats avg(buffer_events) as avg_buffer_events, max(buffer_events) as max_buffer_events by client",
            "| where avg_buffer_events>2 OR max_buffer_events>5",
            "| sort - avg_buffer_events",
        ), "Jellyfin remote stream logs", "buffering frequency by playback client", "remote clients suffering visible playback issues", "Client table of average and maximum buffering events."),
        G("7", "Xbox Achievement Drought After Install", SPL(
            "index=personal sourcetype=xbox:activity",
            "| stats max(days_since_install) as days_since_install, max(days_since_last_achievement) as days_since_last_achievement by title",
            "| where days_since_install>30 AND days_since_last_achievement>14",
            "| sort - days_since_last_achievement",
        ), "Xbox achievement exports", "how long installed games have gone without progress moments", "games that were started but then abandoned", "Title table of days since last achievement."),
        G("7", "Nintendo Update Download Size Hotspot", SPL(
            "index=personal sourcetype=nintendo:play event=update_download",
            "| stats sum(download_gb) as update_download_gb by title",
            "| where update_download_gb>5",
            "| sort - update_download_gb",
        ), "Nintendo update telemetry", "which titles are consuming the most bandwidth for updates", "games with outsized patch demand", "Title leaderboard by downloaded update size."),
        G("7", "Steam Deck Suspend Drain Watch", SPL(
            "index=personal sourcetype=steamdeck:session event=suspend",
            "| stats avg(suspend_battery_loss_pct) as avg_loss_pct, max(suspend_battery_loss_pct) as max_loss_pct by device",
            "| where avg_loss_pct>5 OR max_loss_pct>10",
            "| sort - avg_loss_pct",
        ), "Steam Deck suspend telemetry", "battery drain while devices are supposed to be sleeping", "suspend behavior that eats away at portability", "Device table of average and max suspend battery loss."),
        G("7", "Emby Concurrent Stream Ceiling", SPL(
            "index=personal sourcetype=emby:session event=playback",
            "| bin _time span=10m",
            "| stats dc(session_id) as concurrent_streams by server _time",
            "| where concurrent_streams>3",
            "| sort - concurrent_streams",
        ), "Emby playback sessions", "server concurrency during busy playback windows", "times when household streaming nears the server's limit", "Ten-minute chart of concurrent Emby streams."),
        G("7", "AntennaPod Late-Night Listening Trend", SPL(
            "index=personal sourcetype=antennapod:episode state=played",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=23 OR hour<2",
            "| bin _time span=1w",
            "| stats sum(listened_min) as late_night_minutes by podcast _time",
            "| sort - late_night_minutes",
        ), "AntennaPod play history", "how much podcast listening happens late at night", "shows most associated with sleep-time listening", "Weekly podcast chart of late-night minutes."),
        G("7", "Tautulli Client Error Rate by App", SPL(
            "index=personal sourcetype=tautulli:play",
            "| stats count as plays, sum(eval(error=\"true\")) as errors by client_app",
            "| eval error_pct=round(100*errors/plays,1)",
            "| where plays>=5 AND error_pct>5",
            "| sort - error_pct",
        ), "Tautulli playback telemetry", "playback error rate for each client app", "apps that keep breaking playback sessions", "Client-app error-rate table."),
        G("7", "Steam Wishlist Purchase Conversion", SPL(
            "index=personal sourcetype=steam:player event=wishlist",
            "| stats count(eval(status=\"purchased\")) as purchased_titles, count as total_titles by category",
            "| eval conversion_pct=round(100*purchased_titles/total_titles,1)",
            "| where total_titles>0",
            "| sort - conversion_pct",
        ), "Steam wishlist exports", "how many wishlisted games actually turned into purchases", "categories that convert better than others during sales", "Category table of wishlist conversion percentage."),
        G("7", "RetroArch Session Time by Core", SPL(
            "index=personal sourcetype=retroarch:session",
            "| bin _time span=1w",
            "| stats sum(session_min) as session_minutes by core _time",
            "| sort - session_minutes",
        ), "RetroArch session logs", "weekly playtime across emulation cores", "which retro systems are actually getting attention", "Weekly leaderboard of RetroArch core playtime."),
    ],
    "8": [
        G("8", "Kubernetes Pod Restart Hotspot", SPL(
            "index=personal sourcetype=kubernetes:pod",
            "| stats sum(restart_count) as restart_count by namespace pod",
            "| where restart_count>3",
            "| sort - restart_count",
        ), "Kubernetes pod metrics", "which pods are restarting repeatedly", "services that are unstable inside the homelab cluster", "Namespace and pod table of restart counts."), 
        G("8", "Kubernetes PVC Free Space Under Fifteen Percent", SPL(
            "index=personal sourcetype=kubernetes:pod metric=pvc",
            "| stats latest(free_pct) as free_pct by pvc namespace",
            "| where free_pct<15",
            "| sort free_pct",
        ), "Kubernetes persistent-volume metrics", "which PVCs are closest to running out of space", "storage that needs extension before workloads fail", "PVC table of remaining free percentage."),
        G("8", "Vaultwarden Failed Login Burst", SPL(
            "index=personal sourcetype=vaultwarden:event event=login result=failed",
            "| bin _time span=1h",
            "| stats count as failed_logins by ip _time",
            "| where failed_logins>5",
            "| sort - failed_logins",
        ), "Vaultwarden login events", "failed-login bursts by source IP", "password-manager probing or automation mistakes", "Hourly table of failed logins by IP."),
        G("8", "Paperless OCR Queue Backlog", SPL(
            "index=personal sourcetype=paperless:document",
            "| stats count(eval(status=\"queued\")) as queued_docs, count(eval(status=\"processing\")) as processing_docs by consumer",
            "| where queued_docs>20 OR processing_docs>5",
            "| sort - queued_docs",
        ), "Paperless-ngx ingestion events", "how far OCR and import queues are backing up", "document backlogs before scanning confidence drops", "Consumer table of queued and processing documents."),
        G("8", "Immich ML Job Queue Depth", SPL(
            "index=personal sourcetype=immich:job",
            "| stats count(eval(status=\"queued\")) as queued_jobs by job_type",
            "| where queued_jobs>10",
            "| sort - queued_jobs",
        ), "Immich job telemetry", "queued machine-learning jobs by job type", "photo-processing backlogs that delay search and face grouping", "Job-type table of queued Immich work."),
        G("8", "AdGuard Upstream Failure Share", SPL(
            "index=personal sourcetype=adguard:query",
            "| stats count as queries, count(eval(status=\"upstream_error\")) as upstream_errors by upstream",
            "| eval error_pct=round(100*upstream_errors/queries,1)",
            "| where queries>=50 AND error_pct>1",
            "| sort - error_pct",
        ), "AdGuard Home query logs", "upstream failure rate by resolver", "DNS providers that are hurting resolution quality", "Resolver table of query volume and upstream errors."),
        G("8", "Kubernetes Node NotReady Minutes", SPL(
            "index=personal sourcetype=kubernetes:pod metric=node",
            "| bin _time span=1d",
            "| stats sum(eval(status=\"NotReady\")) as notready_samples by node _time",
            "| where notready_samples>0",
            "| sort - notready_samples",
        ), "Kubernetes node status", "how often nodes fell into NotReady state", "node health problems before workloads migrate unexpectedly", "Daily node table of NotReady samples."),
        G("8", "Vaultwarden Admin Token Age", SPL(
            "index=personal sourcetype=vaultwarden:event event=admin_token",
            "| stats latest(rotation_age_days) as rotation_age_days by instance",
            "| where rotation_age_days>30",
            "| sort - rotation_age_days",
        ), "Vaultwarden admin-token events", "how long the admin token has gone without rotation", "instances drifting beyond a comfortable secret-rotation age", "Instance table of admin-token age."),
        G("8", "Paperless Untagged Document Growth", SPL(
            "index=personal sourcetype=paperless:document",
            "| bin _time span=1w",
            "| stats count(eval(tag_count=0)) as untagged_docs by _time",
            "| sort - _time",
        ), "Paperless document metadata", "weekly growth in imported files with no tags", "searchability problems that accumulate quietly", "Weekly line chart of untagged documents."),
        G("8", "Immich External Library Scan Duration", SPL(
            "index=personal sourcetype=immich:job job_type=library_scan",
            "| stats avg(duration_min) as avg_duration_min, max(duration_min) as max_duration_min by library",
            "| where avg_duration_min>30 OR max_duration_min>60",
            "| sort - avg_duration_min",
        ), "Immich library scans", "how long external-library scans are taking", "libraries that have become slow to index", "Library table of average and maximum scan duration."),
        G("8", "Ingress Certificate Expiry Watch", SPL(
            "index=personal sourcetype=uptime:probe",
            "| stats latest(tls_days_left) as tls_days_left by service",
            "| where match(service,\"ingress|traefik|nginx\") AND tls_days_left>=0 AND tls_days_left<21",
            "| sort tls_days_left",
        ), "TLS uptime probes", "remaining certificate runway on homelab ingress points", "proxy certificates that will soon expire", "Ingress table of TLS days remaining."),
        G("8", "AdGuard Top Blocked Client Drift", SPL(
            "index=personal sourcetype=adguard:query blocked=\"true\"",
            "| bin _time span=1w",
            "| stats count as blocked_queries by client _time",
            "| eventstats avg(blocked_queries) as baseline_blocked_queries by client",
            "| where baseline_blocked_queries>0 AND blocked_queries>baseline_blocked_queries*1.5",
            "| sort - blocked_queries",
        ), "AdGuard blocked-query logs", "weekly growth in blocked requests from each client", "devices that suddenly started talking to noisier endpoints", "Weekly blocked-query chart by client."),
        G("8", "Proxmox Backup Window Overrun", SPL(
            "index=personal sourcetype=proxmox:metric event=backup",
            "| stats avg(duration_min) as avg_duration_min, max(duration_min) as max_duration_min by job",
            "| where avg_duration_min>120 OR max_duration_min>240",
            "| sort - avg_duration_min",
        ), "Proxmox backup jobs", "backup duration compared with expected maintenance windows", "jobs that are expanding enough to threaten the schedule", "Backup-job table of average and max duration."),
        G("8", "TrueNAS Replication Failure Count", SPL(
            "index=personal sourcetype=truenas:pool event=replication",
            "| stats count(eval(status!=\"success\")) as failed_replications by task",
            "| where failed_replications>0",
            "| sort - failed_replications",
        ), "TrueNAS replication events", "which replication tasks are failing most often", "storage replication paths that need attention", "Replication-task failure leaderboard."),
        G("8", "Immich Face Detection Error Summary", SPL(
            "index=personal sourcetype=immich:job job_type=face_detection",
            "| stats count(eval(status=\"error\")) as face_detection_errors by library",
            "| where face_detection_errors>0",
            "| sort - face_detection_errors",
        ), "Immich face-detection jobs", "error totals from face-processing pipelines", "photo libraries that need index or model cleanup", "Library table of face-detection errors."),
    ],
    "9": [
        G("9", "OpenWrt WAN Failover Activation Count", SPL(
            "index=personal sourcetype=openwrt:syslog",
            "| where match(message,\"(?i)failover|wan backup\")",
            "| bin _time span=1d",
            "| stats count as failovers by router _time",
            "| where failovers>0",
            "| sort - failovers",
        ), "OpenWrt syslog", "days where WAN failover actually had to activate", "internet instability before it becomes a forgotten annoyance", "Daily failover count by router."),
        G("9", "OpenWrt SQM Latency Under Load", SPL(
            "index=personal sourcetype=openwrt:syslog event=sqm_test",
            "| stats avg(latency_under_load_ms) as avg_latency_ms, max(latency_under_load_ms) as max_latency_ms by router",
            "| where avg_latency_ms>50 OR max_latency_ms>100",
            "| sort - avg_latency_ms",
        ), "OpenWrt SQM measurements", "latency while the link is under load", "bufferbloat returning despite shaping", "Router table of average and max under-load latency."),
        G("9", "Tailscale DERP Relay Usage Spike", SPL(
            "index=personal sourcetype=tailscale:netmap",
            "| bin _time span=1d",
            "| stats count(eval(path_type=\"derp\")) as derp_sessions, count as total_sessions by node _time",
            "| eval derp_pct=round(100*derp_sessions/total_sessions,1)",
            "| where total_sessions>0 AND derp_pct>20",
            "| sort - derp_pct",
        ), "Tailscale netmap exports", "the share of sessions falling back to DERP relays", "direct-path problems that add latency to the mesh", "Daily DERP percentage by node."),
        G("9", "Tailscale Exit Node Data Share", SPL(
            "index=personal sourcetype=tailscale:netmap role=exit_node",
            "| bin _time span=1d",
            "| stats sum(tx_gb) as tx_gb, sum(rx_gb) as rx_gb by node _time",
            "| sort - tx_gb",
        ), "Tailscale exit-node telemetry", "which nodes are carrying the most routed traffic", "exit nodes that may need more capacity or clearer policy", "Daily transfer chart for exit nodes."),
        G("9", "Cloudflare Tunnel Connector Restart Burst", SPL(
            "index=personal sourcetype=cloudflared:connector",
            "| bin _time span=1d",
            "| stats count(eval(event=\"restart\")) as restarts by connector _time",
            "| where restarts>2",
            "| sort - restarts",
        ), "Cloudflare Tunnel connector logs", "daily connector restart bursts", "tunnels that are unstable enough to impact exposure", "Daily connector restart table."),
        G("9", "Cloudflare Tunnel 502 Origin Error Rate", SPL(
            "index=personal sourcetype=cloudflared:connector",
            "| stats count as requests, sum(eval(status_code=502)) as bad_gateway by hostname",
            "| eval error_pct=round(100*bad_gateway/requests,1)",
            "| where requests>=20 AND error_pct>1",
            "| sort - error_pct",
        ), "Cloudflare Tunnel request logs", "which public hostnames are returning origin 502s", "services that are healthy locally but broken through the tunnel", "Hostname table of 502 error percentage."),
        G("9", "DoH Query Volume by Upstream", SPL(
            "index=personal sourcetype=doh:query",
            "| bin _time span=1d",
            "| stats count as queries, avg(response_ms) as avg_response_ms by upstream _time",
            "| sort - queries",
        ), "DNS-over-HTTPS queries", "daily encrypted query volume and latency by upstream", "how much each resolver is carrying and how fast it feels", "Daily upstream chart of DoH volume and latency."),
        G("9", "Pi-hole Block Ratio Drop After Config Change", SPL(
            "index=personal sourcetype=pihole:query",
            "| bin _time span=1d",
            "| stats count as queries, count(eval(blocked=\"true\")) as blocked_queries by _time",
            "| eval block_pct=round(100*blocked_queries/queries,1)",
            "| streamstats window=7 current=f avg(block_pct) as baseline_block_pct",
            "| where baseline_block_pct>0 AND block_pct<baseline_block_pct*0.7",
            "| sort block_pct",
        ), "Pi-hole query logs", "daily block ratio after list or policy changes", "unexpected drops in protection coverage", "Daily trend of Pi-hole block percentage."),
        G("9", "AdGuard Encrypted DNS Client Adoption", SPL(
            "index=personal sourcetype=adguard:query",
            "| bin _time span=1w",
            "| stats dc(eval(if(encrypted=\"true\",client,null()))) as encrypted_clients, dc(client) as total_clients by _time",
            "| eval adoption_pct=round(100*encrypted_clients/total_clients,1)",
            "| where total_clients>0",
            "| sort - _time",
        ), "AdGuard Home query logs", "the share of clients using encrypted DNS paths", "whether network privacy settings are reaching the devices you care about", "Weekly chart of encrypted-DNS client adoption."),
        G("9", "OpenWrt DHCP Lease Churn", SPL(
            "index=personal sourcetype=openwrt:syslog event=dhcp_lease",
            "| bin _time span=1d",
            "| stats dc(client_mac) as unique_clients, count as lease_events by router _time",
            "| where lease_events>unique_clients*3",
            "| sort - lease_events",
        ), "OpenWrt DHCP lease logs", "days with unusually noisy lease churn", "clients or firmware that keep bouncing on the network", "Daily router table of lease events versus unique clients."),
        G("9", "Tailscale Subnet Router Offline Gap", SPL(
            "index=personal sourcetype=tailscale:netmap role=subnet_router",
            "| stats max(_time) as last_seen by node",
            "| eval hours_since=round((now()-last_seen)/3600,1)",
            "| where hours_since>1",
            "| sort - hours_since",
        ), "Tailscale subnet-router status", "how long advertised subnet routers have been missing", "private-network reachability gaps before they surprise you", "Node table of hours since last subnet-router update."),
        G("9", "DoH Upstream Latency Outlier", SPL(
            "index=personal sourcetype=doh:query",
            "| stats avg(response_ms) as avg_response_ms, perc95(response_ms) as p95_response_ms by upstream",
            "| where avg_response_ms>150 OR p95_response_ms>250",
            "| sort - p95_response_ms",
        ), "DoH resolver telemetry", "which upstreams have slow average or tail latency", "encrypted resolvers that are hurting browsing responsiveness", "Resolver table of average and p95 response time."),
        G("9", "Cloudflare Tunnel Hostname Demand Inventory", SPL(
            "index=personal sourcetype=cloudflared:connector",
            "| stats count as requests, values(connector) as connectors by hostname",
            "| sort - requests",
        ), "Cloudflare Tunnel request data", "which hostnames are receiving the most tunneled demand", "public names that deserve priority when debugging or scaling", "Hostname inventory sorted by request volume."),
        G("9", "OpenWrt Firmware Lag Over Ninety Days", SPL(
            "index=personal sourcetype=openwrt:syslog event=firmware_check",
            "| stats latest(days_behind_release) as days_behind_release by router",
            "| where days_behind_release>90",
            "| sort - days_behind_release",
        ), "OpenWrt firmware checks", "how far each router is behind current releases", "gateways that have accumulated too much patch debt", "Router table of days behind release."),
        G("9", "UniFi Gateway CPU Saturation During IDS", SPL(
            "index=personal sourcetype=unifi:event subsystem=gateway",
            "| stats avg(cpu_pct) as avg_cpu_pct, max(cpu_pct) as max_cpu_pct by gateway",
            "| where avg_cpu_pct>70 OR max_cpu_pct>90",
            "| sort - avg_cpu_pct",
        ), "UniFi gateway metrics", "CPU pressure on the gateway while security features run", "firewall nodes that are approaching their comfort zone", "Gateway table of average and peak CPU usage."),
    ],
    "10": [
        G("10", "Tempest Lightning Proximity Alert", SPL(
            "index=personal sourcetype=weatherflow:obs",
            "| stats min(lightning_distance_km) as nearest_lightning_km, count(eval(lightning_distance_km<10)) as close_strikes by station",
            "| where close_strikes>0",
            "| sort nearest_lightning_km",
        ), "Tempest station telemetry", "nearest lightning strikes seen by the home weather station", "storm cells that are approaching too closely", "Station table of nearest strike distance and close-strike count."),
        G("10", "Soil Moisture Irrigation Deficit by Bed", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=soil_moisture",
            "| stats latest(moisture_pct) as moisture_pct by bed",
            "| where moisture_pct<25",
            "| sort moisture_pct",
        ), "ESPHome plant sensors", "soil moisture for each monitored bed", "garden zones that are drying out before plants show stress", "Bed table of latest soil moisture percentage."),
        G("10", "Frost Probe Sunrise Alert", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=frost",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=3 AND hour<=7",
            "| bin _time span=1d",
            "| stats min(temp_c) as min_temp_c by zone _time",
            "| where min_temp_c<1",
            "| sort min_temp_c",
        ), "Outdoor frost probes", "the coldest pre-dawn temperature in each growing zone", "frost-risk mornings before they damage plants", "Daily frost-risk table by zone."),
        G("10", "Ambee Pollen High Count Day", SPL(
            "index=personal sourcetype=ambee:pollen",
            "| bin _time span=1d",
            "| stats max(overall_index) as pollen_index by location _time",
            "| where pollen_index>4",
            "| sort - pollen_index",
        ), "Ambee pollen feeds", "days when the local pollen index becomes meaningfully high", "allergy-heavy days that affect outdoor plans", "Daily pollen-index chart by location."),
        G("10", "Tempest Rain Gauge Bias vs Manual Gauge", SPL(
            "index=personal sourcetype=weatherflow:obs",
            "| bin _time span=1d",
            "| stats sum(rain_mm) as station_rain_mm, max(manual_gauge_mm) as manual_gauge_mm by station _time",
            "| eval rain_bias_mm=round(station_rain_mm-manual_gauge_mm,1)",
            "| where abs(rain_bias_mm)>5",
            "| sort - rain_bias_mm",
        ), "Tempest rain observations", "agreement between the station and a manual gauge", "calibration drift before rainfall records stop being trustworthy", "Daily rain-bias table."),
        G("10", "PurpleAir Smoke Episode Exposure Hour", SPL(
            "index=personal sourcetype=purpleair:aqi",
            "| bin _time span=1d",
            "| stats count(eval(aqi_us>100)) as smoke_hours by sensor _time",
            "| where smoke_hours>0",
            "| sort - smoke_hours",
        ), "PurpleAir AQI readings", "how many hours a day were affected by smoky air", "exposure days that should influence ventilation choices", "Daily count of smoke-episode hours."),
        G("10", "AirGradient Greenhouse CO2 Ventilation Gap", SPL(
            "index=personal sourcetype=airgradient:sensor",
            "| stats avg(co2_ppm) as avg_co2_ppm, max(co2_ppm) as max_co2_ppm by zone",
            "| where avg_co2_ppm>1200 OR max_co2_ppm>1800",
            "| sort - max_co2_ppm",
        ), "AirGradient CO2 sensors", "greenhouse or shed ventilation quality", "enclosed spaces that are holding too much stale air", "Zone table of average and max CO2 levels."),
        G("10", "Greenhouse VPD Out-of-Range Hour", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=vpd",
            "| bin _time span=1d",
            "| stats count(eval(vpd_kpa<0.6 OR vpd_kpa>1.4)) as out_of_range_hours by zone _time",
            "| where out_of_range_hours>4",
            "| sort - out_of_range_hours",
        ), "Greenhouse VPD sensors", "how many hours the vapor-pressure deficit sat outside the healthy range", "microclimate issues that stunt growth or invite disease", "Daily VPD out-of-range count by zone."),
        G("10", "Soil Temperature Planting Window", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=soil_temp",
            "| bin _time span=1d",
            "| stats avg(soil_temp_c) as soil_temp_c by bed _time",
            "| where soil_temp_c>=10 AND soil_temp_c<=18",
            "| sort - _time",
        ), "Soil-temperature probes", "when beds sit inside a practical planting-temperature window", "timing for outdoor starts without manually checking every bed", "Daily soil-temperature window chart."),
        G("10", "Tempest Pressure Drop Storm Watch", SPL(
            "index=personal sourcetype=weatherflow:obs",
            "| sort 0 station _time",
            "| streamstats current=f last(pressure_hpa) as prev_pressure_hpa by station",
            "| eval pressure_drop_hpa=round(prev_pressure_hpa-pressure_hpa,1)",
            "| where pressure_drop_hpa>4",
            "| sort - pressure_drop_hpa",
        ), "Tempest barometric pressure", "rapid pressure drops that usually precede rough weather", "storm setups before wind and rain arrive", "Event table of rapid pressure drops."),
        G("10", "Leaf Wetness Disease-Risk Duration", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=leaf_wetness",
            "| bin _time span=1d",
            "| stats count(eval(leaf_wetness=1)) as wet_hours, avg(temp_c) as avg_temp_c by zone _time",
            "| where wet_hours>8 AND avg_temp_c>10",
            "| sort - wet_hours",
        ), "Leaf-wetness garden sensors", "how long foliage stayed wet under disease-friendly temperatures", "conditions that favor mildew or fungal pressure", "Daily disease-risk table by zone."),
        G("10", "Tempest Rapid Wind Gust Leaderboard", SPL(
            "index=personal sourcetype=weatherflow:obs",
            "| stats max(wind_gust_kph) as max_wind_gust_kph by station",
            "| sort - max_wind_gust_kph",
        ), "Tempest wind observations", "the strongest gust each station has seen", "high-wind periods that explain damage or motion alerts", "Leaderboard of peak wind gusts."),
        G("10", "Frost-Free Night Streak", SPL(
            "index=personal sourcetype=plant:sensor sensor_type=frost",
            "| bin _time span=1d",
            "| stats min(temp_c) as nightly_low_c by zone _time",
            "| where nightly_low_c>2",
            "| sort - _time",
        ), "Frost probes", "nights that stayed safely above freezing thresholds", "favorable streaks for leaving sensitive plants outside", "Daily frost-free night table."),
        G("10", "Ecowitt Sensor Upload Gap", SPL(
            "index=personal sourcetype=ecowitt:obs",
            "| stats max(_time) as last_seen by sensor_id",
            "| eval minutes_since=round((now()-last_seen)/60,1)",
            "| where minutes_since>30",
            "| sort - minutes_since",
        ), "Ecowitt sensor uploads", "how long each station sensor has been quiet", "outdoor devices that stopped reporting before a storm hits", "Sensor table of minutes since last upload."),
        G("10", "Aquarium Temperature Drift During Heat Wave", SPL(
            "index=personal sourcetype=aquarium:sensor",
            "| stats latest(water_temp_c) as water_temp_c, max(room_temp_c) as room_temp_c by tank",
            "| where room_temp_c>28 AND (water_temp_c<23 OR water_temp_c>27)",
            "| sort - room_temp_c",
        ), "Aquarium climate telemetry", "tank temperature control during hot weather", "heat-wave days that stress fish or cooling gear", "Tank table of water and room temperature."),
    ],
    "11": [
        G("11", "Fi Collar Low-Activity Day", SPL(
            "index=personal sourcetype=fi:activity",
            "| bin _time span=1d",
            "| stats sum(steps) as steps by pet _time",
            "| where steps<2000",
            "| sort steps",
        ), "Fi collar activity exports", "days when a dog moved much less than usual", "slow or off days that merit a wellness check", "Daily low-activity table by pet."),
        G("11", "Fi Collar Escape Geofence Event Count", SPL(
            "index=personal sourcetype=fi:activity event=geofence_exit",
            "| bin _time span=1w",
            "| stats count as exits by pet _time",
            "| where exits>0",
            "| sort - exits",
        ), "Fi geofence events", "how often pets leave approved zones", "escape patterns that need better fencing or alerts", "Weekly geofence-exit count by pet."),
        G("11", "Petkit Fountain Low-Water Alert", SPL(
            "index=personal sourcetype=petkit:status device_type=fountain",
            "| stats count(eval(alert=\"low_water\")) as low_water_alerts by device",
            "| where low_water_alerts>0",
            "| sort - low_water_alerts",
        ), "Petkit fountain status", "low-water alerts from smart fountains", "hydration hardware that needs topping up or cleaning", "Device table of low-water alerts."),
        G("11", "Petlibro Feeder Jam Frequency", SPL(
            "index=personal sourcetype=petlibro:feeder",
            "| stats count(eval(status=\"jam\")) as jams by feeder",
            "| where jams>0",
            "| sort - jams",
        ), "Petlibro feeder logs", "how often each feeder jams during dispensing", "meal automation risks before a feeding is missed", "Feeder table of jam events."),
        G("11", "Litter-Robot Cycle Gap", SPL(
            "index=personal sourcetype=litterrobot:cycle",
            "| stats max(_time) as last_cycle by device",
            "| eval hours_since=round((now()-last_cycle)/3600,1)",
            "| where hours_since>24",
            "| sort - hours_since",
        ), "Litter-Robot cycle data", "how long it has been since the box last cycled", "maintenance or power issues before the box becomes unusable", "Device table of hours since last cycle."),
        G("11", "Tractive Sleepy-Day Location Radius Collapse", SPL(
            "index=personal sourcetype=tractive:location",
            "| bin _time span=1d",
            "| stats dc(zone_name) as zones_visited, max(distance_m) as max_distance_m by pet _time",
            "| where zones_visited=1 AND max_distance_m<200",
            "| sort max_distance_m",
        ), "Tractive location history", "days when a pet barely moved around its normal zones", "routines that look unusually sedentary", "Daily location-radius table by pet."),
        G("11", "Petkit Filter Replacement Overdue", SPL(
            "index=personal sourcetype=petkit:status",
            "| stats latest(filter_days_remaining) as filter_days_remaining by device",
            "| where filter_days_remaining<7",
            "| sort filter_days_remaining",
        ), "Petkit device maintenance exports", "filters that are close to the end of their service window", "consumables that will soon affect water or air quality", "Device table of filter days remaining."),
        G("11", "Furbo Barking Alert Cluster", SPL(
            "index=personal sourcetype=furbo:event event=bark",
            "| bin _time span=1h",
            "| stats count as bark_events by camera _time",
            "| where bark_events>10",
            "| sort - bark_events",
        ), "Furbo bark alerts", "hours where barking alerts arrived in tight clusters", "stress or visitor patterns that keep triggering the dog camera", "Hourly chart of bark-event clusters."),
        G("11", "Fi Weather-Linked Walk Skip", SPL(
            "index=personal sourcetype=fi:activity",
            "| bin _time span=1d",
            "| stats count(eval(walk_logged=\"true\")) as walks, avg(outdoor_temp_c) as outdoor_temp_c by pet _time",
            "| where outdoor_temp_c>32 AND walks=0",
            "| sort - outdoor_temp_c",
        ), "Fi collar walk history", "hot days when a normal walk never happened", "weather-linked routine breaks that explain lower activity", "Daily table of hot days with zero walks."),
        G("11", "Petlibro Portion Consistency Drift", SPL(
            "index=personal sourcetype=petlibro:feeder",
            "| stats avg(portion_g) as avg_portion_g, stdev(portion_g) as portion_sd_g by feeder meal_name",
            "| where avg_portion_g>0 AND portion_sd_g>avg_portion_g*0.15",
            "| sort - portion_sd_g",
        ), "Petlibro dispensing logs", "consistency of dispensed meal portions", "feeders that are drifting away from reliable servings", "Meal table of average portion and standard deviation."),
        G("11", "Aquarium Feeding and Temperature Risk Overlap", SPL(
            "index=personal sourcetype=aquarium:sensor",
            "| bin _time span=1d",
            "| stats count(eval(feeding_event=1)) as feedings, max(water_temp_c) as max_water_temp_c by tank _time",
            "| where feedings=0 OR max_water_temp_c>29",
            "| sort - max_water_temp_c",
        ), "Aquarium pet-care telemetry", "days when fish care and tank temperature both looked risky", "overlooked feedings or overheating before livestock are stressed", "Daily tank table of feedings and peak water temperature."),
        G("11", "Tractive Collar Battery Runway Under Twenty-Four Hours", SPL(
            "index=personal sourcetype=tractive:location",
            "| stats latest(battery_pct) as battery_pct, latest(estimated_hours_left) as estimated_hours_left by device",
            "| where battery_pct<20 OR estimated_hours_left<24",
            "| sort estimated_hours_left",
        ), "Tractive battery telemetry", "remaining charge on GPS collars", "tracking devices that may die before the next walk", "Device table of battery percentage and estimated hours left."),
        G("11", "Fi Resting Time Jump After Vet Visit", SPL(
            "index=personal sourcetype=fi:activity",
            "| bin _time span=1d",
            "| stats sum(rest_min) as rest_min by pet _time",
            "| eventstats avg(rest_min) as baseline_rest_min by pet",
            "| where rest_min>baseline_rest_min*1.5",
            "| sort - rest_min",
        ), "Fi rest metrics", "rest time against the pet's usual baseline", "recovery days or lethargy that stand out after stressful events", "Daily rest-time chart with baseline."),
        G("11", "Litter Weight-Loss Watch", SPL(
            "index=personal sourcetype=litterrobot:cycle",
            "| bin _time span=1w",
            "| stats avg(weight_kg) as avg_weight_kg, count as cycles by pet _time",
            "| streamstats current=f avg(avg_weight_kg) as baseline_weight_kg by pet",
            "| where baseline_weight_kg>0 AND avg_weight_kg<baseline_weight_kg*0.95",
            "| sort avg_weight_kg",
        ), "Litter-box weight telemetry", "weekly weight trends seen during litter-box use", "subtle weight loss that deserves attention", "Weekly pet table of average litter-box weight."),
        G("11", "Aquarium Oxygen Drop During Night", SPL(
            "index=personal sourcetype=aquarium:sensor",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| stats min(dissolved_oxygen_mg_l) as min_dissolved_oxygen_mg_l by tank",
            "| where min_dissolved_oxygen_mg_l<5",
            "| sort min_dissolved_oxygen_mg_l",
        ), "Aquarium oxygen telemetry", "lowest nighttime dissolved oxygen levels in each tank", "aeration problems before fish show visible distress", "Tank table of minimum nighttime dissolved oxygen."),
    ],
    "12": [
        G("12", "Monarch Uncategorized Spend Backlog", SPL(
            "index=personal sourcetype=monarch:transaction",
            "| where category=\"Uncategorized\"",
            "| stats count as uncategorized_transactions by account_name",
            "| sort - uncategorized_transactions",
        ), "Monarch Money exports", "how many transactions still lack a proper category", "budget data that is degrading because cleanup never happened", "Account table of uncategorized transaction counts."),
        G("12", "Copilot Recurring Merchant Price Creep", SPL(
            "index=personal sourcetype=copilot:transaction recurring=true",
            "| bin _time span=90d",
            "| stats avg(amount_usd) as avg_amount_usd by merchant _time",
            "| streamstats current=f last(avg_amount_usd) as prior_amount_usd by merchant",
            "| where prior_amount_usd>0 AND avg_amount_usd>prior_amount_usd*1.1",
            "| sort - avg_amount_usd",
        ), "Copilot recurring transactions", "subscription and recurring charge growth over time", "merchants that have quietly raised prices", "Ninety-day trend of recurring merchant spend."),
        G("12", "Plaid Institution Sync Gap", SPL(
            "index=personal sourcetype=plaid:account",
            "| stats max(_time) as last_sync by institution",
            "| eval hours_since=round((now()-last_sync)/3600,1)",
            "| where hours_since>12",
            "| sort - hours_since",
        ), "Plaid account syncs", "time since each institution last refreshed", "broken links before balances become stale", "Institution table of hours since last sync."),
        G("12", "Dividend Income by Month", SPL(
            "index=personal sourcetype=plaid:investment transaction_type=dividend",
            "| bin _time span=1mon",
            "| stats sum(amount_usd) as dividend_income_usd by account _time",
            "| sort - _time",
        ), "Plaid investment transactions", "monthly dividend cash flow by account", "income seasonality that is otherwise buried in broker portals", "Monthly dividend-income chart by account."),
        G("12", "Credit Utilization Above Target", SPL(
            "index=personal sourcetype=plaid:account",
            "| stats latest(balance_usd) as balance_usd, latest(limit_usd) as limit_usd by card_name",
            "| eval utilization_pct=round(100*balance_usd/limit_usd,1)",
            "| where limit_usd>0 AND utilization_pct>30",
            "| sort - utilization_pct",
        ), "Plaid credit-account balances", "current utilization on revolving accounts", "cards that are drifting into more expensive or score-unfriendly territory", "Card table of credit utilization percentage."),
        G("12", "Cash-Flow Negative Week", SPL(
            "index=personal sourcetype=monarch:transaction",
            "| bin _time span=1w",
            "| stats sum(eval(if(amount_usd>0,amount_usd,0))) as inflow_usd, sum(eval(if(amount_usd<0,abs(amount_usd),0))) as outflow_usd by _time",
            "| eval net_cashflow_usd=round(inflow_usd-outflow_usd,2)",
            "| where net_cashflow_usd<0",
            "| sort net_cashflow_usd",
        ), "Monarch transaction history", "weeks where cash outflow exceeded inflow", "negative-cashflow stretches before they become a pattern", "Weekly net-cashflow chart."),
        G("12", "Copilot Reimbursement Outstanding Age", SPL(
            "index=personal sourcetype=copilot:transaction tag=\"reimbursable\"",
            "| stats sum(amount_usd) as outstanding_usd, max(days_outstanding) as max_days_outstanding by payee",
            "| where outstanding_usd>0 AND max_days_outstanding>30",
            "| sort - max_days_outstanding",
        ), "Copilot reimbursable transactions", "how long outstanding reimbursements have been sitting open", "money that should have come back already", "Payee table of outstanding reimbursement age."),
        G("12", "Subscription Cost Hotspot", SPL(
            "index=personal sourcetype=monarch:transaction recurring=true",
            "| bin _time span=1mon",
            "| stats sum(amount_usd) as monthly_cost_usd by merchant _time",
            "| sort - monthly_cost_usd",
        ), "Monarch recurring charges", "which subscriptions cost the most each month", "services that deserve a renewal review", "Monthly subscription-cost leaderboard."),
        G("12", "Transfer Reconciliation Mismatch", SPL(
            "index=personal sourcetype=plaid:transaction transaction_type=transfer",
            "| stats sum(amount_usd) as transfer_total_usd, dc(account_id) as account_count by transfer_group_id",
            "| where account_count<2",
            "| sort transfer_total_usd",
        ), "Plaid transfer transactions", "transfer groups missing a matching source or destination", "move-money events that may not have reconciled cleanly", "Transfer-group mismatch table."),
        G("12", "Budget Burn Rate Above Plan", SPL(
            "index=personal sourcetype=monarch:transaction",
            "| stats sum(amount_usd) as spent_usd, latest(monthly_budget_usd) as monthly_budget_usd by category",
            "| eval burn_pct=round(100*spent_usd/monthly_budget_usd,1)",
            "| where monthly_budget_usd>0 AND burn_pct>85",
            "| sort - burn_pct",
        ), "Monarch category spend", "which categories have burned through most of the month's budget", "budget lines likely to end the month in the red", "Category table of budget burn percentage."),
        G("12", "Net Worth Source Lag by Institution", SPL(
            "index=personal sourcetype=plaid:account",
            "| stats latest(days_since_refresh) as days_since_refresh by institution",
            "| where days_since_refresh>2",
            "| sort - days_since_refresh",
        ), "Plaid account refresh metadata", "how stale each institution is inside net-worth rollups", "sources that are distorting current balance snapshots", "Institution table of refresh lag in days."),
        G("12", "Cash Drag Alert in Investment Accounts", SPL(
            "index=personal sourcetype=plaid:investment",
            "| stats latest(cash_pct) as cash_pct by account",
            "| where cash_pct>15",
            "| sort - cash_pct",
        ), "Plaid investment account exports", "how much of each investment account is sitting in cash", "cash drag that may be larger than intended", "Account table of cash percentage."),
        G("12", "High-APR Interest Cost Rollup", SPL(
            "index=personal sourcetype=plaid:transaction",
            "| where category=\"Interest Charged\"",
            "| bin _time span=1mon",
            "| stats sum(amount_usd) as interest_cost_usd by account_name _time",
            "| sort - interest_cost_usd",
        ), "Plaid posted transactions", "monthly interest charges by account", "accounts where carried balances are becoming costly", "Monthly interest-cost chart."),
        G("12", "ATM Fee Incident Tracker", SPL(
            "index=personal sourcetype=plaid:transaction",
            "| where category=\"ATM Fee\"",
            "| bin _time span=1mon",
            "| stats count as fee_events, sum(amount_usd) as fees_usd by account_name _time",
            "| where fee_events>0",
            "| sort - fees_usd",
        ), "Plaid transaction history", "when and where ATM fees are still occurring", "avoidable bank-fee patterns that are easy to miss", "Monthly ATM-fee table by account."),
        G("12", "Dividend Payout Concentration by Ticker", SPL(
            "index=personal sourcetype=plaid:investment transaction_type=dividend",
            "| bin _time span=12mon",
            "| stats sum(amount_usd) as annual_dividends_usd by ticker _time",
            "| eventstats sum(annual_dividends_usd) as total_dividends_usd by _time",
            "| eval share_pct=round(100*annual_dividends_usd/total_dividends_usd,1)",
            "| where share_pct>20",
            "| sort - share_pct",
        ), "Plaid dividend records", "how concentrated dividend income is by ticker", "income streams that depend too heavily on one holding", "Annual dividend concentration table."),
    ],
    "13": [
        G("13", "Obsidian Sync Conflict Count", SPL(
            "index=personal sourcetype=obsidian:sync",
            "| stats count(eval(status=\"conflict\")) as sync_conflicts by vault",
            "| where sync_conflicts>0",
            "| sort - sync_conflicts",
        ), "Obsidian Sync logs", "how often vault syncs end in conflicts", "notes that need manual cleanup before they fork further", "Vault table of sync conflicts."),
        G("13", "Todoist Overdue Task Backlog", SPL(
            "index=personal sourcetype=todoist:task",
            "| where overdue=\"true\"",
            "| stats count as overdue_tasks by project",
            "| where overdue_tasks>0",
            "| sort - overdue_tasks",
        ), "Todoist task exports", "how many overdue tasks have accumulated by project", "work buckets that are quietly becoming stale", "Project table of overdue task counts."),
        G("13", "Toggl Focus Block Average by Project", SPL(
            "index=personal sourcetype=toggl:timeentry",
            "| bin _time span=1w",
            "| stats avg(duration_min) as avg_focus_block_min, sum(duration_min) as total_minutes by project _time",
            "| sort - total_minutes",
        ), "Toggl time entries", "average focus-block size and total time by project", "projects that are only getting fragmented attention", "Weekly project chart of focus-block average and total minutes."),
        G("13", "Calendar Free-Busy Overload Day", SPL(
            "index=personal sourcetype=calendar:freebusy",
            "| bin _time span=1d",
            "| stats sum(busy_min) as busy_min by calendar _time",
            "| where busy_min>480",
            "| sort - busy_min",
        ), "Calendar free-busy exports", "days where scheduled busy time crossed a full workday", "calendar overload before it feels normal", "Daily chart of busy minutes by calendar."),
        G("13", "Obsidian Daily Note Gap Over Three Days", SPL(
            "index=personal sourcetype=obsidian:note note_type=daily",
            "| stats max(_time) as last_note by vault",
            "| eval days_since=round((now()-last_note)/86400,1)",
            "| where days_since>3",
            "| sort - days_since",
        ), "Obsidian daily-note events", "how long each vault has gone without a daily note", "journaling gaps that break personal tracking continuity", "Vault table of days since last daily note."),
        G("13", "Todoist Recurring Task Completion Drop", SPL(
            "index=personal sourcetype=todoist:task",
            "| bin _time span=1w",
            "| stats count(eval(completed=\"true\")) as completed_tasks, count as total_tasks by label _time",
            "| eval completion_pct=round(100*completed_tasks/total_tasks,1)",
            "| where total_tasks>=5 AND completion_pct<70",
            "| sort completion_pct",
        ), "Todoist recurring tasks", "weekly completion rate for recurring work", "habits or routines that are slipping", "Weekly completion-percentage chart by label."),
        G("13", "Toggl Idle Time Share Above Twenty Percent", SPL(
            "index=personal sourcetype=toggl:timeentry",
            "| bin _time span=1w",
            "| stats sum(eval(if(idle=\"true\",duration_min,0))) as idle_min, sum(duration_min) as total_min by person _time",
            "| eval idle_pct=round(100*idle_min/total_min,1)",
            "| where total_min>0 AND idle_pct>20",
            "| sort - idle_pct",
        ), "Toggl idle annotations", "how much logged time was classified as idle", "weeks when focus time was fragmented by interruption", "Weekly idle-share chart by person."),
        G("13", "Calendar Context-Switching Day", SPL(
            "index=personal sourcetype=calendar:event",
            "| bin _time span=1d",
            "| stats dc(project_tag) as contexts, count as events by _time",
            "| where contexts>4 AND events>6",
            "| sort - contexts",
        ), "Calendar event exports", "days where many different contexts competed for attention", "calendar setups that amplify switching cost", "Daily table of distinct contexts and event count."),
        G("13", "Obsidian New-Note Creation Drought", SPL(
            "index=personal sourcetype=obsidian:note event=create",
            "| bin _time span=1w",
            "| stats count as new_notes by vault _time",
            "| where new_notes<3",
            "| sort new_notes",
        ), "Obsidian note-creation events", "weekly pace of new notes in each vault", "periods when capture has gone unusually quiet", "Weekly chart of new-note count."),
        G("13", "Todoist Priority-One Aging", SPL(
            "index=personal sourcetype=todoist:task priority=4",
            "| stats max(days_open) as max_days_open, count as task_count by project",
            "| where max_days_open>7",
            "| sort - max_days_open",
        ), "Todoist priority tasks", "how long top-priority work has been sitting open", "critical tasks that are aging beyond comfort", "Project table of oldest priority-one task."),
        G("13", "Toggl Billable vs Non-Billable Split", SPL(
            "index=personal sourcetype=toggl:timeentry",
            "| bin _time span=1mon",
            "| stats sum(eval(if(billable=\"true\",duration_min,0))) as billable_min, sum(duration_min) as total_min by client _time",
            "| eval billable_pct=round(100*billable_min/total_min,1)",
            "| where total_min>0",
            "| sort - billable_pct",
        ), "Toggl billing metadata", "how work time splits between billable and non-billable buckets", "clients or months where effort is not translating into billed time", "Monthly billable-share chart by client."),
        G("13", "Calendar Travel-Time Overbook", SPL(
            "index=personal sourcetype=calendar:event",
            "| bin _time span=1d",
            "| stats sum(travel_min) as travel_min, sum(duration_min) as meeting_min by calendar _time",
            "| where travel_min>120 AND meeting_min>240",
            "| sort - travel_min",
        ), "Calendar event metadata", "days where travel time piled on top of a heavy meeting load", "schedules that are physically unrealistic", "Daily calendar table of meeting and travel minutes."),
        G("13", "Obsidian Sync Latency Outlier", SPL(
            "index=personal sourcetype=obsidian:sync",
            "| stats avg(sync_duration_ms) as avg_sync_duration_ms, max(sync_duration_ms) as max_sync_duration_ms by vault device",
            "| where avg_sync_duration_ms>3000 OR max_sync_duration_ms>10000",
            "| sort - avg_sync_duration_ms",
        ), "Obsidian Sync timing", "how long sync operations are taking by device", "vaults or clients that feel sluggish to sync", "Vault and device table of sync latency."),
        G("13", "Todoist Waiting Label Backlog", SPL(
            "index=personal sourcetype=todoist:task label=\"waiting\"",
            "| stats count as waiting_tasks by project",
            "| where waiting_tasks>5",
            "| sort - waiting_tasks",
        ), "Todoist waiting-on tasks", "how much delegated or blocked work is stacking up", "projects that are waiting on too many external dependencies", "Project table of waiting-tagged tasks."),
        G("13", "Calendar Afternoon Fragmentation", SPL(
            "index=personal sourcetype=calendar:freebusy",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=13 AND hour<18",
            "| bin _time span=1d",
            "| stats dc(slot_start) as busy_blocks, sum(busy_min) as busy_min by _time",
            "| where busy_blocks>5 AND busy_min>180",
            "| sort - busy_blocks",
        ), "Calendar free-busy blocks", "how fragmented afternoon time becomes", "days where deep work is unlikely because the afternoon is chopped up", "Daily afternoon fragmentation chart."),
    ],
    "14": [
        G("14", "FlightAware Departure Delay Watch", SPL(
            "index=personal sourcetype=flightaware:flight",
            "| stats avg(departure_delay_min) as avg_departure_delay_min, max(departure_delay_min) as max_departure_delay_min by origin",
            "| where avg_departure_delay_min>20 OR max_departure_delay_min>60",
            "| sort - avg_departure_delay_min",
        ), "FlightAware flight status", "departure delay patterns by origin airport", "airports that consistently eat away at travel margins", "Origin table of average and max departure delay."),
        G("14", "MarineTraffic Favorite Vessel Arrival Slip", SPL(
            "index=personal sourcetype=marinetraffic:vessel",
            "| stats avg(eta_slip_hr) as avg_eta_slip_hr, max(eta_slip_hr) as max_eta_slip_hr by vessel_name",
            "| where avg_eta_slip_hr>2 OR max_eta_slip_hr>6",
            "| sort - avg_eta_slip_hr",
        ), "MarineTraffic vessel feeds", "ETA slip on favorite ferries or tracked vessels", "routes that are becoming less predictable", "Vessel table of average and max ETA slip."),
        G("14", "Toll Tag Statement Upload Gap", SPL(
            "index=personal sourcetype=tolltag:trip",
            "| stats max(_time) as last_trip by transponder_id",
            "| eval days_since=round((now()-last_trip)/86400,1)",
            "| where days_since>30",
            "| sort - days_since",
        ), "Toll-tag trip exports", "time since each transponder last produced a trip record", "missing statement uploads or dead tags", "Transponder table of days since last trip."),
        G("14", "EV Trip Cost per Mile Outlier", SPL(
            "index=personal sourcetype=abrp:trip",
            "| eval cost_per_mile=round(total_trip_cost_usd/trip_miles,2)",
            "| where trip_miles>20",
            "| eventstats avg(cost_per_mile) as baseline_cost_per_mile by vehicle",
            "| where cost_per_mile>baseline_cost_per_mile*1.3",
            "| sort - cost_per_mile",
        ), "ABRP trip summaries", "which trips cost far more per mile than normal", "route choices or charging prices that spiked trip cost", "Trip table of cost per mile versus baseline."),
        G("14", "ADS-B Low Altitude Overflight Count", SPL(
            "index=personal sourcetype=adsb:aircraft",
            "| bin _time span=1d",
            "| stats count(eval(altitude_ft<3000)) as low_overflights by callsign _time",
            "| where low_overflights>0",
            "| sort - low_overflights",
        ), "ADS-B receiver data", "how many low-altitude overflights happened each day", "aircraft patterns that are more noticeable from the property", "Daily callsign table of low overflights."),
        G("14", "FlightAware Diversion Event Summary", SPL(
            "index=personal sourcetype=flightaware:flight diverted=\"true\"",
            "| stats count as diversions by airline",
            "| where diversions>0",
            "| sort - diversions",
        ), "FlightAware diversion events", "which airlines in your log are seeing diversions", "trip disruptions that deserve contingency planning", "Airline table of diversion events."),
        G("14", "MarineTraffic Anchorage Dwell Ranking", SPL(
            "index=personal sourcetype=marinetraffic:vessel",
            "| stats avg(anchor_hours) as avg_anchor_hours, max(anchor_hours) as max_anchor_hours by vessel_name",
            "| where avg_anchor_hours>12",
            "| sort - avg_anchor_hours",
        ), "MarineTraffic anchorage history", "how long favorite vessels are sitting at anchor", "ships or routes held up longer than expected", "Vessel ranking by anchorage dwell time."),
        G("14", "Toll Spend Leaderboard by Vehicle", SPL(
            "index=personal sourcetype=tolltag:trip",
            "| bin _time span=1mon",
            "| stats sum(amount_usd) as toll_spend_usd by vehicle _time",
            "| sort - toll_spend_usd",
        ), "Toll-tag statement exports", "monthly toll cost by vehicle", "commute or trip patterns that carry the most toll burden", "Monthly toll-spend leaderboard."),
        G("14", "EV Charging Share of Trip Cost", SPL(
            "index=personal sourcetype=abrp:trip",
            "| bin _time span=1mon",
            "| stats sum(charging_cost_usd) as charging_cost_usd, sum(total_trip_cost_usd) as total_trip_cost_usd by vehicle _time",
            "| eval charging_share_pct=round(100*charging_cost_usd/total_trip_cost_usd,1)",
            "| where total_trip_cost_usd>0",
            "| sort - charging_share_pct",
        ), "ABRP trip cost summaries", "what percentage of trip cost came from charging", "vehicles or months where energy cost dominates travel spend", "Monthly chart of charging share of trip cost."),
        G("14", "FlightAware Gate-Hold Hotspot", SPL(
            "index=personal sourcetype=flightaware:flight",
            "| stats avg(gate_hold_min) as avg_gate_hold_min, max(gate_hold_min) as max_gate_hold_min by origin",
            "| where avg_gate_hold_min>15 OR max_gate_hold_min>45",
            "| sort - avg_gate_hold_min",
        ), "FlightAware turnaround data", "airports where gate holds frequently slow departures", "hubs that deserve extra buffer time", "Origin table of gate-hold duration."),
        G("14", "OpenSky Route Diversity by Day", SPL(
            "index=personal sourcetype=adsb:aircraft",
            "| bin _time span=1d",
            "| stats dc(route) as route_count by _time",
            "| sort - route_count",
        ), "OpenSky route snapshots", "how many distinct routes passed through view each day", "especially busy air-traffic days worth correlating with noise or spotting notes", "Daily route-diversity chart."),
        G("14", "MarineTraffic Speed Drop Near Port", SPL(
            "index=personal sourcetype=marinetraffic:vessel",
            "| stats avg(speed_knots) as avg_speed_knots, min(speed_knots) as min_speed_knots by vessel_name port_name",
            "| where avg_speed_knots>0 AND min_speed_knots<3",
            "| sort min_speed_knots",
        ), "MarineTraffic vessel speed", "port approaches where vessels slow sharply", "docking or congestion patterns near favorite ports", "Vessel and port table of minimum speed."),
        G("14", "Toll Tag Replenishment Failure Warning", SPL(
            "index=personal sourcetype=tolltag:trip",
            "| stats latest(balance_usd) as balance_usd, latest(auto_replenish_status) as auto_replenish_status by transponder_id",
            "| where balance_usd<20 AND auto_replenish_status!=\"enabled\"",
            "| sort balance_usd",
        ), "Toll-tag balance exports", "low tag balances without automatic replenishment", "drivers who may hit a payment issue on the next toll road", "Transponder table of balance and replenishment status."),
        G("14", "EV Road Trip Charge Stop Dwell Time", SPL(
            "index=personal sourcetype=evcharger:session trip_mode=road_trip",
            "| stats avg(stop_duration_min) as avg_stop_duration_min, max(stop_duration_min) as max_stop_duration_min by site_name",
            "| where avg_stop_duration_min>45",
            "| sort - avg_stop_duration_min",
        ), "Road-trip charging sessions", "how long stops actually take on travel days", "sites or workflows that keep stretching the journey", "Charging-site table of average stop duration."),
        G("14", "Travel Document Expiry Runway", SPL(
            "index=personal sourcetype=travel:document",
            "| stats latest(days_until_expiry) as days_until_expiry by document_type person",
            "| where days_until_expiry>=0 AND days_until_expiry<90",
            "| sort days_until_expiry",
        ), "Travel document trackers", "how much runway remains before travel documents expire", "passports or permits that need attention before they block a trip", "Document table of days until expiry."),
    ],
    "15": [
        G("15", "MEATER Carryover Overshoot by Protein", SPL(
            "index=personal sourcetype=meater:cook",
            "| stats avg(carryover_delta_c) as avg_carryover_delta_c, max(carryover_delta_c) as max_carryover_delta_c by protein",
            "| where avg_carryover_delta_c>4 OR max_carryover_delta_c>8",
            "| sort - avg_carryover_delta_c",
        ), "MEATER cook telemetry", "how much temperatures rise after food leaves the heat", "proteins that keep overshooting target doneness", "Protein table of average and max carryover rise."),
        G("15", "Anova Temperature Stability Warning", SPL(
            "index=personal sourcetype=anova:session",
            "| eval temp_error_c=abs(temp_delta_c)",
            "| stats avg(temp_error_c) as avg_temp_error_c, max(temp_error_c) as max_temp_error_c by session_id",
            "| where avg_temp_error_c>0.5 OR max_temp_error_c>1.5",
            "| sort - avg_temp_error_c",
        ), "Anova sous-vide sessions", "how tightly the bath stayed near target temperature", "heating sessions that wandered enough to affect texture", "Session table of average and max temperature error."),
        G("15", "Instant Pot Pressure Release Delay", SPL(
            "index=personal sourcetype=instantpot:cook",
            "| stats avg(natural_release_min) as avg_release_min, max(natural_release_min) as max_release_min by recipe",
            "| where avg_release_min>20 OR max_release_min>35",
            "| sort - avg_release_min",
        ), "Instant Pot cook logs", "how long recipes spend in natural pressure release", "programs that keep stretching dinner later than planned", "Recipe table of natural-release duration."),
        G("15", "Wine Fridge Compressor Short-Cycle", SPL(
            "index=personal sourcetype=kitchen:appliance appliance_type=wine_fridge",
            "| bin _time span=1h",
            "| stats count(eval(compressor_state=\"on\")) as on_events, avg(run_min) as avg_run_min by appliance _time",
            "| where on_events>4 AND avg_run_min<5",
            "| sort - on_events",
        ), "Wine-fridge telemetry", "how often the compressor is short-cycling", "cooling patterns that waste energy or shorten compressor life", "Hourly wine-fridge short-cycle chart."),
        G("15", "MEATER Stall Phase Over Two Hours", SPL(
            "index=personal sourcetype=meater:cook",
            "| stats max(stall_minutes) as stall_minutes by cook_id protein",
            "| where stall_minutes>120",
            "| sort - stall_minutes",
        ), "MEATER cook sessions", "how long proteins stay in the stall phase", "cooks that need earlier start times or wrap strategy", "Cook table of stall duration."),
        G("15", "Anova Preheat Delay by Container", SPL(
            "index=personal sourcetype=anova:session",
            "| stats avg(preheat_min) as avg_preheat_min, max(preheat_min) as max_preheat_min by vessel",
            "| where avg_preheat_min>25 OR max_preheat_min>40",
            "| sort - avg_preheat_min",
        ), "Anova preheat telemetry", "how quickly different bath setups reach target temperature", "containers that consistently slow down prep", "Vessel table of average preheat duration."),
        G("15", "Instant Pot Keep-Warm Overuse", SPL(
            "index=personal sourcetype=instantpot:cook",
            "| bin _time span=1w",
            "| stats sum(keep_warm_min) as keep_warm_min by recipe _time",
            "| where keep_warm_min>120",
            "| sort - keep_warm_min",
        ), "Instant Pot cook history", "weekly accumulation of keep-warm time by recipe", "meals that are staying parked too long after cooking", "Weekly recipe chart of keep-warm minutes."),
        G("15", "Wine Fridge Door-Open Duration", SPL(
            "index=personal sourcetype=kitchen:appliance appliance_type=wine_fridge event=door",
            "| bin _time span=1d",
            "| stats sum(open_duration_min) as open_duration_min by appliance _time",
            "| where open_duration_min>15",
            "| sort - open_duration_min",
        ), "Wine-fridge door events", "how long the door stayed open each day", "usage patterns that threaten temperature stability", "Daily table of wine-fridge door-open minutes."),
        G("15", "MEATER Rest-Time Adherence Gap", SPL(
            "index=personal sourcetype=meater:cook",
            "| stats avg(rest_minutes) as avg_rest_minutes, avg(target_rest_minutes) as target_rest_minutes by protein",
            "| where target_rest_minutes>0 AND avg_rest_minutes<target_rest_minutes*0.8",
            "| sort avg_rest_minutes",
        ), "MEATER rest recommendations", "actual rest time versus target for each protein", "servings that are being cut too soon after cooking", "Protein table of target and actual rest time."),
        G("15", "Anova Power Interruption Count", SPL(
            "index=personal sourcetype=anova:session event=power_restore",
            "| bin _time span=1mon",
            "| stats count as interruptions by device _time",
            "| where interruptions>0",
            "| sort - interruptions",
        ), "Anova power-restore events", "how often cooks were interrupted by power loss or reconnect", "sous-vide jobs that were at risk of failing", "Monthly count of Anova interruptions."),
        G("15", "Instant Pot Late-Night Cook Trend", SPL(
            "index=personal sourcetype=instantpot:cook",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=22 OR hour<5",
            "| bin _time span=1mon",
            "| stats count as late_cooks by recipe _time",
            "| sort - late_cooks",
        ), "Instant Pot session history", "which recipes keep being started very late at night", "meal patterns that are pushing cleanup too late", "Monthly recipe leaderboard of late-night cooks."),
        G("15", "Wine Ready-to-Drink Window", SPL(
            "index=personal sourcetype=pantry:item item_type=wine",
            "| stats count(eval(days_to_best_window<=30 AND days_to_best_window>=0)) as ready_bottles by fridge_zone",
            "| where ready_bottles>0",
            "| sort - ready_bottles",
        ), "Wine inventory exports", "how many bottles are entering their preferred drinking window", "collections that should be enjoyed before the window closes", "Fridge-zone table of ready-to-drink bottles."),
        G("15", "MEATER Target Temperature Undershoot", SPL(
            "index=personal sourcetype=meater:cook",
            "| eval undershoot_c=target_temp_c-finish_temp_c",
            "| where undershoot_c>3",
            "| stats avg(undershoot_c) as avg_undershoot_c by protein",
            "| sort - avg_undershoot_c",
        ), "MEATER finish temperatures", "how far final temperature finished below target", "proteins that keep landing underdone", "Protein table of average undershoot."),
        G("15", "Anova Multi-Bath Session Overlap", SPL(
            "index=personal sourcetype=anova:session",
            "| bin _time span=30m",
            "| stats dc(session_id) as concurrent_sessions by device _time",
            "| where concurrent_sessions>1",
            "| sort - concurrent_sessions",
        ), "Anova device sessions", "time windows where one device was asked to support multiple overlapping jobs", "scheduling collisions that complicate kitchen workflow", "Thirty-minute chart of concurrent Anova sessions."),
        G("15", "Wine Fridge Humidity Cork Risk", SPL(
            "index=personal sourcetype=kitchen:appliance appliance_type=wine_fridge",
            "| stats avg(humidity_pct) as avg_humidity_pct, max(humidity_pct) as max_humidity_pct by appliance",
            "| where avg_humidity_pct<50 OR avg_humidity_pct>80 OR max_humidity_pct>85",
            "| sort - avg_humidity_pct",
        ), "Wine-fridge environment telemetry", "humidity conditions that can dry or mold corks", "storage drift that threatens bottle quality", "Appliance table of average and peak humidity."),
    ],
    "16": [
        G("16", "Brewfather Mash Efficiency Drift", SPL(
            "index=personal sourcetype=brew:batch",
            "| bin _time span=1mon",
            "| stats avg(mash_efficiency_pct) as mash_efficiency_pct by recipe _time",
            "| streamstats window=4 current=f avg(mash_efficiency_pct) as baseline_efficiency_pct by recipe",
            "| where baseline_efficiency_pct>0 AND mash_efficiency_pct<baseline_efficiency_pct-5",
            "| sort mash_efficiency_pct",
        ), "Brewfather batch exports", "how mash efficiency is moving against the recent recipe baseline", "recipes that are slipping in brewhouse performance", "Monthly recipe chart of mash efficiency."),
        G("16", "iSpindel Upload Gap", SPL(
            "index=personal sourcetype=ispindel:reading",
            "| stats max(_time) as last_seen by sensor_id",
            "| eval minutes_since=round((now()-last_seen)/60,1)",
            "| where minutes_since>30",
            "| sort - minutes_since",
        ), "iSpindel fermentation telemetry", "time since each hydrometer last uploaded", "fermentation batches flying blind due to missing uploads", "Sensor table of minutes since last reading."),
        G("16", "Tilt Temperature Calibration Bias", SPL(
            "index=personal sourcetype=tilt:hydrometer",
            "| stats avg(temp_c) as tilt_temp_c, avg(reference_temp_c) as reference_temp_c by color",
            "| eval bias_c=round(tilt_temp_c-reference_temp_c,1)",
            "| where abs(bias_c)>0.5",
            "| sort bias_c",
        ), "Tilt hydrometer readings", "temperature bias against a trusted reference probe", "sensors that need recalibration before batch logs drift", "Color table of Tilt temperature bias."),
        G("16", "Fermentation Start Lag After Pitch", SPL(
            "index=personal sourcetype=brew:fermentation",
            "| stats avg(hours_to_active) as avg_hours_to_active by batch_name yeast",
            "| where avg_hours_to_active>24",
            "| sort - avg_hours_to_active",
        ), "Fermentation start telemetry", "how long batches take to show active fermentation after pitching", "laggy starts that might point to yeast or temperature issues", "Batch table of average hours to activity."),
        G("16", "Dry Hop Pressure Spike", SPL(
            "index=personal sourcetype=kegerator:pressure event=dry_hop",
            "| stats max(psi) as max_psi by batch_name",
            "| where max_psi>15",
            "| sort - max_psi",
        ), "Keg pressure readings", "pressure spikes after dry-hop additions", "batches that need extra venting attention", "Batch table of maximum pressure during dry hopping."),
        G("16", "Mash pH Outlier by Recipe", SPL(
            "index=personal sourcetype=brew:mash",
            "| stats avg(ph) as avg_ph, min(ph) as min_ph, max(ph) as max_ph by recipe",
            "| where avg_ph<5.2 OR avg_ph>5.6 OR min_ph<5.0 OR max_ph>5.8",
            "| sort avg_ph",
        ), "Mash-process probes", "whether mash pH is landing inside the preferred window", "recipes that keep missing their target chemistry", "Recipe table of average, min, and max mash pH."),
        G("16", "Keg Pressure Leak Overnight", SPL(
            "index=personal sourcetype=kegerator:pressure",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats first(psi) as start_psi, last(psi) as end_psi by keg _time",
            "| eval overnight_drop_psi=round(start_psi-end_psi,1)",
            "| where overnight_drop_psi>3",
            "| sort - overnight_drop_psi",
        ), "Kegerator pressure telemetry", "overnight pressure loss from each keg", "gas leaks before they flatten a batch", "Daily keg table of overnight pressure drop."),
        G("16", "Brew Fridge Short-Cycle", SPL(
            "index=personal sourcetype=brewfridge:compressor",
            "| bin _time span=1h",
            "| stats count(eval(state=\"on\")) as cycles, avg(run_min) as avg_run_min by fridge _time",
            "| where cycles>4 AND avg_run_min<5",
            "| sort - cycles",
        ), "Brew-fridge compressor logs", "compressor short-cycling during fermentation control", "cooling behavior that wastes energy or stresses equipment", "Hourly brew-fridge cycle chart."),
        G("16", "Packaging Loss Trend by Style", SPL(
            "index=personal sourcetype=brew:batch",
            "| stats avg(packaging_loss_l) as avg_packaging_loss_l by style",
            "| where avg_packaging_loss_l>2",
            "| sort - avg_packaging_loss_l",
        ), "Brewfather packaging records", "how much finished volume is lost during packaging", "styles or workflows that keep giving up too much beer", "Style table of average packaging loss."),
        G("16", "Tilt and iSpindel Gravity Delta", SPL(
            "index=personal sourcetype=brew:fermentation",
            "| stats avg(tilt_sg) as tilt_sg, avg(ispindel_sg) as ispindel_sg by batch_name",
            "| eval sg_delta=round(abs(tilt_sg-ispindel_sg),3)",
            "| where sg_delta>0.004",
            "| sort - sg_delta",
        ), "Dual-sensor fermentation batches", "gravity agreement between Tilt and iSpindel readings", "batches where at least one sensor is drifting", "Batch table of gravity delta between sensors."),
        G("16", "Brewfather Ingredient Stock Low", SPL(
            "index=personal sourcetype=brew:batch event=inventory",
            "| stats latest(days_of_stock_left) as days_of_stock_left by ingredient",
            "| where days_of_stock_left<14",
            "| sort days_of_stock_left",
        ), "Brewfather inventory exports", "which ingredients are close to running out", "brew-day surprises caused by low stock", "Ingredient table of days of stock left."),
        G("16", "Tap Line Cleaning Overdue", SPL(
            "index=personal sourcetype=tapline:clean",
            "| stats latest(days_since_clean) as days_since_clean by tap",
            "| where days_since_clean>30",
            "| sort - days_since_clean",
        ), "Tap-line maintenance logs", "how long each draft line has gone since cleaning", "lines that are drifting into flavor or hygiene risk", "Tap table of days since clean."),
        G("16", "Tap Foam Waste Rate", SPL(
            "index=personal sourcetype=kegerator:pour",
            "| bin _time span=1w",
            "| stats sum(waste_oz) as waste_oz, sum(poured_oz) as poured_oz by tap _time",
            "| eval waste_pct=round(100*waste_oz/poured_oz,1)",
            "| where poured_oz>0 AND waste_pct>10",
            "| sort - waste_pct",
        ), "Kegerator pour telemetry", "how much draft beer is turning into foam waste", "tap lines or settings that are hurting serving yield", "Weekly tap table of foam-waste percentage."),
        G("16", "Crash-Cooling Duration Outlier", SPL(
            "index=personal sourcetype=brew:fermentation event=crash_cool",
            "| stats avg(duration_hr) as avg_duration_hr, max(duration_hr) as max_duration_hr by batch_name",
            "| where avg_duration_hr>24 OR max_duration_hr>36",
            "| sort - avg_duration_hr",
        ), "Fermentation crash-cooling events", "how long crash-cooling is taking per batch", "batches that are cooling slower than the normal process", "Batch table of crash-cooling duration."),
        G("16", "Cellar Humidity Cork Risk by Rack", SPL(
            "index=personal sourcetype=winecellar:reading",
            "| stats avg(humidity_pct) as humidity_pct, avg(temp_c) as temp_c by rack",
            "| where humidity_pct<55 OR humidity_pct>75",
            "| sort humidity_pct",
        ), "Wine-cellar environment readings", "rack humidity versus the zone that keeps corks healthy", "storage zones that need climate adjustment", "Rack table of cellar humidity and temperature."),
    ],
    "17": [
        G("17", "Bambu Lab AMS Feed Failure Count", SPL(
            "index=personal sourcetype=bambulab:job",
            "| stats count(eval(event=\"ams_feed_fail\")) as ams_feed_failures by printer",
            "| where ams_feed_failures>0",
            "| sort - ams_feed_failures",
        ), "Bambu Lab print jobs", "automatic-material-system feed failures by printer", "AMS paths that need cleanup or parts before a larger job fails", "Printer table of AMS feed failures."),
        G("17", "Prusa Connect Offline Gap", SPL(
            "index=personal sourcetype=prusaconnect:printer",
            "| stats max(_time) as last_seen by printer",
            "| eval hours_since=round((now()-last_seen)/3600,1)",
            "| where hours_since>1",
            "| sort - hours_since",
        ), "Prusa Connect status updates", "how long printers have been quiet", "printers that fell off the network or cloud view", "Printer table of hours since last contact."),
        G("17", "Laser Exhaust Underperformance", SPL(
            "index=personal sourcetype=laserweb:job",
            "| stats avg(exhaust_cfm) as avg_exhaust_cfm, min(exhaust_cfm) as min_exhaust_cfm by cutter",
            "| where avg_exhaust_cfm<250 OR min_exhaust_cfm<200",
            "| sort avg_exhaust_cfm",
        ), "LaserWeb job telemetry", "whether exhaust airflow is staying inside the safe range", "extraction systems that are too weak for clean cutting", "Cutter table of average and minimum exhaust flow."),
        G("17", "CNC Coolant Low-Level Warning", SPL(
            "index=personal sourcetype=cnc:coolant",
            "| stats latest(level_pct) as level_pct by machine",
            "| where level_pct<20",
            "| sort level_pct",
        ), "CNC coolant telemetry", "remaining coolant level on each machine", "machines that may soon run too hot or dirty", "Machine table of coolant percentage."),
        G("17", "Bambu Lab Chamber Temperature Drift", SPL(
            "index=personal sourcetype=bambulab:job",
            "| stats avg(chamber_temp_c) as avg_chamber_temp_c, stdev(chamber_temp_c) as temp_sd_c by printer material",
            "| where avg_chamber_temp_c>35 OR temp_sd_c>2",
            "| sort - temp_sd_c",
        ), "Bambu chamber telemetry", "temperature stability during enclosed prints", "jobs where chamber conditions are wandering too much", "Printer and material table of chamber temperature variation."),
        G("17", "Prusa Connect First Layer Retry Trend", SPL(
            "index=personal sourcetype=prusaconnect:printer event=first_layer",
            "| bin _time span=1mon",
            "| stats count(eval(result=\"retry\")) as retries, count as attempts by printer _time",
            "| eval retry_pct=round(100*retries/attempts,1)",
            "| where attempts>=5 AND retry_pct>10",
            "| sort - retry_pct",
        ), "Prusa first-layer events", "monthly first-layer retry rate per printer", "build-surface or calibration problems that are growing", "Monthly printer chart of first-layer retry percentage."),
        G("17", "Laser Tube Runtime Maintenance Window", SPL(
            "index=personal sourcetype=laserweb:job",
            "| stats latest(tube_hours) as tube_hours by cutter",
            "| where tube_hours>900",
            "| sort - tube_hours",
        ), "Laser cutter maintenance telemetry", "tube runtime against the replacement or inspection window", "lasers approaching maintenance thresholds", "Cutter table of accumulated tube hours."),
        G("17", "CNC Warmup Skipped Before Run", SPL(
            "index=personal sourcetype=cnc:job",
            "| stats count(eval(warmup_completed=0)) as skipped_warmups by machine",
            "| where skipped_warmups>0",
            "| sort - skipped_warmups",
        ), "CNC job logs", "runs that started without a completed warmup", "setups that may sacrifice accuracy or spindle life", "Machine table of skipped warmups."),
        G("17", "Drybox Humidity Alert by Filament", SPL(
            "index=personal sourcetype=filament:spool",
            "| stats avg(drybox_humidity_pct) as drybox_humidity_pct by material color",
            "| where drybox_humidity_pct>20",
            "| sort - drybox_humidity_pct",
        ), "Filament drybox sensors", "storage humidity by filament material and color", "spools that are likely to print worse because they are too damp", "Filament table of drybox humidity."),
        G("17", "Workshop VOC Episode During Resin Work", SPL(
            "index=personal sourcetype=workshop:air",
            "| bin _time span=1h",
            "| stats max(voc_index) as max_voc_index by zone _time",
            "| where max_voc_index>200",
            "| sort - max_voc_index",
        ), "Workshop air sensors", "VOC spikes during messy or resin-heavy work", "ventilation gaps that matter for operator comfort and safety", "Hourly VOC spike chart by zone."),
        G("17", "Bambu Lab Firmware Skew Inventory", SPL(
            "index=personal sourcetype=bambulab:job",
            "| stats latest(firmware_version) as firmware_version by printer",
            "| eventstats dc(firmware_version) as firmware_variants",
            "| where firmware_variants>1",
            "| sort - firmware_variants",
        ), "Bambu firmware inventory", "whether the printer fleet is running the same firmware", "partial upgrades that complicate issue isolation", "Fleet inventory of Bambu firmware variants."),
        G("17", "Prusa Nozzle-Change Regression", SPL(
            "index=personal sourcetype=prusaconnect:printer event=print_complete",
            "| stats avg(first_layer_score) as avg_first_layer_score, avg(failure_pct) as avg_failure_pct by printer nozzle_type",
            "| where avg_failure_pct>5 OR avg_first_layer_score<80",
            "| sort avg_first_layer_score",
        ), "Prusa print-completion telemetry", "quality after nozzle changes or nozzle swaps", "hardware changes that reduced print consistency", "Printer and nozzle table of first-layer score and failure rate."),
        G("17", "CNC Tool-Wear Runtime Counter", SPL(
            "index=personal sourcetype=cnc:job",
            "| stats sum(runtime_min) as runtime_min by tool_id",
            "| where runtime_min>600",
            "| sort - runtime_min",
        ), "CNC job runtime logs", "how long each tool has actually been cutting", "wear items that are approaching replacement windows", "Tool runtime leaderboard."),
        G("17", "Laser Overburn Hotspot by Material", SPL(
            "index=personal sourcetype=laserweb:job",
            "| stats avg(overburn_pct) as avg_overburn_pct, max(overburn_pct) as max_overburn_pct by material",
            "| where avg_overburn_pct>5 OR max_overburn_pct>10",
            "| sort - avg_overburn_pct",
        ), "LaserWeb cut telemetry", "materials that repeatedly show overburn", "settings that need re-tuning before stock is wasted", "Material table of average and max overburn."),
        G("17", "Print Queue Age Across Workshop", SPL(
            "index=personal sourcetype=octoprint:job state=queued",
            "| stats max(queue_age_min) as oldest_queue_min, count as queued_jobs by printer",
            "| where oldest_queue_min>60 OR queued_jobs>3",
            "| sort - oldest_queue_min",
        ), "OctoPrint queue metadata", "how long queued jobs have been waiting", "print backlog that is longer than the workshop expects", "Printer table of oldest queue age and queue size."),
    ],
    "18": [
        G("18", "Reolink Camera Offline Hotspot", SPL(
            "index=personal sourcetype=reolink:event event=camera_status",
            "| stats count(eval(status=\"offline\")) as offline_events by camera",
            "| where offline_events>0",
            "| sort - offline_events",
        ), "Reolink camera health", "which cameras keep going offline", "weak cameras before coverage gaps become obvious", "Camera table of offline events."),
        G("18", "UniFi Protect Recording Gap", SPL(
            "index=personal sourcetype=unifiprotect:event event=recording",
            "| stats max(_time) as last_recording by camera",
            "| eval hours_since=round((now()-last_recording)/3600,1)",
            "| where hours_since>1",
            "| sort - hours_since",
        ), "UniFi Protect recording events", "how long each camera has gone without a recording event", "cameras or storage paths that are not capturing footage", "Camera table of hours since last recording."),
        G("18", "Ring Motion Notification Lag", SPL(
            "index=personal sourcetype=ring:event event=motion",
            "| stats avg(notification_delay_ms) as avg_delay_ms, max(notification_delay_ms) as max_delay_ms by device",
            "| where avg_delay_ms>4000 OR max_delay_ms>10000",
            "| sort - avg_delay_ms",
        ), "Ring motion alerts", "delay between motion detection and notification delivery", "doorbell alerts that are arriving too late to be useful", "Device table of average and max motion-notification delay."),
        G("18", "Nest Protect Low Battery Propagation", SPL(
            "index=personal sourcetype=nestprotect:event event=battery",
            "| stats count(eval(battery_pct<20)) as low_battery_devices by home",
            "| where low_battery_devices>0",
            "| sort - low_battery_devices",
        ), "Nest Protect battery telemetry", "how many devices in each home are entering low-battery state", "smoke or CO monitors that need attention soon", "Home table of low-battery Nest Protect devices."),
        G("18", "Reolink Person Detection Confidence Drift", SPL(
            "index=personal sourcetype=reolink:event event=person_detection",
            "| bin _time span=1w",
            "| stats avg(confidence_pct) as confidence_pct by camera _time",
            "| streamstats current=f avg(confidence_pct) as baseline_confidence_pct by camera",
            "| where baseline_confidence_pct>0 AND confidence_pct<baseline_confidence_pct*0.8",
            "| sort confidence_pct",
        ), "Reolink detection events", "weekly confidence drift in person detections", "camera views that degraded due to placement, weather, or firmware", "Weekly confidence trend by camera."),
        G("18", "UniFi Protect Retention Below Target", SPL(
            "index=personal sourcetype=unifiprotect:event event=storage",
            "| stats latest(retention_days) as retention_days by nvr",
            "| where retention_days<7",
            "| sort retention_days",
        ), "UniFi Protect storage telemetry", "remaining retention window for recordings", "NVR storage that is no longer meeting your retention goal", "NVR table of retention days remaining."),
        G("18", "Ring Battery Drain in Cold Weather", SPL(
            "index=personal sourcetype=ring:event",
            "| stats avg(battery_drop_pct_day) as battery_drop_pct_day, avg(outdoor_temp_c) as outdoor_temp_c by device",
            "| where outdoor_temp_c<5 AND battery_drop_pct_day>5",
            "| sort - battery_drop_pct_day",
        ), "Ring battery telemetry", "battery drain rate under cold conditions", "doorbells or cameras that will die quickly in winter weather", "Device table of cold-weather battery drain."),
        G("18", "Nest Protect CO Self-Test Miss", SPL(
            "index=personal sourcetype=nestprotect:event event=self_test",
            "| stats max(days_since_last_test) as days_since_last_test by device",
            "| where days_since_last_test>30",
            "| sort - days_since_last_test",
        ), "Nest Protect self-test events", "how long each unit has gone without a self-test", "life-safety devices that are drifting past expected checks", "Device table of days since last self-test."),
        G("18", "Reolink RTSP Reconnect Flap", SPL(
            "index=personal sourcetype=reolink:event event=rtsp_reconnect",
            "| bin _time span=1d",
            "| stats count as reconnects by camera _time",
            "| where reconnects>3",
            "| sort - reconnects",
        ), "Reolink stream-health events", "daily RTSP reconnect bursts by camera", "network or firmware issues hurting recording stability", "Daily RTSP reconnect chart."),
        G("18", "UniFi Protect Smart Detection by Zone", SPL(
            "index=personal sourcetype=unifiprotect:event event=smart_detect",
            "| bin _time span=1w",
            "| stats count as detections by zone object_type _time",
            "| sort - detections",
        ), "UniFi Protect smart detections", "weekly object-detection volume by camera zone", "zones that are busy enough to need tighter rules or better filters", "Weekly zone and object-type detection leaderboard."),
        G("18", "Ring Shared-User Access Summary", SPL(
            "index=personal sourcetype=ring:event event=user_access",
            "| stats dc(user) as users, count as events by device",
            "| where users>2",
            "| sort - users",
        ), "Ring access logs", "which devices are being touched by many household users", "shared-access surfaces that deserve a quick review", "Device table of unique users and access events."),
        G("18", "Nest Protect Pathlight Night Frequency", SPL(
            "index=personal sourcetype=nestprotect:event event=pathlight",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=22 OR hour<6",
            "| bin _time span=1w",
            "| stats count as pathlight_events by location _time",
            "| sort - pathlight_events",
        ), "Nest Protect pathlight events", "how often nighttime movement triggers hallway lighting", "rooms with more night traffic than expected", "Weekly location chart of pathlight events."),
        G("18", "Camera Firmware Skew Across Vendor", SPL(
            "index=personal sourcetype=camera:health",
            "| stats latest(firmware_version) as firmware_version by vendor camera",
            "| eventstats dc(firmware_version) as firmware_variants by vendor",
            "| where firmware_variants>1",
            "| sort - firmware_variants",
        ), "Camera health inventory", "firmware skew inside each camera vendor fleet", "uneven upgrade coverage that complicates incident response", "Vendor inventory of camera firmware variants."),
        G("18", "Reolink Night Bitrate Under-Run", SPL(
            "index=personal sourcetype=reolink:event event=stream_health",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=20 OR hour<6",
            "| stats avg(bitrate_mbps) as avg_bitrate_mbps, min(bitrate_mbps) as min_bitrate_mbps by camera",
            "| where avg_bitrate_mbps<2 OR min_bitrate_mbps<1",
            "| sort avg_bitrate_mbps",
        ), "Reolink stream bitrate", "how much bitrate drops at night when scenes get harder", "cameras that may be under-recording critical night detail", "Nighttime bitrate table by camera."),
        G("18", "Alarm Arm-to-Detection Latency", SPL(
            "index=personal sourcetype=alarm:event",
            "| stats avg(latency_ms) as avg_latency_ms, max(latency_ms) as max_latency_ms by zone",
            "| where avg_latency_ms>1000 OR max_latency_ms>5000",
            "| sort - avg_latency_ms",
        ), "Alarm-panel events", "latency between arming and follow-on detection visibility", "slow security paths that may delay awareness", "Zone table of average and max alarm latency."),
    ],
    "19": [
        G("19", "Flo Daily Leak Score Spike", SPL(
            "index=personal sourcetype=flo:event event=leak_score",
            "| bin _time span=1d",
            "| stats max(leak_score) as leak_score by home _time",
            "| where leak_score>70",
            "| sort - leak_score",
        ), "Flo by Moen leak scoring", "days where leak-risk scoring became meaningfully elevated", "water anomalies before they become a claim", "Daily leak-score chart by home."),
        G("19", "Rachio Connectivity-Skipped Watering", SPL(
            "index=personal sourcetype=rachio:zone",
            "| stats count(eval(result=\"skipped\" AND reason=\"offline\")) as skipped_runs by controller zone",
            "| where skipped_runs>0",
            "| sort - skipped_runs",
        ), "Rachio run history", "watering jobs skipped because the controller was offline", "connectivity issues that leave zones dry", "Controller and zone table of offline skips."),
        G("19", "Maytronics Dolphin Cycle Completion Gap", SPL(
            "index=personal sourcetype=maytronics:robot",
            "| stats max(_time) as last_cycle by robot",
            "| eval days_since=round((now()-last_cycle)/86400,1)",
            "| where days_since>3",
            "| sort - days_since",
        ), "Maytronics robot telemetry", "time since the pool robot last completed a cycle", "cleaning gaps before debris and chemistry drift pile up", "Robot table of days since last cycle."),
        G("19", "Water Softener Recharge Interval Drift", SPL(
            "index=personal sourcetype=watersoftener:status",
            "| bin _time span=1mon",
            "| stats avg(days_between_regen) as avg_days_between_regen by unit _time",
            "| streamstats window=4 current=f avg(avg_days_between_regen) as baseline_days_between_regen by unit",
            "| where baseline_days_between_regen>0 AND avg_days_between_regen<baseline_days_between_regen*0.8",
            "| sort avg_days_between_regen",
        ), "Water-softener telemetry", "changes in regeneration cadence over time", "systems that are regenerating much more often than usual", "Monthly trend of days between regenerations."),
        G("19", "Flo Automatic Shutoff Event Summary", SPL(
            "index=personal sourcetype=flo:event event=auto_shutoff",
            "| bin _time span=1mon",
            "| stats count as auto_shutoffs by home _time",
            "| where auto_shutoffs>0",
            "| sort - auto_shutoffs",
        ), "Flo shutoff events", "automatic shutoffs by month", "whether leak protection is frequently intervening", "Monthly chart of Flo automatic shutoffs."),
        G("19", "Rachio Rain-Skip Accuracy Review", SPL(
            "index=personal sourcetype=rachio:zone",
            "| bin _time span=1w",
            "| stats count(eval(result=\"skipped\" AND reason=\"rain\")) as rain_skips, sum(rain_mm) as rain_mm by zone _time",
            "| where rain_skips>0",
            "| sort - rain_skips",
        ), "Rachio rain-skip logs", "how often zones skipped because forecast or observed rain was present", "whether weather-based watering rules are engaging often enough", "Weekly zone chart of rain skips and rainfall."),
        G("19", "Pool Chemistry Drift After Fill", SPL(
            "index=personal sourcetype=pool:chemistry event=manual_test",
            "| where hours_since_fill<48",
            "| stats avg(ph) as avg_ph, avg(fc_ppm) as avg_fc_ppm by pool",
            "| where avg_ph>7.8 OR avg_fc_ppm<2",
            "| sort - avg_ph",
        ), "Pool chemistry tests", "early post-fill chemistry stability", "fill events that need faster balancing", "Pool table of post-fill pH and free chlorine."),
        G("19", "Softener Salt Refill Runway Under Two Weeks", SPL(
            "index=personal sourcetype=watersoftener:status",
            "| stats latest(days_of_salt_left) as days_of_salt_left by unit",
            "| where days_of_salt_left<14",
            "| sort days_of_salt_left",
        ), "Water-softener consumable tracking", "how much salt runway remains", "systems that are about to need a refill", "Unit table of days of salt remaining."),
        G("19", "Water Pressure Drop Transient Count", SPL(
            "index=personal sourcetype=waterpressure:reading",
            "| bin _time span=1d",
            "| stats count(eval(pressure_psi<30)) as low_pressure_events by zone _time",
            "| where low_pressure_events>0",
            "| sort - low_pressure_events",
        ), "Water-pressure sensors", "how often water pressure drops below a healthy floor", "pump or plumbing issues before they become user-visible", "Daily zone table of low-pressure events."),
        G("19", "Irrigation Forecast vs Actual Water Gap", SPL(
            "index=personal sourcetype=irrigation:zone",
            "| bin _time span=1w",
            "| stats sum(planned_mm) as planned_mm, sum(applied_mm) as applied_mm by zone _time",
            "| eval gap_mm=round(planned_mm-applied_mm,1)",
            "| where gap_mm>10",
            "| sort - gap_mm",
        ), "Irrigation controller exports", "how far applied watering lagged the planned amount", "zones that are falling short of schedule", "Weekly zone chart of planned versus applied water."),
        G("19", "Pool Fill Water Anomaly From Leak", SPL(
            "index=personal sourcetype=watermeter:flow",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats sum(flow_gal) as overnight_flow_gal by meter _time",
            "| where overnight_flow_gal>200",
            "| sort - overnight_flow_gal",
        ), "Whole-home water-flow data", "large overnight draw that often points to filling or leakage", "water loss hiding behind sleeping hours", "Daily overnight-flow chart."),
        G("19", "Rachio Seasonal Adjust Disabled", SPL(
            "index=personal sourcetype=rachio:zone event=settings",
            "| stats latest(seasonal_adjust_enabled) as seasonal_adjust_enabled by controller",
            "| where seasonal_adjust_enabled!=1",
            "| sort controller",
        ), "Rachio settings exports", "whether seasonal adjustment is still enabled", "controllers that are no longer adapting to weather and season", "Controller table of seasonal-adjust state."),
        G("19", "Pool Robot Dock Communication Loss", SPL(
            "index=personal sourcetype=maytronics:robot event=dock",
            "| stats count(eval(status=\"offline\")) as dock_offline_events by robot",
            "| where dock_offline_events>0",
            "| sort - dock_offline_events",
        ), "Maytronics dock telemetry", "dock communication loss for the pool robot", "charging or connectivity issues that leave the robot unavailable", "Robot table of dock offline events."),
        G("19", "Flo Moisture Sensor Low Battery", SPL(
            "index=personal sourcetype=flo:event event=sensor_battery",
            "| stats count(eval(battery_pct<20)) as low_battery_sensors by home",
            "| where low_battery_sensors>0",
            "| sort - low_battery_sensors",
        ), "Flo sensor-battery exports", "how many moisture sensors are nearing empty", "water sensors that may stop protecting vulnerable rooms", "Home table of low-battery Flo sensors."),
        G("19", "Softener Hardness Breakthrough Alert", SPL(
            "index=personal sourcetype=watersoftener:status",
            "| stats latest(outlet_hardness_gpg) as outlet_hardness_gpg by unit",
            "| where outlet_hardness_gpg>1",
            "| sort - outlet_hardness_gpg",
        ), "Water-softener outlet readings", "hardness detected after water passes the softener", "media or salt issues that are reducing treatment quality", "Unit table of outlet hardness."),
    ],
    "20": [
        G("20", "Geiger Spike vs Background Baseline", SPL(
            "index=personal sourcetype=geiger:cpm",
            "| bin _time span=1h",
            "| stats avg(cpm) as cpm by sensor _time",
            "| eventstats avg(cpm) as baseline_cpm by sensor",
            "| where baseline_cpm>0 AND cpm>baseline_cpm*1.5",
            "| sort - cpm",
        ), "Geiger counter telemetry", "radiation count spikes against the usual background", "sensor events that deserve comparison with public baselines", "Hourly chart of CPM versus baseline."),
        G("20", "Lightning Cluster by Storm Hour", SPL(
            "index=personal sourcetype=lightning:strike",
            "| bin _time span=1h",
            "| stats count as strikes, min(distance_km) as nearest_km by station _time",
            "| where strikes>10 OR nearest_km<5",
            "| sort - strikes",
        ), "Lightning detector feeds", "storm hours with dense strike activity or very near hits", "fast-moving cells that matter to outdoor safety", "Hourly lightning-cluster table."),
        G("20", "Indoor CO2 Overnight Ventilation Gap", SPL(
            "index=personal sourcetype=airgradient:sensor",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=0 AND hour<6",
            "| bin _time span=1d",
            "| stats avg(co2_ppm) as avg_co2_ppm, max(co2_ppm) as max_co2_ppm by room _time",
            "| where avg_co2_ppm>1200 OR max_co2_ppm>1800",
            "| sort - avg_co2_ppm",
        ), "AirGradient indoor air data", "overnight CO2 buildup in sleeping spaces", "ventilation problems that affect sleep quality and comfort", "Daily room chart of overnight average and max CO2."),
        G("20", "Radon Seasonal Rise by Basement Zone", SPL(
            "index=personal sourcetype=radon:reading",
            "| bin _time span=30d",
            "| stats avg(radon_bqm3) as radon_bqm3 by zone _time",
            "| eventstats avg(radon_bqm3) as baseline_radon_bqm3 by zone",
            "| where baseline_radon_bqm3>0 AND radon_bqm3>baseline_radon_bqm3*1.3",
            "| sort - radon_bqm3",
        ), "Radon monitor telemetry", "seasonal radon movement by monitored zone", "periods where basement exposure is trending upward", "Monthly radon trend by zone."),
        G("20", "Allsky Meteor Peak Hour", SPL(
            "index=personal sourcetype=allsky:capture",
            "| bin _time span=1h",
            "| stats count(eval(event_type=\"meteor\")) as meteors by camera _time",
            "| where meteors>0",
            "| sort - meteors",
        ), "Allsky camera captures", "which hours saw the most meteor detections", "nights worth reviewing or sharing", "Hourly leaderboard of meteor detections."),
        G("20", "Raspberry Shake Event Detection vs Local Noise", SPL(
            "index=personal sourcetype=seismo:reading",
            "| bin _time span=1d",
            "| stats avg(noise_floor) as noise_floor, count(eval(event_detected=1)) as detected_events by station _time",
            "| where detected_events>0",
            "| sort - detected_events",
        ), "Raspberry Shake telemetry", "detected events alongside the local seismic noise floor", "whether the sensor is seeing interesting events or just living in a loud spot", "Daily station table of noise floor and detected events."),
        G("20", "Magnetometer Geomagnetic Disturbance Watch", SPL(
            "index=personal sourcetype=magnetometer:reading",
            "| stats avg(delta_nt) as avg_delta_nt, max(delta_nt) as max_delta_nt by sensor",
            "| where avg_delta_nt>50 OR max_delta_nt>100",
            "| sort - max_delta_nt",
        ), "Backyard magnetometer readings", "geomagnetic disturbance against the usual field stability", "storms or local interference worth correlating with other sensors", "Sensor table of average and max field delta."),
        G("20", "Lightning Sensor False-Strike Ratio", SPL(
            "index=personal sourcetype=lightning:strike",
            "| stats count as total_strikes, count(eval(validated=\"false\")) as false_strikes by sensor",
            "| eval false_pct=round(100*false_strikes/total_strikes,1)",
            "| where total_strikes>0 AND false_pct>20",
            "| sort - false_pct",
        ), "Lightning strike telemetry", "how many hits the sensor later marked as false", "detectors that need placement or filtering changes", "Sensor table of false-strike percentage."),
        G("20", "CO2 Recovery Time After Occupancy", SPL(
            "index=personal sourcetype=airgradient:sensor",
            "| stats avg(recovery_min) as avg_recovery_min, max(recovery_min) as max_recovery_min by room",
            "| where avg_recovery_min>45 OR max_recovery_min>90",
            "| sort - avg_recovery_min",
        ), "AirGradient room telemetry", "how quickly rooms recover after people leave", "spaces that ventilate too slowly after occupancy", "Room table of average and max CO2 recovery time."),
        G("20", "Radon Mitigation Fan Failure Proxy", SPL(
            "index=personal sourcetype=radon:reading",
            "| stats latest(fan_rpm) as fan_rpm, latest(radon_bqm3) as radon_bqm3 by zone",
            "| where fan_rpm=0 AND radon_bqm3>150",
            "| sort - radon_bqm3",
        ), "Radon mitigation telemetry", "whether rising radon is happening while the mitigation fan appears stopped", "fan failures before they become a long exposure window", "Zone table of fan RPM and radon level."),
        G("20", "Allsky Clouded-Out Night Ratio", SPL(
            "index=personal sourcetype=allsky:capture",
            "| bin _time span=1d",
            "| stats count(eval(cloud_cover_pct>80)) as cloudy_frames, count as total_frames by camera _time",
            "| eval cloudy_pct=round(100*cloudy_frames/total_frames,1)",
            "| where total_frames>0 AND cloudy_pct>80",
            "| sort - cloudy_pct",
        ), "Allsky camera weather context", "how much of each night was effectively clouded out", "nights where astronomy data will be sparse before you waste review time", "Daily cloudy-frame percentage chart."),
        G("20", "Geiger Battery Bias Watch", SPL(
            "index=personal sourcetype=geiger:cpm",
            "| stats avg(cpm) as avg_cpm, latest(battery_v) as battery_v by sensor",
            "| where battery_v<3.3",
            "| sort battery_v",
        ), "Geiger sensor health", "low-battery conditions that may bias counts or uptime", "detectors that need fresh power before the data degrades", "Sensor table of battery voltage and average CPM."),
        G("20", "Backyard Seismic Quiet-Hour Baseline Shift", SPL(
            "index=personal sourcetype=seismo:reading",
            "| eval hour=tonumber(strftime(_time,\"%H\"))",
            "| where hour>=1 AND hour<5",
            "| bin _time span=1w",
            "| stats avg(noise_floor) as quiet_noise_floor by station _time",
            "| streamstats window=4 current=f avg(quiet_noise_floor) as baseline_noise_floor by station",
            "| where baseline_noise_floor>0 AND quiet_noise_floor>baseline_noise_floor*1.2",
            "| sort - quiet_noise_floor",
        ), "Quiet-hour seismic noise", "changes in the normal overnight noise baseline", "new vibration sources near the sensor before they hide real events", "Weekly quiet-hour noise chart."),
        G("20", "Aurora Opportunity Window", SPL(
            "index=personal sourcetype=allsky:capture",
            "| bin _time span=1h",
            "| stats max(aurora_kp_estimate) as aurora_kp_estimate, avg(cloud_cover_pct) as cloud_cover_pct by camera _time",
            "| where aurora_kp_estimate>=6 AND cloud_cover_pct<40",
            "| sort - aurora_kp_estimate",
        ), "Allsky camera night-sky summaries", "hours where geomagnetic conditions and cloud cover lined up for aurora viewing", "rare clear windows worth checking live", "Hourly chart of aurora estimate and cloud cover."),
        G("20", "Allsky Camera Upload Gap", SPL(
            "index=personal sourcetype=allsky:capture",
            "| stats max(_time) as last_frame by camera",
            "| eval minutes_since=round((now()-last_frame)/60,1)",
            "| where minutes_since>15",
            "| sort - minutes_since",
        ), "Allsky camera uploads", "how long each camera has gone without a frame", "uptime gaps before a meteor shower or aurora night is missed", "Camera table of minutes since last frame."),
    ],
}


def emit_specs(writer: Cat25Writer, sub: str, specs: list[dict[str, object]]) -> None:
    defaults = DEFAULTS[sub]
    for spec in specs:
        writer.U(
            sub=sub,
            title=str(spec["title"]),
            crit=str(spec["crit"]),
            diff=str(spec["diff"]),
            mtypes=list(spec["mtypes"]),
            spl=str(spec["spl"]),
            desc=str(spec["desc"]),
            val=str(spec["val"]),
            impl=str(spec["impl"]),
            viz=str(spec["viz"]),
            grandma_body=str(spec["grandma_body"]),
            refs=list(defaults["refs"]),
            app=str(defaults["app"]),
            ds=str(defaults["ds"]),
            pillar=str(defaults.get("pillar", "Platform")),
        )


def build() -> int:
    writer = Cat25Writer(append=True)
    for sub in TARGET_SUBS:
        emit_specs(writer, sub, SPECS[sub])
    total, counts = writer.summary()
    expected_total = EXPECTED_PER_SUB * len(TARGET_SUBS)
    assert total == expected_total, f"expected {expected_total} UCs, wrote {total}"
    for sub in TARGET_SUBS:
        assert counts.get(sub, 0) == EXPECTED_PER_SUB, f"subcategory 25.{sub} wrote {counts.get(sub, 0)}"
    return total


def main() -> int:
    total = build()
    print(f"{SCRIPT_PATH}\t{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
