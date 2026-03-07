#!/usr/bin/env python3
"""
build.py — Compile per-category markdown files into data.js for the dashboard.

Usage:
    python3 build.py

Reads:
    use-cases/cat-*.md          — use case content (all data including CIM)
    use-cases/INDEX.md          — category metadata (icons, descriptions, starters)

Writes:
    data.js                     — const DATA, CAT_META, CAT_STARTERS, CAT_GROUPS
"""

import glob
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UC_DIR = os.path.join(SCRIPT_DIR, "use-cases")
OUTPUT = os.path.join(SCRIPT_DIR, "data.js")

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
    "infra":    [1, 2, 5, 6, 15, 18, 19],
    "security": [9, 10, 17],
    "cloud":    [3, 4, 20],
    "app":      [7, 8, 11, 12, 13, 14, 16],
}


# Link to the common implementation guide (apps, inputs.conf, Splunk directory)
IMPLEMENTATION_GUIDE_LINK = "docs/implementation-guide.md"


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
                    # Comma-separated technique IDs, e.g. T1562.008, T1190
                    ids = [x.strip() for x in field_value.split(",") if x.strip()]
                    if ids:
                        current_uc["mitre"] = ids
                elif field_name == "detection type":
                    current_uc["dtype"] = field_value.strip()
                elif field_name == "security domain":
                    current_uc["sdomain"] = field_value.strip()
                elif field_name == "required fields":
                    current_uc["reqf"] = field_value

                i += 1
                continue

        i += 1

    # Fill detailed implementation for every UC that doesn't have explicit "Detailed implementation" in markdown
    for sub in category.get("s", []):
        for uc in sub.get("u", []):
            if not (uc.get("md") or "").strip():
                uc["md"] = generate_detailed_impl(uc)

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
    """Write data.js with DATA, CAT_META, and CAT_GROUPS."""
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(cat_meta, ensure_ascii=False, separators=(",", ":"))
    groups_json = json.dumps(CAT_GROUPS, separators=(",", ":"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build.py — do not edit manually\n")
        f.write(f"const DATA = {data_json};\n")
        f.write(f"const CAT_META = {meta_json};\n")
        f.write(f"const CAT_GROUPS = {groups_json};\n")

    size_kb = os.path.getsize(output_path) / 1024
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


if __name__ == "__main__":
    main()
