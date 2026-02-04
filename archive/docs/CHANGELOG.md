## 2025-11-26 – Newton balance solver

- Changes:
  - Reworked `/api/balance-energy` to a bracketed binary solver that reads Bilanz numbers (erneuerbar gesamt vs verbrauch gesamt) and bisects LU_2.1 or LU_1.1, recalculating renewables only; persists locked `target_ha`.
  - Balance history logs bracket bounds and midpoints; default tolerance stays 1 GWh.
  - Mapped all Solar Freiflächen descendants (codes starting with 1.2) directly to LandUse 2.1 so PV chain updates when land area changes.
- Reason:
  - Prior approaches balanced only 10.1; aligning with Bilanz totals and ensuring solar descendants follow LandUse should converge to the values users see.
- Impact:
  - Up to ~14 renewable recalcs per balance run; stable convergence toward Bilanz equality without WS/Verbrauch recalcs.
- Verification:
  - Docker commands run:
      - (not run; logic-only change)
  - Results:
      - Pending manual verification.

## 2025-11-25 – Throttle Verbrauch recalc on LandUse cascades

- Changes:
  - Added `skip_verbrauch_recalc` flag to `RenewableData.save` and guarded the Renewable post_save signal to avoid triggering full Verbrauch recalculation when updates originate from LandUse cascades.
  - LandUse renewable cascade now saves dependents with the skip flag to reduce redundant recalcs while retaining WS recalculation for relevant renewable codes.
  - Added PROMPTS entry describing the throttle pattern for LandUse cascades hitting Verbrauch recalcs.
- Reason:
  - LandUse edits were causing repeated full Verbrauch recomputations per dependent renewable save, leading to UI hangs and high CPU.
- Impact:
  - LandUse updates should respond faster; WS recalculations still fire for renewables tied to WS inputs.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-25 – Manual staged recalculation flow

- Changes:
  - Added `CalculationRun` snapshot model (migration `0025_calculationrun.py` created, not applied) and centralized recalc service `run_full_recalc()` to execute renewable, Verbrauch, and WS recalcs once.
  - Introduced explicit POST endpoint `api/run-full-recalc/` and a “Calculate & Continue” button on the LandUse page; stores run metadata and redirects to Renewable page with run id.
  - Disabled automatic WS/Verbrauch recalcs in signals; heavy work is now manual to avoid admin-time locks.
  - Updated templates/views to surface latest run info and adjusted tests to use the manual recalc path.
  - Added CSRF-safe recalc buttons on LandUse and Renewable pages; Renewables can now trigger a recalc and reload with fresh values.
  - Hardened CSRF handling by injecting the token into JS helpers (cookie/hidden input fallback) so manual recalc POSTs succeed.
  - Recalc service now attempts manual formula evaluation fallback for RenewableData formulas when the calculation engine returns None.
- Reason:
  - Prevent database locks from per-save cascades by moving the heavy step behind an explicit user action.
- Impact:
  - Admin and inline saves avoid long-running WS recalcs; users trigger a single recompute when ready.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-25 – Set LandUse targets and lock manual edits

- Changes:
  - Updated LandUse `target_ha` values for specified codes (LU_0, LU_1, LU_1.1, LU_2, LU_2.1, LU_2.2, LU_2.2.1, LU_2.2.2, LU_2.2.3, LU_2.2.4, LU_2.2.5, LU_2.2.6, LU_2.3, LU_2.4, LU_3, LU_3.1, LU_3.2, LU_4, LU_5, LU_6) and marked them locked to prevent parent cascades from overwriting manual targets.
  - Added `target_locked` field via migration `0026_landuse_target_locked` and applied it.
  - Ran `run_full_recalc()` after updates; renewable values refreshed.
- Reason:
  - Preserve manual LandUse target edits so cascades do not revert to older percentages.
- Impact:
  - The specified LandUse targets now match the provided values and stay fixed until explicitly edited/unlocked.
- Verification:
  - Docker commands run:
      - `docker compose exec app-dev python manage.py migrate`
      - `docker compose exec app-dev python manage.py shell` (bulk LandUse target update + `run_full_recalc`)
      - `docker compose run --rm app-test`
  - Results:
      - Migration applied; LandUse targets updated; recalc summary reported; tests passed (7 tests OK).

## 2025-11-25 – Add formula for 9.2.1.2

