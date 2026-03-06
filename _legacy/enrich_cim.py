#!/usr/bin/env python3
"""
Enrich use-case-dashboard.html with CIM data model fields:
  a  : list of CIM model names (e.g. ["Performance", "Authentication"]) or "N/A"
  qs : tstats example query (string) — added where CIM model applies

Writes back to HTML every 5 use cases processed and reports progress.
"""

import json
import re
import sys

HTML_PATH = "/Users/fsudmann/Splunk Core Infrastructure Monitoring/use-case-dashboard.html"

# ─────────────────────────────────────────────────────────────────────────────
# TSTATS QUERY TEMPLATES  (contextual per use case name)
# ─────────────────────────────────────────────────────────────────────────────

def tstats_perf_cpu(uc):
    return (
        "| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu\n"
        "  from datamodel=Performance where nodename=Performance.CPU\n"
        "  by Performance.host span=1h\n"
        "| where avg_cpu > 90"
    )

def tstats_perf_memory(uc):
    return (
        "| tstats `summariesonly` avg(Performance.mem_used_percent) as mem_pct\n"
        "                        avg(Performance.swap_used_percent) as swap_pct\n"
        "  from datamodel=Performance where nodename=Performance.Memory\n"
        "  by Performance.host span=5m\n"
        "| where mem_pct > 95 OR swap_pct > 20"
    )

def tstats_perf_storage(uc):
    return (
        "| tstats `summariesonly` avg(Performance.disk_used_percent) as disk_pct\n"
        "  from datamodel=Performance where nodename=Performance.Storage\n"
        "  by Performance.host Performance.mount span=1h\n"
        "| where disk_pct > 85"
    )

def tstats_perf_network(uc):
    return (
        "| tstats `summariesonly` sum(Performance.bytes_in) as bytes_in\n"
        "                        sum(Performance.bytes_out) as bytes_out\n"
        "  from datamodel=Performance where nodename=Performance.Network\n"
        "  by Performance.host Performance.interface span=5m"
    )

def tstats_perf_uptime(uc):
    return (
        "| tstats `summariesonly` latest(Performance.uptime) as uptime_sec\n"
        "  from datamodel=Performance where nodename=Performance.Uptime\n"
        "  by Performance.host\n"
        "| eval uptime_days = round(uptime_sec / 86400, 1)"
    )

def tstats_perf_generic(uc):
    """Fallback for VMware / Hyper-V use cases — pick sub-node from name."""
    n = uc.get('n', '').lower()
    if any(k in n for k in ['cpu', 'processor', 'compute']):
        return tstats_perf_cpu(uc)
    elif any(k in n for k in ['memory', 'mem ', 'swap', 'ram']):
        return tstats_perf_memory(uc)
    elif any(k in n for k in ['disk', 'storage', 'i/o', ' io ', 'iops', 'datastore', 'filesystem', 'volume']):
        return tstats_perf_storage(uc)
    elif any(k in n for k in ['network', 'interface', 'bandwidth', 'throughput', 'nic']):
        return tstats_perf_network(uc)
    elif any(k in n for k in ['uptime', 'availability', 'reboot']):
        return tstats_perf_uptime(uc)
    else:
        return tstats_perf_cpu(uc)

def tstats_auth(uc):
    n = uc.get('n', '').lower()
    if any(k in n for k in ['brute', 'failure', 'failed', 'lockout', 'spray', 'invalid']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Authentication.Authentication\n"
            "  where Authentication.action=failure\n"
            "  by Authentication.user Authentication.src span=1h\n"
            "| where count > 10"
        )
    elif any(k in n for k in ['privilege', 'escalat', 'admin', 'sudo', 'root access', 'elevation']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Authentication.Authentication\n"
            "  where Authentication.action=success\n"
            "  by Authentication.user Authentication.src Authentication.dest span=1h\n"
            "| search Authentication.user=*admin* OR Authentication.user=root"
        )
    elif any(k in n for k in ['success', 'logon trend', 'login trend', 'activity']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Authentication.Authentication\n"
            "  by Authentication.action Authentication.user Authentication.src span=1h\n"
            "| sort -count"
        )
    else:
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Authentication.Authentication\n"
            "  where Authentication.action=failure\n"
            "  by Authentication.user Authentication.src Authentication.dest span=1h\n"
            "| where count > 5"
        )

