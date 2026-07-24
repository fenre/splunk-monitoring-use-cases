#!/usr/bin/env python3
"""Quality lift: adapt verified cat-22 exemplars onto the 46 gap-closure UCs.

Clones depth (SPL, detailedImplementation, knownFalsePositives, references,
controlTest, assurance) from verified templates while preserving each gap UC's
identity, title, clause mapping, and prerequisite graph.

Run from repo root:
    python3 scripts/upgrade_compliance_gap_closure.py
    python3 scripts/upgrade_compliance_gap_closure.py --check
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(REPO_ROOT, "content", "cat-22-regulatory-compliance")

# target_uc_id -> verified template_uc_id
TEMPLATE_MAP: dict[str, str] = {
    # TSA Surface (22.56.29–46)
    "22.56.29": "22.56.2",
    "22.56.30": "22.56.7",
    "22.56.31": "22.56.8",
    "22.56.32": "22.56.18",
    "22.56.33": "22.56.2",
    "22.56.34": "22.56.7",
    "22.56.35": "22.56.3",
    "22.56.36": "22.56.4",
    "22.56.37": "22.56.5",
    "22.56.38": "22.56.6",
    "22.56.39": "22.56.8",
    "22.56.40": "22.56.25",
    "22.56.41": "22.56.2",
    "22.56.42": "22.56.18",
    "22.56.43": "22.56.16",
    "22.56.44": "22.56.25",
    "22.56.45": "22.56.26",
    "22.56.46": "22.56.7",
    # SG Cyber Act (22.57.16–24)
    "22.57.16": "22.57.3",
    "22.57.17": "22.57.2",
    "22.57.18": "22.57.5",
    "22.57.19": "22.56.2",
    "22.57.20": "22.57.2",
    "22.57.21": "22.57.1",
    "22.57.22": "22.56.4",
    "22.57.23": "22.52.18",
    "22.57.24": "22.57.6",
    # SOCI (22.52.29–35)
    "22.52.29": "22.52.9",
    "22.52.30": "22.52.10",
    "22.52.31": "22.56.3",
    "22.52.32": "22.52.1",
    "22.52.33": "22.52.1",
    "22.52.34": "22.56.3",
    "22.52.35": "22.56.20",
    # CLC/TS 50701 (22.55.29–33)
    "22.55.29": "22.55.11",
    "22.55.30": "22.55.11",
    "22.55.31": "22.55.18",
    "22.55.32": "22.55.5",
    "22.55.33": "22.55.4",
    # IEC 61511 (22.63.8–9)
    "22.63.8": "22.63.1",
    "22.63.9": "22.63.4",
    # Singletons
    "22.53.29": "22.53.20",
    "22.62.9": "22.62.6",
    "22.61.13": "22.61.12",
    "22.58.9": "22.58.3",
    "22.59.18": "22.55.15",
}

# Per-target lookup renames (template primary lookup -> gap-closure lookup)
LOOKUP_RENAMES: dict[str, dict[str, str]] = {
    "22.56.29": {"tsa_cc_roster_lookup": "tsa_freight_cc_roster_lookup"},
    "22.56.30": {"tsa_pipeline_cirp_exercise_lookup": "tsa_freight_cirp_exercise_lookup"},
    "22.56.31": {"tsa_pipeline_cap_lookup": "tsa_freight_vuln_assessment_lookup"},
    "22.56.32": {"tsa_cip_version_lookup": "tsa_freight_cip_attestation_lookup"},
    "22.56.33": {"tsa_cc_roster_lookup": "tsa_passenger_cc_roster_lookup"},
    "22.56.34": {"tsa_pipeline_cirp_exercise_lookup": "tsa_passenger_cirp_exercise_lookup"},
    "22.56.35": {
        "tsa_pipeline_zones_lookup": "tsa_passenger_zones_lookup",
        "tsa_pipeline_approved_flows_lookup": "tsa_passenger_approved_flows_lookup",
    },
    "22.56.36": {"tsa_pipeline_account_lookup": "tsa_passenger_access_lookup"},
    "22.56.37": {"tsa_pipeline_threat_categories_lookup": "tsa_passenger_monitoring_lookup"},
    "22.56.38": {"tsa_pipeline_patch_lookup": "tsa_passenger_patch_lookup"},
    "22.56.39": {"tsa_pipeline_cap_lookup": "tsa_passenger_csas_lookup"},
    "22.56.40": {
        "tsa_change_asset_lookup": "tsa_passenger_config_lookup",
        "tsa_change_exception_lookup": "tsa_passenger_config_exception_lookup",
    },
    "22.56.41": {"tsa_cc_roster_lookup": "tsa_surface_aco_lookup"},
    "22.56.42": {"tsa_cip_version_lookup": "tsa_pipeline_cip_attestation_lookup"},
    "22.56.43": {"tsa_vendor_session_lookup": "tsa_pipeline_supply_chain_lookup"},
    "22.56.44": {
        "tsa_change_asset_lookup": "tsa_pipeline_config_lookup",
        "tsa_change_exception_lookup": "tsa_pipeline_config_exception_lookup",
    },
    "22.56.45": {},
    "22.56.46": {"tsa_pipeline_cirp_exercise_lookup": "tsa_pipeline_recovery_test_lookup"},
    "22.57.16": {"csa_ccop_control_lookup": "csa_sg_ca_s10_lookup"},
    "22.57.17": {},
    "22.57.18": {"csa_audit_lookup": "csa_sg_ca_s19_lookup"},
    "22.57.19": {"tsa_cc_roster_lookup": "csa_sg_cii_reg_3_lookup"},
    "22.57.20": {},
    "22.57.21": {
        "csa_cii_designation_lookup": "csa_sg_csa_coc_asset_mgmt_lookup",
        "csa_cii_scope_change_lookup": "csa_sg_csa_coc_asset_mgmt_changes_lookup",
    },
    "22.57.22": {"tsa_pipeline_account_lookup": "csa_sg_csa_coc_access_control_lookup"},
    "22.57.23": {"supply_chain_lookup": "csa_sg_csa_coc_supply_chain_lookup"},
    "22.57.24": {"csa_exercise_lookup": "csa_sg_csa_coc_business_continuity_lookup"},
    "22.52.29": {"sons_exercise_lookup": "soci_bc_exercise_lookup"},
    "22.52.30": {"sons_vuln_assessment_lookup": "soci_ecso_vuln_lookup"},
    "22.52.31": {
        "tsa_pipeline_zones_lookup": "soci_ot_zones_lookup",
        "tsa_pipeline_approved_flows_lookup": "soci_ot_approved_flows_lookup",
    },
    "22.52.32": {
        "soci_inscope_assets_lookup": "soci_ot_asset_inventory_lookup",
        "soci_correction_window_lookup": "soci_ot_inventory_exception_lookup",
    },
    "22.52.33": {
        "soci_inscope_assets_lookup": "soci_data_residency_lookup",
        "soci_correction_window_lookup": "soci_data_residency_exception_lookup",
    },
    "22.52.34": {
        "tsa_pipeline_zones_lookup": "soci_ot_encryption_lookup",
        "tsa_pipeline_approved_flows_lookup": "soci_ot_encryption_flows_lookup",
    },
    "22.52.35": {"tsa_log_source_lookup": "soci_audit_retention_lookup"},
    "22.55.29": {"rail_patch_lookup": "rail50701_c12_1_lookup"},
    "22.55.30": {"rail_patch_lookup": "rail50701_c12_2_lookup"},
    "22.55.31": {"rail_safety_coord_lookup": "rail50701_c12_3_lookup"},
    "22.55.32": {"rail_threat_scenario_lookup": "rail50701_annex_a_lookup"},
    "22.55.33": {
        "rail_zoneconduit_lookup": "rail50701_annex_d_lookup",
        "rail_risk_assessment_lookup": "rail50701_annex_d_risk_lookup",
        "rail_threat_scenario_lookup": "rail50701_annex_d_threat_lookup",
    },
    "22.63.8": {"iec_61511_sis_lifecycle_register_lookup": "iec61511_safety_register_lookup"},
    "22.63.9": {
        "iec_61511_sif_proof_test_register_lookup": "iec61511_om_competence_lookup",
        "iec_61511_proof_test_event_lookup": "iec61511_om_training_event_lookup",
    },
    "22.53.29": {"awia_rra_methodology_lookup": "awia_rra_methodology_lookup"},
    "22.62.9": {"vasp_customer_kyc_lookup": "certin_kyc_retention_lookup"},
    "22.61.13": {"cn_csl_log_retention_lookup": "csl_log_retention_lookup"},
    "22.58.9": {
        "lpm_pssi_mcas_controls_lookup": "fr_lpm_siiv_rules_lookup",
        "lpm_pssi_mcas_derogation_lookup": "fr_lpm_siiv_derogation_lookup",
    },
    "22.59.18": {"rail_supplier_deliverables_lookup": "imo_supply_chain_lookup"},
}

# Additional phrase substitutions per target (applied after ID/clause swaps)
EXTRA_SUBS: dict[str, dict[str, str]] = {
    "22.56.29": {
        "Pipeline CC": "Freight Rail CC",
        "pipeline CC": "freight rail CC",
        "TSA-SD-P-2021-01-s3": "TSA-SD-1580-82-2022-01-s3",
        "Pipeline-2021-01B": "SD-1580-82-2022-01",
        "Pipeline CC + Alternate": "Freight Rail CC + Alternate",
    },
    "22.56.33": {
        "Pipeline CC": "Passenger Rail CC",
        "pipeline CC": "passenger rail CC",
        "TSA-SD-P-2021-01-s3": "TSA-SD-1582-2022-01-s3",
        "Pipeline-2021-01B": "SD-1582-2022-01",
        "Pipeline CC + Alternate": "Passenger Rail CC + Alternate",
    },
    "22.56.41": {
        "Cybersecurity Coordinator": "Authorized Compliance Official (ACO)",
        "CC + Alternate": "ACO designation",
        "cc_name": "aco_name",
        "cc_role": "aco_role",
        "cc_phone": "aco_phone",
        "cc_email": "aco_email",
        "alternate_name": "deputy_aco_name",
        "TSA-SD-P-2021-01-s3": "TSA-SCAS-aco-designation",
    },
    "22.57.19": {
        "Cybersecurity Coordinator": "Cybersecurity Officer",
        "CC + Alternate": "CSO + Alternate CSO",
        "cc_name": "cso_name",
        "TSA-SD-P-2021-01-s3": "SG-CII-Reg-3",
        "tsa_freight_cc_roster_lookup": "csa_sg_cii_reg_3_lookup",
    },
    "22.57.17": {"SG-CA-s14": "SG-CA-s14(1)", "CSA-CII-s14": "SG-CA-s14(1)"},
    "22.57.20": {"SG-CA-s14": "SG-CII-Reg-5", "CSA-CII-s14": "SG-CII-Reg-5"},
    "22.57.16": {"SG-CA-s11": "SG-CA-s10", "CSA-CII-s11": "SG-CA-s10"},
    "22.53.29": {"AWIA-EPA-vsat": "AWIA-EPA-vsat-j100"},
    "22.58.9": {
        "FR-ANSSI-rule-governance-cyber-officer": "FR-Decret-2015-351",
        "LPM-PSSI-MCAS-Art-R1332-41-2": "FR-Decret-2015-351",
    },
    "22.61.13": {"CSL-Art-21": "CSL-Art-21-3", "cn_csl_clause=\"CSL-Art-21\"": "cn_csl_clause=\"CSL-Art-21-3\""},
    "22.56.37": {"tsa_pipeline": "tsa_passenger", "Pipeline detection": "Passenger Rail detection"},
}


def _load_uc(uc_id: str) -> dict[str, Any]:
    path = os.path.join(CONTENT, f"UC-{uc_id}.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _uc_id_underscore(uc_id: str) -> str:
    return uc_id.replace(".", "_")


def _replace_id_safe(text: str, old_id: str, new_id: str) -> str:
    """Replace UC IDs without corrupting IDs that share a numeric prefix (22.56.2 vs 22.56.29)."""
    escaped = re.escape(old_id)
    pattern = rf"(?<![0-9.]){escaped}(?![0-9])"
    return re.sub(pattern, new_id, text)


def _deep_replace(obj: Any, replacements: dict[str, str], id_pairs: list[tuple[str, str]] | None = None) -> Any:
    if isinstance(obj, str):
        out = obj
        if id_pairs:
            for old_id, new_id in id_pairs:
                out = _replace_id_safe(out, old_id, new_id)
        # Longest keys first to avoid partial replacement collisions
        for old, new in sorted(replacements.items(), key=lambda kv: len(kv[0]), reverse=True):
            if old in (p[0] for p in (id_pairs or [])):
                continue
            out = out.replace(old, new)
        return out
    if isinstance(obj, list):
        return [_deep_replace(item, replacements, id_pairs) for item in obj]
    if isinstance(obj, dict):
        return {k: _deep_replace(v, replacements, id_pairs) for k, v in obj.items()}
    return obj


def _build_replacements(
    target_id: str,
    template_id: str,
    scaffold: dict[str, Any],
    template: dict[str, Any],
) -> dict[str, str]:
    repl: dict[str, str] = {}
    id_pairs: list[tuple[str, str]] = [(template_id, target_id)]

    repl[_uc_id_underscore(template_id)] = _uc_id_underscore(target_id)

    # Clause / obligation from scaffold (authoritative for gap closure)
    t_comp = template.get("compliance", [{}])[0]
    s_comp = scaffold.get("compliance", [{}])[0]
    t_clause = t_comp.get("clause", "")
    s_clause = s_comp.get("clause", "")
    if t_clause and s_clause and t_clause != s_clause:
        repl[t_clause] = s_clause
    t_ob = t_comp.get("obligationRef", "")
    s_ob = s_comp.get("obligationRef", "")
    if t_ob and s_ob and t_ob != s_ob:
        repl[t_ob] = s_ob

    # Evidence / audit markers
    if t_clause and s_clause:
        repl[f'tsa_sd_clause="{t_clause}"'] = f'tsa_sd_clause="{s_clause}"'
        repl[f'csa_clause="{t_clause}"'] = f'csa_clause="{s_clause}"'
        repl[f'soci_clause="{t_clause}"'] = f'soci_clause="{s_clause}"'
        repl[f'clause={t_clause}'] = f'clause={s_clause}'
        repl[f",clause={t_clause}"] = f",clause={s_clause}"

    # Lookup renames
    for old, new in LOOKUP_RENAMES.get(target_id, {}).items():
        repl[old] = new

    # Extra phrase substitutions
    for old, new in EXTRA_SUBS.get(target_id, {}).items():
        repl[old] = new

    return repl


def _merge_compliance(
    adapted_template_comp: dict[str, Any],
    scaffold_comp: dict[str, Any],
) -> dict[str, Any]:
    """Keep scaffold identity fields; lift assurance depth from adapted template."""
    merged = copy.deepcopy(scaffold_comp)
    for key in (
        "assurance",
        "assurance_rationale",
        "controlObjective",
        "evidenceArtifact",
    ):
        if key in adapted_template_comp:
            merged[key] = adapted_template_comp[key]
    return merged


def upgrade_one(target_id: str) -> dict[str, Any]:
    template_id = TEMPLATE_MAP[target_id]
    template = _load_uc(template_id)
    scaffold = _load_uc(target_id)

    repl = _build_replacements(target_id, template_id, scaffold, template)
    id_pairs = [(template_id, target_id)]
    doc = _deep_replace(copy.deepcopy(template), repl, id_pairs)

    # Identity from scaffold
    doc["id"] = target_id
    doc["title"] = scaffold["title"]

    # Compliance: scaffold clause mapping + template assurance depth
    adapted_comp = doc.get("compliance", [{}])[0]
    doc["compliance"] = [
        _merge_compliance(adapted_comp, scaffold["compliance"][0]),
    ]

    # Evidence field: prefer adapted template depth but ensure clause marker matches
    if "evidence" in doc:
        s_clause = scaffold["compliance"][0]["clause"]
        doc["evidence"] = re.sub(
            r'(tsa_sd_clause|csa_clause|soci_clause|awia_clause|cn_csl_clause|clause)="[^"]*"',
            lambda m: f'{m.group(1)}="{s_clause}"',
            doc["evidence"],
            count=1,
        )

    # Workflow metadata — community until SME verifies
    doc["status"] = "community"
    doc["lastReviewed"] = "2026-07-24"
    doc["reviewer"] = "Compliance SME Panel (exemplar-adapted; pending verification)"

    if "prerequisiteUseCases" in scaffold:
        doc["prerequisiteUseCases"] = scaffold["prerequisiteUseCases"]

    if "exclusions" in scaffold and scaffold.get("exclusions"):
        # Preserve OT-safety / scope exclusions authored in gap manifest
        if target_id.startswith("22.63."):
            doc["exclusions"] = scaffold["exclusions"]

    return doc


def upgrade_all(check_only: bool = False, force: bool = False) -> int:
    if len(TEMPLATE_MAP) != 46:
        print(f"ERROR: expected 46 template mappings, got {len(TEMPLATE_MAP)}", file=sys.stderr)
        return 1

    changed = 0
    for target_id in sorted(TEMPLATE_MAP):
        doc = upgrade_one(target_id)
        path = os.path.join(CONTENT, f"UC-{target_id}.json")
        new_bytes = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
            if old == new_bytes and not force:
                continue
        if check_only:
            print(f"would write {path} (template UC-{TEMPLATE_MAP[target_id]})")
            changed += 1
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_bytes)
        changed += 1
        tpl = TEMPLATE_MAP[target_id]
        impl_len = len(doc.get("detailedImplementation", ""))
        assurance = doc["compliance"][0].get("assurance", "?")
        print(f"wrote {path} <- UC-{tpl} (detailedImplementation={impl_len} chars, assurance={assurance})")
    print(f"{'would write' if check_only else 'wrote'} {changed} files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true", help="Rewrite even when bytes match")
    args = parser.parse_args()
    return upgrade_all(check_only=args.check, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
