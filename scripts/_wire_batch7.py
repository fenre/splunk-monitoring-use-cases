#!/usr/bin/env python3
"""Batch 7 wiring helper — links every existing gold-standard guide
into the catalogue's _category.json subcategory metadata and generates
the matching docs-uc-map.js entries.

Idempotent: re-running preserves existing `guide` fields that point at
the same target and only updates missing ones. Skips the file if a
different guide is already wired (so curated overrides never get lost).

Run from repo root:
    python3 scripts/_wire_batch7.py
"""
from __future__ import annotations
import json
from pathlib import Path

# Maps every gold-standard guide to the subcategories it owns.
# Existing per-guide `use_case_subcategory` frontmatter is the source.
# When more than one guide could plausibly own a subcategory, the more
# specific guide wins (cisco-ise vs vpn-zerotrust-sase on 17.1 →
# cisco-ise wins because it is the targeted NAC guide).
GUIDE_TO_SUBS: dict[str, list[str]] = {
    "docs/guides/active-directory-entra-id.md": ["9.1"],
    "docs/guides/api-gateways.md": ["8.4"],
    "docs/guides/application-servers.md": ["8.2"],
    "docs/guides/aws.md": ["4.1"],
    "docs/guides/azure.md": ["4.2"],
    "docs/guides/catalyst-center.md": ["5.13"],
    "docs/guides/cert-pki.md": ["10.8"],
    "docs/guides/cisco-networks.md": ["5.1"],
    "docs/guides/cisco-thousandeyes.md": ["5.9"],
    "docs/guides/compute-hci.md": ["19.1", "19.2", "19.3"],
    "docs/guides/datacenter-physical.md": ["15.1", "15.2", "15.3"],
    "docs/guides/devops-cicd.md": ["12.1", "12.2", "12.3", "12.4", "12.5", "12.6"],
    "docs/guides/dns-dhcp.md": ["5.6"],
    "docs/guides/edr.md": ["10.3"],
    "docs/guides/email-collaboration.md": ["11.1", "11.2", "11.3", "11.4", "11.5"],
    "docs/guides/email-security.md": ["10.4"],
    "docs/guides/f5-bigip.md": ["5.3"],
    "docs/guides/firewalls.md": ["5.2"],
    "docs/guides/gcp.md": ["4.3"],
    "docs/guides/ids-ips.md": ["10.2"],
    "docs/guides/industry-verticals.md": [
        "21.1", "21.2", "21.3", "21.4", "21.5",
        "21.6", "21.7", "21.8", "21.9", "21.10",
    ],
    "docs/guides/iot-ot.md": [
        "14.1", "14.2", "14.3", "14.4", "14.5",
        "14.6", "14.7", "14.8", "14.9",
    ],
    "docs/guides/kubernetes.md": ["3.2"],
    "docs/guides/linux-servers.md": ["1.1"],
    "docs/guides/message-queues.md": ["8.3"],
    "docs/guides/network-flow.md": ["5.7"],
    "docs/guides/ngfw-security.md": ["10.1"],
    "docs/guides/nosql-cloud-databases.md": ["7.2", "7.3", "7.4", "7.5"],
    "docs/guides/relational-databases.md": ["7.1"],
    "docs/guides/service-management-itsm.md": [
        "16.1", "16.2", "16.3", "16.4", "16.5",
    ],
    "docs/guides/siem-soar.md": ["10.7"],
    "docs/guides/splunk-itsi.md": ["13.2"],
    "docs/guides/splunk-platform-health.md": ["13.1"],
    "docs/guides/storage-backup.md": ["6.1", "6.2", "6.3", "6.4"],
    "docs/guides/vmware-vsphere.md": ["2.1"],
    "docs/guides/vpn-zerotrust-sase.md": ["17.2", "17.3"],
    "docs/guides/vulnerability-management.md": ["10.6"],
    "docs/guides/web-security.md": ["10.5"],
    "docs/guides/web-servers.md": ["8.1"],
    "docs/guides/windows-servers.md": ["1.2"],
    "docs/guides/wireless-infrastructure.md": ["5.4"],
}

