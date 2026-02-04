"""
WS Calculator - Database-Driven Formula Calculations
====================================================

This calculator handles WS (Wochenspeicher/Weekly Storage) data calculations
using the FormulaVariable approach for full extensibility.
"""

from .formula_evaluator import FormulaEvaluator
from simulator.formula_service import FormulaService


class WSCalculator:
    """
    Calculator for WS (Wochenspeicher) data.
    Uses FormulaVariable mappings (fully extensible via Admin).
    """
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.formula_service = FormulaService(use_cache=True)
        self.cache = {}
    
    def set_data_sources(self, ws_data, renewable_data=None, verbrauch_data=None):
        """
        Set up lookup dictionaries from data sources.
        
        Args:
            ws_data: Dict of {code: {'value': x}} for WS data
            renewable_data: Optional dict of renewable data
            verbrauch_data: Optional dict of verbrauch data
        """
        # Clear cache when new data sources are set
        self.cache = {}
        
        value_lookup = {}
        
        # Add WS data with WS_ prefix to match formula references
        for code, data in ws_data.items():
            ws_key = f'WS_{code}' if not code.startswith('WS_') else code
            if data.get('value') is not None:
                value_lookup[ws_key] = float(data['value'])
        
        # Add RenewableData if provided
        if renewable_data:
            for code, data in renewable_data.items():
                renewable_key = f'Renewable_{code}'
                # WS formulas typically use target values
                if data.get('target_value') is not None:
                    value_lookup[renewable_key] = float(data['target_value'])
                elif data.get('status_value') is not None:
                    value_lookup[renewable_key] = float(data['status_value'])
        
        # Add VerbrauchData if provided
        if verbrauch_data:
            for code, data in verbrauch_data.items():
                verbrauch_key = f'Verbrauch_{code}'
                # WS formulas typically use ziel values
                if data.get('ziel') is not None:
                    value_lookup[verbrauch_key] = float(data['ziel'])
                elif data.get('status') is not None:
                    value_lookup[verbrauch_key] = float(data['status'])
        
        # For WS calculations, we use the same lookup for both status and target
        self.evaluator.set_lookups(value_lookup, value_lookup)
    
    def calculate(self, code):
        """
        Calculate value for a WS item using FormulaVariable mappings.
        
        Args:
            code: The WS code (e.g., 'WS_SOLARSTROM' or 'SOLARSTROM')
            
        Returns:
            float: Calculated value or None if fixed or error
        """
        # Normalize code - add WS_ prefix if not present
        lookup_code = f'WS_{code}' if not code.startswith('WS_') else code
        
        # Check cache
        if lookup_code in self.cache:
            return self.cache[lookup_code]
        
        # Use FormulaVariable mappings (database-driven, fully extensible)
        from simulator.formula_service import evaluate_with_mappings
        value, _ = evaluate_with_mappings(lookup_code, category='ws')
        
        # Cache and return (WS only uses single value, not status/target)
        self.cache[lookup_code] = value
        return value
    
    def get_formula(self, code):
        """
        Get the formula for a code from database.
        """
        lookup_code = f'WS_{code}' if not code.startswith('WS_') else code
        formula_def = self.formula_service.get_formula(lookup_code, category='ws')
        if formula_def:
            return formula_def.get('expression')
        return None
    
    def is_fixed(self, code):
        """
        Check if a code is a fixed value from database.
        """
        lookup_code = f'WS_{code}' if not code.startswith('WS_') else code
        formula_def = self.formula_service.get_formula(lookup_code, category='ws')
        if formula_def:
            return formula_def.get('is_fixed', True)
        return True
