import logging
from collections import defaultdict
from typing import Optional, List

from django.db import transaction

logger = logging.getLogger(__name__)


def _hierarchy_depth(code: str) -> int:
    """Return hierarchy depth based on dot count (more dots = deeper)."""
    return code.count(".")


ALWAYS_RECALC_CODES = {"1"}  # top-level rollups that should be recalculated even if not flagged


def recalc_all_verbrauch(
    trigger_code: Optional[str] = None,
    propagate_renewables: bool = True,
) -> List[str]:
    """
    Recalculate all calculated VerbrauchData rows in dependency-safe order.

    - Processes deeper hierarchy items first so parents see fresh child values.
    - Saves only when values change.
    - Loads ALL data sources ONCE upfront to avoid N+1 DB queries.
    - Returns list of codes that were updated.
    """
    # Local import to avoid circular dependency
    from simulator.models import VerbrauchData, RenewableData, LandUse
    from calculation_engine.verbrauch_engine import VerbrauchCalculator

    updated_codes: list[str] = []
    with transaction.atomic():
        items = list(VerbrauchData.objects.all().order_by("-code"))
        # Sort by depth desc so children calculate before parents
        items.sort(key=lambda i: _hierarchy_depth(i.code), reverse=True)

        # ── PERFORMANCE FIX: Load ALL data sources ONCE ──
        # Previously each item.calculate_value() / calculate_ziel_value()
        # did 3 full-table queries (VerbrauchData.all, RenewableData.all,
        # LandUse.all).  With ~30 calculated items this caused 180+ DB
        # queries per recalc_all_verbrauch call.  Now we load once (3 queries
        # total) and keep the in-memory dicts updated as we go.
        verbrauch_data = {
            v.code: {"status": v.status or 0, "ziel": v.ziel or 0}
            for v in items
        }
        renewable_data = {
            r.code: {"status_value": r.status_value or 0, "target_value": r.target_value or 0}
            for r in RenewableData.objects.all()
        }
        landuse_data = {
            lu.code: {"status_ha": lu.status_ha or 0, "target_ha": lu.target_ha or 0}
            for lu in LandUse.objects.all()
        }

        calculator = VerbrauchCalculator()
        calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)

        for item in items:
            if not (
                item.is_calculated
                or item.status_calculated
                or item.ziel_calculated
                or item.code in ALWAYS_RECALC_CODES
            ):
                continue

            new_status = item.status
            new_ziel = item.ziel

            try:
                calc_status, calc_ziel = calculator.calculate(item.code)
                if item.status_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    new_status = calc_status
                if item.ziel_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    new_ziel = calc_ziel
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Verbrauch recalculation failed",
                    extra={
                        "eventType": "validation",
                        "context": {
                            "code": item.code,
                            "trigger_code": trigger_code,
                        },
                    },
                    exc_info=exc,
                )
                continue

            changed = False
            if new_status is not None and new_status != item.status:
                item.status = new_status
                changed = True
            if new_ziel is not None and new_ziel != item.ziel:
                item.ziel = new_ziel
                changed = True

            if changed:
                item.save(skip_cascade=True, skip_recalc=True)
                updated_codes.append(item.code)
                # Keep in-memory lookups fresh so downstream items see updates
                verbrauch_data[item.code] = {
                    "status": item.status or 0,
                    "ziel": item.ziel or 0,
                }
                calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)

        # Optional propagation to RenewableData dependents.
        # In some flows (e.g. WS heat balancing) a full renewable recalc
        # runs immediately after this, so this propagation is intentionally skipped.
        if propagate_renewables:
            for code in updated_codes:
                try:
                    item = VerbrauchData.objects.get(code=code)
                    item._recalculate_renewable_dependents()
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning(
                        "Renewable recalc from Verbrauch failed",
                        extra={
                            "eventType": "validation",
                            "context": {"code": code, "trigger_code": trigger_code},
                        },
                        exc_info=exc,
                    )

    return updated_codes
