import logging
from collections import defaultdict
from typing import Optional, List

from django.db import transaction

logger = logging.getLogger(__name__)


def _hierarchy_depth(code: str) -> int:
    """Return hierarchy depth based on dot count (more dots = deeper)."""
    return code.count(".")


ALWAYS_RECALC_CODES = {"1"}  # top-level rollups that should be recalculated even if not flagged


def recalc_all_verbrauch(trigger_code: Optional[str] = None) -> List[str]:
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
                if item.status_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    new_status = item.calculate_value()
                if item.ziel_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    new_ziel = item.calculate_ziel_value()
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

        # After status/ziel updates, propagate to any RenewableData dependents once
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
