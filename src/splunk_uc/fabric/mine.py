#!/usr/bin/env python3
"""Mine fabric registries from the use-case sidecars.

Spellings that clearly name the same thing become aliases. A value that
cannot be placed is written to ``registries/ambiguous.json`` and is not
given a canonical id. No use-case file is edited.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from splunk_uc.fabric.extract import (
    as_str_list,
    classify_sourcetype_token,
    datamodel_refs,
    dotted_fields,
    quoted_datasources,
    sourcetype_candidates,
    splunkbase_ids,
    ta_tokens,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
REGISTRIES = REPO_ROOT / "registries"

# CIM data model names from the Splunk CIM manual. The key is the
# normalised spelling (lowercase, underscores). Unknown sidecar spellings
# are not mapped onto this list.
CIM_MODELS: dict[str, str] = {
    "alerts": "Alerts",
    "application_state": "Application_State",
    "authentication": "Authentication",
    "certificates": "Certificates",
    "change": "Change",
    "change_analysis": "Change",
    "compute_inventory": "Compute_Inventory",
    "data_access": "Data_Access",
    "databases": "Databases",
    "dlp": "DLP",
    "email": "Email",
    "endpoint": "Endpoint",
    "interprocess_messaging": "Interprocess_Messaging",
    "intrusion_detection": "Intrusion_Detection",
    "inventory": "Inventory",
    "jvm": "JVM",
    "malware": "Malware",
    "network_resolution": "Network_Resolution",
    "network_sessions": "Network_Sessions",
    "network_traffic": "Network_Traffic",
    "performance": "Performance",
    "splunk_audit": "Splunk_Audit",
    "ticket_management": "Ticket_Management",
    "updates": "Updates",
    "vulnerabilities": "Vulnerabilities",
    "web": "Web",
}

# Dataset node -> parent model. Only nodes named in the CIM manual.
# A Dataset.field token whose dataset is not here is listed, not guessed.
DATASET_PARENT: dict[str, str] = {
    "all_traffic": "Network_Traffic",
    "traffic": "Network_Traffic",
    "allowed_traffic": "Network_Traffic",
    "blocked_traffic": "Network_Traffic",
    "authentication": "Authentication",
    "failed_authentication": "Authentication",
    "successful_authentication": "Authentication",
    "all_changes": "Change",
    "account_management": "Change",
    "endpoint": "Endpoint",
    "processes": "Endpoint",
    "filesystem": "Endpoint",
    "registry": "Endpoint",
    "services": "Endpoint",
    "ports": "Endpoint",
    "all_email": "Email",
    "filtering": "Email",
    "ids_attacks": "Intrusion_Detection",
    "all_malware": "Malware",
    "malware_operations": "Malware",
    "dns": "Network_Resolution",
    "all_sessions": "Network_Sessions",
    "session_end": "Network_Sessions",
    "session_start": "Network_Sessions",
    "web": "Web",
    "proxy": "Web",
    "vulnerabilities": "Vulnerabilities",
    "updates": "Updates",
    "inventory": "Inventory",
    "user_inventory": "Inventory",
    "os": "Inventory",
    "compute": "Compute_Inventory",
    "certificates": "Certificates",
    "alerts": "Alerts",
    "ticket_management": "Ticket_Management",
    "all_performance": "Performance",
    "cpu": "Performance",
    "memory": "Performance",
    "storage": "Performance",
    "network": "Performance",
    "databases": "Databases",
    "dlp": "DLP",
    "data_access": "Data_Access",
    "application_state": "Application_State",
}

CIM_FIELDS = frozenset(
    {
        "action",
        "app",
        "authentication_method",
        "availability",
        "bytes",
        "bytes_in",
        "bytes_out",
        "category",
        "command",
        "cpu_load_percent",
        "cve",
        "dest",
        "dest_ip",
        "dest_port",
        "dest_user",
        "direction",
        "dvc",
        "file_hash",
        "file_name",
        "file_path",
        "http_method",
        "http_user_agent",
        "ids_type",
        "mem",
        "mem_used",
        "object",
        "object_category",
        "packets",
        "parent_process",
        "parent_process_name",
        "process",
        "process_name",
        "protocol",
        "reason",
        "response_time",
        "result",
        "severity",
        "severity_id",
        "signature",
        "signature_id",
        "src",
        "src_ip",
        "src_port",
        "src_user",
        "status",
        "storage_used",
        "transport",
        "url",
        "user",
        "user_agent",
        "vendor_product",
    }
)

# Seller concepts. Phrases are matched only to count how often the
# catalogue already uses that language. They are not copied onto use cases
# by this command. Personas are operational roles, not the ``owner`` enum.
OUTCOMES: list[dict[str, Any]] = [
    {
        "id": "lower_security_risk",
        "label": "Lower security risk",
        "phrases": ["security risk", "attack surface", "malicious activity", "compromise"],
    },
    {
        "id": "faster_incident_response",
        "label": "Faster incident response",
        "phrases": ["incident response", "mean time to respond", "investigation time", "triage"],
    },
    {
        "id": "prove_compliance",
        "label": "Prove compliance",
        "phrases": ["audit evidence", "compliance evidence", "regulatory requirement", "control evidence"],
    },
    {
        "id": "reduce_downtime",
        "label": "Reduce downtime",
        "phrases": ["downtime", "unplanned outage", "service disruption", "availability"],
    },
    {
        "id": "protect_sensitive_data",
        "label": "Protect sensitive data",
        "phrases": ["sensitive data", "cardholder data", "personally identifiable", "data loss"],
    },
    {
        "id": "control_privileged_access",
        "label": "Control privileged access",
        "phrases": ["privileged access", "privileged account", "privilege escalation", "admin rights"],
    },
    {
        "id": "detect_fraud",
        "label": "Detect fraud",
        "phrases": ["fraud", "unauthorized transaction", "payment fraud"],
    },
    {
        "id": "improve_service_reliability",
        "label": "Improve service reliability",
        "phrases": ["service reliability", "error rate", "latency", "service health"],
    },
    {
        "id": "reduce_operational_cost",
        "label": "Reduce operational cost",
        "phrases": ["operational cost", "capacity planning", "license consumption", "cloud spend"],
    },
    {
        "id": "contain_threats",
        "label": "Contain threats",
        "phrases": ["containment", "isolate the host", "block the attack", "threat containment"],
    },
    {
        "id": "protect_ot_safety",
        "label": "Protect operational safety",
        "phrases": ["process safety", "safety instrumented", "industrial control", "ot security"],
    },
    {
        "id": "improve_change_safety",
        "label": "Improve change safety",
        "phrases": ["unauthorized change", "configuration drift", "change management", "change window"],
    },
]

AREAS: list[dict[str, Any]] = [
    {
        "id": "security_operations",
        "label": "Security operations",
        "phrases": ["security operations", "soc ", "detection engineering", "threat detection"],
    },
    {
        "id": "network_operations",
        "label": "Network operations",
        "phrases": ["network operations", "routing", "firewall policy", "interface down", "packet loss"],
    },
    {
        "id": "infrastructure_operations",
        "label": "Infrastructure operations",
        "phrases": ["infrastructure operations", "server health", "host down", "disk space", "cpu utilization"],
    },
    {
        "id": "identity_and_access",
        "label": "Identity and access",
        "phrases": ["identity and access", "authentication failure", "single sign-on", "privileged access"],
    },
    {
        "id": "compliance_and_risk",
        "label": "Compliance and risk",
        "phrases": ["compliance", "audit finding", "control failure", "regulatory"],
    },
    {
        "id": "application_performance",
        "label": "Application performance",
        "phrases": ["application performance", "response time", "error rate", "latency"],
    },
    {
        "id": "data_protection",
        "label": "Data protection",
        "phrases": ["data protection", "data loss", "personal data", "cardholder"],
    },
    {
        "id": "cloud_operations",
        "label": "Cloud operations",
        "phrases": ["cloud operations", "cloudtrail", "kubernetes", "serverless"],
    },
    {
        "id": "service_management",
        "label": "Service management",
        "phrases": ["service management", "incident ticket", "sla breach", "change request"],
    },
    {
        "id": "ot_and_safety",
        "label": "OT and safety",
        "phrases": ["operational technology", "scada", "safety instrumented", "industrial protocol"],
    },
    {
        "id": "fraud_and_financial_crime",
        "label": "Fraud and financial crime",
        "phrases": ["fraud", "financial crime", "anti-money", "payment card"],
    },
    {
        "id": "cost_and_capacity",
        "label": "Cost and capacity",
        "phrases": ["capacity", "cloud spend", "license usage", "cost management"],
    },
]

PERSONAS: list[dict[str, Any]] = [
    {
        "id": "soc_analyst",
        "label": "SOC analyst",
        "phrases": ["soc analyst", "security analyst", "tier-1 analyst", "alert queue"],
    },
    {
        "id": "detection_engineer",
        "label": "Detection engineer",
        "phrases": ["detection engineer", "detection content", "saved search", "correlation search"],
    },
    {
        "id": "network_operator",
        "label": "Network operator",
        "phrases": ["network operator", "network engineer", "noc ", "routing change"],
    },
    {
        "id": "platform_engineer",
        "label": "Platform engineer",
        "phrases": ["platform engineer", "system administrator", "infrastructure engineer"],
    },
    {
        "id": "auditor",
        "label": "Auditor",
        "phrases": ["auditor", "audit evidence", "external audit", "control test"],
    },
    {
        "id": "incident_responder",
        "label": "Incident responder",
        "phrases": ["incident responder", "incident response", "containment step", "forensic"],
    },
    {
        "id": "cloud_operator",
        "label": "Cloud operator",
        "phrases": ["cloud operator", "cloud engineer", "cloud administrator"],
    },
    {
        "id": "ot_operator",
        "label": "OT operator",
        "phrases": ["ot operator", "control room", "plant operator", "ics engineer"],
    },
    {
        "id": "service_owner",
        "label": "Service owner",
        "phrases": ["service owner", "service desk", "major incident"],
    },
    {
        "id": "capacity_planner",
        "label": "Capacity planner",
        "phrases": ["capacity planner", "capacity planning", "forecast"],
    },
]


def _text_key(value: str) -> tuple[str, str]:
    """Total order for display strings that differ only by case."""
    return (value.casefold(), value)


def slug(value: str) -> str:
    text = value.strip().casefold().replace(":", "-").replace("_", "-")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "unnamed"


def _norm_cim(value: str) -> str:
    base = value.split("(")[0].strip()
    base = base.replace("-", " ").replace("/", " ")
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").casefold()
    return base


def _norm_industry(value: str) -> str | None:
    text = value.strip().replace("&", " and ")
    text = re.sub(r"\s+", " ", text).strip(" .")
    if not text or len(text) > 80 or "." in text or "\n" in text:
        return None
    return text.casefold()


def _phrase_hit(text: str, phrase: str) -> bool:
    needle = phrase.casefold()
    if needle.endswith(" "):
        return needle in text
    if " " in needle or len(needle) >= 8:
        return needle in text
    return re.search(rf"\b{re.escape(needle)}\b", text) is not None


def _load_equipment() -> list[dict[str, Any]]:
    import importlib.util

    path = REPO_ROOT / "tools" / "build" / "enrichment.py"
    spec = importlib.util.spec_from_file_location("uc_equipment_table", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load equipment table from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.EQUIPMENT)


def _load_splunkbase() -> dict[str, dict[str, Any]]:
    path = REPO_ROOT / "data" / "splunkbase-catalog.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    apps = payload.get("apps") or {}
    return {str(key): value for key, value in apps.items() if isinstance(value, dict)}


def _iter_sidecars(content: Path) -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(content.glob("cat-*/UC-*.json")):
        rows.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return rows


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _ambiguous(counter: Counter[tuple[str, str, str]]) -> dict[str, Any]:
    values = [
        {"kind": kind, "value": value, "reason": reason, "usageCount": count}
        for (kind, value, reason), count in counter.items()
        if value and count > 0
    ]
    values.sort(
        key=lambda item: (
            str(item["kind"]),
            -int(str(item["usageCount"])),
            str(item["value"]),
            str(item["reason"]),
        )
    )
    return {
        "$schema": "../schemas/fabric/ambiguous.schema.json",
        "description": (
            "Observed values that were not given a canonical id. "
            "They are listed so a later edit can place them deliberately."
        ),
        "values": values,
    }


def build_payloads(content: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return registry name -> JSON payload, including ``ambiguous``."""
    root = content or CONTENT
    equipment = _load_equipment()
    catalog = _load_splunkbase()
    equipment_ids = {str(item["id"]) for item in equipment}
    product_kind = {str(item["id"]): str(item.get("kind") or "equipment") for item in equipment}
    ta_to_products: dict[str, set[str]] = defaultdict(set)
    for item in equipment:
        for ta in item.get("tas") or []:
            ta_to_products[str(ta).casefold()].add(str(item["id"]))

    catalog_by_name: dict[str, set[str]] = defaultdict(set)
    for app_id, catalog_row in catalog.items():
        for key in (catalog_row.get("name"), catalog_row.get("displayName")):
            if key:
                catalog_by_name[str(key).casefold()].add(app_id)

    ambiguous: Counter[tuple[str, str, str]] = Counter()
    spelling: dict[str, Counter[str]] = defaultdict(Counter)
    st_ucs: dict[str, set[str]] = defaultdict(set)
    vendor_votes: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    addon_votes: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    cim_votes: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    product_ucs: Counter[str] = Counter()
    model_ucs: dict[str, Counter[str]] = defaultdict(Counter)
    addon_ucs: dict[str, set[str]] = defaultdict(set)
    addon_names: dict[str, Counter[str]] = defaultdict(Counter)
    industry_spellings: dict[str, Counter[str]] = defaultdict(Counter)
    dataset_ucs: Counter[str] = Counter()
    field_ucs: dict[tuple[str, str], set[str]] = defaultdict(set)
    outcome_ucs: dict[str, set[str]] = {item["id"]: set() for item in OUTCOMES}
    area_ucs: dict[str, set[str]] = {item["id"]: set() for item in AREAS}
    persona_ucs: dict[str, set[str]] = {item["id"]: set() for item in PERSONAS}

    for _path, uc in _iter_sidecars(root):
        uc_id = str(uc.get("id", "")).strip()
        if not uc_id:
            continue
        spl = str(uc.get("spl") or "")
        cim_spl = str(uc.get("cimSpl") or "")
        data_sources = str(uc.get("dataSources") or "")
        app = str(uc.get("app") or "")
        kept, rejected = sourcetype_candidates(spl, cim_spl, data_sources)
        quoted, quoted_rejected = quoted_datasources(data_sources)
        for token, reason in rejected + quoted_rejected:
            ambiguous[( "sourcetype", token, reason )] += 1
        tokens = []
        seen_tokens: set[str] = set()
        for token in kept + quoted:
            key = token.casefold()
            if key in seen_tokens:
                continue
            seen_tokens.add(key)
            tokens.append(token)
            spelling[key][token] += 1
            st_ucs[key].add(uc_id)

        equipment_slugs = [item for item in as_str_list(uc.get("equipment")) if item in equipment_ids]
        for slug_id in equipment_slugs:
            product_ucs[slug_id] += 1
        # Splunk platform apps (ES, ITSI, SOAR) are not the device that emits
        # a sourcetype. They stay vendor products for runsOn, and they do not
        # vote on emittedBy.
        emitter_slugs = [item for item in equipment_slugs if product_kind.get(item) == "equipment"]
        if len(emitter_slugs) == 1:
            for token in tokens:
                vendor_votes[token.casefold()][emitter_slugs[0]].add(uc_id)

        for model in as_str_list(uc.get("equipmentModels")):
            placed = False
            for product_id in sorted(equipment_ids, key=len, reverse=True):
                prefix = product_id + "_"
                if model == product_id or model.startswith(prefix):
                    model_name = model[len(prefix) :] if model.startswith(prefix) else model
                    if model_name:
                        model_ucs[product_id][model_name] += 1
                    placed = True
                    break
            if not placed:
                ambiguous[("vendorProduct", model, "equipment-model-without-vendor")] += 1

        sb_ids: list[str] = []
        for sb_app in uc.get("splunkbaseApps") or []:
            if isinstance(sb_app, dict) and sb_app.get("id"):
                sb_ids.append(str(int(sb_app["id"])))
                if sb_app.get("name"):
                    addon_names[str(int(sb_app["id"]))][str(sb_app["name"])] += 1
        for found in splunkbase_ids(app, data_sources):
            sb_ids.append(str(found))
        sb_unique = list(dict.fromkeys(sb_ids))
        for app_id in sb_unique:
            addon_ucs[app_id].add(uc_id)
        if len(sb_unique) == 1:
            for token in tokens:
                addon_votes[token.casefold()][sb_unique[0]].add(uc_id)

        for token in ta_tokens(app, data_sources):
            key = token.casefold()
            products = ta_to_products.get(key, set())
            matched_addons = catalog_by_name.get(key, set())
            if len(products) + len(matched_addons) == 0:
                ambiguous[("addon", token, "ta-token-without-registry-entry")] += 1
            elif len(products) > 1 or len(matched_addons) > 1:
                ambiguous[("addon", token, "ta-token-matches-several-entries")] += 1

        cim_ids: list[str] = []
        for raw in as_str_list(uc.get("cimModels")):
            canonical = CIM_MODELS.get(_norm_cim(raw))
            if canonical is None:
                ambiguous[("cimDataset", raw, "unknown-cim-model")] += 1
                continue
            cim_ids.append(canonical)
            dataset_ucs[slug(canonical)] += 1
        for model_name, dataset_name in datamodel_refs(cim_spl) + datamodel_refs(spl):
            canonical = CIM_MODELS.get(_norm_cim(model_name))
            if canonical is None:
                ambiguous[("cimDataset", model_name, "unknown-cim-model")] += 1
                continue
            cim_ids.append(canonical)
            dataset_ucs[slug(canonical)] += 1
            if dataset_name:
                dataset_ucs[slug(canonical + "-" + dataset_name)] += 1
        cim_unique = list(dict.fromkeys(cim_ids))
        if len(cim_unique) == 1:
            for token in tokens:
                cim_votes[token.casefold()][cim_unique[0]].add(uc_id)

        for raw_field in as_str_list(uc.get("requiredFields")):
            kind, cleaned = classify_sourcetype_token(raw_field) if " " not in raw_field else ("ambiguous", raw_field)
            if "." in raw_field:
                left, right = raw_field.split(".", 1)
                _place_dotted_field(left, right, uc_id, field_ucs, dataset_ucs, ambiguous)
            elif raw_field.casefold() in CIM_FIELDS:
                ambiguous[("cimField", raw_field, "field-without-dataset")] += 1
            else:
                ambiguous[("cimField", raw_field, "unknown-cim-field")] += 1
            del kind, cleaned
        for dataset_name, field_name in dotted_fields(cim_spl) + dotted_fields(spl):
            if field_name.casefold() in CIM_FIELDS or dataset_name.casefold() in DATASET_PARENT:
                _place_dotted_field(dataset_name, field_name, uc_id, field_ucs, dataset_ucs, ambiguous)

        industry = uc.get("industry")
        if isinstance(industry, str) and industry.strip():
            key = _norm_industry(industry)
            if key is None:
                ambiguous[("industry", industry.strip()[:200], "industry-not-a-name")] += 1
            else:
                industry_spellings[key][industry.strip()] += 1

        narrative = " ".join(
            str(uc.get(field) or "")
            for field in ("title", "description", "value", "grandmaExplanation")
        ).casefold()
        for concept, bucket in ((OUTCOMES, outcome_ucs), (AREAS, area_ucs), (PERSONAS, persona_ucs)):
            for item in concept:
                if any(_phrase_hit(narrative, phrase) for phrase in item["phrases"]):
                    bucket[item["id"]].add(uc_id)

    sourcetype_entries: list[dict[str, Any]] = []
    for key, spellings in spelling.items():
        canonical = spellings.most_common(1)[0][0]
        aliases = sorted({name for name in spellings if name != canonical}, key=_text_key)
        entry: dict[str, Any] = {
            "id": _unique_slug(slug(canonical), {item["id"] for item in sourcetype_entries}),
            "canonical": canonical,
            "aliases": aliases,
            "usageCount": len(st_ucs[key]),
        }
        vendors = vendor_votes.get(key, {})
        entry["vendorProduct"] = None
        if len(vendors) == 1:
            product_id, voters = next(iter(vendors.items()))
            if len(voters) >= 2:
                entry["vendorProduct"] = product_id
        elif len(vendors) > 1:
            ambiguous[("sourcetype", canonical, "vendor-conflict")] += 1
        addons = addon_votes.get(key, {})
        entry["addon"] = None
        if len(addons) == 1:
            app_id, voters = next(iter(addons.items()))
            if len(voters) >= 2:
                entry["addon"] = app_id
        elif len(addons) > 1:
            ambiguous[("sourcetype", canonical, "addon-conflict")] += 1
        cims = cim_votes.get(key, {})
        entry["cimDatasets"] = []
        if len(cims) == 1:
            model_name, voters = next(iter(cims.items()))
            if len(voters) >= 2:
                entry["cimDatasets"] = [slug(model_name)]
                dataset_ucs[slug(model_name)] += 0
        elif len(cims) > 1:
            ambiguous[("sourcetype", canonical, "cim-conflict")] += 1
        sourcetype_entries.append(entry)
    sourcetype_entries.sort(key=lambda item: (-int(item["usageCount"]), str(item["id"])))

    vendor_entries = []
    for item in equipment:
        product_id = str(item["id"])
        models = [
            {"id": slug(name), "name": name, "usageCount": count}
            for name, count in sorted(model_ucs.get(product_id, Counter()).items(), key=lambda pair: (-pair[1], pair[0]))
        ]
        aliases = sorted(
            {
                str(item.get("label") or ""),
                *[str(ta) for ta in item.get("tas") or []],
            }
            - {product_id},
            key=_text_key,
        )
        vendor_entries.append(
            {
                "id": product_id,
                "vendor": item.get("vendor") or "",
                "product": item.get("label") or product_id,
                "kind": item.get("kind") or "equipment",
                "aliases": [alias for alias in aliases if alias],
                "models": models,
                "usageCount": int(product_ucs.get(product_id, 0)),
            }
        )
    vendor_entries.sort(key=lambda item: item["id"])

    addon_entries = []
    for app_id, ucs in addon_ucs.items():
        catalog_app = catalog.get(app_id, {})
        names = addon_names.get(app_id, Counter())
        canonical = catalog_app.get("displayName") or (names.most_common(1)[0][0] if names else f"Splunkbase {app_id}")
        aliases = sorted(
            {
                *(str(name) for name in names if str(name) != canonical),
                *([str(catalog_app["name"])] if catalog_app.get("name") and str(catalog_app.get("name")) != canonical else []),
            },
            key=_text_key,
        )
        addon_entries.append(
            {
                "id": app_id,
                "splunkbaseId": int(app_id),
                "name": canonical,
                "folderName": catalog_app.get("name") or "",
                "aliases": aliases,
                "inSplunkbaseCatalog": app_id in catalog,
                "usageCount": len(ucs),
            }
        )
    addon_entries.sort(key=lambda item: (-int(str(item["usageCount"])), str(item["id"])))

    dataset_entries_map: dict[str, dict[str, Any]] = {}
    for model_name in sorted(set(CIM_MODELS.values())):
        dataset_id = slug(model_name)
        dataset_entries_map[dataset_id] = {
            "id": dataset_id,
            "model": model_name,
            "dataset": model_name,
            "usageCount": int(dataset_ucs.get(dataset_id, 0)),
        }
    for dataset_id, count in dataset_ucs.items():
        if dataset_id in dataset_entries_map:
            dataset_entries_map[dataset_id]["usageCount"] = int(count)
            continue
        # dataset ids minted as model-dataset
        parent = _parent_for_dataset_id(dataset_id)
        if parent is None:
            ambiguous[("cimDataset", dataset_id, "dataset-without-known-model")] += count
            continue
        node = dataset_id[len(slug(parent)) + 1 :]
        dataset_entries_map[dataset_id] = {
            "id": dataset_id,
            "model": parent,
            "dataset": node.replace("-", "_"),
            "usageCount": int(count),
        }
    dataset_entries = sorted(dataset_entries_map.values(), key=lambda item: item["id"])

    field_entries = []
    seen_fields: set[str] = set()
    for (dataset_id, field_name), ucs in sorted(field_ucs.items()):
        field_id = slug(dataset_id + "-" + field_name)
        if field_id in seen_fields:
            ambiguous[("cimField", field_name, "field-id-collision")] += len(ucs)
            continue
        seen_fields.add(field_id)
        field_entries.append(
            {
                "id": field_id,
                "name": field_name,
                "dataset": dataset_id,
                "usageCount": len(ucs),
            }
        )

    industry_entries: list[dict[str, Any]] = []
    for key, spellings in industry_spellings.items():
        total = sum(spellings.values())
        if total < 2:
            for surface, count in spellings.items():
                ambiguous[("industry", surface, "industry-seen-once")] += count
            continue
        canonical = spellings.most_common(1)[0][0]
        aliases = sorted({name for name in spellings if name != canonical}, key=_text_key)
        industry_entries.append(
            {
                "id": _unique_slug(slug(canonical), {item["id"] for item in industry_entries}),
                "name": canonical,
                "aliases": aliases,
                "usageCount": total,
            }
        )
    industry_entries.sort(key=lambda item: (-int(item["usageCount"]), str(item["id"])))

    def seller(
        items: list[dict[str, Any]],
        counts: dict[str, set[str]],
        entity_type: str,
        schema_name: str,
    ) -> dict[str, Any]:
        entries = [
            {
                "id": item["id"],
                "label": item["label"],
                "phrases": list(item["phrases"]),
                "usageCount": len(counts[item["id"]]),
            }
            for item in items
        ]
        return {
            "$schema": f"../schemas/fabric/{schema_name}.schema.json",
            "entityType": entity_type,
            "entries": entries,
        }

    return {
        "sourcetypes": {
            "$schema": "../schemas/fabric/sourcetypes.schema.json",
            "entityType": "sourcetype",
            "entries": sourcetype_entries,
        },
        "vendor-products": {
            "$schema": "../schemas/fabric/vendor-products.schema.json",
            "entityType": "vendorProduct",
            "entries": vendor_entries,
        },
        "addons": {
            "$schema": "../schemas/fabric/addons.schema.json",
            "entityType": "addon",
            "entries": addon_entries,
        },
        "cim": {
            "$schema": "../schemas/fabric/cim.schema.json",
            "entityType": "cim",
            "datasets": dataset_entries,
            "fields": field_entries,
        },
        "industries": {
            "$schema": "../schemas/fabric/industries.schema.json",
            "entityType": "industry",
            "entries": industry_entries,
        },
        "business-outcomes": seller(OUTCOMES, outcome_ucs, "businessOutcome", "business-outcomes"),
        "business-areas": seller(AREAS, area_ucs, "businessArea", "business-areas"),
        "personas": seller(PERSONAS, persona_ucs, "persona", "personas"),
        "ambiguous": _ambiguous(ambiguous),
    }


