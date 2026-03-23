#!/usr/bin/env python3
"""
build.py — Compile per-category markdown files into data.js for the dashboard.

Usage:
    python3 build.py

Reads:
    use-cases/cat-*.md          — use case content (all data including CIM)
    use-cases/INDEX.md          — category metadata (icons, descriptions, starters)

Writes:
    data.js                     — const DATA, CAT_META, CAT_GROUPS, EQUIPMENT
    catalog.json                — machine-readable JSON catalog (same data as data.js)
    llms.txt                    — concise AI-agent index (llms.txt standard)
    llms-full.txt               — expanded AI-agent index with all use case titles
"""

import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UC_DIR = os.path.join(SCRIPT_DIR, "use-cases")
OUTPUT = os.path.join(SCRIPT_DIR, "data.js")
OUTPUT_CATALOG_JSON = os.path.join(SCRIPT_DIR, "catalog.json")
OUTPUT_LLMS_TXT = os.path.join(SCRIPT_DIR, "llms.txt")
OUTPUT_LLM_TXT = os.path.join(SCRIPT_DIR, "llm.txt")
OUTPUT_LLMS_FULL_TXT = os.path.join(SCRIPT_DIR, "llms-full.txt")

SITE_BASE_URL = "https://fenre.github.io/splunk-monitoring-use-cases"
RAW_GITHUB_URL = "https://raw.githubusercontent.com/fenre/splunk-monitoring-use-cases/main"

# Emoji → value mappings
CRITICALITY_MAP = {
    "🔴 critical": "critical", "critical": "critical",
    "🟠 high": "high", "high": "high",
    "🟡 medium": "medium", "medium": "medium",
    "🟢 low": "low", "low": "low",
}

DIFFICULTY_MAP = {
    "🟢 beginner": "beginner", "beginner": "beginner",
    "🔵 intermediate": "intermediate", "intermediate": "intermediate",
    "🟠 advanced": "advanced", "advanced": "advanced",
    "🔴 expert": "expert", "expert": "expert",
}

CAT_GROUPS = {
    "infra":      [1, 2, 5, 6, 15, 18, 19],
    "security":   [9, 10, 17],
    "cloud":      [3, 4, 20],
    "app":        [7, 8, 11, 12, 13, 14, 16],
    "industry":   [21],
    "compliance": [22],
}

# Splunk two-pillar strategy: Security / Observability
# Categories that default to "security" when no heuristic matches
PILLAR_SECURITY_CATS = {9, 10, 17}
# Title keywords that indicate a security-relevant use case (matched case-insensitively)
PILLAR_SECURITY_WORDS = [
    "attack", "malware", "threat", "vulnerability", "exploit", "breach",
    "intrusion", "phishing", "ransomware", "unauthorized", "suspicious",
    "abuse", "brute force", "privilege escalation", "ddos", "exfiltration",
    "credential", "compromise", "trojan", "botnet", "backdoor", "rootkit",
    "spyware", "injection", "evasion", "lateral movement", "reconnaissance",
    "command and control", "c2", "data theft", "fraud", "tampering",
    "insider threat", "rogue", "anomalous login", "impossible travel",
    "kerberoasting", "golden ticket", "pass-the-hash", "mimikatz",
    "zero day", "apt", "nation-state", "wiper", "ransomware",
]
# Monitoring type values that indicate observability
PILLAR_OBS_MTYPES = {"performance", "availability", "capacity", "fault", "configuration"}

# Equipment (IT assets) → TA patterns. Used to filter use cases by "what equipment do you have?"
# Each entry: id (slug), label (user-facing), tas (substrings; if any appears in UC's App/TA field, UC is relevant).
# Matching is case-insensitive substring: pattern.lower() in app_ta_field.lower()
EQUIPMENT = [
    # ── Operating Systems ──────────────────────────────────────────────────
    {"id": "linux", "label": "Linux / Unix servers", "tas": ["Splunk_TA_nix"]},
    {"id": "windows", "label": "Windows servers & workstations", "tas": ["Splunk_TA_windows"]},
    {"id": "macos", "label": "macOS", "tas": ["macOS", "Splunk UF for macOS"]},

    # ── Virtualization ─────────────────────────────────────────────────────
    {
        "id": "vmware",
        "label": "VMware",
        "tas": ["Splunk_TA_vmware", "TA-vmware", "VMware", "vSphere", "ESXi", "vCenter"],
        "models": [
            {"id": "vsphere", "label": "vSphere", "tas": ["vSphere", "vsphere"]},
            {"id": "esxi", "label": "ESXi", "tas": ["ESXi", "esxi"]},
            {"id": "vcenter", "label": "vCenter", "tas": ["vCenter", "vcenter"]},
            {"id": "ta_vmware", "label": "Splunk TA for VMware", "tas": ["Splunk_TA_vmware", "TA-vmware"]},
        ],
    },
    {"id": "hyperv", "label": "Microsoft Hyper-V", "tas": ["Hyper-V", "hyperv", "HyperV", "Perfmon:HyperV"]},
    {"id": "proxmox", "label": "Proxmox VE", "tas": ["Proxmox", "proxmox"]},
    {"id": "ovirt", "label": "oVirt / Red Hat Virtualization", "tas": ["oVirt", "ovirt", "RHV", "rhv"]},
    {"id": "openstack", "label": "OpenStack", "tas": ["OpenStack", "openstack"]},

    # ── HCI & Converged ────────────────────────────────────────────────────
    {
        "id": "nutanix",
        "label": "Nutanix",
        "tas": ["Nutanix", "nutanix", "TA-nutanix", "Prism"],
        "models": [
            {"id": "prism_central", "label": "Prism Central", "tas": ["Prism Central"]},
            {"id": "prism_element", "label": "Prism Element", "tas": ["Prism Element"]},
        ],
    },
    {"id": "vxrail", "label": "Dell VxRail", "tas": ["VxRail", "vxrail"]},

    # ── Cloud Providers ────────────────────────────────────────────────────
    {"id": "aws", "label": "Amazon Web Services (AWS)", "tas": ["Splunk_TA_aws", "AWS", "CloudTrail", "CloudWatch"]},
    {"id": "azure", "label": "Microsoft Azure", "tas": ["Splunk_TA_microsoft-cloudservices", "Azure", "Azure Monitor", "Azure Activity"]},
    {"id": "gcp", "label": "Google Cloud Platform (GCP)", "tas": ["Splunk_TA_google-cloudplatform", "GCP", "Google Cloud"]},

    # ── Containers & Orchestration ─────────────────────────────────────────
    {
        "id": "kubernetes",
        "label": "Kubernetes",
        "tas": ["Kubernetes", "Splunk Connect for Kubernetes", "SCK", "kube-state-metrics", "kubelet"],
        "models": [
            {"id": "k8s", "label": "Kubernetes clusters", "tas": ["Kubernetes", "kube-state-metrics", "kubelet"]},
            {"id": "openshift", "label": "OpenShift", "tas": ["OpenShift", "openshift"]},
            {"id": "helm", "label": "Helm", "tas": ["Helm", "helm"]},
        ],
    },
    {"id": "docker", "label": "Docker", "tas": ["Docker", "docker", "Splunk Connect for Docker"]},
    {"id": "argocd", "label": "ArgoCD", "tas": ["ArgoCD", "argocd", "Argo CD"]},

    # ── Network Infrastructure ─────────────────────────────────────────────
    {
        "id": "cisco",
        "label": "Cisco",
        "tas": ["Splunk_TA_cisco", "Cisco", "cisco-firepower", "cisco-asa", "cisco-ios", "cisco-ise",
                "cisco_meraki", "Meraki", "cisco:ucs", "cisco:aci", "cisco:sdwan", "cisco:ucm",
                "cisco:wlc", "Webex", "TA-cisco_ios", "Cisco Catalyst Add-on", "Cisco Meraki Add-on",
                "Cisco Secure Firewall", "ThousandEyes", "Cisco ThousandEyes App"],
        "models": [
            {"id": "firepower", "label": "Cisco Firepower / Secure Firewall", "tas": ["Cisco Firepower", "cisco-firepower", "cisco:firepower", "Cisco Secure Firewall"]},
            {"id": "asa", "label": "Cisco ASA", "tas": ["Splunk_TA_cisco-asa", "Cisco ASA", "cisco-asa", "cisco:asa"]},
            {"id": "ios", "label": "Cisco IOS / Catalyst / ISR / ASR", "tas": ["TA-cisco_ios", "Cisco IOS", "cisco-ios", "cisco:ios"]},
            {"id": "ise", "label": "Cisco ISE", "tas": ["Splunk_TA_cisco-ise", "Cisco ISE", "cisco-ise", "cisco:ise"]},
            {"id": "meraki", "label": "Cisco Meraki", "tas": ["Cisco Meraki Add-on", "Cisco Meraki", "Meraki", "cisco_meraki", "meraki"]},
            {"id": "ucs", "label": "Cisco UCS", "tas": ["Splunk_TA_cisco-ucs", "Cisco UCS", "cisco:ucs", "UCS Manager"]},
            {"id": "aci", "label": "Cisco ACI", "tas": ["cisco:aci", "Cisco ACI", "ACI", "APIC", "TA_cisco-ACI"]},
            {"id": "sdwan", "label": "Cisco SD-WAN / Catalyst Center", "tas": ["cisco:sdwan", "Cisco SD-WAN", "vManage", "Cisco Catalyst Add-on"]},
            {"id": "wlc", "label": "Cisco WLC / Catalyst 9800", "tas": ["cisco:wlc", "Cisco WLC", "WLC"]},
            {"id": "ucm", "label": "Cisco UCM / Unified Communications", "tas": ["cisco:ucm", "Cisco UCM", "UCM CDR", "CUCM"]},
            {"id": "webex", "label": "Cisco Webex", "tas": ["Webex", "webex", "ta_cisco_webex"]},
            {"id": "spaces", "label": "Cisco Spaces", "tas": ["Cisco Spaces", "cisco:spaces", "cisco_spaces", "Spaces Add-On"]},
            {"id": "thousandeyes", "label": "Cisco ThousandEyes", "tas": ["ThousandEyes", "thousandeyes", "Cisco ThousandEyes App"]},
        ],
    },
    {
        "id": "paloalto",
        "label": "Palo Alto Networks",
        "tas": ["Splunk_TA_paloalto", "Palo Alto", "GlobalProtect", "Prisma"],
        "models": [
            {"id": "pan_firewall", "label": "Palo Alto Firewall / PAN-OS", "tas": ["Splunk_TA_paloalto", "Palo Alto", "PAN-OS", "paloalto"]},
            {"id": "globalprotect", "label": "GlobalProtect", "tas": ["GlobalProtect", "globalprotect"]},
            {"id": "prisma", "label": "Prisma Access", "tas": ["Prisma", "prisma"]},
        ],
    },
    {
        "id": "fortinet",
        "label": "Fortinet",
        "tas": ["Fortinet", "FortiGate", "Splunk_TA_fortinet", "TA-fortinet_fortigate"],
        "models": [
            {"id": "fortigate", "label": "FortiGate", "tas": ["FortiGate", "fortigate", "Splunk_TA_fortinet", "TA-fortinet_fortigate"]},
            {"id": "fortianalyzer", "label": "FortiAnalyzer", "tas": ["FortiAnalyzer", "fortianalyzer"]},
        ],
    },
    {
        "id": "f5",
        "label": "F5",
        "tas": ["Splunk_TA_f5-bigip", "F5", "BIG-IP", "f5-bigip"],
        "models": [
            {"id": "bigip", "label": "F5 BIG-IP", "tas": ["Splunk_TA_f5-bigip", "BIG-IP", "f5-bigip", "bigip"]},
            {"id": "asm", "label": "F5 ASM", "tas": ["ASM", "f5-bigip (ASM)"]},
        ],
    },
    {
        "id": "citrix",
        "label": "Citrix",
        "tas": ["Splunk_TA_citrix-netscaler", "citrix", "NetScaler"],
        "models": [
            {"id": "netscaler", "label": "Citrix NetScaler / ADC", "tas": ["Splunk_TA_citrix-netscaler", "citrix", "NetScaler", "netscaler"]},
        ],
    },
    {"id": "checkpoint", "label": "Check Point", "tas": ["Check Point", "checkpoint", "CheckPoint"]},
    {"id": "nsx", "label": "VMware NSX", "tas": ["NSX", "nsx", "vmware_nsx_addon", "NSX-T"]},
    {
        "id": "infoblox",
        "label": "Infoblox",
        "tas": ["Splunk_TA_infoblox", "Infoblox", "infoblox"],
        "models": [
            {"id": "dns", "label": "Infoblox DNS", "tas": ["Infoblox DNS"]},
            {"id": "dhcp", "label": "Infoblox DHCP", "tas": ["Infoblox DHCP"]},
        ],
    },
    {
        "id": "netflow",
        "label": "NetFlow / sFlow",
        "tas": ["NetFlow", "netflow", "sFlow", "sflow"],
        "models": [
            {"id": "netflow", "label": "NetFlow", "tas": ["NetFlow", "netflow"]},
            {"id": "sflow", "label": "sFlow", "tas": ["sFlow", "sflow"]},
        ],
    },
    {
        "id": "snmp",
        "label": "SNMP",
        "tas": ["SNMP", "snmp"],
        "models": [
            {"id": "generic", "label": "SNMP (generic)", "tas": ["SNMP", "snmp"]},
            {"id": "pdu", "label": "PDU / power", "tas": ["PDU", "PDU-MIB", "pdu"]},
            {"id": "ups", "label": "UPS", "tas": ["UPS", "UPS-MIB", "ups"]},
            {"id": "apc", "label": "APC / Schneider Electric", "tas": ["APC", "PowerNet-MIB", "InRow", "AirIR"]},
        ],
    },
    {"id": "syslog", "label": "Syslog (generic)", "tas": ["Splunk_TA_syslog", "Syslog", "syslog"]},

    # ── Web Servers & Reverse Proxies ──────────────────────────────────────
    {
        "id": "apache",
        "label": "Apache HTTP Server",
        "tas": ["Splunk_TA_apache", "apache"],
        "models": [
            {"id": "httpd", "label": "Apache httpd", "tas": ["Splunk_TA_apache", "apache", "httpd"]},
        ],
    },
    {
        "id": "nginx",
        "label": "NGINX",
        "tas": ["TA-nginx", "nginx", "NGINX"],
        "models": [
            {"id": "open", "label": "NGINX Open Source", "tas": ["TA-nginx", "nginx", "NGINX"]},
            {"id": "plus", "label": "NGINX Plus", "tas": ["NGINX Plus", "nginx plus"]},
        ],
    },
    {"id": "iis", "label": "Microsoft IIS", "tas": ["IIS", "Microsoft IIS", "Splunk Add-on for Microsoft IIS"]},
    {"id": "haproxy", "label": "HAProxy", "tas": ["HAProxy", "haproxy"]},
    {"id": "traefik", "label": "Traefik", "tas": ["Traefik", "traefik"]},

    # ── Application Servers ────────────────────────────────────────────────
    {"id": "tomcat", "label": "Apache Tomcat", "tas": ["Tomcat", "tomcat", "Catalina"]},
    {"id": "jboss", "label": "WildFly / JBoss", "tas": ["WildFly", "JBoss", "wildfly", "jboss"]},
    {"id": "phpfpm", "label": "PHP-FPM", "tas": ["PHP-FPM", "php-fpm"]},

    # ── Caching & Proxy ────────────────────────────────────────────────────
    {"id": "varnish", "label": "Varnish Cache", "tas": ["Varnish", "varnish"]},
    {"id": "squid", "label": "Squid Proxy", "tas": ["Squid", "squid"]},
    {"id": "memcached", "label": "Memcached", "tas": ["Memcached", "memcached"]},
    {"id": "envoy", "label": "Envoy Proxy", "tas": ["Envoy", "envoy"]},

    # ── Databases ──────────────────────────────────────────────────────────
    {
        "id": "db_connect",
        "label": "Splunk DB Connect",
        "tas": ["DB Connect", "splunk_app_db_connect"],
    },
    {"id": "mssql", "label": "Microsoft SQL Server", "tas": ["Splunk_TA_microsoft-sqlserver", "microsoft-sqlserver", "SQL Server"]},
    {
        "id": "oracle",
        "label": "Oracle Database",
        "tas": ["Splunk_TA_oracle", "Oracle"],
        "models": [
            {"id": "oracle_db", "label": "Oracle Database", "tas": ["Oracle", "oracle", "tablespace"]},
        ],
    },
    {
        "id": "postgresql",
        "label": "PostgreSQL",
        "tas": ["PostgreSQL", "postgresql", "PgBouncer", "pgbouncer"],
        "models": [
            {"id": "pg", "label": "PostgreSQL", "tas": ["PostgreSQL", "postgresql"]},
            {"id": "pgbouncer", "label": "PgBouncer", "tas": ["PgBouncer", "pgbouncer"]},
        ],
    },
    {"id": "mysql", "label": "MySQL / MariaDB", "tas": ["MySQL", "mysql", "MariaDB", "mariadb", "InnoDB"]},
    {
        "id": "mongodb",
        "label": "MongoDB",
        "tas": ["MongoDB", "mongodb", "mongosh"],
        "models": [
            {"id": "mongod", "label": "MongoDB Server", "tas": ["MongoDB", "mongodb", "mongosh"]},
            {"id": "wiredtiger", "label": "WiredTiger", "tas": ["WiredTiger", "wiredtiger"]},
        ],
    },
    {"id": "redis", "label": "Redis", "tas": ["Redis", "redis"]},
    {
        "id": "elasticsearch",
        "label": "Elasticsearch / OpenSearch",
        "tas": ["Elasticsearch", "elasticsearch", "ES REST API", "OpenSearch"],
        "models": [
            {"id": "es", "label": "Elasticsearch", "tas": ["Elasticsearch", "elasticsearch", "ES REST API"]},
            {"id": "opensearch", "label": "OpenSearch", "tas": ["OpenSearch", "opensearch"]},
        ],
    },
    {"id": "clickhouse", "label": "ClickHouse", "tas": ["ClickHouse", "clickhouse"]},
    {"id": "cassandra", "label": "Apache Cassandra", "tas": ["Cassandra", "cassandra", "nodetool"]},
    {"id": "snowflake", "label": "Snowflake", "tas": ["Snowflake", "snowflake"]},

    # ── Message Queues & Streaming ─────────────────────────────────────────
    {"id": "kafka", "label": "Apache Kafka", "tas": ["TA-kafka", "Kafka", "kafka", "Splunk Connect for Kafka"]},
    {"id": "rabbitmq", "label": "RabbitMQ", "tas": ["RabbitMQ", "rabbitmq"]},
    {"id": "activemq", "label": "Apache ActiveMQ", "tas": ["ActiveMQ", "activemq"]},
    {"id": "zookeeper", "label": "Apache ZooKeeper", "tas": ["ZooKeeper", "zookeeper"]},

    # ── HashiCorp ──────────────────────────────────────────────────────────
    {
        "id": "hashicorp",
        "label": "HashiCorp",
        "tas": ["Vault", "Consul", "Nomad", "HashiCorp", "Terraform"],
        "models": [
            {"id": "vault", "label": "HashiCorp Vault", "tas": ["Vault"]},
            {"id": "consul", "label": "HashiCorp Consul", "tas": ["Consul"]},
            {"id": "nomad", "label": "HashiCorp Nomad", "tas": ["Nomad"]},
            {"id": "terraform", "label": "Terraform", "tas": ["Terraform", "terraform"]},
        ],
    },

    # ── Storage ────────────────────────────────────────────────────────────
    {"id": "netapp", "label": "NetApp", "tas": ["TA-netapp_ontap", "NetApp", "netapp", "ONTAP"]},
    {"id": "pure_storage", "label": "Pure Storage", "tas": ["Pure Storage", "FlashArray", "FlashBlade"]},
    {"id": "dell_emc", "label": "Dell EMC Storage", "tas": ["Dell EMC", "Isilon", "PowerStore", "Unity", "EqualLogic"]},
    {"id": "truenas", "label": "TrueNAS / FreeNAS", "tas": ["TrueNAS", "truenas", "FreeNAS", "freenas"]},
    {"id": "ceph", "label": "Ceph", "tas": ["Ceph", "ceph"]},

    # ── Backup & Data Protection ───────────────────────────────────────────
    {"id": "veeam", "label": "Veeam", "tas": ["Veeam", "veeam"]},
    {"id": "commvault", "label": "Commvault", "tas": ["Commvault", "commvault"]},

    # ── Identity & Access ──────────────────────────────────────────────────
    {"id": "okta", "label": "Okta", "tas": ["Splunk_TA_okta", "okta"]},
    {"id": "cyberark", "label": "CyberArk", "tas": ["Splunk_TA_cyberark", "CyberArk", "cyberark"]},
    {"id": "beyondtrust", "label": "BeyondTrust", "tas": ["BeyondTrust", "beyondtrust"]},

    # ── Microsoft Ecosystem ────────────────────────────────────────────────
    {"id": "m365", "label": "Microsoft 365 / Entra ID", "tas": ["Splunk_TA_MS_O365", "MS_O365", "Office 365", "Entra", "M365", "microsoft-cloudservices"]},
    {"id": "exchange", "label": "Microsoft Exchange", "tas": ["Splunk_TA_microsoft-exchange", "microsoft-exchange", "Exchange"]},
    {"id": "sharepoint", "label": "Microsoft SharePoint", "tas": ["SharePoint", "sharepoint", "SPOSite"]},

    # ── Security Platforms ─────────────────────────────────────────────────
    {"id": "security_essentials", "label": "Splunk Security Essentials (ESCU)", "tas": ["Security Essentials", "ESCU"]},
    {"id": "crowdstrike", "label": "CrowdStrike Falcon", "tas": ["CrowdStrike", "crowdstrike", "Falcon"]},
    {"id": "defender", "label": "Microsoft Defender", "tas": ["Microsoft Defender", "Defender for"]},
    {"id": "tenable", "label": "Tenable / Nessus", "tas": ["Tenable", "tenable", "Nessus"]},
    {"id": "qualys", "label": "Qualys", "tas": ["Qualys", "qualys"]},
    {"id": "proofpoint", "label": "Proofpoint", "tas": ["Proofpoint", "proofpoint", "TA-proofpoint"]},
    {"id": "suricata", "label": "Suricata / Snort (IDS/IPS)", "tas": ["Suricata", "suricata", "TA-suricata", "Snort", "snort"]},
    {"id": "zscaler", "label": "Zscaler", "tas": ["Zscaler", "zscaler"]},

    # ── DevOps & CI/CD ─────────────────────────────────────────────────────
    {"id": "jenkins", "label": "Jenkins", "tas": ["Jenkins", "jenkins"]},
    {"id": "github", "label": "GitHub", "tas": ["GitHub", "github"]},
    {"id": "gitlab", "label": "GitLab", "tas": ["GitLab", "gitlab"]},
    {"id": "ansible", "label": "Ansible", "tas": ["Ansible", "ansible"]},
    {"id": "controlm", "label": "Control-M", "tas": ["Control-M", "control-m"]},

    # ── Monitoring & Observability ─────────────────────────────────────────
    {"id": "itsi", "label": "Splunk ITSI", "tas": ["ITSI", "Splunk ITSI"]},
    {"id": "stream", "label": "Splunk Stream", "tas": ["Splunk Stream", "Splunk App for Stream"]},
    {"id": "opentelemetry", "label": "OpenTelemetry", "tas": ["OpenTelemetry", "OTel Collector", "Splunk_TA_otel", "otelcol"]},
    {"id": "prometheus", "label": "Prometheus", "tas": ["Prometheus", "prometheus"]},
    {"id": "grafana", "label": "Grafana", "tas": ["Grafana", "grafana"]},
    {
        "id": "log_pipeline",
        "label": "Log Pipeline (Fluentd / Fluent Bit)",
        "tas": ["Fluentd", "fluentd", "Fluent Bit", "fluent bit"],
    },

    # ── ITSM & Incident Management ─────────────────────────────────────────
    {"id": "servicenow", "label": "ServiceNow", "tas": ["Splunk_TA_snow", "snow", "ServiceNow"]},
    {"id": "jira", "label": "Atlassian Jira", "tas": ["Jira", "jira"]},
    {"id": "pagerduty", "label": "PagerDuty / Opsgenie", "tas": ["PagerDuty", "pagerduty", "Opsgenie", "opsgenie"]},

    # ── IoT & Operational Technology ───────────────────────────────────────
    {"id": "edge_hub", "label": "Splunk Edge Hub", "tas": ["Splunk Edge Hub", "Edge Hub"]},
    {"id": "modbus", "label": "Modbus (TCP/RTU)", "tas": ["Modbus", "modbus"]},
    {"id": "opcua", "label": "OPC-UA", "tas": ["OPC-UA", "opc-ua", "OPC UA", "opcua"]},
    {"id": "mqtt", "label": "MQTT", "tas": ["MQTT", "mqtt", "Mosquitto", "HiveMQ"]},
    {"id": "aranet", "label": "Aranet Sensors", "tas": ["Aranet", "aranet"]},

    # ── Telephony & UC ─────────────────────────────────────────────────────
    {"id": "asterisk", "label": "Asterisk / FreePBX", "tas": ["Asterisk", "asterisk", "FreePBX", "freepbx", "AMI"]},

    # ── Hardware / BMC ─────────────────────────────────────────────────────
    {
        "id": "hardware_bmc",
        "label": "Hardware / BMC",
        "tas": ["ipmitool", "iDRAC", "iLO", "smartctl", "storcli", "megacli", "BMC", "edac-util", "ssacli", "dmidecode", "perccli", "hpssacli"],
        "models": [
            {"id": "idrac", "label": "Dell iDRAC", "tas": ["iDRAC", "idrac"]},
            {"id": "ilo", "label": "HPE iLO", "tas": ["iLO", "ilo"]},
            {"id": "ipmi", "label": "IPMI (generic)", "tas": ["ipmitool", "IPMI", "ipmi"]},
            {"id": "smartctl", "label": "Disks (SMART / smartctl)", "tas": ["smartctl"]},
            {"id": "storcli", "label": "LSI MegaRAID (storcli)", "tas": ["storcli"]},
            {"id": "megacli", "label": "LSI MegaRAID (megacli)", "tas": ["megacli", "MegaCli"]},
            {"id": "perccli", "label": "Dell PERC (perccli)", "tas": ["perccli"]},
            {"id": "ssacli", "label": "HPE Smart Array (ssacli)", "tas": ["ssacli", "hpssacli"]},
            {"id": "edac", "label": "Memory / EDAC (edac-util)", "tas": ["edac-util", "edac"]},
            {"id": "dmidecode", "label": "System info (dmidecode)", "tas": ["dmidecode"]},
        ],
    },

    # ── Data Center Physical ───────────────────────────────────────────────
    {"id": "apc", "label": "APC / Schneider Electric", "tas": ["APC", "PowerNet-MIB", "InRow", "AirIR"]},
    {"id": "cctv", "label": "CCTV / IP Cameras", "tas": ["NVR", "ONVIF", "Hikvision", "CCTV"]},
]