# Friendly titles consumed by docs-uc-map.js (mirror existing entries).
GUIDE_TITLES: dict[str, str] = {
    "docs/guides/active-directory-entra-id.md": "Active Directory & Entra ID Integration Guide",
    "docs/guides/api-gateways.md": "API Gateways & Service Mesh Integration Guide",
    "docs/guides/application-servers.md": "Application Servers Integration Guide",
    "docs/guides/aws.md": "Amazon Web Services (AWS) Integration Guide",
    "docs/guides/azure.md": "Microsoft Azure Integration Guide",
    "docs/guides/catalyst-center.md": "Cisco Catalyst Center Integration Guide",
    "docs/guides/cert-pki.md": "Certificate & PKI Lifecycle Integration Guide",
    "docs/guides/cisco-networks.md": "Cisco Network Switches & Routers Integration Guide",
    "docs/guides/cisco-thousandeyes.md": "Cisco ThousandEyes Integration Guide",
    "docs/guides/compute-hci.md": "Compute Infrastructure & Hyper-Converged (HCI) Integration Guide",
    "docs/guides/datacenter-physical.md": "Data Center Physical Infrastructure (DCIM, Power, Cooling) Integration Guide",
    "docs/guides/devops-cicd.md": "DevOps & CI/CD Pipeline Integration Guide",
    "docs/guides/dns-dhcp.md": "DNS & DHCP Integration Guide",
    "docs/guides/edr.md": "Endpoint Detection & Response (EDR / XDR) Integration Guide",
    "docs/guides/email-collaboration.md": "Email & Collaboration Platforms Integration Guide",
    "docs/guides/email-security.md": "Email Security (SEG / Anti-Phishing) Integration Guide",
    "docs/guides/f5-bigip.md": "F5 BIG-IP Integration Guide",
    "docs/guides/firewalls.md": "Network Firewalls Integration Guide",
    "docs/guides/gcp.md": "Google Cloud Platform (GCP) Integration Guide",
    "docs/guides/ids-ips.md": "IDS / IPS / Network Detection & Response (NDR) Integration Guide",
    "docs/guides/industry-verticals.md": "Industry Verticals Integration Guide",
    "docs/guides/iot-ot.md": "IoT / Operational Technology (OT) Integration Guide",
    "docs/guides/kubernetes.md": "Kubernetes & Container Orchestration Integration Guide",
    "docs/guides/linux-servers.md": "Linux Servers Integration Guide",
    "docs/guides/message-queues.md": "Message Queues & Event Streaming Integration Guide",
    "docs/guides/network-flow.md": "NetFlow / sFlow / IPFIX Integration Guide",
    "docs/guides/ngfw-security.md": "Next-Generation Firewall (NGFW) Security Integration Guide",
    "docs/guides/nosql-cloud-databases.md": "NoSQL & Cloud-Native Databases Integration Guide",
    "docs/guides/relational-databases.md": "Relational Databases Integration Guide",
    "docs/guides/service-management-itsm.md": "Service Management & ITSM Integration Guide",
    "docs/guides/siem-soar.md": "SIEM / SOAR Platforms Integration Guide",
    "docs/guides/splunk-itsi.md": "Splunk IT Service Intelligence (ITSI) Integration Guide",
    "docs/guides/splunk-platform-health.md": "Splunk Platform Health Integration Guide",
    "docs/guides/storage-backup.md": "Storage & Backup Infrastructure Integration Guide",
    "docs/guides/vmware-vsphere.md": "VMware vSphere Integration Guide",
    "docs/guides/vpn-zerotrust-sase.md": "VPN, Zero Trust & SASE Integration Guide",
    "docs/guides/vulnerability-management.md": "Vulnerability Management Integration Guide",
    "docs/guides/web-security.md": "Web Security & Secure Web Gateway Integration Guide",
    "docs/guides/web-servers.md": "Web Servers Integration Guide",
    "docs/guides/windows-servers.md": "Windows Servers Integration Guide",
    "docs/guides/wireless-infrastructure.md": "Wireless Infrastructure Integration Guide",
}


def _existing_docs_uc_map_paths() -> set[str]:
    """Parse docs-uc-map.js for currently-registered doc paths."""
    import re

    text = Path("docs-uc-map.js").read_text()
    return set(re.findall(r'^  "(docs/[^"]+\.md)":', text, re.M))


