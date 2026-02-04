# Prompt Library

## Run Dev Server (Docker)
- When to use: Start the Django dev server inside the canonical container with live code reload via bind mount.
- Prompt: `docker compose up app-dev`

## Run Test Suite (Docker)
- When to use: Execute Django tests in the isolated test container.
- Prompt: `docker compose run --rm app-test`

## Rebuild Application Image
- When to use: Rebuild the Docker image after dependency or base image changes.
- Prompt: `docker compose build app-dev`

## Follow Structured Logs
- When to use: Inspect JSON-formatted logs from the running dev container.
- Prompt: `docker compose logs -f app-dev`

## Full Setup (Docker + Logging + Docs)
- When to use: Recreate the baseline Docker configuration, structured logging, and context docs in a fresh checkout.
- Prompt: >
  Add Dockerfile, docker-compose (dev/test/prod), .dockerignore, env-driven settings overrides with JSON stdout logging, and refresh CONTEXT.md/CHANGELOG.md/PROMPTS.md to match.

## Prepare Env File
- When to use: Create the runtime env file from the provided example before running containers.
- Prompt: `cp .env.django.example .env.django` (or Windows copy equivalent) and fill real values.

## Recalculate Verbrauch (Docker)
- When to use: Refresh all calculated VerbrauchData rollups before reporting or after data edits.
- Prompt: `docker compose run --rm app-dev python manage.py recalc_verbrauch`

## Run Test Suite (after recalc changes)
- When to use: Validate logging and Verbrauch recalc flows.
- Prompt: `docker compose run --rm app-test`

## Re-run Bilanz/Verbrauch Integration Test
- When to use: Confirm Bilanz reflects updated Verbrauch rollups after edits.
- Prompt: `docker compose run --rm app-test`

## Refresh KLIK Total (code 1) from 1.4
- When to use: Ensure Kraft/Licht totals align with recalculated electricity after edits.
- Prompt: `docker compose run --rm app-dev python manage.py recalc_verbrauch`

## Reduce Dev Log Noise
- When to use: Ensure per-query debug logs are disabled.
- Prompt: `# already set: DJANGO_LOG_LEVEL=INFO; django.db.backends logger at WARNING in settings`

## Verify Prozesswärme mapping (code 3.7)
- When to use: Confirm Bilanz uses VerbrauchData code `3.7` for Prozesswärme totals.
- Prompt: `docker compose run --rm app-test`

## Trigger WS Recalc from Verbrauch/Renewables
- When to use: Ensure WSData is in sync after data edits.
- Prompt: `docker compose run --rm app-dev python manage.py recalc_verbrauch` (then refresh views; signals also recalc WS on saves)

## Update WS trigger codes
- When to use: If WS recalculation needs to listen to additional Verbrauch codes.
- Prompt: Edit `ws_trigger_codes` in `simulator/signals.py` and redeploy/restart.

## Gebaeudewaerme (deprecated)
- When to use: (Reference only) Run the deprecated Gebaeudewaerme recalc command if needed.
- Prompt: `docker compose run --rm app-dev python manage.py recalc_gebaeudewaerme`

## Force Renewable Recalc after Verbrauch edits
- When to use: Renewables with `VerbrauchData_*` formulas already recalc on save; use this if bulk edits bypass saves.
- Prompt: `docker compose run --rm app-dev python manage.py recalc_verbrauch` (triggers renewable refresh via signals)

## Throttle LandUse Cascades Hitting Verbrauch
- When to use: LandUse saves are slow or hanging because each dependent Renewable save triggers full Verbrauch recomputation.
- Prompt: >
  Add a `skip_verbrauch_recalc` flag to `RenewableData.save`, guard the Renewable post_save signal to honor it, and have LandUse→Renewable cascades save dependents with that flag so WS recalcs still run but Verbrauch recalc is skipped; update CONTEXT/CHANGELOG and validate with `docker compose run --rm app-test`.

## Run Full Recalculation (manual, staged flow)
- When to use: After editing LandUse/Verbrauch data, trigger one explicit pass to refresh Renewable, Verbrauch, and WS data and store a CalculationRun snapshot.
- Prompt: >
  POST to `/api/run-full-recalc/` (logged-in) or click “Calculate & Continue” on the LandUse page; this runs `run_full_recalc()` once (single transaction, bulk WS update), records a CalculationRun, and redirects to the Renewable page with `run_id` for metadata.
  Ensure CSRF token is sent (header `X-CSRFToken` from cookie or hidden input).

## Update Renewable Formula (example: 9.2.1.2)
- When to use: If a renewable code needs a formula combining Verbrauch and renewable components.
- Prompt: >
  Edit `calculation_engine/renewable_engine.py` entry for the code, set the formula string (e.g., `IF(VerbrauchData_4.3.5 > (5.4.4.2 + 6.1.3.1.1 + 6.2.3); VerbrauchData_4.3.5 - (5.4.4.2 + 6.1.3.1.1 + 6.2.3); 0)` for 9.2.1.2), keep `is_fixed=False`, and rerun tests via `docker compose run --rm app-test`.

## Balance Bilanz (bracketed binary)
- When to use: Close the Bilanz gap (Verbrauch ziel vs renewable total 10.1) by scaling Solar (LU_2.1) or Wind (LU_1.1) targets using the bracketed binary solver (renewables-only).
- Prompt: >
  POST to `/api/balance-energy` with JSON `{ "driver": "solar" | "wind", "tolerance": 1.0 }`; the API brackets the Bilanz gap (erneuerbar gesamt vs verbrauch gesamt), expands/contracts LU_2.1 or LU_1.1, then binary-searches to tolerance, recalculating renewables only and persisting locked `target_ha`. Response includes bracket/midpoint history and `final_gap`.
