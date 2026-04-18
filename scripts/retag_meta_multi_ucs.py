#!/usr/bin/env python3
"""Phase-D: Re-tag UCs currently mapped to ``Multiple`` (meta-multi).

11 UCs (listed in ``RETAG_TABLE``) carry a single compliance entry where
``regulation="Multiple"`` and ``version="n/a"``. These contribute **zero**
coverage because the ``meta-multi`` framework is a tier-3 placeholder with no
``commonClauses[]``. Phase D of the regulation-coverage-gap plan replaces that
single placeholder entry with 2–4 concrete regulation entries so the UCs flow
into real tier-1 / tier-2 coverage.

The script is **idempotent**: it refuses to touch a UC whose compliance block
no longer contains the original ``Multiple`` placeholder (so you can re-run
it safely).
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
UC_DIR = REPO_ROOT / "use-cases" / "cat-22"


@dataclass(frozen=True)
class Mapping3:
    """A single (regulation, version, clause) compliance target."""

    regulation: str
    version: str
    clause: str
    assurance: str = "contributing"
    mode: str = "satisfies"
    rationale: str = ""


@dataclass(frozen=True)
class UcRetag:
    uc_id: str
    targets: Sequence[Mapping3]


RETAG_TABLE: Sequence[UcRetag] = [
    # ---- Compliance-trending cluster (22.9.6 … 22.9.10) ----
    UcRetag(
        uc_id="22.9.6",
        targets=[
            Mapping3(
                regulation="SOC 2", version="2017 TSC", clause="CC7.2",
                rationale=(
                    "SOC 2 CC7.2 Monitoring of Controls — trending control-test "
                    "pass rate quarter-over-quarter directly satisfies the "
                    "monitoring requirement; contributing because trending "
                    "alone does not replace the per-control test evidence."
                ),
            ),
            Mapping3(
                regulation="ISO 27001", version="2022", clause="9.1",
                rationale=(
                    "ISO/IEC 27001:2022 §9.1 Monitoring, measurement, "
                    "analysis and evaluation — trend data demonstrates the "
                    "monitoring activity the clause requires."
                ),
            ),
        ],
    ),
    UcRetag(
        uc_id="22.9.7",
        targets=[
            Mapping3(
                regulation="ISO 27001", version="2022", clause="8.2",
                rationale=(
                    "ISO/IEC 27001:2022 §8.2 Information security risk "
                    "assessment — burning down SoA exceptions is a direct "
                    "artefact of continuous risk assessment."
                ),
            ),
            Mapping3(
                regulation="ISO 27001", version="2022", clause="9.1",
                rationale=(
                    "§9.1 Monitoring, measurement, analysis and evaluation — "
                    "exception burn-down is the measurement view."
                ),
            ),
        ],
    ),
    UcRetag(
        uc_id="22.9.8",
        targets=[
            Mapping3(
                regulation="SOC 2", version="2017 TSC", clause="CC5.1",
                rationale=(
                    "SOC 2 CC5.1 Control Activities — auditor evidence "
                    "pack throughput and deficiency metrics show that "
                    "control activities are operating."
                ),
            ),
            Mapping3(
                regulation="SOX ITGC", version="PCAOB AS 2201", clause="ITGC.Logging.Continuity",
                rationale=(
                    "SOX ITGC Logging.Continuity — evidence continuity is "
                    "the primary ITGC artefact for external-audit packs."
                ),
            ),
        ],
    ),
    UcRetag(
        uc_id="22.9.9",
        targets=[
            Mapping3(
                regulation="ISO 27001", version="2022", clause="9.1",
                rationale=(
                    "§9.1 Monitoring/measurement — regulatory-change impact "
                    "scoring is a form of monitoring the external context."
                ),
            ),
            Mapping3(
                regulation="SOC 2", version="2017 TSC", clause="CC3.1",
                rationale=(
                    "SOC 2 CC3.1 Risk Assessment — regulatory change is a "
                    "primary risk-assessment input."
                ),
            ),
        ],
    ),
    UcRetag(
        uc_id="22.9.10",
        targets=[
            Mapping3(
                regulation="SOC 2", version="2017 TSC", clause="CC2.1",
                rationale=(
                    "SOC 2 CC2.1 Communication and Information — the "
                    "composite posture score plus driver attribution is "
                    "the internal communication of compliance status."
                ),
            ),
            Mapping3(
                regulation="ISO 27001", version="2022", clause="9.1",
                rationale=(
                    "§9.1 Monitoring, measurement, analysis and evaluation — "
                    "weighted posture composites are a measurement artefact."
                ),
            ),
        ],
    ),
    # ---- APAC breach-handling cluster (22.29.7 … 22.29.12) ----
    UcRetag(
        uc_id="22.29.7",
        targets=[
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale=(
                    "§26WK Notifiable Data Breaches — breach discovery and "
                    "severity classification are explicit prerequisites to "
                    "the NDB timeline."
                ),
            ),
            Mapping3(
                regulation="PIPL", version="2021", clause="Art.15",
                rationale=(
                    "PIPL Art.15 — notification obligations presuppose "
                    "accurate discovery and classification."
                ),
            ),
            Mapping3(
                regulation="SG PDPA", version="2020 amended", clause="§26A",
                rationale=(
                    "SG PDPA §26A Data breach assessment — the statute "
                    "requires a timely severity assessment."
                ),
            ),
            Mapping3(
                regulation="APPI", version="2022 amendments", clause="Art.26",
                rationale=(
                    "APPI Art.26 — leakage reporting depends on accurate "
                    "discovery and classification."
                ),
            ),
        ],
    ),
    UcRetag(
        uc_id="22.29.8",
        targets=[
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale="§26WK NDB — 30-day timeline compliance is a core evidence output.",
            ),
            Mapping3(
                regulation="PIPL", version="2021", clause="Art.15",
                rationale="PIPL Art.15 — 72-hour notification window evidence.",
            ),
            Mapping3(
                regulation="SG PDPA", version="2020 amended", clause="§26A",
                rationale="SG PDPA §26A — 72-hour commissioner notification tracking.",
            ),
            Mapping3(
                regulation="APPI", version="2022 amendments", clause="Art.26",
                rationale="APPI Art.26 — PPC notification timeline evidence.",
            ),
        ],
    ),
    UcRetag(
        uc_id="22.29.9",
        targets=[
            Mapping3(
                regulation="SG PDPA", version="2020 amended", clause="§26A",
                rationale="§26A(1) requires affected individual notification with specific content.",
            ),
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale="§26WK also imposes individual notification; UC evidences delivery.",
            ),
            Mapping3(
                regulation="PIPL", version="2021", clause="Art.15",
                rationale="PIPL Art.15 requires notification to individuals; this UC demonstrates delivery.",
            ),
        ],
    ),
    UcRetag(
        uc_id="22.29.10",
        targets=[
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale="§26WK authority-notification pack completeness.",
            ),
            Mapping3(
                regulation="APPI", version="2022 amendments", clause="Art.26",
                rationale="APPI Art.26 PPC reporting-pack completeness.",
            ),
            Mapping3(
                regulation="SG PDPA", version="2020 amended", clause="§26A",
                rationale="SG PDPA §26A commissioner-report completeness.",
            ),
        ],
    ),
    UcRetag(
        uc_id="22.29.11",
        targets=[
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale="§26WK requires a breach register; linkage across events is primary evidence.",
            ),
            Mapping3(
                regulation="PIPL", version="2021", clause="Art.15",
                rationale="PIPL Art.15 — register maintenance supports authority reporting.",
            ),
            Mapping3(
                regulation="APPI", version="2022 amendments", clause="Art.26",
                rationale="APPI Art.26 — leakage history register.",
            ),
        ],
    ),
    UcRetag(
        uc_id="22.29.12",
        targets=[
            Mapping3(
                regulation="AU Privacy Act", version="current", clause="§26WK",
                rationale="§26WK — remediation evidence is required before the NDB obligation is fully discharged.",
            ),
            Mapping3(
                regulation="PIPL", version="2021", clause="Art.15",
                rationale="PIPL Art.15 — root-cause and remediation support the ongoing obligation.",
            ),
        ],
    ),
]


def build_entry(m: Mapping3) -> Dict[str, str]:
    out: Dict[str, str] = {
        "regulation": m.regulation,
        "version": m.version,
        "clause": m.clause,
        "mode": m.mode,
        "assurance": m.assurance,
        "assurance_rationale": (
            f"Phase-D retagged from meta-multi placeholder to a concrete "
            f"{m.regulation} clause. {m.rationale} Assurance level set to "
            f"'contributing' pending SME review per Phase E of the plan."
        ),
        "provenance": "maintainer",
    }
    return out


def patch_one(path: pathlib.Path, retag: UcRetag) -> bool:
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    compliance = doc.get("compliance") or []
    # Only retag if the UC has the original Multiple/n/a entry.
    mm_entries = [e for e in compliance if e.get("regulation") == "Multiple" and e.get("version") == "n/a"]
    if not mm_entries:
        sys.stderr.write(
            f"skip  {path.name}: no Multiple/n/a entry found (already retagged?).\n"
        )
        return False
    # Remove every Multiple/n/a entry; keep siblings.
    remaining = [e for e in compliance if not (e.get("regulation") == "Multiple" and e.get("version") == "n/a")]
    new_entries: List[Dict[str, str]] = list(remaining) + [build_entry(m) for m in retag.targets]
    doc["compliance"] = new_entries
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def main() -> int:
    written = 0
    skipped = 0
    for retag in RETAG_TABLE:
        path = UC_DIR / f"uc-{retag.uc_id}.json"
        if not path.exists():
            sys.stderr.write(f"error: {path} missing.\n")
            return 1
        if patch_one(path, retag):
            sys.stdout.write(
                f"retagged {path.name}: removed Multiple, added {len(retag.targets)} concrete entries\n"
            )
            written += 1
        else:
            skipped += 1
    sys.stdout.write(f"\nPhase-D retag: patched={written} skipped={skipped}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
