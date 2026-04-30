#!/usr/bin/env python3
"""Extract graph relationships from UC JSON files into a compact graph-data.json.

Produces nodes (categories, equipment, CIM models, pillars) and weighted edges
suitable for rendering with Sigma.js / graphology.

Usage:
    python3 tools/build-graph-data.py              # writes graph-data.json
    python3 tools/build-graph-data.py --out dist/   # writes dist/graph-data.json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
CATEGORY_DIRS = sorted(CONTENT_DIR.glob("cat-*"))

PILLAR_COLORS = {
    "Observability": "#049FD9",
    "IT Operations": "#6BA32A",
    "Security":      "#C24632",
    "Platform":      "#D9B216",
}

WAVE_ORDER = {"crawl": 0, "walk": 1, "run": 2}

STATUS_LABELS = {"verified": "Verified", "draft": "Draft", "community": "Community"}

# Splunk's IT Operations pillar (ITSI) is a service-management layer that
# consumes signals from nearly every infrastructure, application, network,
# and security monitoring use case.  The per-UC `splunkPillar` field records
# which Splunk *product SKU* the UC is primarily delivered through — but ITSI
# aggregates KPIs from all pillars for service health, event correlation, and
# incident management.  The relevance weights below capture this: every
# category whose UCs produce operational signals is relevant to IT Ops.
# Weight 1.0 = core IT Ops domain; 0.0 = not relevant.
_ITOPS_RELEVANCE = {
    1:  0.9,   # Server & Compute — core ops
    2:  0.9,   # Virtualization — core ops
    3:  0.8,   # Containers & Orchestration
    4:  0.8,   # Cloud Infrastructure
    5:  0.9,   # Network Infrastructure — core ops
    6:  0.9,   # Storage & Backup — core ops
    7:  0.8,   # Database & Data Platforms
    8:  0.9,   # Application Infrastructure — core ops
    9:  0.3,   # Identity & Access Management (mostly Security)
    10: 0.15,  # Security Infrastructure (mostly Security; IT Ops manages avail.)
    11: 0.7,   # Email & Collaboration
    12: 0.7,   # DevOps & CI/CD
    13: 0.8,   # Observability & Monitoring Stack (meta-monitoring)
    14: 0.6,   # IoT & OT
    15: 0.9,   # Data Center Physical Infrastructure — core ops
    16: 1.0,   # Service Management & ITSM — ITSI's home domain
    17: 0.15,  # Network Security & Zero Trust (mostly Security)
    18: 0.8,   # Data Center Fabric & SDN
    19: 0.9,   # Compute Infrastructure (HCI & Converged) — core ops
    20: 0.9,   # Cost & Capacity Management — capacity planning
    21: 0.5,   # Industry Verticals
    22: 0.3,   # Regulatory and Compliance Frameworks
    23: 0.1,   # Business Analytics & Executive Intelligence
}


def load_categories():
    cats = {}
    for d in CATEGORY_DIRS:
        meta_path = d / "_category.json"
        if not meta_path.exists():
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        cats[meta["id"]] = {
            "id": meta["id"],
            "name": meta["name"],
            "slug": meta.get("slug", d.name),
            "icon": meta.get("icon", "folder"),
            "description": meta.get("description", ""),
        }
    return cats


def load_all_ucs():
    ucs = []
    for d in CATEGORY_DIRS:
        for fp in sorted(d.glob("UC-*.json")):
            with open(fp) as f:
                try:
                    uc = json.load(f)
                except json.JSONDecodeError:
                    continue
            uc["_file"] = str(fp.relative_to(CONTENT_DIR.parent))
            ucs.append(uc)
    return ucs


def extract_cross_refs(uc):
    """Find UC-x.y.z references in text fields."""
    text = json.dumps(uc)
    refs = set()
    for m in re.finditer(r"UC-(\d+\.\d+\.\d+)", text):
        ref_id = m.group(1)
        if ref_id != uc.get("id"):
            refs.add(ref_id)
    return refs


def cat_id_from_uc_id(uc_id):
    """Extract category number from UC id like '1.1.1' -> 1."""
    parts = uc_id.split(".")
    if parts:
        try:
            return int(parts[0])
        except ValueError:
            pass
    return None


def build_graph(categories, ucs):
    nodes = []
    edges = []
    node_ids = set()

    uc_by_id = {}
    cat_uc_count = Counter()
    cat_equipment = defaultdict(Counter)
    cat_cim = defaultdict(Counter)
    cat_pillar = defaultdict(Counter)
    cat_wave = defaultdict(Counter)
    cat_cross = defaultdict(Counter)

    equipment_total = Counter()
    cim_total = Counter()

    for uc in ucs:
        uid = uc.get("id", "")
        cat_num = cat_id_from_uc_id(uid)
        if cat_num is None:
            continue
        uc_by_id[uid] = uc
        cat_uc_count[cat_num] += 1

        for eq in uc.get("equipment", []):
            cat_equipment[cat_num][eq] += 1
            equipment_total[eq] += 1
        for cm in uc.get("cimModels", []):
            cat_cim[cat_num][cm] += 1
            cim_total[cm] += 1
        pillar = uc.get("splunkPillar", "")
        if pillar:
            cat_pillar[cat_num][pillar] += 1
        wave = uc.get("wave", "")
        if wave:
            cat_wave[cat_num][wave] += 1

    for uc in ucs:
        uid = uc.get("id", "")
        src_cat = cat_id_from_uc_id(uid)
        if src_cat is None:
            continue
        for ref_id in extract_cross_refs(uc):
            tgt_cat = cat_id_from_uc_id(ref_id)
            if tgt_cat is not None and tgt_cat != src_cat:
                cat_cross[src_cat][tgt_cat] += 1

    # --- Pillar nodes ---
    for pillar, color in PILLAR_COLORS.items():
        nid = f"pillar-{pillar}"
        nodes.append({
            "id": nid,
            "label": pillar,
            "type": "pillar",
            "color": color,
            "size": 28,
        })
        node_ids.add(nid)

    # --- Category nodes ---
    for cat_id, meta in categories.items():
        nid = f"cat-{cat_id}"
        dominant_pillar = cat_pillar[cat_id].most_common(1)
        pillar_name = dominant_pillar[0][0] if dominant_pillar else "Observability"
        uc_count = cat_uc_count.get(cat_id, 0)
        nodes.append({
            "id": nid,
            "label": meta["name"],
            "type": "category",
            "color": PILLAR_COLORS.get(pillar_name, "#049FD9"),
            "size": 10 + min(uc_count / 30, 18),
            "ucCount": uc_count,
            "pillar": pillar_name,
            "description": meta.get("description", ""),
        })
        node_ids.add(nid)

        for pname, pcount in cat_pillar[cat_id].items():
            edges.append({
                "source": nid,
                "target": f"pillar-{pname}",
                "type": "belongs-to",
                "weight": pcount,
            })

        # IT Operations relevance: ITSI consumes signals from all pillars
        # for service health KPIs, event correlation, and incident mgmt.
        # Add an edge if the category has operational relevance beyond what
        # the per-UC splunkPillar tagging already captured.
        itops_existing = cat_pillar[cat_id].get("IT Operations", 0)
        relevance = _ITOPS_RELEVANCE.get(cat_id, 0)
        if relevance > 0:
            itops_weight = max(int(uc_count * relevance), 1)
            if itops_weight > itops_existing:
                extra = itops_weight - itops_existing
                edges.append({
                    "source": nid,
                    "target": "pillar-IT Operations",
                    "type": "relevant-to",
                    "weight": extra,
                })

    # --- Equipment nodes (top 80 by total usage) ---
    top_equipment = [eq for eq, _ in equipment_total.most_common(80)]
    for eq in top_equipment:
        nid = f"eq-{eq}"
        count = equipment_total[eq]
        nodes.append({
            "id": nid,
            "label": eq.replace("_", " ").title(),
            "type": "equipment",
            "color": "#8B95A2",
            "size": 4 + min(count / 50, 10),
            "ucCount": count,
        })
        node_ids.add(nid)

    for cat_id in categories:
        for eq, count in cat_equipment[cat_id].items():
            eq_nid = f"eq-{eq}"
            if eq_nid in node_ids and count >= 3:
                edges.append({
                    "source": f"cat-{cat_id}",
                    "target": eq_nid,
                    "type": "uses-equipment",
                    "weight": count,
                })

    # --- CIM model nodes ---
    for cm in sorted(cim_total.keys()):
        if cm in ("N/A",):
            continue
        nid = f"cim-{cm}"
        count = cim_total[cm]
        nodes.append({
            "id": nid,
            "label": cm.replace("_", " "),
            "type": "cim",
            "color": "#04A4B0",
            "size": 4 + min(count / 40, 10),
            "ucCount": count,
        })
        node_ids.add(nid)

    for cat_id in categories:
        for cm, count in cat_cim[cat_id].items():
            cim_nid = f"cim-{cm}"
            if cim_nid in node_ids and count >= 2:
                edges.append({
                    "source": f"cat-{cat_id}",
                    "target": cim_nid,
                    "type": "uses-cim",
                    "weight": count,
                })

    # --- Cross-category edges (UC cross-references aggregated) ---
    seen_pairs = set()
    for src_cat, targets in list(cat_cross.items()):
        for tgt_cat, count in list(targets.items()):
            pair = tuple(sorted([src_cat, tgt_cat]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            total = cat_cross[src_cat].get(tgt_cat, 0) + cat_cross[tgt_cat].get(src_cat, 0)
            if total >= 1:
                edges.append({
                    "source": f"cat-{pair[0]}",
                    "target": f"cat-{pair[1]}",
                    "type": "cross-ref",
                    "weight": total,
                })

    # --- Summary stats ---
    stats = {
        "totalUCs": len(ucs),
        "totalCategories": len(categories),
        "totalEquipment": len(equipment_total),
        "totalCIM": len(cim_total),
        "crossRefUCs": sum(1 for uc in ucs if extract_cross_refs(uc)),
        "crossRefEdges": sum(sum(v.values()) for v in cat_cross.values()),
    }

    return {"nodes": nodes, "edges": edges, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Build graph data from UC catalog")
    parser.add_argument("--out", default=".", help="Output directory")
    args = parser.parse_args()

    print("Loading categories...")
    categories = load_categories()
    print(f"  {len(categories)} categories")

    print("Loading use cases...")
    ucs = load_all_ucs()
    print(f"  {len(ucs)} use cases")

    print("Building graph...")
    graph = build_graph(categories, ucs)
    print(f"  {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "graph-data.json"

    with open(out_path, "w") as f:
        json.dump(graph, f, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path} ({size_kb:.1f} KB)")
    print(f"Stats: {json.dumps(graph['stats'], indent=2)}")


if __name__ == "__main__":
    main()
