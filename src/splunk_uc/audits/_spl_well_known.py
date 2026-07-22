"""Curated baseline of well-known Splunkbase TA sourcetypes and ESCU macros.

Goal: keep the ``audit-spl-references`` MEDIUM tier surfaceable without
forcing every contributor to vendor the entire ESCU repo and every
Splunkbase add-on into ``external/``. Anything in this file is treated
as known-good vocabulary — i.e. the audit will not flag it as
"unknown".

What goes here:

* Sourcetypes from the **top public Splunkbase add-ons** (every one
  documented in the corresponding TA's README on Splunkbase). These
  are facts about Splunk's published add-on conventions, not creative
  expression.
* Macros shipped by **Splunk's Enterprise Security Content Update**
  (`splunk/security_content`_, Apache-2.0). These are the macros
  every modern detection authoring workflow expects to be present.

What does NOT go here:

* Customer-specific or environment-specific identifiers — those go in
  the local reference corpus emitted by
  ``tools/research/build_spl_reference.py`` from ``external/``.
* Splunk-core SPL commands / eval functions / stats functions —
  those live in ``_spl_baseline.py``.

When an entry needs adding, prefer adding to this file over expanding
``_spl_baseline.py`` — it keeps the boundary between "Splunk core
language" and "well-known third-party content" explicit.

.. _`splunk/security_content`: https://github.com/splunk/security_content
"""

from __future__ import annotations

__all__ = [
    "WELL_KNOWN_SOURCETYPES",
    "WELL_KNOWN_MACROS",
    "WELL_KNOWN_INDEXES",
]


