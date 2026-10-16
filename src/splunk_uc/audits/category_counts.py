#!/usr/bin/env python3
"""Fail when ``_category.json`` counts drift from ``content/cat-*/UC-*.json``.

The JSON sidecars are the source of truth. Subcategory identity is the
``X.Y`` prefix of each use-case id. This audit compares that file set with
``useCaseCount`` and the ``subcategories`` array on each category index.

``--write`` updates only those two fields. Existing subcategory metadata is
kept when the prefix still has files. Prefixes with zero files are dropped.
A prefix that is missing from the index is added: its label comes from
``quickStart[].subcategory`` when one exists, otherwise the id itself is
used as a placeholder and printed for a human to name. Use-case files are
never edited.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
ID_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def category_dirs(content: Path | None = None) -> list[Path]:
    """Return category directories under ``content/``, excluding templates."""
    root = content or CONTENT
    return sorted(p for p in root.glob("cat-*") if p.is_dir() and (p / "_category.json").is_file())


def _prefix(uc_id: str) -> str | None:
    match = ID_PATTERN.match(uc_id.strip())
    if not match:
        return None
    return f"{int(match.group(1))}.{int(match.group(2))}"


def _sort_key(prefix: str) -> tuple[tuple[int, str], ...]:
    """Sort ``X.Y`` ids numerically and leave legacy suffixes (``22.40-ext``) last."""
    parts: list[tuple[int, str]] = []
    for part in prefix.split("."):
        match = re.match(r"(\d+)", part)
        number = int(match.group(1)) if match else 10**9
        parts.append((number, part))
    return tuple(parts)


def count_files(cat_dir: Path) -> tuple[Counter[str], list[str]]:
    """Count use cases by ``X.Y`` prefix. Return ``(counts, issues)``."""
    counts: Counter[str] = Counter()
    issues: list[str] = []
    for path in sorted(cat_dir.glob("UC-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{path.name}: failed to parse ({exc})")
            continue
        uc_id = str(payload.get("id", "")).strip()
        prefix = _prefix(uc_id)
        if prefix is None:
            issues.append(f"{path.name}: id {uc_id!r} is not X.Y.Z")
            continue
        counts[prefix] += 1
    return counts, issues


def _quick_start_label(prefix: str, quick_start: list[Any]) -> str | None:
    labels: list[str] = []
    for item in quick_start:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id", "")).strip()
        name = str(item.get("subcategory", "")).strip()
        if not name:
            continue
        if item_id == prefix or item_id.startswith(prefix + "."):
            labels.append(name)
    if not labels:
        return None
    return Counter(labels).most_common(1)[0][0]


def reconcile(meta: dict[str, Any], counts: Counter[str]) -> tuple[dict[str, Any], list[str]]:
    """Return an updated category document and placeholder prefixes.

    Only ``useCaseCount`` and ``subcategories`` change. Metadata on a
    subcategory that still has files is preserved.
    """
    existing = meta.get("subcategories") or []
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for entry in existing:
        if not isinstance(entry, dict):
            continue
        prefix = str(entry.get("id", "")).strip()
        if not prefix or prefix in by_id:
            continue
        by_id[prefix] = dict(entry)
        order.append(prefix)

    raw_quick_start = meta.get("quickStart")
    quick_start: list[Any] = raw_quick_start if isinstance(raw_quick_start, list) else []
    placeholders: list[str] = []
    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    for prefix in order:
        if counts.get(prefix, 0) <= 0:
            continue
        entry = by_id[prefix]
        entry["useCaseCount"] = counts[prefix]
        kept.append(entry)
        seen.add(prefix)

    for prefix in sorted(counts, key=_sort_key):
        if prefix in seen or counts[prefix] <= 0:
            continue
        label = _quick_start_label(prefix, quick_start)
        if label is None:
            label = prefix
            placeholders.append(prefix)
        kept.append({"id": prefix, "name": label, "useCaseCount": counts[prefix]})

    updated = dict(meta)
    updated["subcategories"] = kept
    updated["useCaseCount"] = sum(counts.values())
    return updated, placeholders


def diff_category(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Summarise count and subcategory-set changes for one category."""
    before_ids = [
        str(item.get("id"))
        for item in before.get("subcategories") or []
        if isinstance(item, dict) and item.get("id")
    ]
    collapsed = sorted(
        {prefix for prefix, count in Counter(before_ids).items() if count > 1},
        key=_sort_key,
    )
    before_subs: dict[str, int] = {}
    for item in before.get("subcategories") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        prefix = str(item.get("id"))
        if prefix not in before_subs:
            before_subs[prefix] = int(item.get("useCaseCount") or 0)
    after_subs = {
        str(item.get("id")): int(item.get("useCaseCount") or 0)
        for item in after.get("subcategories") or []
        if isinstance(item, dict)
    }
    return {
        "slug": before.get("slug") or after.get("slug"),
        "beforeTotal": int(before.get("useCaseCount") or 0),
        "afterTotal": int(after.get("useCaseCount") or 0),
        "added": sorted(set(after_subs) - set(before_subs), key=_sort_key),
        "removed": sorted(set(before_subs) - set(after_subs), key=_sort_key),
        "countChanges": {
            prefix: {"before": before_subs[prefix], "after": after_subs[prefix]}
            for prefix in sorted(set(before_subs) & set(after_subs), key=_sort_key)
            if before_subs[prefix] != after_subs[prefix]
        },
        "collapsedDuplicateIds": collapsed,
    }