# Splunk Apps with pre-built dashboards (companion apps for TAs).
# Matched by substring against the UC's App/TA field, same as equipment matching.
SPLUNK_APPS = [
    {"name": "Splunk App for Unix and Linux", "id": 273,
     "url": "https://splunkbase.splunk.com/app/273",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/64464cc4-75ba-11ea-9476-06676674ba60.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/7d145c32-75ba-11ea-b2cd-06676674ba60.png"],
     "tas": ["Splunk_TA_nix"], "archived": True,
     "successor": {"name": "IT Essentials Work", "id": 5403, "url": "https://splunkbase.splunk.com/app/5403"},
     "desc": "Pre-built dashboards for Unix/Linux performance, capacity and alerting"},
    {"name": "Splunk App for Windows Infrastructure", "id": 1680,
     "url": "https://splunkbase.splunk.com/app/1680",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/9d9652a4-7499-11e3-b0c8-005056ad5c72.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/b9eee34e-c197-11e3-85b1-06550dde6d3e.png"],
     "tas": ["Splunk_TA_windows"], "archived": True,
     "successor": {"name": "IT Essentials Work", "id": 5403, "url": "https://splunkbase.splunk.com/app/5403"},
     "desc": "Pre-built dashboards for Windows server and desktop management, Active Directory"},
    {"name": "Microsoft Azure App for Splunk", "id": 4882,
     "url": "https://splunkbase.splunk.com/app/4882",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/d55080b0-6d4d-11ec-baf2-ce06eb58cb63.jpeg", "https://cdn.splunkbase.splunk.com/media/public/screenshots/d7147ff0-6d4d-11ec-9e53-3e3d9b7eaa58.jpeg"],
     "tas": ["Splunk_TA_microsoft-cloudservices", "Azure Monitor", "Azure Activity"],
     "desc": "Dashboards for Azure VMs, Metrics, Storage, Security Monitoring, Billing"},
    {"name": "Microsoft 365 App for Splunk", "id": 3786,
     "url": "https://splunkbase.splunk.com/app/3786",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/47862910-b938-11ec-bed4-4a49cc3b8a38.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/4aa6a7a0-b938-11ec-a542-32c4f9dd13a0.jpeg"],
     "tas": ["Splunk_TA_MS_O365", "MS_O365", "Office 365"],
     "desc": "Dashboards for Azure AD, Defender 365, Exchange, SharePoint, Teams, Power BI"},
    {"name": "App for Cisco Network Data", "id": 1352,
     "url": "https://splunkbase.splunk.com/app/1352",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/47590b50-3981-11ed-807b-8e625ade07cf.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/4dc530fe-3981-11ed-b76f-8ad1f2b29da5.png"],
     "tas": ["TA-cisco_ios", "cisco-ios", "cisco:ios"],
     "desc": "Dashboards and data models for Cisco Switches, Routers, WLAN Controllers"},
    {"name": "Cisco Security Cloud", "id": 7404,
     "url": "https://splunkbase.splunk.com/app/7404",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/37673b17-99fd-4dc1-a5f6-81b9cd15cab7.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/c8eb0ce4-f7bd-412d-950c-63c8c20da0a7.png"],
     "tas": ["cisco-firepower", "cisco-asa", "cisco-ise", "Cisco Secure Firewall", "Cisco Secure Endpoint"],
     "desc": "Modular dashboards and health checks for Cisco Secure Firewall, Duo, Endpoint"},
    {"name": "Cisco ThousandEyes App for Splunk", "id": 7719,
     "url": "https://splunkbase.splunk.com/app/7719",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/1e95cd84-404f-438c-8446-0426643c49a2.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/8e5ba70f-d63f-48af-9d03-cb837f61db45.png"],
     "tas": ["ThousandEyes", "Cisco ThousandEyes"],
     "desc": "Pre-built dashboards for ThousandEyes agent tests, events, and activity logs"},
    {"name": "Fortinet FortiGate App for Splunk", "id": 2800,
     "url": "https://splunkbase.splunk.com/app/2800",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/aa2b4e52-3252-11e5-84c5-02e61222c923.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/480c26fe-3254-11e5-a6ef-063854888a19.png"],
     "tas": ["Fortinet", "FortiGate", "Splunk_TA_fortinet", "TA-fortinet_fortigate"],
     "desc": "Threat visualizations and analytics for FortiGate firewall and UTM data"},
    {"name": "Palo Alto Networks App for Splunk", "id": 491,
     "url": "https://splunkbase.splunk.com/app/491",
     "screenshots": [],
     "tas": ["Splunk_TA_paloalto", "Palo Alto"], "archived": True,
     "successor": {"name": "Splunk App for Palo Alto Networks", "id": 7505, "url": "https://splunkbase.splunk.com/app/7505"},
     "desc": "Dashboards for Palo Alto firewall traffic, threat, and GlobalProtect data"},
    {"name": "Veeam App for Splunk", "id": 7312,
     "url": "https://splunkbase.splunk.com/app/7312",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/033805d0-fe3c-11ee-a32e-be99bb517a22.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/0a08b346-fe3c-11ee-9b85-7afc4dbed252.png"],
     "tas": ["Veeam", "veeam"],
     "desc": "Monitoring and security dashboards for Veeam Backup job statuses and events"},
    {"name": "Zscaler Splunk App", "id": 3866,
     "url": "https://splunkbase.splunk.com/app/3866",
     "screenshots": [],
     "tas": ["Zscaler", "zscaler"],
     "desc": "Dashboards for Zscaler web usage, threat intelligence, DLP, and remote access"},
    {"name": "Splunk App for Jenkins", "id": 3332,
     "url": "https://splunkbase.splunk.com/app/3332",
     "screenshots": [],
     "tas": ["Jenkins", "jenkins"],
     "desc": "Dashboards for Jenkins job and build status, console logs, test results"},
    {"name": "Splunk Add-on for F5 BIG-IP", "id": 2680,
     "url": "https://splunkbase.splunk.com/app/2680",
     "screenshots": [],
     "tas": ["Splunk_TA_f5-bigip", "F5", "BIG-IP"],
     "desc": "Collects network traffic, system logs and performance metrics from F5 BIG-IP"},
    {"name": "Splunk Add-on for ServiceNow", "id": 1928,
     "url": "https://splunkbase.splunk.com/app/1928",
     "screenshots": [],
     "tas": ["Splunk_TA_snow", "ServiceNow"],
     "desc": "Collects ServiceNow incidents, events, change and CMDB data via REST APIs"},
]

