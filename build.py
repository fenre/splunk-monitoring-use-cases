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
    "app":        [7, 8, 11, 12, 13, 14, 16, 21],
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
     "desc": "Pre-built dashboards for Unix/Linux performance, capacity and alerting"},
    {"name": "Splunk App for Windows Infrastructure", "id": 1680,
     "url": "https://splunkbase.splunk.com/app/1680",
     "screenshots": ["https://cdn.splunkbase.splunk.com/media/public/screenshots/9d9652a4-7499-11e3-b0c8-005056ad5c72.png", "https://cdn.splunkbase.splunk.com/media/public/screenshots/b9eee34e-c197-11e3-85b1-06550dde6d3e.png"],
     "tas": ["Splunk_TA_windows"], "archived": True,
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
     "tas": ["Splunk_TA_paloalto", "Palo Alto"],
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
                matched.append({
                    "name": app["name"],
                    "id": app["id"],
                    "url": app["url"],
                    "desc": app.get("desc", ""),
                    "screenshots": app.get("screenshots", []),
                    "archived": app.get("archived", False),
                })
                break
    return matched


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


def generate_detailed_impl(uc):
    """Generate a thorough step-by-step implementation guide from UC fields (used when no explicit Detailed implementation is in markdown)."""
    t = (uc.get("t") or "").strip()
    d = (uc.get("d") or "").strip()
    m = (uc.get("m") or "").strip()
    z = (uc.get("z") or "").strip()
    q = (uc.get("q") or "").strip()
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
        lines.append("If the use case includes a tstats/CIM query, enable Data Model Acceleration for the relevant data model.")
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
    for sub in category.get("s", []):
        for uc in sub.get("u", []):
            if not (uc.get("md") or "").strip():
                uc["md"] = generate_detailed_impl(uc)
            eq_ids, model_ids = equipment_ids_for_ta_string(uc.get("t"))
            uc["e"] = eq_ids
            uc["em"] = model_ids
            matched_apps = apps_for_ta_string(uc.get("t"))
            if matched_apps:
                uc["sapp"] = matched_apps
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


def write_data_js(data, cat_meta, output_path):
    """Write data.js with DATA, CAT_META, CAT_GROUPS, and EQUIPMENT."""
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(cat_meta, ensure_ascii=False, separators=(",", ":"))
    groups_json = json.dumps(CAT_GROUPS, separators=(",", ":"))
    equipment_json = json.dumps(EQUIPMENT, ensure_ascii=False, separators=(",", ":"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build.py — do not edit manually\n")
        f.write(f"const DATA = {data_json};\n")
        f.write(f"const CAT_META = {meta_json};\n")
        f.write(f"const CAT_GROUPS = {groups_json};\n")
        f.write(f"const EQUIPMENT = {equipment_json};\n")

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


if __name__ == "__main__":
    main()
