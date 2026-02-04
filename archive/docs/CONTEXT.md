# Project Overview
- 100ProSim is a Django 4.2 energy simulation app covering land use, renewable supply, consumption, WS cascade data, and dashboard views; database is SQLite in this repo.
- Agent workflow is Docker-only; other developers may optionally use Python venv but Docker definitions are canonical for this project.

# Stack & Runtime
- Python 3.11 (container base), Django 4.2.24, SQLite.
- Containerized via `Dockerfile` and `docker-compose.yml` with services: `app-dev`, `app-test`, `app-prod`.
- Dependencies captured in `requirements.txt` (Django 4.2.24, pandas, numpy); container installs from this file.

# Directory Structure (high level)
- `landuse_project/` Django settings/urls/asgi/wsgi.
- `simulator/` main app (models, views, formulas, signals, templates, static).
- `calculation_engine/` calculation modules.
- `archive/scripts/`, `archive/old_test_scripts/`, `archive/old_migration_scripts/` hold utility and legacy scripts (not imported in web app).
- Data/CSV files at root and in `data/`; `db.sqlite3` in root.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore` added for container workflows; `.env.django.example` documents required env vars; `.env.django` included with placeholders for convenience (replace before real use).
- New helper: `simulator/verbrauch_recalculator.py` plus `python manage.py recalc_verbrauch` to refresh Verbrauch rollups.

# How to Run (Docker)
- Copy `.env.django.example` to `.env.django` and set real secrets/flags.
- Build image: `docker compose build app-dev`
- Dev server: `docker compose up app-dev`
- Test suite: `docker compose run --rm app-test`
- Prod-like server (same runserver entrypoint to avoid new deps): `docker compose up app-prod`
- Manual full recalculation: trigger from UI “Calculate & Continue” on LandUse page or POST `/api/run-full-recalc/` (requires login); this runs renewable + Verbrauch + WS recalcs once and records a CalculationRun snapshot.
- CSRF: recalc buttons send `X-CSRFToken` using cookie/hidden-input fallback; ensure you’re logged in so the token is present.

# Optional venv (other developers)
- `python -m venv .venv && .\\.venv\\Scripts\\activate`
- `pip install -r requirements.txt`
- `python manage.py migrate && python manage.py runserver`

# Logging Format
- Structured JSON to stdout via custom formatter in `landuse_project/settings.py`.
- Fields: `timestamp`, `level`, `component`, `file`, `line`, `function`, `message`, `eventType`, `context`, `stack`.
- Example line:  
  `{"timestamp":"2025-11-24T00:00:00Z","level":"info","component":"simulator.views","file":"/app/simulator/views.py","line":42,"function":"landuse_list","message":"request handled","eventType":"request","context":{"path":"/landuse/"},"stack":null}`

# Known Issues
- Secret key still defaults to a committed value; override via `DJANGO_SECRET_KEY` for any real deployment (placeholder present in `.env.django`).
- Requirements now pinned in `requirements.txt`; keep aligned with Dockerfile installs.
- Basic structured-logging tests added in `simulator/tests.py`; broader coverage still needed.
- Verbrauch calculation engine stub (`calculation_engine/verbrauch_engine.py`) is unused and returns stored status/ziel values; actual Verbrauch calculations live in `simulator/verbrauch_calculations.py`.
- Bilanz calculations (`calculation_engine/bilanz_engine.py`) pull VerbrauchData values directly (no recalculation trigger), so stale/hand-set values will surface unless upstream data is refreshed.
- Gebaeudewaerme calculation stubs still return None; update if those values must be calculated.
- Cascades currently rely on the new `recalc_verbrauch` helper for Verbrauch rollups; ensure it is run (automatically via save hook or manually via management command) when bulk edits occur.
- Automatic WS/Verbrauch recalcs in signals are disabled; heavy recalculation is explicit via the “Calculate & Continue” button or `/api/run-full-recalc/`.
- Migration `0025_calculationrun.py` (new `CalculationRun` snapshot model) is created but not applied; run migrations inside Docker if you need the table.

# Suspected Unused / Legacy Files
- `simulator/models.py.bak`, `simulator/models.py.bak2` (backups).
- Legacy utilities moved to `archive/scripts/`, `archive/old_test_scripts/`, `archive/old_migration_scripts/`; not part of runtime.
- `calculation_engine/verbrauch_engine.py` (TODO stub, not called by views/models).

# Doc vs Code Inconsistencies
- PROJECT_DOCUMENTATION.md marks `.bak` model files as candidates for deletion yet they still exist in the repo.
- Documentation lists venv workflow; canonical Docker workflow was missing and is now introduced here.

# Decisions Log
- Added Dockerfile and docker-compose with dev/test/prod services using runserver entrypoints to avoid adding new dependencies.
- Added structured JSON logging configuration emitted to stdout with env-driven log level.
- Introduced `.dockerignore` to reduce build context noise.
- Added `requirements.txt`, `.env.django.example`, and placeholder `.env.django` for reproducible installs and env guidance.
- Added JSON logging unit tests in `simulator/tests.py`.
- Added Verbrauch recalculation helper and management command; Bilanz now triggers a refresh before reading VerbrauchData.
- Added integration test to confirm Bilanz reflects updated Verbrauch rollups after child edits.
- KLIK total (code `1`) now recalculates from code `1.4` even if not flagged calculated; recalc helper always processes top-level rollups.
- Dev logging: `DJANGO_LOG_LEVEL` set to INFO for app-dev; `django.db.backends` forced to WARNING to prevent per-query debug spam.
- SQLite tuned with `timeout=30` to mitigate “database is locked” during concurrent admin saves/recalcs.
- Bilanz now pulls Prozesswärme totals from VerbrauchData code `3.7` (Endenergieverbrauch PW gesamt) instead of `3.3`.
- Signals updated: Renewable save triggers Verbrauch recalc plus WS recalculation for relevant codes; Verbrauch save triggers WS recalculation for WS-relevant codes (`ws_trigger_codes` in `simulator/signals.py`).
- Gebaeudewaerme recalculation is deprecated/inactive; the helper/command remain for reference only (no integration with Bilanz/WS/Renewables).
- Renewables with `VerbrauchData_*` formulas are recalculated on any Verbrauch save (helper in `simulator/renewable_recalc.py` with manual fallback for non-registry formulas).
- Backup model files moved to `archive/simulator/` to avoid confusion.
- Added manual staged recalculation flow: `CalculationRun` snapshot model, `/api/run-full-recalc/` endpoint, and LandUse “Calculate & Continue” button trigger one explicit renewable/Verbrauch/WS recompute and store run metadata; automatic WS/Verbrauch recalcs in signals are disabled to prevent admin-time locks.
- Renewables page now has a “Recalculate Now” button that posts to the recalc endpoint (CSRF-safe) and reloads with the latest run id; both LandUse and Renewables display the latest CalculationRun metadata.
- Added skip flag on `RenewableData.save` and corresponding signal guard so LandUse cascades no longer trigger full Verbrauch recomputation per dependent; WS recalcs still run for renewable codes relevant to WS.
- LandUse targets can be locked: `target_locked` is set when `target_ha` is manually edited to prevent parent cascades from overwriting. Manual target updates (now locked) applied for LU_0, LU_1, LU_1.1, LU_2, LU_2.1, LU_2.2, LU_2.2.1, LU_2.2.2, LU_2.2.3, LU_2.2.4, LU_2.2.5, LU_2.2.6, LU_2.3, LU_2.4, LU_3, LU_3.1, LU_3.2, LU_4, LU_5, LU_6.
- RenewableData `9.2.1.2` now uses formula `IF(VerbrauchData_4.3.5 > (5.4.4.2 + 6.1.3.1.1 + 6.2.3); VerbrauchData_4.3.5 - (5.4.4.2 + 6.1.3.1.1 + 6.2.3); 0)` to blend Verbrauch and renewable inputs.
- Bilanz page shows CalculationRun metadata; manual button removed/refresh-only to avoid incorrect balance outputs—Bilanz reflects stored values on load. Base template exposes an `extra_js` block for page scripts; LandUse saves do not auto-run full recalc—use explicit recalc triggers where needed. Balance endpoint supports WS driver (adjusts `stromverbr_raumwaerm_korr` row 366) in addition to solar/wind.
- Bilanz balance button now uses binary search without WS: choosing Solar or Wind brackets and bisects the corresponding `target_ha` to close the renewable total 10.1 vs Verbrauch gap within tolerance (default 1 GWh), recalculating renewables + Verbrauch only; landuse `target_ha` is persisted/locked.
- Bilanz sector renewable rows now read RenewableData codes 10.3 (KLIK), 10.4 (Gebäudewärme), 10.5 (Prozesswärme), 10.6 (Mobile) directly instead of proportional splits.
- Balance flow includes a fast slope probe before a capped binary search (max 6 steps) to reduce runtime; WS recalculation is skipped for these balances.
- Balance solver now brackets and binary-searches LU_2.1 or LU_1.1 to close the Bilanz gap using the same figures as the Bilanz view (erneuerbar gesamt vs verbrauch gesamt), recalculating renewables only; tolerance 1 GWh by default (no WS/Verbrauch recalc).

# Quick Reference (Codex Onboarding)
- Run dev: `docker compose up app-dev`; Tests: `docker compose run --rm app-test`.
- Recalc after bulk edits: `docker compose run --rm app-dev python manage.py recalc_verbrauch` (triggers dependent renewables; WS recalcs via signals on relevant codes).
- Cascades: LandUse→Renewable; Verbrauch save→rollups, dependent renewables, WS (codes 2.9.2/2.4); Renewable save→Verbrauch refresh + WS (renewable codes in signals).
- Bilanz: reads refreshed Renewable/Verbrauch; Prozesswärme from Verbrauch code 3.7; KLIK total from 1.4.
- Archive: legacy scripts and backup models in `archive/` (not used at runtime).
- WS recalculation is scoped to Verbrauch codes `2.9.2` and `2.4` (adjust `ws_trigger_codes` in `simulator/signals.py` if WS gains more Verbrauch inputs).
