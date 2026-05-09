"""Dispatcher for ``python -m splunk_uc <verb> [args...]``.

Resolves the verb name from ``_registry.py``, loads the implementation
lazily, and forwards remaining argv to the implementation's ``main``.
On unknown / missing verb, prints a categorised help table and exits
non-zero.

Examples
--------
::

    PYTHONPATH=src python3 -m splunk_uc                       # show help
    PYTHONPATH=src python3 -m splunk_uc --help                 # show help
    PYTHONPATH=src python3 -m splunk_uc audit-reproducibility  # run a verb
    PYTHONPATH=src python3 -m splunk_uc audit-reproducibility --first-build-only

Once ``pip install -e .`` is run the ``PYTHONPATH=src`` prefix is
unnecessary, but the package supports both invocation styles so
maintainers don't need an editable install just to run audits.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from splunk_uc import __version__, _registry


def _format_help() -> str:
    """Build the help text shown when no verb is given or --help is passed.

    Groups verbs by category so future migrations land in a predictable
    location and the user can scan for the right tool quickly.
    """
    lines: list[str] = []
    lines.append(f"splunk_uc {__version__} - Splunk monitoring use-cases CLI")
    lines.append("")
    lines.append("Usage: python -m splunk_uc <verb> [args...]")
    lines.append("       python -m splunk_uc --help")
    lines.append("       python -m splunk_uc --version")
    lines.append("")

    grouped = _registry.by_category()
    if not grouped:
        lines.append("No verbs are registered yet.")
        return "\n".join(lines)

    width = max(len(v.name) for v in _registry.all_verbs())
    for category in sorted(grouped):
        lines.append(f"{category}:")
        for verb in grouped[category]:
            lines.append(f"  {verb.name:<{width}}  {verb.help}")
        lines.append("")
    lines.append("Run `python -m splunk_uc <verb> --help` for verb-specific options.")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a single verb invocation.

    Parameters
    ----------
    argv
        Argument vector excluding the program name. If ``None``, falls
        back to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on usage errors, 2 on unknown verbs.
        Verb-specific exit codes are returned verbatim from the verb's
        ``main`` callable.
    """
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in {"-h", "--help"}:
        sys.stdout.write(_format_help() + "\n")
        return 0

    if args[0] in {"-V", "--version"}:
        sys.stdout.write(f"splunk_uc {__version__}\n")
        return 0

    verb_name = args[0]
    rest = args[1:]

    # Avoid the surprise where users type `python -m splunk_uc audits build`
    # expecting the old positional category form. Help them to the right
    # invocation rather than failing silently.
    if verb_name in {"audits", "generators", "ingest", "migrations", "feasibility"}:
        sys.stderr.write(
            f"error: {verb_name!r} is a category, not a verb. "
            "Run `python -m splunk_uc --help` to list verbs by category.\n"
        )
        return 2

    impl = _registry.resolve(verb_name)
    if impl is None:
        sys.stderr.write(
            f"error: unknown verb {verb_name!r}. "
            "Run `python -m splunk_uc --help` to list available verbs.\n"
        )
        return 2

    return int(impl(rest))


if __name__ == "__main__":
    raise SystemExit(main())
