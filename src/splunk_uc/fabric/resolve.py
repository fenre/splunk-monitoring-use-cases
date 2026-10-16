"""Resolve sidecar facts against the fabric registries.

Explicit facts become ``authored`` edges with confidence 1. Free-text ``app``
tokens and sourcetype spellings that match a registry alias become edges
too. Anything that does not match is recorded on the build report and is
not given an edge.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from splunk_uc.fabric import PREDICATES
from splunk_uc.fabric.extract import (
    _QUOTED,
    _pick,
    as_str_list,
    datamodel_refs,
    quoted_datasources,
    sourcetype_candidates,
    splunkbase_ids,
    ta_tokens,
)
from splunk_uc.fabric.mine import _norm_cim, _norm_industry, slug

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
REGISTRIES = REPO_ROOT / "registries"

_EXAMPLE_CAP = 30


@dataclass
class Fabric:
    """Resolved entities, relationships, and the per-use-case membership used
    by search aliases and the facet index.
    """

    entities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[tuple[str, str, str, str, float]] = field(default_factory=list)
    members: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    pillars: dict[str, str] = field(default_factory=dict)
    presentation_cim: dict[str, list[str]] = field(default_factory=dict)
    rates: dict[str, Any] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)

    def entity_key(self) -> set[tuple[str, str]]:
        return {(entity["type"], entity["id"]) for entity in self.entities}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fold(value: str) -> str:
    return value.strip().casefold()


class _Registries:
    def __init__(self, root: Path) -> None:
        sourcetypes = _load(root / "sourcetypes.json")["entries"]
        vendors = _load(root / "vendor-products.json")["entries"]
        addons = _load(root / "addons.json")["entries"]
        cim = _load(root / "cim.json")
        industries = _load(root / "industries.json")["entries"]
        outcomes = _load(root / "business-outcomes.json")["entries"]
        areas = _load(root / "business-areas.json")["entries"]
        personas = _load(root / "personas.json")["entries"]

        self.sourcetype_by_id = {row["id"]: row for row in sourcetypes}
        self.sourcetype_by_name: dict[str, str] = {}
        for row in sourcetypes:
            self.sourcetype_by_name[_fold(row["canonical"])] = row["id"]
            for alias in row.get("aliases") or []:
                self.sourcetype_by_name.setdefault(_fold(alias), row["id"])

        self.vendor_by_id = {row["id"]: row for row in vendors}
        self.vendor_by_name: dict[str, str] = {}
        for row in vendors:
            for text in [row["id"], row.get("product") or "", row.get("vendor") or ""]:
                if text:
                    self.vendor_by_name.setdefault(_fold(text), row["id"])
            for alias in row.get("aliases") or []:
                self.vendor_by_name.setdefault(_fold(alias), row["id"])

        self.addon_by_id = {row["id"]: row for row in addons}
        self.addon_by_name: dict[str, str] = {}
        for row in addons:
            for text in [row["id"], row.get("name") or "", row.get("folderName") or ""]:
                if text:
                    self.addon_by_name.setdefault(_fold(text), row["id"])
            for alias in row.get("aliases") or []:
                self.addon_by_name.setdefault(_fold(alias), row["id"])

        self.datasets = {row["id"]: row for row in cim["datasets"]}
        self.dataset_by_norm: dict[str, list[str]] = defaultdict(list)
        for row in cim["datasets"]:
            for text in (row["id"], row.get("model") or "", row.get("dataset") or ""):
                key = _norm_cim(text)
                if key and row["id"] not in self.dataset_by_norm[key]:
                    self.dataset_by_norm[key].append(row["id"])

        self.fields = {row["id"]: row for row in cim["fields"]}
        self.fields_by_dataset: dict[str, dict[str, str]] = defaultdict(dict)
        for row in cim["fields"]:
            self.fields_by_dataset[row["dataset"]][_fold(row["name"])] = row["id"]

        self.industry_by_norm: dict[str, dict[str, Any]] = {}
        for row in industries:
            for text in [row["name"], *(row.get("aliases") or [])]:
                key = _norm_industry(text)
                if key:
                    self.industry_by_norm.setdefault(key, row)
        self.industries = industries
        self.outcomes = outcomes
        self.areas = areas
        self.personas = personas
        self.industry_ids = {row["id"] for row in industries}
        self.outcome_ids = {row["id"] for row in outcomes}
        self.area_ids = {row["id"] for row in areas}
        self.persona_ids = {row["id"] for row in personas}
        self.counts = {
            "sourcetype": len(sourcetypes),
            "vendorProduct": len(vendors),
            "addon": len(addons),
            "cimDataset": len(cim["datasets"]),
            "cimField": len(cim["fields"]),
            "industry": len(industries),
            "businessOutcome": len(outcomes),
            "businessArea": len(areas),
            "persona": len(personas),
        }


class _Builder:
    def __init__(self, registries: _Registries) -> None:
        self.reg = registries
        self.entities: dict[tuple[str, str], dict[str, Any]] = {}
        self.edges: dict[tuple[str, str, str], tuple[str, float]] = {}
        self.members: dict[str, dict[str, set[str]]] = {}
        self.pillars: dict[str, str] = {}
        self.presentation_cim: dict[str, set[str]] = {}
        self.unresolved: Counter[str] = Counter()
        self.examples: dict[str, list[str]] = defaultdict(list)
        self.app_with = 0
        self.app_resolved = 0
        self.st_with = 0
        self.st_resolved = 0
        self.uc_ids: set[str] = set()

    def note(self, reason: str, value: str) -> None:
        self.unresolved[reason] += 1
        bucket = self.examples[reason]
        if len(bucket) < _EXAMPLE_CAP and value not in bucket:
            bucket.append(value)

    def add_entity(
        self,
        entity_type: str,
        entity_id: str,
        label: str,
        aliases: list[str] | None = None,
    ) -> None:
        key = (entity_type, entity_id)
        current = self.entities.get(key)
        extra = [alias for alias in (aliases or []) if alias and alias != label]
        if current is None:
            self.entities[key] = {
                "id": entity_id,
                "type": entity_type,
                "label": label,
                "aliases": extra,
            }
            return
        have = set(current["aliases"])
        for alias in extra:
            if alias not in have and alias != current["label"]:
                current["aliases"].append(alias)
                have.add(alias)

    def add_edge(
        self,
        source: str,
        predicate: str,
        target: str,
        provenance: str,
        confidence: float = 1.0,
    ) -> None:
        key = (source, predicate, target)
        current = self.edges.get(key)
        if current is None:
            self.edges[key] = (provenance, confidence)
            return
        if provenance == "authored" and current[0] != "authored":
            self.edges[key] = ("authored", 1.0)

    def membership(self, uc_id: str) -> dict[str, set[str]]:
        return self.members.setdefault(
            uc_id,
            {"sourcetype": set(), "vendorProduct": set(), "addon": set(), "cimDataset": set()},
        )


def _app_signals(uc: dict[str, Any]) -> list[tuple[str, str]]:
    signals: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def push(kind: str, token: str) -> None:
        key = (kind, token.casefold())
        if token and key not in seen:
            seen.add(key)
            signals.append((kind, token))

    for entry in uc.get("splunkbaseApps") or []:
        if isinstance(entry, dict) and entry.get("id"):
            push("splunkbase", str(int(entry["id"])))
    app = str(uc.get("app") or "")
    for token in ta_tokens(app):
        push("ta", token)
    for found in splunkbase_ids(app):
        push("splunkbase", str(found))
    for match in _QUOTED.finditer(app):
        token = _pick(match).strip()
        if token and " " not in token and len(token) >= 3:
            push("quoted", token)
    return signals


def _resolve_uc(builder: _Builder, uc: dict[str, Any]) -> None:
    uc_id = str(uc.get("id") or "").strip()
    if not uc_id:
        return
    builder.uc_ids.add(uc_id)
    title = str(uc.get("title") or uc_id)
    builder.add_entity("usecase", uc_id, title, [f"UC-{uc_id}"])
    pillar = str(uc.get("splunkPillar") or "").strip()
    if pillar:
        builder.pillars[uc_id] = pillar
    member = builder.membership(uc_id)

    spl = str(uc.get("spl") or "")
    cim_spl = str(uc.get("cimSpl") or "")
    data_sources = str(uc.get("dataSources") or "")
    kept, _rejected = sourcetype_candidates(spl, cim_spl, data_sources)
    quoted, _quoted_rejected = quoted_datasources(data_sources)
    tokens: list[str] = []
    seen_tokens: set[str] = set()
    for token in [*kept, *quoted]:
        key = token.casefold()
        if key not in seen_tokens:
            seen_tokens.add(key)
            tokens.append(token)
    if tokens:
        builder.st_with += 1
        missing = False
        for token in tokens:
            st_id = builder.reg.sourcetype_by_name.get(token.casefold())
            if st_id is None:
                missing = True
                builder.note("sourcetype", token)
                continue
            builder.add_edge(uc_id, "uses", st_id, "authored")
            member["sourcetype"].add(st_id)
            row = builder.reg.sourcetype_by_id[st_id]
            if row.get("vendorProduct"):
                member["vendorProduct"].add(row["vendorProduct"])
            if row.get("addon"):
                member["addon"].add(row["addon"])
            for dataset_id in row.get("cimDatasets") or []:
                if dataset_id in builder.reg.datasets:
                    member["cimDataset"].add(dataset_id)
        if not missing:
            builder.st_resolved += 1

    for slug_id in as_str_list(uc.get("equipment")):
        if slug_id in builder.reg.vendor_by_id:
            builder.add_edge(uc_id, "runsOn", slug_id, "authored")
            member["vendorProduct"].add(slug_id)
        else:
            builder.note("vendorProduct", slug_id)

    for model in as_str_list(uc.get("equipmentModels")):
        placed = False
        for product_id in sorted(builder.reg.vendor_by_id, key=len, reverse=True):
            prefix = product_id + "_"
            if model == product_id or model.startswith(prefix):
                builder.add_edge(uc_id, "runsOn", product_id, "authored")
                member["vendorProduct"].add(product_id)
                placed = True
                break
        if not placed:
            builder.note("equipmentModel", model)

    signals = _app_signals(uc)
    if signals:
        builder.app_with += 1
        missing_app = False
        for kind, token in signals:
            if kind == "splunkbase":
                if token in builder.reg.addon_by_id:
                    member["addon"].add(token)
                else:
                    missing_app = True
                    builder.note("addon", token)
                continue
            addon_id = builder.reg.addon_by_name.get(token.casefold())
            vendor_id = builder.reg.vendor_by_name.get(token.casefold())
            if addon_id:
                member["addon"].add(addon_id)
            if vendor_id:
                builder.add_edge(uc_id, "runsOn", vendor_id, "inferred")
                member["vendorProduct"].add(vendor_id)
            if not addon_id and not vendor_id:
                missing_app = True
                builder.note("app", token)
        if not missing_app:
            builder.app_resolved += 1

    industry_raw = str(uc.get("industry") or "").strip()
    if industry_raw:
        key = _norm_industry(industry_raw)
        row = builder.reg.industry_by_norm.get(key) if key else None
        if row is not None:
            builder.add_edge(uc_id, "inIndustry", row["id"], "authored")
        else:
            builder.note("industry", industry_raw[:120])

    datasets: set[str] = set()
    for model_name in as_str_list(uc.get("cimModels")):
        hits = builder.reg.dataset_by_norm.get(_norm_cim(model_name), [])
        if hits:
            datasets.update(hits)
        else:
            builder.note("cimModel", model_name)
    for model_name, dataset_name in datamodel_refs(cim_spl):
        if dataset_name:
            hits = builder.reg.dataset_by_norm.get(_norm_cim(dataset_name), [])
            if not hits:
                hits = builder.reg.dataset_by_norm.get(_norm_cim(f"{model_name}_{dataset_name}"), [])
        else:
            hits = builder.reg.dataset_by_norm.get(_norm_cim(model_name), [])
        if hits:
            datasets.update(hits)
        else:
            builder.note("datamodel", dataset_name or model_name)
    if datasets:
        builder.presentation_cim[uc_id] = set(datasets)
        member["cimDataset"].update(datasets)

    for field_name in as_str_list(uc.get("requiredFields")):
        if not datasets:
            builder.note("field-without-dataset", field_name)
            continue
        linked = False
        folded = field_name.casefold()
        bare = folded.split(".")[-1]
        for dataset_id in datasets:
            field_id = builder.reg.fields_by_dataset.get(dataset_id, {}).get(bare)
            if field_id:
                builder.add_edge(uc_id, "requiresField", field_id, "authored")
                linked = True
        if not linked:
            builder.note("cimField", field_name)

    for raw_pre in as_str_list(uc.get("prerequisiteUseCases")):
        pre = raw_pre[3:] if raw_pre.upper().startswith("UC-") else raw_pre
        if re.fullmatch(r"\d+\.\d+\.\d+", pre):
            builder.add_edge(uc_id, "requires", pre, "authored")
        else:
            builder.note("prerequisite", raw_pre)

    for entry in uc.get("compliance") or []:
        if not isinstance(entry, dict):
            continue
        regulation = str(entry.get("regulation") or "").strip()
        clause = str(entry.get("clause") or "").strip()
        if not regulation or not clause:
            continue
        version = str(entry.get("version") or "").strip()
        control_id = slug("-".join(part for part in (regulation, version, clause) if part))
        label = f"{regulation} {clause}".strip()
        aliases = []
        obligation = str(entry.get("obligationRef") or "").strip()
        if obligation:
            aliases.append(obligation)
        builder.add_entity("complianceControl", control_id, label, aliases)
        builder.add_edge(uc_id, "covers", control_id, "authored")

    _apply_enrichment(builder, uc, uc_id, member)


_ENRICHMENT_LINKS = (
    ("sourcetypes", "uses", "sourcetype"),
    ("vendorProducts", "runsOn", "vendorProduct"),
    ("industries", "inIndustry", "industry"),
    ("businessOutcomes", "servesOutcome", "businessOutcome"),
    ("businessAreas", "inArea", "businessArea"),
    ("personas", "forPersona", "persona"),
)


def _known_ids(reg: _Registries, entity_type: str) -> set[str]:
    if entity_type == "sourcetype":
        return set(reg.sourcetype_by_id)
    if entity_type == "vendorProduct":
        return set(reg.vendor_by_id)
    if entity_type == "industry":
        return reg.industry_ids
    if entity_type == "businessOutcome":
        return reg.outcome_ids
    if entity_type == "businessArea":
        return reg.area_ids
    return reg.persona_ids


def _apply_enrichment(
    builder: _Builder,
    uc: dict[str, Any],
    uc_id: str,
    member: dict[str, set[str]],
) -> None:
    """Turn registry-id lists into edges. Audit-enrichment is the gate."""
    if not any(uc.get(name) for name, _predicate, _entity_type in _ENRICHMENT_LINKS):
        return
    enrichment = uc.get("enrichment") if isinstance(uc.get("enrichment"), dict) else {}
    for field_name, predicate, entity_type in _ENRICHMENT_LINKS:
        known = _known_ids(builder.reg, entity_type)
        assignments = enrichment.get(field_name) if isinstance(enrichment.get(field_name), list) else []
        by_id: dict[str, dict[str, Any]] = {}
        for item in assignments:
            if isinstance(item, dict) and item.get("id"):
                by_id[str(item["id"])] = item
        for entity_id in as_str_list(uc.get(field_name)):
            if entity_id not in known:
                builder.note(field_name, entity_id)
                continue
            meta = by_id.get(entity_id, {})
            source = str(meta.get("source") or "authored")
            provenance = source if source in ("authored", "inferred") else "inferred"
            try:
                confidence = float(meta.get("confidence", 1.0))
            except (TypeError, ValueError):
                confidence = 1.0
            if provenance == "authored":
                confidence = 1.0
            builder.add_edge(uc_id, predicate, entity_id, provenance, confidence)
            if entity_type == "sourcetype":
                member["sourcetype"].add(entity_id)
            elif entity_type == "vendorProduct":
                member["vendorProduct"].add(entity_id)


def _registry_entities(builder: _Builder) -> None:
    reg = builder.reg
    for row in reg.sourcetype_by_id.values():
        builder.add_entity(
            "sourcetype",
            row["id"],
            row["canonical"],
            [row["canonical"], *(row.get("aliases") or [])],
        )
        if row.get("addon") and row["addon"] in reg.addon_by_id:
            builder.add_edge(row["id"], "producedBy", row["addon"], "inferred")
        if row.get("vendorProduct") and row["vendorProduct"] in reg.vendor_by_id:
            builder.add_edge(row["id"], "emittedBy", row["vendorProduct"], "inferred")
        for dataset_id in row.get("cimDatasets") or []:
            if dataset_id in reg.datasets:
                builder.add_edge(row["id"], "mapsTo", dataset_id, "inferred")
    for row in reg.vendor_by_id.values():
        builder.add_entity(
            "vendorProduct",
            row["id"],
            row.get("product") or row["id"],
            [row["id"], row.get("vendor") or "", row.get("product") or "", *(row.get("aliases") or [])],
        )
    for row in reg.addon_by_id.values():
        builder.add_entity(
            "addon",
            row["id"],
            row.get("name") or row["id"],
            [row["id"], row.get("folderName") or "", row.get("name") or "", *(row.get("aliases") or [])],
        )
    for row in reg.datasets.values():
        label = row["dataset"] if row["dataset"] != row["model"] else row["model"]
        builder.add_entity("cimDataset", row["id"], label, [row["model"], row["dataset"]])
    for row in reg.fields.values():
        builder.add_entity("cimField", row["id"], row["name"], [row["name"]])
        if row["dataset"] in reg.datasets:
            builder.add_edge(row["id"], "partOf", row["dataset"], "inferred")
    for row in reg.industries:
        builder.add_entity("industry", row["id"], row["name"], [row["name"], *(row.get("aliases") or [])])
    for row in reg.outcomes:
        builder.add_entity("businessOutcome", row["id"], row["label"], [row["label"]])
    for row in reg.areas:
        builder.add_entity("businessArea", row["id"], row["label"], [row["label"]])
    for row in reg.personas:
        builder.add_entity("persona", row["id"], row["label"], [row["label"]])


def _rate(resolved: int, total: int) -> float:
    if total <= 0:
        return 1.0
    return round(resolved / total, 6)


def resolve(
    *,
    content: Path = CONTENT,
    registries: Path = REGISTRIES,
) -> Fabric:
    """Resolve every sidecar under ``content`` against ``registries``."""
    reg = _Registries(registries)
    builder = _Builder(reg)
    paths = sorted(content.glob("cat-*/UC-*.json"))
    known_ids: set[str] = set()
    loaded: list[dict[str, Any]] = []
    for path in paths:
        uc = json.loads(path.read_text(encoding="utf-8"))
        loaded.append(uc)
        if uc.get("id"):
            known_ids.add(str(uc["id"]))
    for uc in loaded:
        _resolve_uc(builder, uc)
    # Drop requires edges whose target file does not exist. The id shape was
    # checked earlier; existence is a second fact, and a missing target is
    # a report entry rather than a dangling edge.
    dangling = [
        key
        for key in builder.edges
        if key[1] == "requires" and key[2] not in known_ids
    ]
    for key in dangling:
        builder.note("prerequisite", key[2])
        del builder.edges[key]
    _registry_entities(builder)

    entities = sorted(
        builder.entities.values(),
        key=lambda row: (row["type"], row["id"]),
    )
    for entity in entities:
        entity["aliases"] = sorted(
            {alias for alias in entity["aliases"] if alias and alias != entity["label"]},
            key=lambda value: (value.casefold(), value),
        )
    relationships = sorted(
        (
            (source, predicate, target, provenance, confidence)
            for (source, predicate, target), (provenance, confidence) in builder.edges.items()
        ),
        key=lambda row: row[:4],
    )
    # Predicates we emit must be the official set. A typo here is a bug.
    unknown = sorted({row[1] for row in relationships if row[1] not in PREDICATES})
    if unknown:
        raise RuntimeError(f"resolver emitted unknown predicates: {unknown}")

    members = {
        uc_id: {key: sorted(values) for key, values in groups.items()}
        for uc_id, groups in sorted(builder.members.items())
    }
    rates = {
        "definition": (
            "app rate: sidecars with at least one app signal (Splunkbase id, "
            "TA token, or backtick-quoted token) whose every signal matches an "
            "add-on or vendor-product alias. sourcetype rate: sidecars with at "
            "least one explicit sourcetype token whose every token matches the "
            "sourcetype registry."
        ),
        "ucCount": len(paths),
        "appWithSignal": builder.app_with,
        "appResolved": builder.app_resolved,
        "appRate": _rate(builder.app_resolved, builder.app_with),
        "sourcetypeWithSignal": builder.st_with,
        "sourcetypeResolved": builder.st_resolved,
        "sourcetypeRate": _rate(builder.st_resolved, builder.st_with),
    }
    report = {
        "unresolvedCounts": dict(sorted(builder.unresolved.items())),
        "examples": {key: builder.examples[key] for key in sorted(builder.examples)},
    }
    return Fabric(
        entities=entities,
        relationships=relationships,
        members=members,
        pillars=builder.pillars,
        presentation_cim={
            uc_id: sorted(values) for uc_id, values in sorted(builder.presentation_cim.items())
        },
        rates=rates,
        report=report,
    )


def invariant_errors(fabric: Fabric, registries: Path = REGISTRIES) -> list[str]:
    """Return human-readable failures of the fabric consistency rules."""
    errors: list[str] = []
    reg = _Registries(registries)
    counts = Counter(entity["type"] for entity in fabric.entities)
    if counts["usecase"] != fabric.rates.get("ucCount"):
        errors.append(
            f"usecase entities {counts['usecase']} != UC files {fabric.rates.get('ucCount')}"
        )
    for entity_type, expected in reg.counts.items():
        if counts[entity_type] != expected:
            errors.append(
                f"{entity_type} entities {counts[entity_type]} != registry length {expected}"
            )
    keys = fabric.entity_key()
    for source, predicate, target, _provenance, _confidence in fabric.relationships:
        if predicate not in PREDICATES:
            errors.append(f"unknown predicate {predicate}")
            continue
        source_type, target_type = PREDICATES[predicate]
        if (source_type, source) not in keys:
            errors.append(f"{predicate} source missing: {source_type}:{source}")
        if (target_type, target) not in keys:
            errors.append(f"{predicate} target missing: {target_type}:{target}")
    return errors