def _category_dir_for(sub_id: str) -> Path | None:
    """Resolve content/cat-NN-* directory from the leading category id."""
    cat_num = sub_id.split(".", 1)[0]
    matches = list(Path("content").glob(f"cat-{int(cat_num):02d}-*"))
    return matches[0] if matches else None


def _list_uc_ids_for(sub_id: str) -> list[str]:
    cat_dir = _category_dir_for(sub_id)
    if cat_dir is None:
        return []
    out: list[str] = []
    for p in sorted(cat_dir.glob(f"UC-{sub_id}.[0-9]*.json")):
        # Match exactly UC-X.Y.Z.json (numeric Z), not UC-X.YY.*
        stem = p.stem  # e.g. UC-1.1.10
        parts = stem[3:].split(".")
        if len(parts) == 3 and parts[0:2] == sub_id.split(".") and parts[2].isdigit():
            out.append(stem[3:])
    out.sort(key=lambda s: tuple(int(x) if x.isdigit() else x for x in s.split(".")))
    return out


def _wire_category_metadata() -> tuple[int, int]:
    """Add `guide:` to every targeted subcategory in _category.json files.

    Returns (subs_modified, files_written).
    """
    target_by_cat: dict[Path, dict[str, str]] = {}
    for guide, subs in GUIDE_TO_SUBS.items():
        for sub_id in subs:
            cat_dir = _category_dir_for(sub_id)
            if cat_dir is None:
                continue
            target_by_cat.setdefault(cat_dir, {})[sub_id] = guide

    subs_modified = 0
    files_written = 0
    for cat_dir, sub_to_guide in target_by_cat.items():
        meta_path = cat_dir / "_category.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        changed = False
        for sub in meta.get("subcategories", []):
            sid = sub.get("id")
            if sid in sub_to_guide:
                desired = sub_to_guide[sid]
                if sub.get("guide") != desired:
                    # Only set if not already pointing at a different guide.
                    # (We let the per-guide `GUIDE_TO_SUBS` table arbitrate
                    # so curated 22.* compliance-master mappings survive.)
                    if "guide" not in sub:
                        # Insert `guide` after `useCaseCount` for a clean
                        # diff that mirrors the existing layout.
                        new_sub: dict = {}
                        for k, v in sub.items():
                            new_sub[k] = v
                            if k == "useCaseCount":
                                new_sub["guide"] = desired
                        if "guide" not in new_sub:
                            new_sub["guide"] = desired
                        sub.clear()
                        sub.update(new_sub)
                        changed = True
                        subs_modified += 1
        if changed:
            meta_path.write_text(json.dumps(meta, indent=2) + "\n")
            files_written += 1
    return subs_modified, files_written


def _emit_docs_uc_map_entries(only_missing: bool = True) -> str:
    """Generate the JS snippet to splice into docs-uc-map.js.

    When ``only_missing`` is True (the default and what we actually use),
    skip any guide that already has a curated entry in docs-uc-map.js.
    The pre-existing curated entries (e.g. ``industry-verticals.md``)
    intentionally show a hand-picked subset and we don't want to clobber
    that hand curation.
    """
    existing = _existing_docs_uc_map_paths() if only_missing else set()

    lines: list[str] = []
    for guide in sorted(GUIDE_TO_SUBS):
        if guide in existing:
            continue
        subs = GUIDE_TO_SUBS[guide]
        ucs: list[str] = []
        for sub_id in subs:
            ucs.extend(_list_uc_ids_for(sub_id))
        if not ucs:
            continue
        title = GUIDE_TITLES[guide].replace('"', '\\"')
        # Format UC list with chunked rows for readability.
        uc_lines = []
        chunk = 7
        for i in range(0, len(ucs), chunk):
            piece = ", ".join(f'"{u}"' for u in ucs[i:i + chunk])
            uc_lines.append("      " + piece)
        uc_block = ",\n".join(uc_lines)
        lines.append(
            f'  "{guide}": {{\n'
            f'    title: "{title}",\n'
            f'    ucs: [\n{uc_block}\n    ]\n'
            f'  }},'
        )
    return "\n".join(lines)


if __name__ == "__main__":
    subs_modified, files_written = _wire_category_metadata()
    print(f"_category.json: {subs_modified} subcategories wired across {files_written} files")
    print()
    print("--- docs-uc-map.js entries (splice into integration guides section) ---")
    print()
    print(_emit_docs_uc_map_entries())
