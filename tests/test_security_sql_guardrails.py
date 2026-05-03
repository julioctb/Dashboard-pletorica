"""Static guardrails for sensitive Supabase SQL patterns."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "065_harden_auth_metadata_and_private_helpers.sql"


def test_latest_security_migration_uses_private_trigger_and_safe_default_role() -> None:
    text = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE OR REPLACE FUNCTION private.handle_new_user()" in text
    assert "EXECUTE FUNCTION private.handle_new_user();" in text
    assert "NEW.raw_user_meta_data->>'rol'" not in text
    assert "'client'" in text


def test_app_code_does_not_send_role_inside_auth_metadata() -> None:
    user_profile_model = (ROOT / "app" / "domain" / "models" / "user_profile.py").read_text(
        encoding="utf-8"
    )
    assert "'rol':" not in user_profile_model
