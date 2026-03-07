#!/usr/bin/env python3
"""
Import Splunk Security Essentials (SSE) / security_content detections into this repo.

Compares detections from the Splunk security_content repo (GitHub) with existing
cat-10 use cases, then generates new UC entries for detections not already covered.

Usage:
  # Option A: With a local clone of security_content
  python3 import_sse_detections.py --repo /path/to/security_content

  # Option B: Fetch detection list from GitHub API and fetch each YAML (slower, needs network)
  python3 import_sse_detections.py --from-github

Output:
  - Report of already-implemented vs new detections
  - use-cases/cat-10-sse-import.md (new UCs to merge into cat-10 or keep as extension)

Works with or without PyYAML: uses a minimal built-in YAML extractor when PyYAML is not installed.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def _parse_detection_yaml_minimal(text):
    """Extract name, description, search, how_to_implement, data_source, known_false_positives, references, type, tags from detection YAML without PyYAML."""
    out = {
        "name": "", "description": "", "search": "", "how_to_implement": "", "data_source": [],
        "known_false_positives": "", "references": [], "type": "",
        "mitre_attack_id": [], "security_domain": "", "required_fields": [],
    }
    lines = text.split("\n")
    i = 0
    in_tags = False
    tag_key = None
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if stripped.startswith("name:"):
            out["name"] = stripped[5:].strip().strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("description:"):
            val = stripped[12:].strip().strip("'\"")
            if val:
                out["description"] = val
            else:
                i += 1
                buf = []
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                    buf.append(lines[i].strip())
                    i += 1
                out["description"] = " ".join(buf).strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("search:"):
            block = stripped[7:].strip()
            if block in ("|-", "|"):
                i += 1
                buf = []
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                    buf.append(lines[i].rstrip())
                    i += 1
                out["search"] = "\n".join(buf).rstrip()
            elif block:
                out["search"] = block.strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("how_to_implement:"):
            out["how_to_implement"] = stripped[17:].strip().strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("known_false_positives:"):
            out["known_false_positives"] = stripped[22:].strip().strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("data_source:"):
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                m = re.match(r"^-\s*(.+)$", lines[i].strip())
                if m:
                    out["data_source"].append(m.group(1).strip().strip("'\""))
                i += 1
            continue
        if stripped.startswith("references:"):
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                m = re.match(r"^-\s*(.+)$", lines[i].strip())
                if m:
                    out["references"].append(m.group(1).strip().strip("'\""))
                i += 1
            continue
        if stripped.startswith("type:"):
            out["type"] = stripped[5:].strip().strip("'\"").strip()
            i += 1
            continue
        if stripped.startswith("tags:"):
            in_tags = True
            i += 1
            continue
        if in_tags and (lines[i].startswith(" ") or lines[i].startswith("\t")):
            if stripped.startswith("mitre_attack_id:"):
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")) and not re.match(r"^\s\w+:", lines[i]):
                    m = re.match(r"^-\s*(.+)$", lines[i].strip())
                    if m:
                        val = m.group(1).strip().strip("'\"").strip()
                        # Only append values that look like MITRE technique IDs (e.g. T1556.004)
                        if re.match(r"^T\d+(\.\d+)?$", val):
                            out["mitre_attack_id"].append(val)
                    i += 1
                continue
            if stripped.startswith("security_domain:"):
                out["security_domain"] = stripped[16:].strip().strip("'\"").strip()
                i += 1
                continue
            if stripped.startswith("required_fields:"):
                tag_key = "reqf"
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")) and not re.match(r"^\s\w+:", lines[i]):
                    m = re.match(r"^-\s*(.+)$", lines[i].strip())
                    if m:
                        out["required_fields"].append(m.group(1).strip().strip("'\""))
                    i += 1
                continue
        if in_tags and stripped and not (lines[i].startswith(" ") or lines[i].startswith("\t")):
            in_tags = False
        i += 1
    return out

SCRIPT_DIR = Path(__file__).resolve().parent
CAT_10_PATH = SCRIPT_DIR / "cat-10-security-infrastructure.md"
OUTPUT_PATH = SCRIPT_DIR / "cat-10-sse-import.md"
GITHUB_TREE_URL = "https://api.github.com/repos/splunk/security_content/git/trees/develop?recursive=1"
RAW_BASE = "https://raw.githubusercontent.com/splunk/security_content/develop/"

# Map security_content folder to our subcategory id and name
FOLDER_TO_SUBCAT = {
    "endpoint": ("10.3", "Endpoint Detection & Response (EDR)"),
    "network": ("10.2", "Intrusion Detection/Prevention (IDS/IPS)"),
    "web": ("10.5", "Web Security / Secure Web Gateway"),
    "cloud": ("10.6", "Vulnerability Management"),  # or 10.7; many cloud detections are threat/audit
    "application": ("10.7", "SIEM & SOAR"),  # broad; could split by tags later
}
# Exclude deprecated
SKIP_FOLDERS = {"deprecated"}


def get_existing_cat10_titles():
    """Parse cat-10-security-infrastructure.md and return set of normalized UC titles."""
    titles = set()
    if not CAT_10_PATH.exists():
        return titles
    text = CAT_10_PATH.read_text(encoding="utf-8")
    for m in re.finditer(r"### UC-\d+\.\d+\.\d+\s*[·•]\s*(.+?)(?:\n|$)", text):
        t = m.group(1).strip().lower()
        # Normalize: remove extra spaces, collapse punctuation
        t = re.sub(r"\s+", " ", t)
        titles.add(t)
    return titles


def detection_already_covered(sse_name, existing_titles):
    """Check if an SSE detection is already represented in our cat-10 (fuzzy)."""
    norm = sse_name.strip().lower()
    norm = re.sub(r"\s+", " ", norm)
    if norm in existing_titles:
        return True
    # Substring match: if any existing title is contained in sse name or vice versa
    for ext in existing_titles:
        if ext in norm or norm in ext:
            return True
    return False


def slug_to_title(slug):
    """Convert detection filename slug to Title Case (e.g. aws_delete_cloudtrail -> Aws Delete Cloudtrail)."""
    return slug.replace("_", " ").replace("  ", " ").strip().title()


def fetch_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_yaml_from_github(rel_path):
    """Fetch a single detection YAML from raw GitHub."""
    url = RAW_BASE + rel_path
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return yaml.safe_load(r.read().decode("utf-8")) if yaml else None
    except Exception:
        return None


def parse_detection_yaml(yaml_path):
    """Read detection YAML from disk; return dict with name, description, search, how_to_implement, data_source."""
    try:
        text = yaml_path.read_text(encoding="utf-8")
    except Exception:
        return None
    if yaml:
        try:
            data = yaml.safe_load(text)
            if not data:
                return None
            tags = data.get("tags") or {}
            return {
                "name": data.get("name") or slug_to_title(yaml_path.stem),
                "description": data.get("description") or "",
                "search": data.get("search") or "",
                "how_to_implement": data.get("how_to_implement") or "",
                "data_source": data.get("data_source") or [],
                "status": data.get("status", "production"),
                "known_false_positives": data.get("known_false_positives") or "",
                "references": data.get("references") or [],
                "type": data.get("type") or "",
                "mitre_attack_id": tags.get("mitre_attack_id") or [],
                "security_domain": tags.get("security_domain") or "",
                "required_fields": tags.get("required_fields") or [],
            }
        except Exception:
            pass
    data = _parse_detection_yaml_minimal(text)
    if not data.get("name"):
        data["name"] = slug_to_title(yaml_path.stem)
    data["status"] = "production"
    if "mitre_attack_id" not in data:
        data["mitre_attack_id"] = []
    if "required_fields" not in data:
        data["required_fields"] = []
    return data


def uc_block_from_detection(uc_id, det, data_sources_str="Various"):
    """Generate one UC markdown block from a detection dict."""
    name = (det.get("name") or "").strip()
    desc = (det.get("description") or "").strip()
    search = (det.get("search") or "").strip()
    impl = (det.get("how_to_implement") or "").strip()
    ds = det.get("data_source")
    if isinstance(ds, list):
        data_sources_str = ", ".join(str(x) for x in ds) if ds else "Various"
    elif ds:
        data_sources_str = str(ds)
    block = f"""
