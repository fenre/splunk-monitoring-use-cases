#!/usr/bin/env python3
"""Run all cat-25 depth-wave generators in order (append mode)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    total = 0
    for name in (
        "gen_cat25_depth_01",
        "gen_cat25_depth_02",
        "gen_cat25_depth_03",
        "gen_cat25_depth_04",
    ):
        mod = _load(name)
        if hasattr(mod, "generate"):
            result = mod.generate()
            if isinstance(result, tuple):
                total += result[0]
            print(f"{name}: done")
    print(f"Total new UCs this run: {total}")


if __name__ == "__main__":
    main()
