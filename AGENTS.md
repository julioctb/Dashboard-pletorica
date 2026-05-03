# AGENTS.md

Compact repo guidance for future OpenCode sessions. For deeper architecture notes, read `CLAUDE.md`; if prose conflicts with executable code, trust the files named below.

## Sources Of Truth

- App composition starts at `app/app.py`, which calls `create_app()` in `app/bootstrap/app_factory.py`.
- Reflex routes are defined in `app/presentation/config/routes.py` and registered by `app/bootstrap/routes_core.py`, `routes_backoffice.py`, and `routes_portal.py`.
- FastAPI is mounted into Reflex via `api_transformer=api_app`; API entrypoint is `app/api/main.py`, and v1 routers are registered in `app/api/v1/router.py`.
- Runtime/dependency truth is `pyproject.toml` plus `poetry.lock`; `requirements.txt` is partial/deploy-oriented and can lag app deps.
- Reflex config is `rxconfig.py`: `REFLEX_USE_GRANIAN=true`, React StrictMode disabled, `SitemapPlugin` and `TailwindV4Plugin` enabled.

## Commands

- Install: `poetry install`.
- Run app: `poetry run reflex run`.
- Reinitialize Reflex when generated state is broken: `poetry run reflex init`.
- Default tests from config: `poetry run pytest -q` discovers `core/tests` and `tests`; it does not discover `app/tests/`.
- Feature tests under `app/tests/` must be targeted explicitly, for example `poetry run pytest app/tests/test_validation.py -q` or `poetry run pytest app/tests -q`.
- Quality commands are manual; no root CI/pre-commit config exists: `poetry run black app/`, `poetry run isort app/`, `poetry run flake8 app/`, `poetry run mypy app/`.

## Environment And Tests

- Tests are designed to run offline: `tests/conftest.py` supplies fallback Supabase env vars and blocks outbound network calls except localhost.
- Switch `.env` with `./scripts/use-local.sh`, `./scripts/use-cloud.sh`, or `./scripts/switch_env.sh local|cloud [--dry-run]`; the script backs up the current `.env`.
- Local env switch suggests `npx supabase start`; cloud switch suggests `npx supabase stop`.
- `SKIP_AUTH=true` disables app auth for development.
- `DatabaseManager.get_client()` can use `SUPABASE_SERVICE_KEY` and bypass RLS; enforce permission checks in services/state, not only in RLS.

## Architecture Rules That Prevent Mistakes

- The repo has three surfaces: backoffice Reflex, portal Reflex, and a limited FastAPI API under `/api/v1/*`.
- `/` is a role/context dispatcher, not the main dashboard; backoffice starts at `/admin`, portal at `/portal`.
- Keep business logic out of Reflex render functions and components; normal flow is `presentation/state -> domain/services -> domain/repositories -> database`.
- UI and components should not query Supabase directly; put orchestration in `State`, business rules in `app/domain/services/`, and complex data access in repositories.
- Guardrail: `app/presentation/**` must not call `db_manager.get_client()`, `supabase.table(...)`, or `supabase.storage...` directly. Use services (for legacy bridge cases: `presentation_bridge_service`) and keep database calls out of page/state modules.
- `app/modules/*` are mostly DDD facades over legacy `app/domain/*`; do not assume the real logic lives in the module directory.
- Before choosing a state base, inspect the neighboring feature: common bases include `AuthState`, `PortalState`, `NominaBaseState`, and `CRUDStateMixin` combinations.
- For Reflex reactive rendering, use `rx.cond(...)` and `rx.foreach(...)`; keep `@rx.var` pure and cheap and prefer explicit setters in `State`.
- Validation intentionally exists in two layers: form validators in `presentation/pages/.../*validators.py` and domain/core validators in `app/domain/` or `app/core/validation/`.

## API And Migrations

- Do not infer an API endpoint from a UI page; API coverage is intentionally limited.
- New API modules use `app/api/v1/<module>/router.py` and `schemas.py`, then register the router in `app/api/v1/router.py`.
- SQL migrations live in `migrations/` and are applied manually in Supabase; numbering has duplicates/gaps, so inspect existing filenames before adding a new one.

## Placement Conventions

- For new UI features prefer the modular page shape (`page.py`, `state.py`, `components.py`, `modal.py`) unless the neighboring feature uses the legacy `*_page.py`, `*_state.py`, `*_modals.py`, `*_validators.py` style.
- Reuse shared UI from `app/presentation/components/ui`, `shared`, `common`, and existing backoffice component folders before adding new widgets.
- `wip/` is explicitly non-production and not in the Python package tree; do not import from it.
