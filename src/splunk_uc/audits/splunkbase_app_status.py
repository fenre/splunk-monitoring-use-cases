#!/usr/bin/env python3
"""Fail when a cited Splunkbase app is missing, archived, or a different app.

Every ``Splunkbase <id>`` citation and every ``splunkbase.splunk.com/app/<id>``
URL in a use case is resolved against
``https://splunkbase.splunk.com/api/v1/app/<id>/``. A citation fails when the
API returns 404, the app is archived, or the add-on name beside the id shares
no word with the live title.

``data/splunkbase-app-status-backlog.json`` lists the citations that already
fail. The list may only shrink: ``--check`` fails on a hit that is not listed
and on a listed citation that no longer fails.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-splunkbase-app-status
    PYTHONPATH=src python3 -m splunk_uc audit-splunkbase-app-status --check
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import REPO, iter_uc_sidecars
from splunk_uc.audits.splunkbase_ids import NEARBY_NAME_RE

BACKLOG = REPO / "data" / "splunkbase-app-status-backlog.json"
API_URL = "https://splunkbase.splunk.com/api/v1/app/{app_id}/"

ID_RE = re.compile(
    r"splunkbase\.splunk\.com/app/(?P<urlid>\d+)"
    r"|\bSplunkbase(?:\s+(?:app|ID))?(?:\s*\*\*)?\s*(?P<inlineid>\d{3,5})\b",
    re.IGNORECASE,
)
STOPWORDS = frozenset(
    {"splunk", "addon", "add", "for", "the", "app", "ta", "of", "and", "with", "via"}
)

Fetcher = Callable[[set[str]], dict[str, dict[str, Any]]]


def _tokens(name: str) -> set[str]:
    text = name.lower().replace("add-on", "addon").replace("_", " ")
    return {word for word in re.findall(r"[a-z0-9]+", text) if word not in STOPWORDS and len(word) >= 3}


def titles_conflict(nearby_name: str, api_title: str) -> bool:
    """True when the local add-on name and the live title share no word."""
    if not nearby_name or nearby_name == "<unknown>":
        return False
    local = _tokens(nearby_name)
    remote = _tokens(api_title)
    if not local or not remote:
        return False
    return local.isdisjoint(remote)


def _nearby_name(text: str, start: int) -> str:
    window = text[max(0, start - 160) : start]
    matches = list(NEARBY_NAME_RE.finditer(window))
    if not matches:
        return "<unknown>"
    return re.sub(r"\s+", " ", matches[-1].group("name")).strip(" .,;:")


def _walk_strings(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            yield from _walk_strings(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value
    elif isinstance(value, int) and path.endswith(".id") and "splunkbaseApps" in path:
        yield path, f"Splunkbase {value}"


def collect_citations() -> list[dict[str, Any]]:
    """One row per use case and cited app id, keeping the strongest problem seen later."""
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for _path, payload in iter_uc_sidecars():
        uc_id = f"UC-{payload.get('id')}"
        for _field, text in _walk_strings(payload):
            for match in ID_RE.finditer(text):
                app_id = match.group("urlid") or match.group("inlineid")
                if app_id is None:
                    continue
                key = (uc_id, app_id)
                row = found.setdefault(
                    key,
                    {"id": uc_id, "appId": int(app_id), "names": set()},
                )
                row["names"].add(_nearby_name(text, match.start()))
    return list(found.values())


def classify(
    citations: list[dict[str, Any]],
    facts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return sorted violations. Archived and missing outrank a title mismatch."""
    violations: list[dict[str, Any]] = []
    for citation in citations:
        app_id = str(citation["appId"])
        fact = facts.get(app_id) or {"httpStatus": 404}
        if fact.get("httpStatus") == 404:
            reason = "missing"
        elif fact.get("isArchived"):
            reason = "archived"
        elif any(
            titles_conflict(name, str(fact.get("title") or ""))
            for name in citation.get("names") or []
        ):
            reason = "title_mismatch"
        else:
            continue
        violations.append({"id": citation["id"], "appId": citation["appId"], "reason": reason})
    violations.sort(key=lambda row: (row["id"], row["appId"], row["reason"]))
    return violations


def load_backlog(path: Path | None = None) -> set[tuple[str, int, str]]:
    path = BACKLOG if path is None else path
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(entry["id"], int(entry["appId"]), entry["reason"]) for entry in data.get("useCases", [])}


def compare(
    violations: list[dict[str, Any]],
    backlog: set[tuple[str, int, str]],
) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    current = {(row["id"], int(row["appId"]), row["reason"]) for row in violations}
    new = sorted(current - backlog)
    stale = sorted(backlog - current)
    return new, stale


def _fetch_one(app_id: str) -> dict[str, Any]:
    url = API_URL.format(app_id=app_id)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "splunk-uc-audit-splunkbase-app-status", "Accept": "application/json"},
    )
    context = ssl.create_default_context()
    delay = 1.0
    last_error = "no response"
    for _attempt in range(4):
        try:
            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "httpStatus": 200,
                "title": payload.get("title") or "",
                "isArchived": bool(payload.get("is_archived")),
                "appid": payload.get("appid") or "",
            }
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {"httpStatus": 404}
            if exc.code == 429 or exc.code >= 500:
                last_error = f"HTTP {exc.code}"
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Splunkbase API failed for {app_id}: {last_error}")


def fetch_apps(app_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Resolve each id. Sleeps between calls. Raises if the API cannot be read."""
    facts: dict[str, dict[str, Any]] = {}
    for index, app_id in enumerate(sorted(app_ids, key=int)):
        if index:
            time.sleep(0.2)
        facts[app_id] = _fetch_one(app_id)
    return facts


def main(argv: list[str] | None = None, fetcher: Fetcher | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Exit 1 on unlisted or stale citations.")
    args = parser.parse_args(argv)

    citations = collect_citations()
    app_ids = {str(row["appId"]) for row in citations}
    try:
        facts = (fetcher or fetch_apps)(app_ids)
    except Exception as exc:
        print(f"FAIL: could not resolve Splunkbase app ids: {exc}")
        return 1
    violations = classify(citations, facts)
    backlog = load_backlog()
    new, stale = compare(violations, backlog)

    by_reason: dict[str, int] = {}
    for row in violations:
        by_reason[row["reason"]] = by_reason.get(row["reason"], 0) + 1
    summary = ", ".join(f"{reason} {count}" for reason, count in sorted(by_reason.items())) or "none"
    print(
        f"Splunkbase app status: {len(violations)} citations "
        f"({summary}; {len(backlog)} in backlog)"
    )
    for uc_id, app_id, reason in new[:40]:
        print(f"  NEW   {uc_id} {app_id} {reason}")
    if len(new) > 40:
        print(f"  ... {len(new) - 40} more new citations")
    for uc_id, app_id, reason in stale[:40]:
        print(f"  STALE {uc_id} {app_id} {reason}")
    if len(stale) > 40:
        print(f"  ... {len(stale) - 40} more stale backlog entries")

    if args.check and (new or stale):
        print(
            "FAIL: a Splunkbase id is missing, archived, or names a different app, "
            f"or a backlog entry no longer fails. See {BACKLOG.relative_to(REPO)}."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
