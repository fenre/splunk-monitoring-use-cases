"""Assign registry ids for the enrichment pilot.

``loose-1`` is the first ruleset: it over-matches phrases, titles, and
spellings. ``strict-1`` is the tightened contract. The grader is separate
from both rulesets. Precision counts only assignments graded correct.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

from splunk_uc.audits.enrichment import (
    FIELDS,
    RegistryIndex,
    _explicit_sourcetypes,
    _narrative,
    audit_tree,
)
from splunk_uc.fabric.mine import _norm_industry, _phrase_hit

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
REGISTRIES = REPO_ROOT / "registries"
SEED = 20261016
PILOT_SIZE = 300
PER_CATEGORY = 8
POSITIVE_KEYS = ("title", "description", "value", "grandmaExplanation")
VENDOR_KEYS = ("title", "app", "dataSources", "spl")
INSERT_ORDER = (*FIELDS, "enrichment")
BARS = {
    "businessAreas": 0.90,
    "sourcetypes": 0.90,
    "industries": 0.90,
    "vendorProducts": 0.90,
    "personas": 0.85,
    "businessOutcomes": 0.85,
}

# Architect grades for registry phrases. correct is specific enough to assign.
# debatable is a real hint that is too broad. wrong is incidental wording.
PHRASE_GRADE: dict[str, dict[str, str]] = {
    "businessOutcomes": {
        "security risk": "correct",
        "attack surface": "correct",
        "malicious activity": "correct",
        "compromise": "wrong",
        "incident response": "correct",
        "mean time to respond": "correct",
        "investigation time": "debatable",
        "triage": "wrong",
        "audit evidence": "correct",
        "compliance evidence": "correct",
        "regulatory requirement": "correct",
        "control evidence": "debatable",
        "downtime": "debatable",
        "unplanned outage": "correct",
        "service disruption": "correct",
        "availability": "wrong",
        "sensitive data": "correct",
        "cardholder data": "correct",
        "personally identifiable": "correct",
        "data loss": "debatable",
        "privileged access": "correct",
        "privileged account": "correct",
        "privilege escalation": "correct",
        "admin rights": "correct",
        "fraud": "debatable",
        "unauthorized transaction": "correct",
        "payment fraud": "correct",
        "service reliability": "correct",
        "error rate": "debatable",
        "latency": "wrong",
        "service health": "debatable",
        "operational cost": "correct",
        "capacity planning": "correct",
        "license consumption": "correct",
        "cloud spend": "correct",
        "containment": "debatable",
        "isolate the host": "correct",
        "block the attack": "correct",
        "threat containment": "correct",
        "process safety": "correct",
        "safety instrumented": "correct",
        "industrial control": "correct",
        "ot security": "correct",
        "unauthorized change": "correct",
        "configuration drift": "correct",
        "change management": "debatable",
        "change window": "correct",
    },
    "businessAreas": {
        "security operations": "correct",
        "soc ": "wrong",
        "detection engineering": "correct",
        "threat detection": "correct",
        "network operations": "correct",
        "routing": "wrong",
        "firewall policy": "correct",
        "interface down": "correct",
        "packet loss": "correct",
        "infrastructure operations": "correct",
        "server health": "correct",
        "host down": "debatable",
        "disk space": "correct",
        "cpu utilization": "correct",
        "identity and access": "correct",
        "authentication failure": "debatable",
        "single sign-on": "correct",
        "privileged access": "correct",
        "compliance": "wrong",
        "audit finding": "correct",
        "control failure": "correct",
        "regulatory": "wrong",
        "application performance": "correct",
        "response time": "debatable",
        "error rate": "debatable",
        "latency": "wrong",
        "data protection": "correct",
        "data loss": "debatable",
        "personal data": "correct",
        "cardholder": "debatable",
        "cloud operations": "correct",
        "cloudtrail": "debatable",
        "kubernetes": "wrong",
        "serverless": "wrong",
        "service management": "correct",
        "incident ticket": "correct",
        "sla breach": "correct",
        "change request": "debatable",
        "operational technology": "correct",
        "scada": "debatable",
        "safety instrumented": "correct",
        "industrial protocol": "correct",
        "fraud": "debatable",
        "financial crime": "correct",
        "anti-money": "correct",
        "payment card": "correct",
        "capacity": "wrong",
        "cloud spend": "correct",
        "license usage": "correct",
        "cost management": "correct",
    },
    "personas": {
        "soc analyst": "correct",
        "security analyst": "correct",
        "tier-1 analyst": "correct",
        "alert queue": "debatable",
        "detection engineer": "correct",
        "detection content": "debatable",
        "saved search": "wrong",
        "correlation search": "wrong",
        "network operator": "correct",
        "network engineer": "correct",
        "noc ": "wrong",
        "routing change": "debatable",
        "platform engineer": "correct",
        "system administrator": "correct",
        "infrastructure engineer": "correct",
        "auditor": "debatable",
        "audit evidence": "wrong",
        "external audit": "debatable",
        "control test": "wrong",
        "incident responder": "correct",
        "incident response": "wrong",
        "containment step": "correct",
        "forensic": "debatable",
        "cloud operator": "correct",
        "cloud engineer": "correct",
        "cloud administrator": "correct",
        "ot operator": "correct",
        "control room": "correct",
        "plant operator": "correct",
        "ics engineer": "correct",
        "service owner": "correct",
        "service desk": "correct",
        "major incident": "debatable",
        "capacity planner": "correct",
        "capacity planning": "wrong",
        "forecast": "wrong",
    },
}

_TOKEN = re.compile(r"(?<![A-Za-z0-9]){token}(?![A-Za-z0-9])", re.IGNORECASE)
_BOILERPLATE = ("delayed incident response", "reducing operational risk", "spreadsheet checks")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _positive_text(uc: dict[str, Any]) -> str:
    return "\n".join(str(uc.get(key) or "") for key in POSITIVE_KEYS)


def _field_text(uc: dict[str, Any], keys: tuple[str, ...]) -> str:
    return "\n".join(str(uc.get(key) or "") for key in keys)


def _quote(text: str, phrase: str) -> str | None:
    idx = text.casefold().find(phrase.casefold())
    if idx < 0:
        return None
    return text[idx : idx + len(phrase)]


def _boilerplate(text: str, phrase: str) -> bool:
    idx = text.casefold().find(phrase.casefold())
    if idx < 0:
        return False
    window = text[max(0, idx - 48) : idx + len(phrase)].casefold()
    return any(snippet in window for snippet in _BOILERPLATE)


def _token_hit(text: str, token: str) -> bool:
    if len(token) < 3:
        return False
    return _TOKEN.pattern.format(token=re.escape(token)) and re.search(
        _TOKEN.pattern.format(token=re.escape(token)),
        text,
    ) is not None


def category_dirs(content: Path) -> list[Path]:
    return sorted(path for path in content.glob("cat-*") if path.is_dir() and any(path.glob("UC-*.json")))


def pilot_paths(content: Path | None = None, *, seed: int = SEED) -> list[Path]:
    """Seeded 300 paths: 8 from each category, then 100 more by category size."""
    root = content or CONTENT
    rng = random.Random(seed)
    cats = category_dirs(root)
    chosen: list[Path] = []
    remaining: dict[Path, list[Path]] = {}
    sizes: dict[Path, int] = {}
    for cat in cats:
        files = sorted(cat.glob("UC-*.json"))
        sizes[cat] = len(files)
        take = min(PER_CATEGORY, len(files))
        picked = rng.sample(files, take)
        chosen.extend(picked)
        picked_set = set(picked)
        remaining[cat] = [path for path in files if path not in picked_set]
    total = sum(sizes.values()) or 1
    raw = {cat: (PILOT_SIZE - len(chosen)) * sizes[cat] / total for cat in cats}
    extra_budget = PILOT_SIZE - len(chosen)
    alloc = {cat: int(raw[cat]) for cat in cats}
    leftover = extra_budget - sum(alloc.values())
    for cat in sorted(cats, key=lambda item: (raw[item] - alloc[item], sizes[item]), reverse=True):
        if leftover <= 0:
            break
        alloc[cat] += 1
        leftover -= 1
    for cat in cats:
        pool = remaining[cat]
        take = min(alloc[cat], len(pool))
        if take:
            chosen.extend(rng.sample(pool, take))
            remaining[cat] = [path for path in pool if path not in set(chosen)]
    if len(chosen) < PILOT_SIZE:
        pool = [path for paths in remaining.values() for path in paths]
        need = min(PILOT_SIZE - len(chosen), len(pool))
        chosen.extend(rng.sample(pool, need))
    if len(chosen) != PILOT_SIZE:
        raise RuntimeError(f"pilot sample is {len(chosen)}, expected {PILOT_SIZE}")
    return chosen


class _Catalog:
    def __init__(self, root: Path) -> None:
        self.index = RegistryIndex(root)
        self.phrases: dict[str, list[tuple[str, str]]] = {field: [] for field in ("businessOutcomes", "businessAreas", "personas")}
        for field, filename in (
            ("businessOutcomes", "business-outcomes.json"),
            ("businessAreas", "business-areas.json"),
            ("personas", "personas.json"),
        ):
            for row in _load(root / filename)["entries"]:
                for phrase in row.get("phrases") or []:
                    self.phrases[field].append((str(phrase), str(row["id"])))
        self.industry_names = [
            (str(row.get("name") or ""), str(row["id"]))
            for row in _load(root / "industries.json")["entries"]
        ]
        self.vendor_tokens: dict[str, list[str]] = {}
        for row in _load(root / "vendor-products.json")["entries"]:
            tokens = [str(row["id"])]
            if row.get("product"):
                tokens.append(str(row["product"]))
            tokens.extend(str(alias) for alias in row.get("aliases") or [])
            self.vendor_tokens[str(row["id"])] = tokens
        self.sourcetype_rows = list(self.index.sourcetype_spellings.items())


def _assignment(entity_id: str, evidence: str, source: str, confidence: float, model: str, version: str) -> dict[str, Any]:
    return {
        "id": entity_id,
        "source": source,
        "confidence": confidence,
        "evidence": evidence,
        "model": model,
        "version": version,
    }


def _phrase_hits(uc: dict[str, Any], catalog: _Catalog, field: str, text: str, *, allow: set[str], version: str) -> list[dict[str, Any]]:
    found: list[tuple[int, str, str]] = []
    for phrase, entity_id in catalog.phrases[field]:
        grade = PHRASE_GRADE[field].get(phrase.casefold())
        if allow and grade not in allow:
            continue
        if not _phrase_hit(text.casefold(), phrase):
            continue
        if version == "strict-1" and _boilerplate(text, phrase):
            continue
        quote = _quote(text, phrase)
        if quote is None:
            continue
        found.append((len(phrase), entity_id, quote))
    found.sort(key=lambda item: (-item[0], item[1]))
    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    cap = {"businessOutcomes": 3, "businessAreas": 2, "personas": 4}[field]
    limit = cap if version == "strict-1" else 8
    for length, entity_id, quote in found:
        if entity_id in seen:
            continue
        seen.add(entity_id)
        confidence = 0.9 if length >= 16 else 0.75
        kept.append(_assignment(entity_id, quote, "inferred", confidence, "phrase-list", version))
        if len(kept) >= limit:
            break
    return kept


def _sourcetypes(uc: dict[str, Any], catalog: _Catalog, version: str) -> list[dict[str, Any]]:
    narrative, data_sources = _narrative(uc)
    if version == "strict-1":
        explicit = _explicit_sourcetypes(narrative, data_sources)
        found: list[dict[str, Any]] = []
        seen: set[str] = set()
        for spelling_cf in sorted(explicit):
            entity_id = catalog.index.sourcetype_by_spelling.get(spelling_cf)
            if entity_id is None or entity_id in seen:
                continue
            exact = next(
                (spelling for spelling in catalog.index.sourcetype_spellings[entity_id] if spelling in narrative),
                None,
            )
            if exact is None:
                continue
            seen.add(entity_id)
            match = re.search(
                rf"sourcetype\s*=\s*(?:\*\*)?\s*[`'\"']?{re.escape(exact)}",
                narrative,
                re.IGNORECASE,
            )
            evidence = narrative[match.start() : match.end()] if match else exact
            found.append(_assignment(entity_id, evidence, "authored", 1.0, "explicit-sourcetype", version))
        return found
    full = narrative.casefold()
    found = []
    for entity_id, spellings in catalog.sourcetype_rows:
        exact = next((spelling for spelling in sorted(spellings) if spelling.casefold() in full), None)
        if exact is None:
            continue
        found.append(_assignment(entity_id, exact, "inferred", 0.5, "substring-sourcetype", version))
        if len(found) >= 6:
            break
    return found


def _industries(uc: dict[str, Any], catalog: _Catalog, version: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    raw = str(uc.get("industry") or "").strip()
    key = _norm_industry(raw) if raw else None
    matched = catalog.index.industry_by_norm.get(key) if key else None
    proposed: list[dict[str, str]] = []
    if raw and matched is None:
        proposed.append(
            {
                "field": "industries",
                "value": raw,
                "note": "The industry field does not match a registry industry.",
            }
        )
    found: list[dict[str, Any]] = []
    if matched and raw:
        found.append(_assignment(matched, raw, "authored", 1.0, "industry-field", version))
    if version == "loose-1":
        # Title and description guesses are the loose error pattern. strict-1
        # does not use them.
        guessed_from = f"{uc.get('title') or ''}\n{uc.get('description') or ''}"
        for name, entity_id in catalog.industry_names:
            if entity_id == matched or len(name) < 6:
                continue
            if name.casefold() in guessed_from.casefold():
                quote = _quote(guessed_from, name)
                if quote:
                    found.append(_assignment(entity_id, quote, "inferred", 0.4, "title-industry", version))
    return found, proposed


def _vendors(uc: dict[str, Any], catalog: _Catalog, version: str) -> list[dict[str, Any]]:
    equipment = [str(item) for item in uc.get("equipment") or [] if isinstance(item, str)]
    if version == "strict-1":
        text = _field_text(uc, VENDOR_KEYS)
        found = []
        for entity_id in equipment:
            if entity_id not in catalog.index.ids["vendorProducts"]:
                continue
            tokens = [token for token in catalog.vendor_tokens.get(entity_id, [entity_id]) if len(token) >= 3]
            hit = next((token for token in tokens if _token_hit(text, token)), None)
            if hit is None:
                continue
            quote = _quote(text, hit) or hit
            found.append(_assignment(entity_id, quote, "authored", 1.0, "vendor-token", version))
        return found
    full, _data_sources = _narrative(uc)
    folded = full.casefold()
    found = []
    for entity_id, tokens in catalog.vendor_tokens.items():
        token = next((item for item in tokens if len(item) >= 4 and item.casefold() in folded), None)
        if token is None:
            continue
        found.append(_assignment(entity_id, token, "inferred", 0.4, "substring-vendor", version))
        if len(found) >= 6:
            break
    return found


def _owner_persona(uc: dict[str, Any], version: str) -> dict[str, Any] | None:
    if version != "loose-1":
        return None
    owner = str(uc.get("owner") or "").strip()
    if owner.casefold() not in {"ciso", "dpo", "cfo"}:
        return None
    return _assignment("auditor", owner, "inferred", 0.3, "owner-copy", version)


def assign_uc(uc: dict[str, Any], catalog: _Catalog, version: str) -> dict[str, Any]:
    """Return id lists, enrichment, and proposedValues for one sidecar."""
    if version not in {"loose-1", "strict-1"}:
        raise ValueError(version)
    allow = {"correct"} if version == "strict-1" else {"correct", "debatable", "wrong"}
    text = _positive_text(uc) if version == "strict-1" else _narrative(uc)[0]
    enrichment: dict[str, Any] = {}
    payload: dict[str, Any] = {}
    for field in ("businessOutcomes", "businessAreas", "personas"):
        rows = _phrase_hits(uc, catalog, field, text, allow=allow, version=version)
        if field == "personas":
            copied = _owner_persona(uc, version)
            if copied and copied["id"] not in {row["id"] for row in rows}:
                rows.append(copied)
        if rows:
            payload[field] = [row["id"] for row in rows]
            enrichment[field] = rows
    industries, proposed = _industries(uc, catalog, version)
    if industries:
        payload["industries"] = [row["id"] for row in industries]
        enrichment["industries"] = industries
    sourcetypes = _sourcetypes(uc, catalog, version)
    if sourcetypes:
        payload["sourcetypes"] = [row["id"] for row in sourcetypes]
        enrichment["sourcetypes"] = sourcetypes
    vendors = _vendors(uc, catalog, version)
    if vendors:
        payload["vendorProducts"] = [row["id"] for row in vendors]
        enrichment["vendorProducts"] = vendors
    if proposed:
        enrichment["proposedValues"] = proposed
    if enrichment:
        payload["enrichment"] = enrichment
    return payload


def grade_assignment(uc: dict[str, Any], field: str, row: dict[str, Any], catalog: _Catalog) -> str:
    """Grade one assignment. This rubric does not call ``assign_uc``."""
    evidence = str(row.get("evidence") or "")
    owner = str(uc.get("owner") or "").strip()
    if field == "personas" and owner and evidence.strip().casefold() == owner.casefold():
        return "wrong"
    if field in PHRASE_GRADE:
        label = PHRASE_GRADE[field].get(evidence.strip().casefold(), "wrong")
        positive = _positive_text(uc)
        if evidence.casefold() not in positive.casefold():
            return "wrong"
        if label == "correct" and _boilerplate(positive, evidence):
            return "debatable"
        return label
    if field == "sourcetypes":
        narrative, data_sources = _narrative(uc)
        explicit = _explicit_sourcetypes(narrative, data_sources)
        spellings = catalog.index.sourcetype_spellings.get(row["id"], set())
        exact = any(spelling in evidence and spelling.casefold() in explicit for spelling in spellings)
        return "correct" if exact else "wrong"
    if field == "industries":
        raw = str(uc.get("industry") or "").strip()
        key = _norm_industry(raw) if raw else None
        matched = catalog.index.industry_by_norm.get(key) if key else None
        return "correct" if row["id"] == matched else "wrong"
    if field == "vendorProducts":
        text = _field_text(uc, VENDOR_KEYS)
        tokens = catalog.vendor_tokens.get(row["id"], [])
        return "correct" if any(_token_hit(text, token) for token in tokens if len(token) >= 3) else "wrong"
    return "wrong"


def _precision(counts: Counter[str]) -> float | None:
    total = sum(counts.values())
    if total == 0:
        return None
    return round(counts["correct"] / total, 4)


def summarize(paths: list[Path], catalog: _Catalog, version: str) -> dict[str, Any]:
    coverage: Counter[str] = Counter()
    confidence: Counter[str] = Counter()
    graded: dict[str, Counter[str]] = {field: Counter() for field in FIELDS}
    proposed: list[dict[str, str]] = []
    no_outcome: list[str] = []
    no_area: list[str] = []
    samples: list[dict[str, str]] = []
    for path in paths:
        uc = _load(path)
        uc_id = str(uc.get("id") or path.stem)
        payload = assign_uc(uc, catalog, version)
        enrichment = payload.get("enrichment") or {}
        if "businessOutcomes" not in payload:
            no_outcome.append(uc_id)
        if "businessAreas" not in payload:
            no_area.append(uc_id)
        for item in enrichment.get("proposedValues") or []:
            proposed.append({"uc": uc_id, **item})
        for field in FIELDS:
            rows = enrichment.get(field) or []
            if rows:
                coverage[field] += 1
            for row in rows:
                confidence[f"{row['confidence']:.2f}"] += 1
                label = grade_assignment(uc, field, row, catalog)
                graded[field][label] += 1
                if len(samples) < 20 and version == "strict-1":
                    samples.append(
                        {
                            "uc": uc_id,
                            "title": str(uc.get("title") or ""),
                            "field": field,
                            "id": row["id"],
                            "evidence": row["evidence"],
                            "grade": label,
                        }
                    )
    precision = {field: _precision(graded[field]) for field in FIELDS}
    return {
        "version": version,
        "coverage": {field: {"assigned": coverage[field], "rate": round(coverage[field] / len(paths), 4)} for field in FIELDS},
        "confidence": dict(sorted(confidence.items())),
        "graded": {field: dict(graded[field]) for field in FIELDS},
        "precision": precision,
        "proposedValues": proposed,
        "noHonestOutcome": no_outcome,
        "noHonestArea": no_area,
        "evidenceSample": samples,
    }


def bars_hold(summary: dict[str, Any]) -> bool:
    precision = summary["precision"]
    return all(precision.get(field) is not None and precision[field] >= bar for field, bar in BARS.items())


def insert_enrichment(text: str, payload: dict[str, Any]) -> str:
    """Insert enrichment keys before the final brace. Other bytes stay put."""
    original = json.loads(text)
    for key in payload:
        if key in original:
            raise ValueError(f"refusing to overwrite {key}")
    stripped = text.rstrip()
    if not stripped.endswith("}"):
        raise ValueError("sidecar does not end with an object")
    ordered = {key: payload[key] for key in INSERT_ORDER if key in payload}
    rendered = json.dumps(ordered, indent=2, ensure_ascii=False)
    interior = rendered[1:-1].strip("\n")
    prefix = stripped[:-1].rstrip()
    updated = prefix + ",\n" + interior + "\n}\n"
    if not updated.startswith(prefix):
        raise ValueError("insert changed the existing sidecar bytes")
    parsed = json.loads(updated)
    for key, value in original.items():
        if parsed[key] != value:
            raise ValueError(f"insert changed {key}")
    for key, value in ordered.items():
        if parsed[key] != value:
            raise ValueError(f"insert dropped {key}")
    return updated


def write_assignments(paths: list[Path], catalog: _Catalog, version: str = "strict-1") -> int:
    written = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        uc = json.loads(text)
        if any(key in uc for key in (*FIELDS, "enrichment")):
            continue
        payload = assign_uc(uc, catalog, version)
        if not payload:
            continue
        path.write_text(insert_enrichment(text, payload), encoding="utf-8")
        written += 1
    return written


def build_report(content: Path | None = None, registries: Path | None = None) -> dict[str, Any]:
    root = content or CONTENT
    catalog = _Catalog(registries or REGISTRIES)
    paths = pilot_paths(root)
    per_category = Counter(path.parent.name for path in paths)
    loose = summarize(paths, catalog, "loose-1")
    strict = summarize(paths, catalog, "strict-1")
    return {
        "seed": SEED,
        "sampleSize": len(paths),
        "perCategory": dict(sorted(per_category.items())),
        "includesCat18": any(path.parent.name.startswith("cat-18-") for path in paths),
        "includesCat25": any(path.parent.name.startswith("cat-25-") for path in paths),
        "before": loose,
        "after": strict,
        "bars": BARS,
        "barsHold": bars_hold(strict),
        "review": (
            "The grader scored every loose-1 assignment, at least 30 per field, "
            "as correct, debatable, or wrong. Precision uses only correct. "
            "strict-1 was then run on the same 300. Every remaining strict "
            "assignment was graded again. Personas and outcomes stay sparse "
            "because most sidecars never use a specific registry phrase; those "
            "use cases are flagged instead of given a guessed value."
        ),
        "tightening": (
            "strict-1 drops generic and wrong phrases, ignores boilerplate "
            "incident-response wording, copies no owner into personas, takes "
            "industries only from the industry field, and keeps a sourcetype "
            "or vendor only when the sidecar states it explicitly."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=None, help="Write the pilot grade report JSON.")
    parser.add_argument("--write", action="store_true", help="Insert strict-1 enrichment into the pilot sidecars.")
    parser.add_argument("--content", type=Path, default=None)
    parser.add_argument("--registries", type=Path, default=None)
    args = parser.parse_args(argv)
    report = build_report(args.content, args.registries)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"pilot sample={report['sampleSize']} barsHold={report['barsHold']}")
    for label in ("before", "after"):
        precision = report[label]["precision"]
        print(label, " ".join(f"{field}={precision[field]}" for field in FIELDS))
    if args.write:
        if not report["barsHold"]:
            print("strict-1 missed a precision bar; sidecars were not changed")
            return 2
        catalog = _Catalog(args.registries or REGISTRIES)
        written = write_assignments(pilot_paths(args.content), catalog, "strict-1")
        issues = audit_tree(args.content, args.registries)
        print(f"wrote {written} sidecars; audit issues={len(issues)}")
        if issues:
            for issue in issues[:20]:
                print(issue)
            return 1
    return 0 if report["barsHold"] or not args.write else 2


if __name__ == "__main__":
    raise SystemExit(main())