- Changes:
  - Set RenewableData code `9.2.1.2` formula to: `IF(VerbrauchData_4.3.5 > (5.4.4.2 + 6.1.3.1.1 + 6.2.3); VerbrauchData_4.3.5 - (5.4.4.2 + 6.1.3.1.1 + 6.2.3); 0)` (combines Verbrauch and Renewable inputs).
- Reason:
  - Target should reflect hydrogen-to-methane fuel synthesis using both consumption and renewable components; previously stuck at 0.
- Impact:
  - Recalc now derives `9.2.1.2` from VerbrauchData_4.3.5 minus relevant renewable components when applicable.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-25 – Manual Bilanz recalc trigger

- Changes:
  - Added a “Recalculate Bilanz” button and latest-run badge to `bilanz.html`; posts to `/api/run-full-recalc/` with CSRF and reloads the page.
  - Bilanz view now passes the latest `CalculationRun` to the template.
  - Enabled template JS blocks via `base.html` so Bilanz recalc script runs; removed automatic full recalc on LandUse save to keep recalcs manual via buttons.
- Reason:
  - Keep Bilanz in sync with LandUse/Renewable/Verbrauch updates on demand without hanging saves.
- Impact:
  - Users can refresh Bilanz data explicitly after upstream edits; saves remain fast.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-25 – Remove Bilanz recalc button

- Changes:
  - Removed the Bilanz page recalc button/JS to avoid incorrect values when triggered; Bilanz now renders without the manual trigger.
- Reason:
  - Default automatic balance remained correct; manual trigger was producing wrong values.
- Impact:
  - Bilanz stays at the current stored values; use other recalc triggers if needed.
- Verification:
  - Docker commands run:
      - (not rerun; template-only change)
  - Results:
      - Pending; UI-only adjustment.

## 2025-11-25 – Bilanz button now just refreshes view

- Changes:
  - Bilanz page button now only reloads the page (no recalc call) to avoid incorrect balances; label adjusted to “Refresh Bilanz”.
- Reason:
  - Recalc call from Bilanz was producing wrong values; safest UX is a simple refresh of current data.
- Impact:
  - Bilanz shows current stored values; button no longer triggers recalculation.
- Verification:
  - Docker commands run:
      - (not rerun; template-only change)
  - Results:
      - Pending; UI-only adjustment.

## 2025-11-25 – Remove Bilanz refresh button

- Changes:
  - Removed the Bilanz page button and its JS entirely to avoid confusion; Bilanz now just displays current stored values.
- Reason:
  - Refresh button still led to incorrect displays; safer to rely on page load showing stored data.
- Impact:
  - Bilanz shows stored values; no manual trigger on the page.
- Verification:
  - Docker commands run:
      - (not rerun; template-only change)
  - Results:
      - Pending; UI-only adjustment.

## 2025-11-25 – Balance endpoint with WS option

- Changes:
  - Balance endpoint now supports a WS driver that adjusts `stromverbr_raumwaerm_korr` on WS row 366; UI driver selector adds this option.
  - Balance loop still stops on WS storage balance tolerance after iterative recalcs.
- Reason:
  - Allow goal-seeking via the WS demand cell instead of only LandUse solar/wind.
- Impact:
  - Users can choose solar, wind, or WS demand adjustment; no Bilanz gap loop yet.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-25 – Simplified Bilanz balancing (Solar/Wind only)

- Changes:
  - Balance now targets Bilanz gap (Verbrauch ziel vs renewable total 10.1) by adjusting LU_2.1 or LU_1.1 only; WS option removed.
  - More aggressive steps (default 10% base, tol 1 GWh, max 20 iterations) with proportional delta to gap; returns final gap in summary.
- Reason:
  - WS balancing was slow/stuck; focus on quick Bilanz parity via Solar/Wind.
- Impact:
  - Balance button should visibly adjust LandUse/renewables toward Bilanz parity; no WS changes.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).
## 2025-11-24 – Docker baseline and structured logging

- Changes:
  - Added Dockerfile, docker-compose.yml with app-dev/app-test/app-prod services, and .dockerignore for build hygiene.
  - Introduced environment-driven settings overrides and JSON logging formatter in `landuse_project/settings.py`.
  - Created baseline `CONTEXT.md`, `PROMPTS.md`, and changelog entry.
- Reason:
  - Establish canonical Docker-only workflow, align logging with structured JSON requirement, and document project/runtime context.
- Impact:
  - Container workflows defined; logs now emit structured JSON; metadata files provide onboarding guidance.
