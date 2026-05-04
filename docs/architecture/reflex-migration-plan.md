# Reflex Architecture Migration Plan

## Objective

Standardize project patterns and enforce the boundary:

`presentation/state -> domain/services -> repositories -> database`

## Execution Phases

1. Baseline inventory of mixed structures and direct database access points.
2. Define architecture contract and PR checklist.
3. Strengthen service layer for use cases still solved in State.
4. Remove direct Supabase usage from presentation and route through services.
5. Standardize feature structure around `page.py`, `state.py`, and companion modules.
6. Add guardrails and automated checks.
7. Verify critical flows across backoffice, portal, and API.

## Current Status

- Direct Supabase access removed from `app/presentation/**`.
- Added a dedicated bridge service for legacy operations:
  - `app/domain/services/presentation_bridge_service.py`
- Added architecture guard test:
  - `tests/test_architecture_presentation_boundaries.py`

## PR Checklist

- No usage of `db_manager.get_client()` in `app/presentation/**`.
- No usage of `supabase.table(...)` in `app/presentation/**`.
- No usage of `supabase.storage...` in `app/presentation/**`.
- New features follow neighboring structure and prefer modular page layout.
- Form validation and domain validation both present when business-critical.

## Notes

- Existing legacy pages can remain in place while internals move to service orchestration.
- Prefer incremental migrations by feature to reduce regression risk.