# ---------------------------------------------------------------------------
# Sourcetypes from popular Splunkbase Technology Add-ons.
#
# Each grouping cites the TA on Splunkbase. Where a TA defines a parametric
# family (e.g. WinEventLog:<channel>) we list the most common channels;
# wildcarded uses (`sourcetype="WinEventLog:*"`) are handled by the
# parser's `is_wildcard` flag and never reach the audit.
# ---------------------------------------------------------------------------
WELL_KNOWN_SOURCETYPES: set[str] = {
    # Splunk Add-on for Microsoft Windows (TA-windows) — Splunkbase 742
    "WinEventLog",
    "WinEventLog:Security",
    "WinEventLog:System",
    "WinEventLog:Application",
    "WinEventLog:Setup",
    "WinEventLog:DNS Server",
    "WinEventLog:Microsoft-Windows-PowerShell/Operational",
    "WinEventLog:Microsoft-Windows-Sysmon/Operational",
    "WinEventLog:Microsoft-Windows-AppXDeploymentServer/Operational",
    "WinEventLog:Microsoft-Windows-PrintService/Operational",
    "WinEventLog:Microsoft-Windows-WMI-Activity/Operational",
    "WinEventLog:Microsoft-Windows-TaskScheduler/Operational",
    "WinEventLog:Microsoft-Windows-Bits-Client/Operational",
    "WinEventLog:Microsoft-Windows-Windows Defender/Operational",
    "WinEventLog:ForwardedEvents",
    "XmlWinEventLog",
    "XmlWinEventLog:Security",
    "XmlWinEventLog:System",
    "XmlWinEventLog:Application",
    "XmlWinEventLog:Microsoft-Windows-PowerShell/Operational",
    "XmlWinEventLog:Microsoft-Windows-Sysmon/Operational",
    "XmlWinEventLog:Microsoft-Windows-AppXDeploymentServer/Operational",
    "WinHostMon",
    "WinRegistry",
    "WinPrintMon",
    "WinNetMon",
    "MSAD:NT6:DNS",
    "Perfmon",
    "Perfmon:CPU",
    "Perfmon:Memory",
    "Perfmon:LogicalDisk",
    "Perfmon:Network",
    # Splunk Add-on for Sysmon (Splunkbase 1914)
    "sysmon",
    "Sysmon",
    # Splunk Add-on for Linux / Unix (TA-nix) — Splunkbase 833
    "linux_secure",
    "syslog",
    "linux_audit",
    "auditd",
    "Unix:Service",
    "Unix:Uptime",
    "Unix:Version",
    "Unix:Update",
    "Unix:UserAccounts",
    "Unix:VSFTPDLog",
    "Unix:CPUTime",
    "Unix:DiskSpace",
    "Unix:File",
    "Unix:Hardware",
    "Unix:NetworkPorts",
    "Unix:NetworkInterface",
    "Unix:Process",
    "ps",
    "df",
    "vmstat",
    "iostat",
    "top",
    "lastlog",
    "interfaces",
    "openPorts",
    "package",
    "usersWithLoginPrivs",
    "osx_secure",
    "Unix:SSHDConfig",
    # Splunk Add-on for Active Directory / LDAP — Splunkbase 1151
    "MSAD:NT6:Replication",
    "MSAD:NT6:Health",
    "ActiveDirectory",
    # Splunk Add-on for AWS — Splunkbase 1876
    "aws:cloudtrail",
    "aws:cloudwatch",
    "aws:cloudwatchlogs",
    "aws:cloudwatchlogs:vpcflow",
    "aws:cloudwatchlogs:guardduty",
    "aws:cloudwatchlogs:eks",
    "aws:cloudwatchlogs:cloudtrail",
    "aws:cloudwatchlogs:waf",
    "aws:config",
    "aws:config:notification",
    "aws:config:rule",
    "aws:description",
    "aws:elb:accesslogs",
    "aws:cloudfront:accesslogs",
    "aws:s3:accesslogs",
    "aws:s3",
    "aws:rds:audit",
    "aws:rds:slowquery",
    "aws:billing",
    "aws:billing:cur",
    "aws:cur",
    "aws:guardduty",
    "aws:inspector",
    "aws:inspector:findings",
    "aws:macie",
    "aws:waf",
    "aws:vpcflow",
    "aws:lambda:cloudwatchlogs",
    "aws:firehose:json",
    "aws:metadata",
    "aws:cloudtrail:digest",
    "aws:securityhub:findings",
    # Microsoft Azure / Office 365 — Splunkbase 3757 / 4055
    "azure:audit",
    "azure:resource:graph",
    "azure:monitor:activity",
    "azure:monitor:resource",
    "azure:monitor:aad",
    "azure_monitor_aad",
    "azure:graph:audit",
    "azure:eventhub",
    "ms:aad:audit",
    "ms:aad:signin",
    "ms:aad:auditlog",
    "ms:o365:management",
    "o365:management:activity",
    "o365:management:activity:azureactivedirectory",
    "o365:management:activity:exchange",
    "o365:management:activity:sharepoint",
    "o365:management:activity:onedrive",
    "ms:defender:atp:alerts",
    "ms:defender:atp:advancedhuntingschema",
    "ms:defender:m365",
    # Google Cloud Platform / GCP — Splunkbase 3088
    "google:gcp:pubsub:message",
    "google_gcp_pubsub_message",
    "google:gcp:billing:resource",
    "google:gcp:billing:report",
    "google:gcp:audit",
    "google:gcp:resource:asset",
    "gws:reports:login",
    "gws:reports:admin",
    "gws:reports:drive",
    "gws:reports:meet",
    "gws:reports:saml",
    "gws:reports:user_accounts",
    "gws:reports:groups_enterprise",
    # Splunk Connect for Kubernetes — Splunkbase 4467
    "kube:objects:events",
    "kube:objects:metrics",
    "kube:objects:pods",
    "kube:objects:nodes",
    "kube:container",
    "kube:container:logs",
    "kube:objects:configmaps",
    "kube:objects:deployments",
    "kube:objects:replicasets",
    "kube:objects:services",
    "kube:objects:statefulsets",
    "kube:objects:namespaces",
    "kube:objects:secrets",
    "kube:objects:ingresses",
    "kube:objects:persistentvolumeclaims",
    "kube:objects:cronjobs",
    "kube:objects:jobs",
    "kube:audit",
    # Splunk Add-on for ServiceNow — Splunkbase 1928
    "snow:incident",
    "snow:problem",
    "snow:change_request",
    "snow:change_task",
    "snow:cmdb_ci",
    "snow:em_event",
    "snow:em_alert",
    "snow:sys_user",
    "snow:incident_sla",
    "snow:audit",
    # Splunk Add-on for Cisco ASA / Firepower — Splunkbase 1620
    "cisco:asa",
    "cisco:fwsm",
    "cisco:pix",
    "cisco:ftd",
    "cisco:firepower",
    "cisco:firepower:syslog",
    "cisco:firepower:event",
    "cisco:firepower:host",
    "cisco:firepower:flow",
    "cisco:firepower:malware",
    "cisco:firepower:intrusion",
    "cisco:firepower:correlation",
    # Splunk Add-on for Cisco IOS — Splunkbase 1467
    "cisco:ios",
    "cisco:iosxe",
    "cisco:iosxr",
    "cisco:nxos",
    "cisco:wlc:syslog",
    "cisco:catalyst:wireless",
    # Splunk Add-on for Cisco UCS — Splunkbase 1734
    "cisco:ucs:inventory",
    "cisco:ucs:stats",
    "cisco:ucs:fault",
    "cisco:ucs:event",
    # Cisco Meraki — Splunkbase 5197
    "meraki",
    "meraki:flows",
    "meraki:syslog",
    "meraki:events",
    "meraki:airmarshal",
    "meraki:urls",
    "meraki:ids",
    "meraki:wireless",
    "meraki_security_events",
    "meraki_appliance_events",
    "meraki:wirelessHealth",
    # Cisco Catalyst Center / DNAC — Splunkbase 5811
    "cisco:dnac:devicehealth",
    "cisco:dnac:clienthealth",
    "cisco:dnac:networkhealth",
    "cisco:dnac:issue",
    "cisco:dnac:compliance",
    # Cisco Cyber Vision — Splunkbase 5403
    "cybervision:event",
    "cybervision:alert",
    # Splunk Add-on for Palo Alto Networks — Splunkbase 2757
    "pan:traffic",
    "pan:threat",
    "pan:system",
    "pan:config",
    "pan:hipmatch",
    "pan:hipmatch_general_health",
    "pan:url",
    "pan:wildfire",
    "pan:wildfire_report",
    "pan:globalprotect",
    "pan:userid",
    "pan:correlation",
    "pan:authentication",
    "pan:data",
    "pan:decryption",
    "pan:gtp",
    "pan:dns",
    # Fortinet FortiGate / FortiAnalyzer — Splunkbase 2846
    "fgt_event",
    "fgt_traffic",
    "fgt_utm",
    "fgt_log",
    "fortigate_traffic",
    "fortigate_event",
    "fortigate_utm",
    # Check Point — Splunkbase 4293
    "opsec",
    "checkpoint:opsec",
    "cp_log",
    # Juniper Networks — Splunkbase 2847
    "juniper:firewall",
    "juniper:idp",
    "juniper:junos",
    "juniper:junos:firewall",
    "juniper:junos:idp",
    "juniper:junos:traffic",
    # F5 BIG-IP — Splunkbase 2680
    "f5:bigip:apm:syslog",
    "f5:bigip:asm:syslog",
    "f5:bigip:ltm:syslog",
    "f5:bigip:irule:syslog",
    "f5:silverline:asm",
    # Tenable / Nessus / Tenable.io / Tenable.sc — Splunkbase 1418
    "tenable:io:vuln",
    "tenable:io:assets",
    "tenable:io:plugins",
    "tenable:sc:vuln",
    "tenable:vuln",
    "tenable:asset",
    "tenable:plugin",
    "nessus_scan",
    # Qualys — Splunkbase 2964
    "qualys:hostDetection",
    "qualys:hostsummary",
    "qualys_knowledgebase",
    "qualys_vm_detection",
    "qualys:vmdr:knowledgebase",
    "qualys:vmdr:vulnerability",
    # CrowdStrike Falcon — Splunkbase 4710
    "CrowdStrike:Detection",
    "CrowdStrike:Audit",
    "CrowdStrike:Telemetry",
    "CrowdStrike:Hosts",
    "crowdstrike:falconhost:json",
    "crowdstrike:falconhost",
    # Carbon Black — Splunkbase 1085 / 5219
    "bit9:carbonblack:json",
    "carbonblack:edr",
    "carbonblack:cb:edr:event",
    "vmware:cb:edr",
    # SentinelOne — Splunkbase 4988
    "sentinelone:cef",
    "sentinelone:event",
    # Symantec Endpoint Protection — Splunkbase 2772
    "symantec:ep:agt:file",
    "symantec:ep:proactive:file",
    "symantec:ep:scan:file",
    "symantec:ep:syslog",
    # Trend Micro — Splunkbase 5403
    "trendmicro:officescan",
    "trendmicro:deepsecurity",
    # GitHub Actions — Splunkbase 5536
    "github:actions",
    "github:audit",
    "github:webhook",
    "github:enterprise:audit",
    # GitLab — Splunkbase 5234
    "gitlab:audit",
    "gitlab:application",
    # Atlassian Jira / Confluence — Splunkbase 5219
    "atlassian:jira:audit",
    "atlassian:confluence:access",
    # Okta — Splunkbase 2806
    "OktaIM2:log",
    "OktaIM2:groups",
    "OktaIM2:users",
    "OktaIM2:apps",
    "okta:im2:log",
    "okta:im2",
    "okta",
    # Duo Security — Splunkbase 3504
    "duo:authentication",
    "duo:administrator",
    "duo:telephony",
    "duo:offlineenrollment",
    # CyberArk — Splunkbase 3393
    "cyberark:epv:cef",
    "cyberark:epm",
    # Zscaler — Splunkbase 3865
    "zscalernss-fw",
    "zscalernss-web",
    "zscalernss-dns",
    "zscaler:web",
    "zscaler:firewall",
    "zscaler:zia:weblog",
    "zscaler:zia:dnslog",
    "zscaler:zpa:auditlog",
    # Forcepoint — Splunkbase 3500
    "forcepoint:one",
    "forcepoint:web",
    "forcepoint:email",
    "forcepoint:dlp",
    # Splunk Stream — Splunkbase 1812
    "stream:dns",
    "stream:http",
    "stream:tcp",
    "stream:udp",
    "stream:tls",
    "stream:smtp",
    "stream:icmp",
    "stream:smb",
    "stream:ldap",
    "stream:smb2",
    "stream:mysql",
    "stream:ftp",
    # Splunk Enterprise / Splunk Cloud platform internals
    "splunkd",
    "splunkd_access",
    "splunkd_ui_access",
    "splunkd_remote_searches",
    "splunk_web_access",
    "splunk_web_service",
    "splunk_resource_usage",
    "splunk_disk_objects",
    "scheduler",
    "audittrail",
    "audit",
    "metrics",
    "dispatch",
    "splunk_python",
    "license_usage",
    "btool",
    # Web servers
    "access_combined",
    "access_combined_wcookie",
    "access_common",
    "apache:access",
    "apache:error",
    "iis",
    "ms:iis:auto",
    "ms:iis:default",
    "nginx:access",
    "nginx:error",
    "nginx:plus:access",
    # Databases
    "oracle:auditDB",
    "oracle:audit",
    "mysql:error",
    "mysql:slow",
    "mssql:errorlog",
    "postgres:errorlog",
    # Load balancers / proxies
    "haproxy",
    "haproxy:tcp",
    "haproxy:http",
    "squid:access",
    # Open-source observability
    "redis:info",
    "memcached:stats",
    "zookeeper:mntr",
    "kafka:logs",
    "elasticsearch:logs",
    "elasticsearch:slowlogs",
    "vault:audit",
    "consul:metrics",
    "consul:logs",
    "etcd:metrics",
    "rabbitmq:metrics",
    "rabbitmq:logs",
    "mongodb:errorlog",
    "mongodb:slowQueries",
    # Prometheus / OTel
    "prometheus:metrics",
    "prometheus:ocp",
    "otel:metrics",
    "otel:logs",
    "otel:traces",
    # Cloud-native / CI
    "kafka:metrics",
    "consul:health",
    # ServiceNow / ITSM
    "servicenow:incident",
    "servicenow:cmdb",
    # Backup / DR
    "veeam:job",
    "veeam:event",
    "veeam:repository",
    # Misc Cisco
    "cisco:ise:syslog",
    "cisco:ise:radius",
    "cisco:asa:syslog",
    "cisco:netflow",
    "cisco:secureendpoint:event",
    "cisco:secureendpoint:webhook",
    # Generic open formats
    "json",
    "xml",
    "csv",
    "cef",
    "leef",
    "key_value",
    "_json",
    # OPNsense / pfSense — community add-ons
    "opnsense:filterlog",
    "pfsense:filterlog",
    # ------------------------------------------------------------------
    # cat-24 Business Intelligence & Analytics Platforms — BI tooling and
    # modern-data-stack sourcetypes. These are the canonical ingest names
    # for the admin/audit logs, REST-API scripted inputs, and DB Connect
    # probes documented in each UC's ``dataSources`` field.
    # ------------------------------------------------------------------
    # BI tools
    "tableau:backgrounder",
    "tableau:vizqlserver",
    "tableau:dataserver",
    "tableau:httpd",
    "tableau:vizportal",
    "tableau:licensing",
    "tableau:tsm:metrics",
    "powerbi:admin:refreshes",
    "powerbi:admin:api",
    "powerbi:gateway:info",
    "powerbi:gateway:mashup",
    "powerbi:capacity:metrics",
    "looker:system_activity",
    "looker:api",
    "looker:lookml_validation",
    "qlik:scheduler",
    "qlik:engine",
    "qlik:proxy",
    "superset:app",
    "metabase:app",
    "redash:app",
    "bi:embed:client",
    "microstrategy:dsserror",
    "cognos:audit",
    "businessobjects:audit",
    "oracle:analytics:usage",
    "thoughtspot:audit",
    # Data orchestration / transformation
    "airflow:scheduler",
    "airflow:task",
    "dbt:run_results",
    "dbt:sources",
    "dbt:semantic_layer",
    # Data ingestion / ELT
    "fivetran:log",
    "airbyte:job",
    "kafka:connect",
    "aws:cloudwatch:glue",
    "azure:monitor:adf",
    # Data quality & observability
    "montecarlo:incident",
    "great_expectations:validation",
    "soda:scan",
    "dbx:warehouse_freshness",
    "dbx:warehouse_rowcounts",
    "dbx:warehouse_columns",
    "dbx:warehouse_nullrates",
    "dbx:metric_probe",
    # Catalog / lineage / governance
    "collibra:audit",
    "atlan:audit",
    "openlineage:event",
    "unity_catalog:audit",
    "purview:scan",
    # Semantic / metrics layer
    "cube:api",
    # Reverse ETL & activation
    "hightouch:sync",
    "census:sync",
    "segment:delivery",
    "rudderstack:delivery",
    # ------------------------------------------------------------------
    # Phase 1 — data-engineering depth (24.7 / 24.8 / 24.9)
    # ------------------------------------------------------------------
    # Orchestration
    "airflow:worker",
    "airflow:statsd",
    "dagster:daemon",
    "dagster:run",
    "dagster:event",
    "prefect:worker",
    "prefect:agent",
    "prefect:api",
    "dbtcloud:run",
    "controlm:job",
    "controlm:em",
    "controlm:agent",
    # Ingestion / ELT
    "fivetran:connector",
    "airbyte:worker",
    "kafkaconnect:status",
    "kafkaconnect:worker",
    "kafkaconnect:jmx",
    "aws:glue:jobrun",
    "azure:datafactory",
    "matillion:task",
    "informatica:session",
    # Data quality & observability
    "greatexpectations:validation",
    "bigeye:issue",
    # ------------------------------------------------------------------
    # Phase 2 — BI-tool breadth (24.3 / 24.4 / 24.5 / 24.6)
    # ------------------------------------------------------------------
    "qlik:qrs",
    "domo:activity",
    # ------------------------------------------------------------------
    # Phase 3 — governance & activation (24.10 / 24.11 / 24.12 / 24.13)
    # ------------------------------------------------------------------
    "semantic_layer:query",
    # ------------------------------------------------------------------
    # Phase 4 — monitoring-angle matrix (breadth across the roster)
    # ------------------------------------------------------------------
    # BI tools
    "tableau:cloud:activity",
    "tableau:prep:flow",
    "fabric:capacity:metrics",
    "powerbi:dataflow",
    "powerbi:reportserver",
    "lookerstudio:usage",
    "qlik:cloud:audit",
    "qlik:nprinting",
    "qlikview:distribution",
    "preset:audit",
    "lightdash:app",
    "sigma:audit",
    "mode:audit",
    "hex:audit",
    "evidence:build",
    "sas:viya:audit",
    "sac:audit",
    "yellowfin:audit",
    "gooddata:audit",
    "sisense:audit",
    # Orchestration
    "argo:workflow",
    "astronomer:dag",
    "databricks:jobs",
    "aws:states:execution",
    "gcp:composer",
    "azure:synapse:pipeline",
    "mage:pipeline",
    "kestra:execution",
    # Ingestion / ELT
    "aws:dms:task",
    "gcp:dataflow",
    "stitch:extraction",
    "meltano:run",
    "hevo:pipeline",
    "dlt:load",
    "rivery:run",
    "informatica:iics",
    "talend:job",
    # Data quality & observability
    "elementary:test",
    "datafold:diff",
    "anomalo:check",
    "metaplane:monitor",
    "acceldata:policy",
    "lightup:check",
    # Catalog / lineage / governance
    "alation:audit",
    "atlan:audit",
    "datahub:event",
    "openmetadata:audit",
    "immuta:audit",
    "amundsen:event",
    "secoda:audit",
    # Semantic / metrics layer
    "atscale:query",
    "kyvos:query",
    # Reverse ETL & activation
    "segment:delivery",
    "polytomic:sync",
    "grouparoo:run",
    # ------------------------------------------------------------------
    # cat-25 Personal & Hobbyist Monitoring (the fun category)
    # ------------------------------------------------------------------
    # Fitness & activity
    "strava:activity",
    "garmin:activity",
    "fitbit:activity",
    "peloton:workout",
    "zwift:activity",
    # Health, sleep & wearables
    "apple:health",
    "oura:daily",
    "whoop:cycle",
    "withings:measure",
    "dexcom:egv",
    # Connected cars & EVs
    "tesla:vehicle",
    "tesla:charge",
    "obd:pid",
    "evcharger:session",
    # Smart home platforms & automation
    "homeassistant:event",
    "homey:flow",
    "nodered:event",
    # Smart home devices & sensors
    "zigbee2mqtt:device",
    "shelly:status",
    "ecobee:thermostat",
    # Home energy & solar
    "solaredge:power",
    "enphase:production",
    "powerwall:aggregate",
    "dsmr:telegram",
    "emporia:circuit",
    # Media, gaming & entertainment
    "tautulli:play",
    "jellyfin:activity",
    "spotify:play",
    "steam:player",
    "sonarr:event",
    # Home lab & self-hosting
    "truenas:pool",
    "docker:stats",
    "proxmox:metric",
    "nut:ups",
    "uptime:probe",
    "rpi:metric",
    "synology:disk",
    # Home network & connectivity
    "speedtest:result",
    "pihole:query",
    "unifi:event",
    # Weather, environment & garden
    "airgradient:sensor",
    "purpleair:aqi",
    "ecowitt:obs",
    "weatherflow:obs",
    "plant:sensor",
    "aquarium:sensor",
    # Pets & home life
    "whistle:activity",
    "tractive:position",
    "petfeeder:event",
    "litterrobot:cycle",
    "birdfeeder:detection",
    "doorbell:event",
    # Personal finance & crypto
    "crypto:price",
    "coinbase:txn",
    "firefly:txn",
    "wallet:balance",
    # Digital life & productivity
    "rescuetime:activity",
    "screentime:usage",
    "github:personal",
    "habit:entry",
    "calendar:event",
    "passwordmanager:audit",
    "email:metadata",
    # Travel, commute & flight-spotting
    "adsb:aircraft",
    "flight:log",
    "commute:trip",
    "transit:arrival",
    "geofence:event",
    "travel:document",
    "airprice:quote",
    # Kitchen, cooking & fermentation
    "sourdough:reading",
    "bbq:probe",
    "kitchen:appliance",
    "espresso:shot",
    "pantry:item",
    "kombucha:reading",
    # Homebrewing, beer & wine
    "brew:fermentation",
    "kegerator:pour",
    "winecellar:reading",
    # Making, 3D printing & workshop
    "octoprint:job",
    "printer:telemetry",
    "filament:spool",
    "cnc:job",
    "workshop:air",
    "tool:battery",
    # Home security & surveillance
    "frigate:event",
    "camera:health",
    "alarm:event",
    "lock:access",
    "plate:detection",
    # Water, plumbing & utilities
    "watermeter:flow",
    "sumppump:event",
    "wellpump:event",
    "pool:chemistry",
    "watersoftener:status",
    "irrigation:zone",
    # Citizen science & backyard sensing (25.20)
    "seismo:reading",
    "geiger:cpm",
    "lightning:strike",
    "radon:reading",
    "allsky:capture",
    "riverlevel:reading",
    "magnetometer:reading",
    "satpass:prediction",
    # Radio, SDR & space (25.21)
    "aprs:packet",
    "wspr:spot",
    "noaa:apt",
    "meteorscatter:ping",
    "sstv:image",
    # Backyard astronomy & observatory (25.22)
    "observatory:env",
    "skyquality:reading",
    "imaging:session",
    "mount:status",
    "allsky:cloud",
    # Family, baby & household chaos (25.23)
    "baby:feed",
    "baby:sleep",
    "diaper:change",
    "chore:completion",
    "allowance:ledger",
    "family:calendar",
    "growth:measurement",
    # Homestead, bees & livestock (25.24)
    "beehive:reading",
    "chickencoop:door",
    "egg:count",
    "livestock:tag",
    "feed:level",
    "pasture:sensor",
    # Advanced health & biohacking (25.25)
    "hrv:reading",
    "spo2:reading",
    "bloodpanel:result",
    "supplement:intake",
    "cgm:glucose",
    "apnea:event",
    "bodycomp:measure",
    "bloodpressure:reading",
    # Wildlife & biodiversity (25.26)
    "birdnet:detection",
    "trailcam:detection",
    "mothtrap:capture",
    "batdetector:pass",
    "pollinator:count",
    "wildlifecam:visit",
    # Aquariums, reptiles & vivariums (25.27)
    "reeftank:param",
    "vivarium:climate",
    "fishfeeder:event",
    "doser:event",
    "ato:event",
    "pondsensor:reading",
    # Sports, skills & training telemetry (25.28)
    "vbt:rep",
    "gait:metric",
    "hangboard:session",
    "golfswing:metric",
    "powermeter:interval",
    "shotarc:make",
}