def audit_tree(content: Path | None = None) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Return ``(issues, changed summaries, placeholder prefixes)``."""
    issues: list[str] = []
    changes: list[dict[str, Any]] = []
    placeholders: list[str] = []
    for cat_dir in category_dirs(content):
        meta_path = cat_dir / "_category.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{meta_path}: failed to parse ({exc})")
            continue
        counts, file_issues = count_files(cat_dir)
        issues.extend(f"{cat_dir.name}/{item}" for item in file_issues)
        updated, new_placeholders = reconcile(meta, counts)
        placeholders.extend(f"{cat_dir.name}:{prefix}" for prefix in new_placeholders)
        file_total = sum(counts.values())
        declared_total = int(meta.get("useCaseCount") or 0)
        declared_ids = {
            str(item.get("id"))
            for item in meta.get("subcategories") or []
            if isinstance(item, dict) and item.get("id")
        }
        file_ids = {prefix for prefix, count in counts.items() if count > 0}
        if declared_total != file_total:
            issues.append(
                f"{cat_dir.name}: useCaseCount is {declared_total}, files sum to {file_total}"
            )
        if declared_ids != file_ids:
            missing = sorted(file_ids - declared_ids, key=_sort_key)
            extra = sorted(declared_ids - file_ids, key=_sort_key)
            issues.append(
                f"{cat_dir.name}: subcategory ids differ "
                f"(missing {missing or '-'}, extra {extra or '-'})"
            )
        for item in meta.get("subcategories") or []:
            if not isinstance(item, dict):
                continue
            prefix = str(item.get("id", "")).strip()
            if prefix not in file_ids:
                continue
            declared = int(item.get("useCaseCount") or 0)
            actual = counts[prefix]
            if declared != actual:
                issues.append(
                    f"{cat_dir.name}: subcategory {prefix} useCaseCount is {declared}, files sum to {actual}"
                )
        summary = diff_category(meta, updated)
        if (
            summary["beforeTotal"] != summary["afterTotal"]
            or summary["added"]
            or summary["removed"]
            or summary["countChanges"]
        ):
            changes.append(summary)
    return issues, changes, placeholders


def _split_objects(array_body: str) -> list[str]:
    """Return the raw JSON objects inside a pretty-printed array body."""
    objects: list[str] = []
    depth = 0
    start: int | None = None
    in_string = False
    escape = False
    for index, char in enumerate(array_body):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(array_body[start : index + 1])
                start = None
    return objects


def _set_count(obj_text: str, count: int) -> str:
    return re.sub(
        r'("useCaseCount"\s*:\s*)\d+',
        rf"\g<1>{count}",
        obj_text,
        count=1,
    )


def _format_new_subcategory(entry: dict[str, Any]) -> str:
    blob = json.dumps(
        {"id": entry["id"], "name": entry["name"], "useCaseCount": entry["useCaseCount"]},
        indent=2,
        ensure_ascii=False,
    )
    return "\n".join(f"    {line}" if line else line for line in blob.splitlines())


def _render_preserved(original_text: str, updated: dict[str, Any]) -> str:
    """Patch subcategory blocks and the category total. Leave every other byte.

    Kept subcategory objects are copied from the source file so descriptions,
    guides, and ``\\u`` escapes stay as authored. Duplicate ids keep the first
    block. New prefixes are appended. The category ``useCaseCount`` is the
    2-space-indented key, not the per-subcategory copies.
    """
    match = re.search(r'^  "subcategories": \[', original_text, flags=re.M)
    if match is None:
        raise ValueError("category file has no subcategories array")
    body_start = match.end()
    depth = 1
    in_string = False
    escape = False
    end = None
    for index in range(body_start, len(original_text)):
        char = original_text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise ValueError("subcategories array is not closed")
    original_blocks: dict[str, str] = {}
    for block in _split_objects(original_text[body_start:end]):
        payload = json.loads(block)
        prefix = str(payload.get("id", "")).strip()
        if prefix and prefix not in original_blocks:
            original_blocks[prefix] = block
    rendered_blocks: list[str] = []
    for entry in updated.get("subcategories") or []:
        prefix = str(entry.get("id", "")).strip()
        if prefix in original_blocks:
            block = _set_count(original_blocks[prefix], int(entry["useCaseCount"]))
            if block.startswith("{"):
                block = "    " + block
            rendered_blocks.append(block)
        else:
            rendered_blocks.append(_format_new_subcategory(entry))
    interior = ",\n".join(rendered_blocks)
    text = original_text[:body_start] + "\n" + interior + "\n  " + original_text[end:]
    total = int(updated.get("useCaseCount") or 0)
    text, replaced = re.subn(
        r'^  "useCaseCount": \d+',
        f'  "useCaseCount": {total}',
        text,
        count=1,
        flags=re.M,
    )
    if replaced != 1:
        raise ValueError("category file has no top-level useCaseCount")
    return text


def write_tree(content: Path | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Rewrite drifted category indexes. Return ``(changes, placeholders)``."""
    changes: list[dict[str, Any]] = []
    placeholders: list[str] = []
    for cat_dir in category_dirs(content):
        meta_path = cat_dir / "_category.json"
        original_text = meta_path.read_text(encoding="utf-8")
        meta = json.loads(original_text)
        counts, issues = count_files(cat_dir)
        if issues:
            raise SystemExit(f"{cat_dir.name}: refusing to write over parse errors: {issues[0]}")
        updated, new_placeholders = reconcile(meta, counts)
        placeholders.extend(f"{cat_dir.name}:{prefix}" for prefix in new_placeholders)
        summary = diff_category(meta, updated)
        if updated == meta:
            continue
        rendered = _render_preserved(original_text, updated)
        if rendered != original_text:
            meta_path.write_text(rendered, encoding="utf-8")
            changes.append(summary)
    return changes, placeholders


