import logging
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
    - Returns list of codes that were updated.
    """
    # Local import to avoid circular dependency
    from simulator.models import VerbrauchData

    updated_codes: list[str] = []
    with transaction.atomic():
        items = list(VerbrauchData.objects.all().order_by("-code"))
        # Sort by depth desc so children calculate before parents
        items.sort(key=lambda i: _hierarchy_depth(i.code), reverse=True)
        # Build lookups once and reuse a single calculator (major speedup vs per-row calculator init).
        from simulator.models import RenewableData, LandUse
        from calculation_engine.verbrauch_engine import VerbrauchCalculator

        renewable_data = {
            r.code: {"status_value": r.status_value or 0, "target_value": r.target_value or 0}
            for r in RenewableData.objects.all()
        }
        landuse_data = {
            lu.code: {"status_ha": lu.status_ha or 0, "target_ha": lu.target_ha or 0}
            for lu in LandUse.objects.all()
        }
        verbrauch_data = {
            v.code: {"status": v.status or 0, "ziel": v.ziel or 0}
            for v in items
        }

        calculator = VerbrauchCalculator()
        calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)

        def _refresh_verbrauch_lookup(code: str, status_value, ziel_value) -> None:
            verbrauch_data.setdefault(code, {})
            verbrauch_data[code]["status"] = status_value if status_value is not None else 0
            verbrauch_data[code]["ziel"] = ziel_value if ziel_value is not None else 0

            code_us = code.replace(".", "_")
            key_dot = f"Verbrauch_{code}"
            key_us = f"Verbrauch_{code_us}"

            if status_value is None:
                calculator.evaluator.status_lookup.pop(key_dot, None)
                calculator.evaluator.status_lookup.pop(key_us, None)
            else:
                s = float(status_value)
                calculator.evaluator.status_lookup[key_dot] = s
                calculator.evaluator.status_lookup[key_us] = s

            if ziel_value is None:
                calculator.evaluator.target_lookup.pop(key_dot, None)
                calculator.evaluator.target_lookup.pop(key_us, None)
            else:
                z = float(ziel_value)
                calculator.evaluator.target_lookup[key_dot] = z
                calculator.evaluator.target_lookup[key_us] = z

        updated_codes_set: set[str] = set()

        # Two dependency passes are enough for this hierarchy and still much faster than previous logic.
        for _pass in range(2):
            changed_in_pass = False

            for item in items:
                if not (
                    item.is_calculated
                    or item.status_calculated
                    or item.ziel_calculated
                    or item.code in ALWAYS_RECALC_CODES
                ):
                    continue

                try:
                    calc_status, calc_ziel = calculator.calculate(item.code)
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

                new_status = item.status if calc_status is None else calc_status
                new_ziel = item.ziel if calc_ziel is None else calc_ziel

                changed = False
                if new_status is not None and new_status != item.status:
                    item.status = new_status
                    changed = True
                if new_ziel is not None and new_ziel != item.ziel:
                    item.ziel = new_ziel
                    changed = True

                if changed:
                    item.save(skip_cascade=True, skip_recalc=True)
                    updated_codes_set.add(item.code)
                    _refresh_verbrauch_lookup(item.code, item.status, item.ziel)
                    # Any dependency update invalidates cached formula outputs.
                    calculator.cache = {}
                    changed_in_pass = True

            if not changed_in_pass:
                break

        updated_codes = sorted(updated_codes_set)

        # Optional renewable propagation: run once globally instead of per updated code.
        if propagate_renewables and updated_codes:
            try:
                from simulator.recalc_service import recalc_all_renewables_full

                recalc_all_renewables_full(exclude_ws_dependent=False)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Renewable recalc from Verbrauch failed",
                    extra={
                        "eventType": "validation",
                        "context": {
                            "trigger_code": trigger_code,
                            "updated_codes": len(updated_codes),
                        },
                    },
                    exc_info=exc,
                )

    return updated_codes