def _parent_for_dataset_id(dataset_id: str) -> str | None:
    for model_name in sorted(set(CIM_MODELS.values()), key=len, reverse=True):
        prefix = slug(model_name) + "-"
        if dataset_id.startswith(prefix):
            return model_name
    return None


def _place_dotted_field(
    left: str,
    right: str,
    uc_id: str,
    field_ucs: dict[tuple[str, str], set[str]],
    dataset_ucs: Counter[str],
    ambiguous: Counter[tuple[str, str, str]],
) -> None:
    if right.casefold() not in CIM_FIELDS and left.casefold() not in DATASET_PARENT and _norm_cim(left) not in CIM_MODELS:
        ambiguous[("cimField", f"{left}.{right}", "unknown-dotted-field")] += 1
        return
    model = CIM_MODELS.get(_norm_cim(left))
    if model is not None:
        dataset_id = slug(model)
    else:
        parent = DATASET_PARENT.get(left.casefold())
        if parent is None:
            ambiguous[("cimField", f"{left}.{right}", "dataset-not-in-cim-manual")] += 1
            return
        dataset_id = slug(parent + "-" + left)
        dataset_ucs[dataset_id] += 0
    if right.casefold() not in CIM_FIELDS:
        ambiguous[("cimField", f"{left}.{right}", "field-not-in-cim-manual")] += 1
        return
    field_ucs[(dataset_id, right)].add(uc_id)
    dataset_ucs[dataset_id] += 0