def tstats_network_traffic(uc):
    n = uc.get('n', '').lower()
    if any(k in n for k in ['block', 'deny', 'drop', 'reject']):
        return (
            "| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes\n"
            "  from datamodel=Network_Traffic.All_Traffic\n"
            "  where All_Traffic.action=blocked\n"
            "  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h\n"
            "| sort -count"
        )
    elif any(k in n for k in ['bandwidth', 'throughput', 'utilization', 'top talker']):
        return (
            "| tstats `summariesonly` sum(All_Traffic.bytes) as bytes\n"
            "  from datamodel=Network_Traffic.All_Traffic\n"
            "  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h\n"
            "| sort -bytes"
        )
    else:
        return (
            "| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes\n"
            "  from datamodel=Network_Traffic.All_Traffic\n"
            "  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h\n"
            "| sort -bytes"
        )

def tstats_dns(uc):
    n = uc.get('n', '').lower()
    if any(k in n for k in ['fail', 'nxdomain', 'error', 'refused', 'servfail']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Network_Resolution.DNS\n"
            "  where DNS.reply_code_id=3\n"
            "  by DNS.src DNS.query span=1h\n"
            "| sort -count"
        )
    elif any(k in n for k in ['tunnel', 'exfil', 'dga', 'suspicious', 'anomal']):
        return (
            "| tstats `summariesonly` count dc(DNS.query) as unique_queries\n"
            "  from datamodel=Network_Resolution.DNS\n"
            "  by DNS.src span=1h\n"
            "| where unique_queries > 500"
        )
    else:
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Network_Resolution.DNS\n"
            "  by DNS.src DNS.query DNS.record_type span=5m\n"
            "| sort -count"
        )

def tstats_web(uc):
    n = uc.get('n', '').lower()
    if any(k in n for k in ['error', '5xx', '4xx', '500', '404', 'server error']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Web.Web\n"
            "  where Web.status>=400\n"
            "  by Web.src Web.uri_path Web.status span=5m\n"
            "| sort -count"
        )
    elif any(k in n for k in ['latency', 'slow', 'response time', 'performance']):
        return (
            "| tstats `summariesonly` avg(Web.bytes) as avg_bytes count\n"
            "  from datamodel=Web.Web\n"
            "  by Web.uri_path Web.status span=5m\n"
            "| sort -avg_bytes"
        )
    elif any(k in n for k in ['top', 'traffic', 'request volume', 'throughput']):
        return (
            "| tstats `summariesonly` count sum(Web.bytes) as total_bytes\n"
            "  from datamodel=Web.Web\n"
            "  by Web.src Web.uri_path Web.status span=1h\n"
            "| sort -count"
        )
    else:
        return (
            "| tstats `summariesonly` count sum(Web.bytes) as total_bytes\n"
            "  from datamodel=Web.Web\n"
            "  by Web.src Web.dest Web.uri_path Web.status span=1h\n"
            "| sort -count"
        )

def tstats_ids(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Intrusion_Detection.IDS_Attacks\n"
        "  by IDS_Attacks.src IDS_Attacks.signature IDS_Attacks.severity span=1h\n"
        "| sort -count"
    )

def tstats_malware(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Malware.Malware_Attacks\n"
        "  by Malware_Attacks.dest Malware_Attacks.signature Malware_Attacks.action span=1h\n"
        "| sort -count"
    )

def tstats_endpoint_processes(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Endpoint.Processes\n"
        "  by Processes.dest Processes.process_name Processes.user span=1h\n"
        "| sort -count"
    )

def tstats_endpoint_services(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Endpoint.Services\n"
        "  by Services.dest Services.name Services.status span=5m\n"
        '| search Services.status!="running"'
    )

def tstats_vulnerabilities(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Vulnerabilities.Vulnerabilities\n"
        "  by Vulnerabilities.dest Vulnerabilities.severity Vulnerabilities.cve\n"
        '| search Vulnerabilities.severity IN ("critical","high")\n'
        "| sort -count"
    )

def tstats_change(uc):
    return (
        "| tstats `summariesonly` count\n"
        "  from datamodel=Change.All_Changes\n"
        "  by All_Changes.user All_Changes.object_category All_Changes.action span=1h\n"
        "| sort -count"
    )