# ---------------------------------------------------------------------------
# Macros from Splunk's published Enterprise Security Content Update
# (`splunk/security_content`, Apache-2.0). The catalogue here covers
# the macros most frequently invoked from detection SPL — keeping it
# narrow because every macro added here weakens the audit's ability
# to surface real hallucinations.
# ---------------------------------------------------------------------------
WELL_KNOWN_MACROS: set[str] = {
    # ------------------------------------------------------------------
    # Splunk Common Information Model (CIM) add-on — Splunkbase 1621
    # ------------------------------------------------------------------
    # ``cim_<datamodel>_indexes`` macros are the canonical entry points
    # CIM authors expect every dashboard / detection to use as the
    # data-source filter (lets the customer point each data model at
    # the indexes that hold their data without rewriting SPL). They are
    # documented in `docs.splunk.com/Documentation/CIM/.../Usage`.
    "cim_Alerts_indexes",
    "cim_Application_State_indexes",
    "cim_Authentication_indexes",
    "cim_Change_indexes",
    "cim_Compute_Inventory_indexes",
    "cim_DLP_indexes",
    "cim_Databases_indexes",
    "cim_Email_indexes",
    "cim_Endpoint_indexes",
    "cim_Event_Signatures_indexes",
    "cim_IDS_indexes",
    "cim_Inventory_indexes",
    "cim_JVM_indexes",
    "cim_Malware_indexes",
    "cim_Network_Resolution_indexes",
    "cim_Network_Sessions_indexes",
    "cim_Network_Traffic_indexes",
    "cim_Performance_indexes",
    "cim_Splunk_Audit_indexes",
    "cim_Ticket_Management_indexes",
    "cim_Updates_indexes",
    "cim_Vulnerabilities_indexes",
    "cim_Web_indexes",
    # ------------------------------------------------------------------
    # Splunk Enterprise utility macros (commonly published in dashboards
    # and the Splunk Lantern library; not strictly an add-on but every
    # mature production environment carries them or an equivalent).
    # ------------------------------------------------------------------
    # IP -> geo enrichment used in many Splunk-supplied compliance and
    # security dashboards. Documented in the Splunk Enterprise
    # Search Reference under the `iplocation` command guidance.
    "get_geolocation",
    # ------------------------------------------------------------------
    # Cisco ThousandEyes App for Splunk — Splunkbase 7719
    # ------------------------------------------------------------------
    # Index-aliasing macros the TA defines in `default/macros.conf`
    # so dashboards work against whichever index the deployer routes
    # ThousandEyes data into. See ``ta_cisco_thousandeyes`` README.
    "event_index",
    "path_viz_index",
    # Time / event helpers
    "security_content_ctime",
    "security_content_summariesonly",
    "summariesonly",
    "drop_dm_object_name",
    # Index aliases (every detection author defines these per environment;
    # they're also the exact list ESCU expects to be macroed):
    "wineventlog_security",
    "wineventlog_system",
    "wineventlog_application",
    "wineventlog_dns",
    "powershell",
    "sysmon",
    "azure_monitor_aad",
    "google_gcp_pubsub_message",
    "amazon_security_lake",
    "cloudtrail",
    "linux_audit",
    "linux_secure",
    "kubernetes_metrics",
    "kubernetes_objects",
    "stream_dns",
    "stream_http",
    "stream_index",
    "okta",
    "okta_im2",
    "o365_management_activity",
    "office365_management_activity",
    "github",
    "github_audit",
    "github_actions",
    "gws_reports",
    "ms_defender",
    "ms_defender_advanced_hunting",
    "circleci",
    "gitlab",
    # Process-related ESCU macros
    "process_wmic",
    "process_powershell",
    "process_net",
    "process_cmd",
    "process_rundll32",
    "process_regsvr32",
    "process_mshta",
    "process_certutil",
    "process_bitsadmin",
    "process_schtasks",
    "process_at",
    "process_psexec",
    "process_reg",
    "process_runas",
    "process_taskhost",
    "process_taskhostw",
    "process_winrshost",
    "process_winrm",
    "process_wsmprovhost",
    # Notable / risk framework macros (Splunk Enterprise Security)
    "notable",
    "risk",
    "incident_review",
    "es_notable",
    # MCP server data macros (ESCU adds these for MCP detections)
    "mcp_server",
    # Common URL toolbox macros (Splunk Add-on for URL Toolbox)
    "ut_parse",
    "ut_parse_extended",
    "ut_levenshtein",
    "ut_shannon",
    # AWS / Cloudtrail macros widely used in ESCU
    "comment",
}


# ---------------------------------------------------------------------------
# Indexes that always exist on a Splunk instance once the platform or a
# top-1 add-on is installed. These join ``BUILTIN_FIELD_TOKENS`` (Splunk
# core internal indexes) so the audit doesn't flag tenant-agnostic
# names like ``notable`` / ``risk`` / ``cim_modactions``.
# ---------------------------------------------------------------------------
WELL_KNOWN_INDEXES: set[str] = {
    # Splunk Enterprise Security
    "notable",
    "risk",
    "cim_modactions",
    "ioc",
    "threat_activity",
    "endpoint_summary",
    # Splunk IT Service Intelligence
    "itsi_summary",
    "itsi_grouped_alerts",
    "itsi_tracked_alerts",
    "itsi_kpi_summary",
    # Splunk Universal Forwarder boundary
    "summary",
}
