"""Presentation graph derived from fabric relationships.

Pillars are not fabric entities. They stay here so ``graph.html`` still
has a place to hang categories. Equipment and CIM nodes come from
``runsOn`` membership and resolved CIM datasets, not from a second parse
of free text.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from splunk_uc.fabric import PREDICATES
from splunk_uc.fabric.resolve import CONTENT, Fabric

PILLAR_COLORS = {
    "Observability": "#049FD9",
    "IT Operations": "#6BA32A",
    "Security": "#C24632",
    "Platform": "#D9B216",
}

_ITOPS_RELEVANCE = {
    1: 0.9,
    2: 0.9,
    3: 0.8,
    4: 0.8,
    5: 0.9,
    6: 0.9,
    7: 0.8,
    8: 0.9,
    9: 0.3,
    10: 0.15,
    11: 0.7,
    12: 0.7,
    13: 0.8,
    14: 0.6,
    15: 0.9,
    16: 1.0,
    17: 0.15,
    18: 0.8,
    19: 0.9,
    20: 0.9,
    21: 0.5,
    22: 0.3,
    23: 0.1,
    24: 0.6,
    25: 0.05,
}


def _category_meta(content: Path) -> dict[int, dict[str, str]]:
    found: dict[int, dict[str, str]] = {}
    for path in sorted(content.glob("cat-*/_category.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        found[int(meta["id"])] = {
            "name": meta.get("name") or str(meta["id"]),
            "description": meta.get("description") or "",
        }
    return found


def _cat(uc_id: str) -> int | None:
    head = uc_id.split(".", 1)[0]
    if head.isdigit():
        return int(head)
    return None


def presentation_graph(fabric: Fabric, *, content: Path = CONTENT) -> dict[str, Any]:
    """Aggregated graph-data.json payload."""
    categories = _category_meta(content)
    cat_uc: Counter[int] = Counter()
    cat_equipment: dict[int, Counter[str]] = defaultdict(Counter)
    cat_cim: dict[int, Counter[str]] = defaultdict(Counter)
    cat_pillar: dict[int, Counter[str]] = defaultdict(Counter)
    equipment_total: Counter[str] = Counter()
    cim_total: Counter[str] = Counter()
    labels = {(row["type"], row["id"]): row["label"] for row in fabric.entities}

    for uc_id, groups in fabric.members.items():
        cat_id = _cat(uc_id)
        if cat_id is None:
            continue
        cat_uc[cat_id] += 1
        pillar = fabric.pillars.get(uc_id)
        if pillar:
            cat_pillar[cat_id][pillar] += 1
        for product_id in groups.get("vendorProduct") or []:
            cat_equipment[cat_id][product_id] += 1
            equipment_total[product_id] += 1
        for dataset_id in groups.get("cimDataset") or []:
            cat_cim[cat_id][dataset_id] += 1
            cim_total[dataset_id] += 1

    cat_cross: dict[int, Counter[int]] = defaultdict(Counter)
    cross_ucs: set[str] = set()
    for source, predicate, target, _provenance, _confidence in fabric.relationships:
        if predicate != "requires":
            continue
        src_cat = _cat(source)
        tgt_cat = _cat(target)
        if src_cat is None or tgt_cat is None or src_cat == tgt_cat:
            continue
        cat_cross[src_cat][tgt_cat] += 1
        cross_ucs.add(source)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    for pillar, color in PILLAR_COLORS.items():
        nid = f"pillar-{pillar}"
        nodes.append({"id": nid, "label": pillar, "type": "pillar", "color": color, "size": 28})
        node_ids.add(nid)

    for cat_id, meta in sorted(categories.items()):
        nid = f"cat-{cat_id}"
        dominant = cat_pillar[cat_id].most_common(1)
        pillar_name = dominant[0][0] if dominant else "Observability"
        uc_count = cat_uc.get(cat_id, 0)
        nodes.append(
            {
                "id": nid,
                "label": meta["name"],
                "type": "category",
                "color": PILLAR_COLORS.get(pillar_name, "#049FD9"),
                "size": 10 + min(uc_count / 30, 18),
                "ucCount": uc_count,
                "pillar": pillar_name,
                "description": meta["description"],
            }
        )
        node_ids.add(nid)
        for pname, pcount in sorted(cat_pillar[cat_id].items()):
            edges.append(
                {
                    "source": nid,
                    "target": f"pillar-{pname}",
                    "type": "belongs-to",
                    "weight": pcount,
                }
            )
        relevance = _ITOPS_RELEVANCE.get(cat_id, 0)
        if relevance > 0:
            itops_existing = cat_pillar[cat_id].get("IT Operations", 0)
            itops_weight = max(int(uc_count * relevance), 1)
            if itops_weight > itops_existing:
                edges.append(
                    {
                        "source": nid,
                        "target": "pillar-IT Operations",
                        "type": "relevant-to",
                        "weight": itops_weight - itops_existing,
                    }
                )

    for product_id, count in equipment_total.most_common(80):
        nid = f"eq-{product_id}"
        nodes.append(
            {
                "id": nid,
                "label": labels.get(("vendorProduct", product_id), product_id),
                "type": "equipment",
                "color": "#8B95A2",
                "size": 4 + min(count / 50, 10),
                "ucCount": count,
            }
        )
        node_ids.add(nid)
    for cat_id in categories:
        for product_id, count in sorted(cat_equipment[cat_id].items()):
            nid = f"eq-{product_id}"
            if nid in node_ids and count >= 3:
                edges.append(
                    {
                        "source": f"cat-{cat_id}",
                        "target": nid,
                        "type": "uses-equipment",
                        "weight": count,
                    }
                )

    for dataset_id in sorted(cim_total):
        nid = f"cim-{dataset_id}"
        count = cim_total[dataset_id]
        nodes.append(
            {
                "id": nid,
                "label": labels.get(("cimDataset", dataset_id), dataset_id),
                "type": "cim",
                "color": "#04A4B0",
                "size": 4 + min(count / 40, 10),
                "ucCount": count,
            }
        )
        node_ids.add(nid)
    for cat_id in categories:
        for dataset_id, count in sorted(cat_cim[cat_id].items()):
            nid = f"cim-{dataset_id}"
            if nid in node_ids and count >= 2:
                edges.append(
                    {
                        "source": f"cat-{cat_id}",
                        "target": nid,
                        "type": "uses-cim",
                        "weight": count,
                    }
                )

    seen_pairs: set[tuple[int, int]] = set()
    for src_cat, targets in sorted(cat_cross.items()):
        for tgt_cat in sorted(targets):
            pair = (src_cat, tgt_cat) if src_cat < tgt_cat else (tgt_cat, src_cat)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            total = cat_cross[src_cat].get(tgt_cat, 0) + cat_cross[tgt_cat].get(src_cat, 0)
            edges.append(
                {
                    "source": f"cat-{pair[0]}",
                    "target": f"cat-{pair[1]}",
                    "type": "cross-ref",
                    "weight": total,
                }
            )

    nodes.sort(key=lambda row: (row["type"], row["id"]))
    edges.sort(key=lambda row: (row["type"], row["source"], row["target"]))
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "totalUCs": sum(cat_uc.values()),
            "totalCategories": len(categories),
            "totalEquipment": len(equipment_total),
            "totalCIM": len(cim_total),
            "crossRefUCs": len(cross_ucs),
            "crossRefEdges": sum(sum(counter.values()) for counter in cat_cross.values()),
        },
    }


def full_export(fabric: Fabric) -> dict[str, Any]:
    """Node/edge export with use cases as nodes, for an external viewer."""
    nodes = [
        {"id": f"{row['type']}:{row['id']}", "label": row["label"], "type": row["type"]}
        for row in fabric.entities
    ]
    edges = [
        {
            "source": f"{PREDICATES[predicate][0]}:{source}",
            "target": f"{PREDICATES[predicate][1]}:{target}",
            "type": predicate,
            "provenance": provenance,
            "confidence": confidence,
        }
        for source, predicate, target, provenance, confidence in fabric.relationships
    ]
    return {"nodes": nodes, "edges": edges}


def write_graph_file(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
