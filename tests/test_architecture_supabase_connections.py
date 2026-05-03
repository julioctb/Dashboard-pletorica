"""Architecture guardrails for Supabase client creation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
ALLOWED_FILE = APP_DIR / "database" / "connection.py"


def test_supabase_client_is_created_only_in_connection_module() -> None:
    violations: list[str] = []

    for py_file in sorted(APP_DIR.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        if py_file == ALLOWED_FILE:
            continue

        text = py_file.read_text(encoding="utf-8")
        if "create_client(" in text:
            violations.append(str(py_file.relative_to(ROOT)))

    assert not violations, "\n".join(
        [
            "Supabase create_client() must be centralized in app/database/connection.py:",
            *violations,
        ]
    )