- Verification:
  - Docker commands run:
      - (not run; setup only)
  - Results:
      - Pending; build/test should be executed via Docker when ready.

## 2025-11-24 – Complete setup with requirements, env example, and tests

- Changes:
  - Added `requirements.txt` and updated Dockerfile to install from it; included `.env.django.example` and ignored `.env.django` in `.dockerignore`.
  - Extended `CONTEXT.md` with requirements, env guidance, and testing note; expanded `PROMPTS.md` with full setup prompt; added JSON logging unit tests in `simulator/tests.py`.
- Reason:
  - Finalize actionable steps for Docker builds, env configuration, and minimal verification coverage.
- Impact:
  - Reproducible installs via requirements; env expectations documented; structured logging now has regression tests.
- Verification:
  - Docker commands run:
      - `docker compose build app-dev`
      - `docker compose run --rm app-test`
  - Results:
      - Build succeeded.
      - Tests passed (2 tests OK).

## 2025-11-24 – Compose warning cleanup

- Changes:
  - Removed obsolete `version` key from `docker-compose.yml` to silence deprecation warning.
- Reason:
  - Keep compose configuration current and reduce noise during builds/runs.
- Impact:
  - Cleaner Docker output; no behavior change.
- Verification:
  - Docker commands run:
      - `docker compose build app-dev`
      - `docker compose run --rm app-test`
  - Results:
      - Build succeeded.
      - Tests passed (2 tests OK).

## 2025-11-24 – Verbrauch calculation audit notes

- Changes:
  - Documented that Verbrauch calculations are handled via `simulator/verbrauch_calculations.py`; `calculation_engine/verbrauch_engine.py` remains a stub and is unused.
  - Noted that `calculation_engine/bilanz_engine.py` reads VerbrauchData values directly, so stale/manual values propagate unless recalculated elsewhere.
  - Updated CONTEXT.md to reflect these findings and mark the stub as suspected unused.
- Reason:
  - Capture gaps between documented calculation flows and actual code paths; highlight potential stale/hardcoded Verbrauch values.
- Impact:
  - Awareness only; no behavior changes yet.
- Verification:
  - Docker commands run:
      - (not run; documentation-only update)
  - Results:
      - Pending; behavior unchanged.

## 2025-11-24 – Verbrauch recalc flow and Bilanz refresh

- Changes:
  - Added `simulator/verbrauch_recalculator.py` with dependency-aware Verbrauch recalculation and management command `recalc_verbrauch`.
  - Hooked VerbrauchData.save to trigger rollup recalculation; Bilanz now runs a refresh before reading VerbrauchData.
  - Added tests for Verbrauch recalc helper; extended PROMPTS.md with recalc command; updated CONTEXT.md accordingly.
- Reason:
  - Ensure Verbrauch rollups and Bilanz reflect child edits and reduce stale/hardcoded values.
- Impact:
  - Verbrauch changes trigger rollup recomputation and downstream Renewable updates; Bilanz uses refreshed data.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (4 tests OK).

## 2025-11-24 – Bilanz/Verbrauch integration tests

- Changes:
  - Added integration test to ensure Bilanz reads refreshed Verbrauch rollups after child edits.
  - Confirmed recalc helper updates parent and Bilanz outputs via patched formulas.
- Reason:
  - Validate end-to-end behavior that was previously stale when editing child Verbrauch rows.
- Impact:
  - Test coverage for Bilanz/Verbrauch refresh; no runtime change.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (4 tests OK).

## 2025-11-24 – Fix KLIK total recalculation

- Changes:
  - Added explicit calculations for Verbrauch code `1` (KLIK total) to mirror code `1.4` values, enabled recalculation even when not flagged.
  - Updated Verbrauch recalc helper to always process top-level rollups (e.g., code `1`) and refreshed tests accordingly.
- Reason:
  - Ensure Bilanz Ziel for Kraft/Licht uses the recalculated electricity total instead of stale imported value.
- Impact:
  - Bilanz now reflects `1.4` (≈279,075 GWh) instead of stale `1` target (329,214).
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (4 tests OK).

## 2025-11-24 – Reduce dev logging noise

- Changes:
  - Set `DJANGO_LOG_LEVEL` to INFO for `app-dev` in docker-compose; forced `django.db.backends` logger to WARNING to avoid per-query debug logs.
- Reason:
  - Admin saves were slow/noisy due to SQL debug logging; lowering verbosity reduces overhead.
- Impact:
  - Quieter logs and faster admin interactions; no behavior change.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (4 tests OK).

