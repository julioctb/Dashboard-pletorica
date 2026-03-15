#!/usr/bin/env python3
"""Detect likely Python boolean control flow on reactive Reflex values."""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SKIP_FILE_SUFFIXES = {"state.py"}
IGNORED_PARAM_NAMES = {"self", "cls"}


@dataclass
class Issue:
    path: Path
    line: int
    kind: str
    expr: str
    function_name: str
    reason: str


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            if not any(path.name.endswith(suffix) for suffix in SKIP_FILE_SUFFIXES):
                files.append(path)
            continue
        if not path.exists():
            continue
        for candidate in path.rglob("*.py"):
            if any(part in SKIP_DIRS for part in candidate.parts):
                continue
            if any(candidate.name.endswith(suffix) for suffix in SKIP_FILE_SUFFIXES):
                continue
            files.append(candidate)
    return sorted(set(files))


def target_names(target: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(target, ast.Name):
        names.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for item in target.elts:
            names.update(target_names(item))
    return names


def expr_uses_tracked_name(node: ast.AST, tracked_names: set[str]) -> bool:
    return any(isinstance(child, ast.Name) and child.id in tracked_names for child in ast.walk(node))


class FunctionIssueFinder(ast.NodeVisitor):
    def __init__(self, source: str, path: Path, function_name: str, tracked_names: set[str]) -> None:
        self.source = source
        self.path = path
        self.function_name = function_name
        self.tracked_names = set(tracked_names)
        self.issues: list[Issue] = []

    def _record(self, node: ast.AST, kind: str, reason: str) -> None:
        expr = ast.get_source_segment(self.source, node) or "<unknown>"
        self.issues.append(
            Issue(
                path=self.path,
                line=node.lineno,
                kind=kind,
                expr=expr.strip(),
                function_name=self.function_name,
                reason=reason,
            )
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        if expr_uses_tracked_name(node.value, self.tracked_names):
            for target in node.targets:
                self.tracked_names.update(target_names(target))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value and expr_uses_tracked_name(node.value, self.tracked_names):
            self.tracked_names.update(target_names(node.target))
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        if expr_uses_tracked_name(node.test, self.tracked_names):
            self._record(
                node.test,
                "if",
                "uses Python `if` on a value derived from a reactive parameter; prefer rx.cond/rx.match",
            )
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        if expr_uses_tracked_name(node.test, self.tracked_names):
            self._record(
                node.test,
                "ternary",
                "uses a Python ternary on a reactive value; prefer rx.cond",
            )
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if expr_uses_tracked_name(node, self.tracked_names):
            operator = "and" if isinstance(node.op, ast.And) else "or"
            self._record(
                node,
                operator,
                f"uses Python `{operator}` on a reactive value; prefer `&` or `|`",
            )
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if isinstance(node.op, ast.Not) and expr_uses_tracked_name(node, self.tracked_names):
            self._record(
                node,
                "not",
                "uses Python `not` on a reactive value; prefer `~` or rx.cond",
            )
        self.generic_visit(node)


def function_is_relevant(node: ast.FunctionDef | ast.AsyncFunctionDef, path: Path) -> bool:
    if any(path.name.endswith(suffix) for suffix in SKIP_FILE_SUFFIXES):
        return False
    params = [
        arg.arg
        for arg in node.args.args
        if arg.arg not in IGNORED_PARAM_NAMES
    ]
    return bool(params)


def scan_file(path: Path) -> list[Issue]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    issues: list[Issue] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not function_is_relevant(node, path):
            continue
        tracked_names = {
            arg.arg
            for arg in node.args.args
            if arg.arg not in IGNORED_PARAM_NAMES
        }
        finder = FunctionIssueFinder(source, path, node.name, tracked_names)
        for statement in node.body:
            finder.visit(statement)
        issues.extend(finder.issues)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check common Reflex render helpers for Python boolean control flow on reactive values."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["app/presentation"],
        help="Files or directories to scan. Defaults to app/presentation.",
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
        print("No suspicious Python boolean control flow on reactive values found.")
        return 0

    print("Suspicious Python boolean control flow on reactive values found:\n")
    for issue in issues:
        print(
            f"{issue.path}:{issue.line}: `{issue.expr}` in `{issue.function_name}` -> {issue.reason}"
        )

    print(
        f"\nFound {len(issues)} issue(s). Replace Python control flow with rx.cond/rx.match or bitwise operators."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
