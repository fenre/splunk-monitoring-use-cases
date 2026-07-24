#!/usr/bin/env python3
"""Consolidate cat-25 subcategories per data/cat25_merge_manifest.json.

Renumber absorbed UCs into survivor subcategories with gap-free Z indices,
update _category.json, and refresh non-technical-view.data.ts UC id references.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT_DIR = REPO / "content" / "cat-25-personal-hobbyist-monitoring"
CAT_JSON = CAT_DIR / "_category.json"
MANIFEST = REPO / "data" / "cat25_merge_manifest.json"
NTV_TS = REPO / "apps" / "web" / "src" / "data" / "non-technical-view.data.ts"

UC_FILE = re.compile(r"^UC-25\.(\d+)\.(\d+)\.json$")
SUBCAT_KEY = re.compile(r"^25\.(\d+)$")
ID_IN_TEXT = re.compile(r"\b25\.\d+\.\d+\b")
UC_ID_IN_TEXT = re.compile(r"\bUC-25\.\d+\.\d+\b")


def parse_subcat_num(subcat_id: str) -> int:
    m = SUBCAT_KEY.match(subcat_id)
    if not m:
        raise ValueError(f"Invalid subcategory id: {subcat_id!r}")
    return int(m.group(1))


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    merges = data["merges"]
    absorbed: set[str] = set()
    survivors: set[str] = set()
    for group in merges:
        sid = group["survivor"]
        survivors.add(sid)
        for aid in group["absorb"]:
            if aid in absorbed:
                raise ValueError(f"{aid} appears in multiple merge groups")
            if aid in survivors:
                raise ValueError(f"{aid} is both survivor and absorbed")
            absorbed.add(aid)
        if sid in absorbed:
            raise ValueError(f"{sid} is both survivor and absorbed")
    return merges


def collect_group_ucs(survivor: str, absorb: list[str]) -> list[tuple[int, int, Path]]:
    """Return sorted (subcat_num, z, path) for all UCs in merge group."""
    subcats = [survivor, *absorb]
    wanted = {parse_subcat_num(s) for s in subcats}
    rows: list[tuple[int, int, Path]] = []
    for path in CAT_DIR.glob("UC-25.*.*.json"):
        m = UC_FILE.match(path.name)
        if not m:
            continue
        y, z = int(m.group(1)), int(m.group(2))
        if y in wanted:
            rows.append((y, z, path))
    rows.sort(key=lambda t: (t[0], t[1]))
    return rows


def build_id_map(merges: list[dict]) -> dict[str, str]:
    id_map: dict[str, str] = {}
    for group in merges:
        survivor = group["survivor"]
        surv_num = parse_subcat_num(survivor)
        rows = collect_group_ucs(survivor, group["absorb"])
        for idx, (_y, _z, path) in enumerate(rows, start=1):
            old_id = path.stem.replace("UC-", "")
            new_id = f"25.{surv_num}.{idx}"
            if old_id != new_id:
                id_map[old_id] = new_id
    return id_map


def replace_ids_in_text(text: str, id_map: dict[str, str]) -> str:
    """Replace UC ids in free text using word boundaries to avoid prefix collisions."""
    if not id_map:
        return text
    present = [old_id for old_id in id_map if old_id in text or f"UC-{old_id}" in text]
    if not present:
        return text
    for old_id in sorted(present, key=len, reverse=True):
        new_id = id_map[old_id]
        text = re.sub(rf"\bUC-{re.escape(old_id)}\b", f"UC-{new_id}", text)
        text = re.sub(rf"\b{re.escape(old_id)}\b", new_id, text)
    return text


def uc_ids_in_merge_groups(merges: list[dict]) -> set[str]:
    ids: set[str] = set()
    for group in merges:
        rows = collect_group_ucs(group["survivor"], group["absorb"])
        for _y, _z, path in rows:
            ids.add(path.stem.replace("UC-", ""))
    return ids


def migrate_uc_files(id_map: dict[str, str], merge_uc_ids: set[str], *, dry_run: bool) -> None:
    staging = CAT_DIR / ".merge-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    full_map: dict[str, str] = {}
    for path in CAT_DIR.glob("UC-25.*.*.json"):
        old_id = path.stem.replace("UC-", "")
        full_map[old_id] = id_map.get(old_id, old_id)

    rewrite_count = 0
    for path in sorted(CAT_DIR.glob("UC-25.*.*.json")):
        old_id = path.stem.replace("UC-", "")
        if old_id not in merge_uc_ids:
            continue
        new_id = full_map[old_id]
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        raw = replace_ids_in_text(raw, id_map)
        payload = json.loads(raw)
        payload["id"] = new_id
        raw = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        dest = staging / f"UC-{new_id}.json"
        if not dry_run:
            dest.write_text(raw, encoding="utf-8")
        rewrite_count += 1

    if dry_run:
        print(f"[dry-run] Would rewrite {rewrite_count} UC sidecars")
        shutil.rmtree(staging)
        return

    for old_id in merge_uc_ids:
        src = CAT_DIR / f"UC-{old_id}.json"
        if src.exists():
            src.unlink()

    for staged in sorted(staging.glob("UC-*.json")):
        staged.rename(CAT_DIR / staged.name)
    staging.rmdir()
    print(f"Rewrote {rewrite_count} UC sidecars ({len(id_map)} id changes)")


def merge_data_sources(*parts: str) -> str:
    seen: set[str] = set()
    tokens: list[str] = []
    for part in parts:
        for chunk in part.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            key = chunk.lower()
            if key in seen:
                continue
            seen.add(key)
            tokens.append(chunk)
    return ", ".join(tokens)


def update_category_json(merges: list[dict], *, dry_run: bool) -> None:
    data = json.loads(CAT_JSON.read_text(encoding="utf-8"))
    absorb_all: set[str] = set()
    merge_by_survivor = {g["survivor"]: g for g in merges}
    for g in merges:
        absorb_all.update(g["absorb"])

    counts = Counter()
    for path in CAT_DIR.glob("UC-25.*.*.json"):
        m = UC_FILE.match(path.name)
        if m:
            counts[int(m.group(1))] += 1

    new_subs: list[dict] = []
    for sub in data["subcategories"]:
        sid = sub["id"]
        if sid in absorb_all:
            continue
        entry = dict(sub)
        if sid in merge_by_survivor:
            g = merge_by_survivor[sid]
            entry["name"] = g["name"]
            if g.get("primaryAppTa"):
                entry["primaryAppTa"] = g["primaryAppTa"]
            absorbed_sources = [
                s.get("dataSources", "")
                for s in data["subcategories"]
                if s["id"] in g["absorb"]
            ]
            entry["dataSources"] = merge_data_sources(
                g.get("dataSources", entry.get("dataSources", "")),
                *absorbed_sources,
            )
        num = parse_subcat_num(sid)
        entry["useCaseCount"] = counts.get(num, 0)
        new_subs.append(entry)

    data["subcategories"] = new_subs
    data["useCaseCount"] = sum(counts.values())

    # Update quickStart ids via id_map if present
    id_map = build_id_map(merges)
    for qs in data.get("quickStart", []):
        qid = qs.get("id", "")
        if qid in id_map:
            qs["id"] = id_map[qid]
            g = merge_by_survivor.get(f"25.{qid.split('.')[1]}")
            if g:
                qs["subcategory"] = g["name"]

    if dry_run:
        print(
            f"[dry-run] Would update _category.json: "
            f"{len(new_subs)} subcategories, {data['useCaseCount']} UCs"
        )
        return

    CAT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Updated _category.json: {len(new_subs)} subcategories, "
        f"{data['useCaseCount']} UCs (removed {len(absorb_all)} absorbed)"
    )


def subcat_from_uc_id(uc_id: str) -> str | None:
    parts = uc_id.split(".")
    if len(parts) == 3 and parts[0] == "25":
        return f"25.{parts[1]}"
    return None


def parse_cat25_areas(cat25_block: str) -> list[dict]:
    """Parse `{ name, description, ucs }` blocks from category 25 areas array."""
    areas_start = cat25_block.find("areas: [")
    if areas_start < 0:
        raise RuntimeError("Could not find areas: [ in category 25")
    lines = cat25_block[areas_start:].splitlines()
    areas: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'\s+\{ name: "(.*)", description: "(.*)", ucs: \[$', line)
        if not m:
            i += 1
            continue
        name, desc = m.group(1), m.group(2)
        ucs_lines: list[str] = []
        i += 1
        while i < len(lines):
            ucs_line = lines[i]
            if re.match(r"\s+\]\},?\s*$", ucs_line):
                break
            ucs_lines.append(ucs_line)
            i += 1
        ucs_raw = "\n".join(ucs_lines)
        uc_ids = re.findall(r'id: "(\d+\.\d+\.\d+)"', ucs_raw)
        areas.append({"name": name, "desc": desc, "ucs_raw": ucs_raw, "uc_ids": uc_ids})
        i += 1
    if not areas:
        raise RuntimeError("Could not parse category 25 areas")
    return areas


def update_non_technical_view(id_map: dict[str, str], merges: list[dict], *, dry_run: bool) -> None:
    absorb_to_survivor: dict[str, str] = {}
    survivor_names: dict[str, str] = {}
    for g in merges:
        survivor_names[g["survivor"]] = g["name"]
        for aid in g["absorb"]:
            absorb_to_survivor[aid] = g["survivor"]

    text = NTV_TS.read_text(encoding="utf-8")

    # Apply id remaps globally in the TS file
    for old_id, new_id in sorted(id_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = text.replace(f'"{old_id}"', f'"{new_id}"')

    cat25_start = text.find('"25": {')
    if cat25_start < 0:
        raise RuntimeError("Could not find category 25 block in non-technical-view.data.ts")
    cat25_end = text.find('\n  "26":', cat25_start)
    if cat25_end < 0:
        cat25_end = text.find("\n};", cat25_start)
    cat25_block = text[cat25_start:cat25_end]

    parsed_areas = parse_cat25_areas(cat25_block)

    def area_survivor(area: dict) -> str | None:
        subcats = {subcat_from_uc_id(uid) for uid in area["uc_ids"]}
        subcats.discard(None)
        mapped: set[str] = set()
        for sc in subcats:
            if sc in absorb_to_survivor:
                mapped.add(absorb_to_survivor[sc])
            elif sc in survivor_names:
                mapped.add(sc)
            else:
                return None
        if len(mapped) == 1:
            only = next(iter(mapped))
            return only if only in survivor_names else None
        return None

    merged: dict[str, dict] = {}
    order: list[str] = []
    for area in parsed_areas:
        surv = area_survivor(area)
        key = surv if surv else f"__standalone__:{area['name']}"
        if key not in merged:
            merged[key] = {
                "name": survivor_names[surv] if surv else area["name"],
                "desc": area["desc"],
                "ucs_entries": [],
                "prefer_desc_from_survivor": surv is not None,
            }
            order.append(key)
        entry = merged[key]
        entry["ucs_entries"].append(area["ucs_raw"])
        if surv and surv in survivor_names:
            entry["name"] = survivor_names[surv]
            if any(subcat_from_uc_id(uid) == surv for uid in area["uc_ids"]):
                entry["desc"] = area["desc"]

    final_order = list(order)

    def dedupe_ucs(ucs_chunks: list[str]) -> str:
        seen: set[str] = set()
        entries: list[str] = []
        for chunk in ucs_chunks:
            for ucs_line in chunk.splitlines():
                m = re.search(r'id: "(\d+\.\d+\.\d+)"', ucs_line)
                if m:
                    uid = m.group(1)
                    if uid in seen:
                        continue
                    seen.add(uid)
                stripped = ucs_line.strip().rstrip(",")
                if stripped.startswith("{ id:"):
                    entries.append("        " + stripped.lstrip())
        return ",\n        ".join(entries)

    rebuilt_areas: list[str] = []
    for key in final_order:
        entry = merged[key]
        ucs_body = dedupe_ucs(entry["ucs_entries"])
        rebuilt_areas.append(
            f'      {{ name: "{entry["name"]}", description: "{entry["desc"]}", ucs: [\n'
            f"{ucs_body}\n"
            f"      ]}}"
        )

    areas_start = cat25_block.find("areas: [")
    areas_close = cat25_block.find("    ]\n  }", areas_start)
    if areas_close < 0:
        raise RuntimeError("Could not find areas closing bracket in category 25")

    prefix = cat25_block[: areas_start + len("areas: [\n")]
    suffix = cat25_block[areas_close:]
    new_cat25_block = prefix + ",\n".join(rebuilt_areas) + "\n" + suffix
    new_text = text[:cat25_start] + new_cat25_block + text[cat25_end:]

    if dry_run:
        print(
            f"[dry-run] Would update non-technical-view.data.ts: "
            f"{len(parsed_areas)} areas -> {len(final_order)} areas"
        )
        return

    NTV_TS.write_text(new_text, encoding="utf-8")
    print(
        f"Updated non-technical-view.data.ts: "
        f"{len(parsed_areas)} areas -> {len(final_order)} areas"
    )


def write_id_map(id_map: dict[str, str], *, dry_run: bool) -> None:
    out = REPO / "data" / "cat25_id_remap.json"
    payload = {
        "description": "Old -> new UC id mapping from cat-25 subcategory consolidation.",
        "changes": len(id_map),
        "id_map": dict(sorted(id_map.items())),
    }
    if dry_run:
        print(f"[dry-run] Would write {out} with {len(id_map)} id changes")
        return
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(id_map)} id changes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    merges = load_manifest(MANIFEST)
    id_map = build_id_map(merges)
    merge_uc_ids = uc_ids_in_merge_groups(merges)

    absorbed = sum(len(g["absorb"]) for g in merges)
    print(f"Merge groups: {len(merges)}, absorbing {absorbed} subcategories")
    print(f"UC id remaps: {len(id_map)} (touching {len(merge_uc_ids)} sidecars)")

    migrate_uc_files(id_map, merge_uc_ids, dry_run=args.dry_run)
    update_category_json(merges, dry_run=args.dry_run)
    update_non_technical_view(id_map, merges, dry_run=args.dry_run)
    write_id_map(id_map, dry_run=args.dry_run)

    if not args.dry_run:
        mapping = REPO / "data" / "provenance" / "mapping-ledger.json"
        if mapping.exists():
            print(
                "NOTE: mapping-ledger.json may need refresh via make sync-generated "
                "after migration."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
