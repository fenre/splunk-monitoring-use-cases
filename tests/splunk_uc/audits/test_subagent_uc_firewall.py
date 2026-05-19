"""Unit tests for audit-subagent-uc-firewall (Lane B Task B-7)."""

from __future__ import annotations

import pytest

from splunk_uc.audits.subagent_uc_firewall import (
    SUBAGENT_AUTHORED_LABEL,
    evaluate_firewall,
    is_uc_sidecar_path,
    main,
)


class TestIsUcSidecarPath:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("content/cat-1-network/UC-1.1.1.json", True),
            ("content/cat-22-regulatory-compliance/UC-22.1.1.json", True),
            ("dist/uc/UC-1.1.1/index.json", False),
            ("content/README.md", False),
            ("content/cat-1-network/README.md", False),
            ("content/cat-1-network/UC-1.1.1.md", False),
        ],
    )
    def test_path_classification(self, path: str, expected: bool) -> None:
        assert is_uc_sidecar_path(path) is expected


class TestEvaluateFirewall:
    def test_subagent_with_uc_path_fails(self) -> None:
        result = evaluate_firewall(
            [SUBAGENT_AUTHORED_LABEL],
            ["content/cat-1-network/UC-1.1.1.json", "docs/foo.md"],
        )
        assert result.passed is False
        assert result.violating_paths == ["content/cat-1-network/UC-1.1.1.json"]

    def test_subagent_with_non_uc_paths_passes(self) -> None:
        result = evaluate_firewall(
            [SUBAGENT_AUTHORED_LABEL],
            ["src/splunk_uc/audits/foo.py", "docs/subagent-firewall.md"],
        )
        assert result.passed is True
        assert result.violating_paths == []

    def test_no_label_with_uc_paths_passes_maintainer_control(self) -> None:
        result = evaluate_firewall(
            [],
            ["content/cat-1-network/UC-1.1.1.json"],
        )
        assert result.passed is True

    def test_maintainer_authored_label_with_uc_paths_passes(self) -> None:
        result = evaluate_firewall(
            ["maintainer-authored"],
            ["content/cat-1-network/UC-1.1.1.json"],
        )
        assert result.passed is True


class TestMainCli:
    def test_check_subagent_uc_path_exits_1(self) -> None:
        rc = main(
            [
                "--check",
                "--labels",
                SUBAGENT_AUTHORED_LABEL,
                "--paths",
                "content/cat-1-x/UC-1.1.1.json",
            ]
        )
        assert rc == 1

    def test_no_context_safe_pass(self) -> None:
        rc = main(["--check"])
        assert rc == 0

    def test_explicit_maintainer_uc_pass(self) -> None:
        rc = main(
            [
                "--check",
                "--paths",
                "content/cat-1-network/UC-1.1.1.json",
            ]
        )
        assert rc == 0