### UC-{uc_id} · {name}
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** {desc[:500]}{"…" if len(desc) > 500 else ""}
- **App/TA:** Splunk Security Essentials / ESCU
- **Data Sources:** {data_sources_str}
- **SPL:**
```spl
{search}
```
- **Implementation:** {impl[:400]}{"…" if len(impl) > 400 else ""}
- **Visualization:** Table, Timeline (from ESCU).
- **CIM Models:** N/A

---
"""
    return block


def run_with_repo(repo_path, existing_titles, limit=None):
    """Scan local security_content repo and build new UCs."""
    repo = Path(repo_path)
    detections_dir = repo / "detections"
    if not detections_dir.is_dir():
        print("detections/ not found in repo", file=sys.stderr)
        return [], []
    new_ucs = []
    covered = []
    # Next index per subcategory (we use 10.9.x for all SSE imports to avoid renumbering 10.1-10.8)
    next_10_9 = 1
    for folder in sorted(detections_dir.iterdir()):
        if not folder.is_dir() or folder.name in SKIP_FOLDERS:
            continue
        subcat_id, subcat_name = FOLDER_TO_SUBCAT.get(folder.name, ("10.9", "Splunk Security Essentials (ESCU)"))
        for yf in sorted(folder.glob("*.yml")):
            det = parse_detection_yaml(yf)
            if not det:
                continue
            name = det.get("name") or slug_to_title(yf.stem)
            if detection_already_covered(name, existing_titles):
                covered.append((folder.name, name))
                continue
            det["_subcat_id"] = "10.9"  # Put all in 10.9 for simplicity
            det["_uc_id"] = f"10.9.{next_10_9}"
            new_ucs.append(det)
            next_10_9 += 1
            if limit and len(new_ucs) >= limit:
                return new_ucs, covered
    return new_ucs, covered


def run_from_github(existing_titles, limit=50):
    """Fetch tree from GitHub, then fetch each detection YAML (rate-limited)."""
    print("Fetching detection list from GitHub…", flush=True)
    tree = fetch_json(GITHUB_TREE_URL)
    paths = [
        n["path"] for n in tree.get("tree", [])
        if n.get("path", "").startswith("detections/") and n["path"].endswith(".yml")
        and not n["path"].startswith("detections/deprecated/")
    ]
    print(f"Found {len(paths)} detections (excluding deprecated).", flush=True)
    new_ucs = []
    covered = []
    next_10_9 = 1
    for i, rel_path in enumerate(paths):
        if limit and len(new_ucs) >= limit:
            break
        parts = rel_path.split("/")
        if len(parts) != 3:
            continue
        folder = parts[1]
        det_dict = fetch_yaml_from_github(rel_path)
        if not det_dict:
            continue
        name = det_dict.get("name") or slug_to_title(Path(rel_path).stem)
        if detection_already_covered(name, existing_titles):
            covered.append((folder, name))
            continue
        det_dict["_uc_id"] = f"10.9.{next_10_9}"
        det_dict["_subcat_id"] = "10.9"
        new_ucs.append(det_dict)
        next_10_9 += 1
        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(paths)}…", flush=True)
    return new_ucs, covered


def main():
    ap = argparse.ArgumentParser(description="Import SSE/security_content detections into cat-10.")
    ap.add_argument("--repo", type=str, help="Path to local clone of security_content repo")
    ap.add_argument("--from-github", action="store_true", help="Fetch list and YAMLs from GitHub (no clone)")
    ap.add_argument("--limit", type=int, default=None, help="Max number of new UCs to generate (default: all)")
    ap.add_argument("--no-write", action="store_true", help="Only report counts, do not write cat-10-sse-import.md")
    args = ap.parse_args()
    if not args.repo and not args.from_github:
        ap.error("Use --repo PATH or --from-github")
    if args.from_github and not yaml:
        print("Install PyYAML for --from-github: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    existing = get_existing_cat10_titles()
    print(f"Existing cat-10 UC titles (normalized): {len(existing)}")
    if args.repo:
        new_ucs, covered = run_with_repo(args.repo, existing, limit=args.limit)
    else:
        new_ucs, covered = run_from_github(existing, limit=args.limit or 2000)
    print(f"Already covered (by title): {len(covered)}")
    print(f"New UCs to add: {len(new_ucs)}")
    if args.no_write:
        return
    if not new_ucs:
        print("Nothing to write.")
        return
    out_lines = [
        "",
        "## 10.9 Splunk Security Essentials (ESCU)",
        "",
        "**Primary App/TA:** Splunk Security Essentials, DA-ESS-ContentUpdate, security_content.",
        "",
        "The following use cases are imported from the [Splunk security_content](https://github.com/splunk/security_content) repository (1,900+ detections). Merge this file into cat-10-security-infrastructure.md or keep as a separate extension.",
        "",
        "---",
    ]
    for det in new_ucs:
        out_lines.append(uc_block_from_detection(det["_uc_id"], det))
    OUTPUT_PATH.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
