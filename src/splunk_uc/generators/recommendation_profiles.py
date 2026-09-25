#!/usr/bin/env python3
"""Validate recommendation profiles and emit compact public artifacts.

Write:
    graph-recommend.json
    api/v1/recommender/profiles.json  (additive v1)

    python -m splunk_uc generate-recommendation-profiles
    python -m splunk_uc generate-recommendation-profiles --check
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PROFILES_DIR = ROOT / "data" / "recommendation-profiles"
SCHEMA_PATH = ROOT / "schemas" / "recommendation-profile.schema.json"
CONTENT = ROOT / "content"
GRAPH_OUT = ROOT / "graph-recommend.json"
API_OUT = ROOT / "api" / "v1" / "recommender" / "profiles.json"
SOURCES_PATH = ROOT / "data" / "source-references.json"


def _deterministic_timestamp() -> str:
    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env:
        try:
            return (
                datetime.fromtimestamp(int(env), tz=UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        except ValueError:
            pass
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            check=True,
        )
        ts = int(out.stdout.strip())
        return (
            datetime.fromtimestamp(ts, tz=UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_uc_ids() -> set[str]:
    ids: set[str] = set()
    for path in CONTENT.glob("cat-*/UC-*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"FATAL: invalid JSON {path}: {exc}") from exc
        uc_id = data.get("id")
        if isinstance(uc_id, str):
            ids.add(uc_id)
    return ids


def _source_ids() -> set[str]:
    blob = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for group, entries in blob.items():
        if group.startswith("_") or not isinstance(entries, dict):
            continue
        ids.update(entries.keys())
    return ids


def load_profiles() -> list[dict[str, Any]]:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    known_ucs = _load_uc_ids()
    known_sources = _source_ids()
    profiles: list[dict[str, Any]] = []
    errors: list[str] = []

    for path in sorted(PROFILES_DIR.glob("*.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        for err in validator.iter_errors(profile):
            errors.append(f"{path.name}: {err.message}")
        slug = profile.get("slug")
        if slug and path.stem != slug:
            errors.append(f"{path.name}: filename must match slug {slug}")
        ranks = [item.get("rank") for item in profile.get("corePack") or []]
        if ranks != sorted(ranks):
            errors.append(f"{path.name}: corePack ranks must be strictly increasing")
        if len(ranks) != len(set(ranks)):
            errors.append(f"{path.name}: duplicate corePack ranks")
        for item in profile.get("corePack") or []:
            uc_id = item.get("ucId")
            if uc_id not in known_ucs:
                errors.append(f"{path.name}: unknown ucId {uc_id}")
            for sid in item.get("sourceIds") or []:
                if sid not in known_sources:
                    errors.append(f"{path.name}: unknown sourceId {sid} on {uc_id}")
        for sid in profile.get("sourceIds") or []:
            if sid not in known_sources:
                errors.append(f"{path.name}: unknown sourceId {sid}")
        profiles.append(profile)

    if errors:
        print("FATAL: recommendation profile validation failed:", file=sys.stderr)
        for line in errors:
            print(f"  {line}", file=sys.stderr)
        raise SystemExit(1)
    return profiles


def compact_payload(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for profile in sorted(profiles, key=lambda p: str(p["slug"])):
        core = []
        for item in sorted(profile["corePack"], key=lambda x: int(x["rank"])):
            core.append(
                {
                    "i": item["ucId"],
                    "r": item["rank"],
                    "why": item["why"],
                    "now": item["whyNow"],
                    "m": item["metric"],
                    "d": list(item["dataNeeded"]),
                    "src": list(item["sourceIds"]),
                    "c": item.get("classHint") or "start_now",
                    "blk": item.get("blocker") or "",
                }
            )
        compact[profile["slug"]] = {
            "label": profile["label"],
            "confidence": profile["confidence"],
            "maturity": profile["maturity"],
            "role": list(profile["role"]),
            "outcomes": list(profile["outcomes"]),
            "suites": list(profile["suites"]),
            "hypothesis": profile["valueHypothesis"],
            "data": list(profile["requiredData"]),
            "core": core,
        }
    return {
        "schemaVersion": "1.0.0",
        "generatedAt": _deterministic_timestamp(),
        "profiles": compact,
    }


def _dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def write_payload(payload: dict[str, Any]) -> None:
    GRAPH_OUT.write_text(_dumps(payload), encoding="utf-8")
    API_OUT.parent.mkdir(parents=True, exist_ok=True)
    API_OUT.write_text(_dumps(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = compact_payload(load_profiles())
    body = _dumps(payload)
    if args.check:
        drift = False
        for path in (GRAPH_OUT, API_OUT):
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            if existing != body:
                print(f"FATAL: drift in {path.relative_to(ROOT)}", file=sys.stderr)
                drift = True
        return 1 if drift else 0
    write_payload(payload)
    print(f"Wrote {GRAPH_OUT.relative_to(ROOT)} and {API_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