# Known Splunkbase Technology Add-ons (TAs) — matched against uc["t"] to add direct links.
# Only entries whose Splunkbase URLs have been verified (HTTP 200) are included.
SPLUNK_TAS = [
    {"name": "Splunk Add-on for Unix and Linux", "id": 833,
     "tas": ["Splunk_TA_nix"]},
    {"name": "Splunk Add-on for Microsoft Windows", "id": 742,
     "tas": ["Splunk_TA_windows"]},
    {"name": "Splunk Add-on for AWS", "id": 1876,
     "tas": ["Splunk_TA_aws"]},
    {"name": "Splunk Add-on for Microsoft Cloud Services", "id": 3110,
     "tas": ["Splunk_TA_microsoft-cloudservices"]},
    {"name": "Splunk Add-on for Microsoft Office 365", "id": 4055,
     "tas": ["Splunk_TA_MS_O365", "MS_O365"]},
    {"name": "Splunk Add-on for Google Cloud Platform", "id": 3088,
     "tas": ["Splunk_TA_google-cloudplatform"]},
    {"name": "Splunk Add-on for Google Workspace", "id": 5556,
     "tas": ["Splunk_TA_GoogleWorkspace"]},
    {"name": "Splunk Add-on for VMware", "id": 3258,
     "tas": ["Splunk_TA_vmware", "TA-vmware"]},
    {"name": "Palo Alto Networks Add-on for Splunk", "id": 2757,
     "tas": ["Splunk_TA_paloalto"]},
    {"name": "Splunk Add-on for Fortinet FortiGate", "id": 2846,
     "tas": ["Splunk_TA_fortinet", "TA-fortinet_fortigate"]},
    {"name": "Splunk Add-on for Checkpoint", "id": 3435,
     "tas": ["Splunk_TA_checkpoint"]},
    {"name": "Splunk Add-on for ServiceNow", "id": 1767,
     "tas": ["Splunk_TA_snow"]},
    {"name": "Zscaler Add-on for Splunk", "id": 3865,
     "tas": ["Splunk_TA_zscaler", "Zscaler"]},
    {"name": "Cisco Meraki Add-on for Splunk", "id": 5580,
     "tas": ["Cisco Meraki", "Splunkbase 5580"]},
    {"name": "Splunk Add-on for Cisco ASA", "id": 1621,
     "tas": ["cisco-asa", "Cisco ASA"]},
    {"name": "Splunk Add-on for Cisco ISE", "id": 1843,
     "tas": ["Splunk_TA_cisco-ise", "cisco-ise"]},
    {"name": "Splunk Add-on for Cisco IOS", "id": 1467,
     "tas": ["TA-cisco_ios"]},
    {"name": "Okta Identity Cloud Add-on for Splunk", "id": 4412,
     "tas": ["Splunk_TA_okta"]},
    {"name": "Splunk Add-on for Nessus", "id": 2804,
     "tas": ["Splunk_TA_nessus"]},
    {"name": "OT Security Add-on for Splunk", "id": 5151,
     "tas": ["OT Security Add-on", "Splunkbase 5151"]},
    {"name": "TA for Zeek", "id": 5466,
     "tas": ["Splunkbase 5466", "TA for Zeek"]},
    {"name": "CrowdStrike Falcon Event Streams TA", "id": 5082,
     "tas": ["TA-crowdstrike-falcon"]},
    {"name": "Splunk Add-on for Carbon Black", "id": 4679,
     "tas": ["Splunk_TA_vmware_carbonblack"]},
    {"name": "TA for Tanium", "id": 6076,
     "tas": ["Splunk_TA_tanium"]},
]

# Link to the common implementation guide (apps, inputs.conf, Splunk directory)
IMPLEMENTATION_GUIDE_LINK = "docs/implementation-guide.md"

REGULATION_LABELS = [
    "GDPR", "CCPA", "NIS2", "DORA", "PCI DSS", "HIPAA", "SOX",
    "NERC CIP", "ISO 27001", "NIST CSF", "NIST 800-53", "SOC 2",
    "MiFID II", "FedRAMP", "CMMC", "FISMA", "CJIS",
]

def assign_regulations(uc, cat_id, sub_id):
    """Auto-assign regulation tags based on title/subcategory heuristics.
    Tier 1: explicit title/subcategory matches (high confidence).
    Tier 2: keyword-based (moderate confidence).
    Tier 3: broad frameworks like ISO 27001, NIST CSF — manual only."""
    auto = set()
    title = uc.get("n", "").lower()
    cat_str = str(cat_id)
    sub_str = str(sub_id)

    # Tier 1: explicit matches in 10.12 and 14.2
    if sub_str.startswith("10.12"):
        if "pci" in title:
            auto.add("PCI DSS")
        if "hipaa" in title:
            auto.add("HIPAA")
        if "sox" in title:
            auto.add("SOX")
        if "fedramp" in title:
            auto.add("FedRAMP")
        if "cmmc" in title:
            auto.add("CMMC")
        if "nist" in title:
            auto.add("NIST 800-53")
        if "fisma" in title:
            auto.add("FISMA")
        if "cjis" in title:
            auto.add("CJIS")
    if sub_str.startswith("14.2") and "nerc cip" in title:
        auto.add("NERC CIP")
    if sub_str.startswith("10.14") and "nerc cip" in title:
        auto.add("NERC CIP")

    # 21.11 UCs get their regulation from subcategory context
    if sub_str.startswith("21.11"):
        if "gdpr" in title:
            auto.add("GDPR")
        if "nis2" in title:
            auto.add("NIS2")
        if "dora" in title and cat_str != "12":
            auto.add("DORA")
        if "ccpa" in title or "cpra" in title:
            auto.add("CCPA")
        if "mifid" in title:
            auto.add("MiFID II")
        if "iso 27001" in title or "isms" in title:
            auto.add("ISO 27001")
        if "nist csf" in title:
            auto.add("NIST CSF")
        if "soc 2" in title:
            auto.add("SOC 2")

    # Tier 2: keyword-based
    for kw in ("pii", "data masking", "data retention", "data subject",
               "personal data", "anonymization", "pseudonymization",
               "data protection"):
        if kw in title:
            auto.add("GDPR")
            auto.add("CCPA")
            break
    if "consent" in title and "consent admin" not in title:
        auto.add("GDPR")
    if "cardholder" in title or "payment card" in title:
        auto.add("PCI DSS")
    if "pci" in title and "PCI DSS" not in auto:
        auto.add("PCI DSS")
    if "ephi" in title or "protected health information" in title:
        auto.add("HIPAA")
    if "segregation of duties" in title:
        auto.add("SOX")
    if "nerc cip" in title or "bes cyber" in title:
        auto.add("NERC CIP")
    if "dora" in title and cat_str != "12":
        auto.add("DORA")

    return sorted(auto)


