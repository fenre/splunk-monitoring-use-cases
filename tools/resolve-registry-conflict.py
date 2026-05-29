#!/usr/bin/env python3
"""
Resolve src/splunk_uc/_registry.py merge conflicts of the shape:

    register(
        Verb(
    <<<<<<< HEAD
            name="<pr-verb>",
            module="<pr-module>",
            help="<pr-help>",
    =======
            name="<main-verb>",
            module="<main-module>",
            help=(
                "<main-help>"
            ),
    >>>>>>> origin/main
            category="<cat>",
        )
    )

Both branches added a Verb at the same anchor slot. Resolution: keep main's
Verb in place, then append a NEW register() block for the PR's verb
immediately after, preserving the shared category= tail.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CONFLICT_RE = re.compile(
    r"register\(\n"
    r"    Verb\(\n"
    r"<<<<<<< HEAD\n"
    r"(?P<pr_lines>(?:.*\n)+?)"
    r"=======\n"
    r"(?P<main_lines>(?:.*\n)+?)"
    r">>>>>>> origin/main\n"
    r"(?P<tail>(?:    +.*\n)*?)"
    r"    \)\n"
    r"\)\n",
    re.MULTILINE,
)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: resolve_registry_conflict.py <path>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    text = path.read_text()
    match = CONFLICT_RE.search(text)
    if match is None:
        if "<<<<<<<" in text:
            print("ERROR: unrecognised conflict shape", file=sys.stderr)
            return 1
        print("no conflict to resolve")
        return 0

    pr_lines = match.group("pr_lines")
    main_lines = match.group("main_lines")
    tail = match.group("tail")

    main_block = (
        "register(\n"
        "    Verb(\n"
        f"{main_lines}"
        f"{tail}"
        "    )\n"
        ")\n"
    )
    pr_block = (
        "register(\n"
        "    Verb(\n"
        f"{pr_lines}"
        f"{tail}"
        "    )\n"
        ")\n"
    )

    replacement = main_block + pr_block
    new_text = text[: match.start()] + replacement + text[match.end():]
    path.write_text(new_text)
    if "<<<<<<<" in new_text or ">>>>>>>" in new_text:
        print("ERROR: markers remain", file=sys.stderr)
        return 1
    print("resolved cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