def _unique_slug(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    number = 2
    while f"{base}-{number}" in taken:
        number += 1
    return f"{base}-{number}"


def write_registries(payloads: dict[str, dict[str, Any]], dest: Path | None = None) -> None:
    root = dest or REGISTRIES
    for name, payload in payloads.items():
        _dump(root / f"{name}.json", payload)


def registries_differ(content: Path | None = None, dest: Path | None = None) -> list[str]:
    """Return registry filenames whose committed JSON differs from a fresh mine."""
    root = dest or REGISTRIES
    payloads = build_payloads(content)
    drifted: list[str] = []
    for name, payload in payloads.items():
        path = root / f"{name}.json"
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
            drifted.append(path.name)
    return drifted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write registries/*.json from the sidecars.")
    parser.add_argument("--check", action="store_true", help="Fail when registries/*.json drift from the sidecars.")
    parser.add_argument("--content", type=Path, default=None)
    parser.add_argument("--dest", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.write:
        payloads = build_payloads(args.content)
        write_registries(payloads, args.dest)
        _print_summary(payloads)
        return 0
    drifted = registries_differ(args.content, args.dest)
    if drifted:
        print("fabric registries drifted: " + ", ".join(drifted))
        return 1
    print("fabric registries match the sidecars")
    return 0


def _print_summary(payloads: dict[str, dict[str, Any]]) -> None:
    for name, payload in payloads.items():
        if name == "cim":
            print(f"{name}: {len(payload['datasets'])} datasets, {len(payload['fields'])} fields")
        elif name == "ambiguous":
            print(f"ambiguous: {len(payload['values'])} values")
        else:
            print(f"{name}: {len(payload['entries'])} entries")


if __name__ == "__main__":
    raise SystemExit(main())