def tstats_email(uc):
    n = uc.get('n', '').lower()
    if any(k in n for k in ['spam', 'phish', 'malicious', 'block', 'quarantine']):
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Email.All_Email\n"
            "  where All_Email.action=blocked\n"
            "  by All_Email.src_user All_Email.recipient All_Email.message_type span=1h\n"
            "| sort -count"
        )
    else:
        return (
            "| tstats `summariesonly` count\n"
            "  from datamodel=Email.All_Email\n"
            "  by All_Email.src_user All_Email.recipient All_Email.action span=1h\n"
            "| sort -count"
        )

def tstats_network_sessions(uc):
    return (
        "| tstats `summariesonly` count\n"
        "         sum(Network_Sessions.bytes_in) as bytes_in\n"
        "         sum(Network_Sessions.bytes_out) as bytes_out\n"
        "  from datamodel=Network_Sessions.All_Sessions\n"
        "  by All_Sessions.src All_Sessions.user All_Sessions.app span=1h\n"
        "| sort -count"
    )

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION LOGIC
# Returns (models, tstats_query)
#   models     : list[str]  e.g. ["Performance", "Authentication"]  OR  "N/A"
#   tstats_query: str | None
# ─────────────────────────────────────────────────────────────────────────────

def classify(uc, cat_i, sub_i):
    t = uc.get('t', '').lower()   # TA / app field
    d = uc.get('d', '').lower()   # data sources field
    n = uc.get('n', '').lower()   # use case name

    def has(*args, fields=(t, d)):
        return any(a in f for a in args for f in fields)

    def name_has(*args):
        return any(a in n for a in args)

    cat = int(cat_i)
    sub = str(sub_i)

    # ── CAT 1: Server & Compute ──────────────────────────────────────────────
    if cat == 1:
        if sub == '1.1':  # Linux
            if has('sourcetype=cpu'):
                return ['Performance'], tstats_perf_cpu(uc)
            elif has('sourcetype=vmstat') and name_has('memory', 'mem ', 'swap', 'oom', 'paging'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('sourcetype=vmstat') and name_has('load', 'uptime', 'availability'):
                return ['Performance'], tstats_perf_uptime(uc)
            elif has('sourcetype=vmstat'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('sourcetype=df') or (has('sourcetype=iostat') and name_has('disk', 'storage', 'filesystem', 'i/o', ' io ')):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('sourcetype=iostat'):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('sourcetype=interfaces') or (name_has('network', 'bandwidth', 'interface') and has('splunk_ta_nix')):
                return ['Performance'], tstats_perf_network(uc)
            elif has('sourcetype=linux_secure', 'linux_secure') or name_has('logon', 'login', 'ssh ', 'sudo', 'privilege', 'brute force', 'authentication', 'lockout', 'pam '):
                return ['Authentication'], tstats_auth(uc)
            elif has('sourcetype=syslog') and name_has('process', 'service', 'daemon', 'crash'):
                return ['Endpoint'], tstats_endpoint_processes(uc)
            elif has('lsof', 'netstat', 'ss -') and name_has('port', 'listening', 'socket', 'network connection'):
                return ['Endpoint'], tstats_endpoint_processes(uc)
            elif has('sourcetype=auditd') and name_has('file', 'change', 'modification', 'audit'):
                return ['Change'], tstats_change(uc)
            else:
                return 'N/A', None

        elif sub == '1.2':  # Windows
            if has('perfmon:cpu', 'perfmon:processor'):
                return ['Performance'], tstats_perf_cpu(uc)
            elif has('perfmon:memory', 'perfmon:available mbytes', 'perfmon:pages'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('perfmon:logicaldisk', 'perfmon:physicaldisk', 'perfmon:disk'):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('perfmon:network', 'perfmon:network interface'):
                return ['Performance'], tstats_perf_network(uc)
            elif has('perfmon:') and name_has('cpu', 'processor'):
                return ['Performance'], tstats_perf_cpu(uc)
            elif has('perfmon:') and name_has('memory', 'mem ', 'swap', 'page'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('perfmon:') and name_has('disk', 'storage', 'i/o'):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('perfmon:') and name_has('network', 'bandwidth', 'interface'):
                return ['Performance'], tstats_perf_network(uc)
            elif has('perfmon:'):
                return ['Performance'], tstats_perf_generic(uc)
            elif name_has('failed logon', 'failed login', 'logon failure', 'lockout', 'brute force', 'credential', 'kerberos', 'ntlm', 'rdp auth', 'pass-the') or \
                 (has('wineventlog:security') and name_has('logon', 'login', 'auth', 'password')):
                return ['Authentication'], tstats_auth(uc)
            elif has('winhostmon:service') or (has('wineventlog:system', 'wineventlog:application') and name_has('service', 'crash', 'stopped', 'failure')):
                return ['Endpoint'], tstats_endpoint_services(uc)
            elif has('winhostmon:process') or (has('wineventlog:security') and name_has('process', 'execution', 'task')):
                return ['Endpoint'], tstats_endpoint_processes(uc)
            elif has('wineventlog:security') and name_has('privilege', 'escalat', 'admin', 'elevation', 'uac', 'token'):
                return ['Authentication'], tstats_auth(uc)
            elif has('wineventlog:') and name_has('change', 'modification', 'policy', 'registry', 'configuration'):
                return ['Change'], tstats_change(uc)
            else:
                return 'N/A', None

        elif sub == '1.3':  # macOS — no standard CIM mapping for raw scripted inputs
            return 'N/A', None

        elif sub == '1.4':  # Bare Metal / Hardware — IPMI, SNMP sensors
            return 'N/A', None

        else:
            return 'N/A', None

    # ── CAT 2: Virtualization ────────────────────────────────────────────────
    elif cat == 2:
        if sub == '2.1':  # VMware vSphere
            if has('vmware:perf:cpu'):
                return ['Performance'], tstats_perf_cpu(uc)
            elif has('vmware:perf:mem'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('vmware:perf:disk', 'vmware:perf:storage', 'vmware:perf:datastore'):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('vmware:perf:net'):
                return ['Performance'], tstats_perf_network(uc)
            elif has('vmware:perf:') and name_has('cpu', 'processor', 'utilization') :
                return ['Performance'], tstats_perf_cpu(uc)
            elif has('vmware:perf:') and name_has('memory', 'mem', 'balloon', 'swap'):
                return ['Performance'], tstats_perf_memory(uc)
            elif has('vmware:perf:') and name_has('disk', 'datastore', 'storage', 'io', 'latency'):
                return ['Performance'], tstats_perf_storage(uc)
            elif has('vmware:perf:') and name_has('network', 'bandwidth', 'nic', 'interface'):
                return ['Performance'], tstats_perf_network(uc)
            else:
                return 'N/A', None

        elif sub == '2.2':  # Hyper-V
            if has('perfmon:hyperv', 'perfmon:hyper-v') or name_has('cpu', 'memory', 'disk', 'network', 'bandwidth', 'iops'):
                return ['Performance'], tstats_perf_generic(uc)
            else:
                return 'N/A', None

        else:  # 2.3 KVM / Proxmox / oVirt — custom scripted inputs, no CIM
            return 'N/A', None

    # ── CAT 3: Containers & Orchestration ───────────────────────────────────
    elif cat == 3:
        return 'N/A', None

    # ── CAT 4: Cloud Infrastructure ─────────────────────────────────────────
    elif cat == 4:
        if has('cloudtrail', 'azure:audit', 'azure:activity', 'mscs:azure:audit',
               'google:gcp:pubsub', 'gcp:audit'):
            return ['Change'], tstats_change(uc)
        elif name_has('api call', 'configuration change', 'policy change', 'permission',
                      'iam change', 'resource change', 'privilege', 'admin activity',
                      'unauthorized', 'root account'):
            return ['Change'], tstats_change(uc)
        else:
            return 'N/A', None

    # ── CAT 5: Network Infrastructure ───────────────────────────────────────
    elif cat == 5:
        if sub == '5.1':  # Routers & Switches
            if name_has('traffic', 'bandwidth', 'interface utilization', 'flow', 'throughput'):
                return ['Network_Traffic'], tstats_network_traffic(uc)
            elif name_has('acl', 'access list', 'permit', 'deny'):
                return ['Network_Traffic'], tstats_network_traffic(uc)
            else:
                return 'N/A', None

        elif sub == '5.2':  # Firewalls
            return ['Network_Traffic'], tstats_network_traffic(uc)

        elif sub == '5.3':  # Load Balancers & ADCs
            if name_has('http', 'web', 'request', 'response', 'uri', 'url', 'virtual server'):
                return ['Web'], tstats_web(uc)
            elif name_has('traffic', 'connection', 'pool', 'bandwidth', 'throughput'):
                return ['Network_Traffic'], tstats_network_traffic(uc)
            else:
                return 'N/A', None

        elif sub == '5.4':  # Wireless
            if name_has('auth', 'association', 'connect', 'deauth', 'disassociat'):
                return ['Authentication'], tstats_auth(uc)
            else:
                return 'N/A', None

        elif sub == '5.5':  # SD-WAN
            if name_has('traffic', 'bandwidth', 'throughput', 'tunnel', 'flow'):
                return ['Network_Traffic'], tstats_network_traffic(uc)
            else:
                return 'N/A', None

        elif sub == '5.6':  # DNS & DHCP
            if name_has('dns', 'resolution', 'query', 'domain', 'nxdomain', 'record', 'lookup'):
                return ['DNS'], tstats_dns(uc)
            else:
                return 'N/A', None

        elif sub == '5.7':  # Network Flow
            return ['Network_Traffic'], tstats_network_traffic(uc)

        elif sub == '5.8':  # DNA Center / Network Management
            return 'N/A', None

        elif sub == '5.9':  # Cisco Meraki
            if name_has('traffic', 'firewall', 'blocked', 'allow', 'security event', 'ids', 'ips'):
                return ['Network_Traffic'], tstats_network_traffic(uc)
            else:
                return 'N/A', None

        else:
            return 'N/A', None

    # ── CAT 6: Storage & Backup ──────────────────────────────────────────────
    elif cat == 6:
        if sub == '6.4' and has('wineventlog:security') and name_has('file access', 'object access', 'file audit'):
            return ['Change'], tstats_change(uc)
        else:
            return 'N/A', None

    # ── CAT 7: Database & Data Platforms ────────────────────────────────────
    elif cat == 7:
        if sub == '7.1':  # Relational DBs — CIM Databases model exists but limited tstats use
            if has('db connect', 'splunk_ta_microsoft-sqlserver') or \
               has('mssql', 'mysql', 'postgres', 'oracle', 'sql server', fields=(d,)):
                return ['Databases'], None  # tstats rarely used against Databases DM
        return 'N/A', None

    # ── CAT 8: Application Infrastructure ───────────────────────────────────
    elif cat == 8:
        if sub == '8.1':  # Web Servers & Reverse Proxies
            return ['Web'], tstats_web(uc)
        elif sub == '8.4':  # API Gateways
            if name_has('http', 'request', 'endpoint', 'api call', 'response', 'latency'):
                return ['Web'], tstats_web(uc)
            else:
                return 'N/A', None
        else:
            return 'N/A', None

    # ── CAT 9: Identity & Access Management ─────────────────────────────────
    elif cat == 9:
        return ['Authentication'], tstats_auth(uc)

    # ── CAT 10: Security Infrastructure ─────────────────────────────────────
    elif cat == 10:
        if sub == '10.1':  # NGFW (security-focused)
            if name_has('threat', 'intrusion', 'attack', 'detection', 'ids', 'ips', 'malware', 'exploit', 'vulnerability', 'c2', 'command and control'):
                return ['Network_Traffic', 'Intrusion_Detection'], tstats_ids(uc)
            else:
                return ['Network_Traffic'], tstats_network_traffic(uc)

        elif sub == '10.2':  # IDS/IPS
            return ['Intrusion_Detection'], tstats_ids(uc)

        elif sub == '10.3':  # EDR
            if name_has('malware', 'ransomware', 'virus', 'detection', 'threat', 'c2', 'beacon'):
                return ['Malware', 'Endpoint'], tstats_malware(uc)
            else:
                return ['Endpoint'], tstats_endpoint_processes(uc)

        elif sub == '10.4':  # Email Security
            return ['Email'], tstats_email(uc)

        elif sub == '10.5':  # Web Security / SWG
            if name_has('url', 'web', 'http', 'proxy', 'browsing'):
                return ['Web', 'Network_Traffic'], tstats_network_traffic(uc)
            else:
                return ['Network_Traffic'], tstats_network_traffic(uc)

        elif sub == '10.6':  # Vulnerability Management
            return ['Vulnerabilities'], tstats_vulnerabilities(uc)

        elif sub == '10.7':  # SIEM / SOAR
            return 'N/A', None

        elif sub == '10.8':  # PKI / Certificates
            return 'N/A', None

        else:
            return 'N/A', None

    # ── CAT 11: Email & Collaboration ───────────────────────────────────────
    elif cat == 11:
        if sub in ('11.1', '11.2'):
            if name_has('email', 'message', 'mail flow', 'spam', 'phish', 'delivery', 'queue', 'bounce'):
                return ['Email'], tstats_email(uc)
            else:
                return 'N/A', None
        else:  # 11.3 UC/VoIP
            return 'N/A', None

    # ── CAT 12: DevOps & CI/CD ───────────────────────────────────────────────
    elif cat == 12:
        return 'N/A', None

    # ── CAT 13: Observability & Monitoring Stack ─────────────────────────────
    elif cat == 13:
        return 'N/A', None

    # ── CAT 14: IoT & OT ────────────────────────────────────────────────────
    elif cat == 14:
        return 'N/A', None

    # ── CAT 15: Data Center Physical Infrastructure ──────────────────────────
    elif cat == 15:
        if sub == '15.3' and name_has('access', 'badge', 'entry', 'door', 'unauthoriz'):
            return ['Authentication'], tstats_auth(uc)
        else:
            return 'N/A', None

    # ── CAT 16: Service Management & ITSM ───────────────────────────────────
    elif cat == 16:
        return 'N/A', None

    # ── CAT 17: Network Security & Zero Trust ───────────────────────────────
    elif cat == 17:
        if sub == '17.1':  # NAC
            return ['Authentication', 'Network_Sessions'], tstats_auth(uc)
        elif sub == '17.2':  # VPN & Remote Access
            return ['Authentication', 'Network_Sessions'], tstats_network_sessions(uc)
        elif sub == '17.3':  # Zero Trust / SASE
            return ['Authentication', 'Network_Traffic'], tstats_auth(uc)
        else:
            return 'N/A', None

    # ── CAT 18: Data Center Fabric & SDN ────────────────────────────────────
    elif cat == 18:
        return 'N/A', None

    # ── CAT 19: HCI & Converged ──────────────────────────────────────────────
    elif cat == 19:
        return 'N/A', None

    # ── CAT 20: Cost & Capacity ──────────────────────────────────────────────
    elif cat == 20:
        return 'N/A', None

    else:
        return 'N/A', None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def load_html():
    with open(HTML_PATH, encoding='utf-8') as f:
        return f.read()

def extract_data(html):
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('const DATA'):
            json_str = line[len('const DATA = '):]
            if json_str.endswith(';'):
                json_str = json_str[:-1]
            return json.loads(json_str), i
    raise ValueError("const DATA not found in HTML")

def write_html(html, data, data_line_idx):
    lines = html.split('\n')
    lines[data_line_idx] = 'const DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    print("Loading HTML...", flush=True)
    html = load_html()
    data, data_line_idx = extract_data(html)

    total_uc = sum(len(sub['u']) for cat in data for sub in cat['s'])
    print(f"Found {len(data)} categories, {total_uc} use cases\n", flush=True)

    processed = 0
    cim_count = 0
    na_count = 0
    pending_write = []

    for cat in data:
        cat_i = cat['i']
        for sub in cat['s']:
            sub_i = sub['i']
            for uc in sub['u']:
                models, tstats_q = classify(uc, cat_i, sub_i)

                uc['a'] = models
                if tstats_q:
                    uc['qs'] = tstats_q
                elif 'qs' in uc:
                    del uc['qs']  # remove stale field if re-running

                if models == 'N/A':
                    na_count += 1
                else:
                    cim_count += 1

                processed += 1
                pending_write.append(uc['i'])

                if len(pending_write) >= 5:
                    write_html(html, data, data_line_idx)
                    pct = processed / total_uc * 100
                    last5 = ', '.join(pending_write)
                    has_tstats = sum(1 for u in pending_write if True)  # written above
                    print(f"  [{processed:4d}/{total_uc}] {pct:5.1f}%  wrote UC {last5}", flush=True)
                    pending_write = []

    # Write any remaining
    if pending_write:
        write_html(html, data, data_line_idx)
        print(f"  [{processed:4d}/{total_uc}] 100.0%  wrote UC {', '.join(pending_write)}", flush=True)

    print(f"\n✓ Done.", flush=True)
    print(f"  CIM-mapped : {cim_count} ({cim_count/total_uc*100:.1f}%)", flush=True)
    print(f"  N/A        : {na_count} ({na_count/total_uc*100:.1f}%)", flush=True)
    print(f"  tstats added: {sum(1 for cat in data for sub in cat['s'] for uc in sub['u'] if uc.get('qs'))}", flush=True)

if __name__ == '__main__':
    main()
