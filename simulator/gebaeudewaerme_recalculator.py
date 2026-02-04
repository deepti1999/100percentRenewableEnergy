import logging
import re
from typing import Optional, List

from django.db import transaction

logger = logging.getLogger(__name__)


def recalc_all_gebaeudewaerme(trigger_code: Optional[str] = None) -> List[str]:
    """
    Deprecated placeholder: GebaeudewaermeData calculations are not active.
    """
    logger.info(
        "Gebaeudewaerme recalculation skipped (deprecated)",
        extra={"eventType": "other", "context": {"trigger_code": trigger_code}},
    )
    return []
