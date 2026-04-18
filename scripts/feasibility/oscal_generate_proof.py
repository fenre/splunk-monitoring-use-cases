#!/usr/bin/env python3
"""Phase 0.5b feasibility proof — OSCAL Component Definition generation + validation.

Takes ``use-cases/cat-22/uc-22.35.1.json`` (the draft UC exemplar) and emits a
minimal NIST OSCAL v1.1.1 Component Definition, then hands the output off to
``scripts/feasibility/oscal_validate.mjs`` (Node + Ajv) for schema validation.

Why Node+Ajv and not Python jsonschema / jsonschema-rs?
    * NIST's OSCAL schemas use ECMA-262 Unicode property escapes in patterns
      (``\\p{L}``, ``\\p{N}``) that Python's ``re`` module does not support, so
      the pure-Python ``jsonschema`` library cannot even load the schema.
    * ``jsonschema-rs`` supports ECMA-262 regex, but does not correctly
      resolve NIST's ~119 anchor-style ``"$ref": "#id-anchor"`` values. Even a
      minimal-valid component-definition fails with a misleading error rooted
      at ``definitions/URIReferenceDatatype/type``.
    * Ajv handles both ECMA-262 regex and anchor-style refs natively. That is
      the industry-standard validator for OSCAL in JavaScript tooling, so it
      also keeps our toolchain aligned with what NIST itself ships.

Run:
    .venv-feasibility/bin/python scripts/feasibility/oscal_generate_proof.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import uuid

REPO = pathlib.Path(__file__).resolve().parents[2]
EXEMPLAR = REPO / "use-cases" / "cat-22" / "uc-22.35.1.json"
OSCAL_SCHEMA = REPO / "vendor" / "oscal" / "oscal_component_schema_v1.1.1.json"
OUTPUT = REPO / "data" / "crosswalks" / "oscal" / "component-definition-uc-22.35.1.json"
NODE_VALIDATOR = REPO / "scripts" / "feasibility" / "oscal_validate.mjs"

REGULATION_TO_SOURCE_HREF = {
    "GDPR": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "HIPAA": "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164",
    "PCI-DSS": "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4_0.pdf",
    "SOC-2": "https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services",
    "SOX-ITGC": "https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201",
}

UUID_NAMESPACE = uuid.UUID("00000000-0000-5000-8000-000000000022")


def stable_uuid(seed: str) -> str:
    """Return a deterministic v5 UUID so generated artefacts are reproducible."""
    return str(uuid.uuid5(UUID_NAMESPACE, seed))


def iso_timestamp() -> str:
    return dt.datetime(2026, 4, 16, 0, 0, 0, tzinfo=dt.timezone.utc).isoformat(timespec="seconds")


def slugify_control_id(regulation: str, clause: str) -> str:
    """Normalise (regulation, clause) into an OSCAL control-id token."""
    raw = f"{regulation}-{clause}".lower()
    for old, new in (
        (" ", "-"),
        ("(", ""),
        (")", ""),
        ("§", "sec"),
        (".", "-"),
        (":", "-"),
        ("/", "-"),
    ):
        raw = raw.replace(old, new)
    return raw


def build_implemented_requirements(uc_full_id: str, compliance: list[dict]) -> list[dict]:
    reqs: list[dict] = []
    for entry in compliance:
        req_uuid = stable_uuid(
            f"req:{uc_full_id}:{entry['regulation']}:{entry['version']}:{entry['clause']}"
        )
        req: dict = {
            "uuid": req_uuid,
            "control-id": slugify_control_id(entry["regulation"], entry["clause"]),
            "description": (
                f"Splunk use case {uc_full_id} provides {entry['assurance']} assurance "
                f"in mode '{entry['mode']}' for {entry['regulation']} "
                f"{entry['version']} clause {entry['clause']}. "
                f"Rationale: {entry['assurance_rationale']}"
            ),
            "props": [
                {"name": "assurance", "ns": "https://fenre.github.io/splunk-monitoring-use-cases/ns/compliance", "value": entry["assurance"]},
                {"name": "mode", "ns": "https://fenre.github.io/splunk-monitoring-use-cases/ns/compliance", "value": entry["mode"]},
                {"name": "regulation", "ns": "https://fenre.github.io/splunk-monitoring-use-cases/ns/compliance", "value": entry["regulation"]},
                {"name": "regulation-version", "ns": "https://fenre.github.io/splunk-monitoring-use-cases/ns/compliance", "value": entry["version"]},
                {"name": "clause", "ns": "https://fenre.github.io/splunk-monitoring-use-cases/ns/compliance", "value": entry["clause"]},
            ],
        }
        # OSCAL's links[] has minItems: 1 when present, so only attach the key
        # when we actually have a reference URL.
        clause_url = entry.get("clauseUrl")
        if clause_url:
            req["links"] = [{"href": clause_url, "rel": "reference"}]
        reqs.append(req)
    return reqs


def build_component_definition(uc: dict) -> dict:
    uc_id = uc["id"]
    uc_full_id = f"UC-{uc_id}"
    component_uuid = stable_uuid(f"component:{uc_full_id}")
    comp_def_uuid = stable_uuid(f"component-definition:{uc_full_id}")
    impl_uuid = stable_uuid(f"control-implementation:{uc_full_id}")

    regulations = {entry["regulation"] for entry in uc["compliance"]}
    import_sources = [
        {
            "uuid": stable_uuid(f"import-source:{reg}"),
            "href": REGULATION_TO_SOURCE_HREF.get(reg, f"urn:regulation:{reg}"),
        }
        for reg in sorted(regulations)
    ]

    component = {
        "uuid": component_uuid,
        "type": "software",
        "title": uc["title"],
        "description": uc["description"],
        "purpose": uc["value"],
        "props": [
            {"name": "uc-id", "value": uc_full_id},
            {"name": "control-family", "value": uc.get("controlFamily", "")},
            {"name": "owner", "value": uc.get("owner", "")},
            {"name": "criticality", "value": uc.get("criticality", "")},
        ],
        "control-implementations": [
            {
                "uuid": impl_uuid,
                "source": import_sources[0]["href"] if import_sources else "urn:unknown",
                "description": (
                    f"Clause-level mappings maintained in the UC authoring schema "
                    f"at use-cases/cat-22/uc-{uc_id}.json."
                ),
                "implemented-requirements": build_implemented_requirements(
                    uc_full_id, uc["compliance"]
                ),
            }
        ],
    }

    resources = [
        {
            "uuid": stable_uuid(f"resource:{ref['url']}"),
            "title": ref.get("title", ref["url"]),
            "rlinks": [{"href": ref["url"]}],
        }
        for ref in uc.get("references", [])
    ]
    back_matter = {"resources": resources} if resources else None

    component_definition: dict = {
        "uuid": comp_def_uuid,
        "metadata": {
            "title": f"{uc_full_id} — {uc['title']} (Splunk Monitoring Use Case)",
            "last-modified": iso_timestamp(),
            "version": "0.1.0-draft",
            "oscal-version": "1.1.1",
            "parties": [
                {
                    "uuid": stable_uuid("party:maintainers"),
                    "type": "organization",
                    "name": "Splunk Monitoring Use Cases — maintainers",
                }
            ],
        },
        "components": [component],
    }
    if back_matter is not None:
        component_definition["back-matter"] = back_matter

    return {"component-definition": component_definition}


def run_ajv_validation(output_path: pathlib.Path) -> int:
    """Delegate schema validation to scripts/feasibility/oscal_validate.mjs."""
    node_bin = shutil.which("node")
    if node_bin is None:
        sys.stderr.write(
            "FAIL: `node` is not on PATH. Install Node 18+ and run `npm install` in the repo root\n"
            "      so Ajv is available. Node + Ajv is the only validator that correctly handles\n"
            "      NIST OSCAL's anchor-style $refs and ECMA-262 regex patterns.\n"
        )
        return 2
    proc = subprocess.run(
        [node_bin, str(NODE_VALIDATOR), str(output_path)],
        check=False,
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def main() -> int:
    if not OSCAL_SCHEMA.exists():
        sys.stderr.write(f"missing OSCAL schema at {OSCAL_SCHEMA}\n")
        return 2
    if not NODE_VALIDATOR.exists():
        sys.stderr.write(f"missing Node validator at {NODE_VALIDATOR}\n")
        return 2

    with EXEMPLAR.open("r", encoding="utf-8") as handle:
        uc = json.load(handle)

    component_def = build_component_definition(uc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(component_def, indent=2) + "\n"
    OUTPUT.write_text(serialised, encoding="utf-8")

    exit_code = run_ajv_validation(OUTPUT)
    if exit_code != 0:
        return exit_code

    payload_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(
        f"      generator output : {OUTPUT.relative_to(REPO)}\n"
        f"      sha256 (on-disk) : {payload_hash}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
