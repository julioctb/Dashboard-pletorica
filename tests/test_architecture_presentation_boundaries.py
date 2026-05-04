"""Architecture guardrails for presentation-layer boundaries."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = ROOT / "app" / "presentation"


def _iter_python_files() -> list[Path]:
    return sorted(
        path
        for path in PRESENTATION_DIR.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def test_presentation_does_not_use_direct_supabase_client() -> None:
    forbidden_tokens = (
        "db_manager.get_client(",
        "supabase.table(",
        "supabase.storage",
    )
    violations: list[str] = []

    for py_file in _iter_python_files():
        text = py_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                rel = py_file.relative_to(ROOT)
                violations.append(f"{rel}: contains `{token}`")

    assert not violations, "\n".join(["Forbidden direct Supabase usage in presentation:", *violations])
