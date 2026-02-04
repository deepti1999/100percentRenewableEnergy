"""
Calculation Engine - Centralized Formula Management
===================================================

This package contains ALL calculation logic for the energy simulation system.
NO formulas should exist in models.py or views.py.

Structure:
- landuse_engine.py: LandUse hierarchical calculations
- renewable_engine.py: Renewable energy formulas and calculations
- verbrauch_engine.py: Verbrauch (consumption) calculations
- formula_evaluator.py: Generic formula evaluation engine
"""

from .landuse_engine import LandUseCalculator
from .renewable_engine import RenewableCalculator
from .verbrauch_engine import VerbrauchCalculator

__all__ = ['LandUseCalculator', 'RenewableCalculator', 'VerbrauchCalculator']
