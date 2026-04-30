#!/usr/bin/env python3
"""
DEPRECATED — sync_json_to_markdown.py

This script synced JSON sidecars from content/ to use-cases/*.md for the
legacy v6 build pipeline. The v6 pipeline has been deprecated — the v7
build reads directly from content/cat-*/UC-*.json.

This script should not be run. It is preserved for historical reference only.
"""

import sys


def main():
    print(
        "DEPRECATED: sync_json_to_markdown.py is no longer needed.\n"
        "The v7 build reads directly from content/cat-*/UC-*.json.\n"
        "The legacy use-cases/*.md files are not the source of truth.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

# --- Original code below preserved for reference ---

import json
import os
import re
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(ROOT_DIR, "content")
UC_DIR = os.path.join(ROOT_DIR, "use-cases")

CRITICALITY_EMOJI = {
    "critical": "🔴 Critical",
    "high": "🟠 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}

DIFFICULTY_EMOJI = {
    "beginner": "🟢 Beginner",
    "intermediate": "🔵 Intermediate",
    "advanced": "🟠 Advanced",
    "expert": "🔴 Expert",
}

WAVE_EMOJI = {
    "crawl": "🐢 crawl",
    "walk": "🚶 walk",
    "run": "🏃 run",
}


def find_md_file_for_cat(cat_num):
    """Find the markdown file for a given category number."""
    for fname in os.listdir(UC_DIR):
        if fname.startswith(f"cat-{cat_num:02d}-") and fname.endswith(".md"):
            return os.path.join(UC_DIR, fname)
    return None


def extract_md_uc_ids(filepath):
    """Extract all UC IDs present in a markdown file."""
    ids = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*", line)
            if m:
                ids.add(m.group(1))
    return ids


def extract_md_subcategories(filepath):
    """Extract subcategory headings and their line numbers from a markdown file."""
    subs = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        m = re.match(r"^#{2,3}\s+(\d+\.\d+)\s+(.+)$", line.strip())
        if m:
            subs.append({
                "id": m.group(1),
                "name": m.group(2).strip(),
                "line": i,
            })
    return subs, lines


def json_to_markdown(uc_data):
    """Convert a UC JSON sidecar to a markdown entry."""
    uc_id = uc_data["id"]
    title = uc_data.get("title", "Untitled")
    lines = []

    lines.append(f"### UC-{uc_id} · {title}")

    crit = uc_data.get("criticality", "")
    if crit:
        lines.append(f"- **Criticality:** {CRITICALITY_EMOJI.get(crit, crit)}")

    diff = uc_data.get("difficulty", "")
    if diff:
        lines.append(f"- **Difficulty:** {DIFFICULTY_EMOJI.get(diff, diff)}")

    wave = uc_data.get("wave", "")
    if wave:
        lines.append(f"- **Wave:** {WAVE_EMOJI.get(wave, wave)}")

    prereqs = uc_data.get("prerequisiteUseCases", [])
    if prereqs:
        lines.append(f"- **Prerequisite UCs:** {', '.join(prereqs)}")

    mtypes = uc_data.get("monitoringType", [])
    if mtypes:
        lines.append(f"- **Monitoring type:** {', '.join(mtypes)}")

    desc = uc_data.get("description", "")
    value = uc_data.get("value", desc)
    if value:
        lines.append(f"- **Value:** {value}")

    app = uc_data.get("app", "")
    if app:
        lines.append(f"- **App/TA:** {app}")

    premium = uc_data.get("premiumApps", [])
    if premium:
        plist = []
        for p in premium:
            if isinstance(p, str):
                plist.append(p)
            elif isinstance(p, dict):
                dn = p.get("displayName", p.get("name", ""))
                note = p.get("note", "")
                if note:
                    plist.append(f"{dn} ({note})")
                else:
                    plist.append(dn)
        if plist:
            lines.append(f"- **Premium Apps:** {', '.join(plist)}")

    ds = uc_data.get("dataSources", "")
    if ds:
        lines.append(f"- **Data Sources:** {ds}")

    pillar = uc_data.get("splunkPillar", "")
    if pillar:
        lines.append(f"- **Splunk Pillar:** {pillar}")

    industry = uc_data.get("industry", "")
    if industry:
        lines.append(f"- **Industry:** {industry}")

    telco = uc_data.get("telcoUseCase", "")
    if telco:
        lines.append(f"- **Telco Use Case:** {telco}")

    hw = uc_data.get("hardware", "")
    if hw:
        lines.append(f"- **Equipment Models:** {hw}")

    spl = uc_data.get("spl", "")
    if spl:
        lines.append("- **SPL:**")
        lines.append("```spl")
        lines.append(spl)
        lines.append("```")

    impl = uc_data.get("implementation", "")
    if impl:
        lines.append(f"- **Implementation:** {impl}")

    viz = uc_data.get("visualization", "")
    if viz:
        lines.append(f"- **Visualization:** {viz}")

    cim_models = uc_data.get("cimModels", [])
    if cim_models:
        lines.append(f"- **CIM Models:** {', '.join(cim_models)}")

    dma = uc_data.get("dataModelAcceleration", "")
    if dma:
        lines.append(f"- **Data model acceleration:** {dma}")

    schema = uc_data.get("schema", "")
    if schema:
        lines.append(f"- **Schema:** {schema}")

    cim_spl = uc_data.get("cimSpl", "")
    if cim_spl:
        lines.append("- **CIM SPL:**")
        lines.append("```spl")
        lines.append(cim_spl)
        lines.append("```")

    refs = uc_data.get("references", [])
    if refs:
        ref_strs = []
        for r in refs:
            title_r = r.get("title", "")
            url = r.get("url", "")
            if title_r and url:
                ref_strs.append(f"[{title_r}]({url})")
            elif url:
                ref_strs.append(url)
        if ref_strs:
            lines.append(f"- **References:** {', '.join(ref_strs)}")

    kfp = uc_data.get("knownFalsePositives", "")
    if kfp:
        lines.append(f"- **Known false positives:** {kfp}")

    mitre = uc_data.get("mitreAttack", [])
    if mitre:
        lines.append(f"- **MITRE ATT&CK:** {', '.join(mitre)}")

    dtype = uc_data.get("detectionType", "")
    if dtype:
        lines.append(f"- **Detection type:** {dtype}")

    sdomain = uc_data.get("securityDomain", "")
    if sdomain:
        lines.append(f"- **Security domain:** {sdomain}")

    reqf = uc_data.get("requiredFields", [])
    if reqf:
        lines.append(f"- **Required fields:** {', '.join(reqf)}")

    regs_list = uc_data.get("compliance", [])
    if regs_list:
        reg_names = sorted(set(r.get("regulation", "") for r in regs_list if r.get("regulation")))
        if reg_names:
            lines.append(f"- **Regulations:** {', '.join(reg_names)}")

    status = uc_data.get("status", "")
    if status:
        lines.append(f"- **Status:** {status}")

    reviewed = uc_data.get("lastReviewed", "")
    if reviewed:
        lines.append(f"- **Last reviewed:** {reviewed}")

    sver = uc_data.get("splunkVersions", [])
    if sver:
        lines.append(f"- **Splunk versions:** {', '.join(sver)}")

    reviewer = uc_data.get("reviewer", "")
    if reviewer:
        lines.append(f"- **Reviewer:** {reviewer}")

    return "\n".join(lines)


SUBCATEGORY_NAMES = {
    "2.7": "Proxmox VE",
    "2.8": "oVirt / Red Hat Virtualization",
    "2.9": "OpenStack",
    "2.10": "Dell VxRail",
    "5.13": "Cisco Catalyst Center (Assurance & Compliance)",
    "5.14": "Reverse Proxies & API Gateways (Squid / Traefik)",
    "5.15": "Infoblox DDI (DNS / DHCP / IPAM)",
    "9.8": "BeyondTrust Privileged Access",
    "10.17": "SonicWall Firewall",
    "10.18": "Broadcom / Symantec Endpoint & Proxy",
    "11.6": "Proofpoint Email Security",
    "11.7": "Asterisk / FreePBX VoIP (Email & Collaboration)",
    "12.7": "Control-M & ArgoCD Advanced Operations",
    "13.6": "Grafana & Dashboard Observability",
    "13.7": "Log Pipeline (Fluentd / Fluent Bit)",
    "14.10": "Aranet Environmental Sensors",
    "15.4": "APC / Schneider Electric PDU & UPS",
    "15.5": "CCTV / IP Camera (NVR / ONVIF)",
    "16.6": "PagerDuty / Opsgenie Incident Management",
    "17.4": "Cloudflare WAF & DDoS Protection",
    "17.5": "Forcepoint ONE SSE",
    "17.6": "Akamai Guardicore Microsegmentation",
}


def uc_sort_key(uc_id):
    """Sort key for UC IDs like '1.1.134' -> (1, 1, 134)."""
    parts = uc_id.split(".")
    return tuple(int(p) for p in parts)


def determine_subcategory(uc_id):
    """Extract subcategory prefix from UC ID (e.g., '1.1' from '1.1.134')."""
    parts = uc_id.split(".")
    return f"{parts[0]}.{parts[1]}"


def infer_subcategory_name(sub_id, uc_data_list):
    """Infer a subcategory name from the SUBCATEGORY_NAMES table or UC titles."""
    if sub_id in SUBCATEGORY_NAMES:
        return SUBCATEGORY_NAMES[sub_id]
    if uc_data_list:
        first_title = uc_data_list[0].get("title", "")
        words = first_title.split()
        if len(words) >= 2:
            candidate = " ".join(words[:3])
            return candidate
    return f"Additional Use Cases ({sub_id})"


def main():
    apply_mode = "--apply" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    total_missing = 0
    total_injected = 0
    cat_stats = {}

    for cat_dir in sorted(os.listdir(CONTENT_DIR)):
        if not cat_dir.startswith("cat-"):
            continue
        cat_path = os.path.join(CONTENT_DIR, cat_dir)
        if not os.path.isdir(cat_path):
            continue

        m = re.match(r"cat-(\d+)-", cat_dir)
        if not m:
            continue
        cat_num = int(m.group(1))

        json_ids = {}
        for fname in os.listdir(cat_path):
            if not fname.startswith("UC-") or not fname.endswith(".json"):
                continue
            fpath = os.path.join(cat_path, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                uc_id = data.get("id", "")
                if uc_id:
                    json_ids[uc_id] = data
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  WARNING: Could not parse {fpath}: {e}", file=sys.stderr)

        md_file = find_md_file_for_cat(cat_num)
        if not md_file:
            print(f"  WARNING: No markdown file found for category {cat_num}", file=sys.stderr)
            continue

        md_ids = extract_md_uc_ids(md_file)

        missing = set(json_ids.keys()) - md_ids
        if not missing:
            if verbose:
                print(f"  {cat_dir}: OK — all {len(json_ids)} JSON UCs are in markdown")
            continue

        cat_stats[cat_num] = len(missing)
        total_missing += len(missing)
        print(f"  {cat_dir}: {len(missing)} UCs missing from markdown (JSON has {len(json_ids)}, MD has {len(md_ids)})")

        if not apply_mode:
            if verbose:
                for uid in sorted(missing, key=uc_sort_key):
                    print(f"    MISSING: UC-{uid} — {json_ids[uid].get('title', '?')}")
            continue

        subs, lines = extract_md_subcategories(md_file)
        missing_by_sub = defaultdict(list)
        for uid in missing:
            sub_prefix = determine_subcategory(uid)
            missing_by_sub[sub_prefix].append(uid)

        sub_line_map = {}
        for s in subs:
            sub_line_map[s["id"]] = s

        new_content_blocks = []

        for sub_id in sorted(missing_by_sub.keys(), key=lambda x: tuple(int(p) for p in x.split("."))):
            uids = sorted(missing_by_sub[sub_id], key=uc_sort_key)

            if sub_id in sub_line_map:
                sub_info = sub_line_map[sub_id]
                sub_idx = None
                for idx, s in enumerate(subs):
                    if s["id"] == sub_id:
                        sub_idx = idx
                        break
                if sub_idx is not None and sub_idx + 1 < len(subs):
                    next_sub_line = subs[sub_idx + 1]["line"]
                else:
                    next_sub_line = len(lines)

                insert_line = next_sub_line
                for li in range(next_sub_line - 1, sub_info["line"], -1):
                    if lines[li].strip():
                        insert_line = li + 1
                        break

                uc_blocks = []
                for uid in uids:
                    md_block = json_to_markdown(json_ids[uid])
                    uc_blocks.append(md_block)

                new_content_blocks.append((insert_line, uc_blocks, sub_id, False))
            else:
                uc_data_list = [json_ids[uid] for uid in uids]
                sub_name = infer_subcategory_name(sub_id, uc_data_list)

                uc_blocks = []
                for uid in uids:
                    md_block = json_to_markdown(json_ids[uid])
                    uc_blocks.append(md_block)

                new_content_blocks.append((len(lines), uc_blocks, sub_id, sub_name))

        new_content_blocks.sort(key=lambda x: x[0], reverse=True)

        new_lines = list(lines)
        for insert_line, uc_blocks, sub_id, sub_name in new_content_blocks:
            block_text = []
            if sub_name:
                block_text.append(f"\n### {sub_id} {sub_name}\n\n")

            for i_uc, md_block in enumerate(uc_blocks):
                block_text.append("---\n\n")
                block_text.append(md_block + "\n\n")

            combined = "".join(block_text)
            block_lines = [l + "\n" if not l.endswith("\n") else l for l in combined.split("\n")]
            for bl in reversed(block_lines):
                new_lines.insert(insert_line, bl)
            total_injected += len(uc_blocks)

        with open(md_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"    → Injected {len(missing)} UCs into {os.path.basename(md_file)}")

    print(f"\n{'='*60}")
    print(f"Summary: {total_missing} UCs exist in JSON but not in markdown")
    if apply_mode:
        print(f"Injected: {total_injected} UC entries into markdown files")
    else:
        print("Run with --apply to inject missing entries into markdown files")

    if cat_stats:
        print("\nPer-category breakdown:")
        for cat_num in sorted(cat_stats):
            print(f"  Cat-{cat_num:02d}: {cat_stats[cat_num]} missing")

    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
