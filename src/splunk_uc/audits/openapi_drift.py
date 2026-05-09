#!/usr/bin/env python3
"""OpenAPI drift detection — ensures all API paths in dist/ are documented in OpenAPI specs."""

from __future__ import annotations

import pathlib
import re
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


def load_yaml_paths(yaml_path: pathlib.Path) -> set[str]:
    """Extract path patterns from an OpenAPI YAML file."""
    if not yaml_path.exists():
        return set()
    text = yaml_path.read_text(encoding="utf-8")
    paths = set()
    for m in re.finditer(r"^\s{2}(/[^\s:]+):", text, re.MULTILINE):
        paths.add(m.group(1))
    return paths


def collect_dist_paths(dist_api: pathlib.Path) -> set[str]:
    """Walk dist/api/ and collect relative URL paths."""
    if not dist_api.exists():
        return set()
    paths = set()
    for f in dist_api.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".yaml", ".jsonld"):
            rel = "/" + str(f.relative_to(dist_api.parent.parent))
            paths.add(rel)
    return paths


def main(argv: list[str] | None = None) -> int:
    del argv
    root_spec = load_yaml_paths(PROJECT_ROOT / "openapi.yaml")
    v1_spec = load_yaml_paths(PROJECT_ROOT / "api" / "v1" / "openapi.yaml")
    documented = root_spec | v1_spec

    dist_api = PROJECT_ROOT / "dist" / "api"
    if not dist_api.exists():
        print("dist/api/ not found — run 'make build' first. Skipping drift check.")
        return 0

    actual = collect_dist_paths(dist_api)

    undocumented = []
    for p in sorted(actual):
        is_documented = any(
            p == doc_path
            or re.match(doc_path.replace("{", "(?P<").replace("}", ">[^/]+)") + "$", p)
            for doc_path in documented
        )
        if not is_documented:
            undocumented.append(p)

    if undocumented:
        print(f"OpenAPI drift: {len(undocumented)} undocumented path(s):", file=sys.stderr)
        for p in undocumented[:20]:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"OpenAPI drift: all {len(actual)} API paths documented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
