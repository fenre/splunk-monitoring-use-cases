#!/usr/bin/env python3
"""
Resolve src/splunk_uc/_registry.py merge conflicts of the shape:

    register(
        Verb(
    <<<<<<< HEAD
            name="<side-a-verb>",
            module="<side-a-module>",
            help="<side-a-help>",
    =======
            name="<side-b-verb>",
            module="<side-b-module>",
            help=(
                "<side-b-help>"
            ),
    >>>>>>> origin/main          # merge: the other side is origin/main
    >>>>>>> 4f5de607d (feat: ...) # rebase: the other side is the replayed commit
            category="<cat>",
        )
    )

Both branches added a Verb at the same anchor slot. Resolution: keep BOTH
verbs by emitting two separate register() blocks, each preserving the shared
category= tail. Works for either direction:

  * `git merge origin/main`  -> closing marker is `>>>>>>> origin/main`
  * `git rebase origin/main`  -> closing marker is `>>>>>>> <sha> (subject)`

Registration order is not semantically significant (the dispatcher keys on
verb name), so the HEAD-side verb is emitted first and the incoming-side verb
second regardless of merge/rebase direction.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CONFLICT_RE = re.compile(
    r"register\(\n"
    r"    Verb\(\n"
    r"<<<<<<< HEAD\n"
    r"(?P<head_lines>(?:.*\n)+?)"
    r"=======\n"
    r"(?P<incoming_lines>(?:.*\n)+?)"
    r">>>>>>> .*\n"  # origin/main (merge) or <sha> (subject) (rebase)
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

    head_lines = match.group("head_lines")
    incoming_lines = match.group("incoming_lines")
    tail = match.group("tail")

    head_block = (
        "register(\n"
        "    Verb(\n"
        f"{head_lines}"
        f"{tail}"
        "    )\n"
        ")\n"
    )
    incoming_block = (
        "register(\n"
        "    Verb(\n"
        f"{incoming_lines}"
        f"{tail}"
        "    )\n"
        ")\n"
    )

    replacement = head_block + incoming_block
    new_text = text[: match.start()] + replacement + text[match.end():]
    path.write_text(new_text)
    if "<<<<<<<" in new_text or ">>>>>>>" in new_text:
        print("ERROR: markers remain", file=sys.stderr)
        return 1
    print("resolved cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