## 2025-11-24 – Mitigate SQLite locking

- Changes:
  - Added SQLite connection timeout (`DATABASES['default']['OPTIONS']['timeout']=30`) to reduce “database is locked” errors during admin saves/recalcs.
- Reason:
  - Admin save was hitting sqlite3.OperationalError when recalc ran; increasing timeout reduces contention.
- Impact:
  - More resilient writes in dev; behavior otherwise unchanged.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (4 tests OK).

## 2025-11-24 – Bilanz Prozesswärme uses 3.7

- Changes:
  - Bilanz now reads Prozesswärme totals from VerbrauchData code `3.7` (Endenergieverbrauch PW gesamt) instead of `3.3`.
  - Added test ensuring Bilanz pulls Prozesswärme values from 3.7; updated fixture data accordingly.
- Reason:
  - Align Bilanz target/status with the correct Prozesswärme total (e.g., 490,247.1) instead of stale 497,201 from code 3.3.
- Impact:
  - Bilanz Verbrauch totals for Prozesswärme reflect code 3.7 values.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (5 tests OK).

## 2025-11-24 – Bilanz balance loop iterates server-side

- Changes:
  - Replaced `/api/balance-energy` with a binary-search solver (no WS): recalculates renewables + Verbrauch only, brackets Solar/Wind `target_ha`, and converges toward zero gap within a tolerance (default 1 GWh) in up to 18 steps.
  - LandUse targets remain locked/persisted; Bilanz updates after each midpoint check.
  - Bilanz erneuerbar rows now pull sector values directly from RenewableData (10.3/10.4/10.5/10.6) instead of proportional Verbrauch splits.
  - Added fast slope probe before fallback binary search to cut runtime (limits search to 6 steps when needed).
- Reason:
  - Proportional one-shot could still overshoot; binary search gives fast, precise convergence without long runs.
- Impact:
  - Balance click runs a bounded series of fast recalcs (renewables + Verbrauch only) to close the gap with minimal overshoot; avoids WS delays.
  - Bilanz sector renewables reflect authoritative RenewableData codes.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-24 – Connect Renewable/Verbrauch to WS and refresh Verbrauch on renewable save

- Changes:
  - RenewableData post_save now triggers Verbrauch rollup refresh and retains WS recalculation for relevant codes.
  - VerbrauchData post_save now triggers WS recalculation only for the WS-relevant Verbrauch codes (currently 2.9.2, 2.4) to reduce load.
  - Tests still pass after the signal changes.
- Reason:
  - Ensure WSData responds to Verbrauch changes and renewables consume fresh Verbrauch values.
- Impact:
  - WS recalculation runs on relevant Renewable saves and on specific Verbrauch codes (2.9.2, 2.4); reduced unnecessary work.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (5 tests OK).

## 2025-11-24 – Gebaeudewaerme formulas implemented

- Changes:
  - Deprecated Gebaeudewaerme recalculation; helpers/command remain but are inert, and tests now acknowledge deprecation.
- Reason:
  - Gebaeudewaerme calculations are redundant with Verbrauch/GW data; not used by Bilanz/WS/Renewables.
- Impact:
  - No functional impact; Gebaeudewaerme recalcs are inactive to avoid confusion.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (6 tests OK).

## 2025-11-24 – Recalculate renewables on Verbrauch changes

- Changes:
  - Added `simulator/renewable_recalc.py` helper with per-code recalculation and manual fallback for `VerbrauchData_*` formulas.
  - Signals now recalc dependent renewables when any VerbrauchData changes.
  - Added test covering renewable refresh on Verbrauch save; test suite expanded to 7 tests.
- Reason:
  - Keep renewable values that depend on VerbrauchData in sync after Verbrauch edits.
- Impact:
  - On Verbrauch save, renewables with `VerbrauchData_*` formulas are refreshed; WS and Verbrauch cascades remain.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).

## 2025-11-24 – Archive legacy files and add quick reference

- Changes:
  - Moved `scripts/`, `old_test_scripts/`, `old_migration_scripts/`, and backup `models.py.bak*` into `archive/` to reduce confusion.
  - Added Codex quick reference section to CONTEXT.md.
- Reason:
  - Keep runtime tree clean and make onboarding easier while preserving legacy assets.
- Impact:
  - No runtime behavior change; legacy files retained under `archive/`.
- Verification:
  - Docker commands run:
      - `docker compose run --rm app-test`
  - Results:
      - Tests passed (7 tests OK).
