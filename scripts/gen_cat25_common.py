#!/usr/bin/env python3
"""Shared helpers for cat-25 Personal & Hobbyist Monitoring UC generators."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT25 = REPO / "content" / "cat-25-personal-hobbyist-monitoring"
HEC = {
    "title": "Splunk HTTP Event Collector",
    "url": "https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector",
}

GRANDMA_OPENERS = (
    "It tracks",
    "It watches",
    "It counts",
    "It spots",
    "It warns",
    "It logs",
    "It maps",
    "It ranks",
    "It compares",
    "It surfaces",
    "It checks",
    "It measures",
    "It highlights",
    "It records",
    "It flags",
    "It totals",
    "It lists",
    "It monitors",
    "It reveals",
    "It reminds",
    "It celebrates",
    "It nudges",
    "It blends",
    "It gathers",
    "It turns",
    "It frames",
    "It produces",
    "It builds",
    "It keeps",
    "It notices",
    "It works out",
    "It adds up",
    "It shows",
    "It tells you",
    "It brings back",
    "It lays out",
    "It treats",
    "It combines",
    "It gives you",
    "It catches",
    "It finds",
    "It scans",
    "It reviews",
    "It summarises",
    "It estimates",
    "It predicts",
    "It scores",
    "It rates",
    "It times",
    "It charts",
)


def R(*pairs):
    return [{"title": t, "url": u} for t, u in pairs] + [HEC]


def scan_existing() -> tuple[dict[str, int], set[str], dict[str, set[str]]]:
    """Return (max_z_by_sub, titles, grandma_openers_by_sub)."""
    max_z: dict[str, int] = defaultdict(int)
    titles: set[str] = set()
    openers: dict[str, set[str]] = defaultdict(set)
    for path in sorted(CAT25.glob("UC-25.*.*.json")):
        m = re.match(r"UC-25\.(\d+)\.(\d+)\.json$", path.name)
        if not m:
            continue
        sub, z = m.group(1), int(m.group(2))
        max_z[sub] = max(max_z[sub], z)
        data = json.loads(path.read_text(encoding="utf-8"))
        titles.add(data.get("title", ""))
        ge = data.get("grandmaExplanation", "")
        if isinstance(ge, str) and ge.strip():
            words = ge.strip().split()
            openers[sub].add(" ".join(words[:3]).lower())
            openers[sub].add(" ".join(words[:2]).lower())
            openers[sub].add(ge.strip()[:20].lower())
    return max_z, titles, openers


class Cat25Writer:
    def __init__(self, append: bool = True):
        self.append = append
        self.max_z, self.titles, self.openers = scan_existing()
        self._counts: dict[str, int] = defaultdict(int)
        self._opener_idx: dict[str, int] = defaultdict(int)

    def _next_opener(self, sub: str) -> str:
        idx = self._opener_idx[sub]
        while True:
            opener = GRANDMA_OPENERS[idx % len(GRANDMA_OPENERS)]
            idx += 1
            key = opener.lower()
            used = self.openers.get(sub, set())
            if key not in used:
                self._opener_idx[sub] = idx
                self.openers[sub].add(key)
                return opener

    def U(
        self,
        sub: str,
        title: str,
        crit: str,
        diff: str,
        mtypes: list[str],
        spl: str,
        desc: str,
        val: str,
        impl: str,
        viz: str,
        grandma_body: str,
        refs: list[dict],
        app: str,
        ds: str,
        pillar: str = "Platform",
        grandma: str | None = None,
    ) -> str:
        assert title not in self.titles, f"duplicate title: {title}"
        assert desc.strip() != val.strip(), f"desc==value for {title}"
        self.titles.add(title)
        self._counts[sub] += 1
        if self.append:
            z = self.max_z[sub] + self._counts[sub]
        else:
            z = self._counts[sub]
        uc_id = f"25.{sub}.{z}"
        if grandma is None:
            opener = self._next_opener(sub)
            grandma = f"{opener} {grandma_body.lstrip()}"
        doc = {
            "$schema": "../../schemas/uc.schema.json",
            "id": uc_id,
            "title": title,
            "criticality": crit,
            "difficulty": diff,
            "monitoringType": mtypes,
            "splunkPillar": pillar,
            "dataSources": ds,
            "app": app,
            "spl": spl,
            "description": desc,
            "value": val,
            "implementation": impl,
            "visualization": viz,
            "cimModels": [],
            "references": refs,
            "grandmaExplanation": grandma,
        }
        path = CAT25 / f"UC-{uc_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return uc_id

    def summary(self) -> tuple[int, dict[str, int]]:
        added = dict(self._counts)
        return sum(added.values()), added
