#!/usr/bin/env python3
"""Detect likely invalid CSS values passed to Reflex token props."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TOKEN_SPACING_PROPS = {
    "spacing",
    "p",
    "px",
    "py",
    "pt",
    "pr",
    "pb",
    "pl",
    "m",
    "mx",
    "my",
    "mt",
    "mr",
    "mb",
    "ml",
}
ALLOWED_TOKENS = {str(index) for index in range(10)}
CSS_UNIT_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%)$")
THEME_ROOTS = {"Spacing", "Radius", "Typography", "Shadows"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}


@dataclass
class Issue:
    path: Path
    line: int
    prop: str
    expr: str
    reason: str


def attr_chain(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def is_breakpoints_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    chain = attr_chain(node.func)
    return chain in {"rx.breakpoints", "breakpoints"}


def find_value_issues(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            if node.value in ALLOWED_TOKENS:
                return []
            if CSS_UNIT_RE.match(node.value):
                return [f"uses CSS length `{node.value}`"]
            if node.value.isdigit():
                return [f"uses unsupported token `{node.value}`"]
            return []
        if isinstance(node.value, int):
            return [f"uses integer `{node.value}`; Reflex token props expect strings like \"2\""]
        return []

    if isinstance(node, ast.Attribute):
        chain = attr_chain(node)
        if chain and chain.split(".", 1)[0] in THEME_ROOTS:
            return [f"uses theme constant `{chain}` instead of a Radix token"]
        return []

    if isinstance(node, ast.Dict):
        issues: list[str] = []
        for value in node.values:
            issues.extend(find_value_issues(value))
        return issues

    if is_breakpoints_call(node):
        issues: list[str] = []
        for keyword in node.keywords:
            if keyword.arg is None:
                continue
            nested = find_value_issues(keyword.value)
            issues.extend([f"breakpoint `{keyword.arg}` {issue}" for issue in nested])
        return issues

    return []


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue
        if not path.exists():
            continue
        for candidate in path.rglob("*.py"):
            if any(part in SKIP_DIRS for part in candidate.parts):
                continue
            files.append(candidate)
    return sorted(set(files))


def scan_file(path: Path) -> list[Issue]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    issues: list[Issue] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg not in TOKEN_SPACING_PROPS:
                continue
            reasons = find_value_issues(keyword.value)
            if not reasons:
                continue
            expr = ast.get_source_segment(source, keyword.value) or "<unknown>"
            for reason in reasons:
                issues.append(
                    Issue(
                        path=path,
                        line=keyword.value.lineno,
                        prop=keyword.arg,
                        expr=expr.strip(),
                        reason=reason,
                    )
                )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check common Reflex token props for CSS-like values."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["app"],
        help="Files or directories to scan. Defaults to app.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = [Path(raw).resolve() for raw in args.paths]
    files = iter_python_files(paths)
    issues: list[Issue] = []
    for file_path in files:
        issues.extend(scan_file(file_path))

    if not issues:
        print("No suspicious Reflex token-prop values found.")
        return 0

    print("Suspicious Reflex token-prop values found:\n")
    for issue in issues:
        print(
            f"{issue.path}:{issue.line}: `{issue.prop}={issue.expr}` -> {issue.reason}"
        )

    print(
        f"\nFound {len(issues)} issue(s). Replace CSS values with Radix tokens or use the CSS prop name instead."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
