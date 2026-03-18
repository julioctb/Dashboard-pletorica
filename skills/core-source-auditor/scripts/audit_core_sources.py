#!/usr/bin/env python3
"""Audita app/core como fuente de verdad del repo."""

from __future__ import annotations

import argparse
import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class PublicSymbol:
    name: str
    kind: str
    module: str
    path: Path
    lineno: int


@dataclass(frozen=True)
class DuplicateFunction:
    qualified_name: str
    path: Path
    lineno: int
    statement_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Ruta del repo a auditar")
    parser.add_argument(
        "--write",
        help="Ruta markdown donde escribir el reporte. Si no se indica, se imprime a stdout.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Incluye app/tests en el analisis de consumidores externos",
    )
    return parser.parse_args()


def iter_python_files(base: Path) -> list[Path]:
    return sorted(
        path
        for path in base.rglob("*.py")
        if "__pycache__" not in path.parts and ".venv" not in path.parts
    )


def module_name(repo_root: Path, path: Path) -> str:
    return ".".join(path.relative_to(repo_root).with_suffix("").parts)


def read_ast(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def collect_public_symbols(repo_root: Path, core_files: list[Path]) -> list[PublicSymbol]:
    symbols: list[PublicSymbol] = []
    for path in core_files:
        tree = read_ast(path)
        if tree is None:
            continue
        module = module_name(repo_root, path)
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    symbols.append(
                        PublicSymbol(
                            name=node.name,
                            kind=kind,
                            module=module,
                            path=path,
                            lineno=node.lineno,
                        )
                    )
                continue
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and is_public_constant(target.id):
                        symbols.append(
                            PublicSymbol(
                                name=target.id,
                                kind="constant",
                                module=module,
                                path=path,
                                lineno=node.lineno,
                            )
                        )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if is_public_constant(node.target.id):
                    symbols.append(
                        PublicSymbol(
                            name=node.target.id,
                            kind="constant",
                            module=module,
                            path=path,
                            lineno=node.lineno,
                        )
                    )
    return symbols


def is_public_constant(name: str) -> bool:
    return bool(name) and name.isupper() and not name.startswith("_")


def collect_reexports(core_files: list[Path]) -> set[str]:
    reexported: set[str] = set()
    for path in core_files:
        if path.name != "__init__.py":
            continue
        tree = read_ast(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        reexported.add(alias.asname or alias.name)
    return reexported


def collect_external_imports(
    repo_root: Path,
    external_files: list[Path],
) -> tuple[dict[str, set[Path]], dict[tuple[str, str], set[Path]], dict[str, set[Path]]]:
    imported_modules: dict[str, set[Path]] = defaultdict(set)
    imported_symbols: dict[tuple[str, str], set[Path]] = defaultdict(set)
    area_consumers: dict[str, set[Path]] = defaultdict(set)

    for path in external_files:
        tree = read_ast(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("app.core"):
                        imported_modules[alias.name].add(path)
                        area_consumers[area_key(alias.name)].add(path)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if not module.startswith("app.core"):
                    continue
                imported_modules[module].add(path)
                area_consumers[area_key(module)].add(path)
                for alias in node.names:
                    if alias.name != "*":
                        imported_symbols[(module, alias.name)].add(path)
    return imported_modules, imported_symbols, area_consumers


def area_key(module: str) -> str:
    parts = module.split(".")
    if len(parts) <= 2:
        return "core"
    return parts[2]


def detect_wrapper_modules(external_files: list[Path]) -> list[tuple[Path, list[str]]]:
    wrappers: list[tuple[Path, list[str]]] = []
    for path in external_files:
        tree = read_ast(path)
        if tree is None:
            continue
        body = list(getattr(tree, "body", []))
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            if isinstance(body[0].value.value, str):
                body = body[1:]
        if not body:
            continue

        core_modules: list[str] = []
        valid = True
        has_core_import = False

        for node in body:
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app.core"):
                has_core_import = True
                core_modules.append(node.module or "")
                continue
            if isinstance(node, ast.Import):
                core_imports = [alias.name for alias in node.names if alias.name.startswith("app.core")]
                if core_imports:
                    has_core_import = True
                    core_modules.extend(core_imports)
                    continue
            if isinstance(node, ast.Assign):
                if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                    continue
            valid = False
            break

        if valid and has_core_import:
            wrappers.append((path, sorted(set(core_modules))))
    return sorted(wrappers, key=lambda item: item[0].as_posix())


class DuplicateVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.scope: list[str] = []
        self.groups: dict[str, list[DuplicateFunction]] = defaultdict(list)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record(node)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record(node)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _record(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if node.name.startswith("__"):
            return
        normalized = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
        qualified = ".".join([*self.scope, node.name]) if self.scope else node.name
        self.groups[normalized].append(
            DuplicateFunction(
                qualified_name=qualified,
                path=self.path,
                lineno=node.lineno,
                statement_count=len(node.body),
            )
        )


def collect_duplicate_functions(core_files: list[Path]) -> list[list[DuplicateFunction]]:
    groups: dict[str, list[DuplicateFunction]] = defaultdict(list)
    for path in core_files:
        tree = read_ast(path)
        if tree is None:
            continue
        visitor = DuplicateVisitor(path)
        visitor.visit(tree)
        for key, value in visitor.groups.items():
            groups[key].extend(value)

    duplicates = [
        group
        for group in groups.values()
        if len(group) >= 2 and not all(item.statement_count == 1 and item.qualified_name.endswith("descripcion") for item in group)
    ]
    duplicates.sort(key=lambda group: (-len(group), group[0].qualified_name))
    return duplicates


def collect_name_occurrences(app_files: list[Path]) -> dict[str, set[Path]]:
    index: dict[str, set[Path]] = defaultdict(set)
    for path in app_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for name in set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", text)):
            index[name].add(path)
    return index


def build_dead_candidates(
    symbols: list[PublicSymbol],
    imported_symbols: dict[tuple[str, str], set[Path]],
    reexports: set[str],
    occurrence_index: dict[str, set[Path]],
) -> list[PublicSymbol]:
    candidates: list[PublicSymbol] = []
    for symbol in symbols:
        if symbol.name in reexports:
            continue
        direct_importers = imported_symbols.get((symbol.module, symbol.name), set())
        occurrences = occurrence_index.get(symbol.name, set()) - {symbol.path}
        if direct_importers:
            continue
        if occurrences:
            continue
        candidates.append(symbol)
    return sorted(candidates, key=lambda item: (item.path.as_posix(), item.lineno, item.name))


def group_core_files(repo_root: Path, core_files: list[Path]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for path in core_files:
        rel = path.relative_to(repo_root).as_posix()
        area = path.relative_to(repo_root / "app" / "core").parts[0]
        if area == "__init__.py":
            area = "root"
        groups[area].append(rel)
    return {key: sorted(value) for key, value in sorted(groups.items())}


def format_report(
    repo_root: Path,
    grouped_core_files: dict[str, list[str]],
    area_consumers: dict[str, set[Path]],
    wrappers: list[tuple[Path, list[str]]],
    duplicates: list[list[DuplicateFunction]],
    dead_candidates: list[PublicSymbol],
) -> str:
    lines: list[str] = []
    lines.append("# Auditoria de app/core")
    lines.append("")
    lines.append(f"Generado: {date.today().isoformat()}")
    lines.append("")
    lines.append("## 1. Fuentes de verdad detectadas")
    lines.append("")
    for area, files in grouped_core_files.items():
        lines.append(f"- `{area}`: {len(files)} modulo(s)")
        for file_path in files:
            lines.append(f"  - `{file_path}`")
    lines.append("")
    lines.append("## 2. Consumidores directos fuera de core")
    lines.append("")
    if area_consumers:
        for area, consumers in sorted(area_consumers.items()):
            lines.append(f"- `{area}`: {len(consumers)} archivo(s) consumidor(es)")
    else:
        lines.append("- No se detectaron imports directos desde `app.core` fuera de `app/core`.")
    lines.append("")
    lines.append("## 3. Wrappers o facades fuera de core")
    lines.append("")
    if wrappers:
        for path, modules in wrappers:
            rel = path.relative_to(repo_root).as_posix()
            modules_str = ", ".join(f"`{module}`" for module in modules)
            lines.append(f"- `{rel}` -> {modules_str}")
    else:
        lines.append("- No se detectaron wrappers puros de `app.core`.")
    lines.append("")
    lines.append("## 4. Duplicacion estructural en app/core")
    lines.append("")
    if duplicates:
        for group in duplicates[:12]:
            title = f"`{group[0].qualified_name.split('.')[-1]}` repetido en {len(group)} ubicaciones"
            lines.append(f"- {title}")
            for item in group:
                rel = item.path.relative_to(repo_root).as_posix()
                lines.append(f"  - `{rel}:{item.lineno}` -> `{item.qualified_name}`")
    else:
        lines.append("- No se detectaron funciones o metodos con cuerpo identico.")
    lines.append("")
    lines.append("## 5. Candidatos de codigo muerto")
    lines.append("")
    if dead_candidates:
        for symbol in dead_candidates[:30]:
            rel = symbol.path.relative_to(repo_root).as_posix()
            lines.append(f"- `{rel}:{symbol.lineno}` -> `{symbol.name}` ({symbol.kind})")
    else:
        lines.append("- No se detectaron candidatos fuertes con este criterio estatico.")
    lines.append("")
    lines.append("## 6. Notas")
    lines.append("")
    lines.append("- Los candidatos de codigo muerto se calculan de forma estatica y deben validarse antes de borrar.")
    lines.append("- Los wrappers detectados no son necesariamente un problema, pero si un indicador de capa legacy o compatibilidad.")
    lines.append("- La duplicacion estructural apunta a puntos naturales de centralizacion; no implica que todos deban abstraerse del mismo modo.")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    repo_root = Path(args.root).resolve()
    app_root = repo_root / "app"
    core_root = app_root / "core"
    if not core_root.exists():
        raise SystemExit(f"No se encontro {core_root}")

    all_app_files = iter_python_files(app_root)
    core_files = [path for path in all_app_files if core_root in path.parents or path == core_root]
    external_files = [path for path in all_app_files if not (core_root in path.parents or path == core_root)]
    if not args.include_tests:
        external_files = [path for path in external_files if "tests" not in path.parts]

    grouped_core_files = group_core_files(repo_root, core_files)
    symbols = collect_public_symbols(repo_root, core_files)
    reexports = collect_reexports(core_files)
    _, imported_symbols, area_consumers = collect_external_imports(repo_root, external_files)
    wrappers = detect_wrapper_modules(external_files)
    duplicates = collect_duplicate_functions(core_files)
    occurrence_index = collect_name_occurrences(all_app_files)
    dead_candidates = build_dead_candidates(symbols, imported_symbols, reexports, occurrence_index)
    report = format_report(
        repo_root=repo_root,
        grouped_core_files=grouped_core_files,
        area_consumers=area_consumers,
        wrappers=wrappers,
        duplicates=duplicates,
        dead_candidates=dead_candidates,
    )

    if args.write:
        output_path = (repo_root / args.write).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