def _print_changes(changes: list[dict[str, Any]], placeholders: list[str]) -> None:
    if not changes:
        print("category counts match the use-case files")
    for change in changes:
        print(
            f"{change['slug']}: {change['beforeTotal']} -> {change['afterTotal']}"
            f" added={change['added'] or '-'} removed={change['removed'] or '-'}"
        )
        for prefix, delta in change["countChanges"].items():
            print(f"  {prefix}: {delta['before']} -> {delta['after']}")
        if change.get("collapsedDuplicateIds"):
            print(f"  collapsed duplicate ids: {change['collapsedDuplicateIds']}")
    if placeholders:
        print("placeholder subcategory names (id used as the label):")
        for item in placeholders:
            print(f"  {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update useCaseCount and subcategories to match the files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when category totals or subcategory ids disagree with the files.",
    )
    parser.add_argument(
        "--content",
        type=Path,
        default=None,
        help="Alternate content root (tests). Defaults to the repository content/ directory.",
    )
    args = parser.parse_args(argv)
    content = args.content
    if args.write:
        changes, placeholders = write_tree(content)
        _print_changes(changes, placeholders)
        return 0
    issues, changes, placeholders = audit_tree(content)
    _print_changes(changes, placeholders)
    if issues and (args.check or not sys.stdout.isatty()):
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
