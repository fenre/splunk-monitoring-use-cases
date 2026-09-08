#!/usr/bin/env python3
"""One-shot patch for EQUIPMENT registry: kind, vendor, new entries, aliases."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
_ENRICHMENT = _REPO / "tools/build/enrichment.py"

_VENDORS: dict[str, str] = {
    "linux": "Open Source / Community",
    "windows": "Microsoft",
    "macos": "Apple",
    "vmware": "VMware",
    "hyperv": "Microsoft",
    "proxmox": "Proxmox",
    "ovirt": "Red Hat",
    "openstack": "OpenInfra Foundation",
    "nutanix": "Nutanix",
    "vxrail": "Dell / VMware",
    "aws": "Amazon",
    "azure": "Microsoft",
    "gcp": "Google",
    "oci": "Oracle",
    "alibaba": "Alibaba",
    "kubernetes": "CNCF",
    "docker": "Docker",
    "argocd": "CNCF",
    "cisco": "Cisco",
    "paloalto": "Palo Alto Networks",
    "fortinet": "Fortinet",
    "f5": "F5",
    "citrix": "Citrix",
    "checkpoint": "Check Point",
    "nsx": "VMware",
    "infoblox": "Infoblox",
    "netflow": "IETF / Multi-vendor",
    "snmp": "IETF / Multi-vendor",
    "syslog": "IETF / Multi-vendor",
    "zscaler": "Zscaler",
    "netskope": "Netskope",
    "cloudflare": "Cloudflare",
    "guardicore": "Akamai",
    "broadcom_symantec": "Broadcom",
    "forcepoint": "Forcepoint",
    "sonicwall": "SonicWall",
    "apache": "Apache Software Foundation",
    "nginx": "F5",
    "iis": "Microsoft",
    "haproxy": "HAProxy Technologies",
    "traefik": "Traefik Labs",
    "tomcat": "Apache Software Foundation",
    "jboss": "Red Hat",
    "phpfpm": "PHP Group",
    "varnish": "Varnish Software",
    "squid": "Squid Project",
    "memcached": "Memcached",
    "envoy": "CNCF",
    "db_connect": "Splunk",
    "mssql": "Microsoft",
    "oracle": "Oracle",
    "postgresql": "PostgreSQL Global Development Group",
    "mysql": "Oracle",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elastic",
    "clickhouse": "ClickHouse",
    "cassandra": "Apache Software Foundation",
    "snowflake": "Snowflake",
    "kafka": "Apache Software Foundation",
    "rabbitmq": "Broadcom",
    "activemq": "Apache Software Foundation",
    "zookeeper": "Apache Software Foundation",
    "hashicorp": "HashiCorp",
    "netapp": "NetApp",
    "pure_storage": "Pure Storage",
    "dell_emc": "Dell",
    "truenas": "iXsystems",
    "ceph": "Red Hat",
    "veeam": "Veeam",
    "commvault": "Commvault",
    "okta": "Okta",
    "cyberark": "CyberArk",
    "beyondtrust": "BeyondTrust",
    "cert_pki": "Multi-vendor",
    "m365": "Microsoft",
    "exchange": "Microsoft",
    "sharepoint": "Microsoft",
    "security_essentials": "Splunk",
    "crowdstrike": "CrowdStrike",
    "defender": "Microsoft",
    "tenable": "Tenable",
    "qualys": "Qualys",
    "proofpoint": "Proofpoint",
    "suricata": "OISF",
    "jenkins": "Jenkins Project",
    "github": "GitHub",
    "gitlab": "GitLab",
    "ansible": "Red Hat",
    "controlm": "BMC",
    "itsi": "Splunk",
    "stream": "Splunk",
    "opentelemetry": "CNCF",
    "prometheus": "CNCF",
    "grafana": "Grafana Labs",
    "log_pipeline": "CNCF",
    "servicenow": "ServiceNow",
    "jira": "Atlassian",
    "pagerduty": "PagerDuty",
    "edge_hub": "Splunk",
    "modbus": "Multi-vendor OT",
    "opcua": "OPC Foundation",
    "mqtt": "OASIS",
    "aranet": "Aranet",
    "asterisk": "Digium / Sangoma",
    "hardware_bmc": "Multi-vendor",
    "apc_dc": "Schneider Electric",
    "cctv": "Multi-vendor",
    "cisco_duo": "Cisco",
    "cisco_umbrella": "Cisco",
    "cisco_secure_endpoint": "Cisco",
    "cisco_secure_access": "Cisco",
    "cisco_email_security": "Cisco",
    "cisco_web_security": "Cisco",
    "cisco_secure_network_analytics": "Cisco",
    "cisco_xdr": "Cisco",
    "cisco_appdynamics": "Cisco",
    "cisco_cyber_vision": "Cisco",
    "cisco_edge_intelligence": "Cisco",
    "cisco_ind": "Cisco",
    "siemens": "Siemens",
    "rockwell": "Rockwell Automation",
    "schneider": "Schneider Electric",
    "abb": "ABB",
    "honeywell": "Honeywell",
    "emerson": "Emerson",
    "ge_vernova": "GE Vernova",
    "yokogawa": "Yokogawa",
    "aveva": "AVEVA",
    "fanuc": "FANUC",
    "kuka": "KUKA",
    "beckhoff": "Beckhoff",
    "phoenix_contact": "Phoenix Contact",
    "wago": "WAGO",
    "copa_data": "COPA-DATA",
    "ignition": "Inductive Automation",
    "vtscada": "Trihedral",
    "tridium": "Tridium",
    "jci_metasys": "Johnson Controls",
    "ibm_maximo": "IBM",
    "sap_pm": "SAP",
    "scada_hmi": "Multi-vendor OT",
    "dcs": "Multi-vendor OT",
    "historian": "Multi-vendor OT",
    "mes": "Multi-vendor OT",
    "plc_rtu": "Multi-vendor OT",
    "safety_system": "Multi-vendor OT",
    "energy_meter": "Multi-vendor OT",
    "vibration_sensor": "Multi-vendor OT",
    "bacnet_devices": "ASHRAE / Multi-vendor",
    "dnp3": "IEEE / Multi-vendor",
    "iec104": "IEC",
    "iec61850": "IEC",
    "profinet": "PROFIBUS & PROFINET International",
    "ethernetip": "ODVA",
    "ethercat": "EtherCAT Technology Group",
    "s7comm": "Siemens",
    "mtconnect": "MTConnect Institute",
    "profibus": "PROFIBUS & PROFINET International",
    "hart": "FieldComm Group",
    "knx": "KNX Association",
    "lorawan": "LoRa Alliance",
    "zigbee": "Connectivity Standards Alliance",
    "coap": "IETF",
    "claroty": "Claroty",
    "dragos": "Dragos",
    "nozomi": "Nozomi Networks",
    "splunk": "Splunk",
    "splunk_es": "Splunk",
    "splunk_soar": "Splunk",
    "juniper": "Juniper Networks",
    "arista": "Arista Networks",
    "zeek": "Zeek Project",
    "pos": "Multi-vendor Retail",
    "scada": "Multi-vendor OT",
    "fiveg": "Telecommunications",
    "smartgrid": "Utilities",
    "ehr": "Healthcare IT",
    "oilgas": "Energy",
    "pipeline": "Energy",
    "fleet": "Transportation",
    "water": "Utilities",
    "claims": "Insurance",
    "contact_center": "Communications",
    "cx": "Communications",
    "microsoft": "Microsoft",
    "claroty": "Claroty",
    "dragos": "Dragos",
    "nozomi": "Nozomi Networks",
    "openshift": "Red Hat",
    "aruba": "HPE",
    "sap": "SAP",
    "salesforce": "Salesforce",
    "campus": "Multi-vendor",
}

_SPLUNK_PLATFORM_IDS = frozenset(
    {"splunk", "splunk_es", "splunk_soar", "itsi", "stream", "security_essentials", "edge_hub", "db_connect"}
)

_NEW_ENTRIES: list[dict[str, Any]] = [
    {"id": "splunk", "label": "Splunk Platform", "kind": "splunk-platform", "vendor": "Splunk", "tas": []},
    {
        "id": "splunk_es",
        "label": "Splunk Enterprise Security",
        "kind": "splunk-platform",
        "vendor": "Splunk",
        "tas": ["Splunk Enterprise Security", "Splunk ES", "splunk-es", "splunk_es"],
    },
    {
        "id": "splunk_soar",
        "label": "Splunk SOAR",
        "kind": "splunk-platform",
        "vendor": "Splunk",
        "tas": ["Splunk SOAR", "Splunk Phantom", "splunk-soar", "splunk_soar"],
    },
    {
        "id": "juniper",
        "label": "Juniper Networks",
        "kind": "equipment",
        "vendor": "Juniper Networks",
        "tas": ["Splunk_TA_juniper", "Juniper", "Junos", "Juniper SRX", "Juniper MX"],
    },
    {
        "id": "arista",
        "label": "Arista Networks",
        "kind": "equipment",
        "vendor": "Arista Networks",
        "tas": ["Arista", "Arista EOS", "CloudVision", "Splunk_TA_arista"],
    },
    {
        "id": "zeek",
        "label": "Zeek (Bro IDS)",
        "kind": "equipment",
        "vendor": "Zeek Project",
        "tas": ["Zeek", "Splunk_TA_bro", "Bro IDS", "bro:conn"],
    },
    {
        "id": "pos",
        "label": "Point of Sale (POS)",
        "kind": "equipment",
        "vendor": "Multi-vendor Retail",
        "tas": ["point of sale", "point-of-sale", "POS terminal", "POS system"],
    },
    {
        "id": "scada",
        "label": "SCADA Systems",
        "kind": "equipment",
        "vendor": "Multi-vendor OT",
        "tas": ["SCADA system", "SCADA platform", "SCADA server"],
    },
    {
        "id": "fiveg",
        "label": "5G Mobile Networks",
        "kind": "equipment",
        "vendor": "Telecommunications",
        "tas": ["5G core", "5G network", "5G RAN", "5G SA", "NR RAN"],
    },
    {
        "id": "smartgrid",
        "label": "Smart Grid",
        "kind": "equipment",
        "vendor": "Utilities",
        "tas": ["smart grid", "smartgrid", "AMI meter", "smart meter"],
    },
    {
        "id": "ehr",
        "label": "Electronic Health Records (EHR)",
        "kind": "equipment",
        "vendor": "Healthcare IT",
        "tas": ["electronic health record", "EHR system", "Epic EHR", "Cerner EHR"],
    },
    {
        "id": "oilgas",
        "label": "Oil & Gas Operations",
        "kind": "equipment",
        "vendor": "Energy",
        "tas": ["oil and gas", "oil & gas", "upstream oil", "downstream oil"],
    },
    {
        "id": "pipeline",
        "label": "Pipeline Operations",
        "kind": "equipment",
        "vendor": "Energy",
        "tas": ["pipeline operations", "pipeline SCADA", "pipeline monitoring"],
    },
    {
        "id": "fleet",
        "label": "Fleet Management",
        "kind": "equipment",
        "vendor": "Transportation",
        "tas": ["fleet management", "fleet telematics", "vehicle tracking"],
    },
    {
        "id": "water",
        "label": "Water Utilities",
        "kind": "equipment",
        "vendor": "Utilities",
        "tas": ["water utility", "water treatment plant", "SCADA water"],
    },
    {
        "id": "claims",
        "label": "Insurance Claims Systems",
        "kind": "equipment",
        "vendor": "Insurance",
        "tas": ["insurance claims", "claims processing", "claims system"],
    },
    {
        "id": "contact_center",
        "label": "Contact Center Platforms",
        "kind": "equipment",
        "vendor": "Communications",
        "tas": ["contact center platform", "call center platform"],
    },
    {
        "id": "cx",
        "label": "Customer Experience Platforms",
        "kind": "equipment",
        "vendor": "Communications",
        "tas": ["customer experience platform", "CX platform"],
    },
    {
        "id": "microsoft",
        "label": "Microsoft Platform",
        "kind": "equipment",
        "vendor": "Microsoft",
        "tas": ["Microsoft platform", "Microsoft infrastructure", "Microsoft server"],
    },
    {
        "id": "claroty",
        "label": "Claroty",
        "kind": "equipment",
        "vendor": "Claroty",
        "tas": ["Claroty", "Claroty XDome", "claroty"],
    },
    {
        "id": "dragos",
        "label": "Dragos",
        "kind": "equipment",
        "vendor": "Dragos",
        "tas": ["Dragos Platform", "Dragos", "dragos"],
    },
    {
        "id": "nozomi",
        "label": "Nozomi Networks",
        "kind": "equipment",
        "vendor": "Nozomi Networks",
        "tas": ["Nozomi Networks", "Nozomi Guardian", "nozomi"],
    },
    {
        "id": "openshift",
        "label": "Red Hat OpenShift",
        "kind": "equipment",
        "vendor": "Red Hat",
        "tas": ["OpenShift", "openshift", "OCP cluster"],
    },
    {
        "id": "aruba",
        "label": "HPE Aruba",
        "kind": "equipment",
        "vendor": "HPE",
        "tas": ["Aruba", "HPE Aruba", "ArubaOS"],
    },
    {
        "id": "sap",
        "label": "SAP",
        "kind": "equipment",
        "vendor": "SAP",
        "tas": ["SAP ERP", "SAP HANA", "SAP NetWeaver"],
    },
    {
        "id": "salesforce",
        "label": "Salesforce",
        "kind": "equipment",
        "vendor": "Salesforce",
        "tas": ["Salesforce", "Sales Cloud", "Service Cloud"],
    },
    {
        "id": "campus",
        "label": "Campus Networking",
        "kind": "equipment",
        "vendor": "Multi-vendor",
        "tas": ["campus network", "campus switching", "campus LAN"],
    },
]


def _load_equipment_list(source: str) -> list[dict[str, Any]]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "EQUIPMENT":
                    value = ast.literal_eval(node.value)
                    if isinstance(value, list):
                        return value
    raise RuntimeError("EQUIPMENT list not found")


def patch_registry(equipment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_ids = {e["id"] for e in equipment}
    out: list[dict[str, Any]] = []
    for entry in equipment:
        eid = entry["id"]
        patched = dict(entry)
        patched["kind"] = "splunk-platform" if eid in _SPLUNK_PLATFORM_IDS else "equipment"
        patched["vendor"] = _VENDORS.get(eid) or patched.get("label", eid).split(" / ")[0].split(" (")[0]
        if eid == "paloalto":
            tas = list(patched.get("tas", []))
            for extra in ("palo_alto", "palo-alto", "paloaltonetworks", "Palo Alto Networks"):
                if extra not in tas:
                    tas.append(extra)
            patched["tas"] = tas
        if eid == "cisco":
            models = list(patched.get("models") or [])
            if "cyber_vision" not in {m["id"] for m in models}:
                models.append(
                    {
                        "id": "cyber_vision",
                        "label": "Cisco Cyber Vision",
                        "tas": [
                            "Cisco Cyber Vision",
                            "cisco-cybervision",
                            "cisco-cyber-vision",
                            "cisco_cyber_vision",
                        ],
                    }
                )
            patched["models"] = models
        if eid == "itsi":
            tas = list(patched.get("tas", []))
            for extra in ("splunk itsi", "Splunk ITSI", "splunk-itsi"):
                if extra not in tas:
                    tas.append(extra)
            patched["tas"] = tas
        if eid == "stream":
            tas = list(patched.get("tas", []))
            for extra in ("splunk stream", "splunk-stream"):
                if extra not in tas:
                    tas.append(extra)
            patched["tas"] = tas
        out.append(patched)
    for entry in _NEW_ENTRIES:
        if entry["id"] not in existing_ids:
            out.append(dict(entry))
    return out


def write_enrichment(equipment: list[dict[str, Any]]) -> None:
    source = _ENRICHMENT.read_text(encoding="utf-8")
    start = source.index("EQUIPMENT = [")
    end = source.index("\n]", start) + 2
    body = json.dumps(equipment, indent=4, ensure_ascii=False)
    _ENRICHMENT.write_text(source[:start] + f"EQUIPMENT = {body}\n" + source[end:], encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    source = _ENRICHMENT.read_text(encoding="utf-8")
    equipment = _load_equipment_list(source)
    patched = patch_registry(equipment)
    print(f"Entries: {len(equipment)} -> {len(patched)}")
    if args.write:
        write_enrichment(patched)
        print(f"Wrote {_ENRICHMENT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
