#!/usr/bin/env python3
"""Wave 10A: deepen cat-25 subcategories 25.86–25.100 from 28 to 33 (+5 each)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from gen_cat25_common import CAT25, Cat25Writer, R

TARGET_SUBS = tuple(str(i) for i in range(86, 101))
EXPECTED_PER_SUB = 5

# Reuse Wave 9A deepen templates.
from gen_cat25_wave9a import deepen_specs, load_sub_meta as _load  # noqa: E402


def load_sub_meta() -> dict[str, dict[str, str]]:
    data = json.loads((CAT25 / "_category.json").read_text(encoding="utf-8"))
    meta: dict[str, dict[str, str]] = {}
    for sub in data["subcategories"]:
        num = str(sub["id"]).split(".")[-1]
        if num in TARGET_SUBS:
            meta[num] = {
                "name": sub["name"],
                "app": sub["primaryAppTa"],
                "ds": sub["dataSources"],
            }
    assert len(meta) == len(TARGET_SUBS)
    return meta


def sourcetypes_for_sub(sub: str) -> list[str]:
    found: list[str] = []
    for path in sorted(CAT25.glob(f"UC-25.{sub}.*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for blob in (doc.get("spl", ""), doc.get("dataSources", "")):
            for match in re.finditer(r"sourcetype=(?:\"([^\"]+)\"|(\S+))", str(blob)):
                st = (match.group(1) or match.group(2)).strip("\"'")
                if st and st not in found:
                    found.append(st)
    return found


def main() -> int:
    meta = load_sub_meta()
    writer = Cat25Writer(append=True)
    created: list[str] = []
    for sub in TARGET_SUBS:
        sts = sourcetypes_for_sub(sub)
        assert sts, f"no sourcetypes for 25.{sub}"
        specs = deepen_specs(sub, meta[sub]["name"], sts)
        assert len(specs) == EXPECTED_PER_SUB
        for spec in specs:
            created.append(
                writer.U(
                    sub=sub,
                    title=str(spec["title"]),
                    crit=str(spec["crit"]),
                    diff=str(spec["diff"]),
                    mtypes=list(spec["mtypes"]),
                    spl=str(spec["spl"]),
                    desc=str(spec["desc"]),
                    val=str(spec["val"]),
                    impl=str(spec["impl"]),
                    viz=str(spec["viz"]),
                    grandma_body=str(spec["grandma_body"]),
                    refs=R(
                        (
                            "Splunk Search Reference",
                            "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual",
                        ),
                    ),
                    app=meta[sub]["app"],
                    ds=meta[sub]["ds"],
                )
            )
    total, by_sub = writer.summary()
    print(f"new_use_cases={total}")
    for sub in TARGET_SUBS:
        print(f"25.{sub}=+{by_sub.get(sub, 0)}")
    print(f"first_id={created[0]}")
    print(f"last_id={created[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