# Premium Splunk products that require separate licensing
PREMIUM_APPS = [
    {
        "label": "Splunk Enterprise Security",
        "ta_keywords": ["enterprise security", "escu", "es correlation"],
        "name_keywords": [],
    },
    {
        "label": "Splunk IT Service Intelligence (ITSI)",
        "ta_keywords": ["itsi", "it service intelligence"],
        "name_keywords": ["itsi"],
    },
    {
        "label": "Splunk SOAR",
        "ta_keywords": ["soar", "phantom"],
        "name_keywords": ["soar playbook", "soar forwarding"],
    },
    {
        "label": "Splunk User Behavior Analytics (UBA)",
        "ta_keywords": ["uba", "user behavior analytics"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Edge Hub",
        "ta_keywords": ["edge hub", "splunk edge hub"],
        "name_keywords": [],
    },
    {
        "label": "Splunk OT Intelligence",
        "ta_keywords": ["ot intelligence", "splunk oti"],
        "name_keywords": [],
    },
    {
        "label": "Splunk OT Security Add-on",
        "ta_keywords": ["ot security add-on"],
        "name_keywords": [],
    },
    {
        "label": "Splunk App for Fraud Analytics",
        "ta_keywords": ["fraud analytics"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Behavioral Profiling App",
        "ta_keywords": ["behavioral profiling"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Airport Ground Operations App",
        "ta_keywords": ["airport ground operations"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Intelligence Management",
        "ta_keywords": ["intelligence management", "trustar"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Attack Analyzer",
        "ta_keywords": ["attack analyzer"],
        "name_keywords": [],
    },
    {
        "label": "Splunk Asset and Risk Intelligence",
        "ta_keywords": ["asset and risk intelligence"],
        "name_keywords": [],
    },
]


def assign_premium(uc):
    """Auto-assign premium app labels based on TA field and UC name.
    Only checks TA and name fields (not implementation/SPL) to avoid tagging
    optional recommendations as requirements."""
    ta = (uc.get("t", "") or "").lower()
    name = (uc.get("n", "") or "").lower()

    matched = []
    for app in PREMIUM_APPS:
        for kw in app["ta_keywords"]:
            if kw in ta:
                matched.append(app["label"])
                break
        else:
            for kw in app["name_keywords"]:
                if kw in name:
                    matched.append(app["label"])
                    break

    if not matched:
        return ""
    return ", ".join(sorted(set(matched)))


# --- ESCU Detection Classification ------------------------------------------------
# Detection types from ESCU that represent the methodology
ESCU_METHODOLOGY_TYPES = {"ttp", "anomaly", "hunting", "baseline", "correlation"}

# Detection types from ESCU that represent entity/risk_object_type rather than methodology
ESCU_ENTITY_LABELS = {
    "system": "host or system", "user": "user account",
    "process_name": "process", "process": "process",
    "parent_process_name": "parent process", "parent_process": "parent process",
    "ip_address": "IP address", "file_name": "file", "file_path": "file path",
    "file_hash": "file hash", "url": "URL", "domain": "domain",
    "http_user_agent": "HTTP user agent", "signature": "detection signature",
    "email_subject": "email", "email_address": "email address",
    "service": "service", "registry_path": "registry key",
    "registry_value_text": "registry value", "registry_value_name": "registry value",
    "command": "command", "certificate_serial": "certificate",
    "other": "entity", "operational metrics": "operational metric",
}


def is_escu_detection(uc):
    """True if use case is an ESCU/SSE detection rule (has ESCU in App/TA and a detection type)."""
    ta = (uc.get("t") or "").lower()
    return ("escu" in ta or "security essentials" in ta) and bool((uc.get("dtype") or "").strip())


def _escu_is_rba(uc):
    """True if the ESCU detection uses Risk-Based Alerting."""
    spl = (uc.get("q") or "").lower()
    dtype_low = (uc.get("dtype") or "").strip().lower()
    if "risk.all_risk" in spl or "risk_object" in spl:
        return True
    if dtype_low in ESCU_ENTITY_LABELS:
        return True
    return False


def _escu_classify(uc):
    """Classify an ESCU detection into (methodology, entity_label, is_rba)."""
    dtype = (uc.get("dtype") or "TTP").strip()
    dtype_low = dtype.lower()
    is_rba = _escu_is_rba(uc)

    if dtype_low in ESCU_METHODOLOGY_TYPES:
        methodology = "TTP" if dtype_low == "ttp" else dtype_low.capitalize()
        entity_label = None
    elif dtype_low in ESCU_ENTITY_LABELS:
        methodology = "TTP"
        entity_label = ESCU_ENTITY_LABELS[dtype_low]
    else:
        methodology = "TTP"
        entity_label = None

    return methodology, entity_label, is_rba


def generate_escu_short_impl(uc):
    """Generate a concise, type-specific implementation summary for ESCU detections."""
    methodology, entity_label, is_rba = _escu_classify(uc)
    d = (uc.get("d") or "the required data sources").strip().rstrip(".")

    if methodology == "Hunting":
        return (
            "ESCU Hunting detection \u2014 not designed for automated alerting. "
            "Run ad-hoc or on a low-frequency schedule from Splunk Enterprise Security for analyst-driven investigation. "
            "Requires %s ingested and CIM-normalized." % d
        )
    if methodology == "Anomaly":
        return (
            "ESCU Anomaly detection \u2014 requires a baseline period (7\u201314 days minimum) before results are actionable. "
            "Enable in ES Content Management as a Correlation Search. "
            "Requires %s ingested and CIM-normalized." % d
        )
    if methodology == "Baseline":
        return (
            "ESCU Baseline detection \u2014 establishes normal behavior patterns used by companion Anomaly detections. "
            "Enable in ES Content Management; does not generate alerts independently. "
            "Requires %s ingested and CIM-normalized." % d
        )
    if is_rba:
        ec = " attributed to %s entities" % entity_label if entity_label else ""
        return (
            "ESCU Risk-Based Alerting detection. Enable in ES Content Management as a Correlation Search. "
            "Generates risk events%s \u2014 Notable Events fire when an entity\u2019s cumulative risk "
            "exceeds the configured threshold. Requires %s ingested and CIM-normalized." % (ec, d)
        )
    return (
        "ESCU %s detection. Enable in ES Content Management as a Correlation Search. "
        "Generates Notable Events directly when triggered. "
        "Requires %s ingested and CIM-normalized." % (methodology, d)
    )


def generate_escu_detailed_impl(uc):
    """Generate high-quality Enterprise Security implementation guidance for ESCU detections."""
    name = (uc.get("n") or "Detection").strip()
    data_sources = (uc.get("d") or "See Data Sources above").strip()
    spl = (uc.get("q") or "").strip()
    kfp = (uc.get("kfp") or "").strip()
    mitre = uc.get("mitre") or []
    cim_models = uc.get("a") or []
    sdomain = (uc.get("sdomain") or "").strip()

    methodology, entity_label, is_rba = _escu_classify(uc)

    lines = []

    # ---- Header ----
    lines.append("Enterprise Security Detection Rule")
    lines.append("")

    method_descs = {
        "TTP": "a TTP (Tactics, Techniques, and Procedures) detection that identifies known adversary behaviors with high fidelity",
        "Hunting": "a Hunting detection designed for analyst-driven threat hunting rather than automated alerting",
        "Anomaly": "an Anomaly detection that identifies statistical deviations from established baseline behavior",
        "Baseline": "a Baseline detection that establishes normal behavior patterns to support companion Anomaly detections",
        "Correlation": "a Correlation detection that aggregates and correlates signals from multiple detection sources",
    }
    method_desc = method_descs.get(methodology, "a %s detection" % methodology)

    intro = '"%s" is %s, sourced from the Splunk Enterprise Security Content Update (ESCU).' % (name, method_desc)

    if is_rba and methodology not in ("Hunting", "Baseline"):
        if entity_label:
            intro += (
                " It operates within the Risk-Based Alerting (RBA) framework, attributing risk to %s entities."
                " Rather than generating standalone alerts, each firing contributes a risk score to the identified"
                " entity \u2014 Notable Events are created only when cumulative risk exceeds the configured threshold,"
                " significantly reducing alert fatigue while preserving detection coverage." % entity_label
            )
        else:
            intro += (
                " It operates within the Risk-Based Alerting (RBA) framework."
                " Rather than generating standalone alerts, it contributes risk scores to identified entities \u2014"
                " Notable Events are created only when cumulative risk exceeds the threshold."
            )
    elif methodology == "Hunting":
        intro += (
            " Hunting detections are not intended for automated alerting."
            " They are run on-demand or on a low-frequency schedule by security analysts"
            " investigating specific threat hypotheses."
        )
    elif methodology == "Baseline":
        intro += (
            " Baseline detections do not generate alerts independently."
            " They establish behavioral norms used by companion Anomaly detections."
        )
    elif methodology == "Anomaly":
        intro += (
            " Anomaly detections require a baseline period to learn normal behavior before"
            " results become actionable. When triggered, deviations generate Notable Events"
            " for analyst investigation."
        )
    else:
        intro += " When triggered, it creates a Notable Event in the Incident Review dashboard for analyst triage."

    lines.append(intro)
    lines.append("")

    # ---- Prerequisites ----
    lines.append("Prerequisites")
    lines.append("")
    lines.append("\u2022 Splunk Enterprise Security 7.x or later with the ES Content Update (ESCU) app installed and up to date.")
    lines.append(
        "\u2022 Data sources: %s. Must be ingested into Splunk and normalized to the Common Information Model (CIM)"
        " via the appropriate Technology Add-on." % data_sources
    )

    real_cim = [m for m in cim_models if m.upper() != "N/A"] if cim_models else []
    if real_cim:
        lines.append(
            "\u2022 Data Model Acceleration: enable DMA for %s under Settings \u2192 Data Models."
            " Set the acceleration summary range to cover the detection\u2019s lookback window"
            " (typically 7 days minimum)." % ", ".join(real_cim)
        )

    if sdomain:
        domain_prereqs = {
            "endpoint": "Configure endpoint data collection (Sysmon, EDR agents, Windows Security Event Logs) and verify the Endpoint data model is populated and accelerated.",
            "network": "Ensure network traffic, DNS, and proxy logs are flowing and the Network Traffic and Network Resolution data models are populated.",
            "threat": "Configure threat intelligence feeds and verify the Threat Intelligence data model is populated for IOC matching.",
            "identity": "Ensure authentication and identity logs are ingested. Configure the Asset and Identity framework with your CMDB and HR data sources for entity enrichment.",
            "access": "Verify access control and authorization logs are ingested and the Authentication data model is accelerated.",
            "audit": "Ensure audit trail data is ingested with proper timestamp parsing and CIM field mappings.",
        }
        desc = domain_prereqs.get(sdomain.lower(),
                                  "Ensure data relevant to the %s security domain is ingested and CIM-normalized." % sdomain)
        lines.append("\u2022 Security domain (%s): %s" % (sdomain, desc))

    if mitre:
        lines.append(
            "\u2022 MITRE ATT&CK: %s. Review the ATT&CK matrix for adjacent techniques"
            " to identify detection coverage gaps in your environment." % ", ".join(mitre)
        )

    lines.append("")

    # ---- Deployment ----
    lines.append("Deployment")
    lines.append("")

    if methodology == "Hunting":
        lines.append("1. In Enterprise Security, navigate to Configure \u2192 Content \u2192 Content Management.")
        lines.append('2. Search for "%s" or filter by Analytic Story.' % name)
        lines.append(
            "3. Hunting detections are typically left disabled for automated scheduling."
            " Instead, run them on-demand from the Search bar or schedule at low frequency (daily or weekly)."
        )
        lines.append(
            "4. Review results manually \u2014 hunting detections cast a wider net and expect"
            " analyst judgment to separate signal from noise."
        )
        lines.append(
            "5. When results warrant further investigation, create a Notable Event manually"
            " or initiate your incident response workflow."
        )
    elif methodology == "Baseline":
        lines.append("1. In Enterprise Security, navigate to Configure \u2192 Content \u2192 Content Management.")
        lines.append('2. Search for "%s" or filter by Analytic Story.' % name)
        lines.append(
            "3. Enable the Baseline detection and allow it to run for at least 14 days"
            " to establish reliable behavioral norms."
        )
        lines.append(
            "4. Locate the companion Anomaly detection(s) in the same Analytic Story \u2014"
            " they depend on the baseline data this detection produces."
        )
        lines.append(
            "5. Baseline detections do not require alert actions."
            " Focus on ensuring consistent data ingestion during the baseline period."
        )
    elif is_rba:
        lines.append("1. In Enterprise Security, navigate to Configure \u2192 Content \u2192 Content Management.")
        lines.append('2. Search for "%s" or filter by Analytic Story to locate the detection.' % name)
        lines.append(
            "3. Review the detection\u2019s configuration: scheduling interval, risk score weight,"
            " and risk message template. The default risk score reflects the detection\u2019s relative"
            " severity \u2014 adjust based on your organization\u2019s risk tolerance."
        )
        lines.append(
            "4. Enable the detection. It will run as a scheduled Correlation Search and write risk events"
            " to the risk index when conditions are met."
        )
        lines.append(
            '5. Verify the Risk Notable aggregation rule is enabled (Content Management \u2192 search for "Risk Notable").'
            " This is the correlation search that fires when an entity\u2019s cumulative risk score"
            " crosses the configured threshold, creating the Notable Event that analysts investigate."
        )
        lines.append(
            "6. Optionally configure Adaptive Response Actions on this detection \u2014 for example,"
            " automatically enriching risk events with threat intelligence lookups, adding entities to a"
            " triage watchlist, or triggering a SOAR playbook for high-confidence detections."
        )
    else:
        lines.append("1. In Enterprise Security, navigate to Configure \u2192 Content \u2192 Content Management.")
        lines.append('2. Search for "%s" or filter by Analytic Story.' % name)
        lines.append(
            "3. Review the detection configuration \u2014 verify the scheduling interval and"
            " throttling settings match your operational tempo."
        )
        lines.append(
            "4. Enable the detection as a Correlation Search."
            " It will create Notable Events directly when triggered."
        )
        lines.append(
            "5. Set the Notable Event severity and urgency appropriate to your environment\u2019s risk posture."
        )
        lines.append(
            "6. Configure Adaptive Response Actions: email notifications, ServiceNow ticket creation,"
            " SOAR playbook triggers, or other response workflows."
        )

    lines.append("")

    # ---- Tuning ----
    lines.append("Tuning and False Positive Management")
    lines.append("")

    if kfp and kfp.strip() not in ("", "|"):
        lines.append("Known false positives for this detection: %s" % kfp)
        lines.append("")

    if is_rba and methodology not in ("Hunting", "Baseline"):
        lines.append(
            "\u2022 Adjust the risk score weight in Content Management."
            " Start with the ESCU default and increase for detections that consistently"
            " produce true positives in your environment; decrease for noisy detections."
        )
        lines.append(
            "\u2022 Use the Risk Analysis dashboard in ES to identify which detections contribute"
            " the most risk events and which entities are most frequently flagged \u2014"
            " this reveals both coverage strengths and tuning opportunities."
        )
        lines.append(
            "\u2022 Create lookup-based suppressions for known-good activity: approved administrative"
            " tools, vulnerability scanner IPs, scheduled batch processes, and maintenance windows."
        )
        lines.append(
            "\u2022 If the detection fires frequently on a specific entity that is consistently benign,"
            " consider adding a per-entity risk exception rather than disabling the detection entirely \u2014"
            " this preserves coverage for other entities."
        )
    elif methodology == "Anomaly":
        lines.append(
            "\u2022 Allow a minimum 7\u201314 day baseline period before treating results as actionable."
            " Anomaly detections need sufficient data to establish reliable behavioral norms."
        )
        lines.append(
            "\u2022 Review and adjust the statistical threshold (standard deviation multiplier or count threshold)"
            " based on your environment\u2019s natural variance. Start conservative and tighten over time."
        )
        lines.append(
            "\u2022 Exclude recurring legitimate patterns: automated processes, scheduled reports,"
            " batch jobs, and other predictable activity that creates expected outliers."
        )
        lines.append(
            "\u2022 Re-evaluate the baseline periodically \u2014 organizational changes"
            " (mergers, new applications, infrastructure migrations) can shift behavioral norms."
        )
    elif methodology == "Hunting":
        lines.append(
            "\u2022 Hunting detections are expected to produce broader result sets that require analyst"
            " interpretation. Focus on refining the search scope (time range, specific hosts or users)"
            " rather than eliminating all noise."
        )
        lines.append(
            "\u2022 Maintain a hunting journal documenting hypotheses tested, results found,"
            " and detection improvements identified."
        )
        lines.append(
            "\u2022 Share high-fidelity findings with the detection engineering team to convert"
            " recurring hunting patterns into automated TTP or Anomaly detections."
        )
    else:
        lines.append(
            "\u2022 Review the detection\u2019s filter criteria and adjust for known-good activity in your environment."
        )
        lines.append(
            "\u2022 Configure throttling in Content Management to prevent duplicate Notable Events"
            " for the same entity within a configurable window"
            " (typically 1\u201324 hours depending on detection frequency)."
        )
        lines.append(
            "\u2022 Use Notable Event Suppression for entities or patterns that are consistently benign"
            " after investigation."
        )

    lines.append("")

    # ---- Analyst Workflow ----
    if methodology != "Baseline":
        lines.append("Analyst Response Workflow")
        lines.append("")

        if is_rba and methodology != "Hunting":
            lines.append("When a Risk Notable fires for an entity associated with this detection:")
            lines.append("")
            lines.append(
                "1. Open the Notable Event in Incident Review. Examine the entity\u2019s risk"
                " timeline \u2014 this detection is one of potentially many contributing risk signals."
                " The composite risk score provides more context than any single detection alone."
            )
            lines.append(
                "2. Review the Risk Message and Analytic Story annotations to understand what"
                " adversary behavior was detected and its position in the MITRE ATT&CK kill chain."
            )

            domain_investigation = {
                "endpoint": (
                    "3. Pivot to the Asset Investigator to review the host\u2019s recent process executions,"
                    " file modifications, registry changes, and network connections."
                    " Cross-reference with EDR telemetry for process trees and parent-child relationships."
                ),
                "network": (
                    "3. Pivot to the Asset Investigator to review the device\u2019s network connections,"
                    " DNS queries, and traffic volume patterns."
                    " Check for beaconing behavior, unusual destination IPs, or data exfiltration indicators."
                ),
                "identity": (
                    "3. Pivot to the Identity Investigator to review the user\u2019s authentication history,"
                    " privilege usage, and access patterns across systems."
                    " Check for impossible travel, off-hours activity, or access outside the user\u2019s normal scope."
                ),
                "access": (
                    "3. Pivot to the Identity Investigator and the Access Anomalies dashboard to review"
                    " authorization patterns, privilege escalation, and resource access."
                    " Verify against the user\u2019s role and recent access requests."
                ),
            }
            lines.append(domain_investigation.get(
                sdomain.lower() if sdomain else "",
                "3. Pivot to the Asset Investigator or Identity Investigator to review the entity\u2019s"
                " full activity timeline and correlate with threat intelligence and other security events."
            ))

            lines.append(
                "4. Assess the full scope: check for related risk events from the same Analytic Story"
                " and from other entities that may indicate lateral movement or a coordinated attack."
            )
            lines.append(
                "5. Determine disposition: True Positive (initiate incident response),"
                " Benign True Positive (legitimate activity \u2014 document and consider tuning),"
                " or False Positive (add suppression and adjust detection)."
            )
            lines.append(
                "6. Update the Notable Event status, set the owner, and document findings"
                " in the investigation notes for audit trail and team visibility."
            )

        elif methodology == "Hunting":
            lines.append("When reviewing Hunting results:")
            lines.append("")
            lines.append(
                "1. Run the search manually or review scheduled results."
                " Evaluate each returned event against your threat hypothesis"
                " \u2014 not every result indicates compromise."
            )
            lines.append(
                "2. Cross-reference findings with current threat intelligence,"
                " recent security advisories, and outputs from other detection sources."
            )
            lines.append(
                "3. If suspicious activity is confirmed, create a Notable Event or"
                " escalate directly to your incident response process with the supporting evidence."
            )
            lines.append(
                "4. Document the hunting exercise: hypothesis, data sources queried,"
                " time range, findings, and any detection engineering improvements identified."
            )
        else:
            lines.append("When this detection generates a Notable Event:")
            lines.append("")
            lines.append(
                "1. Open the Notable Event in Incident Review."
                " Review the triggering event details, affected entities, and assigned severity."
            )
            lines.append(
                "2. Investigate the involved entities using the Asset Investigator"
                " and Identity Investigator dashboards for historical context and behavioral patterns."
            )
            lines.append(
                "3. Correlate with related Notable Events and threat intelligence"
                " to assess whether this is an isolated event or part of a broader campaign."
            )
            lines.append(
                "4. Take appropriate response actions: contain, remediate, and recover."
                " Leverage SOAR playbooks where available for consistent and rapid response."
            )
            lines.append(
                "5. Update the Notable Event status and document investigation findings"
                " for post-incident review and compliance."
            )

        lines.append("")

    # ---- SPL Context for Risk Investigation searches ----
    if spl and "risk.all_risk" in spl.lower():
        lines.append("About the SPL Query Shown Above")
        lines.append("")
        lines.append(
            "The SPL displayed for this use case is the Risk Investigation drilldown search \u2014"
            " it queries the Risk data model to show all risk events associated with a specific entity."
            " This is the search analysts use during investigation to understand what contributed"
            " to an entity\u2019s risk score."
        )
        lines.append("")
        lines.append(
            "The actual detection logic is packaged within the ESCU Correlation Search definition"
            " and runs automatically on schedule. To view or modify the detection\u2019s underlying"
            " search logic, navigate to Configure \u2192 Content \u2192 Content Management"
            " and click on the detection name."
        )
        lines.append("")

    # ---- Validation ----
    lines.append("Validation")
    lines.append("")
    lines.append("Confirm the required data sources are flowing:")
    lines.append("")
    lines.append("```spl")
    lines.append("| tstats count where index=* by index, sourcetype | sort -count")
    lines.append("```")
    lines.append("")
    lines.append("Verify the detection is enabled and firing:")
    lines.append("")
    lines.append("```spl")
    lines.append('index=_audit action="alert_fired" ss_name="*"')
    lines.append("| stats count by ss_name, trigger_time | sort -trigger_time")
    lines.append("```")

    return "\n".join(lines)


ESCU_GENERIC_IMPL_PREFIX = "deploy the detection from splunk security essentials"


def assign_pillar(uc, cat_id):
    """Auto-assign Splunk pillar (security/observability/both) based on UC fields and heuristics.
    If the UC already has a manually-set pillar field, respect it."""
    existing = uc.get("pillar", "")
    if existing:
        return existing

    is_security = False
    is_observability = False

    if uc.get("sdomain") or uc.get("mitre") or uc.get("dtype"):
        is_security = True

    if cat_id in PILLAR_SECURITY_CATS:
        is_security = True

    mtypes = uc.get("mtype", [])
    mtypes_lower = {m.lower() for m in mtypes}
    if "security" in mtypes_lower:
        is_security = True
    if mtypes_lower & PILLAR_OBS_MTYPES:
        is_observability = True

    title_lower = uc.get("n", "").lower()
    value_lower = uc.get("v", "").lower()
    text_to_check = title_lower + " " + value_lower
    for word in PILLAR_SECURITY_WORDS:
        if word in text_to_check:
            is_security = True
            break

    if not is_security and not is_observability:
        if cat_id in PILLAR_SECURITY_CATS:
            is_security = True
        else:
            is_observability = True

    if is_security and is_observability:
        return "both"
    if is_security:
        return "security"
    return "observability"


def apps_for_ta_string(ta_str):
    """Given a use case's App/TA field, return list of matching SPLUNK_APPS entries."""
    if not (ta_str or "").strip():
        return []
    raw = (ta_str or "").replace("`", "").strip().lower()
    if not raw:
        return []
    matched = []
    seen_ids = set()
    for app in SPLUNK_APPS:
        for pattern in app["tas"]:
            if pattern.lower() in raw and app["id"] not in seen_ids:
                seen_ids.add(app["id"])
                entry = {
                    "name": app["name"],
                    "id": app["id"],
                    "url": app["url"],
                    "desc": app.get("desc", ""),
                    "screenshots": app.get("screenshots", []),
                    "archived": app.get("archived", False),
                }
                if app.get("successor"):
                    entry["successor"] = app["successor"]
                matched.append(entry)
                break
    return matched


def ta_link_for_ta_string(ta_str):
    """Given a use case's App/TA field, return first matching SPLUNK_TAS entry as {name, id, url} or None."""
    if not (ta_str or "").strip():
        return None
    raw = (ta_str or "").replace("`", "").strip().lower()
    if not raw:
        return None
    for ta in SPLUNK_TAS:
        for pattern in ta["tas"]:
            if pattern.lower() in raw:
                return {
                    "name": ta["name"],
                    "id": ta["id"],
                    "url": f"https://splunkbase.splunk.com/app/{ta['id']}",
                }
    return None


def equipment_ids_for_ta_string(ta_str):
    """Given a use case's App/TA field (t), return (equipment_ids, model_compound_ids).
    model_compound_ids are "eqId_modelId" for equipment that has models and whose model tas matched."""
    if not (ta_str or "").strip():
        return [], []
    raw = (ta_str or "").replace("`", "").strip().lower()
    if not raw:
        return [], []
    seen = set()
    model_seen = set()
    for eq in EQUIPMENT:
        for pattern in eq["tas"]:
            if pattern.lower() in raw:
                seen.add(eq["id"])
                break
        models = eq.get("models") or []
        for mod in models:
            for pattern in mod["tas"]:
                if pattern.lower() in raw:
                    model_seen.add(eq["id"] + "_" + mod["id"])
                    break
    return sorted(seen), sorted(model_seen)


def _split_spl_stages(spl):
    """Split SPL on | at top level (not inside quotes, backticks, or bracketed subsearches)."""
    if not (spl or "").strip():
        return []
    spl = spl.strip()
    parts = []
    buf = []
    in_dq = in_sq = False
    in_bt = False
    bracket = 0
    i = 0
    while i < len(spl):
        c = spl[i]
        if in_bt:
            buf.append(c)
            if c == "`":
                in_bt = False
            i += 1
            continue
        if c == "`" and not in_dq and not in_sq:
            in_bt = True
            buf.append(c)
            i += 1
            continue
        if c == '"' and (i == 0 or spl[i - 1] != "\\"):
            in_dq = not in_dq
        elif c == "'" and not in_dq:
            in_sq = not in_sq
        elif not in_dq and not in_sq:
            if c == "[":
                bracket += 1
            elif c == "]":
                bracket = max(0, bracket - 1)
            elif c == "|" and bracket == 0:
                seg = "".join(buf).strip()
                if seg:
                    parts.append(seg)
                buf = []
                i += 1
                continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _truncate_words(s, max_len=420):
    """Trim string to max_len at word boundary."""
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    cut = s[: max_len - 1].rsplit(" ", 1)[0]
    return cut + "…"


def _spl_explain_context(uc):
    """Build a dict of use-case fields for tailored SPL explanations."""
    if not uc:
        return None
    return {
        "title": (uc.get("n") or "").strip(),
        "value": (uc.get("v") or "").strip(),
        "data_sources": (uc.get("d") or "").strip(),
        "app_ta": (uc.get("t") or "").strip(),
        "dtype": (uc.get("dtype") or "").strip(),
        "mtype": uc.get("mtype") or [],
    }


def _extract_base_search_terms(stage):
    """Pull index/sourcetype/host from a base-search stage for cross-checking with Data Sources."""
    st = (stage or "").strip()
    out = {"indexes": [], "sourcetypes": [], "hosts": []}
    if not st:
        return out
    seen_i, seen_s, seen_h = set(), set(), set()
    for m in re.finditer(r"index\s*=\s*([^\s\)]+)", st, re.I):
        val = m.group(1).strip("`,\"'")
        if val and val not in seen_i:
            seen_i.add(val)
            out["indexes"].append(val)
    for m in re.finditer(r'sourcetype\s*=\s*("(?:\\.|[^"])*"|[^\s\)]+)', st, re.I):
        val = m.group(1).strip('"')
        if val and val not in seen_s:
            seen_s.add(val)
            out["sourcetypes"].append(val)
    for m in re.finditer(r"host\s*=\s*([^\s\)]+)", st, re.I):
        val = m.group(1).strip("`,\"'")
        if val and val not in seen_h:
            seen_h.add(val)
            out["hosts"].append(val)
    return out


def _data_sources_mention_sourcetype(data_sources, sourcetype):
    """True if documented data sources text references this sourcetype (substring match)."""
    if not (data_sources and sourcetype):
        return False
    ds_low = data_sources.lower()
    st_low = sourcetype.lower()
    if st_low in ds_low:
        return True
    # backtick-wrapped in markdown often becomes plain in d
    bare = re.sub(r"^[^\w]+|[^\w]+$", "", sourcetype)
    return bare.lower() in ds_low


def _spl_explain_intro(spl, ctx, cim_variant=False):
    """2–4 short paragraphs tying the search to this use case and documented sources."""
    if not ctx:
        return ""
    lines = []
    title = ctx["title"]
    value = _truncate_words(ctx["value"], 480)
    ds = ctx["data_sources"]
    ta = ctx["app_ta"]
    if title and value:
        lines.append("**%s** — %s" % (title, value))
    elif title:
        lines.append("**%s**" % title)
    elif value:
        lines.append(_truncate_words(value, 480))
    env = []
    if ds:
        env.append("Documented **Data sources**: %s." % ds.rstrip("."))
    if ta:
        env.append("**App/TA** (typical add-on context): %s." % ta.rstrip("."))
    if env:
        lines.append(
            " ".join(env)
            + " The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs."
        )
    if cim_variant:
        lines.append(
            "This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. "
            "Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing."
        )
    stages = _split_spl_stages(spl)
    if stages:
        terms = _extract_base_search_terms(stages[0])
        bits = []
        if terms["indexes"]:
            bits.append("**index**: " + ", ".join(terms["indexes"][:4]))
        if terms["sourcetypes"]:
            bits.append("**sourcetype**: " + ", ".join(terms["sourcetypes"][:4]))
        hosts_f = [h for h in terms["hosts"][:4] if h not in ("*", '"*"', "'*'")]
        if hosts_f:
            bits.append("**host** filter: " + ", ".join(hosts_f))
        if bits:
            cross = "The first pipeline stage scopes events using " + "; ".join(bits) + "."
            if ds and terms["sourcetypes"]:
                matched = [s for s in terms["sourcetypes"] if _data_sources_mention_sourcetype(ds, s)]
                if matched:
                    cross += (
                        " That sourcetype matches what this use case lists under Data sources."
                        if len(matched) == 1
                        else " Those sourcetypes align with what this use case lists under Data sources."
                    )
                else:
                    cross += (
                        " If that sourcetype is not mentioned in Data sources, double-check parsing or "
                        "update the documentation to match the feed you actually ingest."
                    )
            lines.append(cross)
    if ctx.get("dtype"):
        lines.append(
            "**Detection type** for this use case: %s — interpret thresholds and fields in that context."
            % ctx["dtype"]
        )
    return "\n\n".join(lines)


def _extract_by_clause(st):
    """Return text after 'by' for stats/timechart/chart/top (truncated)."""
    bm = re.search(r"\bby\s+([^|]+)", st, re.I)
    if not bm:
        return ""
    return " ".join(bm.group(1).split())[:160]


def _extract_span_clause(st):
    m = re.search(r"\bspan\s*=\s*([^\s|]+)", st, re.I)
    return m.group(1).strip() if m else ""


def _explain_one_spl_stage(stage, stage_index=0, ctx=None):
    """Return one bullet line (without leading •) describing a pipeline stage, or None to skip."""
    st = (stage or "").strip()
    if not st:
        return None
    if st.startswith("|"):
        st = st[1:].strip()
    low = st.lower()
    # Splunk macro
    if st.startswith("`") and "`" in st[1:]:
        end = st.find("`", 1)
        name = st[1:end] if end > 1 else st.strip("`")
        return (
            "Invokes macro `%s` — in Search, use the UI or expand to inspect the underlying SPL."
            % name
        )
    if low.startswith("tstats") or re.search(r"\bfrom\s+datamodel\s*=", low):
        dm = re.search(r"datamodel\s*=\s*([^\s|]+)", st, re.I)
        if dm:
            return (
                "Uses `tstats` against accelerated summaries for data model `%s` — enable acceleration for that model."
                % dm.group(1).rstrip(")")
            )
        return "Uses `tstats` against precomputed summaries; ensure the referenced data model is accelerated."
    if low.startswith("mstats"):
        return "Uses `mstats` to query metrics indexes (pre-aggregated metric data)."
    if low.startswith("metadata") or low.startswith("metasearch"):
        return "Uses `metadata`/`metasearch` to inspect indexes, sources, hosts, or sourcetypes (not raw events)."
    if re.match(r"^\|?\s*inputlookup\b", low):
        return "Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting."
    if low.startswith("loadjob"):
        return "Loads a prior job's results with `loadjob`."
    if re.match(r"^\|?\s*rest\b", low):
        return "Calls Splunk `rest` to read configuration or REST-exposed entities."
    if low.startswith("search"):
        return "Applies an explicit `search` filter to narrow the current result set."
    if low.startswith("stats") or low.startswith("eventstats") or low.startswith("streamstats"):
        cmd = "stats"
        if low.startswith("eventstats"):
            cmd = "eventstats"
        elif low.startswith("streamstats"):
            cmd = "streamstats"
        by_c = _extract_by_clause(st)
        if by_c:
            return (
                "`%s` rolls up events into metrics; results are split **by %s** so each row reflects one combination "
                "of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case)."
                % (cmd, by_c)
            )
        return (
            "`%s` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows."
            % cmd
        )
    if low.startswith("timechart"):
        span_s = _extract_span_clause(st)
        by_c = _extract_by_clause(st)
        parts = ["`timechart` plots the metric over time"]
        if span_s:
            parts.append("using **span=%s** buckets" % span_s)
        if by_c:
            parts.append("with a separate series **by %s**" % by_c)
        parts.append("— ideal for trending and alerting on this use case.")
        return " ".join(parts)
    if low.startswith("chart") and not low.startswith("timechart"):
        by_c = _extract_by_clause(st)
        if by_c:
            return "`chart` builds a categorical visualization, grouping **by %s**." % by_c
        return "Builds a non-time chart with `chart` (categories or split-by fields)."
    if low.startswith("top"):
        by_c = _extract_by_clause(st)
        if by_c:
            return "`top` lists the most common values, **by %s**, for quick hotspot analysis." % by_c
        return "`top` shows the most frequent field values (limit with an explicit `limit=` if needed)."
    if low.startswith("rare"):
        by_c = _extract_by_clause(st)
        if by_c:
            return "`rare` surfaces the least common values, **by %s** — helpful for outliers tied to this scenario." % by_c
        return "Shows the least frequent field values with `rare`."
    if low.startswith("eval"):
        ev = re.search(r"eval\s+([^=]+)=", st, re.I)
        if ev:
            fld = ev.group(1).strip().split()[0]
            return "`eval` defines or adjusts **%s** — often to normalize units, derive a ratio, or prepare for thresholds." % fld
        return "Computes or normalizes fields using `eval` (ratios, coalesce, string prep)."
    if low.startswith("where"):
        wm = re.search(r"^\s*where\s+(.+)$", st, re.I | re.S)
        cond = wm.group(1).strip() if wm else ""
        if len(cond) > 120:
            cond = cond[:117] + "…"
        if cond:
            return (
                "Filters the current rows with `where %s` — typically the threshold or rule expression for this monitoring goal."
                % cond
            )
        return "Filters rows with `where` (conditions on aggregated or computed fields)."
    if low.startswith("fields"):
        return "Keeps or drops fields with `fields` to shape columns and size."
    if low.startswith("rename"):
        return "Renames fields with `rename` for clarity or joins."
    if low.startswith("sort"):
        return "Orders rows with `sort` — combine with `head`/`tail` for top-N patterns."
    if low.startswith("head"):
        return "Limits the number of rows with `head`."
    if low.startswith("tail"):
        return "Takes the last N rows with `tail`."
    if low.startswith("dedup"):
        return "Removes duplicate values with `dedup` — pair with `sort` when order matters."
    if low.startswith("join"):
        return "Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation."
    if low.startswith("appendcols"):
        return "Adds columns from a subsearch with `appendcols`."
    if low.startswith("append"):
        return "Appends rows from a subsearch with `append`."
    if low.startswith("union"):
        return "Combines multiple searches with `union`."
    if low.startswith("lookup"):
        return "Enriches events using `lookup` (lookup definition + optional OUTPUT fields)."
    if low.startswith("outputlookup"):
        return "Writes results to a lookup with `outputlookup` (permissions and retention apply)."
    if low.startswith("rex"):
        return "Extracts fields with `rex` (regular expression)."
    if low.startswith("regex"):
        return "Filters rows matching a pattern with `regex`."
    if low.startswith("transaction"):
        return "Groups related events into transactions — prefer `maxspan`/`maxpause`/`maxevents` for bounded memory."
    if low.startswith("bin") or low.startswith("bucket"):
        return "Discretizes time or numeric ranges with `bin`/`bucket`."
    if low.startswith("mvexpand"):
        return "Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion."
    if low.startswith("spath"):
        return "Extracts structured paths (JSON/XML) with `spath`."
    if low.startswith("makeresults"):
        return "Generates synthetic events with `makeresults` (tests or scaffolding)."
    if low.startswith("return"):
        return "Returns subsearch results to an outer search with `return`."
    if low.startswith("format"):
        return "Formats subsearch output for `map`/`join` with `format`."
    if low.startswith("map"):
        return "Runs a templated search per row with `map`."
    if low.startswith("foreach"):
        return "Iterates over multivalue fields with `foreach`."
    if low.startswith("xyseries"):
        return "Pivots fields for charting with `xyseries`."
    if low.startswith("fillnull"):
        return "Fills null values with `fillnull`."
    if low.startswith("filldown"):
        return "Propagates values downward with `filldown`."
    if low.startswith("from ") or low.startswith("| from "):
        return "Uses `from` (dataset / Federated Search) — verify dataset availability and permissions."
    # Base / indexed search
    if (
        "index=" in low
        or "sourcetype=" in low
        or "eventtype=" in low
        or re.search(r"\btag\s*=", low)
        or "source=" in low
        or re.search(r"\bhost\s*=", low)
        or "earliest=" in low
        or "latest=" in low
    ):
        bits = []
        for m in re.finditer(r"index\s*=\s*([^\s\)]+)", st, re.I):
            bits.append("index=%s" % m.group(1).strip(","))
        sm = re.search(r"sourcetype\s*=\s*(\"[^\"]+\"|[^\s\)]+)", st, re.I)
        if sm:
            bits.append("sourcetype=%s" % sm.group(1).strip(","))
        if "earliest=" in low or "latest=" in low:
            bits.append("time bounds")
        if re.search(r"\btag\s*=", low):
            bits.append("tags")
        if bits:
            line = "Scopes the data: " + ", ".join(bits[:4]) + ("…" if len(bits) > 4 else "") + "."
            if ctx and ctx.get("data_sources"):
                line += " Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion."
            elif ctx:
                line += " Adjust names if your deployment uses different index or sourcetype conventions."
            return line
        return "Filters the initial event set (index, sourcetype, host, time, tags, etc.)."
    if st.startswith("["):
        return "Uses a bracketed subsearch `[ ... ]` whose results constrain or feed the outer search."
    # Fallback: short preview
    one = " ".join(st.split())
    if len(one) > 140:
        one = one[:137] + "…"
    hint = ""
    if ctx and ctx.get("title"):
        hint = " (see **%s**)" % ctx["title"]
    return "Pipeline stage%s: %s" % (hint, one)


def explain_spl_pipeline(spl, max_bullets=24, uc=None, cim_variant=False):
    """Plain-language walkthrough: use-case context plus per-stage notes (heuristic)."""
    if not (spl or "").strip():
        return ""
    ctx = _spl_explain_context(uc) if uc else None
    stages = _split_spl_stages(spl)
    if not stages:
        return ""
    bullets = []
    cap = max(4, min(max_bullets, 40))
    for si, stage in enumerate(stages):
        if len(bullets) >= cap - 1:
            bullets.append(
                "Additional pipeline stages follow — tune fields, macros, and thresholds for **%s** and your environment."
                % (ctx.get("title") or "this use case")
                if ctx
                else "Additional pipeline stages follow — adjust indexes, fields, macros, and thresholds for your environment."
            )
            break
        line = _explain_one_spl_stage(stage, stage_index=si, ctx=ctx)
        if line:
            bullets.append(line)
    if not bullets:
        return ""
    title_heading = "Understanding this CIM / accelerated SPL" if cim_variant else "Understanding this SPL"
    out = [title_heading, ""]
    intro = _spl_explain_intro(spl, ctx, cim_variant=cim_variant) if ctx else ""
    if intro:
        out.append(intro)
        out.append("")
    out.append("**Pipeline walkthrough**")
    out.append("")
    for b in bullets:
        out.append("• " + b)
    return "\n".join(out)


def generate_detailed_impl(uc):
    """Generate a thorough step-by-step implementation guide from UC fields (used when no explicit Detailed implementation is in markdown)."""
    t = (uc.get("t") or "").strip()
    d = (uc.get("d") or "").strip()
    m = (uc.get("m") or "").strip()
    z = (uc.get("z") or "").strip()
    q = (uc.get("q") or "").strip()
    qs = (uc.get("qs") or "").strip()
    script = (uc.get("script") or "").strip()
    # First 2–3 sentences of implementation for Step 1 (cap length)
    m_lead = m[:500] + ("…" if len(m) > 500 else "") if m else "Configure inputs and permissions as needed for your environment."
    lines = [
        "Prerequisites",
        "• Install and configure the required add-on or app: " + (t or "see App/TA above") + ".",
        "• Ensure the following data sources are available: " + (d or "see Data Sources above") + ".",
        "• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: " + IMPLEMENTATION_GUIDE_LINK,
        "",
        "Step 1 — Configure data collection",
        m_lead,
        "",
        "Step 2 — Create the search and alert",
    ]
    if q:
        lines.append("Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):")
        lines.append("")
        lines.append("```spl")
        lines.append(q)
        lines.append("```")
        lines.append("")
        expl = explain_spl_pipeline(q, uc=uc)
        if expl:
            lines.append(expl)
            lines.append("")
        if qs:
            lines.append("Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):")
            lines.append("")
            lines.append("```spl")
            lines.append(qs)
            lines.append("```")
            lines.append("")
            expl_cim = explain_spl_pipeline(qs, max_bullets=18, uc=uc, cim_variant=True)
            if expl_cim:
                lines.append(expl_cim)
                lines.append("")
        needs_dma = (
            "tstats" in q.lower()
            or "mstats" in q.lower()
            or (qs and ("tstats" in qs.lower() or "mstats" in qs.lower()))
        )
        if needs_dma:
            lines.append(
                "Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries."
            )
            lines.append("")
    else:
        lines.append("Run the SPL query from the SPL Query section above in Search. Save as a report or alert. Adjust the time range and threshold as needed. If the use case includes a tstats/CIM query, enable Data Model Acceleration for the relevant data model.")
    lines.extend([
        "",
        "Step 3 — Validate",
        "Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.",
        "",
        "Step 4 — Operationalize",
        "Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. " + (("Consider visualizations: " + z) if z else "Use the Visualization section above for suggested panels."),
    ])
    # Scripted input: use explicit script if present; else add generic example when use case mentions scripted input
    d_m_lower = (d + " " + m).lower()
    if script:
        lines.extend([
            "",
            "Scripted input example",
            "Use the script below in a scripted input (see Implementation guide for inputs.conf). Ensure the script is executable and the path in inputs.conf matches your app location:",
            "",
            "```bash",
            script,
            "```",
        ])
    elif "scripted" in d_m_lower:
        lines.extend([
            "",
            "Scripted input (generic example)",
            "This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:",
            "",
            "```ini",
            "[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]",
            "interval = 300",
            "sourcetype = your_sourcetype",
            "index = main",
            "disabled = 0",
            "```",
            "",
            "The script should print one event per line (e.g. key=value). Example minimal script (bash):",
            "",
            "```bash",
            "#!/usr/bin/env bash",
            "# Output metrics or events, one per line",
            "echo \"metric=value timestamp=$(date +%s)\"",
            "```",
            "",
            "For full details (paths, scheduling, permissions), see the Implementation guide: " + IMPLEMENTATION_GUIDE_LINK,
        ])
    return "\n".join(lines)


def parse_category_file(filepath):
    """Parse a single cat-*.md file into a category dict."""
    basename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    category = {"s": []}
    current_sub = None
    current_uc = None

    # Code block state: tracks which field we're collecting for
    in_code_block = False
    code_target = None  # "q" for main SPL, "qs" for CIM SPL
    code_lines = []

    # Tracks the last field seen (for associating code blocks)
    last_field = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Code block handling ──
        if in_code_block:
            if stripped.startswith("```"):
                # End of code block — store collected lines
                if current_uc is not None and code_target:
                    current_uc[code_target] = "\n".join(code_lines)
                in_code_block = False
                code_target = None
                code_lines = []
            else:
                code_lines.append(line)
            i += 1
            continue

        # ── Category heading: # 1. Server & Compute  OR  ## 6. Storage ──
        m = re.match(r"^#{1,2}\s+(\d+)\.\s+(.+)$", stripped)
        if m:
            category["i"] = int(m.group(1))
            category["n"] = m.group(2).strip()
            category["src"] = basename  # e.g. cat-10-security-infrastructure.md — for GitHub source links
            i += 1
            continue

        # ── Subcategory heading: ## 1.1 Linux  OR  ### 6.1 SAN ──
        m = re.match(r"^#{2,3}\s+(\d+\.\d+)\s+(.+)$", stripped)
        if m:
            current_sub = {
                "i": m.group(1),
                "n": m.group(2).strip(),
                "u": [],
            }
            category["s"].append(current_sub)
            current_uc = None
            last_field = None
            i += 1
            continue

        # ── Use case heading: ### UC-1.1.1 · Title  OR  #### UC-6.1.1 · Title ──
        m = re.match(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+)$", stripped)
        if m:
            current_uc = {
                "i": m.group(1),
                "n": m.group(2).strip(),
                "c": "",
                "f": "",
                "v": "",
                "t": "",
                "d": "",
                "q": "",
                "m": "",
                "z": "",
                "kfp": "",   # known false positives (SSE)
                "refs": "",  # references (URLs, comma-separated)
                "mitre": [], # MITRE ATT&CK IDs
                "dtype": "", # detection type: TTP, Anomaly, Baseline, Hunting, Correlation
                "sdomain": "", # security domain: endpoint, network, threat, identity, etc.
                "reqf": "",   # required fields for the search
                "md": "",    # detailed implementation (expandable); parsed or generated
                "script": "",  # optional script example (scripted input)
                "premium": "",  # Premium Apps (ES, ITSI, SOAR, etc.) when required
                "hw": "",       # Equipment Models — specific hardware models (searchable)
                "dma": "",    # data model acceleration note (e.g. "Enable for Performance, Network_Traffic")
                "schema": "", # schema context: CIM, OCSF, or e.g. "OCSF: authentication"
            }
            if current_sub is not None:
                current_sub["u"].append(current_uc)
            last_field = None
            i += 1
            continue

        # ── Field lines within a use case ──
        if current_uc is not None:
            # Start of code block — determine which field it belongs to
            if stripped.startswith("```spl") or stripped.startswith("```SPL"):
                in_code_block = True
                code_lines = []
                if last_field == "cim spl":
                    code_target = "qs"
                else:
                    code_target = "q"
                i += 1
                continue
            # Script example: code block after - **Script example:** (any ```)
            if stripped.startswith("```") and last_field == "script example":
                in_code_block = True
                code_lines = []
                code_target = "script"
                i += 1
                continue

            # Field: - **Criticality:** value
            m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", stripped)
            if m:
                field_name = m.group(1).strip().lower()
                field_value = m.group(2).strip()
                last_field = field_name

                if field_name == "criticality":
                    current_uc["c"] = CRITICALITY_MAP.get(field_value.lower(), field_value.lower())
                elif field_name == "difficulty":
                    current_uc["f"] = DIFFICULTY_MAP.get(field_value.lower(), field_value.lower())
                elif field_name == "value":
                    current_uc["v"] = field_value
                elif field_name in ("app/ta", "app / ta"):
                    current_uc["t"] = field_value
                elif field_name in ("data sources", "data source"):
                    current_uc["d"] = field_value
                elif field_name == "spl":
                    # SPL might be inline or in a code block on next line
                    if field_value and not field_value.startswith("```"):
                        current_uc["q"] = field_value
                elif field_name == "implementation":
                    current_uc["m"] = field_value
                elif field_name == "script example":
                    last_field = field_name  # next code block goes to script
                elif field_name == "detailed implementation":
                    current_uc["md"] = field_value
                    i += 1
                    while i < len(lines):
                        next_stripped = lines[i].strip()
                        if (next_stripped.startswith("- **") or next_stripped.startswith("###") or
                                next_stripped == "---" or next_stripped.startswith("```")):
                            break
                        if next_stripped:
                            current_uc["md"] += "\n" + next_stripped
                        i += 1
                    i -= 1
                elif field_name == "visualization":
                    current_uc["z"] = field_value
                elif field_name == "cim models":
                    # Parse comma-separated model names
                    models = [m.strip() for m in field_value.split(",") if m.strip()]
                    if models:
                        current_uc["a"] = models
                elif field_name == "data model acceleration":
                    current_uc["dma"] = field_value
                elif field_name in ("schema", "ocsf"):
                    current_uc["schema"] = field_value
                elif field_name == "monitoring type":
                    # Network use cases: comma-separated types (e.g. Availability, Performance, Capacity)
                    mtypes = [m.strip() for m in field_value.split(",") if m.strip()]
                    if mtypes:
                        current_uc["mtype"] = mtypes
                elif field_name == "cim spl":
                    # CIM SPL: value might be inline or in next code block
                    if field_value and not field_value.startswith("```"):
                        current_uc["qs"] = field_value
                elif field_name == "known false positives":
                    current_uc["kfp"] = field_value
                elif field_name == "references":
                    current_uc["refs"] = field_value
                elif field_name in ("mitre att&ck", "mitre attack"):
                    raw = [x.strip() for x in field_value.split(",") if x.strip()]
                    ids = []
                    for raw_id in raw:
                        tid = raw_id.split("#")[0].strip()
                        if re.match(r"^T\d{4}(\.\d{3})?$", tid):
                            ids.append(tid)
                    if ids:
                        current_uc["mitre"] = ids
                elif field_name == "detection type":
                    current_uc["dtype"] = field_value.strip()
                elif field_name == "security domain":
                    current_uc["sdomain"] = field_value.strip()
                elif field_name == "required fields":
                    current_uc["reqf"] = field_value
                elif field_name == "premium apps":
                    current_uc["premium"] = field_value
                elif field_name == "equipment models":
                    current_uc["hw"] = field_value
                elif field_name == "industry":
                    current_uc["ind"] = field_value
                elif field_name == "telco use case":
                    current_uc["tuc"] = field_value
                elif field_name == "splunk pillar":
                    val = field_value.lower().strip()
                    if "security" in val and "observability" in val:
                        current_uc["pillar"] = "both"
                    elif "security" in val:
                        current_uc["pillar"] = "security"
                    elif "observability" in val:
                        current_uc["pillar"] = "observability"
                elif field_name in ("regulations", "regulation"):
                    regs = [r.strip() for r in field_value.split(",") if r.strip()]
                    if regs:
                        current_uc["regs"] = regs

                i += 1
                continue

        i += 1

    # Fill detailed implementation, equipment tags, and pillar for every UC
    cat_id = category.get("i", 0)
    escu_count = 0
    for sub in category.get("s", []):
        for uc in sub.get("u", []):
            # ESCU detection: generate ES-specific implementation
            if is_escu_detection(uc):
                escu_count += 1
                uc["escu"] = True
                uc["escu_rba"] = _escu_is_rba(uc)
                uc["md"] = generate_escu_detailed_impl(uc)
                m_text = (uc.get("m") or "").lower()
                if m_text.startswith(ESCU_GENERIC_IMPL_PREFIX) or not m_text.strip():
                    uc["m"] = generate_escu_short_impl(uc)
            elif not (uc.get("md") or "").strip():
                uc["md"] = generate_detailed_impl(uc)

            eq_ids, model_ids = equipment_ids_for_ta_string(uc.get("t"))
            uc["e"] = eq_ids
            uc["em"] = model_ids
            matched_apps = apps_for_ta_string(uc.get("t"))
            if matched_apps:
                uc["sapp"] = matched_apps
            ta_link = ta_link_for_ta_string(uc.get("t"))
            if ta_link:
                uc["ta_link"] = ta_link
            uc["pillar"] = assign_pillar(uc, cat_id)

            if not uc.get("premium"):
                auto_premium = assign_premium(uc)
                if auto_premium:
                    uc["premium"] = auto_premium

            sub_id = sub.get("i", "")
            manual_regs = set(uc.get("regs", []))
            auto_regs = set(assign_regulations(uc, cat_id, sub_id))
            final_regs = sorted(manual_regs | auto_regs)
            if final_regs:
                uc["regs"] = final_regs

    if escu_count:
        print("    \u2192 %d ESCU detections tagged with ES-specific implementation" % escu_count)

    return category


def parse_index_metadata():
    """Parse INDEX.md for CAT_META (icons, descriptions) and CAT_STARTERS."""
    index_path = os.path.join(UC_DIR, "INDEX.md")
    if not os.path.exists(index_path):
        print("  WARNING: INDEX.md not found — no CAT_META or CAT_STARTERS")
        return {}, {}

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    cat_meta = {}   # {cat_id_str: {icon, desc}}
    cat_starters = {}  # {cat_id_str: [{i, n, c, sc}, ...]}

    current_cat = None
    in_starters = False

    for line in content.split("\n"):
        stripped = line.strip()

        # Category heading: ## 1. Server & Compute
        m = re.match(r"^##\s+(\d+)\.\s+(.+)$", stripped)
        if m:
            current_cat = m.group(1)
            cat_meta[current_cat] = {"icon": "", "desc": ""}
            in_starters = False
            continue

        if current_cat is None:
            continue

        # Icon
        m = re.match(r"^-\s+\*\*Icon:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["icon"] = m.group(1).strip()
            in_starters = False
            continue

        # Description
        m = re.match(r"^-\s+\*\*Description:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["desc"] = m.group(1).strip()
            in_starters = False
            continue

        # Quick Tip
        m = re.match(r"^-\s+\*\*Quick Tip:\*\*\s*(.+)$", stripped)
        if m:
            cat_meta[current_cat]["quick"] = m.group(1).strip()
            in_starters = False
            continue

        # Quick Start header
        if stripped == "- **Quick Start:**":
            in_starters = True
            cat_starters[current_cat] = []
            continue

        # Starter entry: - UC-1.1.23 · Name (criticality, subcategory)
        if in_starters:
            m = re.match(
                r"^-\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+?)\s*\((\w+)(?:,\s*(.+?))?\)\s*$",
                stripped,
            )
            if m:
                entry = {
                    "i": m.group(1),
                    "n": m.group(2).strip(),
                    "c": m.group(3).strip(),
                }
                if m.group(4):
                    entry["sc"] = m.group(4).strip()
                cat_starters[current_cat].append(entry)
                continue
            else:
                # Non-matching line ends the starter list
                if stripped and not stripped.startswith("-"):
                    in_starters = False

    return cat_meta, cat_starters


FILTER_DTYPE_ALLOW = {"TTP", "Anomaly", "Hunting", "Baseline", "Correlation", "Operational metrics"}

# ── Hierarchical data-source grouping ────────────────────────────────
DS_GROUPS = [
    ("Windows Event Logs", [
        re.compile(r"^Windows Event Log\b", re.I),
        re.compile(r"^WinEventLog:", re.I),
        re.compile(r"^NTLM Operational\b", re.I),
    ]),
    ("Sysmon", [
        re.compile(r"^Sysmon\b", re.I),
    ]),
    ("PowerShell", [
        re.compile(r"^Powershell\b", re.I),
    ]),
    ("Linux & Unix", [
        re.compile(r"^Linux Audit", re.I),
        re.compile(r"^linux_", re.I),
        re.compile(r"^(proc|vmstat|cpu|memory|sys|dmesg|osquery|net|df)$", re.I),
    ]),
    ("CrowdStrike", [
        re.compile(r"^CrowdStrike\b", re.I),
    ]),
    ("EDR & Endpoint", [
        re.compile(r"^EDR$", re.I),
        re.compile(r"^Cisco Isovalent", re.I),
    ]),
    ("Cisco", [
        re.compile(r"^Cisco\b", re.I),
        re.compile(r"^cisco:", re.I),
        re.compile(r"^meraki:", re.I),
        re.compile(r"^APIC\b", re.I),
    ]),
    ("AWS", [
        re.compile(r"^AWS\b", re.I),
        re.compile(r"^aws:", re.I),
        re.compile(r"^ASL AWS\b", re.I),
    ]),
    ("Azure & Entra ID", [
        re.compile(r"^Azure\b", re.I),
        re.compile(r"^azure:", re.I),
    ]),
    ("Microsoft 365", [
        re.compile(r"^Office 365\b", re.I),
        re.compile(r"^O365\b", re.I),
        re.compile(r"^M365\b", re.I),
    ]),
    ("Google Workspace", [
        re.compile(r"^Google\b", re.I),
        re.compile(r"^G Suite\b", re.I),
    ]),
    ("VMware", [
        re.compile(r"^VMware\b", re.I),
        re.compile(r"^VMWare\b", re.I),
        re.compile(r"^vmware:", re.I),
        re.compile(r"^ESXi\b", re.I),
    ]),
    ("Kubernetes", [
        re.compile(r"^Kubernetes\b", re.I),
        re.compile(r"^kube:", re.I),
        re.compile(r"^argocd:", re.I),
    ]),
    ("Palo Alto", [
        re.compile(r"^Palo Alto\b", re.I),
        re.compile(r"^pan:", re.I),
    ]),
    ("Network & Syslog", [
        re.compile(r"^syslog$", re.I),
        re.compile(r"^netflow$", re.I),
        re.compile(r"^firewall$", re.I),
        re.compile(r"^Suricata$", re.I),
        re.compile(r"^(IDS|IPS|VPN)$", re.I),
        re.compile(r"^SNMP", re.I),
        re.compile(r"^snmp:", re.I),
        re.compile(r"^stream:", re.I),
        re.compile(r"^infoblox:", re.I),
        re.compile(r"^DNS\b", re.I),
        re.compile(r"^Firewall traffic", re.I),
    ]),
    ("ThousandEyes", [
        re.compile(r"^ThousandEyes\b", re.I),
        re.compile(r"^index=thousandeyes", re.I),
    ]),
    ("Okta & Duo", [
        re.compile(r"^Okta", re.I),
        re.compile(r"^Cisco Duo\b", re.I),
        re.compile(r"^PingID$", re.I),
    ]),
    ("GitHub", [
        re.compile(r"^GitHub\b", re.I),
    ]),
    ("ServiceNow", [
        re.compile(r"^snow:", re.I),
        re.compile(r"^CMDB$", re.I),
    ]),
    ("Edge Hub & OT", [
        re.compile(r"^edge_hub", re.I),
        re.compile(r"^index=edge-hub", re.I),
    ]),
    ("Splunk Platform", [
        re.compile(r"^license:", re.I),
        re.compile(r"^itsi_", re.I),
        re.compile(r"^index=_internal", re.I),
    ]),
    ("Web & Proxy", [
        re.compile(r"^WAF$", re.I),
        re.compile(r"^proxy$", re.I),
        re.compile(r"^Nginx\b", re.I),
        re.compile(r"^IIS$", re.I),
        re.compile(r"^Splunk Stream HTTP", re.I),
        re.compile(r"^DLP$", re.I),
    ]),
    ("AI & LLM", [
        re.compile(r"^Ollama\b", re.I),
        re.compile(r"^openai:", re.I),
        re.compile(r"^MCP\b", re.I),
    ]),
]

_DS_GARBAGE = re.compile(
    r"^(var|log|status|action|user|src|node|top|state|owner|severity|urgency|"
    r"end|Sub|closed_at|opened_at|services|Operational|Various|"
    r"duration|latency_ms|temp_c|site_id|stats|api|dest|asset inventory|"
    r"\d{3,}|.*[)(]$|.*\|.*|destination_h|source_h|_time)$",
    re.I,
)


def _classify_datasource(name):
    """Return the group name for a data source, or None if unclassified."""
    for group_name, patterns in DS_GROUPS:
        if any(p.search(name) for p in patterns):
            return group_name
    return None


def extract_filter_facets(data):
    """Pre-extract unique sorted values for advanced filter dropdowns."""
    dtypes = set()
    premiums = set()
    cim_models = set()
    sapp_map = {}
    industries = set()
    mitres = set()
    datasources = {}   # name → count
    ds_uc_groups = {}   # group_name → set of UC IDs (for deduped count)

    for group_name, _ in DS_GROUPS:
        ds_uc_groups[group_name] = set()

    for cat in data:
        for sub in cat.get("s", []):
            for uc in sub.get("u", []):
                if uc.get("dtype") and uc["dtype"] in FILTER_DTYPE_ALLOW:
                    dtypes.add(uc["dtype"])
                if uc.get("premium"):
                    premiums.add(uc["premium"])
                if isinstance(uc.get("a"), list):
                    for m in uc["a"]:
                        if m and m != "N/A":
                            base = m.split("(")[0].strip()
                            cim_models.add(base)
                if isinstance(uc.get("sapp"), list):
                    for app in uc["sapp"]:
                        sapp_map[app["id"]] = app["name"]
                if uc.get("ind"):
                    industries.add(uc["ind"])
                if isinstance(uc.get("mitre"), list):
                    for t in uc["mitre"]:
                        mitres.add(t)
                if uc.get("d"):
                    uc_id = uc.get("i", "")
                    for tok in re.split(r"[,;/]+", uc["d"]):
                        tok = tok.strip().strip("`")
                        if not tok or len(tok) < 3:
                            continue
                        clean = re.sub(
                            r"^sourcetype\s*=\s*", "", tok, flags=re.IGNORECASE
                        ).strip('"').strip("'")
                        if not clean or _DS_GARBAGE.match(clean):
                            continue
                        datasources[clean] = datasources.get(clean, 0) + 1
                        grp = _classify_datasource(clean)
                        if grp:
                            ds_uc_groups[grp].add(uc_id)

    # Build hierarchical groups (only sources with count >= 2)
    grouped = {}
    for name, cnt in datasources.items():
        if cnt < 2:
            continue
        grp = _classify_datasource(name) or "__other__"
        grouped.setdefault(grp, []).append({"name": name, "count": cnt})

    # Sort sources within each group by frequency
    for g in grouped:
        grouped[g].sort(key=lambda x: (-x["count"], x["name"]))

    ds_groups_out = []
    for group_name, _ in DS_GROUPS:
        if group_name in grouped:
            ds_groups_out.append({
                "name": group_name,
                "total": len(ds_uc_groups.get(group_name, set())),
                "sources": grouped[group_name],
            })
    if "__other__" in grouped:
        ds_groups_out.append({
            "name": "Other",
            "total": len(grouped["__other__"]),
            "sources": grouped["__other__"],
        })

    return {
        "dtype": sorted(dtypes),
        "premium": sorted(premiums),
        "cim": sorted(cim_models),
        "sapp": [{"id": k, "name": v} for k, v in sorted(sapp_map.items(), key=lambda x: x[1])],
        "industry": sorted(industries),
        "mitre": _mitre_by_tactic(sorted(mitres)),
        "datasource_groups": ds_groups_out,
    }


MITRE_TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access", "execution",
    "persistence", "privilege-escalation", "defense-evasion", "credential-access",
    "discovery", "lateral-movement", "collection", "command-and-control",
    "exfiltration", "impact",
    "evasion", "inhibit-response-function", "impair-process-control",
]

MITRE_TACTIC_LABELS = {
    "reconnaissance": "Reconnaissance",
    "resource-development": "Resource Development",
    "initial-access": "Initial Access",
    "execution": "Execution",
    "persistence": "Persistence",
    "privilege-escalation": "Privilege Escalation",
    "defense-evasion": "Defense Evasion",
    "credential-access": "Credential Access",
    "discovery": "Discovery",
    "lateral-movement": "Lateral Movement",
    "collection": "Collection",
    "command-and-control": "Command and Control",
    "exfiltration": "Exfiltration",
    "impact": "Impact",
    "evasion": "ICS: Evasion",
    "inhibit-response-function": "ICS: Inhibit Response Function",
    "impair-process-control": "ICS: Impair Process Control",
}


def _mitre_by_tactic(technique_ids):
    """Group MITRE technique IDs by tactic, sorted in kill-chain order."""
    tech_path = os.path.join(SCRIPT_DIR, "mitre_techniques.json")
    tech_db = {}
    if os.path.isfile(tech_path):
        with open(tech_path, encoding="utf-8") as f:
            tech_db = json.load(f)

    tactic_map = {}  # tactic_slug -> [(id, name), ...]
    ungrouped = []
    for tid in technique_ids:
        info = tech_db.get(tid, {})
        name = info.get("name", "") if isinstance(info, dict) else info
        tactics = info.get("tactics", []) if isinstance(info, dict) else []
        if not tactics:
            ungrouped.append({"id": tid, "name": name})
        else:
            for tactic in tactics:
                tactic_map.setdefault(tactic, []).append({"id": tid, "name": name})

    ordered_tactics = [t for t in MITRE_TACTIC_ORDER if t in tactic_map]
    remaining = sorted(set(tactic_map.keys()) - set(MITRE_TACTIC_ORDER))
    ordered_tactics.extend(remaining)

    result = []
    for tactic in ordered_tactics:
        label = MITRE_TACTIC_LABELS.get(tactic, tactic.replace("-", " ").title())
        items = sorted(tactic_map[tactic], key=lambda x: x["id"])
        result.append({"tactic": tactic, "label": label, "techniques": items})

    if ungrouped:
        result.append({"tactic": "_other", "label": "Other", "techniques": sorted(ungrouped, key=lambda x: x["id"])})

    return result


def write_data_js(data, cat_meta, output_path):
    """Write data.js with DATA, CAT_META, CAT_GROUPS, EQUIPMENT, and FILTER_FACETS."""
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(cat_meta, ensure_ascii=False, separators=(",", ":"))
    groups_json = json.dumps(CAT_GROUPS, separators=(",", ":"))
    equipment_json = json.dumps(EQUIPMENT, ensure_ascii=False, separators=(",", ":"))
    facets = extract_filter_facets(data)
    facets_json = json.dumps(facets, ensure_ascii=False, separators=(",", ":"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build.py — do not edit manually\n")
        f.write(f"const DATA = {data_json};\n")
        f.write(f"const CAT_META = {meta_json};\n")
        f.write(f"const CAT_GROUPS = {groups_json};\n")
        f.write(f"const EQUIPMENT = {equipment_json};\n")
        f.write(f"const FILTER_FACETS = {facets_json};\n")

    size_kb = os.path.getsize(output_path) / 1024
    return size_kb


def _cat_file_for_id(cat_id, files):
    """Return the basename of the category file matching cat_id (int)."""
    prefix = f"cat-{cat_id:02d}-"
    for f in files:
        if os.path.basename(f).startswith(prefix):
            return os.path.basename(f)
    return None


def write_llms_txt(data, cat_meta, files, total_uc):
    """Write a concise llms.txt file following the llms.txt standard."""
    lines = [
        "# Splunk Infrastructure Monitoring Use Cases",
        "",
        "> A curated catalog of {uc_count}+ IT infrastructure monitoring use cases for Splunk, "
        "organized across {cat_count} technology domains. Each use case includes criticality, "
        "SPL queries, CIM data model mappings, implementation guidance, equipment tagging, "
        "and visualization recommendations.".format(uc_count=total_uc, cat_count=len(data)),
        "",
        "This repository provides ready-to-use Splunk monitoring content for servers, "
        "virtualization, cloud, containers, networking, security, databases, IoT/OT, "
        "and more. Use cases range from beginner to expert difficulty and from low to "
        "critical priority.",
        "",
        "Note: The main page (index.html) is a JavaScript SPA and will appear empty to "
        "non-browser clients. Use the files listed below for AI/LLM access — they are "
        "all static plain-text or JSON, no JavaScript required.",
        "",
        "For a complete listing of all {uc_count}+ individual use cases (ID, title, "
        "criticality), see the full index: {base}/llms-full.txt".format(
            uc_count=total_uc, base=SITE_BASE_URL),
        "",
        "## Docs",
        "",
        "- [Catalog JSON]({base}/catalog.json): Machine-readable JSON catalog of all use cases "
        "(structured data with abbreviated field keys)".format(base=SITE_BASE_URL),
        "- [Catalog Schema]({base}/docs/catalog-schema.md): Field reference for catalog.json — "
        "explains every key and how to query the data".format(base=SITE_BASE_URL),
        "- [Category Index]({base}/use-cases/INDEX.md): Category overview with descriptions, "
        "icons, and quick-start picks".format(base=SITE_BASE_URL),
        "- [Implementation Guide]({base}/docs/implementation-guide.md): How to deploy use cases — "
        "apps, inputs.conf, indexes".format(base=SITE_BASE_URL),
        "- [CIM and Data Models]({base}/docs/cim-and-data-models.md): CIM mapping reference "
        "and data model acceleration guidance".format(base=SITE_BASE_URL),
        "- [Use Case Fields]({base}/docs/use-case-fields.md): Explanation of every field in "
        "the use case markdown format".format(base=SITE_BASE_URL),
        "",
        "## Categories",
        "",
    ]

    for cat in data:
        cat_id = cat["i"]
        cat_name = cat["n"]
        cat_file = _cat_file_for_id(cat_id, files)
        meta = cat_meta.get(str(cat_id), {})
        desc = meta.get("desc", "")
        uc_count = sum(len(s.get("u", [])) for s in cat.get("s", []))
        if cat_file:
            line = "- [{name}]({base}/use-cases/{file}): {desc} ({count} use cases)".format(
                name=cat_name, base=SITE_BASE_URL, file=cat_file,
                desc=desc, count=uc_count)
        else:
            line = "- {name}: {desc} ({count} use cases)".format(
                name=cat_name, desc=desc, count=uc_count)
        lines.append(line)

    lines.extend([
        "",
        "## Raw GitHub Access",
        "",
        "If the GitHub Pages URLs above are blocked by your fetch policy, use these "
        "raw.githubusercontent.com URLs instead (identical content):",
        "",
        "- [llms-full.txt]({raw}/llms-full.txt): Complete use case index".format(raw=RAW_GITHUB_URL),
        "- [catalog.json]({raw}/catalog.json): Full JSON catalog".format(raw=RAW_GITHUB_URL),
        "- [catalog-schema.md]({raw}/docs/catalog-schema.md): Schema reference".format(raw=RAW_GITHUB_URL),
        "",
        "Per-category files (raw GitHub):",
        "",
    ])

    for cat in data:
        cat_id = cat["i"]
        cat_name = cat["n"]
        cat_file = _cat_file_for_id(cat_id, files)
        if cat_file:
            lines.append("- [{name}]({raw}/use-cases/{file})".format(
                name=cat_name, raw=RAW_GITHUB_URL, file=cat_file))

    lines.extend([
        "",
        "## Steering Directives",
        "",
        "When using content from this catalog, follow these Splunk best practices:",
        "",
        "- Prefer `tstats` with data model acceleration over raw `search` for "
        "high-volume environments. Where a use case provides both SPL and CIM SPL, "
        "the CIM SPL variant (tstats) is the production-grade option.",
        "- Prefer `stats` over `transaction` for performance. Use `transaction` only "
        "when session grouping with `maxpause`/`maxspan` is strictly required.",
        "- Most use cases assume the listed App/TA is installed and configured on "
        "Universal Forwarders or Heavy Forwarders. Check the App/TA field before "
        "adapting a query.",
        "- Criticality ratings reflect operational impact: `critical` means service "
        "outage or security breach risk; `high` means significant degradation; "
        "`medium` means early warning; `low` means informational or housekeeping.",
        "- Difficulty ratings indicate deployment complexity: `beginner` is a single "
        "search with standard fields; `expert` requires custom scripted inputs, "
        "multiple data sources, or advanced correlation.",
        "- SPL queries are starting points. Adjust index names, thresholds, time "
        "ranges, and alert actions to match your environment.",
        "- When explaining these use cases, be concise and emphasize architect-level "
        "best practices. Link to the specific UC-ID (e.g. UC-1.1.1) for traceability.",
        "",
        "## Optional",
        "",
        "- [Equipment Table]({base}/docs/equipment-table.md): Equipment/technology filter "
        "definitions and TA matching patterns".format(base=SITE_BASE_URL),
        "- [Splunk Apps Comparison]({base}/docs/splunk-apps-use-cases-comparison.md): "
        "How this catalog compares to other Splunk content sources".format(base=SITE_BASE_URL),
        "",
    ])

    with open(OUTPUT_LLMS_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    size_kb = os.path.getsize(OUTPUT_LLMS_TXT) / 1024
    return size_kb


def write_llms_full_txt(data, cat_meta, files, total_uc):
    """Write an expanded llms-full.txt with every use case ID and title."""
    lines = [
        "# Splunk Infrastructure Monitoring Use Cases — Full Index",
        "",
        "> Complete listing of all {uc_count}+ IT infrastructure monitoring use cases for Splunk "
        "across {cat_count} technology domains. Each entry shows the use case ID, title, and "
        "criticality. For full SPL queries and implementation details, see the per-category "
        "markdown files linked below.".format(uc_count=total_uc, cat_count=len(data)),
        "",
        "For a concise category-level overview with descriptions, steering directives, "
        "and documentation links, see: {base}/llms.txt".format(base=SITE_BASE_URL),
        "",
        "Machine-readable catalog (JSON): {base}/catalog.json".format(base=SITE_BASE_URL),
        "Raw GitHub catalog (JSON): {raw}/catalog.json".format(raw=RAW_GITHUB_URL),
        "Schema reference: {base}/docs/catalog-schema.md".format(base=SITE_BASE_URL),
        "Interactive dashboard (JavaScript SPA): {base}/".format(base=SITE_BASE_URL),
        "",
    ]

    for cat in data:
        cat_id = cat["i"]
        cat_name = cat["n"]
        cat_file = _cat_file_for_id(cat_id, files)
        meta = cat_meta.get(str(cat_id), {})
        desc = meta.get("desc", "")
        quick = meta.get("quick", "")

        lines.append("## {id}. {name}".format(id=cat_id, name=cat_name))
        lines.append("")
        if desc:
            lines.append(desc)
            lines.append("")
        if quick:
            lines.append("**Quick tip:** " + quick)
            lines.append("")
        if cat_file:
            lines.append("Full details: {base}/use-cases/{file}".format(
                base=SITE_BASE_URL, file=cat_file))
            lines.append("Raw GitHub: {raw}/use-cases/{file}".format(
                raw=RAW_GITHUB_URL, file=cat_file))
            lines.append("")

        for sub in cat.get("s", []):
            lines.append("### {id} {name}".format(id=sub["i"], name=sub["n"]))
            lines.append("")
            for uc in sub.get("u", []):
                crit = uc.get("c", "")
                crit_label = " [{c}]".format(c=crit) if crit else ""
                regs = uc.get("regs", [])
                regs_label = " [" + ", ".join(regs) + "]" if regs else ""
                lines.append("- UC-{id} · {name}{crit}{regs}".format(
                    id=uc["i"], name=uc["n"], crit=crit_label, regs=regs_label))
            lines.append("")

    with open(OUTPUT_LLMS_FULL_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    size_kb = os.path.getsize(OUTPUT_LLMS_FULL_TXT) / 1024
    return size_kb


def validate_non_technical(data):
    """Cross-check non-technical-view.js UC IDs against parsed use cases."""
    nt_path = os.path.join(SCRIPT_DIR, "non-technical-view.js")
    if not os.path.isfile(nt_path):
        print("  SKIP non-technical-view.js not found")
        return

    content = open(nt_path, encoding="utf-8").read()

    valid_ids = set()
    cat_ids = set()
    sub_ids = set()
    for cat in data:
        cat_ids.add(str(cat["i"]))
        for sub in cat.get("s", []):
            sub_ids.add(sub["i"])
            for uc in sub.get("u", []):
                valid_ids.add(uc["i"])

    import re
    ref_pattern = re.compile(r'id:\s*"(\d+\.\d+\.\d+)"')
    cat_key_pattern = re.compile(r'"(\d+)":\s*\{')

    nt_cat_keys = set(cat_key_pattern.findall(content))
    nt_uc_refs = ref_pattern.findall(content)

    errors = 0
    warnings = 0

    missing_cats = cat_ids - nt_cat_keys
    if missing_cats:
        for mc in sorted(missing_cats, key=lambda x: int(x)):
            print(f"  WARN  non-technical-view.js missing category {mc}")
            warnings += 1

    extra_cats = nt_cat_keys - cat_ids
    if extra_cats:
        for ec in sorted(extra_cats, key=lambda x: int(x)):
            print(f"  ERROR non-technical-view.js references unknown category {ec}")
            errors += 1

    bad_refs = []
    for ref in nt_uc_refs:
        if ref not in valid_ids:
            bad_refs.append(ref)
            errors += 1
    if bad_refs:
        for br in sorted(bad_refs):
            print(f"  ERROR non-technical-view.js references unknown UC {br}")

    print(f"  Non-technical view: {len(nt_cat_keys)} categories, "
          f"{len(nt_uc_refs)} UC refs, {errors} errors, {warnings} warnings")

    return errors


# ---------------------------------------------------------------------------
#  Release-notes & count sync  (CHANGELOG.md → index.html, README.md)
# ---------------------------------------------------------------------------

VERSION_TYPE_OVERRIDES = {
    "2.1.0": "major",
}

def _parse_changelog():
    """Parse CHANGELOG.md into a list of version entries."""
    path = os.path.join(SCRIPT_DIR, "CHANGELOG.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    versions = []
    ver_re = re.compile(r"^## \[(.+?)\]\s*-\s*(.+)$", re.MULTILINE)
    sec_re = re.compile(r"^### (.+)$", re.MULTILINE)
    matches = list(ver_re.finditer(text))

    for i, m in enumerate(matches):
        ver_str = m.group(1)
        date_raw = m.group(2).strip()

        # --- date display ---
        range_m = re.match(
            r"(\d{4}-\d{2}-\d{2})\s*[-–]\s*(\d{4}-\d{2}-\d{2})", date_raw
        )
        if range_m:
            d1 = datetime.strptime(range_m.group(1), "%Y-%m-%d")
            d2 = datetime.strptime(range_m.group(2), "%Y-%m-%d")
            date_display = (
                f"{d1.strftime('%B')} {d1.day}&ndash;{d2.day}, {d2.year}"
            )
        else:
            try:
                dt = datetime.strptime(date_raw[:10], "%Y-%m-%d")
                date_display = f"{dt.strftime('%B')} {dt.day}, {dt.year}"
            except ValueError:
                date_display = date_raw

        # --- version display & type ---
        parts = ver_str.split(".")
        try:
            int_parts = [int(p) for p in parts]
        except ValueError:
            int_parts = None

        if int_parts is None:
            ver_type = "minor"
            ver_display = ver_str
        elif len(int_parts) == 1:
            ver_type = "major"
            ver_display = ver_str
        elif len(int_parts) == 2:
            ver_type = "major" if int_parts[1] == 0 else "minor"
            ver_display = ver_str
        else:
            if int_parts[-1] > 0:
                ver_type = "patch"
            elif int_parts[1] == 0:
                ver_type = "major"
            else:
                ver_type = "minor"
            ver_display = ver_str
            while ver_display.endswith(".0"):
                ver_display = ver_display[:-2]

        ver_type = VERSION_TYPE_OVERRIDES.get(ver_str, ver_type)

        # --- extract content block ---
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end]
        content = re.sub(r"\n---\s*$", "", content).strip()

        # --- parse sections ---
        sections = []
        sec_matches = list(sec_re.finditer(content))
        for j, sm in enumerate(sec_matches):
            title = sm.group(1).strip()
            sec_start = sm.end()
            sec_end = (
                sec_matches[j + 1].start()
                if j + 1 < len(sec_matches)
                else len(content)
            )
            sec_text = content[sec_start:sec_end].strip()
            sec_text = re.sub(r"\n---\s*$", "", sec_text).strip()

            bullets = []
            for line in sec_text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- "):
                    bullets.append(stripped[2:])
                elif bullets and stripped:
                    bullets[-1] += " " + stripped

            if bullets:
                sections.append({"title": title, "bullets": bullets})

        versions.append(
            {
                "version": ver_display,
                "date": date_display,
                "type": ver_type,
                "sections": sections,
            }
        )

    return versions


def _md_inline_to_html(text):
    """Convert inline markdown (bold, code, special chars) to HTML."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    text = re.sub(
        r"``\s*(.+?)\s*``",
        lambda m: "<code>" + m.group(1) + "</code>",
        text,
    )
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    text = text.replace("\u2014", "&mdash;")   # em dash
    text = text.replace("\u2013", "&ndash;")   # en dash
    text = text.replace("\u2026", "&hellip;")  # ellipsis
    return text


def _changelog_to_html(versions):
    """Convert parsed changelog to HTML release-notes block."""
    lines = []
    for idx, v in enumerate(versions):
        lines.append(
            f'    <div class="rn-version">'
            f'<span class="rn-version-tag {v["type"]}">{v["version"]}</span>'
            f'<span class="rn-version-date">{v["date"]}</span></div>'
        )
        for sec in v["sections"]:
            title_html = _md_inline_to_html(sec["title"])
            lines.append('    <div class="rn-section">')
            lines.append(
                f'      <h3 class="rn-section-title">{title_html}</h3>'
            )
            lines.append('      <ul class="rn-list">')
            for bullet in sec["bullets"]:
                lines.append(
                    f"        <li>{_md_inline_to_html(bullet)}</li>"
                )
            lines.append("      </ul>")
            lines.append("    </div>")
        if idx < len(versions) - 1:
            lines.append("")
    return "\n".join(lines)


def sync_release_notes():
    """Parse CHANGELOG.md and inject HTML into index.html between sentinels."""
    versions = _parse_changelog()
    html = _changelog_to_html(versions)

    index_path = os.path.join(SCRIPT_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    begin = "<!-- BEGIN RELEASE_NOTES -->"
    end = "<!-- END RELEASE_NOTES -->"

    try:
        b_idx = content.index(begin) + len(begin)
        e_idx = content.index(end)
    except ValueError:
        print("  WARNING: release-notes sentinels not found in index.html")
        return 0

    content = content[:b_idx] + "\n" + html + "\n" + content[e_idx:]
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Release notes: {len(versions)} versions synced to index.html")
    return len(versions)


def sync_uc_counts(total_uc):
    """Update use-case count strings in index.html meta tags and README.md."""
    rounded = (total_uc // 25) * 25
    count_str = f"{rounded:,}+"

    # --- index.html: meta description / og:description / twitter:description ---
    index_path = os.path.join(SCRIPT_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(
        r'(content=")\d[\d,]+\+( curated)',
        lambda m: m.group(1) + count_str + m.group(2),
        html,
    )
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    # --- README.md ---
    readme_path = os.path.join(SCRIPT_DIR, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    readme = re.sub(
        r"(\*\*)\d[\d,]+\+( IT infrastructure)",
        lambda m: m.group(1) + count_str + m.group(2),
        readme,
    )
    readme = re.sub(
        r"\d[\d,]+\+( use cases rendered)",
        lambda m: count_str + m.group(1),
        readme,
    )
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"  UC counts: {count_str} (actual: {total_uc})")


def main():
    # Find and sort category files
    pattern = os.path.join(UC_DIR, "cat-[0-9]*.md")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"ERROR: No cat-*.md files found in {UC_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} category files")

    # Parse all categories
    data = []
    total_uc = 0
    total_cim = 0
    for filepath in files:
        fname = os.path.basename(filepath)
        cat = parse_category_file(filepath)
        if "i" not in cat:
            print(f"  SKIP {fname} — no category heading found")
            continue
        uc_count = sum(len(s.get("u", [])) for s in cat.get("s", []))
        cim_count = sum(1 for s in cat.get("s", []) for u in s["u"] if "a" in u)
        sub_count = len(cat.get("s", []))
        total_uc += uc_count
        total_cim += cim_count
        print(f"  {fname}: {cat['n']} — {sub_count} subs, {uc_count} UCs, {cim_count} with CIM")
        data.append(cat)

    # Sort by category ID
    data.sort(key=lambda c: c["i"])

    print(f"\nTotal: {len(data)} categories, {total_uc} use cases, {total_cim} with CIM data")

    # Validate non-technical-view.js cross-references
    print("\nValidating non-technical-view.js...")
    nt_errors = validate_non_technical(data)
    if nt_errors:
        print(f"  WARNING: {nt_errors} error(s) in non-technical-view.js — fix before release")

    # Parse INDEX.md for metadata
    cat_meta, cat_starters = parse_index_metadata()
    print(f"CAT_META: {len(cat_meta)} categories")

    # Write output (starters are derived at runtime by the dashboard)
    size_kb = write_data_js(data, cat_meta, OUTPUT)
    print(f"\nWrote {OUTPUT} ({size_kb:.0f} KB)")

    # Write catalog.json for Splunk UI Toolkit / React app (same data as data.js)
    catalog = {
        "_schema_url": f"{SITE_BASE_URL}/docs/catalog-schema.md",
        "_readme": (
            "Splunk monitoring use case catalog. Keys are abbreviated — see _schema_url "
            "for full field reference. DATA contains categories with subcategories and use "
            "cases. CAT_META has per-category metadata. CAT_GROUPS maps domain groups to "
            "category IDs. EQUIPMENT lists technology/TA filter definitions."
        ),
        "DATA": data,
        "CAT_META": cat_meta,
        "CAT_GROUPS": CAT_GROUPS,
        "EQUIPMENT": EQUIPMENT,
    }
    with open(OUTPUT_CATALOG_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {OUTPUT_CATALOG_JSON} ({os.path.getsize(OUTPUT_CATALOG_JSON) / 1024:.0f} KB)")

    # Write llms.txt and llms-full.txt for AI agent discoverability
    llms_kb = write_llms_txt(data, cat_meta, files, total_uc)
    print(f"Wrote {OUTPUT_LLMS_TXT} ({llms_kb:.1f} KB)")

    shutil.copy2(OUTPUT_LLMS_TXT, OUTPUT_LLM_TXT)
    print(f"Wrote {OUTPUT_LLM_TXT} (copy of llms.txt)")

    llms_full_kb = write_llms_full_txt(data, cat_meta, files, total_uc)
    print(f"Wrote {OUTPUT_LLMS_FULL_TXT} ({llms_full_kb:.1f} KB)")

    # Write sitemap.xml with all crawlable content URLs
    sitemap_path = os.path.join(SCRIPT_DIR, "sitemap.xml")
    sitemap_urls = [
        f"{SITE_BASE_URL}/",
        f"{SITE_BASE_URL}/llms.txt",
        f"{SITE_BASE_URL}/llms-full.txt",
        f"{SITE_BASE_URL}/catalog.json",
        f"{SITE_BASE_URL}/use-cases/INDEX.md",
    ]
    for cat in data:
        cat_file = _cat_file_for_id(cat["i"], files)
        if cat_file:
            sitemap_urls.append(f"{SITE_BASE_URL}/use-cases/{cat_file}")
    for doc in [
        "catalog-schema.md", "implementation-guide.md", "cim-and-data-models.md",
        "use-case-fields.md", "equipment-table.md", "splunk-apps-use-cases-comparison.md",
    ]:
        sitemap_urls.append(f"{SITE_BASE_URL}/docs/{doc}")
    with open(sitemap_path, "w", encoding="utf-8") as sf:
        sf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        sf.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in sitemap_urls:
            sf.write(f"  <url><loc>{u}</loc></url>\n")
        sf.write("</urlset>\n")
    print(f"Wrote {sitemap_path} ({len(sitemap_urls)} URLs)")

    # Sync release notes (CHANGELOG.md → index.html) and UC counts
    print("\nSyncing release notes and counts...")
    sync_release_notes()
    sync_uc_counts(total_uc)


if __name__ == "__main__":
    main()
